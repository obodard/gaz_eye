"""
Tests for api/pricing.py — price parsing and GeoJSON fetch.
All network calls are mocked; the live endpoint is never called.
"""

import gzip
import json
from unittest.mock import MagicMock, patch

import pytest

from api.pricing import (
    detect_stale_prices,
    fetch_stations,
    filter_by_autonomy,
    build_recommendation,
    parse_price_value,
    rank_routes,
)


# ---------------------------------------------------------------------------
# parse_price_value tests
# ---------------------------------------------------------------------------

class TestParsePriceValue:
    """Tests for the parse_price_value() helper."""

    def test_valid_cent_string(self):
        """'154.9¢' should parse to 1.549."""
        assert parse_price_value("154.9¢") == pytest.approx(1.549)

    def test_unicode_cent_symbol(self):
        """Unicode cent symbol (U+00A2) should also be stripped."""
        assert parse_price_value("154.9\u00a2") == pytest.approx(1.549)

    def test_none_returns_inf(self):
        """None input should return float('inf')."""
        assert parse_price_value(None) == float('inf')

    def test_empty_string_returns_inf(self):
        """Empty string should return float('inf')."""
        assert parse_price_value("") == float('inf')

    def test_cent_symbol_only_returns_inf(self):
        """A '¢'-only string should return float('inf') (no numeric part)."""
        assert parse_price_value("¢") == float('inf')

    def test_string_without_cent_symbol(self):
        """A numeric string without '¢' is treated as cents and divided by 100."""
        # e.g. "154.9" → 1.549
        assert parse_price_value("154.9") == pytest.approx(1.549)

    def test_non_numeric_returns_inf(self):
        """A non-numeric string should return float('inf')."""
        assert parse_price_value("n/a") == float('inf')

    def test_zero_price(self):
        """'0¢' should parse to 0.0."""
        assert parse_price_value("0¢") == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Helpers to build mock GeoJSON responses
# ---------------------------------------------------------------------------

def _make_geojson(features: list, generated_at: str = "2026-05-01T00:00:00Z") -> dict:
    """Build a minimal GeoJSON structure for testing."""
    return {
        "type": "FeatureCollection",
        "metadata": {"generated_at": generated_at, "total_stations": len(features)},
        "features": features,
    }


def _make_station_feature(
    address: str = "123 rue Test, Montréal",
    brand: str = "Ultramar",
    lat: float = 45.5,
    lng: float = -73.5,
    gas_type: str = "Régulier",
    price: str = "154.9¢",
    is_available: bool = True,
) -> dict:
    """Build a minimal GeoJSON feature for a station."""
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lng, lat]},
        "properties": {
            "Address": address,
            "brand": brand,
            "Prices": [
                {"GasType": gas_type, "Price": price, "IsAvailable": is_available}
            ],
        },
    }


def _mock_response(data: dict, status: int = 200) -> MagicMock:
    """Return a mock requests.Response for the given dict."""
    mock = MagicMock()
    mock.status_code = status
    mock.content = json.dumps(data).encode("utf-8")
    mock.raise_for_status = MagicMock()
    return mock


# ---------------------------------------------------------------------------
# fetch_stations tests
# ---------------------------------------------------------------------------

