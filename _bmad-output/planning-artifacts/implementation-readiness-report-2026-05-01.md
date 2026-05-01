---
stepsCompleted:
  - step-01-document-discovery
  - step-02-prd-analysis
  - step-03-epic-coverage-validation
  - step-04-ux-alignment
  - step-05-epic-quality-review
  - step-06-final-assessment
status: complete
date: '2026-05-01'
project_name: 'gaz_eye'
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
---

# Implementation Readiness Assessment Report

**Date:** 2026-05-01
**Project:** gaz_eye
**Assessor:** Implementation Readiness Workflow

---

## Document Inventory

| Type | File | Format | Status |
|------|------|--------|--------|
| PRD | `_bmad-output/planning-artifacts/prd.md` | Whole document | ✅ Found |
| Architecture | `_bmad-output/planning-artifacts/architecture.md` | Whole document | ✅ Found |
| Epics & Stories | `_bmad-output/planning-artifacts/epics.md` | Whole document | ✅ Found |
| UX Design | `_bmad-output/planning-artifacts/ux-design-specification.md` | Whole document | ✅ Found |
| UX Directions | `_bmad-output/planning-artifacts/ux-design-directions.html` | HTML mockup | ✅ Found (supplementary) |

No duplicates. No missing required documents.

---

## PRD Analysis

### Functional Requirements (37 total)

FR1–FR6: Trip Input (origin, destination, range, waypoints add/remove, submission)
FR7–FR10: Route Discovery (Google Maps 3-alt fetch, drive time/distance, cross-province, polyline decode)
FR11–FR15: Station Discovery (GeoJSON fetch, Haversine corridor, price parsing, missing price handling, fuel type filter)
FR16–FR18: Autonomy Filtering (distance from origin, safety buffer exclusion, no-stations case)
FR19–FR23: Recommendation Engine (cheapest/worst station, savings ¢/L, savings $/tank, route ranking)
FR24–FR27: Map Visualization (3 routes distinct style, station markers + price labels, best vs other distinction, marker click detail)
FR28–FR30: Recommendation Display (3-route comparison panel, savings per litre + per tank, data timestamp)
FR31–FR34: Configuration (fuel type, tank size, corridor distance, safety buffer)
FR35–FR37: Error Handling (Régie Essence unavailable, no routes found, Google Maps API errors)

### Non-Functional Requirements (10 total)

NFR1: Full pipeline renders within 5 seconds
NFR2: Map with up to 50 markers renders without lag
NFR3: GeoJSON fetched and parsed within 3 seconds
NFR4: Haversine corridor matching completes within 1 second for 300 km route
NFR5: Google Maps API key stored server-side only
NFR6: No user data persisted beyond local machine
NFR7: Directions API called with `alternatives=true`
NFR8: GeoJSON endpoint handles both JSON and gzip responses (dual-parse)
NFR9: Régie Essence requests include browser-like User-Agent header
NFR10: Google Maps JavaScript API used for map rendering (ToS compliance)

### Additional Requirements Noted in PRD

- Brownfield context: `gaz_saver.py` must be preserved and extended, not replaced
- Single-user, macOS laptop, Chrome/Safari latest — no multi-browser matrix
- No authentication, no public deployment, fully private local tool
- `GOOGLE_MAPS_API_KEY` must not be exposed in frontend source

### PRD Completeness Assessment

The PRD is well-structured and unusually thorough for a low-complexity project. All 37 FRs have unambiguous, testable language. NFRs are measurable (specific time targets). User journeys are detailed and map cleanly to functional requirements. **No gaps identified in the PRD itself.**

---

## Epic Coverage Validation

### Coverage Matrix

