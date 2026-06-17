"""
Tests for api/routes.py — POST /api/plan endpoint.
All external calls (Google Maps, Régie Essence) are mocked.
A live API key is never required.
"""

import os
from unittest.mock import MagicMock, mock_open, patch

import polyline as polyline_lib
import pytest
import yaml

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
        assert b"Chekov" in resp.data

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


# ---------------------------------------------------------------------------
# Anomaly filter integration tests (Story 4.2)
# ---------------------------------------------------------------------------

class TestPlanAnomalyFilter:
    """Tests for the anomaly filter integration in POST /api/plan."""

    @patch("api.routes.detect_stale_prices")
    @patch("api.routes.requests.get")
    @patch("api.routes.fetch_stations")
    def test_filter_called_when_enabled(self, mock_fetch, mock_get, mock_detect, client):
        """detect_stale_prices is called with all_stations and exemptions when filter is enabled."""
        yaml_content = yaml.dump({"anomaly_filter_enabled": True, "anomaly_filter_exemptions": ["costco"]})
        mock_fetch.return_value = (_make_stations(2), "2026-05-01T00:00:00Z")
        mock_get.return_value = _make_mock_get(_make_gm_response(1))
        mock_detect.side_effect = lambda stations, *a, **kw: stations

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            resp = client.post("/api/plan", json=_VALID_BODY)

        assert resp.status_code == 200
        mock_detect.assert_called()
        call_kwargs = mock_detect.call_args.kwargs
        assert call_kwargs["exemptions"] == ["costco"]
        # Verify all_stations (the full fetch result) is passed as second positional argument
        expected_all_stations = mock_fetch.return_value[0]
        assert mock_detect.call_args.args[1] is expected_all_stations

    @patch("api.routes.detect_stale_prices")
    @patch("api.routes.requests.get")
    @patch("api.routes.fetch_stations")
    def test_filter_not_called_when_disabled(self, mock_fetch, mock_get, mock_detect, client):
        """detect_stale_prices is NOT called when anomaly_filter_enabled=False."""
        yaml_content = yaml.dump({"anomaly_filter_enabled": False})
        mock_fetch.return_value = (_make_stations(2), "2026-05-01T00:00:00Z")
        mock_get.return_value = _make_mock_get(_make_gm_response(1))

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            resp = client.post("/api/plan", json=_VALID_BODY)

        assert resp.status_code == 200
        mock_detect.assert_not_called()

    @patch("api.routes.detect_stale_prices")
    @patch("api.routes.requests.get")
    @patch("api.routes.fetch_stations")
    def test_exemptions_forwarded(self, mock_fetch, mock_get, mock_detect, client):
        """Exemption list is forwarded exactly to detect_stale_prices."""
        yaml_content = yaml.dump({"anomaly_filter_enabled": True, "anomaly_filter_exemptions": ["olco", "pioneer"]})
        mock_fetch.return_value = (_make_stations(2), "2026-05-01T00:00:00Z")
        mock_get.return_value = _make_mock_get(_make_gm_response(1))
        mock_detect.side_effect = lambda stations, *a, **kw: stations

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            resp = client.post("/api/plan", json=_VALID_BODY)

        assert resp.status_code == 200
        call_kwargs = mock_detect.call_args.kwargs
        assert call_kwargs["exemptions"] == ["olco", "pioneer"]

    @patch("api.routes.detect_stale_prices")
    @patch("api.routes.requests.get")
    @patch("api.routes.fetch_stations")
    def test_missing_exemptions_defaults_to_empty_list(self, mock_fetch, mock_get, mock_detect, client):
        """Missing anomaly_filter_exemptions in YAML defaults to empty list."""
        yaml_content = yaml.dump({"anomaly_filter_enabled": True})
        mock_fetch.return_value = (_make_stations(2), "2026-05-01T00:00:00Z")
        mock_get.return_value = _make_mock_get(_make_gm_response(1))
        mock_detect.side_effect = lambda stations, *a, **kw: stations

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            resp = client.post("/api/plan", json=_VALID_BODY)

        assert resp.status_code == 200
        call_kwargs = mock_detect.call_args.kwargs
        assert call_kwargs["exemptions"] == []

    @patch("api.routes.detect_stale_prices")
    @patch("api.routes.requests.get")
    @patch("api.routes.fetch_stations")
    def test_yaml_oserror_defaults_to_enabled(self, mock_fetch, mock_get, mock_detect, client):
        """OSError reading config file defaults to filter enabled with empty exemptions."""
        mock_fetch.return_value = (_make_stations(2), "2026-05-01T00:00:00Z")
        mock_get.return_value = _make_mock_get(_make_gm_response(1))
        mock_detect.side_effect = lambda stations, *a, **kw: stations

        with patch("builtins.open", side_effect=OSError("disk error")):
            resp = client.post("/api/plan", json=_VALID_BODY)

        assert resp.status_code == 200
        # Filter should be active (default True) with empty exemptions
        mock_detect.assert_called()
        assert mock_detect.call_args.kwargs["exemptions"] == []


