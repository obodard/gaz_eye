# Story 2.2: Station Corridor Discovery & Route Distance

## Status

done

## Story

**As a developer,**
I want the system to find all Quebec stations within a configurable corridor of a route polyline and calculate each station's cumulative distance from the trip origin,
So that the autonomy filter in `pricing.py` receives correctly-distanced stations to work with.

## Acceptance Criteria

**AC1:** Given a list of decoded route polyline points, a list of all Quebec stations (each with `lat`, `lng`), and a `corridor_km` value, when `find_stations_in_corridor(polyline_points, all_stations, corridor_km)` is called, then it returns only stations where the minimum Haversine distance to any polyline point is ≤ `corridor_km`; each returned station includes a `distance_from_route_km` field with that minimum distance.

**AC2:** Given an empty station list, when `find_stations_in_corridor(polyline_points, [], corridor_km)` is called, then it returns an empty list without error.

**AC3:** Given a list of decoded route polyline points and a station lat/lng, when `distance_along_route(polyline_points, station_lat, station_lng)` is called, then it returns the cumulative sum of polyline segment lengths (km) up to the segment point nearest to the station; this is NOT a straight-line distance from origin — it is the sum of Haversine segment distances along the polyline.

**AC4:** Given `pytest tests/test_geo.py` is run after these functions are added, then new tests pass covering: station exactly on polyline (included), station beyond corridor (excluded), empty station list, `distance_along_route` for station nearest first point (≈0), nearest last point (≈total route length), and a midpoint station.

## Tasks / Subtasks

- [x] Task 1: Add `find_stations_in_corridor(polyline_points, all_stations, corridor_km)` to `api/geo.py`
  - [x] For each station, compute min Haversine distance across all polyline points
  - [x] Include station if min distance ≤ `corridor_km`
  - [x] Add `distance_from_route_km` field (the min distance value, rounded to 4 decimal places) to each returned station dict — return a copy, do not mutate the input
  - [x] Return empty list for empty input without error
- [x] Task 2: Add `distance_along_route(polyline_points, station_lat, station_lng)` to `api/geo.py`
  - [x] Find the index of the nearest polyline point to the station using Haversine
  - [x] Sum Haversine distances for all consecutive point pairs from index 0 up to (but not including) the nearest point index
  - [x] Return float km (cumulative polyline path distance, NOT straight-line from origin)
  - [x] Edge case: station nearest first point → returns 0.0
- [x] Task 3: Add new tests to `tests/test_geo.py`
  - [x] `find_stations_in_corridor`: station within corridor (included + distance_from_route_km present)
  - [x] `find_stations_in_corridor`: station beyond corridor (excluded)
  - [x] `find_stations_in_corridor`: empty station list → `[]`
  - [x] `find_stations_in_corridor`: station exactly on a polyline point (min distance ≈ 0, always included)
  - [x] `distance_along_route`: station nearest first point → `≈ 0.0`
  - [x] `distance_along_route`: station nearest last point → `≈ total route length`
  - [x] `distance_along_route`: station nearest midpoint → partial cumulative distance
- [x] Task 4: Run `pytest tests/test_geo.py` and confirm all tests (old + new) pass

### Review Findings

- [x] [Review][Patch] `find_stations_in_corridor` raises ValueError on empty polyline_points with a non-empty station list [api/geo.py:34] — `min(generator)` raises `ValueError: min() arg is an empty sequence` when `polyline_points=[]` but stations are present. `distance_along_route` guards this case; `find_stations_in_corridor` does not. Fix: add `if not polyline_points: return []` at the top of the function.

## Dev Notes

### File to Modify: `api/geo.py`

This story **extends** `api/geo.py` (created in Story 2.1). Do NOT recreate the file. Import `haversine` from within the same module:

```python
# At the top of api/geo.py, after the existing imports and functions:
# haversine() and decode_polyline() already exist — use them directly
```

**`find_stations_in_corridor` implementation:**

```python
def find_stations_in_corridor(
    polyline_points: list[dict],
    all_stations: list[dict],
    corridor_km: float,
) -> list[dict]:
    """Return stations within corridor_km of any polyline point, with distance_from_route_km added."""
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
```

**Critical: Do NOT mutate the input station dicts.** Use `dict(station)` to create a shallow copy before adding `distance_from_route_km`. The input `all_stations` list is reused across multiple routes — mutating it would cause the second route to receive stale `distance_from_route_km` values from the first route.

**`distance_along_route` implementation:**

```python
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

    # Find index of nearest polyline point
    nearest_idx = min(
        range(len(polyline_points)),
        key=lambda i: haversine(station_lat, station_lng, polyline_points[i]["lat"], polyline_points[i]["lng"]),
    )

    # Sum segment lengths from index 0 to nearest_idx
    cumulative = 0.0
    for i in range(nearest_idx):
        cumulative += haversine(
            polyline_points[i]["lat"], polyline_points[i]["lng"],
            polyline_points[i + 1]["lat"], polyline_points[i + 1]["lng"],
        )
    return cumulative
```

