# Story 4.2: Exemptions, Kill Switch & Route Pipeline Integration

Status: review

## Story

As a developer,
I want `stations.yaml` to carry the anomaly filter configuration, and the `/api/plan` route to invoke `detect_stale_prices()` at the correct pipeline position with full exemption, kill-switch, and logging support,
so that the filter operates transparently on every trip query, can exclude structural discounters legitimately, and can be disabled in seconds without a code deploy.

## Acceptance Criteria

**AC1:** Given `stations.yaml` is opened, when the file is inspected, then it contains two new top-level keys:
- `anomaly_filter_enabled: true` (boolean, default `true`)
- `anomaly_filter_exemptions: ["costco", "olco"]` (list of lowercase name substrings)
And the existing `cities`, `settings` structure is completely unchanged.

**AC2:** Given `detect_stale_prices()` is called with a non-empty `exemptions` list and a station whose name contains "Costco" (any case), when the function runs, then that station is not excluded regardless of its price relative to neighbors — exemption matching is case-insensitive substring matching.

**AC3:** Given `anomaly_filter_enabled: true` in `stations.yaml` and a trip is requested via `POST /api/plan`, when the route handler in `api/routes.py` processes the request, then `detect_stale_prices()` is called **after** `find_stations_in_corridor()` and **before** `filter_by_autonomy()` — this ordering is mandatory. The `all_stations` full dataset (not just corridor stations) is passed as the second argument.

**AC4:** Given `anomaly_filter_enabled: false` in `stations.yaml` and a trip is requested, when the route handler processes the request, then `detect_stale_prices()` is NOT called — the pipeline proceeds directly from corridor matching to `filter_by_autonomy()`. No code deploy is required to toggle this behaviour; editing `stations.yaml` is sufficient.

**AC5:** Given `detect_stale_prices()` excludes a station (sets its price to `float('inf')`), when the `chekov.pricing` logger emits the exclusion entry, then the log message contains all of: station name, station `price_per_litre` (dollars, before exclusion), local median price (dollars), neighbor count used, radius used (km), and the Régie Essence `data_timestamp`. The log is emitted at `INFO` level — it does not appear in the API response body.

**AC6:** Given `api/routes.py` loads filter config from `stations.yaml`, when `anomaly_filter_exemptions` is missing from `stations.yaml`, then the route handler defaults to an empty exemptions list and continues without error.

**AC7:** Given `tests/test_routes.py` is run after this story, when `pytest tests/test_routes.py` is executed, then all existing tests continue to pass. New tests cover:
- Filter active (`anomaly_filter_enabled: true`): `detect_stale_prices()` is called with correct arguments (mocked)
- Filter disabled (`anomaly_filter_enabled: false`): `detect_stale_prices()` is NOT called
- Exemption list forwarded correctly to `detect_stale_prices()` when present in config
- Missing `anomaly_filter_exemptions` key defaults to empty list without error

## Tasks / Subtasks

- [x] Task 1: Add filter config keys to `stations.yaml` (AC1)
  - [x] Add `anomaly_filter_enabled: true` as a new top-level key, after the `settings` list
  - [x] Add `anomaly_filter_exemptions: ["costco", "olco"]` as a new top-level key immediately after `anomaly_filter_enabled`
  - [x] Preserve all existing content exactly (`cities`, `settings`, comments, encoding)

- [x] Task 2: Extend `detect_stale_prices()` in `api/pricing.py` to emit structured log (AC5)
  - [x] Add `data_timestamp: str = ""` as a new final parameter to `detect_stale_prices()`
  - [x] Inside the function, when a station is excluded, emit an INFO log via `logger` with all required fields
  - [x] `original_price` captures `station_copy['price_per_litre']` BEFORE setting it to `float('inf')`
  - [x] Do NOT change the function's return value or any existing behavior

- [x] Task 3: Update `api/routes.py` to load filter config and integrate `detect_stale_prices()` (AC3, AC4, AC6)
  - [x] Added `import yaml` and `from pathlib import Path` imports
  - [x] Extended pricing import to include `detect_stale_prices`
  - [x] Added `_CONFIG_PATH = Path(__file__).parent.parent / "stations.yaml"` constant
  - [x] Filter config loaded per-request inside `plan()` with OSError fallback
  - [x] `detect_stale_prices()` called after corridor annotation, before `filter_by_autonomy()`

- [x] Task 4: Write tests for filter integration in `tests/test_routes.py` (AC7)
  - [x] Added `TestPlanAnomalyFilter` class with 4 tests
  - [x] `test_filter_called_when_enabled` — verifies call and exemptions kwarg
  - [x] `test_filter_not_called_when_disabled` — verifies no call when disabled
  - [x] `test_exemptions_forwarded` — verifies list forwarded correctly
  - [x] `test_missing_exemptions_defaults_to_empty_list` — verifies empty list default

## Dev Notes

### Files to Modify