class TestFetchStations:
    """Tests for fetch_stations()."""

    @patch("api.pricing.requests.get")
    def test_happy_path_returns_station_list(self, mock_get):
        """fetch_stations returns a list of station dicts with required fields."""
        feature = _make_station_feature(
            address="123 rue Test, Montréal",
            brand="Ultramar",
            lat=45.5,
            lng=-73.5,
            price="154.9¢",
        )
        geojson = _make_geojson([feature], generated_at="2026-05-01T12:00:00Z")
        mock_get.return_value = _mock_response(geojson)

        stations, timestamp = fetch_stations("Régulier")

        assert len(stations) == 1
        s = stations[0]
        assert s["address"] == "123 rue Test, Montréal"
        assert s["lat"] == pytest.approx(45.5)
        assert s["lng"] == pytest.approx(-73.5)
        assert s["price_per_litre"] == pytest.approx(1.549)
        assert "name" in s
        assert timestamp == "2026-05-01T12:00:00Z"

    @patch("api.pricing.requests.get")
    def test_station_not_available_gets_inf_price(self, mock_get):
        """Stations with IsAvailable=false should have price_per_litre=float('inf')."""
        feature = _make_station_feature(price="154.9¢", is_available=False)
        geojson = _make_geojson([feature])
        mock_get.return_value = _mock_response(geojson)

        stations, _ = fetch_stations("Régulier")

        assert len(stations) == 1
        assert stations[0]["price_per_litre"] == float('inf')

    @patch("api.pricing.requests.get")
    def test_station_missing_price_gets_inf(self, mock_get):
        """Stations with no matching fuel type get price_per_litre=float('inf')."""
        feature = _make_station_feature(gas_type="Super", price="159.9¢")
        geojson = _make_geojson([feature])
        mock_get.return_value = _mock_response(geojson)

        stations, _ = fetch_stations("Régulier")  # asking for Régulier but only Super exists

        assert len(stations) == 1
        assert stations[0]["price_per_litre"] == float('inf')

    @patch("api.pricing.requests.get")
    def test_network_exception_propagates(self, mock_get):
        """fetch_stations should propagate RequestException, not swallow it."""
        import requests as req_lib
        mock_get.side_effect = req_lib.RequestException("timeout")

        with pytest.raises(req_lib.RequestException):
            fetch_stations("Régulier")

    @patch("api.pricing.requests.get")
    def test_gzip_fallback_parsing(self, mock_get):
        """fetch_stations falls back to gzip.decompress if json.loads fails."""
        feature = _make_station_feature(price="160.0¢")
        geojson = _make_geojson([feature])
        raw_bytes = gzip.compress(json.dumps(geojson).encode("utf-8"))

        mock = MagicMock()
        mock.status_code = 200
        mock.content = raw_bytes
        mock.raise_for_status = MagicMock()
        mock_get.return_value = mock

        stations, _ = fetch_stations("Régulier")

        assert len(stations) == 1
        assert stations[0]["price_per_litre"] == pytest.approx(1.60)

    @patch("api.pricing.requests.get")
    def test_user_agent_header_sent(self, mock_get):
        """fetch_stations must send a browser-like User-Agent header."""
        geojson = _make_geojson([])
        mock_get.return_value = _mock_response(geojson)

        fetch_stations("Régulier")

        headers = mock_get.call_args.kwargs["headers"]
        assert "User-Agent" in headers
        assert "Mozilla" in headers["User-Agent"]

    @patch("api.pricing.requests.get")
    def test_empty_features_returns_empty_list(self, mock_get):
        """An empty features array returns an empty station list."""
        geojson = _make_geojson([])
        mock_get.return_value = _mock_response(geojson)

        stations, _ = fetch_stations("Régulier")

        assert stations == []

    @patch("api.pricing.requests.get")
    def test_brand_aucun_uses_address_as_name(self, mock_get):
        """Stations with brand='Aucun' should use address as name."""
        feature = _make_station_feature(brand="Aucun", address="456 boul. Test")
        geojson = _make_geojson([feature])
        mock_get.return_value = _mock_response(geojson)

        stations, _ = fetch_stations("Régulier")

        assert stations[0]["name"] == "456 boul. Test"


# ---------------------------------------------------------------------------
# filter_by_autonomy tests
# ---------------------------------------------------------------------------

def _make_station(distance_km: float, price: float = 1.50) -> dict:
    """Build a minimal station dict for filter/recommendation tests."""
    return {
        "name": "Test Station",
        "address": "Test",
        "lat": 45.0,
        "lng": -73.0,
        "price_per_litre": price,
        "distance_from_origin_km": distance_km,
    }


class TestFilterByAutonomy:
    """Tests for filter_by_autonomy()."""

    def test_normal_case_with_explicit_buffer(self):
        """Stations within range - buffer are included; those beyond are excluded."""
        # range=200, buffer=30 → threshold = 170 km
        # stations at 80, 100, 120 all within 170 → included
        # station at 180 is beyond threshold → excluded
        stations = [_make_station(80.0), _make_station(100.0), _make_station(120.0), _make_station(180.0)]
        result = filter_by_autonomy(stations, range_km=200, buffer_km=30)
        distances = [s["distance_from_origin_km"] for s in result]
        assert 80.0 in distances
        assert 100.0 in distances
        assert 120.0 in distances
        assert 180.0 not in distances  # 180 > 170 threshold → excluded

    def test_correct_threshold(self):
        """Stations at exactly the threshold are included; beyond are excluded."""
        stations = [_make_station(170.0), _make_station(171.0)]
        result = filter_by_autonomy(stations, range_km=200, buffer_km=30)
        assert len(result) == 1
        assert result[0]["distance_from_origin_km"] == 170.0

    def test_default_buffer_is_10_percent_or_15km_whichever_greater(self):
        """Default buffer = max(range * 0.10, 15). For range=200, buffer=20."""
        stations = [_make_station(179.0), _make_station(181.0)]
        result = filter_by_autonomy(stations, range_km=200)  # buffer = max(20, 15) = 20, threshold = 180
        assert len(result) == 1
        assert result[0]["distance_from_origin_km"] == 179.0

    def test_default_buffer_minimum_15km(self):
        """For range=100, buffer = max(10, 15) = 15."""
        stations = [_make_station(84.0), _make_station(86.0)]
        result = filter_by_autonomy(stations, range_km=100)  # buffer=15, threshold=85
        assert len(result) == 1
        assert result[0]["distance_from_origin_km"] == 84.0

    def test_empty_stations_returns_empty(self):
        """Empty input returns empty list without error."""
        result = filter_by_autonomy([], range_km=200, buffer_km=20)
        assert result == []

    def test_all_filtered_out_returns_empty(self):
        """All stations beyond range return empty list."""
        stations = [_make_station(200.0), _make_station(250.0)]
        result = filter_by_autonomy(stations, range_km=100, buffer_km=20)
        assert result == []


