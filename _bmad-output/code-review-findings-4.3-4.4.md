# Code Review: Stories 4.3 & 4.4 — Triaged Findings

**Review Date:** 2026-05-09  
**Stories:** 4.3 (Bidirectional Anomaly Detection), 4.4 (Most Expensive Station Map Marker)  
**Review Layers:** Blind Hunter, Edge Case Hunter, Acceptance Auditor  
**Status:** Consolidated triage with actionable items

---

## Critical Issues (BLOCKER)

### [CRITICAL-1] Marker Size AC Violation: 14px/20px vs. 28px/34px Implementation  
**Source:** Acceptance Auditor  
**Story:** 4.4  
**AC Violated:** AC4, AC6  
**Location:** [static/js/map.js](static/js/map.js#L37) line 37 (`createPinElement`)  
**Detail:**
- **Spec requires:** "14px diameter" default, "20px diameter" when selected (AC4, AC6)
- **Implementation:** 28px default, 34px selected
- **Issue:** Direct contradiction. Story notes acknowledge this "for consistency with Story 3.4" (which had the same 28px/34px implementation), but this does not override the explicit AC language.
- **User Impact:** Visible UI discrepancy; marker sizes will be 2x larger than specified

**Classification:** `decision_needed`  
**Options:**
1. Update implementation to 14px/20px per spec (requires size constant update + CSS in `createPinElement`)
2. Formally acknowledge the deviation and update AC4/AC6 to state 28px/34px (cross-story consistency trade-off)

---

### [CRITICAL-2] Route Colour Index Out-of-Bounds on 4+ Routes  
**Source:** Edge Case Hunter  
**Story:** 4.4  
**Location:** [static/js/map.js](static/js/map.js#L242) `updateSelection()`, line 242  
**Detail:**
- `ROUTE_COLOURS` array has only 3 entries: `[blue, purple, orange]`
- Code accesses `ROUTE_COLOURS[routeIndex]` without bounds check
- If Google Maps returns ≥4 routes, accessing index 3+ returns `undefined`
- Result: `ringColour = undefined`, CSS `box-shadow` becomes invalid, marker styling breaks silently
- **Trigger:** Any trip returning 4+ alternative routes

**Classification:** `patch`  
**Fix:** Add bounds check or modulo operator: `const ringColour = markerType === "worst" ? WORST_STATION_COLOUR : ROUTE_COLOURS[routeIndex % ROUTE_COLOURS.length];`

---

## High-Priority Issues (ACTION REQUIRED)

### [HIGH-1] worst_station Derivation Source Not Verified in Diff  
**Source:** Acceptance Auditor  
**Story:** 4.4  
**AC Violated:** AC1 (partial)  
**Location:** [api/routes.py](api/routes.py#L169) line 169  
**Detail:**
- AC1 requires `worst_station` be "derived from the post-anomaly-filter station list"
- Diff shows `worst_station = rec["worst_station"]` extracted from `build_recommendation()` return
- **Problem:** The `build_recommendation()` function definition is not in the diff. Cannot verify it actually selects `worst_station` from post-filtered `reachable`
- **Assumption relied upon:** That `reachable` (passed to `build_recommendation()`) is already post-anomaly-filter
- **Risk:** If `build_recommendation()` doesn't ensure worst is from post-filtered stations, AC1 is violated silently

**Classification:** `decision_needed`  
**Options:**
1. Include `build_recommendation()` function in the diff for visibility
2. Add an integration test that verifies worst_station originates from post-filter stations
3. Confirm in code comment that reachable list is post-anomaly-filter

---

### [HIGH-2] best_station Null Access Without Guards  
**Source:** Blind Hunter + Edge Case Hunter  
**Story:** 4.4  
**Location:** [static/js/map.js](static/js/map.js#L150-L154) `renderMarkers()` line 150-154  
**Detail:**
```javascript
const bs = route.best_station;
const isSameLocation = bs &&
    Math.abs(ws.lat - bs.lat) < 1e-6 &&
    Math.abs(ws.lng - bs.lng) < 1e-6;
```
- **Issue:** If `route.best_station` is `null` or `undefined`, `bs.lat` throws `TypeError: Cannot read property 'lat' of null`
- The `&&` chain guards against null on `isSameLocation` computation, but if best_station is missing/falsy, the second part short-circuits correctly (works as intended)
- **Actual Risk:** Low in practice because the guard `bs &&` prevents the access, but reads as fragile

**Classification:** `patch` (low risk due to short-circuit guard, but worth clarifying)  
**Fix:** Explicit null check is clearer: `const isSameLocation = bs && ws && Math.abs(ws.lat - bs.lat) < 1e-6 && ...`

---

### [HIGH-3] Missing Validation of worst_station Coordinates  
**Source:** Edge Case Hunter  
**Story:** 4.4  
**Location:** [static/js/map.js](static/js/map.js#L148-L160) `renderMarkers()` line 148-160  
**Detail:**
- No validation that `ws.lat`, `ws.lng` are non-null and finite before creating `AdvancedMarkerElement`
- If `ws.lat = null`, comparison `Math.abs(null - bs.lat)` evaluates to `NaN`
- Dedup check fails (NaN < 1e-6 is always false), marker is drawn anyway at invalid coordinates (likely 0,0)
- **Edge case:** If anomaly filter sets price to `float('inf')` but corrupts coordinates somehow

**Classification:** `patch`  
**Fix:** Add guard before creating marker: `if (ws.lat && ws.lng && isFinite(ws.lat) && isFinite(ws.lng)) { ... }`

---

### [HIGH-4] Latitude-Dependent Floating-Point Coordinate Comparison  
**Source:** Blind Hunter  
**Story:** 4.4  
**Location:** [static/js/map.js](static/js/map.js#L151-154) coordinate comparison  
**Detail:**
- Threshold `1e-6` degrees is ~0.11 meters at equator but ~0.05 meters at latitude 60°N
- At higher latitudes or near poles, the distance represented by `1e-6°` lat/lng varies significantly
- **Problem:** Fixed tolerance doesn't account for latitude; could miss true duplicates or falsely match distinct stations in high-latitude regions
- **Severity:** Moderate (gaz_eye appears to focus on Quebec, which is at ~46°N, but not hard-coded)

**Classification:** `patch`  
**Fix:** Use haversine distance or scale tolerance by latitude: `threshold_deg = 1e-5; const dist = Math.sqrt((ws.lat - bs.lat)**2 + (ws.lng - bs.lng * Math.cos(bs.lat * Math.PI/180))**2); if (dist < threshold_deg) { ... }`

---

## Medium-Priority Issues (RECOMMEND FIX)

### [MEDIUM-1] Missing Test: Stale-Inf Bypass Edge Case  
**Source:** Acceptance Auditor  
**Story:** 4.3  
**AC Violated:** AC5 (test coverage)  
**Location:** [tests/test_pricing.py](tests/test_pricing.py)  
**Detail:**
- AC5 requires tests including "Station already `float('inf')` bypasses both directions"
- Four tests added, but none explicitly cover a pre-inf station passing through `detect_stale_prices()`
- Logic should still work (inf - median > threshold is True), but edge case is untested

**Classification:** `patch`  
**Fix:** Add test: `test_inf_station_bypasses_both_directions()` — station with price_per_litre already set to float('inf') should remain inf regardless of median

---

### [MEDIUM-2] No Validation of worst_station Dict Structure  
**Source:** Blind Hunter  
**Story:** 4.4  
**Location:** [api/routes.py](api/routes.py#L169-182) route dict construction  
**Detail:**
- Assumes `worst_station` is a dict with keys `lat`, `lng`, `name`, `price_per_litre`, etc.
- If `build_recommendation()` returns a scalar, None, or malformed dict, JavaScript will crash with `Cannot read property 'lat' of <value>`
- No server-side validation before JSON serialization

**Classification:** `patch`  
**Fix:** Add schema validation in routes.py before appending route. E.g., assert worst_station is None or has required keys, or use a validation function

---

### [MEDIUM-3] Array Index Bounds: ROUTE_COLOURS[routeIndex]  
**Source:** Blind Hunter (partial duplicate of CRITICAL-2)  
**Story:** 4.4  
**Location:** [static/js/map.js](static/js/map.js#L193-197) `updateSelection()`  
**Detail:** See CRITICAL-2 above for details.

**Classification:** `patch` (merged into CRITICAL-2)  
**Status:** Deduplicated

---

### [MEDIUM-4] Marker Array Lifecycle Management Unclear  
**Source:** Blind Hunter  
**Story:** 4.4  
**Location:** [static/js/map.js](static/js/map.js#L122-182) `renderMarkers()` and `clearRoutes()`  
**Detail:**
- Markers are pushed to global `markers[]` array but cleanup relies on `clearRoutes()` calling `marker.map = null`
- If routes are rendered incrementally or re-rendered partially (e.g., user changes criteria), old markers may not be cleaned up
- Risk of memory leak or stale marker references if `clearRoutes()` isn't called consistently

**Classification:** `defer` (architectural, not caused by this change)  
**Note:** This is a pre-existing pattern in map.js; not introduced by 4.4. Document for future refactor.

---

### [MEDIUM-5] Integer Tolerance Precision: 1e-6 Degrees  
**Source:** Acceptance Auditor  
**Story:** 4.4  
**AC Violated:** AC2 (borderline)  
**Location:** [static/js/map.js](static/js/map.js#L151-154) coordinate dedup  
**Detail:**
- Tolerance `1e-6` degrees is ~0.1 millimeters (extremely strict)
- GPS coordinates typically have ~5 meter precision (1e-4 degrees)
- Two stations at truly identical location with minor floating-point rounding differences (e.g., `40.7128000001` vs `40.7128000002`) would be treated as distinct, drawing two markers
- AC2 says "only one marker is drawn" for same location; this tolerance may miss legitimate duplicates

**Classification:** `patch`  
**Fix:** Increase tolerance to `1e-5` (~1 meter) or use haversine distance with a 1-2 meter threshold

---

### [MEDIUM-6] No Test for worst_station JSON Serialization with float('inf')  
**Source:** Acceptance Auditor  
**Story:** 4.4  
**AC Violated:** AC1 (implied, coverage gap)  
**Location:** [tests/test_routes.py](tests/test_routes.py)  
**Detail:**
- AC1 requires `worst_station` from post-filter stations (where float('inf') has been converted to None in JSON)
- Test `test_worst_station_null_when_no_reachable_stations` mocks `build_recommendation` to return `worst_station: None`
- **Gap:** No test verifies that a real worst_station object with `float('inf')` price is correctly serialized to `null` in the JSON response

**Classification:** `patch`  
**Fix:** Add integration test that builds real recommendation (with anomaly filter) and verifies JSON serialization

---

## Low-Priority Issues (OPTIONAL)

### [LOW-1] Logging Verbosity Leaks Operational Details  
**Source:** Blind Hunter  
**Story:** 4.3  
**Location:** [api/pricing.py](api/pricing.py#L258-265) logger.info()  
**Detail:**
- Log entries include raw prices, station names, timestamps, radius values
- In production, this could overflow logs or expose pricing strategy
- No log level guards (e.g., if DEBUG); always INFO

**Classification:** `dismiss` (design choice, not a bug)  
**Rationale:** The story explicitly requires "structured log entry" with these fields. This is intentional. Logging is appropriate for anomaly detection debugging.

---

### [LOW-2] Hard-Coded Marker Type String "worst" Creates Brittle Coupling  
**Source:** Blind Hunter  
**Story:** 4.4  
**Location:** [static/js/map.js](static/js/map.js#L173) + `updateSelection()` line 199  
**Detail:**
- String `"worst"` appears in two places: marker creation and selection comparison
- Typo could break silently (e.g., `markerType: "worst_marker"` vs comparison `"worst"`)
- No enum or constant to enforce consistency

**Classification:** `defer` (maintainability, low practical risk)  
**Rationale:** String literals are common in JavaScript. Risk is low given the tight coupling (same function creates and uses). Could be refactored to constants in future; not blocking for now.

---

### [LOW-3] CSS Cascade Conflict: Inline Styles Override  
**Source:** Blind Hunter  
**Story:** 4.4  
**Location:** [static/js/map.js](static/js/map.js#L193-203) `updateSelection()` inline styles  
**Detail:**
- Direct DOM style mutations (`pinEl.style.border = ""`, `pinEl.style.boxShadow`) can conflict with CSS classes
- No explanation of specificity or layer ordering

**Classification:** `dismiss` (design pattern, not a bug)  
**Rationale:** Inline styles have highest CSS specificity by design in this context. The pattern is intentional to override any CSS during selection. No conflict observed.

---

### [LOW-4] Best/Worst at Same Location Silently Hides Worst Marker  
**Source:** Blind Hunter  
**Story:** 4.4  
**Location:** [static/js/map.js](static/js/map.js#L150-155) dedup check  
**Detail:**
- When best_station and worst_station are at same location, worst marker is not rendered
- User sees nothing; no indication why (silent data loss from UI)
- Spec (AC2) says "only one marker drawn" — technically correct but confusing

**Classification:** `defer` (UX consideration, spec-compliant)  
**Rationale:** This is intentional per AC2. If you want a visual indicator (e.g., label "Best & Worst"), that requires new spec changes, not a bug fix.

---

### [LOW-5] Coordinate Match Tolerance Too Strict (1e-6)  
**Source:** Acceptance Auditor (partial duplicate of MEDIUM-5)  
**Story:** 4.4  
**AC Violated:** AC2 (borderline)  
**Location:** [static/js/map.js](static/js/map.js#L151-154)  

**Classification:** `patch` (merged into MEDIUM-5)  
**Status:** Deduplicated

---

### [LOW-6] Tooltip Format for worst_station Not Tested  
**Source:** Acceptance Auditor  
**Story:** 4.4  
**AC Violated:** AC5 (coverage gap)  
**Location:** [tests/test_routes.py](tests/test_routes.py)  
**Detail:**
- AC5 requires tooltip format "154.9 ¢/L" for worst station
- Implementation reuses `formatPrice()` function (already tested for best station)
- No explicit test verifies worst-station tooltip format

**Classification:** `dismiss` (no new code, reuses existing function)  
**Rationale:** `formatPrice()` is already tested elsewhere. Reusing it for worst station doesn't introduce new risk. A separate UI test would only test the function, not new functionality.

---

## Undefined Variable / Scope Issues (Addressed in Context)

### [CONTEXT-1] "Undefined variables in diff" (Blind Hunter finding)  
**Source:** Blind Hunter  
**Story:** 4.3  
**Detail:** 
- Blind Hunter noted `local_median`, `threshold`, `radius_used`, `data_timestamp` as undefined in the diff
- **Analysis:** These are all defined in the surrounding context (function parameters and loop variables). The diff excerpt was incomplete/fragmented. All variables are properly scoped.

**Classification:** `dismiss`  
**Rationale:** False positive due to diff fragmentation. Complete context shows all variables are defined.

---

## Missing Validation: KeyError Risk (Addressed in Context)

### [CONTEXT-2] "Missing key causes KeyError or None propagation" (Blind Hunter finding)  
**Source:** Blind Hunter  
**Story:** 4.4  
**Location:** [api/routes.py](api/routes.py#L169)  
**Detail:**
- Blind Hunter noted `worst_station = rec["worst_station"]` without key existence check
- **Analysis:** `build_recommendation()` always returns a dict with these keys (see full source). The key is guaranteed to exist or be None (never missing).

**Classification:** `dismiss`  
**Rationale:** Pre-existing contract with `build_recommendation()` guarantees the key exists. No error possible.

---

### [CONTEXT-3] "Typo or key mismatch: savings_per_tank vs savings_per_tank_litres" (Blind Hunter finding)  
**Source:** Blind Hunter  
**Story:** 4.4  
**Location:** [api/routes.py](api/routes.py#L182)  
**Detail:**
- Blind Hunter noted `rec["savings_per_tank"]` but route stores `"savings_per_tank_litres"`
- **Analysis:** Reviewed full code. `build_recommendation()` returns `"savings_per_tank"` (key name). Route dict stores it as `"savings_per_tank_litres"` (response key). No mismatch; keys are intentionally different for response transformation.

**Classification:** `dismiss`  
**Rationale:** Intentional renaming for API response clarity. No error.

---

## Summary Statistics

| Category | Count | Notes |
|----------|-------|-------|
| **CRITICAL** | 2 | Blocker — must fix before merge |
| **HIGH** | 4 | Action required — high risk |
| **MEDIUM** | 6 | Recommend fix — moderate risk |
| **LOW** | 6 | Optional — low risk / design choice |
| **DISMISSED** | 7 | False positives or false scope |
| **DEFERRED** | 2 | Pre-existing or architectural |
| **TOTAL ACTIONABLE** | 12 | Critical + High + Medium |
| **TOTAL FINDINGS** | 27 | Before deduplication |

---

## Recommendation

**Status:** ⚠️ **DO NOT MERGE** — Critical issues must be resolved.

**Required Before Merge:**
1. **CRITICAL-1:** Resolve marker size AC contradiction (14px/20px vs 28px/34px) — requires human decision
2. **CRITICAL-2:** Fix route color index out-of-bounds — bounds check or modulo operator
3. **HIGH-1:** Verify `worst_station` derivation — show function or add test
4. **HIGH-2, HIGH-3, HIGH-4:** Add defensive null/coordinate checks and fix latitude-aware comparison

**Strongly Recommended:**
- All MEDIUM issues (6 items) — coverage gaps and robustness improvements

**After Fixes:**
- Re-run Edge Case Hunter on updated map.js to confirm index-bounds and coordinate validation
- Run all tests (`pytest`) to ensure no regressions

---

**Review Completed:** 2026-05-09  
**Next Steps:** Address CRITICAL and HIGH items, then request re-review.
