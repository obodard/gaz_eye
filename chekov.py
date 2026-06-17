#!/usr/bin/env python3
"""
Chekov — Fetch and display gas prices from Régie Essence Québec.

Reads a list of stations from stations.yaml, fetches the latest prices
from the public GeoJSON endpoint, and displays them grouped by city.
"""

import gzip
import io
import json
import logging
import sys
from pathlib import Path
from typing import Any, Optional

import requests
import yaml
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Set up logging for generic messaging (instead of print)
# This will output to stdout making it visible to Docker cron outputs
logger = logging.getLogger("Chekov")
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

GEOJSON_URL = "https://regieessencequebec.ca/stations.geojson.gz"
CONFIG_FILE = Path(__file__).parent / "stations.yaml"


def load_config(path: Path) -> dict[str, Any]:
    """Load station configuration from YAML file."""
    if not path.exists():
        logger.error(f"{Fore.RED}Error:{Style.RESET_ALL} Config file not found: {path}")
        logger.error(f"Create a {Style.BRIGHT}stations.yaml{Style.RESET_ALL} file with your stations.")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not config or "cities" not in config:
        logger.error(f"{Fore.RED}Error:{Style.RESET_ALL} Invalid config — missing 'cities' key in {path}")
        sys.exit(1)

    # Normalize settings to a dictionary
    raw_settings = config.get("settings", [])
    settings = {}
    if isinstance(raw_settings, list):
        for item in raw_settings:
            if isinstance(item, dict):
                settings.update(item)
    
    # Add defaults if not present
    config["tank_litres"] = settings.get("tank_litres", 50)
    config["gaz_type"] = settings.get("gaz_type", "Régulier")

    return config


def fetch_stations() -> dict[str, Any]:
    """Download and parse the GeoJSON station data."""
    logger.info(f"{Style.DIM}Fetching latest prices from Régie Essence Québec...{Style.RESET_ALL}")

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
        logger.error(f"{Fore.RED}Error fetching data:{Style.RESET_ALL} {e}")
        sys.exit(1)

    # Try to parse — requests may auto-decompress, or server may send plain JSON
    try:
        try:
            data = json.loads(resp.content)
        except (json.JSONDecodeError, UnicodeDecodeError):
            raw = gzip.decompress(resp.content)
            data = json.loads(raw)
    except Exception as e:
        logger.error(f"{Fore.RED}Error parsing data:{Style.RESET_ALL} {e}")
        sys.exit(1)

    return data


def index_stations_by_address(features: list[dict[str, Any]], address_queries: set[str]) -> dict[str, dict[str, Any]]:
    """Index stations for faster O(N) lookup based on partial address match."""
    index: dict[str, dict[str, Any]] = {}
    pending_queries = {q.lower(): q for q in address_queries}

    for feature in features:
        if not pending_queries:
            break
        props = feature.get("properties", {})
        station_address = props.get("Address", "").lower()
        
        found = []
        for q_lower, original_q in pending_queries.items():
            if q_lower in station_address:
                index[original_q] = feature
                found.append(q_lower)
        
        for q_lower in found:
            del pending_queries[q_lower]

    return index


def parse_price_value(price_entry: dict[str, Any]) -> float:
    """Extract numeric price value (dollars) for sorting."""
    if not price_entry.get("IsAvailable") or price_entry.get("Price") is None:
        return float('inf')

    price_str = price_entry["Price"]
    price_val = price_str.replace("¢", "").replace("\u00a2", "").strip()
    try:
        cents = float(price_val)
        return cents / 100
    except ValueError:
        return float('inf')


def format_price(price_entry: dict[str, Any], width: int = 10) -> str:
    """Format a price entry for display with fixed width."""
    val = parse_price_value(price_entry)
    if val == float('inf'):
        txt = "n/a"
    else:
        txt = f"{val:.3f}$"

    padded = f"{txt:>{width}}"
    return f"{Style.BRIGHT}{padded}{Style.RESET_ALL}"