**Why cumulative polyline distance matters:**
The Google Maps polyline is a path — a station that is 50 km along the road from the origin may be geometrically only 20 km in straight-line distance. Using straight-line distance from origin would mislead the autonomy filter. The `distance_from_origin_km` returned here represents "how far has the driver already traveled before reaching the nearest refueling opportunity on this route."

**Performance consideration (NFR4):**
The full Quebec GeoJSON has ~3,000+ stations. For each route with ~100+ polyline points, the naive O(stations × points) loop completes comfortably within the 1-second NFR4 budget for a 300 km route in pure Python. No optimization (spatial index, numpy) is needed for MVP.

### File to Modify: `tests/test_geo.py`

**Test setup — build a simple 3-point polyline for testing:**

```python
# Use a simple L-shaped route: Montréal → (mid) → Laval
POLYLINE_POINTS = [
    {"lat": 45.5017, "lng": -73.5673},  # Montréal (origin)
    {"lat": 45.5500, "lng": -73.6400},  # Mid-route
    {"lat": 45.6066, "lng": -73.7124},  # Laval (destination)
]
```

**Corridor test: station exactly on a polyline point:**
```python
def test_find_stations_in_corridor_includes_exact_match():
    stations = [{"lat": 45.5500, "lng": -73.6400, "name": "Mid-Station", "price_per_litre": 1.5}]
    result = find_stations_in_corridor(POLYLINE_POINTS, stations, corridor_km=2.0)
    assert len(result) == 1
    assert result[0]["distance_from_route_km"] == pytest.approx(0.0, abs=0.01)
```

**Corridor test: station far from route:**
```python
def test_find_stations_in_corridor_excludes_distant_station():
    stations = [{"lat": 46.8139, "lng": -71.2082, "name": "Quebec City", "price_per_litre": 1.6}]
    result = find_stations_in_corridor(POLYLINE_POINTS, stations, corridor_km=2.0)
    assert len(result) == 0
```

**Mutation safety — verify input stations are not modified:**
```python
def test_find_stations_in_corridor_does_not_mutate_input():
    stations = [{"lat": 45.5500, "lng": -73.6400, "name": "Test", "price_per_litre": 1.5}]
    find_stations_in_corridor(POLYLINE_POINTS, stations, corridor_km=2.0)
    assert "distance_from_route_km" not in stations[0]  # original dict unchanged
```

**Distance along route: station nearest first point:**
```python
def test_distance_along_route_nearest_origin():
    # Station at Montréal (first point) → cumulative distance = 0
    dist = distance_along_route(POLYLINE_POINTS, 45.5017, -73.5673)
    assert dist == pytest.approx(0.0, abs=0.01)
```

**Distance along route: station nearest last point → ≈ total route length:**
```python
def test_distance_along_route_nearest_last_point():
    # Station at Laval (last point) → should be ≈ total polyline length
    total_length = (
        haversine(45.5017, -73.5673, 45.5500, -73.6400)
        + haversine(45.5500, -73.6400, 45.6066, -73.7124)
    )
    dist = distance_along_route(POLYLINE_POINTS, 45.6066, -73.7124)
    assert abs(dist - total_length) < 0.1
```

### Reminder: Input Station Dict Schema

Stations coming from `fetch_stations()` in `api/pricing.py` have this shape:
```python
{
    "name": str,
    "address": str,
    "lat": float,
    "lng": float,
    "price_per_litre": float,
}
```

`find_stations_in_corridor` receives this input and adds `distance_from_route_km`. The subsequent `distance_along_route` call in `api/routes.py` (Story 2.3) will add `distance_from_origin_km` to each corridor station before autonomy filtering.

### What NOT to Touch

- `api/pricing.py` — no changes required
- `api/routes.py` — no changes required
- `tests/test_pricing.py` — no changes required
- `checkov.py` — must remain 100% unchanged
- The existing `decode_polyline` and `haversine` tests in `tests/test_geo.py` — do not delete or modify them

## Dev Agent Record

### Implementation Plan

- Extended `api/geo.py` (created in 2.1) with `find_stations_in_corridor` and `distance_along_route`.
- Both functions are pure, use `haversine` internally from the same module.
- Input mutation safety enforced via `dict(station)` shallow copy in `find_stations_in_corridor`.
- Tests implemented in the same `tests/test_geo.py` file alongside 2.1 tests.

### Debug Log

- All functions implemented concurrently with Story 2.1 since `api/geo.py` was a new file in both stories.

### Completion Notes

- `api/geo.py` extended with `find_stations_in_corridor` and `distance_along_route`.
- 7 new tests added to `tests/test_geo.py` (mutation safety, corridor inclusion/exclusion, route distance edge cases).
- All 18 tests in `tests/test_geo.py` pass; no regressions in `tests/test_pricing.py`.

## File List

- `api/geo.py` (modified — add `find_stations_in_corridor`, `distance_along_route`)
- `tests/test_geo.py` (modified — add corridor and route distance tests)

## Change Log

- 2026-05-01: Story 2.2 created — ready-for-dev
- 2026-05-01: Story 2.2 implemented — corridor functions added to api/geo.py; all tests pass
