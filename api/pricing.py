"""
gaz_eye pricing module.

Provides GeoJSON fetch from Régie Essence Québec and price parsing logic.
Ported from gaz_saver.py with the following key differences:
- fetch_stations() raises exceptions instead of calling sys.exit()
- parse_price_value() accepts a raw string (or None), not a dict
- Returns station list suitable for the /api/plan pipeline
"""

import gzip
import json
import logging
import math
import statistics
import sys
from typing import Any, Optional

import requests

from api.geo import haversine

logger = logging.getLogger("gaz_eye.pricing")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

GEOJSON_URL = "https://regieessencequebec.ca/stations.geojson.gz"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, application/geo+json, */*",
    "Accept-Encoding": "gzip, deflate, br",
}

ANOMALY_THRESHOLD_CAD = 0.05


def parse_price_value(price_str: Optional[str]) -> float:
    """Parse a cent-string price (e.g. '154.9¢') to dollars per litre.

    Returns float('inf') for None, empty string, or non-parseable input.
    """
    if not price_str:
        return float('inf')

    cleaned = price_str.replace("¢", "").replace("\u00a2", "").strip()
    if not cleaned:
        return float('inf')

    try:
        cents = float(cleaned)
        if math.isnan(cents) or cents < 0:
            return float('inf')
        return cents / 100.0
    except ValueError:
        return float('inf')


def fetch_stations(fuel_type: str = "Régulier") -> tuple[list[dict[str, Any]], str]:
    """Fetch and parse station data from the Régie Essence Québec GeoJSON endpoint.

    Returns a tuple of (stations, data_timestamp) where stations is a list of dicts
    each containing: name, address, lat, lng, price_per_litre.

    Raises requests.RequestException on network failure.
    Raises ValueError on parse failure.
    """
    resp = requests.get(GEOJSON_URL, headers=_HEADERS, timeout=30)
    resp.raise_for_status()

    # Dual-parse: try plain JSON first (endpoint may auto-decompress), fall back to gzip
    try:
        try:
            data = json.loads(resp.content)
        except (json.JSONDecodeError, UnicodeDecodeError):
            raw = gzip.decompress(resp.content)
            data = json.loads(raw)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"Failed to parse GeoJSON response: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Unexpected GeoJSON format: expected a JSON object at the top level")

    features = data.get("features", [])
    metadata = data.get("metadata", {})
    data_timestamp = metadata.get("generated_at", "")

    stations: list[dict[str, Any]] = []
    for feature in features:
        props = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        coords = geometry.get("coordinates") or [None, None]

        address = props.get("Address", "")
        brand = props.get("brand", "")
        name = brand if brand and brand != "Aucun" else address

        # Find price for requested fuel type
        prices = props.get("Prices") or []
        price_entry = next((p for p in prices if p.get("GasType") == fuel_type), None)

        if price_entry is None or not price_entry.get("IsAvailable"):
            price_per_litre = float('inf')
        else:
            price_per_litre = parse_price_value(price_entry.get("Price"))

        # coords in GeoJSON are [lng, lat]
        lng = coords[0] if len(coords) > 0 else None
        lat = coords[1] if len(coords) > 1 else None

        if lat is None or lng is None:
            continue

        stations.append({
            "name": name,
            "address": address,
            "lat": float(lat),
            "lng": float(lng),
            "price_per_litre": price_per_litre,
        })

    return stations, data_timestamp


def filter_by_autonomy(
    stations: list[dict[str, Any]],
    range_km: float,
    buffer_km: Optional[float] = None,
) -> list[dict[str, Any]]:
    """Return stations reachable within range_km minus safety buffer.

    If buffer_km is None, defaults to max(range_km * 0.10, 15) km.
    """
    if buffer_km is None:
        buffer_km = max(range_km * 0.10, 15.0)

    max_distance = range_km - buffer_km
    return [s for s in stations if s.get("distance_from_origin_km", 0.0) <= max_distance]


def build_recommendation(
    stations: list[dict[str, Any]],
    tank_litres: float,
) -> dict[str, Any]:
    """Build a cheapest/worst station recommendation with savings.

    Stations with price_per_litre == float('inf') are excluded from selection.
    Returns a dict with best_station, worst_station, savings_per_litre, savings_per_tank.
    """
    valid = [s for s in stations if s.get("price_per_litre", float('inf')) != float('inf')]

    if not valid:
        return {
            "best_station": None,
            "worst_station": None,
            "savings_per_litre": 0.0,
            "savings_per_tank": 0.0,
        }

    best = min(valid, key=lambda s: s["price_per_litre"])
    worst = max(valid, key=lambda s: s["price_per_litre"])
    savings_per_litre = worst["price_per_litre"] - best["price_per_litre"]
    savings_per_tank = savings_per_litre * tank_litres

    return {
        "best_station": best,
        "worst_station": worst,
        "savings_per_litre": round(savings_per_litre, 4),
        "savings_per_tank": round(savings_per_tank, 4),
    }


def rank_routes(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add a rank field to each route dict; rank 1 = highest savings_per_litre.

    Mutates dicts in-place and returns the list for chaining.
    """
    sorted_routes = sorted(routes, key=lambda r: r.get("savings_per_litre", 0.0), reverse=True)
    for i, route in enumerate(sorted_routes, start=1):
        route["rank"] = i
    return routes


_RADII = [5.0, 10.0, 20.0, 50.0]


def detect_stale_prices(
    corridor_stations: list[dict[str, Any]],
    all_stations: list[dict[str, Any]],
    threshold: float = ANOMALY_THRESHOLD_CAD,
    exemptions: Optional[list[str]] = None,
    data_timestamp: str = "",
) -> list[dict[str, Any]]:
    """Return corridor_stations with anomalously cheap stations' price set to float('inf').

    Uses a density-adaptive spatial median (radii: 5, 10, 20, 50 km) to detect stale prices.
    Stations with no price data, or fewer than 5 neighbors within 50 km, bypass the filter.
    """
    if threshold < 0:
        raise ValueError(f"threshold must be non-negative, got {threshold}")
    
    if exemptions is None:
        exemptions = []

    # Pre-filter all_stations to valid-price stations once (performance optimisation)
    valid_pool = [
        s for s in all_stations
        if s.get("price_per_litre", float("inf")) != float("inf")
    ]

    result: list[dict[str, Any]] = []
    for station in corridor_stations:
        station_copy = dict(station)

        # Bypass: no price data
        if station["price_per_litre"] == float("inf"):
            result.append(station_copy)
            continue

        # Bypass: exempted station (case-insensitive substring match)
        station_name = station.get("name", "").lower()
        if any(isinstance(exc, str) and exc.lower() in station_name for exc in exemptions):
            result.append(station_copy)
            continue

        # Density-adaptive neighbor search
        neighbors = None
        radius_used = None
        for radius in _RADII:
            candidates = [
                s for s in valid_pool
                if not (math.isclose(s["lat"], station["lat"], abs_tol=1e-8) and math.isclose(s["lng"], station["lng"], abs_tol=1e-8))
                and haversine(station["lat"], station["lng"], s["lat"], s["lng"]) <= radius
            ]
            if len(candidates) >= 5:
                neighbors = candidates
                radius_used = radius
                break

        # Bypass: insufficient neighbors within 50 km
        if neighbors is None:
            result.append(station_copy)
            continue

        local_median = statistics.median(s["price_per_litre"] for s in neighbors)

        if local_median - station["price_per_litre"] > threshold:
            original_price = station_copy["price_per_litre"]
            neighbor_count = len(neighbors)
            logger.info(
                f"Stale price excluded: {station_copy.get('name', '<unknown>')} | "
                f"price={original_price:.3f} | median={local_median:.3f} | "
                f"neighbors={neighbor_count} | radius={radius_used}km | "
                f"ts={data_timestamp}"
            )
            station_copy["price_per_litre"] = float("inf")

        result.append(station_copy)

    return result
