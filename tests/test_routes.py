"""
Tests for api/routes.py — POST /api/plan endpoint.
All external calls (Google Maps, Régie Essence) are mocked.
A live API key is never required.
"""

import os
from unittest.mock import MagicMock, patch

import polyline as polyline_lib
import pytest

from app import create_app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client(monkeypatch):
    """Flask test client with a dummy API key in the environment."""
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "test_api_key_dummy")
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _encoded_polyline() -> str:
    """Return a real short encoded polyline for two Quebec coordinates."""
    return polyline_lib.encode([(45.5017, -73.5673), (45.6066, -73.7124)])


def _make_gm_response(n_routes: int = 3) -> dict:
    """Build a minimal Google Maps Directions API response."""
    route = {
        "summary": "Via Hwy 50",
        "legs": [{"duration": {"value": 7200, "text": "2 hours"}, "distance": {"value": 200000}}],
        "overview_polyline": {"points": _encoded_polyline()},
    }
    return {"status": "OK", "routes": [dict(route) for _ in range(n_routes)]}


def _make_mock_get(response_dict: dict, status_code: int = 200) -> MagicMock:
    """Return a mock that simulates a successful requests.get call."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = response_dict
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


def _make_stations(n: int = 3) -> list:
    """Return n minimal station dicts with reachable distance_from_origin_km."""
    return [
        {
            "name": f"Station {i}",
            "address": f"{i} rue Test, Montréal",
            "lat": 45.5017 + i * 0.01,
            "lng": -73.5673 - i * 0.01,
            "price_per_litre": 1.50 + i * 0.01,
        }
        for i in range(n)
    ]


_VALID_BODY = {
    "origin": "Montréal, QC",
    "destination": "Duhamel, QC",
    "range_km": 200,
    "waypoints": [],
    "fuel_type": "Régulier",
    "corridor_km": 2.0,
    "buffer_km": 15,
    "tank_litres": 50,
}


# ---------------------------------------------------------------------------
# Serve index (Story 3.1)
# ---------------------------------------------------------------------------

class TestServeIndex:
    """Tests for GET / — SPA shell served as Jinja2 template."""

    def test_returns_200(self, client):
        """GET / returns 200 with HTML content."""
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"gaz_eye" in resp.data

    def test_api_key_in_script_src_only(self, client):
        """GOOGLE_MAPS_API_KEY appears only in Maps CDN script src, not as a JS variable."""
        resp = client.get("/")
        html = resp.data.decode("utf-8")
        assert "key=test_api_key_dummy" in html
        assert "window.GOOGLE_MAPS_API_KEY" not in html
        assert '"test_api_key_dummy"' not in html
        assert "'test_api_key_dummy'" not in html


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

class TestPlanHappyPath:
    """Success case for POST /api/plan."""

    @patch("api.routes.requests.get")
    @patch("api.routes.fetch_stations")
    def test_returns_200_with_routes(self, mock_fetch, mock_get, client):
        """Happy path: 3 GM routes returned, all required keys present."""
        mock_fetch.return_value = (_make_stations(3), "2026-05-01T00:00:00Z")
        mock_get.return_value = _make_mock_get(_make_gm_response(3))

        resp = client.post("/api/plan", json=_VALID_BODY)

        assert resp.status_code == 200
        data = resp.get_json()
        assert "routes" in data
        assert "data_timestamp" in data

    @patch("api.routes.requests.get")
    @patch("api.routes.fetch_stations")
    def test_route_schema_keys_present(self, mock_fetch, mock_get, client):
        """Each route object must contain all required fields."""
        mock_fetch.return_value = (_make_stations(3), "2026-05-01T00:00:00Z")
        mock_get.return_value = _make_mock_get(_make_gm_response(1))

        resp = client.post("/api/plan", json=_VALID_BODY)
        data = resp.get_json()
        route = data["routes"][0]

        for key in (
            "label", "drive_time_seconds", "drive_time_display",
            "polyline_encoded", "stations", "best_station",
            "savings_per_litre", "savings_per_tank_litres",
        ):
            assert key in route, f"Missing route key: {key}"

    @patch("api.routes.requests.get")
    @patch("api.routes.fetch_stations")
    def test_api_key_not_in_response_body(self, mock_fetch, mock_get, client, monkeypatch):
        """The Google Maps API key must never appear in the response body."""
        monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "super_secret_key_xyz")
        mock_fetch.return_value = (_make_stations(2), "2026-05-01T00:00:00Z")
        mock_get.return_value = _make_mock_get(_make_gm_response(2))

        resp = client.post("/api/plan", json=_VALID_BODY)

        assert "super_secret_key_xyz" not in resp.data.decode()

    @patch("api.routes.requests.get")
    @patch("api.routes.fetch_stations")
    def test_drive_time_display_format(self, mock_fetch, mock_get, client):
        """drive_time_display should be formatted correctly (e.g. '2 h 00 min')."""
        mock_fetch.return_value = (_make_stations(1), "2026-05-01T00:00:00Z")
        mock_get.return_value = _make_mock_get(_make_gm_response(1))

        resp = client.post("/api/plan", json=_VALID_BODY)
        data = resp.get_json()

        # 7200 seconds = 2 h 00 min
        assert data["routes"][0]["drive_time_display"] == "2 h 00 min"

    @patch("api.routes.requests.get")
    @patch("api.routes.fetch_stations")
    def test_station_schema_keys_present(self, mock_fetch, mock_get, client):
        """Each station must contain all eight required fields from AC1."""
        mock_fetch.return_value = (_make_stations(3), "2026-05-01T00:00:00Z")
        mock_get.return_value = _make_mock_get(_make_gm_response(1))

        resp = client.post("/api/plan", json=_VALID_BODY)
        data = resp.get_json()

        stations = data["routes"][0]["stations"]
        assert len(stations) > 0, "Expected at least one station in the corridor"
        for key in ("name", "address", "price_per_litre", "distance_from_route_km",
                    "distance_from_origin_km", "lat", "lng", "is_best"):
            assert key in stations[0], f"Missing station key: {key}"

    @patch("api.routes.requests.get")
    @patch("api.routes.fetch_stations")
    def test_label_from_summary(self, mock_fetch, mock_get, client):
        """Route label should be taken from the Google Maps summary field."""
        mock_fetch.return_value = (_make_stations(1), "2026-05-01T00:00:00Z")
        mock_get.return_value = _make_mock_get(_make_gm_response(1))

        resp = client.post("/api/plan", json=_VALID_BODY)
        data = resp.get_json()

        assert data["routes"][0]["label"] == "Via Hwy 50"


# ---------------------------------------------------------------------------
# Error cases — upstream failures
# ---------------------------------------------------------------------------

class TestPlanUpstreamErrors:
    """502 errors triggered by upstream failures."""

    @patch("api.routes.requests.get")
    @patch("api.routes.fetch_stations")
    def test_google_maps_network_error_returns_502(self, mock_fetch, mock_get, client):
        """Google Maps RequestException → HTTP 502 with error='google_maps'."""
        import requests as req_lib
        mock_fetch.return_value = (_make_stations(2), "2026-05-01T00:00:00Z")
        mock_get.side_effect = req_lib.RequestException("timeout")

        resp = client.post("/api/plan", json=_VALID_BODY)

        assert resp.status_code == 502
        data = resp.get_json()
        assert data["error"] == "google_maps"
        assert "message" in data

    @patch("api.routes.fetch_stations")
    def test_regie_essence_failure_returns_502(self, mock_fetch, client):
        """fetch_stations exception → HTTP 502 with error='regie_essence'."""
        mock_fetch.side_effect = ValueError("parse failure")

        resp = client.post("/api/plan", json=_VALID_BODY)

        assert resp.status_code == 502
        data = resp.get_json()
        assert data["error"] == "regie_essence"
        assert "message" in data


# ---------------------------------------------------------------------------
# Validation — missing required fields
# ---------------------------------------------------------------------------

class TestPlanValidation:
    """400 errors for missing required fields."""

    def test_missing_origin_returns_400(self, client):
        """Missing 'origin' → 400 with error='internal'."""
        body = {k: v for k, v in _VALID_BODY.items() if k != "origin"}
        resp = client.post("/api/plan", json=body)
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "internal"

    def test_missing_destination_returns_400(self, client):
        """Missing 'destination' → 400 with error='internal'."""
        body = {k: v for k, v in _VALID_BODY.items() if k != "destination"}
        resp = client.post("/api/plan", json=body)
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "internal"

    def test_missing_range_km_returns_400(self, client):
        """Missing 'range_km' → 400 with error='internal'."""
        body = {k: v for k, v in _VALID_BODY.items() if k != "range_km"}
        resp = client.post("/api/plan", json=body)
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "internal"

    def test_empty_body_returns_400(self, client):
        """Empty body → 400 with error='internal'."""
        resp = client.post("/api/plan", json={})
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "internal"


# ---------------------------------------------------------------------------
# _format_drive_time unit tests
# ---------------------------------------------------------------------------

class TestFormatDriveTime:
    """Tests for the private _format_drive_time helper."""

    def test_exactly_two_hours(self):
        """7200 seconds = '2 h 00 min'."""
        from api.routes import _format_drive_time
        assert _format_drive_time(7200) == "2 h 00 min"

    def test_two_hours_fourteen_minutes(self):
        """8040 seconds = '2 h 14 min'."""
        from api.routes import _format_drive_time
        assert _format_drive_time(8040) == "2 h 14 min"

    def test_sub_hour(self):
        """2700 seconds = '45 min'."""
        from api.routes import _format_drive_time
        assert _format_drive_time(2700) == "45 min"

    def test_zero_seconds(self):
        """0 seconds = '0 min'."""
        from api.routes import _format_drive_time
        assert _format_drive_time(0) == "0 min"
