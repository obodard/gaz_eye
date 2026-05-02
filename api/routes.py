"""
gaz_eye API Blueprint.

All HTTP routes live here. app.py only registers this blueprint — no routes
are defined in app.py directly.
"""

import logging
import os
from pathlib import Path

import requests
import yaml
from flask import Blueprint, current_app, jsonify, render_template, request

from api.geo import decode_polyline, find_stations_in_corridor, distance_along_route
from api.pricing import (
    build_recommendation,
    detect_stale_prices,
    fetch_stations,
    filter_by_autonomy,
    rank_routes,
)

bp = Blueprint("api", __name__)
logger = logging.getLogger("gaz_eye.routes")

DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"
_CONFIG_PATH = Path(__file__).parent.parent / "stations.yaml"


def _format_drive_time(seconds: int) -> str:
    """Format drive duration seconds into a human-readable string like '2 h 14 min'."""
    hours, remainder = divmod(seconds, 3600)
    minutes = remainder // 60
    if hours > 0:
        return f"{hours} h {minutes:02d} min"
    return f"{minutes} min"


@bp.route("/")
def serve_index():
    """Serve the gaz_eye SPA shell as a Jinja2 template."""
    return render_template(
        "index.html",
        google_maps_api_key=current_app.config["GOOGLE_MAPS_API_KEY"]
    )


@bp.route("/api/plan", methods=["POST"])
def plan():
    """Accept trip parameters and return up to three routes with fuel recommendations."""
    body = request.get_json(silent=True) or {}

    missing = [f for f in ("origin", "destination", "range_km") if f not in body]
    if missing:
        return jsonify({"error": "internal", "message": f"Missing required field(s): {', '.join(missing)}"}), 400

    origin = body["origin"]
    destination = body["destination"]
    try:
        range_km = float(body["range_km"])
        corridor_km = float(body.get("corridor_km", 2.0))
        tank_litres = float(body.get("tank_litres", 50))
    except (TypeError, ValueError) as exc:
        return jsonify({"error": "internal", "message": f"Invalid numeric field: {exc}"}), 400

    waypoints = body.get("waypoints", [])
    if not isinstance(waypoints, list):
        return jsonify({"error": "internal", "message": "waypoints must be a list"}), 400

    fuel_type = body.get("fuel_type", "Régulier")

    raw_buffer = body.get("buffer_km")
    if raw_buffer is not None:
        try:
            buffer_km = float(raw_buffer)
        except (TypeError, ValueError):
            return jsonify({"error": "internal", "message": "buffer_km must be a number"}), 400
    else:
        buffer_km = None

    # Fetch stations first so a Régie Essence failure surfaces before spending a Google Maps quota call
    try:
        all_stations, data_timestamp = fetch_stations(fuel_type)
    except Exception as exc:
        return jsonify({"error": "regie_essence", "message": str(exc)}), 502

    try:
        with open(_CONFIG_PATH, encoding="utf-8") as _f:
            _yaml_cfg = yaml.safe_load(_f)
        if not isinstance(_yaml_cfg, dict):
            _yaml_cfg = {}
    except (OSError, yaml.YAMLError) as _cfg_exc:
        logger.warning(f"Could not load anomaly filter config from {_CONFIG_PATH}: {_cfg_exc}")
        _yaml_cfg = {}
    anomaly_filter_enabled = _yaml_cfg.get("anomaly_filter_enabled", True)
    _raw_exemptions = _yaml_cfg.get("anomaly_filter_exemptions") or []
    anomaly_filter_exemptions = _raw_exemptions if isinstance(_raw_exemptions, list) else [_raw_exemptions]

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")

    params: dict = {
        "origin": origin,
        "destination": destination,
        "alternatives": "true",
        "key": api_key,
    }
    if waypoints:
        params["waypoints"] = "|".join(waypoints)

    try:
        resp = requests.get(DIRECTIONS_URL, params=params, timeout=15)
        resp.raise_for_status()
        try:
            gm_data = resp.json()
        except ValueError as exc:
            return jsonify({"error": "google_maps", "message": f"Invalid JSON response: {exc}"}), 502
    except requests.RequestException as exc:
        safe_msg = str(exc).replace(api_key, "***") if api_key else str(exc)
        return jsonify({"error": "google_maps", "message": safe_msg}), 502

    gm_status = gm_data.get("status", "")
    if gm_status and gm_status not in ("OK", "ZERO_RESULTS"):
        return jsonify({
            "error": "google_maps",
            "message": gm_status,
            "details": gm_data.get("error_message", ""),
        }), 502

    gm_routes = gm_data.get("routes", [])

    routes = []
    for gm_route in gm_routes:
        encoded_polyline = (gm_route.get("overview_polyline") or {}).get("points", "")
        if not encoded_polyline:
            continue
        polyline_pts = decode_polyline(encoded_polyline)
        if not polyline_pts:
            continue

        legs = gm_route.get("legs") or []
        if not legs:
            continue
        drive_time_seconds = (legs[0].get("duration") or {}).get("value", 0)
        label = gm_route.get("summary", f"Route {len(routes) + 1}")

        corridor_stations = find_stations_in_corridor(polyline_pts, all_stations, corridor_km)
        for s in corridor_stations:
            s["distance_from_origin_km"] = round(
                distance_along_route(polyline_pts, s["lat"], s["lng"]), 2
            )

        if anomaly_filter_enabled:
            corridor_stations = detect_stale_prices(
                corridor_stations,
                all_stations,
                exemptions=anomaly_filter_exemptions,
                data_timestamp=data_timestamp,
            )

        reachable = filter_by_autonomy(corridor_stations, range_km, buffer_km)

        rec = build_recommendation(reachable, tank_litres)
        best_station = rec["best_station"]

        for s in reachable:
            s["is_best"] = (best_station is not None and s is best_station)
            # float('inf') is not valid JSON — replace with None so the client
            # receives null and can display the station as "price unavailable"
            if s.get("price_per_litre") == float("inf"):
                s["price_per_litre"] = None

        routes.append({
            "label": label,
            "drive_time_seconds": drive_time_seconds,
            "drive_time_display": _format_drive_time(drive_time_seconds),
            "polyline_encoded": encoded_polyline,
            "stations": reachable,
            "best_station": best_station,
            "savings_per_litre": rec["savings_per_litre"],
            "savings_per_tank_litres": rec["savings_per_tank"],
        })

    rank_routes(routes)

    return jsonify({"routes": routes, "data_timestamp": data_timestamp}), 200