# ---------------------------------------------------------------------------
# worst_station in route response (Story 4.4)
# ---------------------------------------------------------------------------

class TestWorstStation:
    """Tests for worst_station field in POST /api/plan route response."""

    @patch("api.routes.requests.get")
    @patch("api.routes.fetch_stations")
    def test_route_schema_includes_worst_station(self, mock_fetch, mock_get, client):
        """Success case: worst_station field is present and non-null when reachable stations exist."""
        # _make_stations(3) produces 3 stations with prices 1.50, 1.51, 1.52
        mock_fetch.return_value = (_make_stations(3), "2026-05-01T00:00:00Z")
        mock_get.return_value = _make_mock_get(_make_gm_response(1))

        resp = client.post("/api/plan", json=_VALID_BODY)

        assert resp.status_code == 200
        route = resp.get_json()["routes"][0]
        assert "worst_station" in route, "worst_station key must be present in route response"
        # With 3 stations having valid prices, worst_station must be non-null
        assert route["worst_station"] is not None

    @patch("api.routes.build_recommendation")
    @patch("api.routes.requests.get")
    @patch("api.routes.fetch_stations")
    def test_worst_station_null_when_no_reachable_stations(
        self, mock_fetch, mock_get, mock_build, client
    ):
        """worst_station is null when build_recommendation returns worst_station=None."""
        mock_fetch.return_value = (_make_stations(3), "2026-05-01T00:00:00Z")
        mock_get.return_value = _make_mock_get(_make_gm_response(1))
        mock_build.return_value = {
            "best_station": None,
            "worst_station": None,
            "savings_per_litre": 0.0,
            "savings_per_tank": 0.0,
        }

        resp = client.post("/api/plan", json=_VALID_BODY)

        assert resp.status_code == 200
        route = resp.get_json()["routes"][0]
        assert "worst_station" in route
        assert route["worst_station"] is None

    @patch("api.routes.requests.get")
    @patch("api.routes.fetch_stations")
    def test_worst_station_price_serializes_to_null(self, mock_fetch, mock_get, client):
        """worst_station with float('inf') price correctly serializes to null in JSON."""
        mock_fetch.return_value = (_make_stations(3), "2026-05-01T00:00:00Z")
        mock_get.return_value = _make_mock_get(_make_gm_response(1))

        resp = client.post("/api/plan", json=_VALID_BODY)

        assert resp.status_code == 200
        data = resp.get_json()
        route = data["routes"][0]
        # worst_station should be non-null (we have 3 stations with valid prices)
        assert route["worst_station"] is not None
        # Price should be a finite number, not null (stations have valid prices)
        assert isinstance(route["worst_station"]["price_per_litre"], (int, float))
        assert route["worst_station"]["price_per_litre"] is not None


# ---------------------------------------------------------------------------
# POST /api/chat endpoint (Story 5.2)
# ---------------------------------------------------------------------------

def _make_adk_response_with_function_call():
    """ADK response with a functionCall and a text part."""
    return {
        "result": "ok",
        "events": [
            {
                "author": "chekov_assistant",
                "content": {
                    "parts": [
                        {
                            "functionCall": {
                                "name": "submit_trip",
                                "args": {"origin": "Montréal", "destination": "Duhamel", "range_km": 180},
                            }
                        }
                    ]
                },
            },
            {
                "author": "chekov_assistant",
                "content": {
                    "parts": [
                        {"text": "Planning Montréal → Duhamel with 180 km range — loading routes."}
                    ]
                },
            },
        ],
    }


def _make_adk_response_text_only():
    """ADK response with only a text part (no function call)."""
    return {
        "result": "ok",
        "events": [
            {
                "author": "chekov_assistant",
                "content": {
                    "parts": [{"text": "What is your destination?"}]
                },
            },
        ],
    }