# ---------------------------------------------------------------------------
# build_recommendation tests
# ---------------------------------------------------------------------------

class TestBuildRecommendation:
    """Tests for build_recommendation()."""

    def test_normal_case_two_stations(self):
        """Best is cheapest, worst is most expensive; savings are correct."""
        stations = [_make_station(50.0, price=1.40), _make_station(80.0, price=1.60)]
        rec = build_recommendation(stations, tank_litres=50)
        assert rec["best_station"]["price_per_litre"] == pytest.approx(1.40)
        assert rec["worst_station"]["price_per_litre"] == pytest.approx(1.60)
        assert rec["savings_per_litre"] == pytest.approx(0.20)
        assert rec["savings_per_tank"] == pytest.approx(10.0)

    def test_all_inf_prices(self):
        """All inf prices → best/worst are None, savings are 0."""
        stations = [_make_station(50.0, price=float('inf')), _make_station(80.0, price=float('inf'))]
        rec = build_recommendation(stations, tank_litres=50)
        assert rec["best_station"] is None
        assert rec["worst_station"] is None
        assert rec["savings_per_litre"] == 0.0
        assert rec["savings_per_tank"] == 0.0

    def test_single_station(self):
        """Single station → best == worst, savings = 0."""
        stations = [_make_station(50.0, price=1.50)]
        rec = build_recommendation(stations, tank_litres=50)
        assert rec["best_station"]["price_per_litre"] == pytest.approx(1.50)
        assert rec["worst_station"]["price_per_litre"] == pytest.approx(1.50)
        assert rec["savings_per_litre"] == pytest.approx(0.0)
        assert rec["savings_per_tank"] == pytest.approx(0.0)

    def test_identical_prices(self):
        """Two stations with identical prices → savings = 0."""
        stations = [_make_station(50.0, price=1.50), _make_station(80.0, price=1.50)]
        rec = build_recommendation(stations, tank_litres=50)
        assert rec["savings_per_litre"] == pytest.approx(0.0)

    def test_tank_litres_zero(self):
        """tank_litres=0 → savings_per_tank = 0 regardless of prices."""
        stations = [_make_station(50.0, price=1.40), _make_station(80.0, price=1.60)]
        rec = build_recommendation(stations, tank_litres=0)
        assert rec["savings_per_litre"] == pytest.approx(0.20)
        assert rec["savings_per_tank"] == pytest.approx(0.0)

    def test_empty_station_list(self):
        """Empty station list → None best/worst, 0 savings."""
        rec = build_recommendation([], tank_litres=50)
        assert rec["best_station"] is None
        assert rec["worst_station"] is None
        assert rec["savings_per_litre"] == 0.0
        assert rec["savings_per_tank"] == 0.0

    def test_inf_stations_excluded_from_selection(self):
        """Mixed inf and valid stations — inf excluded, best/worst from valid ones only."""
        stations = [
            _make_station(50.0, price=float('inf')),
            _make_station(60.0, price=1.40),
            _make_station(70.0, price=1.60),
        ]
        rec = build_recommendation(stations, tank_litres=50)
        assert rec["best_station"]["price_per_litre"] == pytest.approx(1.40)
        assert rec["worst_station"]["price_per_litre"] == pytest.approx(1.60)


# ---------------------------------------------------------------------------
# rank_routes tests
# ---------------------------------------------------------------------------

class TestRankRoutes:
    """Tests for rank_routes()."""

    def test_three_routes_ranked_correctly(self):
        """Route with highest savings_per_litre gets rank 1."""
        routes = [
            {"label": "A", "savings_per_litre": 0.05},
            {"label": "B", "savings_per_litre": 0.20},
            {"label": "C", "savings_per_litre": 0.10},
        ]
        result = rank_routes(routes)
        ranked = {r["label"]: r["rank"] for r in result}
        assert ranked["B"] == 1
        assert ranked["C"] == 2
        assert ranked["A"] == 3

    def test_single_route_gets_rank_1(self):
        """Single route always gets rank 1."""
        routes = [{"label": "A", "savings_per_litre": 0.05}]
        result = rank_routes(routes)
        assert result[0]["rank"] == 1

    def test_equal_savings(self):
        """Routes with equal savings all get valid ranks (1-indexed, no gaps)."""
        routes = [
            {"label": "A", "savings_per_litre": 0.10},
            {"label": "B", "savings_per_litre": 0.10},
        ]
        result = rank_routes(routes)
        ranks = sorted(r["rank"] for r in result)
        assert ranks == [1, 2]

    def test_returns_same_list(self):
        """rank_routes returns the same list object (mutates in-place)."""
        routes = [{"label": "A", "savings_per_litre": 0.10}]
        result = rank_routes(routes)
        assert result is routes

    def test_empty_routes(self):
        """Empty routes list returns empty list without error."""
        result = rank_routes([])
        assert result == []


