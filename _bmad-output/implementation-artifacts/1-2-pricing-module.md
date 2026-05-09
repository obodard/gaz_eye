# Story 1.2: Pricing Module — GeoJSON Fetch & Price Parsing

## Status

done

## Story

**As a developer,**
I want the Régie Essence GeoJSON fetch and price parsing logic extracted from `gaz_saver.py` into an importable `api/pricing.py` module,
So that the backend can programmatically access live Quebec gas station data and prices without depending on the CLI entry point.

## Acceptance Criteria

**AC1:** Given `api/pricing.py` is imported, when `fetch_stations(fuel_type)` is called, then it returns a list of station dicts from the Régie Essence GeoJSON endpoint, each containing at minimum `Address`, `Latitude`, `Longitude`, and the relevant price field for the given fuel type; the function sends a browser-like `User-Agent` header; it handles both pre-decompressed JSON and raw gzip responses (dual-parse); on network failure it raises an exception (not `sys.exit()`); stations with `IsAvailable: false` or missing price data have their price represented as `float('inf')`.

**AC2:** Given a raw price string `"154.9¢"`, when `parse_price_value("154.9¢")` is called, then it returns `1.549` (float, dollars per litre).

**AC3:** Given a missing or `None` price value, when `parse_price_value(None)` or `parse_price_value("")` is called, then it returns `float('inf')` as the sentinel value.

**AC4:** Given `gaz_saver.py` exists after the extraction, when it is run directly (`python gaz_saver.py`), then it still works correctly — the module extraction does not break the existing CLI.

**AC5:** Given `tests/test_pricing.py` exists, when `pytest tests/test_pricing.py` is executed, then all tests pass; `requests.get` is mocked throughout — the live Régie Essence endpoint is never called; tests cover `parse_price_value` with: valid cent-string, `None`, empty string, `¢`-only string, and a string without `¢`.

## Tasks / Subtasks

- [x] Task 1: Create `api/pricing.py` with `fetch_stations(fuel_type)` and `parse_price_value(value)` 
  - [x] `parse_price_value(value)` — accepts a raw string (e.g. `"154.9¢"`) or `None`; strips `¢`, divides by 100; returns `float('inf')` for `None`, empty, or non-parseable input
  - [x] `fetch_stations(fuel_type)` — fetches GeoJSON from `GEOJSON_URL`, dual-parse (try `json.loads()` first, fall back to `gzip.decompress()`), sends browser-like `User-Agent`, raises exception on failure (no `sys.exit()`); returns list of station dicts with `Address`, `Latitude`, `Longitude`, `price_per_litre` (parsed float), `name`, `lat`, `lng`
  - [x] Stations with `IsAvailable: false` or missing/null price → `price_per_litre = float('inf')`
  - [x] Extract metadata `generated_at` from response root and return it as second value
- [x] Task 2: Ensure `gaz_saver.py` still works after extraction
  - [x] Verified `gaz_saver.py` uses its own local `fetch_stations()` (unchanged)
- [x] Task 3: Create `tests/__init__.py` and `tests/test_pricing.py`
  - [x] Tests for `parse_price_value`: all 8 cases covered
  - [x] Tests for `fetch_stations`: happy path, IsAvailable=false, missing fuel type, network exception propagation, gzip fallback, User-Agent header, empty features, brand='Aucun'
  - [x] Never calls live endpoint
- [x] Task 4: Run tests and verify all pass

## Dev Notes

**Extraction Strategy:**
- `api/pricing.py` is a NEW module — it does NOT import from `gaz_saver.py`
- `gaz_saver.py` stays 100% unchanged — it keeps its own copy of `fetch_stations` (which calls `sys.exit()`) and `parse_price_value`
- The new `api/pricing.py` version of `fetch_stations` RAISES exceptions instead of calling `sys.exit()` — this is the key behavioral difference
- The new `parse_price_value` takes a raw string (NOT a dict/price_entry like in gaz_saver.py) — simpler interface for the API use case