| File | Change |
|------|--------|
| `stations.yaml` | **UPDATE**: add `anomaly_filter_enabled` and `anomaly_filter_exemptions` top-level keys |
| `api/pricing.py` | **UPDATE**: extend `detect_stale_prices()` signature with `data_timestamp` + add exclusion logging |
| `api/routes.py` | **UPDATE**: add imports, `_CONFIG_PATH` constant, filter config loading, and conditional pipeline call |
| `tests/test_routes.py` | **UPDATE**: add `TestPlanAnomalyFilter` class with 4 tests |

### Depends on Story 4.1

Story 4.1 must be complete before this story. `detect_stale_prices()` must already exist in `api/pricing.py` with signature:
```python
def detect_stale_prices(
    corridor_stations: list[dict[str, Any]],
    all_stations: list[dict[str, Any]],
    threshold: float = ANOMALY_THRESHOLD_CAD,
    exemptions: list[str] = None,
) -> list[dict[str, Any]]:
```
This story adds `data_timestamp: str = ""` as a final keyword parameter. Existing callers without this parameter remain valid (default `""`).

### Current State of `stations.yaml`

The file has this structure (end of file):
```yaml
settings:
  - tank_litres: 50
  - gaz_type: "Régulier" # "Régulier" | "Super" | "Diesel"
```

Append the two new keys after `settings`:
```yaml
anomaly_filter_enabled: true
anomaly_filter_exemptions: ["costco", "olco"]
```

No existing keys are touched.

### Current Pipeline Ordering in `api/routes.py`

The current per-route processing loop in `plan()` is:
```python
corridor_stations = find_stations_in_corridor(polyline_pts, all_stations, corridor_km)
for s in corridor_stations:
    s["distance_from_origin_km"] = round(
        distance_along_route(polyline_pts, s["lat"], s["lng"]), 2
    )

reachable = filter_by_autonomy(corridor_stations, range_km, buffer_km)
```

**Required new ordering (insert between annotation and autonomy filter):**
```python
corridor_stations = find_stations_in_corridor(polyline_pts, all_stations, corridor_km)
for s in corridor_stations:
    s["distance_from_origin_km"] = round(
        distance_along_route(polyline_pts, s["lat"], s["lng"]), 2
    )

# Anomaly filter: must run AFTER corridor matching, BEFORE autonomy filtering
if anomaly_filter_enabled:
    corridor_stations = detect_stale_prices(
        corridor_stations,
        all_stations,
        exemptions=anomaly_filter_exemptions,
        data_timestamp=data_timestamp,
    )

reachable = filter_by_autonomy(corridor_stations, range_km, buffer_km)
```

The `distance_from_origin_km` annotation must happen BEFORE `detect_stale_prices()` so that the corridor stations passed to the filter already have this field populated (future proofing for any filter logic that might need it).

### Loading `stations.yaml` Per-Request

`stations.yaml` is read on each `POST /api/plan` request. This allows toggling `anomaly_filter_enabled` without restarting Flask. The file is small (~40 lines) and disk I/O cost is negligible relative to the network calls.

`_CONFIG_PATH = Path(__file__).parent.parent / "stations.yaml"` resolves correctly because:
- `__file__` = `.../api/routes.py`
- `parent` = `.../api/`
- `parent.parent` = `.../{project-root}/`

If the file is missing (e.g., testing), the `OSError` handler defaults to `{}` (filter disabled, empty exemptions). This makes tests easier: mock the file open or patch `_yaml_cfg` directly.

### How to Test Filter Integration in `test_routes.py`

The cleanest approach is to patch both the yaml file read and `detect_stale_prices`:

```python
@patch("api.routes.detect_stale_prices")
@patch("builtins.open", mock_open(read_data=yaml.dump({"anomaly_filter_enabled": True, "anomaly_filter_exemptions": ["costco"]})))
@patch("api.routes.requests.get")
@patch("api.routes.fetch_stations")
def test_filter_called_when_enabled(self, mock_fetch, mock_get, mock_detect, client):
    mock_fetch.return_value = (_make_stations(2), "2026-05-01T00:00:00Z")
    mock_get.return_value = _make_mock_get(_make_gm_response(1))
    mock_detect.side_effect = lambda stations, *a, **kw: stations  # pass-through

    resp = client.post("/api/plan", json=_VALID_BODY)
    assert resp.status_code == 200
    mock_detect.assert_called()
    _, call_all_stations = mock_detect.call_args[0][:2]
    # all_stations = the full fetch_stations result
```

Alternative: patch `api.routes.yaml.safe_load` to return a fixed dict. Either approach is acceptable. Do NOT assert on the exact number of calls (one per route) if the number of routes is variable.

### Existing Import Line to Extend in `api/routes.py`

Current line:
```python
from api.pricing import fetch_stations, filter_by_autonomy, build_recommendation, rank_routes
```

Change to:
```python
from api.pricing import fetch_stations, filter_by_autonomy, build_recommendation, rank_routes, detect_stale_prices
```

### Logging Format for Exclusion

Use the existing `chekov.pricing` logger (already defined in `api/pricing.py`). The log message format:
```
Stale price excluded: Station Petro-Canada | price=1.485 | median=1.553 | neighbors=8 | radius=5km | ts=2026-05-01T00:00:00Z
```