# ---------------------------------------------------------------------------
# detect_stale_prices tests
# ---------------------------------------------------------------------------

class TestDetectStalePrices:
    """Tests for detect_stale_prices() — density-adaptive spatial median filter."""

    def _st(self, lat: float, lng: float, price: float, name: str = "Station") -> dict:
        """Build a minimal station dict."""
        return {"name": name, "lat": lat, "lng": lng, "price_per_litre": price}

    def test_station_excluded_at_threshold(self):
        """Station 5.6¢ below local median is excluded (price set to float('inf'))."""
        # 6 neighbors clustered at ~1.1 km (0.01° lat offset), price=1.55
        neighbors = [self._st(45.51 + i * 0.001, -73.5, 1.55) for i in range(6)]
        candidate = self._st(45.5, -73.5, 1.494)  # 1.55 - 1.494 = 0.056 > 0.05
        result = detect_stale_prices([candidate], neighbors + [candidate])
        assert result[0]["price_per_litre"] == float("inf")

    def test_station_kept_below_threshold(self):
        """Station 4.4¢ below local median is kept (under threshold)."""
        neighbors = [self._st(45.51 + i * 0.001, -73.5, 1.55) for i in range(6)]
        candidate = self._st(45.5, -73.5, 1.506)  # 1.55 - 1.506 = 0.044 < 0.05
        result = detect_stale_prices([candidate], neighbors + [candidate])
        assert result[0]["price_per_litre"] == pytest.approx(1.506)

    def test_station_bypassed_insufficient_neighbors(self):
        """Station with fewer than 5 neighbors within 50 km bypasses the filter."""
        # 3 neighbors at ~11 km (0.1° lat offset), only 3 < 5 — filter never activates
        neighbors = [self._st(45.5 + (i + 1) * 0.1, -73.5, 1.55) for i in range(3)]
        candidate = self._st(45.5, -73.5, 1.40)  # would be flagged if enough neighbors existed
        result = detect_stale_prices([candidate], neighbors + [candidate])
        assert result[0]["price_per_litre"] == pytest.approx(1.40)

    def test_station_bypassed_inf_price(self):
        """Station with price_per_litre=float('inf') bypasses the filter unchanged."""
        neighbors = [self._st(45.51 + i * 0.001, -73.5, 1.55) for i in range(6)]
        candidate = self._st(45.5, -73.5, float("inf"))
        result = detect_stale_prices([candidate], neighbors + [candidate])
        assert result[0]["price_per_litre"] == float("inf")

    def test_density_expansion_to_10km(self):
        """3 neighbors within 5 km → expand; 8 neighbors at 10 km → median used."""
        # 3 neighbors at ~4 km (0.036° lat ≈ 4 km), price=1.55
        close = [self._st(45.536 + i * 0.001, -73.5, 1.55) for i in range(3)]
        # 5 neighbors at ~9 km (0.081° lat ≈ 9 km), price=1.55
        far = [self._st(45.581 + i * 0.001, -73.5, 1.55) for i in range(5)]
        candidate = self._st(45.5, -73.5, 1.494)  # 5.6¢ below median of 1.55
        result = detect_stale_prices([candidate], close + far + [candidate])
        # 10 km radius gives 8 neighbors (≥5) → station is excluded
        assert result[0]["price_per_litre"] == float("inf")

    def test_empty_corridor_returns_empty(self):
        """Empty corridor_stations returns [] without error."""
        all_stations = [self._st(45.5, -73.5, 1.55)]
        result = detect_stale_prices([], all_stations)
        assert result == []

    def test_all_stations_not_mutated(self):
        """all_stations dicts are not mutated after a call that excludes a station."""
        neighbors = [self._st(45.51 + i * 0.001, -73.5, 1.55) for i in range(6)]
        candidate = self._st(45.5, -73.5, 1.494)
        all_stations = neighbors + [candidate]
        original_prices = [s["price_per_litre"] for s in all_stations]
        detect_stale_prices([candidate], all_stations)
        assert [s["price_per_litre"] for s in all_stations] == original_prices
