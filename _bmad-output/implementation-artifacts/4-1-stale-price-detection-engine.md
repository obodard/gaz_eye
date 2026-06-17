# Story 4.1: Stale Price Detection Engine

Status: review

## Story

As a developer,
I want a pure `detect_stale_prices()` function in `api/pricing.py` that uses a density-adaptive spatial median to identify and exclude stale-priced stations,
so that the recommendation pipeline silently filters out Régie listings that are anomalously cheap relative to their geographic neighbors before any recommendation is built.

## Acceptance Criteria

**AC1:** Given `api/pricing.py` is imported, when the module is inspected, then the constant `ANOMALY_THRESHOLD_CAD = 0.05` is defined at module level — not hardcoded inside any function and not duplicated elsewhere.

**AC2:** Given a list of all Quebec stations (`all_stations`) each with `lat`, `lng`, and `price_per_litre` fields, a candidate station, a `threshold` value (default `ANOMALY_THRESHOLD_CAD`), and an empty exemption list, when `detect_stale_prices(corridor_stations, all_stations, threshold, exemptions)` is called, then it returns a copy of `corridor_stations` where any station priced more than `threshold` below its local geographic median has its `price_per_litre` set to `float('inf')`, and the original station dicts in `all_stations` are not mutated.

**AC3:** Given a candidate station and the `all_stations` dataset, when the density-adaptive radius logic runs inside `detect_stale_prices()`, then it searches for neighbors at 5 km, then 10 km, then 20 km, then 50 km — stopping at the first radius that yields ≥5 neighbors (excluding the candidate itself). If fewer than 5 neighbors are found within 50 km, the station bypasses the filter entirely (its price is left unchanged).

**AC4:** Given a station where the local median price is 155.0¢/L and the station's price is 149.5¢/L (5.5¢/L below median, exceeding the 5¢/L default threshold), when `detect_stale_prices()` processes this station, then that station's `price_per_litre` is set to `float('inf')` in the returned list.

**AC5:** Given a station where the local median price is 155.0¢/L and the station's price is 150.5¢/L (4.5¢/L below median, under the default threshold), when `detect_stale_prices()` processes this station, then that station's `price_per_litre` is unchanged.

**AC6:** Given a station already having `price_per_litre == float('inf')` (price unavailable), when `detect_stale_prices()` processes it, then it is left unchanged — stations with no price data bypass the anomaly filter.

**AC7:** Given `tests/test_pricing.py` contains tests for `detect_stale_prices()`, when `pytest tests/test_pricing.py` is run, then all tests pass. Tests must cover:
- Station excluded at the default 5¢/L threshold (5 km neighbor radius)
- Station kept because it is only 4¢/L below median
- Station bypassed because fewer than 5 neighbors within 50 km
- Station bypassed because `price_per_litre == float('inf')`
- Density expansion: station has 3 neighbors at 5 km but ≥5 at 10 km — 10 km radius is used
- Empty `corridor_stations` list returns an empty list without error
- `all_stations` list is not mutated after the call

**AC8:** Given the full Quebec dataset (~3,000 stations) is passed as `all_stations`, when `detect_stale_prices()` processes it, then total wall-clock time is < 100ms; no external calls are made — all computation is in-memory using `haversine()` from `api/geo.py`.

## Tasks / Subtasks

- [x] Task 1: Add `ANOMALY_THRESHOLD_CAD` constant to `api/pricing.py` (AC1)
  - [x] Add `ANOMALY_THRESHOLD_CAD = 0.05` at module level, after the existing module-level constants (`GEOJSON_URL`, `_HEADERS`)
  - [x] Do NOT hardcode `0.05` inside the function — the constant is the single source of truth

- [x] Task 2: Implement `detect_stale_prices()` in `api/pricing.py` (AC2, AC3, AC4, AC5, AC6, AC8)
  - [x] Function signature: `def detect_stale_prices(corridor_stations: list[dict[str, Any]], all_stations: list[dict[str, Any]], threshold: float = ANOMALY_THRESHOLD_CAD, exemptions: list[str] = None) -> list[dict[str, Any]]:`
  - [x] Treat `exemptions=None` as an empty list inside the function (avoid mutable default argument)
  - [x] Return an independent copy of `corridor_stations` — use `dict(s)` for each station dict; do NOT mutate `all_stations` or the original dicts
  - [x] For each station in `corridor_stations`:
    - If `price_per_litre == float('inf')`: skip filter, copy as-is
    - If station name matches any exemption substring (case-insensitive `.lower() in name.lower()`): skip filter, copy as-is
    - Otherwise: run density-adaptive neighbor search
  - [x] Density-adaptive radius search:
    - `_RADII = [5.0, 10.0, 20.0, 50.0]`
    - For each radius in `_RADII`: collect all stations in `all_stations` (excluding the candidate itself by identity or by lat/lng equality) with `price_per_litre != float('inf')` and `haversine(candidate.lat, candidate.lng, neighbor.lat, neighbor.lng) <= radius`
    - Stop at first radius yielding ≥5 neighbors
    - If no radius yields ≥5 neighbors: skip filter, copy as-is
  - [x] Compute `local_median`: use `statistics.median()` on the neighbor `price_per_litre` values
  - [x] If `local_median - station['price_per_litre'] > threshold`: set copied station's `price_per_litre` to `float('inf')` in the result
  - [x] Import `statistics` from stdlib (already available — no new dependencies)
  - [x] Import `haversine` from `api.geo` — use the existing implementation, do NOT reimplement