| FR | PRD Requirement (summary) | Epic Coverage | Status |
|----|--------------------------|---------------|--------|
| FR1 | Origin text input | Epic 3 / Story 3.2 | ✅ Covered |
| FR2 | Destination text input | Epic 3 / Story 3.2 | ✅ Covered |
| FR3 | Range input (km) | Epic 3 / Story 3.2 | ✅ Covered |
| FR4 | Add optional waypoints | Epic 3 / Story 3.2 | ✅ Covered |
| FR5 | Remove a waypoint | Epic 3 / Story 3.2 | ✅ Covered |
| FR6 | Submit trip query | Epic 3 / Story 3.3 | ✅ Covered |
| FR7 | Fetch 3 routes from Google Maps | Epic 2 / Story 2.3 | ✅ Covered |
| FR8 | Display drive time and distance | Epic 2 / Story 2.3 | ✅ Covered |
| FR9 | Handle cross-province routes | Epic 2 / Story 2.3 | ✅ Covered |
| FR10 | Decode route polylines | Epic 2 / Story 2.1 | ✅ Covered |
| FR11 | Fetch Régie Essence GeoJSON | Epic 1 / Story 1.2 | ✅ Covered |
| FR12 | Haversine corridor matching | Epic 2 / Story 2.2 | ✅ Covered |
| FR13 | Parse cent-string prices | Epic 1 / Story 1.2 | ✅ Covered |
| FR14 | Handle missing/unavailable prices | Epic 1 / Story 1.2 | ✅ Covered |
| FR15 | Filter by fuel type | Epic 1 / Story 1.2 | ✅ Covered |
| FR16 | Distance from origin to station | Epic 2 / Story 2.2 | ✅ Covered |
| FR17 | Autonomy filter with safety buffer | Epic 1 / Story 1.3 | ✅ Covered |
| FR18 | Handle no reachable stations | Epic 1 / Story 1.3 | ✅ Covered |
| FR19 | Cheapest reachable station per route | Epic 1 / Story 1.3 | ✅ Covered |
| FR20 | Most expensive reachable station | Epic 1 / Story 1.3 | ✅ Covered |
| FR21 | Savings per litre | Epic 1 / Story 1.3 | ✅ Covered |
| FR22 | Savings per tank | Epic 1 / Story 1.3 | ✅ Covered |
| FR23 | Route ranking by fuel cost | Epic 1 / Story 1.3 | ✅ Covered |
| FR24 | 3 routes on map, distinct styling | Epic 3 / Story 3.4 | ✅ Covered |
| FR25 | Station markers with price labels | Epic 3 / Story 3.4 | ✅ Covered |
| FR26 | Best vs other station distinction | Epic 3 / Story 3.4 | ✅ Covered |
| FR27 | Station marker click → details | Epic 3 / Story 3.4 | ✅ Covered |
| FR28 | 3-route comparison panel | Epic 3 / Story 3.3 | ✅ Covered |
| FR29 | Savings ¢/L and $/tank on cards | Epic 3 / Story 3.3 | ✅ Covered |
| FR30 | Data freshness timestamp | Epic 3 / Story 3.5 | ✅ Covered |
| FR31 | Configure fuel type | Epic 3 / Story 3.2 | ✅ Covered |
| FR32 | Configure tank size | Epic 3 / Story 3.2 | ✅ Covered |
| FR33 | Configure corridor distance | Epic 3 / Story 3.2 | ✅ Covered |
| FR34 | Configure safety buffer | Epic 3 / Story 3.2 | ✅ Covered |
| FR35 | Régie Essence error message | Epic 3 / Story 3.5 | ✅ Covered |
| FR36 | No routes found message | Epic 3 / Story 3.5 | ✅ Covered |
| FR37 | Google Maps API error handling | Epic 3 / Story 3.5 | ✅ Covered |

### Coverage Statistics

- **Total PRD FRs:** 37
- **FRs covered in epics:** 37
- **Coverage:** 100% ✅

### NFR Coverage

All 10 NFRs are addressed in story acceptance criteria:
- NFR1 (5s): Story 2.3 (single endpoint minimises round trips), Story 3.3 (loading state)
- NFR2 (map lag): Story 3.4 (AdvancedMarkerElement, polylines)
- NFR3 (GeoJSON 3s): Story 1.2 (fetch_stations extracted and tested)
- NFR4 (Haversine 1s): Story 2.2 (in-memory loop against full station dataset)
- NFR5 (API key server-side): Story 2.3 AC ("key not in response body"), Story 3.1 AC (Jinja2 injection only)
- NFR6 (no data beyond local): Story 3.2 (localStorage only, no backend persistence)
- NFR7 (alternatives=true): Story 2.3 AC explicitly states this parameter
- NFR8 (dual-parse): Story 1.2 AC explicitly states dual-parse strategy
- NFR9 (User-Agent): Story 1.2 AC explicitly states User-Agent requirement
- NFR10 (Maps JS ToS): Story 3.1 (Google Maps JS API via CDN)

---

## UX Alignment Assessment

### UX Document Status

✅ **Found and complete** — `ux-design-specification.md` is a comprehensive, fully-specified UX document covering: color system, typography, layout, component states, interaction patterns, responsive strategy, and accessibility.

### UX ↔ PRD Alignment