This matches the module's existing logging style: `%(message)s` format only, no timestamps or levels prepended by the formatter.

### Project Context Rules to Follow

- Use built-in generics: `list[dict[str, Any]]` — NOT `List[Dict]`
- Use f-strings exclusively — no `.format()` or `%` interpolation
- `encoding="utf-8"` on all file opens (station names contain French accents)
- `snake_case` for all new variable names
- No `print()` — use `logger.info()` for the exclusion log only; no other new logging is needed
- Every new function or modified function retains its one-line docstring

### References

- [Source: api/routes.py#plan()] — full current pipeline (UPDATE target)
- [Source: api/pricing.py#detect_stale_prices()] — function from Story 4.1 (UPDATE target)
- [Source: stations.yaml] — current config structure (UPDATE target)
- [Source: tests/test_routes.py] — existing test classes and helpers (UPDATE target)
- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.2] — AC source
- [Source: _bmad-output/project-context.md] — project coding rules

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6

### Debug Log References

### Completion Notes List

- Added `anomaly_filter_enabled: true` and `anomaly_filter_exemptions: ["costco", "olco"]` to `stations.yaml` after `settings` block
- Extended `detect_stale_prices()` with `data_timestamp: str = ""` parameter; added structured INFO log on exclusion capturing name, original price, local median, neighbor count, radius, and data_timestamp
- Updated `api/routes.py`: added `import yaml`, `from pathlib import Path`, `detect_stale_prices` to pricing imports, `_CONFIG_PATH` constant, per-request YAML config loading with OSError fallback, conditional `detect_stale_prices()` call inserted after corridor annotation and before `filter_by_autonomy()`
- Added `TestPlanAnomalyFilter` (4 tests) to `tests/test_routes.py` using `mock_open` + `builtins.open` context manager pattern for YAML mocking
- All 81 tests pass (41 pricing, 18 geo, 22 routes); zero regressions

### File List

- `stations.yaml` — Added `anomaly_filter_enabled` and `anomaly_filter_exemptions` top-level keys
- `api/pricing.py` — Extended `detect_stale_prices()` with `data_timestamp` parameter and exclusion logging
- `api/routes.py` — Added `import yaml`, `from pathlib import Path`, `detect_stale_prices` import, `_CONFIG_PATH` constant, filter config loading, conditional anomaly filter call in pipeline
- `tests/test_routes.py` — Added `mock_open` and `yaml` imports; added `TestPlanAnomalyFilter` class with 4 tests

### Change Log

- 2026-05-01: Implemented Story 4.2 — Exemptions, Kill Switch & Route Pipeline Integration. Extended `detect_stale_prices()` with `data_timestamp` + structured logging, integrated filter into `/api/plan` pipeline with YAML-driven kill switch and exemptions, added 4 route integration tests. All 81 tests pass.

### Review Findings

**Adversarial Review (2026-05-09) — 1 Patch Applied:**

- [x] [Review][Patch] No error handling on `detect_stale_prices()` call; any exception crashes entire `/api/plan` endpoint with 500 error [api/routes.py:158-160] — Applied: wrapped in try/except with `logger.warning(f"Anomaly filter failed: {_filter_exc}; skipping filter")` to gracefully degrade

**Original Pre-Review Findings (Already Implemented):**

- [x] [Review][Patch] Uncaught `yaml.YAMLError` crashes every `/api/plan` request when `stations.yaml` has a syntax error [api/routes.py — yaml load block] — add `yaml.YAMLError` to the `except` clause
- [x] [Review][Patch] YAML root non-dict value causes `AttributeError` on `.get()` [api/routes.py — yaml load block] — add `isinstance(_yaml_cfg, dict)` guard after `safe_load`
- [x] [Review][Patch] Scalar string `anomaly_filter_exemptions` value iterates characters instead of station names [api/routes.py — exemptions assignment] — add `isinstance(raw, list)` guard
- [x] [Review][Patch] `OSError` on YAML config read swallowed silently with no warning log [api/routes.py — try/except OSError] — add `logger.warning(...)` in the except block
- [x] [Review][Patch] No test covers OSError fallback path (filter defaults + no exemptions) [tests/test_routes.py] — add `TestPlanAnomalyFilter.test_yaml_oserror_defaults_to_enabled`
- [x] [Review][Patch] `assert mock_detect.call_args.args[1] is not None` is vacuous — any non-None value passes including an empty list [tests/test_routes.py — test_filter_called_when_enabled] — assert `call_args.args[1]` equals the `all_stations` list returned by `mock_fetch`
- [x] [Review][Defer] YAML config re-read from disk on every request — no caching [api/routes.py] — deferred, file is small and disk I/O is negligible vs network calls; noted in dev notes as intentional design
- [x] [Review][Defer] `builtins.open` mock intercepts all `open()` calls in the handler, not just `_CONFIG_PATH` [tests/test_routes.py — TestPlanAnomalyFilter] — deferred, pre-existing test pattern; acceptable because `plan()` only opens stations.yaml