- [x] Task 3: Write tests for `detect_stale_prices()` in `tests/test_pricing.py` (AC7)
  - [x] Add import: `from api.pricing import detect_stale_prices`
  - [x] Add `class TestDetectStalePrices:` after existing test classes
  - [x] `test_station_excluded_at_threshold`: build 6 neighbors at ~4.5km, price=1.55; candidate price=1.494 (5.1¢ below); assert result station `price_per_litre == float('inf')`
  - [x] `test_station_kept_below_threshold`: same neighbors; candidate price=1.506 (4.9¢ below); assert unchanged
  - [x] `test_station_bypassed_insufficient_neighbors`: only 3 stations within 50km; assert station price unchanged
  - [x] `test_station_bypassed_inf_price`: station has `price_per_litre=float('inf')`; assert returned unchanged
  - [x] `test_density_expansion_to_10km`: 3 neighbors at 4km (< 5); 5 more neighbors at 9km (≥5 at 10km radius); verify 10km radius is used (median computed over the ≥5 set)
  - [x] `test_empty_corridor_returns_empty`: call with `corridor_stations=[]`; assert result is `[]`
  - [x] `test_all_stations_not_mutated`: call with a known stale station; assert `all_stations` list dicts are identical before and after
  - [ ] Do NOT mock `haversine` — keep tests using real distance calculations with constructed lat/lng coordinates

## Dev Notes

### Files to Modify

| File | Change |
|------|--------|
| `api/pricing.py` | **UPDATE**: add `ANOMALY_THRESHOLD_CAD` constant + `detect_stale_prices()` function |
| `tests/test_pricing.py` | **UPDATE**: add `TestDetectStalePrices` class with 7 tests |

### Current State of `api/pricing.py`

The module already provides:
- `parse_price_value(price_str)` — parses cent-strings to dollar floats, returns `float('inf')` on bad input
- `fetch_stations(fuel_type)` — fetches and parses the full Régie Essence GeoJSON; returns `(stations, data_timestamp)`
- `filter_by_autonomy(stations, range_km, buffer_km)` — filters by reachable distance
- `build_recommendation(stations, tank_litres)` — finds cheapest/worst with savings
- `rank_routes(routes)` — ranks routes by savings

Module-level structure:
```python
# module docstring
# imports: gzip, json, logging, math, sys, typing.Any/Optional, requests
logger = logging.getLogger("chekov.pricing")
# logger setup block
GEOJSON_URL = "..."
_HEADERS = { ... }
# functions follow
```

Insert `ANOMALY_THRESHOLD_CAD = 0.05` immediately after `_HEADERS`, before the first function definition. Import `statistics` in the stdlib imports group (alphabetically between `math` and `sys`). Add `from api.geo import haversine` in the local imports group (new group at the bottom of imports).

### Haversine is Already Implemented in `api/geo.py`

`haversine(lat1, lng1, lat2, lng2) -> float` — returns km distance between two points. Do NOT copy or reimplement. Import it.

```python
# api/geo.py excerpt (read-only reference)
def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return the great-circle distance in km between two lat/lng points."""
    # Haversine formula — EARTH_RADIUS_KM = 6371.0
```

### Median Calculation

Use `statistics.median(values)` from the Python stdlib. It handles both odd and even-length lists correctly. The list to pass is `[s['price_per_litre'] for s in neighbors]` — all neighbors are already guaranteed to have `price_per_litre != float('inf')` (filtered during collection).

### No New Dependencies

All required modules (`statistics`, `math`) are Python stdlib. `haversine` is already in the project. Do NOT add any new entries to `requirements.txt`.

### Performance Note (NFR11: < 100ms)

The naïve approach — for each of N corridor stations, scan all ~3,000 stations at up to 4 radii — is O(N × 3000 × 4). For N ≤ ~50 corridor stations this is ≤ 600,000 Haversine calls, each taking ~1µs, totalling ~600ms — too slow.

**Optimization strategy:** Pre-filter `all_stations` to those with valid prices once before the outer loop. The inner radius loop short-circuits on first radius meeting the threshold, so average cost is much lower. For ~3,000 total stations and typical Quebec geography, radius=5km will find ≥5 neighbors for most stations (Quebec cities are dense), so the expansion to 10/20/50km is rarely needed. This brings the typical case well under 100ms.

**If still too slow:** Consider sorting stations by lat and using a lat-band pre-filter (± radius / 111.0 degrees latitude) before computing Haversine for candidates. Only implement this if actual timing shows >100ms in testing.