All 4 user journeys in the UX spec (J1 Friday Commute, J2 Waypoint Detour, J3 Low Fuel Urgency, J4 Urban Quick Check) directly map to the PRD's Journey Requirements Summary. The UX spec adds implementation detail (e.g., skeleton card dimensions, amber range indicator, km shortfall messaging) that is consistent with PRD intent — no conflicting requirements found.

### UX ↔ Architecture Alignment

**Aligned:**
- Split-pane layout → Architecture confirms `static/index.html`, `static/css/style.css`
- `AdvancedMarkerElement` → Architecture confirms Google Maps JS API CDN
- `localStorage` → Architecture confirms `state.js` singleton with `DEFAULT_SETTINGS`
- `CustomEvent("routeSelected")` → Architecture confirms this exact pattern
- Flask Jinja2 serving `index.html` → Architecture confirms `render_template`

### 🟠 ISSUE FOUND: Alpine.js vs. Vanilla JS Conflict

**UX Specification states:**
> "Alpine.js for lightweight reactivity without a full framework build step — or vanilla JS if even simpler is preferred"
> "Settings Drawer uses Alpine.js `x-show` + `x-transition` for the slide animation"

**Architecture states:**
> "Vanilla JS ES modules, no bundler, no framework."
> "No JavaScript build tooling is needed for a single-user local tool"

**Impact:** Story 3.2 inherits the `translateX` transition from the UX spec but does not specify Alpine.js or vanilla JS for the drawer open/close logic. A dev agent reading the UX spec may reach for Alpine.js, violating the Architecture constraint. Since both docs are in scope for dev agents, this ambiguity could cause implementation drift.

**Recommendation:** Story 3.2 should explicitly state "implement using vanilla JS (`classList`/`style.transform`) — do not introduce Alpine.js."

---

## Epic Quality Review

### Epic Structure Validation

#### Epic 1: Project Foundation & Pricing Engine

**User value check:** The goal ("pricing pipeline operational, recommendation engine unit-tested") is technical in framing but reflects the only realistic Epic 1 for this brownfield developer-tool project. The developer is the sole user; the pricing engine is the product's core data moat. **Acceptable for this project context** — the technical framing is appropriate when the "user" is also the developer and the tool has no consumer UX in this epic.

**Independence:** Fully testable via `pytest` without any subsequent epic. ✅

#### Epic 2: Route Planning API

**User value check:** "Backend 100% complete, testable via `curl`" — again technically framed but correctly scoped. The value is that the developer can verify the entire route+pricing pipeline before investing in the frontend. ✅

**Independence:** Fully testable via `curl` using only Epic 1 output. ✅

#### Epic 3: Trip Planning SPA

**User value check:** "Olivier can open `http://localhost:5000`, enter a trip, and see three colour-coded route cards" — clear, user-centric, unambiguous. ✅

**Independence:** Fully usable once Epic 1 + 2 are in place. ✅

### Story Dependency Analysis

Story dependencies are clean throughout. Each story builds only on prior stories within the same epic:

| Epic | Chain | Verdict |
|------|-------|---------|
| Epic 1 | 1.1 → 1.2 → 1.3 | ✅ No forward deps |
| Epic 2 | 2.1 → 2.2 → 2.3 | ✅ No forward deps |
| Epic 3 | 3.1 → 3.2 → 3.3 → 3.4 → 3.5 | ✅ No forward deps |

### Acceptance Criteria Quality

Given/When/Then format is used consistently. ACs are specific and testable. Edge cases are addressed (empty station list, all prices `float('inf')`, 0 tank litres, null best_station, < 3 routes returned, Google Maps failures). 

### 🟡 MINOR CONCERN 1: Route Label Origin Unspecified

**Location:** Story 2.3, Story 3.3
**Issue:** Both stories reference route labels like `"Via Hwy 50"` but no story specifies how this label is derived from the Google Maps Directions API response. The API returns a `summary` field per route — a dev agent needs to know to use `route["summary"]` from the Google Maps response to populate the `label` field in the `/api/plan` response schema. This is an implementation detail that could easily be missed.

**Recommendation:** Add to Story 2.3 AC: "The `label` field is populated from the `summary` field of the Google Maps Directions API route object (e.g., `'Via Hwy 50'`)."

### 🟡 MINOR CONCERN 2: `best_station: null` Not Explicitly Handled in Story 3.3

**Location:** Story 3.3
**Issue:** Story 2.3 correctly specifies `best_station (object or null)` in the API response. Story 3.3 renders cards assuming a best station exists. Story 3.5 handles the no-stations edge case, but the `null` check for `best_station` during card render is not explicit in Story 3.3's ACs — a dev agent could assume it's always present.

