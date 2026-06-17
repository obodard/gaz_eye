"""
chekov geospatial module.

Pure geospatial functions: polyline decoding, Haversine distance,
corridor matching, and route distance. No side effects, no network calls.
"""

import math

import polyline as _polyline

EARTH_RADIUS_KM = 6371.0


def decode_polyline(encoded_string: str) -> list[dict]:
    """Decode a Google Maps encoded polyline string into lat/lng dicts."""
    return [{"lat": float(lat), "lng": float(lng)} for lat, lng in _polyline.decode(encoded_string)]


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return the great-circle distance in km between two lat/lng points."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(min(a, 1.0)))


def find_stations_in_corridor(
    polyline_points: list[dict],
    all_stations: list[dict],
    corridor_km: float,
) -> list[dict]:
    """Return stations within corridor_km of any polyline point, with distance_from_route_km added."""
    if not polyline_points:
        return []
    result = []
    for station in all_stations:
        min_dist = min(
            haversine(station["lat"], station["lng"], pt["lat"], pt["lng"])
            for pt in polyline_points
        )
        if min_dist <= corridor_km:
            station_copy = dict(station)
            station_copy["distance_from_route_km"] = round(min_dist, 4)
            result.append(station_copy)
    return result


def distance_along_route(
    polyline_points: list[dict],
    station_lat: float,
    station_lng: float,
) -> float:
    """Return the cumulative route distance (km) from the origin to the nearest polyline point.

    This is NOT straight-line distance from origin. It is the sum of consecutive
    Haversine segment lengths along the polyline up to the nearest point.
    """
    if not polyline_points:
        return 0.0

    nearest_idx = min(
        range(len(polyline_points)),
        key=lambda i: haversine(station_lat, station_lng, polyline_points[i]["lat"], polyline_points[i]["lng"]),
    )

    cumulative = 0.0
    for i in range(nearest_idx):
        cumulative += haversine(
            polyline_points[i]["lat"], polyline_points[i]["lng"],
            polyline_points[i + 1]["lat"], polyline_points[i + 1]["lng"],
        )
    return cumulative
