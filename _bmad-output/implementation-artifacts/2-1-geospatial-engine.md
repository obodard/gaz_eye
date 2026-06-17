# Story 2.1: Geospatial Engine — Polyline Decode & Haversine Distance

## Status

done

## Story

**As a developer,**
I want the geospatial functions for decoding Google Maps encoded polylines and computing Haversine distances implemented and unit-tested,
So that corridor matching has a solid, independently-verified foundation before it is wired into the API endpoint.

## Acceptance Criteria

**AC1:** Given an encoded Google Maps polyline string, when `decode_polyline(encoded_string)` is called, then it returns a list of `{"lat": float, "lng": float}` dicts representing the route path; it uses the `polyline` PyPI package (not a hand-rolled implementation); `polyline` is added to `requirements.txt`.

**AC2:** Given two lat/lng coordinate pairs, when `haversine(lat1, lng1, lat2, lng2)` is called, then it returns the great-circle distance in kilometres as a float; the result for Montréal (45.5017, -73.5673) to Laval (45.6066, -73.7124) is within ±0.5 km of the expected value (~13.5 km); passing the same point twice returns `0.0`.

**AC3:** Given `api/geo.py` exists with `decode_polyline` and `haversine`, when `pytest tests/test_geo.py` is run, then all tests pass; tests cover: `decode_polyline` round-trip with a known polyline, `haversine` known-distance pair (Montréal→Laval), `haversine` same-point edge case.

## Tasks / Subtasks

- [x] Task 1: Add `polyline` to `requirements.txt`
  - [x] Add `polyline` (no version pin, consistent with project conventions)
- [x] Task 2: Create `api/geo.py` with `decode_polyline` and `haversine`
  - [x] `decode_polyline(encoded_string)` — calls `polyline.decode(encoded_string)` and converts `(lat, lng)` tuples to `{"lat": float, "lng": float}` dicts
  - [x] `haversine(lat1, lng1, lat2, lng2)` — pure Haversine formula, Earth radius 6371 km, returns float km
  - [x] Both functions have imperative one-line docstrings
  - [x] Use built-in generics for type hints (`list[dict]`, `tuple[float, float]` — no `typing` container imports)
- [x] Task 3: Create `tests/test_geo.py`
  - [x] Test `decode_polyline` with a known encoded polyline and verify at least 2 output lat/lng values
  - [x] Test `haversine` Montréal→Laval: result within ±0.5 km of actual computed value (~16.24 km; story spec estimated 13.5 km which was incorrect for those coordinates — formula is correct)
  - [x] Test `haversine` same point both ways → `0.0`
  - [x] Test `haversine` symmetry: `haversine(A, B) == haversine(B, A)`
- [x] Task 4: Run `pytest tests/test_geo.py` and confirm all tests pass

### Review Findings

- [x] [Review][Patch] haversine math domain error for near-antipodal points [api/geo.py:27] — floating-point rounding can produce `a` slightly > 1.0 for antipodal coordinates, causing `math.asin(math.sqrt(a))` to raise `ValueError: math domain error`. Fix: clamp `a` with `min(a, 1.0)` before the sqrt.

## Dev Notes

### File to Create: `api/geo.py`

This is a **NEW** file. No existing equivalent. It sits alongside `api/pricing.py` and `api/routes.py`.

**Module responsibility (strict architecture rule):**
- `api/geo.py` owns ALL geospatial math: polyline decoding, Haversine distance, corridor matching, and route distance.
- No geospatial logic should appear in `api/routes.py` or `api/pricing.py`.
- Functions are **pure** — no network calls, no side effects, no logging.

**`decode_polyline` implementation:**

The `polyline` PyPI package (`import polyline`) provides `polyline.decode(encoded_string)` which returns a list of `(lat, lng)` tuples. Convert to the `{"lat": float, "lng": float}` dict format required by the rest of the pipeline:

```python
import polyline as _polyline

def decode_polyline(encoded_string: str) -> list[dict]:
    """Decode a Google Maps encoded polyline string into lat/lng dicts."""
    return [{"lat": float(lat), "lng": float(lng)} for lat, lng in _polyline.decode(encoded_string)]
```

**Do NOT** implement the Google Encoded Polyline Algorithm from scratch. The `polyline` package already handles this correctly. This is explicitly required by the architecture ("use the `polyline` PyPI package (not a hand-rolled implementation)").

**`haversine` implementation:**

```python
import math

EARTH_RADIUS_KM = 6371.0

def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return the great-circle distance in km between two lat/lng points."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))
```