**Recommendation:** Add to Story 3.3 AC: "If `best_station` is `null`, the card renders in the no-stations state (handled fully in Story 3.5)."

### 🟡 MINOR CONCERN 3: Low-Range Amber Indicator Threshold is Hardcoded

**Location:** Story 3.5
**Issue:** The AC states "Given I enter a range value ≤ 50 km... the range input gains an amber border." The value `50 km` is not derived from any PRD/Architecture/UX specification — the UX spec says "when range is very low" without defining a threshold. This means the threshold is an arbitrary implementation decision embedded in the story that could diverge from what feels right in practice.

**Recommendation:** Acceptable as-is for MVP (50 km is a reasonable heuristic). Alternatively, make the amber trigger dynamic: amber when `range_km ≤ (safety_buffer_km * 3)`, which scales with the configured buffer. Either choice should be documented.

### 🟡 MINOR CONCERN 4: NFR Performance Targets Not Testable via Story ACs

**Location:** Epic-level, NFR1–NFR4
**Issue:** NFR1 (5s full pipeline), NFR3 (3s GeoJSON), and NFR4 (1s Haversine) are defined but no story has acceptance criteria that verify these performance targets. They will only be discovered via manual timing after implementation.

**Recommendation:** Add a timing assertion to Story 2.3 integration tests, e.g., "The mocked test suite completes a full `POST /api/plan` request in < 100ms (ensuring no algorithmic inefficiency is introduced)." This doesn't guarantee production latency but catches obvious regressions.

### 🟢 POSITIVE FINDING: Brownfield Preservation Correctly Handled

Story 1.1 explicitly requires `gaz_saver.py` and `stations.yaml` to be preserved unchanged. Story 1.2 requires that `python gaz_saver.py` still works after extraction. This is exactly correct brownfield handling — no risk of breaking the existing tool.

### 🟢 POSITIVE FINDING: API Key Security Enforced at Story Level

Story 2.3 AC includes `"the GOOGLE_MAPS_API_KEY value does not appear anywhere in the response body"` — this is the right place to enforce NFR5 and ensures a dev agent cannot accidentally expose it.

---

## Summary and Recommendations

### Overall Readiness Status

## ✅ READY — with 4 recommended improvements

The planning artifacts are complete, well-structured, and mutually consistent. FR coverage is 100%. The epic dependency chain is clean. Acceptance criteria are specific and testable. The project is ready for implementation.

### Issues by Severity

| Severity | Count | Summary |
|----------|-------|---------|
| 🔴 Critical | 0 | None |
| 🟠 Major | 1 | Alpine.js vs. vanilla JS framework conflict |
| 🟡 Minor | 4 | Route label origin, null best_station, amber threshold, NFR performance ACs |

---

### Action Items Before Implementation

#### 🟠 Action 1 (Recommended — before dev starts): Resolve Alpine.js Ambiguity in Story 3.2

**Add to Story 3.2 AC:**
> "The drawer open/close animation is implemented using vanilla JS (`element.classList.add/remove` or `element.style.transform`) — Alpine.js must NOT be introduced; it conflicts with the Architecture constraint of no JS frameworks."

This prevents a dev agent from choosing Alpine.js based on the UX spec mention and then conflicting with the Architecture doc.

#### 🟡 Action 2 (Low urgency): Add Route Label Source to Story 2.3

**Add to Story 2.3 AC:**
> "The `label` field in the route response object is populated from the Google Maps Directions API `summary` field on each route object."

#### 🟡 Action 3 (Low urgency): Clarify null best_station handling in Story 3.3

**Add to Story 3.3 AC (under the card render criteria):**
> "If `best_station` is `null` (no reachable stations on this route), the card renders in the gray no-stations state as fully specified in Story 3.5."

#### 🟡 Action 4 (Optional): Amber indicator threshold decision

Either accept ≤ 50 km as the threshold (no change needed) or update Story 3.5 to make it dynamic. Leaving it as-is is fine for MVP.

---

### Final Note

This assessment identified **5 issues** across **2 categories** (1 architectural conflict, 4 story-level gaps). The single major issue (Alpine.js conflict) is easy to resolve with a one-line AC addition. The minor items are implementation detail gaps that a skilled dev agent would likely resolve correctly, but making them explicit reduces ambiguity. The overall quality of the planning artifacts is high — comprehensive, internally consistent, and ready for the developer agent to begin with Story 1.1.

