# Edge Case Hunter Report: Stories 4.3 & 4.4

**Stories:** 4.3 (Bidirectional Anomaly Detection) + 4.4 (Most Expensive Station Marker)  
**Date:** 2026-05-09  
**Status:** FINDINGS DOCUMENTED  

---

## CRITICAL FINDINGS

### 1. Route Colour Index Out of Bounds
**Title:** Fourth or subsequent route causes undefined marker ring colour

**Edge case / boundary condition:**  
When Google Maps returns 4+ routes but `ROUTE_COLOURS` array contains only 3 colours (blue, purple, orange), accessing `ROUTE_COLOURS[3]` returns `undefined`. This occurs when rendering marker selection rings for routes beyond the third.

**File and code location:**  
[static/js/map.js](static/js/map.js#L242-L244)

**Why it's a problem:**  
- Line 242: `const ringColour = markerType === "worst" ? WORST_STATION_COLOUR : ROUTE_COLOURS[routeIndex];`
- If `routeIndex >= 3`, `ringColour` becomes `undefined`
- Line 248: `pinEl.style.boxShadow = `0 0 0 2px ${ringColour}`;` assigns `"0 0 0 2px undefined"`, which is invalid CSS and produces no visual ring
- Users cannot visually distinguish best/worst markers for 4th+ routes when selected
- Test coverage gap: `test_route_schema_includes_worst_station` tests 3 routes (uses `_make_gm_response(3)` default), missing 4+ route scenario

**Suggested severity:** HIGH

**Suggested fix:**  
Define additional route colours or wrap access with modulo/fallback:
```javascript
const ringColour = markerType === "worst" ? WORST_STATION_COLOUR : ROUTE_COLOURS[routeIndex % ROUTE_COLOURS.length];
```

---

### 2. Worst Station Marker Drawn with Null Coordinates
**Title:** Null or undefined lat/lng in worst_station produces marker at invalid location

**Edge case / boundary condition:**  
If a station dict in the response has `lat: null` or `lng: null` (should not occur in normal flow but possible if data pipeline is corrupted), the comparison `Math.abs(ws.lat - bs.lat)` evaluates to `NaN`, which is never `< 1e-6`. The check `!isSameLocation` evaluates to `true` (since `NaN < 1e-6` is false, making `isSameLocation` false). A marker is then created at coordinates `{ lat: null, lng: null }`, which Google Maps may place at (0,0) or render incorrectly.

**File and code location:**  
[static/js/map.js](static/js/map.js#L126-L145)

**Why it's a problem:**  
- Lines 126–130: Comparison logic assumes `ws.lat` and `ws.lng` are valid numbers
- Line 122: No guard clause validates that `ws.lat` and `ws.lng` exist and are finite before creating the marker
- AdvancedMarkerElement will accept `{ lat: null, lng: null }` without throwing an error
- Marker may render at wrong location or not render at all, confusing user
- `formatPrice()` checks for null/undefined/!isFinite() (line 33), but coordinate validation is missing

**Suggested severity:** MEDIUM

**Suggested fix:**  
Validate coordinates before drawing marker:
```javascript
if (route.worst_station && ws.lat != null && ws.lng != null && isFinite(ws.lat) && isFinite(ws.lng)) {
    // ... marker creation code
}
```

---

### 3. Best and Worst Stations at Identical Coordinates Not Deduped (JavaScript Precision Edge)
**Title:** Floating-point precision loss in coordinate comparison allows duplicate markers

**Edge case / boundary condition:**  
Two stations with identical real-world coordinates may differ by tiny floating-point rounding errors when serialized to JSON and deserialized by JavaScript. For example, backend `lat=45.50169999999999` rounds to JSON, JavaScript deserializes as `lat=45.501699`, and comparison `Math.abs(ws.lat - bs.lat) < 1e-6` (which is 0.000001°) may fail to detect the duplicate if the error is 1e-7 or smaller. Conversely, if a backend computation introduces a 2e-6 error, the dedup check will miss it.

More likely: stations at exactly the same coordinates should be rare, but if they occur (e.g., multiple pumps at same lat/lng), both best and worst could be drawn on top of each other.

**File and code location:**  
[static/js/map.js](static/js/map.js#L127-L129)

**Why it's a problem:**  
- The threshold `1e-6` radians ≈ 0.11 meters at equator; this is tighter than typical GPS error (~5 meters)
- Legitimate duplicate-location stations (e.g., two pumps at same GPS point) should ideally be deduplicated at the backend, not the frontend
- Two overlapping markers will make one unclickable or difficult to interact with
- No test covers floating-point edge case (tests using `_make_stations()` produce distinct lat/lng values)
- AC2 states "only one marker is drawn" but doesn't specify the precision threshold

**Suggested severity:** MEDIUM

**Suggested fix:**  
- Document that the 1e-6° threshold is intentional
- Consider stricter comparison or backend dedup logic
- Add test with nearly-identical coordinates:
  ```javascript
  test('worst_station at 45.501700001, best_station at 45.501700000 draws one marker', () => {
      // should deduplicate within floating-point precision
  });
  ```

---

### 4. Exemptions Not Applied Bidirectionally (Logic Correctness, Not Runtime)
**Title:** Exemption bypass evaluated before median comparison prevents expensive-direction false positives

**Edge case / boundary condition:**  
In `detect_stale_prices()`, the exemption check (lines 243–246) is applied BEFORE the expensive/cheap comparison (lines 254–256). This is correct — exempted stations bypass the filter entirely in both directions. However, if the order were reversed (cheaper outlier/expensive outlier computed first, then exemptions checked), an exempted station could be marked for exclusion in one direction before exemption is recognized. Current code is correct, but this is a subtle dependency on statement order.

**File and code location:**  
[api/pricing.py](api/pricing.py#L243-L256)

**Why it's a problem:**  
- The order of checks is load-bearing: exemptions MUST be evaluated before any median comparison
- Code comment or assertion would clarify intent
- Future refactoring could inadvertently swap the check order without realizing the consequence
- Tests pass but don't explicitly verify exemption takes precedence

**Suggested severity:** LOW (implementation is correct, but fragile)

**Suggested fix:**  
Add explanatory comment in code:
```python
# CRITICAL: exemption check must precede median comparison.
# Exempted stations bypass filter in both directions.
```

---

### 5. Worst Station Becomes Best When All Stations Priced Equally
**Title:** Degenerate case where `worst_station == best_station` in JavaScript UI not tested

**Edge case / boundary condition:**  
`build_recommendation()` in [api/pricing.py](api/pricing.py#L163-L182) correctly sets `best_station` and `worst_station` to the same reference when only one valid station exists (line 172) or all valid stations have identical prices. In the latter case:
```python
best = min(valid, key=lambda s: s["price_per_litre"])
worst = max(valid, key=lambda s: s["price_per_litre"])
```
If all prices are equal, `min()` and `max()` return the first and last station in `valid`, which may be the same dict object or different dicts with identical prices.

JavaScript dedup check (line 128) compares `ws.lat - bs.lat` to detect same location, but if two DIFFERENT station objects have identical `lat`/`lng`, they will pass the check and both markers will be drawn.

**File and code location:**  
[api/pricing.py](api/pricing.py#L177-L178) + [static/js/map.js](static/js/map.js#L127-L129)

**Why it's a problem:**  
- Test `test_identical_prices` in test_pricing.py verifies backend logic but no JavaScript test verifies that two markers are NOT drawn when prices are identical
- AC2 requires "only one marker is drawn" — but current check compares coordinates, not object identity
- If backend returns `{"best_station": {...}, "worst_station": {...}}` with identical `lat`/`lng` but different `name`/`price`, frontend draws both
- Scenario: two stations at same location with same price → best and worst are different objects → both markers drawn → UI clutter

**Suggested severity:** MEDIUM

**Suggested fix:**  
Strengthen dedup check to compare all identifying fields or use marker object identity:
```javascript
const isSameStation = bs && 
    ws.lat === bs.lat && 
    ws.lng === bs.lng && 
    ws.name === bs.name;  // or use object reference if backend guarantees same object
```

Or better, have backend return `worst_station: null` when `worst_station === best_station`:
```python
# In build_recommendation
if best is worst:
    worst = None
```

---

### 6. Marker Array Mutation Order with Selection Event
**Title:** Polyline selection fires before marker resize loop completes

**Edge case / boundary condition:**  
In [static/js/map.js](static/js/map.js#L87), the route polyline has a click handler that calls `setSelectedRoute(routeIndex)`. This fires a `routeSelected` event (in state.js), which is heard by the map module (line 52) and calls `updateSelection()`. If a user clicks a polyline while `renderMarkers()` is still executing its async loop (`.then()`), the marker array may be incomplete when `updateSelection()` iterates over it.

However, `renderMarkers()` is async (line 99: `export async function`), and callers must await it. If callers do not await, race condition occurs.

**File and code location:**  
[static/js/map.js](static/js/map.js#L52, #L87, #L99-L150)

**Why it's a problem:**  
- `renderMarkers()` uses `await google.maps.importLibrary("marker")` (line 100) — asynchronous
- If an event handler triggers `updateSelection()` before `renderMarkers()` finishes, `markers` array is incomplete
- Loop in `updateSelection()` (line 201) iterates over partial `markers`, skipping uninitialized entries
- No test covers async race condition; all tests are synchronous

**Suggested severity:** LOW (unlikely in practice; markers render quickly, user cannot click before render completes)

**Suggested fix:**  
- Ensure all calls to `renderMarkers()` are awaited (check calling code in app.js)
- Add a flag to track render completion: `let isRenderingMarkers = false;` in `renderMarkers()` and guard `updateSelection()` calls
- Document async contract in JSDoc

---

### 7. Float('inf') Sentinel Loses Meaning After JSON Serialization
**Title:** Backend sends `null` for unavailable prices; frontend formatPrice() handles null but marker creation uses raw values

**Edge case / boundary condition:**  
In [api/routes.py](api/routes.py#L133-135), unavailable prices (`float('inf')`) are converted to `None` before JSON serialization:
```python
if s.get("price_per_litre") == float("inf"):
    s["price_per_litre"] = None
```

However, `best_station` and `worst_station` references are never checked for `None` price before being sent. If a station's price is set to `None`, and it becomes the best or worst, the marker is created with `station.price_per_litre = None`.

In JavaScript, `formatPrice(null)` returns `"n/a"` (line 31–33), which is correct. However, there is no explicit guard: if a worst_station has `price_per_litre: null`, the code proceeds normally. This is fine, but represents a state that shouldn't occur if the backend filters correctly.

**File and code location:**  
[api/routes.py](api/routes.py#L141-143) + [api/pricing.py](api/pricing.py#L177) + [static/js/map.js](static/js/map.js#L228)

**Why it's a problem:**  
- Best/worst stations should never have `float('inf')` prices because `build_recommendation()` filters by `!= float('inf')` (line 169)
- After the for loop (lines 131–135), `best_station` and `worst_station` dicts are unchanged (they still reference objects in `reachable`)
- If `best_station.price_per_litre` was previously `float('inf')`, it will be `None` after the loop, but this should not occur because `build_recommendation` excludes inf prices
- State inconsistency: response could theoretically contain `{"best_station": {"price_per_litre": null}, ...}`, breaking AC4's schema assumption

**Suggested severity:** LOW (defensive; should not occur in practice, but could add assertion)

**Suggested fix:**  
Assert after mutation:
```python
# Validate serialization: best/worst should never be None or have None price
if best_station is not None:
    assert best_station.get("price_per_litre") is not None, "best_station price_per_litre is None"
if worst_station is not None:
    assert worst_station.get("price_per_litre") is not None, "worst_station price_per_litre is None"
```

---

### 8. updateSelection() Assumes Three ROUTE_COLOURS but Handles Any Number of Routes
**Title:** Marker ring colour is undefined for routes beyond index 2

**Edge case / boundary condition:**  
(Noted above as Critical Finding #1, but worth revisiting)

Both story 3.4 and this story define `ROUTE_COLOURS = [3 colors]` but the `/api/plan` endpoint can return up to 3 Google Maps alternative routes (via `"alternatives": "true"`). If Google ever returns fewer than 3 routes, indices are safe. But if Google's API changes to return 4+, or if a client hacks the request, the 4th route's marker ring colour is undefined.

**File and code location:**  
[static/js/map.js](static/js/map.js#L8-12, #L242)

**Why it's a problem:**  
- Hard-coded array limits extensibility
- No error handling or fallback
- Silently produces invalid CSS

**Suggested severity:** HIGH

**Suggested fix:**  
```javascript
const ringColour = markerType === "worst" 
    ? WORST_STATION_COLOUR 
    : ROUTE_COLOURS[routeIndex % ROUTE_COLOURS.length];
```

---

### 9. Exemption List May Contain Non-String Values
**Title:** Type guard in exemption check assumes all exemptions are strings

**Edge case / boundary condition:**  
In [api/routes.py](api/routes.py#L62-63), exemptions are loaded from YAML:
```python
_raw_exemptions = _yaml_cfg.get("anomaly_filter_exemptions") or []
anomaly_filter_exemptions = _raw_exemptions if isinstance(_raw_exemptions, list) else [_raw_exemptions]
```

If YAML contains `anomaly_filter_exemptions: [123, "costco", null]`, the list will have mixed types. In [api/pricing.py](api/pricing.py#L245), the check is:
```python
if any(isinstance(exc, str) and exc.lower() in station_name for exc in exemptions):
```

This correctly guards with `isinstance(exc, str)`, so non-strings are safely ignored. No runtime error occurs, but silently ignoring integer or null exemptions may not match user intent.

**File and code location:**  
[api/pricing.py](api/pricing.py#L245) + [api/routes.py](api/routes.py#L62-63)

**Why it's a problem:**  
- YAML parsing is lenient; a misconfigured YAML file with non-string exemptions doesn't fail loudly
- User adds `anomaly_filter_exemptions: [123, costco]` intending to exempt station 123 (int), but it's silently ignored
- `isinstance()` guard is defensive but no validation or warning is logged

**Suggested severity:** LOW (safety guard is present, but UX could warn user)

**Suggested fix:**  
Log a warning if non-string exemptions are found:
```python
for exc in exemptions:
    if not isinstance(exc, str):
        logger.warning(f"Exemption {exc!r} is not a string; skipping. Exemptions must be strings.")
```

---

### 10. Median Comparison Uses Strict Inequality (Boundary Case at Threshold)
**Title:** Station priced exactly at threshold is NOT excluded (edge case: threshold = delta)

**Edge case / boundary condition:**  
In [api/pricing.py](api/pricing.py#L254-255):
```python
cheap_outlier = local_median - station["price_per_litre"] > threshold
expensive_outlier = station["price_per_litre"] - local_median > threshold
```

Uses strict `>` inequality. Given `threshold = 0.05`, a station exactly `0.05` below or above the median is kept; `0.0500001` is excluded. This is a deliberate design choice (AC4 specifies "above threshold", implying `>`), but it's a boundary condition worth testing explicitly.

**File and code location:**  
[api/pricing.py](api/pricing.py#L254-255) + Tests at [tests/test_pricing.py](tests/test_pricing.py#L429, #L432)

**Why it's a problem:**  
- Test `test_station_kept_below_threshold()` uses `price=1.506` (delta = 0.044, below 0.05)
- Test `test_station_excluded_at_threshold()` uses `price=1.494` (delta = 0.056, above 0.05)
- No test for delta exactly = 0.05
- User could be confused if a station at exactly +5.0¢ is not flagged

**Suggested severity:** LOW (design is intentional; minor documentation gap)

**Suggested fix:**  
Add explicit test at boundary:
```python
def test_station_kept_at_exact_threshold(self):
    """Station exactly at threshold (5.0¢) is kept, not excluded."""
    neighbors = [self._st(45.51 + i * 0.001, -73.5, 1.55) for i in range(6)]
    candidate = self._st(45.5, -73.5, 1.50)  # exactly 5.0¢ below, at threshold
    result = detect_stale_prices([candidate], neighbors + [candidate])
    assert result[0]["price_per_litre"] == pytest.approx(1.50)
```

---

## SUMMARY TABLE

| # | Title | Severity | Status | Location |
|---|-------|----------|--------|----------|
| 1 | Route Colour Index Out of Bounds | **HIGH** | Unhandled | map.js:242 |
| 2 | Worst Station Marker at Null Coordinates | **MEDIUM** | Unhandled | map.js:126–145 |
| 3 | Floating-Point Precision in Dedup Check | **MEDIUM** | Unhandled | map.js:127–129 |
| 4 | Exemption Order Dependency (Logic) | **LOW** | Correct but fragile | pricing.py:243–256 |
| 5 | Identical Prices Produce Two Markers | **MEDIUM** | Unhandled | pricing.py + map.js |
| 6 | Async Render/Selection Race | **LOW** | Unlikely in practice | map.js:52, 99 |
| 7 | Float('inf') Sentinel Meaning Lost | **LOW** | Defensive, should not occur | routes.py:133 |
| 8 | Marker Ring Colour Undefined (4th+ Routes) | **HIGH** | Same as #1 | map.js:242 |
| 9 | Non-String Exemptions Silently Ignored | **LOW** | Safe but no warning | pricing.py:245 |
| 10 | Boundary Case at Exact Threshold | **LOW** | Intentional design; test gap | pricing.py:254 |

---

## RECOMMENDED ACTIONS (Priority Order)

1. **[HIGH]** Fix ROUTE_COLOURS index bounds (affects 4th+ routes)
2. **[MEDIUM]** Validate worst_station coordinates before drawing marker
3. **[MEDIUM]** Strengthen best/worst dedup to compare all fields or use object identity
4. **[MEDIUM]** Document or fix identical-price scenario in backend
5. **[LOW]** Add safeguard comments for exemption check order
6. **[LOW]** Add boundary-case tests for threshold and async race conditions
7. **[LOW]** Add warning logging for non-string exemptions