The same-point case (`lat1==lat2, lng1==lng2`) will naturally return `0.0` — no special case needed. The formula produces `a=0 → asin(0) = 0`.

**`requirements.txt` format:**
The existing `requirements.txt` has no version pins (consistent with project rules). Add `polyline` on its own line, no version specifier.

**Type hints — CRITICAL:**
Use Python 3.9+ built-in generics. Do NOT import `List`, `Dict`, `Tuple` from `typing`:
```python
# CORRECT
def decode_polyline(encoded_string: str) -> list[dict]:

# WRONG — violates project rules
from typing import List, Dict
def decode_polyline(encoded_string: str) -> List[Dict]:
```

**Docstrings — imperative mood:**
```python
def haversine(...) -> float:
    """Return the great-circle distance in km between two lat/lng points."""
```

### File to Create: `tests/test_geo.py`

**Known encoded polyline for testing:**

Google Maps `overview_polyline.points` format. Use a short, hand-verifiable polyline:

```python
# Encodes roughly: [(45.5017, -73.5673), (45.6066, -73.7124)]
# These are Montréal and Laval approximate coordinates
MONTREAL_LAVAL_POLYLINE = "gj~tGfkrbM}qBjq@"
```

Alternatively, encode a minimal 2-point polyline in the test itself:
```python
import polyline as _polyline
encoded = _polyline.encode([(45.5017, -73.5673), (45.6066, -73.7124)])
```

**Key test assertions:**

```python
# decode_polyline: round-trip
def test_decode_polyline_returns_lat_lng_dicts():
    encoded = polyline_lib.encode([(45.5017, -73.5673), (45.6066, -73.7124)])
    result = decode_polyline(encoded)
    assert len(result) == 2
    assert "lat" in result[0] and "lng" in result[0]
    assert abs(result[0]["lat"] - 45.5017) < 0.001
    assert abs(result[0]["lng"] - -73.5673) < 0.001

# haversine: known distance
def test_haversine_montreal_to_laval():
    dist = haversine(45.5017, -73.5673, 45.6066, -73.7124)
    assert abs(dist - 13.5) < 0.5  # within ±0.5 km

# haversine: same point
def test_haversine_same_point():
    assert haversine(45.5017, -73.5673, 45.5017, -73.5673) == pytest.approx(0.0)
```

**Import pattern for test file:**
```python
import polyline as polyline_lib  # avoid name clash with module import
import pytest
from api.geo import decode_polyline, haversine
```

### Project Context Rules to Follow

- No `print()` — but these are pure functions with no output; no logging needed
- `snake_case` for all identifiers
- Functional style — standalone functions, no classes
- `EARTH_RADIUS_KM` as a module-level constant (`UPPER_CASE`) — not a magic number inline

### What NOT to Touch

- `api/pricing.py` — no changes required for this story
- `api/routes.py` — no changes required for this story
- `tests/test_pricing.py` — no changes required for this story
- `chekov.py` — must remain 100% unchanged

## Dev Agent Record

### Implementation Plan

- Created `api/geo.py` as a pure-function module with no side effects.
- Used `polyline` PyPI package for `decode_polyline`; standard Haversine formula for `haversine`.
- Both functions use Python 3.9+ built-in generics and imperative docstrings.
- Note: Story spec estimated Montréal→Laval at ~13.5 km; actual Haversine result for those coordinates is ~16.24 km. The formula implementation is correct per the standard derivation. Test updated to reflect actual value.

### Debug Log

- Initial venv had stale path (pointed to old project directory); recreated cleanly.
- `pytest` not in requirements.txt; installed separately into venv.
- Haversine distance test: story estimated ~13.5 km but actual great-circle distance for given coordinates is ~16.24 km. Verified formula correctness and updated assertion.

### Completion Notes

- `api/geo.py` created with `decode_polyline` and `haversine`.
- `polyline` added to `requirements.txt`.
- `tests/test_geo.py` created with 18 tests covering Stories 2.1 and 2.2.
- All 18 geo tests pass; all 34 existing pricing tests pass (no regressions).

## File List

- `requirements.txt` (modified — add `polyline`)
- `api/geo.py` (created — `decode_polyline`, `haversine`)
- `tests/test_geo.py` (created — tests for `decode_polyline`, `haversine`)

## Change Log

- 2026-05-01: Story 2.1 created — ready-for-dev
- 2026-05-01: Story 2.1 implemented — api/geo.py and tests/test_geo.py created; all tests pass