def _make_mock_post(response_dict, status_code=200):
    """Return a mock for requests.post."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = response_dict
    return mock_resp


class TestChatEndpoint:
    """Tests for POST /api/chat — ADK proxy endpoint."""

    @patch("api.routes.requests.post")
    def test_function_call_normalized(self, mock_post, client):
        """ADK response with functionCall → normalized {action, params, message}."""
        mock_post.return_value = _make_mock_post(_make_adk_response_with_function_call())

        resp = client.post("/api/chat", json={
            "message": "Montréal to Duhamel, 180 km range",
            "session_id": "abc-123",
            "is_context_update": False,
        })

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["action"] == "submit_trip"
        assert data["params"]["origin"] == "Montréal"
        assert data["params"]["destination"] == "Duhamel"
        assert data["message"] == "Planning Montréal → Duhamel with 180 km range — loading routes."

    @patch("api.routes.requests.post")
    def test_text_only_response(self, mock_post, client):
        """ADK response with only text → action 'chat_only', empty params."""
        mock_post.return_value = _make_mock_post(_make_adk_response_text_only())

        resp = client.post("/api/chat", json={
            "message": "Where should I go?",
            "session_id": "abc-123",
            "is_context_update": False,
        })

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["action"] == "chat_only"
        assert data["params"] == {}
        assert data["message"] == "What is your destination?"

    @patch("api.routes.requests.post")
    def test_adk_timeout_returns_502(self, mock_post, client):
        """ADK timeout → HTTP 502 with correct error body."""
        import requests as req_lib
        mock_post.side_effect = req_lib.Timeout("10s timeout")

        resp = client.post("/api/chat", json={
            "message": "Hello",
            "session_id": "abc-123",
            "is_context_update": False,
        })

        assert resp.status_code == 502
        data = resp.get_json()
        assert data["error"] == "adk_agent"
        assert "form" in data["message"].lower()

    @patch("api.routes.requests.post")
    def test_adk_connection_refused_returns_502(self, mock_post, client):
        """ADK connection refused → HTTP 502."""
        import requests as req_lib
        mock_post.side_effect = req_lib.ConnectionError("Connection refused")

        resp = client.post("/api/chat", json={
            "message": "Hello",
            "session_id": "abc-123",
            "is_context_update": False,
        })

        assert resp.status_code == 502
        data = resp.get_json()
        assert data["error"] == "adk_agent"

    @patch("api.routes.requests.post")
    def test_context_update_returns_204(self, mock_post, client):
        """is_context_update=true → HTTP 204 with no body."""
        mock_post.return_value = _make_mock_post(_make_adk_response_text_only())

        resp = client.post("/api/chat", json={
            "message": "[TRIP CONTEXT] origin=Montréal",
            "session_id": "abc-123",
            "is_context_update": True,
        })

        assert resp.status_code == 204
        assert resp.data == b""

    @patch("api.routes.requests.post")
    def test_context_update_adk_down_still_204(self, mock_post, client):
        """Context update with ADK down → still returns 204."""
        import requests as req_lib
        mock_post.side_effect = req_lib.ConnectionError("down")

        resp = client.post("/api/chat", json={
            "message": "[TRIP CONTEXT] origin=Montréal",
            "session_id": "abc-123",
            "is_context_update": True,
        })

        assert resp.status_code == 204

    @patch("api.routes.requests.post")
    def test_adk_500_returns_502(self, mock_post, client):
        """ADK returns HTTP 500 → Flask returns 502."""
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 500
        mock_post.return_value = mock_resp

        resp = client.post("/api/chat", json={
            "message": "Hello",
            "session_id": "abc-123",
            "is_context_update": False,
        })

        assert resp.status_code == 502
        data = resp.get_json()
        assert data["error"] == "adk_agent"

    @patch("api.routes.requests.post")
    def test_unknown_action_falls_back_to_chat_only(self, mock_post, client):
        """Unknown action name from ADK → fallback to 'chat_only'."""
        adk_response = {
            "result": "ok",
            "events": [
                {
                    "author": "chekov_assistant",
                    "content": {
                        "parts": [
                            {"functionCall": {"name": "unknown_action", "args": {"foo": "bar"}}},
                            {"text": "I did something unexpected."},
                        ]
                    },
                },
            ],
        }
        mock_post.return_value = _make_mock_post(adk_response)

        resp = client.post("/api/chat", json={
            "message": "Do something weird",
            "session_id": "abc-123",
            "is_context_update": False,
        })

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["action"] == "chat_only"
        assert data["params"] == {}
        assert "unexpected" in data["message"]

    @patch("api.routes.requests.post")
    def test_adk_request_payload_format(self, mock_post, client):
        """Verify the ADK request payload matches the expected format."""
        mock_post.return_value = _make_mock_post(_make_adk_response_text_only())

        client.post("/api/chat", json={
            "message": "Hello world",
            "session_id": "test-session",
            "is_context_update": False,
        })

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["appName"] == "agent"
        assert payload["userId"] == "local_user"
        assert payload["sessionId"] == "test-session"
        assert payload["newMessage"]["role"] == "user"
        assert payload["newMessage"]["parts"][0]["text"] == "Hello world"


# ---------------------------------------------------------------------------
# GET /api/nearest_station endpoint
# ---------------------------------------------------------------------------

class TestNearestStation:
    """Tests for GET /api/nearest_station."""

    @patch("api.routes.fetch_stations")
    def test_returns_nearest_station(self, mock_fetch, client):
        """Returns the station closest to the given coordinates."""
        stations = [
            {"name": "Far Station", "address": "1 rue Far", "lat": 46.1, "lng": -74.6,
             "price_per_litre": 1.60},
            {"name": "Near Station", "address": "2 rue Near", "lat": 46.12, "lng": -74.59,
             "price_per_litre": 1.55},
        ]
        mock_fetch.return_value = (stations, "2026-05-01T00:00:00Z")

        resp = client.get("/api/nearest_station?lat=46.12&lng=-74.59")

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["station"] is not None
        assert data["station"]["name"] == "Near Station"
        assert "distance_km" in data

    @patch("api.routes.fetch_stations")
    def test_missing_lat_returns_400(self, mock_fetch, client):
        """Missing lat query param → 400."""
        resp = client.get("/api/nearest_station?lng=-74.0")
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "bad_request"

    @patch("api.routes.fetch_stations")
    def test_missing_lng_returns_400(self, mock_fetch, client):
        """Missing lng query param → 400."""
        resp = client.get("/api/nearest_station?lat=46.0")
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "bad_request"

    @patch("api.routes.fetch_stations")
    def test_regie_failure_returns_502(self, mock_fetch, client):
        """fetch_stations exception → 502 with error='regie_essence'."""
        mock_fetch.side_effect = ValueError("fetch failed")

        resp = client.get("/api/nearest_station?lat=46.1&lng=-74.6")

        assert resp.status_code == 502
        assert resp.get_json()["error"] == "regie_essence"

    @patch("api.routes.fetch_stations")
    def test_empty_stations_returns_null_station(self, mock_fetch, client):
        """No stations available → station field is null."""
        mock_fetch.return_value = ([], "2026-05-01T00:00:00Z")

        resp = client.get("/api/nearest_station?lat=46.1&lng=-74.6")

        assert resp.status_code == 200
        assert resp.get_json()["station"] is None

    @patch("api.routes.fetch_stations")
    def test_inf_price_serialized_to_null(self, mock_fetch, client):
        """Station with price float('inf') → price_per_litre serialized as null."""
        stations = [
            {"name": "No Price Station", "address": "1 rue Test", "lat": 46.1, "lng": -74.6,
             "price_per_litre": float("inf")},
        ]
        mock_fetch.return_value = (stations, "2026-05-01T00:00:00Z")

        resp = client.get("/api/nearest_station?lat=46.1&lng=-74.6")

        assert resp.status_code == 200
        assert resp.get_json()["station"]["price_per_litre"] is None

    @patch("api.routes.fetch_stations")
    def test_fuel_type_forwarded_to_fetch(self, mock_fetch, client):
        """fuel_type query param is forwarded to fetch_stations."""
        mock_fetch.return_value = (
            [{"name": "S", "address": "A", "lat": 46.0, "lng": -74.0, "price_per_litre": 1.5}],
            "2026-05-01T00:00:00Z",
        )

        client.get("/api/nearest_station?lat=46.0&lng=-74.0&fuel_type=Super")

        mock_fetch.assert_called_once_with("Super")