**`parse_price_value` signature in `api/pricing.py`:**
```python
def parse_price_value(price_str: Optional[str]) -> float:
    """Parse a cent-string price (e.g. '154.9¢') to dollars per litre."""
```

**`fetch_stations` return format:**
Each station dict should contain:
```python
{
    "name": str,          # brand + partial address or fallback
    "address": str,       # full Address from GeoJSON
    "lat": float,
    "lng": float,
    "price_per_litre": float,   # parsed dollars, or float('inf')
}
```
Also return `data_timestamp` (the `generated_at` string from GeoJSON metadata).

**GeoJSON price field structure:**  
The `Prices` array in each feature has objects with `GasType` and `Price` fields.
Filter for the matching `fuel_type` (e.g. `"Régulier"`). Use `IsAvailable` to gate.

**Testing conventions (from project-context.md):**
- `pytest` as test runner
- Tests in `tests/` directory at project root
- Test files named `test_<module>.py`
- Mock `requests.get` — never hit live endpoint

## Dev Agent Record

### Implementation Plan
- Created `api/pricing.py` as a new independent module (does NOT import from `gaz_saver.py`)
- `parse_price_value(price_str)` takes a raw string, strips `¢`/unicode cent, divides by 100; returns `float('inf')` on None/empty/non-numeric
- `fetch_stations(fuel_type)` returns `(stations_list, data_timestamp)` tuple; raises on network error (no sys.exit); dual-parse gzip/JSON; User-Agent header set
- `gaz_saver.py` unchanged — still has its own `fetch_stations` that calls `sys.exit()`
- Created `tests/__init__.py` and `tests/test_pricing.py` with 16 tests; all mocked via `unittest.mock.patch`

### Debug Log
(to be filled during implementation)

### Completion Notes
✅ All ACs satisfied:
- AC1: `fetch_stations()` returns list with required fields, sends User-Agent, dual-parse, raises exceptions
- AC2: `parse_price_value("154.9¢")` → 1.549
- AC3: `parse_price_value(None)` and `parse_price_value("")` → `float('inf')`
- AC4: `gaz_saver.py` unchanged (git diff clean, parses without error)
- AC5: 16 tests in `tests/test_pricing.py`, all passing, no live network calls

## File List

- `api/pricing.py` (created)
- `tests/__init__.py` (created)
- `tests/test_pricing.py` (created)

## Change Log

### Review Findings

- [x] [Review][Decision] Station dict key naming conflict — **dismissed**: lowercase `address`/`lat`/`lng` is correct per dev notes and project-context.md; AC1 text was imprecise (referenced raw GeoJSON field names, not output schema)
- [x] [Review][Patch] Duplicate `StreamHandler` registered on every module import [api/pricing.py:18-24]
- [x] [Review][Patch] GeoJSON `null` geometry/properties/prices causes `AttributeError` [api/pricing.py:87-99]
- [x] [Review][Patch] Corrupt or invalid response body unhandled after gzip fallback [api/pricing.py:74-79]
- [x] [Review][Patch] `"nan¢"` and negative prices pass as valid, corrupting recommendations [api/pricing.py:49-55]
- [x] [Review][Patch] Top-level JSON array from endpoint crashes `fetch_stations` [api/pricing.py:73]
- [x] [Review][Patch] `test_user_agent_header_sent` uses fragile multi-path header extraction [tests/test_pricing.py:193-199]
- [x] [Review][Defer] `float('inf')` is not JSON serializable — stations with unavailable prices will crash `json.dumps` when the `/api/plan` endpoint serializes them; needs to be filtered or replaced before the API response layer; deferred to story 2.3 [api/pricing.py] — deferred, pre-existing

- 2026-05-01: Story 1.2 implemented — api/pricing.py created with fetch_stations and parse_price_value; tests/test_pricing.py with 16 passing tests