def display_results(config: dict[str, Any], data: dict[str, Any]) -> None:
    """Display matched station prices in a sorted table."""
    features = data.get("features", [])
    metadata = data.get("metadata", {})
    generated_at = metadata.get("generated_at", "unknown")
    total_stations = metadata.get("total_stations", "?")

    logger.info("")
    logger.info(f"{Style.BRIGHT}⛽ Régie Essence Québec — Prix du carburant{Style.RESET_ALL}")
    logger.info(f"{Style.DIM}Données: {generated_at} ({total_stations} stations){Style.RESET_ALL}")
    logger.info("")

    tank_litres = config.get("tank_litres", 50)
    gaz_type = config.get("gaz_type", "Régulier")

    # Header
    header = (
        f"  {Fore.CYAN}{'Station':<50}{Style.RESET_ALL} {gaz_type:>10} {'Delta':>10} {tank_litres:>2}L (±)"
    )
    logger.info(f"{Style.BRIGHT}{header}{Style.RESET_ALL}")
    logger.info(f"  {'─' * 83}")

    # Build queries and reference tracking
    all_queries = set()
    ref_station_query: Optional[str] = None

    for city in config["cities"]:
        for station_cfg in city.get("stations", []):
            address_query = station_cfg["address"]
            all_queries.add(address_query)
            if station_cfg.get("reference_station"):
                ref_station_query = address_query

    # Single pass lookup
    station_index = index_stations_by_address(features, all_queries)

    rows = []
    not_found = []
    ref_price = None

    if ref_station_query and ref_station_query in station_index:
        ref_prices = station_index[ref_station_query]["properties"].get("Prices", [])
        for p in ref_prices:
            if p.get("GasType") == gaz_type:
                ref_price = parse_price_value(p)
                break

    for city in config["cities"]:
        city_name = city["city"]
        for station_cfg in city.get("stations", []):
            address_query = station_cfg["address"]
            match = station_index.get(address_query)

            if match is None:
                not_found.append(f"{city_name}: {address_query}")
                continue

            props = match["properties"]
            brand = props.get("brand", "")
            prices = props.get("Prices", [])

            alias = station_cfg.get("alias", "")
            brand_display = brand if brand and brand != "Aucun" else "Inconnu"
            
            city_col = f"{city_name}, {brand_display}"
            if alias:
                city_col += f" ({alias})"

            price_map = {p.get("GasType", ""): p for p in prices}
            selected_entry = price_map.get(gaz_type, {})
            
            rows.append({
                "station": city_col,
                "sort_val": parse_price_value(selected_entry),
                "price_formatted": format_price(selected_entry),
            })

    # Sort by selected gas type price
    rows.sort(key=lambda x: x["sort_val"])

    for row in rows:
        delta_str = ""
        tank_delta_str = ""
        curr_price = row["sort_val"]
        price_str = row["price_formatted"]
        
        if ref_price is not None and curr_price != float('inf') and ref_price != float('inf'):
            delta = curr_price - ref_price
            tank_delta = delta * tank_litres
            
            sign = "+" if delta > 0 else "-" if delta < 0 else ""
            
            if delta == 0:
                delta_str = "0.000$"
                tank_delta_str = "0.00$"
            else:
                delta_str = f"{sign}{abs(delta):.3f}$"
                tank_delta_str = f"{sign}{abs(tank_delta):.2f}$"
        
        delta_padded = f"{delta_str:>10}"
        tank_delta_padded = f"{tank_delta_str:>10}"
        
        logger.info(f"  {Fore.CYAN}{row['station']:<50}{Style.RESET_ALL} {price_str} {delta_padded} {Style.BRIGHT}{tank_delta_padded}{Style.RESET_ALL}")

    logger.info(f"  {'─' * 83}")

    if not_found:
        logger.info(f"\n{Fore.YELLOW}⚠ Stations not found ({len(not_found)}):{Style.RESET_ALL}")
        for nf in not_found:
            logger.info(f"  • {nf}")
        logger.info(f"{Style.DIM}Tip: Check address strings in stations.yaml against "
                    f"https://regieessencequebec.ca/{Style.RESET_ALL}")

    logger.info("")


def main() -> None:
    config = load_config(CONFIG_FILE)
    data = fetch_stations()
    display_results(config, data)


if __name__ == "__main__":
    main()
