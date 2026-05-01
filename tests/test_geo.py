"""
Tests for api/geo.py — polyline decoding, Haversine distance,
corridor discovery, and route distance.
"""

import polyline as polyline_lib
import pytest

from api.geo import decode_polyline, haversine, find_stations_in_corridor, distance_along_route


# ---------------------------------------------------------------------------
# Shared fixtures / constants
# ---------------------------------------------------------------------------

# Simple 3-point polyline: Montréal → mid-point → Laval
POLYLINE_POINTS = [
    {"lat": 45.5017, "lng": -73.5673},  # Montréal (origin)
    {"lat": 45.5500, "lng": -73.6400},  # Mid-route
    {"lat": 45.6066, "lng": -73.7124},  # Laval (destination)
]


# ---------------------------------------------------------------------------
# decode_polyline tests (Story 2.1 — AC1, AC3)
# ---------------------------------------------------------------------------

class TestDecodePolyline:
    """Tests for decode_polyline()."""

    def test_returns_list_of_lat_lng_dicts(self):
        """Round-trip: encode two points then decode; keys and values match."""
        encoded = polyline_lib.encode([(45.5017, -73.5673), (45.6066, -73.7124)])
        result = decode_polyline(encoded)
        assert len(result) == 2
        assert "lat" in result[0] and "lng" in result[0]
        assert abs(result[0]["lat"] - 45.5017) < 0.001
        assert abs(result[0]["lng"] - -73.5673) < 0.001

    def test_second_point_values(self):
        """Second decoded point matches the second encoded coordinate."""
        encoded = polyline_lib.encode([(45.5017, -73.5673), (45.6066, -73.7124)])
        result = decode_polyline(encoded)
        assert abs(result[1]["lat"] - 45.6066) < 0.001
        assert abs(result[1]["lng"] - -73.7124) < 0.001

    def test_values_are_floats(self):
        """lat and lng values should be Python floats."""
        encoded = polyline_lib.encode([(45.5017, -73.5673)])
        result = decode_polyline(encoded)
        assert isinstance(result[0]["lat"], float)
        assert isinstance(result[0]["lng"], float)


# ---------------------------------------------------------------------------
# haversine tests (Story 2.1 — AC2, AC3)
# ---------------------------------------------------------------------------

class TestHaversine:
    """Tests for haversine()."""

    def test_montreal_to_laval_within_tolerance(self):
        """Montréal → Laval great-circle distance should be ~16.2 km (±0.5 km tolerance)."""
        dist = haversine(45.5017, -73.5673, 45.6066, -73.7124)
        # The story spec estimated ~13.5 km; the correct Haversine result for these
        # exact coordinates is ~16.24 km. The formula is correct per standard derivation.
        assert abs(dist - 16.24) < 0.5

    def test_same_point_returns_zero(self):
        """Same point twice must return 0.0."""
        assert haversine(45.5017, -73.5673, 45.5017, -73.5673) == pytest.approx(0.0)

    def test_symmetry(self):
        """haversine(A→B) == haversine(B→A)."""
        d1 = haversine(45.5017, -73.5673, 45.6066, -73.7124)
        d2 = haversine(45.6066, -73.7124, 45.5017, -73.5673)
        assert d1 == pytest.approx(d2)

    def test_returns_float(self):
        """Return value is a float."""
        result = haversine(45.5017, -73.5673, 45.6066, -73.7124)
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# find_stations_in_corridor tests (Story 2.2 — AC1, AC2, AC4)
# ---------------------------------------------------------------------------

class TestFindStationsInCorridor:
    """Tests for find_stations_in_corridor()."""

    def _station(self, lat: float, lng: float, name: str = "Test", price: float = 1.5) -> dict:
        return {"lat": lat, "lng": lng, "name": name, "price_per_litre": price}

    def test_station_within_corridor_is_included(self):
        """A station near a polyline point should be in the result."""
        stations = [self._station(45.5500, -73.6400, "Mid-Station")]  # exactly on mid-point
        result = find_stations_in_corridor(POLYLINE_POINTS, stations, corridor_km=2.0)
        assert len(result) == 1

    def test_station_beyond_corridor_is_excluded(self):
        """A station far from the route should not appear in the result."""
        stations = [self._station(46.8139, -71.2082, "Quebec City")]
        result = find_stations_in_corridor(POLYLINE_POINTS, stations, corridor_km=2.0)
        assert len(result) == 0

    def test_empty_station_list_returns_empty(self):
        """Empty input station list should return empty list without error."""
        result = find_stations_in_corridor(POLYLINE_POINTS, [], corridor_km=2.0)
        assert result == []

    def test_station_exactly_on_polyline_point_included(self):
        """Station at exact polyline point has min distance ≈ 0 and is always included."""
        stations = [self._station(45.5500, -73.6400, "Mid-Station")]
        result = find_stations_in_corridor(POLYLINE_POINTS, stations, corridor_km=2.0)
        assert len(result) == 1
        assert result[0]["distance_from_route_km"] == pytest.approx(0.0, abs=0.01)

    def test_distance_from_route_km_field_present(self):
        """Returned station dicts include distance_from_route_km."""
        stations = [self._station(45.5500, -73.6400, "Mid-Station")]
        result = find_stations_in_corridor(POLYLINE_POINTS, stations, corridor_km=2.0)
        assert "distance_from_route_km" in result[0]

    def test_does_not_mutate_input_stations(self):
        """Original station dicts must not be modified."""
        stations = [self._station(45.5500, -73.6400, "Mid-Station")]
        find_stations_in_corridor(POLYLINE_POINTS, stations, corridor_km=2.0)
        assert "distance_from_route_km" not in stations[0]


# ---------------------------------------------------------------------------
# distance_along_route tests (Story 2.2 — AC3, AC4)
# ---------------------------------------------------------------------------

class TestDistanceAlongRoute:
    """Tests for distance_along_route()."""

    def test_station_nearest_origin_returns_zero(self):
        """Station at first polyline point → cumulative distance ≈ 0."""
        dist = distance_along_route(POLYLINE_POINTS, 45.5017, -73.5673)
        assert dist == pytest.approx(0.0, abs=0.01)

    def test_station_nearest_last_point_returns_total_length(self):
        """Station at last polyline point → ≈ total polyline length."""
        total = (
            haversine(45.5017, -73.5673, 45.5500, -73.6400)
            + haversine(45.5500, -73.6400, 45.6066, -73.7124)
        )
        dist = distance_along_route(POLYLINE_POINTS, 45.6066, -73.7124)
        assert abs(dist - total) < 0.1

    def test_station_nearest_midpoint_returns_partial_distance(self):
        """Station at mid polyline point → only first segment length."""
        first_segment = haversine(45.5017, -73.5673, 45.5500, -73.6400)
        dist = distance_along_route(POLYLINE_POINTS, 45.5500, -73.6400)
        assert abs(dist - first_segment) < 0.1

    def test_empty_polyline_returns_zero(self):
        """Empty polyline list should return 0.0 without error."""
        assert distance_along_route([], 45.5017, -73.5673) == 0.0

    def test_returns_float(self):
        """Return value is a float."""
        result = distance_along_route(POLYLINE_POINTS, 45.5500, -73.6400)
        assert isinstance(result, float)
