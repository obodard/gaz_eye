#!/usr/bin/env python3
"""
Gaz Saver — Fetch and display gas prices from Régie Essence Québec.

Reads a list of stations from stations.yaml, fetches the latest prices
from the public GeoJSON endpoint, and displays them grouped by city.
"""

import gzip
import io
import json
import sys
from pathlib import Path

import requests
import yaml

GEOJSON_URL = "https://regieessencequebec.ca/stations.geojson.gz"
CONFIG_FILE = Path(__file__).parent / "stations.yaml"

# Terminal colors
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
RESET = "\033[0m"


def load_config(path: Path) -> dict:
    """Load station configuration from YAML file."""
    if not path.exists():
        print(f"{RED}Error:{RESET} Config file not found: {path}")
        print(f"Create a {BOLD}stations.yaml{RESET} file with your stations.")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not config or "cities" not in config:
        print(f"{RED}Error:{RESET} Invalid config — missing 'cities' key in {path}")
        sys.exit(1)

    return config


def fetch_stations() -> dict:
    """Download and parse the GeoJSON station data."""
    print(f"{DIM}Fetching latest prices from Régie Essence Québec...{RESET}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/131.0.0.0 Safari/537.36",
        "Accept": "application/json, application/geo+json, */*",
        "Accept-Encoding": "gzip, deflate, br",
    }

    try:
        resp = requests.get(GEOJSON_URL, headers=headers, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"{RED}Error fetching data:{RESET} {e}")
        sys.exit(1)

    # Try to parse — requests may auto-decompress, or server may send plain JSON
    try:
        # First, try parsing the content as-is (requests handles gzip via
        # Accept-Encoding automatically, so resp.content may already be plain)
        try:
            data = json.loads(resp.content)
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fallback: manually decompress if still gzipped
            raw = gzip.decompress(resp.content)
            data = json.loads(raw)
    except Exception as e:
        print(f"{RED}Error parsing data:{RESET} {e}")
        sys.exit(1)

    return data


def find_station(features: list, address_query: str) -> dict | None:
    """Find a station by partial address match (case-insensitive)."""
    query_lower = address_query.lower()
    for feature in features:
        props = feature.get("properties", {})
        station_address = props.get("Address", "")
        if query_lower in station_address.lower():
            return feature
    return None


def parse_price_value(price_entry: dict) -> float:
    """Extract numeric price value (dollars) for sorting."""
    if not price_entry.get("IsAvailable") or price_entry.get("Price") is None:
        return float('inf')  # Put unavailable at the bottom

    price_str = price_entry["Price"]
    price_val = price_str.replace("¢", "").replace("\u00a2", "").strip()
    try:
        cents = float(price_val)
        return cents / 100
    except ValueError:
        return float('inf')


def format_price(price_entry: dict) -> str:
    """Format a price entry for display."""
    val = parse_price_value(price_entry)
    if val == float('inf'):
        return f"{DIM}  n/a  {RESET}"

    return f"{BOLD}{val:.3f}${RESET}"


def display_results(config: dict, data: dict):
    """Display matched station prices in a sorted table."""
    features = data.get("features", [])
    metadata = data.get("metadata", {})
    generated_at = metadata.get("generated_at", "unknown")
    total_stations = metadata.get("total_stations", "?")

    print()
    print(f"{BOLD}⛽ Régie Essence Québec — Prix du carburant{RESET}")
    print(f"{DIM}Données: {generated_at} ({total_stations} stations){RESET}")
    print()

    # Header
    header = (
        f"  {CYAN}{'City':<20}{RESET} {'Station':<40} {'Régulier':>10} {'Super':>10} {'Delta':>10}"
    )
    print(f"{BOLD}{header}{RESET}")
    print(f"  {'─' * 95}")

    rows = []
    not_found = []

    for city in config["cities"]:
        city_name = city["name"]
        for station_cfg in city.get("stations", []):
            address_query = station_cfg["address"]
            match = find_station(features, address_query)

            if match is None:
                not_found.append(f"{city_name}: {address_query}")
                continue

            props = match["properties"]
            name = props.get("Name", "?")
            brand = props.get("brand", "")
            prices = props.get("Prices", [])

            if brand and brand != "Aucun":
                display_name = f"{brand} — {name}"
            else:
                display_name = name

            if len(display_name) > 38:
                display_name = display_name[:35] + "..."

            price_map = {p.get("GasType", ""): p for p in prices}
            reg_entry = price_map.get("Régulier", {})
            
            rows.append({
                "city": city_name,
                "name": display_name,
                "sort_val": parse_price_value(reg_entry),
                "reg": format_price(reg_entry),
                "sup": format_price(price_map.get("Super", {})),
            })

    # Sort by Régulier price
    rows.sort(key=lambda x: x["sort_val"])

    prev_price = None
    for row in rows:
        delta_str = ""
        curr_price = row["sort_val"]
        
        if prev_price is not None and curr_price != float('inf') and prev_price != float('inf'):
            delta = curr_price - prev_price
            sign = "+" if delta > 0 else ""
            delta_str = f"{sign}{delta:.3f}$"
            if delta == 0:
                delta_str = "0.000$"
        
        print(f"  {CYAN}{row['city']:<20}{RESET} {row['name']:<40} {row['reg']:>10} {row['sup']:>10} {delta_str:>10}")
        prev_price = curr_price

    print(f"  {'─' * 95}")

    if not_found:
        print(f"\n{YELLOW}⚠ Stations not found ({len(not_found)}):{RESET}")
        for nf in not_found:
            print(f"  • {nf}")
        print(f"{DIM}Tip: Check address strings in stations.yaml against "
              f"https://regieessencequebec.ca/{RESET}")

    print()


def main():
    config = load_config(CONFIG_FILE)
    data = fetch_stations()
    display_results(config, data)


if __name__ == "__main__":
    main()