### Existing Test Patterns in `tests/test_pricing.py`

The test file already imports `pytest`, `MagicMock`, `patch`, `json`, `gzip` and has helpers:
- `_make_geojson(features, generated_at)` — builds a GeoJSON dict
- `_make_station_feature(...)` — builds a GeoJSON feature dict
- `_mock_response(data, status)` — builds a mock `requests.Response`

For `TestDetectStalePrices`, build station dicts directly (not via GeoJSON features):
```python
{"name": "Station X", "lat": 45.5, "lng": -73.5, "price_per_litre": 1.55}
```

### Project Context Rules to Follow

- Use built-in generics: `list[dict[str, Any]]` — NOT `List[Dict]`
- Import only `Any` and `Optional` from `typing` (not container types)
- Use `snake_case` for function names
- Every function must have a one-line docstring (imperative mood)
- No `print()` — but `detect_stale_prices()` does NOT log; logging happens in Story 4.2 at the route handler level

### References

- [Source: api/pricing.py] — full current implementation (UPDATE target)
- [Source: api/geo.py] — `haversine()` function to import
- [Source: tests/test_pricing.py] — existing test patterns and import block
- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.1] — AC source
- [Source: _bmad-output/project-context.md] — project coding rules

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6

### Debug Log References

### Completion Notes List

- Added `import statistics` (stdlib) and `from api.geo import haversine` imports to `api/pricing.py`
- Added `ANOMALY_THRESHOLD_CAD = 0.05` constant at module level after `_HEADERS`
- Implemented `detect_stale_prices()` with density-adaptive radii [5, 10, 20, 50 km], pre-filtering valid_pool for performance, using `dict(s)` shallow copies to avoid mutation
- Exemptions and inf-price bypass implemented as specified
- `_RADII` list defined as module-level private constant
- 7 tests in `TestDetectStalePrices` — all pass; existing 34 pricing tests unaffected
- `data_timestamp` parameter added in Story 4.2 (signature remains backward-compatible via default `""`)

### File List

- `api/pricing.py` — Added `import statistics`, `from api.geo import haversine`, `ANOMALY_THRESHOLD_CAD`, `_RADII`, `detect_stale_prices()`
- `tests/test_pricing.py` — Added `detect_stale_prices` to imports; added `TestDetectStalePrices` class with 7 tests

### Change Log

- 2026-05-01: Implemented Story 4.1 — Stale Price Detection Engine. Added `ANOMALY_THRESHOLD_CAD` constant, `detect_stale_prices()` function with density-adaptive spatial median filter, and 7 unit tests. All 41 pricing tests pass.

### Review Findings

**Adversarial Review (2026-05-09) — 3 Patches Applied:**

- [x] [Review][Patch] Type annotation `list[str] = None` violates type-checker rules; should be `Optional[list[str]] = None` [api/pricing.py:196] — Applied: changed signature to `Optional[list[str]] = None`
- [x] [Review][Patch] Negative threshold values (e.g., `-0.05`) pass unvalidated, silently excluding all stations [api/pricing.py — detect_stale_prices entry] — Applied: added guard `if threshold < 0: raise ValueError(f"threshold must be non-negative, got {threshold}")`
- [x] [Review][Patch] Floating-point equality `s["lat"] == station["lat"]` vulnerable to precision loss from external API data; co-located stations may be silently included as self in neighbor pool [api/pricing.py:232] — Applied: changed to `math.isclose(s["lat"], station["lat"], abs_tol=1e-8) and math.isclose(s["lng"], station["lng"], abs_tol=1e-8)`

**Original Pre-Review Findings (Already Implemented):**

- [x] [Review][Patch] `None` in exemptions list causes `AttributeError` in detect_stale_prices [api/pricing.py — exemption-check loop] — `exc.lower()` crashes if a YAML null appears in the list; guard with `isinstance(exc, str)`
- [x] [Review][Patch] `station_copy['name']` KeyError in exclusion log f-string [api/pricing.py — logger.info call] — use `station_copy.get('name', '<unknown>')` to avoid crash on stations without a name key
- [x] [Review][Defer] Coordinate equality self-exclusion may drop co-located stations from neighbor pool [api/pricing.py — neighbor candidate filter] — deferred, pre-existing and spec-compliant (`by identity or by lat/lng equality`)
- [x] [Review][Defer] `price_per_litre=None` in station dict not guarded in valid_pool comprehension [api/pricing.py — valid_pool] — deferred, unreachable with current `fetch_stations()` data source
- [x] [Review][Defer] O(C×N×K) linear haversine scan without spatial indexing [api/pricing.py — detect_stale_prices] — deferred, acceptable for current dataset size; revisit if >50 corridor stations observed
- [x] [Review][Defer] `test_all_stations_not_mutated` does not assert that `corridor_stations` input dicts are also unchanged [tests/test_pricing.py] — deferred, shallow-copy guarantee is already tested for all_stations; corridor_stations test adds limited marginal value
