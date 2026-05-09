# Story 1.3: Autonomy Filtering & Recommendation Engine

## Status

done

## Story

**As a developer,**
I want the backend to filter stations by driving autonomy and compute cheapest/worst recommendations with savings,
So that the `/api/plan` endpoint (built in Epic 2) can call these pure functions without containing any inline business logic.

## Acceptance Criteria

**AC1:** Given a list of stations each with `price_per_litre` and `distance_from_origin_km`, a `range_km` value, and a `buffer_km` value, when `filter_by_autonomy(stations, range_km, buffer_km)` is called, then it returns only stations where `distance_from_origin_km <= range_km - buffer_km`; if `buffer_km` is not provided, the default is `max(range_km * 0.10, 15)` km.

**AC2:** Given a filtered list with zero stations, when `filter_by_autonomy(...)` is called, then it returns an empty list without raising an error.

**AC3:** Given a filtered list of reachable stations and a `tank_litres` value, when `build_recommendation(stations, tank_litres)` is called, then it returns a dict with: `best_station` (dict, lowest `price_per_litre`), `worst_station` (dict, highest `price_per_litre`), `savings_per_litre` (float, difference between worst and best), `savings_per_tank` (float, `savings_per_litre * tank_litres`); stations with `price_per_litre == float('inf')` are excluded from best/worst selection.

**AC4:** Given a list of per-route dicts each containing `savings_per_litre`, when `rank_routes(routes)` is called, then it returns the same list with an added `rank` integer field where rank 1 = highest `savings_per_litre` (most savings = best value).

**AC5:** Given `tests/test_pricing.py` has tests for the new functions, when `pytest tests/test_pricing.py` is run, then all tests pass; edge cases covered include: empty station list, all prices `float('inf')`, single station, two stations with identical prices, `tank_litres = 0`.

## Tasks / Subtasks

- [x] Task 1: Add `filter_by_autonomy(stations, range_km, buffer_km=None)` to `api/pricing.py`
  - [x] Default `buffer_km = max(range_km * 0.10, 15)` when not provided
  - [x] Return stations where `distance_from_origin_km <= range_km - buffer_km`
  - [x] Return empty list for empty input (no error)
- [x] Task 2: Add `build_recommendation(stations, tank_litres)` to `api/pricing.py`
  - [x] Exclude stations with `price_per_litre == float('inf')`
  - [x] Find `best_station` (min `price_per_litre`) and `worst_station` (max `price_per_litre`)
  - [x] Compute `savings_per_litre = worst.price_per_litre - best.price_per_litre`
  - [x] Compute `savings_per_tank = savings_per_litre * tank_litres`
  - [x] Return dict with all four keys; handle edge cases: all inf, single station, empty list
- [x] Task 3: Add `rank_routes(routes)` to `api/pricing.py`
  - [x] Sort by `savings_per_litre` descending (highest savings = rank 1)
  - [x] Add `rank` field (1-indexed) to each route dict
  - [x] Return the mutated list
- [x] Task 4: Add tests to `tests/test_pricing.py`
  - [x] `filter_by_autonomy`: 6 test cases including normal, default buffer, empty, all filtered
  - [x] `build_recommendation`: 7 test cases including all inf, single, identical, tank=0, empty
  - [x] `rank_routes`: 5 test cases including 3 routes, single, equal, returns same list, empty

## Dev Notes

**All functions in `api/pricing.py` — pure functions, no side effects**

**`filter_by_autonomy` signature:**
```python
def filter_by_autonomy(stations: list[dict], range_km: float, buffer_km: Optional[float] = None) -> list[dict]:
    """Return stations reachable within range_km minus safety buffer."""
```

**`build_recommendation` return schema:**
```python
{
    "best_station": dict | None,
    "worst_station": dict | None,
    "savings_per_litre": float,   # 0.0 if single station or all inf
    "savings_per_tank": float,    # 0.0 if tank_litres == 0
}
```

**`rank_routes` note:** Mutates the dicts in-place (adds `rank` key) AND returns the list for chaining. Routes with equal `savings_per_litre` can have any tie-breaking order.

**Testing conventions:**
- Use `pytest`
- No network calls — these are pure functions
- Test with `float('inf')` explicitly in assertions

## Dev Agent Record

### Implementation Plan
- Added `filter_by_autonomy()` to `api/pricing.py`: default buffer = `max(range_km * 0.10, 15)`, filters by `distance_from_origin_km <= range_km - buffer_km`
- Added `build_recommendation()`: excludes inf-priced stations, finds best/worst, computes savings; returns dict with None best/worst and 0 savings for edge cases
- Added `rank_routes()`: sorts by `savings_per_litre` descending, adds `rank` field (1-indexed), mutates in-place, returns list
- Added 18 new tests to `tests/test_pricing.py` covering all edge cases from the ACs

### Debug Log
(to be filled during implementation)

### Completion Notes
✅ All ACs satisfied:
- AC1: `filter_by_autonomy()` with explicit buffer filters correctly
- AC2: Empty station list returns `[]` without error
- AC3: `build_recommendation()` returns correct best/worst/savings; `float('inf')` stations excluded
- AC4: `rank_routes()` assigns rank 1 to highest savings_per_litre
- AC5: 34 total tests in `tests/test_pricing.py` (18 new for Story 1.3), all passing

## File List

- `api/pricing.py` (modified — added filter_by_autonomy, build_recommendation, rank_routes)
- `tests/test_pricing.py` (modified — added TestFilterByAutonomy, TestBuildRecommendation, TestRankRoutes)

## Change Log

### Review Findings

- [x] [Review][Defer] `distance_from_origin_km` missing on unannotated stations defaults to `0.0` — stations fetched before the geospatial engine (story 2.1) annotates them always pass `filter_by_autonomy`; pipeline must ensure this field is set before calling filter; deferred to story 2.1/2.2 [api/pricing.py:118] — deferred, pre-existing

- 2026-05-01: Story 1.3 implemented — filter_by_autonomy, build_recommendation, rank_routes added to api/pricing.py; 18 new tests added, 34 total passing
