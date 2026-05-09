---
stepsCompleted:
  - step-01-init
  - step-02-context
  - step-03-starter
  - step-04-decisions
  - step-05-patterns
  - step-06-structure
  - step-07-validation
  - step-08-complete
  - update-anomaly-filter-2026-05-01
lastStep: 8
status: 'complete'
completedAt: '2026-04-30'
lastUpdated: '2026-05-09'
updateHistory:
  - date: '2026-05-01'
    changes: 'Added anomaly detection (FR38-FR42): detect_stale_prices() in api/pricing.py, updated data flow, directory structure, requirements mapping, gap analysis (gaps 4-6: filter order, stations.yaml schema, ANOMALY_THRESHOLD_CAD constant), validation FR count 35→42'
  - date: '2026-05-09'
    changes: 'Extended Epic 4 (FR43–FR47): bidirectional anomaly detection (expensive direction), worst_station field in /api/plan route object, red AdvancedMarkerElement map marker for most expensive reachable station; FR count 42→47; updated data flow, requirements mapping, validation spot-checks, gap analysis gaps 4+6'
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/product-brief-gaz_eye.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
  - _bmad-output/project-context.md
  - docs/architecture.md
  - docs/development-guide.md
  - docs/project-overview.md
  - docs/source-tree-analysis.md
workflowType: 'architecture'
project_name: 'gaz_eye'
user_name: 'Olivier'
date: '2026-04-30'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:** 47 FRs across seven domains:
- Trip Input (FR1–FR6): origin, destination, range, optional waypoints
- Route Discovery (FR7–FR10): Google Maps Directions API integration, polyline decoding
- Station Discovery (FR11–FR15): Régie Essence GeoJSON fetch, corridor matching (Haversine), fuel type filtering
- Price Quality Filtering (FR38–FR47): spatial stale-price anomaly detection **bidirectional** (cheap + expensive direction), density-adaptive neighbor radius, structural discounter exemption list (applied bidirectionally), kill switch, structured exclusion logging, `worst_station` in `/api/plan` response, red `AdvancedMarkerElement` map pin for most expensive reachable station
- Autonomy Filtering (FR16–FR18): distance-to-station calculation, safety buffer enforcement
- Recommendation Engine (FR19–FR23): cheapest/worst station per route, per-litre and per-tank savings, route ranking
- Map & Display (FR24–FR30, FR46–FR47): interactive Google Maps JS rendering, bi-directional card/map sync, data freshness indicator, distinct red marker for most expensive reachable station per route

**Non-Functional Requirements:**
- **Performance:** Full pipeline (API + compute + render) completes within a few seconds
- **Accuracy:** Savings calculations within ¢0.1/L of live Régie Essence data
- **Safety:** Autonomy filter never recommends a station beyond remaining range minus safety buffer
- **Resilience:** Graceful degradation on Régie Essence endpoint failure (error display, no crash)
- **Platform:** macOS laptop, Chrome/Safari latest — no multi-browser matrix, no mobile requirement

**Scale & Complexity:**
- Primary domain: Full-stack web application (locally-hosted SPA)
- Complexity level: Low-medium — single user, no auth, no DB, no compliance; geospatial algorithm layer is the primary engineering challenge
- Estimated architectural components: ~6 (backend API server, routing client, GeoJSON client, geospatial engine, recommendation engine, frontend SPA)

### Technical Constraints & Dependencies

- **Brownfield:** `gaz_saver.py` (270 LOC) must be extracted from a runnable script into an importable Python module; `parse_price_value`, `fetch_stations`, and GeoJSON dual-parse logic are reused verbatim
- **API key isolation:** Google Maps Directions API key must remain server-side — never exposed in frontend JavaScript or network responses
- **GeoJSON dual-parse:** Régie Essence endpoint may return pre-decompressed JSON or raw gzip — dual-parse strategy must be preserved from existing code
- **Google Maps JS API ToS:** Map rendering uses the JavaScript API (compliant); Directions calls are backend-only
- **Python 3.9+ required:** Existing codebase uses built-in generics (`dict[str, Any]`); no `typing` container imports
- **No database:** User settings persist via `localStorage` only; backend is stateless

### Cross-Cutting Concerns Identified

- **Polyline decoding** — Google Maps Directions API returns encoded polylines; decoding to lat/lng points is a prerequisite for all corridor matching. Net-new logic not present in existing codebase.
- **Haversine corridor matching** — for each route, find all GeoJSON stations within N km of any decoded polyline point. Core algorithm; must be efficient enough to run against the full Quebec station dataset (~3,000+ stations).
- **Configurability propagation** — corridor distance and safety buffer are user-configurable; these values must flow consistently from frontend settings → backend request → filtering logic.
- **Map ↔ card sync** — selecting a route card must highlight that route on the map, and vice versa; this is the primary frontend state management challenge.
- **Data freshness transparency** — the GeoJSON `generated_at` timestamp must be surfaced in the UI so the user can assess price staleness.

## Starter Template Evaluation

### Primary Technology Domain

Full-stack web application (brownfield) — Python backend + browser-based SPA, locally hosted on macOS.
No traditional starter template applies; this section records the foundational stack decisions.

### Stack Selection: Flask 3.1.3 + Vanilla JS

**Rationale:** Flask 3.1.3 (Python ≥3.9) preserves the existing Python version constraint.
Its functional decorator model aligns with the project's no-class convention.
No JavaScript build tooling is needed for a single-user local tool — vanilla JS with
ES modules keeps the tech stack entirely in Python + plain HTML/JS.

**Backend initialization:**

```bash
pip install flask==3.1.3
```

**Architectural Decisions Established:**

**Language & Runtime:** Python 3.9+, WSGI synchronous (Flask + Werkzeug dev server)

**Project Structure:**
```
app.py                # Flask application entry point
api/
  routes.py           # @app.route endpoint handlers
  geo.py              # Polyline decoding + Haversine corridor matching (net-new)
  pricing.py          # Extracted from gaz_saver.py: fetch_stations, parse_price_value
static/
  index.html          # SPA shell
  js/
    app.js            # Main SPA logic (ES modules)
    map.js            # Google Maps JS API integration
    state.js          # Route selection state + card/map bidirectional sync
  css/
    style.css
```

**Frontend:** Vanilla JS ES modules, no bundler, no framework. Google Maps JS API via CDN.
Settings (fuel type, tank size, corridor, buffer) persisted via `localStorage`.

**Static Serving:** Flask serves `/static` natively; root route (`/`) serves `index.html`.

**Development:** `flask --app app run --debug` (hot reload enabled)

**Note:** Project restructuring (extracting `gaz_saver.py` into `api/pricing.py` and
creating `app.py`) should be the first implementation story.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- API shape: single `/api/plan` endpoint
- API key isolation: environment variable, never in frontend
- Hard fail on external service errors

**Important Decisions (Shape Architecture):**
- Frontend state: singleton module pattern
- Project launch: `run.sh` script

**Deferred Decisions (Post-MVP):**
- Progressive rendering / two-step API (Phase 2 if latency becomes an issue)
- Graceful degradation for Régie Essence outages (Phase 2)

### Data Architecture

- **No database.** Backend is fully stateless. All persistent state lives in the browser (`localStorage`).
- **Data flow per request:** `run.sh` → Flask → `/api/plan` → [Google Maps Directions API + Régie Essence GeoJSON] → geospatial engine → recommendation engine → JSON response → frontend render.
- **Settings schema** (stored in `localStorage`): `{ fuel_type, tank_litres, corridor_km, safety_buffer_km }`. Defaults match PRD: corridor 2 km, buffer = max(10% of range, 15 km).

### Authentication & Security

- **No authentication.** Single-user local tool on `localhost`. No login, no sessions, no CSRF surface.
- **API key isolation:** `GOOGLE_MAPS_API_KEY` loaded from environment variable at Flask startup. Loaded via `python-dotenv` from a `.env` file listed in `.gitignore`. Key is **never** included in any JSON response or frontend-accessible route.
- **No CORS configuration needed** — frontend and backend share the same Flask origin (`localhost:5000`).

### API & Communication Patterns

- **Single endpoint:** `POST /api/plan`
  - Request body: `{ origin, destination, range_km, waypoints[], fuel_type, corridor_km, buffer_km }`
  - Response: `{ routes: [{ label, drive_time, polyline, stations: [...], best_station, savings_per_litre, savings_per_tank }], data_timestamp, error? }`
- **Hard fail policy:** If Google Maps Directions API fails OR Régie Essence GeoJSON fetch fails, the endpoint returns HTTP 502 with a structured error body `{ error: "source", message: "..." }`. Rationale: without live pricing, route cost comparison has no value.
- **Static file serving:** Flask root route (`GET /`) serves `static/index.html`. All other static assets served from `/static/`.
- **Error response schema:** `{ error: "google_maps" | "regie_essence" | "internal", message: string }`

### Frontend Architecture

- **State management:** `state.js` exports a singleton object with:
  - `state.routes[]` — loaded results
  - `state.selectedRouteIndex` — currently highlighted route
  - `state.setSelectedRoute(index)` — updates selection and fires a DOM `CustomEvent("routeSelected")` that both `map.js` and card components listen to
  - `state.settings` — mirrored from `localStorage`
- **Module structure:** ES modules (`type="module"`), no bundler. `app.js` is the entry point; it imports `map.js`, `state.js`, and handles form submission + card rendering.
- **Google Maps JS API:** Loaded via CDN `<script>` tag with `loading=async` and `callback=initMap`. Map instance stored in `map.js` module scope.
- **Bidirectional sync:** Card clicks call `state.setSelectedRoute(index)`; map marker clicks call the same function. The `routeSelected` CustomEvent triggers visual updates in both surfaces.

### Infrastructure & Deployment

- **Launch:** `run.sh` — sets `FLASK_APP=app.py`, `FLASK_ENV=development`, loads `.env` if present, then executes `flask run`. Single command for the developer.
- **No CI/CD.** Personal local tool.
- **Logging:** Follows project context rule — `logging.Logger` with `StreamHandler(sys.stdout)`, `%(message)s` format. Flask access logs suppressed or minimal.
- **`.gitignore` additions:** `.env`, `__pycache__/`, `*.pyc`

### Decision Impact Analysis

**Implementation Sequence (ordered by dependency):**
1. Extract `api/pricing.py` from `gaz_saver.py` (prerequisite for everything)
2. Create `app.py` + `run.sh` + Flask skeleton
3. Implement `api/geo.py` (polyline decoding + Haversine)
4. Implement `POST /api/plan` route wiring all components together
5. Build `static/index.html` + form + card layout
6. Implement `state.js` singleton + `map.js` Google Maps integration
7. Wire card ↔ map bidirectional sync
8. Implement settings drawer + `localStorage` persistence

**Cross-Component Dependencies:**
- `api/geo.py` is a hard dependency of `routes.py` — cannot implement the endpoint without polyline decoding
- `api/pricing.py` must preserve `parse_price_value` and `fetch_stations` signatures exactly — downstream recommendation logic depends on them
- `state.js` must be initialized before `map.js` and card rendering — it is the single source of truth for selection state

## Implementation Patterns & Consistency Rules

### Critical Conflict Points (9 identified)

API response shape, JSON field naming convention, Flask route registration location,
localStorage key management, loading/error UI ownership, Google Maps init callback,
DOM custom event naming, HTTP status code usage, settings defaults location.

### Naming Patterns

**API JSON fields:** `snake_case` throughout. No camelCase translation layer.
Example: `drive_time_seconds`, `savings_per_litre`, `distance_from_origin_km`

**Flask route functions:** `snake_case`, verb-prefixed.
Example: `plan_trip()`, `serve_index()`

**JavaScript functions:** `camelCase`.
Example: `setSelectedRoute()`, `renderCards()`, `initMap()`

**JavaScript files:** `snake_case`.
Example: `state.js`, `map.js`, `app.js`

**`localStorage` keys:** `SCREAMING_SNAKE_CASE` constants, defined only in `state.js`.
```js
const SETTINGS_KEY = "gaz_eye_settings";  // defined once, referenced everywhere
```
Never use raw string literals for localStorage keys outside `state.js`.

**DOM Custom Events:** `camelCase`.
Example: `routeSelected`, `resultsLoaded`, `planError`

### API Format Patterns

**Success response** — direct JSON, no wrapper:
```json
{
  "routes": [...],
  "data_timestamp": "2026-04-30T18:00:00Z"
}
```

**Error response:**
```json
{ "error": "regie_essence", "message": "Failed to fetch GeoJSON: connection timeout" }
```
HTTP status codes: `400` bad input, `502` upstream failure (Google Maps or Régie Essence), `500` unexpected internal error.

**Route object schema:**
```json
{
  "label": "Via Hwy 50",
  "drive_time_seconds": 8040,
  "drive_time_display": "2 h 14 min",
  "polyline_encoded": "...",
  "stations": [...],
  "best_station": { ... },
  "worst_station": { ... },
  "savings_per_litre": 0.082,
  "savings_per_tank_litres": 3.28
}
```

**Station object schema:**
```json
{
  "name": "Ultramar Lachute",
  "address": "123 rue Principale, Lachute",
  "price_per_litre": 1.429,
  "distance_from_route_km": 0.4,
  "distance_from_origin_km": 87.2,
  "lat": 45.851,
  "lng": -74.334,
  "is_best": true
}
```

### Structure Patterns

**Flask route registration:** All routes in `api/routes.py` via a Flask Blueprint.
`app.py` creates the app and registers the blueprint only — zero routes in `app.py`.

```python
# app.py — correct
from api.routes import bp
app.register_blueprint(bp)

# app.py — WRONG, never do this
@app.route("/api/plan")
def plan_trip(): ...
```

**Module responsibilities (strict):**
- `api/pricing.py` — GeoJSON fetch, price parsing, autonomy filtering. Ported from `gaz_saver.py`.
- `api/geo.py` — polyline decoding, Haversine distance. All geospatial math lives here.
- `api/routes.py` — HTTP layer only. Calls functions from `pricing.py` and `geo.py`. No business logic inline.

**Settings defaults:** Defined once in `state.js` as `DEFAULT_SETTINGS`. Never hardcoded elsewhere.
```js
const DEFAULT_SETTINGS = {
  fuel_type: "Régulier",
  tank_litres: 50,
  corridor_km: 2.0,
  safety_buffer_km: 15
};
```

### Process Patterns

**Loading state:** Owned exclusively by `app.js`.
```js
// app.js — correct
document.body.classList.add("is-loading");
// ... fetch ...
document.body.classList.remove("is-loading");
```
No other module adds/removes `is-loading`.

**Error display:** Owned exclusively by `app.js` via `#error-banner`.
```js
// app.js — correct
const banner = document.getElementById("error-banner");
banner.textContent = message;
banner.hidden = false;
```
No other module touches `#error-banner`.

**Google Maps init callback:** Always `window.initMap`, always defined in `map.js`.
```js
// map.js
export function initMap() { ... }
window.initMap = initMap;
```
Never defined inline in `index.html` script tags.

### Enforcement Guidelines

**All AI agents MUST:**
- Use `snake_case` for all Python identifiers and all JSON API fields
- Use `camelCase` for all JavaScript functions and variables
- Register Flask routes only in `api/routes.py` via Blueprint
- Never inline business logic in route handlers — delegate to `pricing.py` or `geo.py`
- Never duplicate `DEFAULT_SETTINGS` or `SETTINGS_KEY` — import from `state.js`
- Never use string literals for localStorage keys outside `state.js`
- Never define `initMap` outside `map.js`

**Anti-patterns to avoid:**
- ❌ `@app.route(...)` in `app.py`
- ❌ Haversine calculation inline in a route handler
- ❌ `localStorage.setItem("settings", ...)` with a raw string key outside `state.js`
- ❌ `{ "data": { "routes": [...] } }` response wrapper
- ❌ `camelCase` JSON fields in API responses (e.g., `driveTime` instead of `drive_time_seconds`)

## Project Structure & Boundaries

### Complete Project Directory Structure

```
gaz_eye/
├── .env                          # GOOGLE_MAPS_API_KEY (gitignored)
├── .env.example                  # Template with key names, empty values
├── .gitignore                    # .env, __pycache__/, *.pyc
├── README.md
├── requirements.txt              # flask==3.1.3, python-dotenv, requests, pyyaml, colorama
├── run.sh                        # Launch script: loads .env, runs flask --app app run --debug
├── stations.yaml                 # Preserved (existing CLI)
├── gaz_saver.py                  # Preserved (existing CLI)
├── app.py                        # Flask app factory: creates app, registers Blueprint
├── api/
│   ├── __init__.py
│   ├── routes.py                 # Blueprint; POST /api/plan
│   ├── pricing.py                # fetch_stations, parse_price_value, detect_stale_prices,
│   │                             # filter_by_autonomy, build_recommendation — ported from
│   │                             # gaz_saver.py + anomaly detection (net-new)
│   └── geo.py                    # decode_polyline, haversine, find_stations_in_corridor,
│                                 # distance_along_route
├── static/
│   ├── index.html                # SPA shell: form, #route-cards, #error-banner, map container
│   ├── css/
│   │   └── style.css             # Layout, card styles, loading overlay, map container
│   └── js/
│       ├── app.js            # Entry point: form submit, fetch /api/plan, renderCards(),
│       │                         # loading state (is-loading), error display (#error-banner)
│       ├── map.js            # Google Maps JS API: initMap(), renderRoutes(), renderMarkers(),
│       │                         # window.initMap = initMap
│       └── state.js          # Singleton: DEFAULT_SETTINGS, SETTINGS_KEY, state object,
│                                 # setSelectedRoute(), loadSettings(), saveSettings()
└── tests/
    ├── __init__.py
    ├── test_pricing.py           # Unit tests: parse_price_value(), filter_by_autonomy(),
    │                             # build_recommendation() — mock requests.get
    ├── test_geo.py               # Unit tests: haversine(), decode_polyline(),
    │                             # find_stations_in_corridor() — pure function tests
    └── test_routes.py            # Integration tests: POST /api/plan — mock pricing + geo
```

### Architectural Boundaries

**Module responsibilities (enforced):**
- `api/routes.py` — HTTP layer only; calls `pricing.py` and `geo.py`
- `api/pricing.py` — GeoJSON fetch, price parsing, anomaly filter, autonomy filter, recommendation builder
- `api/geo.py` — polyline decode, Haversine, corridor matching
- `app.js` — owns loading state (`is-loading`) and error display (`#error-banner`)
- `state.js` — owns all `localStorage` access and route selection state
- `map.js` — owns Google Maps instance and all map rendering

**Data flow:**
```
form submit → POST /api/plan → [Google Maps API + Régie Essence GeoJSON]
  → geo.py (decode + corridor)
  → pricing.py detect_stale_prices()   ← anomaly filter bidirectional (cheap + expensive direction)
  → pricing.py filter_by_autonomy()    ← autonomy filter
  → pricing.py build_recommendation()  ← derives worst_station (most expensive non-anomalous reachable station)
  → JSON response → app.js renderCards() → state.setSelectedRoute(0)
  → CustomEvent("routeSelected") → map.js renderRoutes() + renderMarkers()
  → map.js renders worst_station as red AdvancedMarkerElement (--error: #DC2626)
```

### Requirements to Structure Mapping

| FR Domain | File(s) |
|---|---|
| FR1–FR6 Trip Input | `static/index.html`, `static/js/app.js` |
| FR7–FR10 Route Discovery + Polyline | `api/routes.py`, `api/geo.py` |
| FR11–FR15 Station Discovery | `api/pricing.py`, `api/geo.py` |
| FR38–FR44 Price Quality Filtering | `api/pricing.py` (`detect_stale_prices()` — bidirectional cheap + expensive) |
| FR45 `worst_station` in `/api/plan` response | `api/pricing.py` (`build_recommendation()`), `api/routes.py` |
| FR46–FR47 Most Expensive Station Marker | `static/js/map.js` (`renderMarkers()`) |
| FR16–FR18 Autonomy Filtering | `api/pricing.py` |
| FR19–FR23 Recommendation Engine | `api/pricing.py` |
| FR24–FR27 Map Visualization | `static/js/map.js` |
| FR28–FR30 Recommendation Display | `static/js/app.js` |
| Settings persistence | `static/js/state.js` |

### Integration Points

**External integrations:**
- Google Maps Directions API — called from `api/routes.py`, key from `GOOGLE_MAPS_API_KEY` env var
- Google Maps JavaScript API — loaded via CDN `<script>` in `index.html`, callback `window.initMap`
- Régie Essence GeoJSON endpoint — called from `api/pricing.py`, User-Agent header required

**Internal communication:**
- Backend modules communicate via direct Python function calls
- Frontend modules communicate via `state.setSelectedRoute()` + `CustomEvent("routeSelected")`
- `app.js` → `state.js` and `map.js` via ES module imports + custom events

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
- Flask 3.1.3 requires Python ≥3.9 — matches project constraint exactly
- `python-dotenv` integrates cleanly with Flask's app factory pattern
- Vanilla JS ES modules natively supported in Chrome/Safari latest — no polyfills needed
- Google Maps JS API CDN + `type="module"` scripts coexist without conflict
- No version conflicts across the full stack

**Pattern Consistency:**
- `snake_case` API fields align with Python backend; no translation layer introduced
- Blueprint pattern in `api/routes.py` is consistent with Flask conventions and the no-class rule
- `CustomEvent` pattern is native DOM — no library dependency introduced
- `localStorage` singleton in `state.js` is consistent with the stateless backend decision

**Structure Alignment:**
- Every module boundary has a documented responsibility
- `app.py` as pure factory (no routes) enforced by anti-pattern rule
- `tests/` structure matches project context rules: pytest, `tests/` dir, `test_<module>.py` naming

### Requirements Coverage Validation ✅

**Functional Requirements (47 FRs) — all covered.**

Spot-checks on hardest FRs:

| FR | Coverage |
|---|---|
| FR38 — detect stale stations below local median | `api/pricing.py` `detect_stale_prices()` |
| FR39 — density-adaptive radius (expand until ≥5 neighbors) | `api/pricing.py` `detect_stale_prices()` |
| FR40 — structural discounter exemption list | `stations.yaml` `anomaly_filter_exemptions`; checked in `detect_stale_prices()` |
| FR41 — kill switch (disable without code deploy) | `stations.yaml` `anomaly_filter_enabled`; checked in `api/routes.py` before calling filter |
| FR42 — structured log entry per excluded station | `gaz_eye.pricing` logger in `detect_stale_prices()` |
| FR43 — detect stale stations above local median (expensive direction) | `api/pricing.py` `detect_stale_prices()` — same `ANOMALY_THRESHOLD_CAD`, same exemption list, same log format |
| FR44 — bidirectional anomaly detection | `api/pricing.py` `detect_stale_prices()` — both directions in one call; `float('inf')` sentinel applied to cheap and expensive outliers |
| FR45 — `worst_station` field in `/api/plan` response | `api/pricing.py` `build_recommendation()` returns most expensive non-anomalous reachable station; `api/routes.py` includes it in the route object |
| FR46 — red map marker for most expensive station | `static/js/map.js` `renderMarkers()` — red `AdvancedMarkerElement` (`--error: #DC2626`); always derived from post-filter station list |
| FR47 — hover + enlarge behaviour for worst marker | `static/js/map.js` `renderMarkers()` — hover tooltip with name + price; enlarges on `routeSelected` event matching cheapest marker behaviour |
| FR10 — decode route polylines | `api/geo.py` `decode_polyline()` |
| FR12 — Haversine corridor matching | `api/geo.py` `find_stations_in_corridor()` |
| FR16 — distance from origin to station | `api/geo.py` `distance_along_route()` |
| FR17 — autonomy filter with safety buffer | `api/pricing.py` `filter_by_autonomy()` |
| FR18 — no reachable stations case | empty `stations[]` response; `app.js` renders "no stations" message |
| FR27 — station marker interaction | `map.js` `renderMarkers()` click handler → `state.setSelectedRoute()` |
| FR30 — data freshness timestamp | `data_timestamp` field in API response; rendered in `app.js` |

**Non-Functional Requirements:**
- Performance: single `/api/plan` endpoint; GeoJSON fetched once per request, filtered in-memory
- Accuracy: `parse_price_value()` reused verbatim from battle-tested `gaz_saver.py`
- Safety: `filter_by_autonomy()` gates all recommendations — no out-of-range station can reach `build_recommendation()`
- API key security: key never leaves `api/routes.py`; no frontend route exposes it
- Resilience: HTTP 502 + structured error body on upstream failure; `#error-banner` displays it

### Implementation Readiness Validation ✅

- **Decision Completeness:** All critical decisions documented with versions, rationale, and anti-patterns
- **Structure Completeness:** Every file named, every module's public API described
- **Pattern Completeness:** 9 conflict points identified and resolved; enforcement guidelines documented

### Gap Analysis

**Critical Gaps: None.**

**Important Gaps (must be addressed in implementation stories):**

1. **`decode_polyline()` algorithm** — Use the `polyline` PyPI package (`pip install polyline`) rather than implementing the Google Encoded Polyline Algorithm from scratch. Add `polyline` to `requirements.txt`.

2. **`distance_along_route()` semantics** — Distance from origin to station is the cumulative distance along the route polyline to the nearest polyline point, not straight-line distance. Implementation story must specify this clearly.

3. **Google Maps JS API key in `index.html`** — The Maps JavaScript API key is a separate concern from the Directions API key. It must be injected into `index.html` at serve time by Flask (via template rendering), not hardcoded in the static file. Add `GOOGLE_MAPS_JS_KEY` as a second env var. Flask's root route should render `index.html` as a Jinja2 template.

4. **Anomaly filter placement in `api/pricing.py`** — `detect_stale_prices(stations, all_stations, threshold, exemptions)` must be called in `routes.py` **after** corridor matching and **before** `filter_by_autonomy()`. This order is mandatory: the anomaly filter requires the full `all_stations` dataset (for neighbor lookup), so it must run while that dataset is still in scope. The filter is **bidirectional**: stations priced more than `ANOMALY_THRESHOLD_CAD` below *or* above the local median are both set to `float('inf')` — cheap-direction exclusions prevent inflated savings; expensive-direction exclusions prevent `worst_station` from being set by a stale high-price outlier.

5. **`stations.yaml` config schema additions** — Two new top-level keys are required:
   - `anomaly_filter_enabled: true` (boolean kill switch; default `true`)
   - `anomaly_filter_exemptions: ["costco", "olco"]` (list of case-insensitive name substrings)
   These must be loaded and passed through from `fetch_stations()` into the route handler, then forwarded to `detect_stale_prices()`. No UI exposure required.

6. **`ANOMALY_THRESHOLD_CAD` constant** — Defined once in `api/pricing.py` as `ANOMALY_THRESHOLD_CAD = 0.05` (i.e., 5¢/L). Applied **bidirectionally** (both cheap and expensive direction) using the same threshold value. Never hardcoded elsewhere. Configurable only by editing this constant — not a user-facing setting.

**Nice-to-Have:**
- `run.sh` should check if `.env` exists and warn if `GOOGLE_MAPS_API_KEY` is unset
- Phase 2: Graceful Régie Essence degradation (show routes without pricing)
- Phase 2: `distance_along_route()` upgraded to driving distance via Maps Roads API

### Architecture Completeness Checklist

**Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status: READY FOR IMPLEMENTATION**
**Confidence Level: High**

**Key Strengths:**
- Brownfield extraction risk mitigated: `pricing.py` is a direct port, not a rewrite
- The hardest algorithm (`geo.py`) is fully isolated and independently testable
- Zero ambiguity in module ownership — every piece of state and every UI concern has exactly one owner
- Gap around `decode_polyline()` flagged with a concrete solution (`polyline` package)

**Areas for Future Enhancement:**
- Phase 2: Graceful Régie Essence degradation
- Phase 2: Driving-distance routing to stations (vs. crow-flies)
- Phase 3: Google Maps JS key injection hardened via server-side template rendering

### Implementation Handoff

**AI Agent Guidelines:**
- Read `_bmad-output/project-context.md` before writing any code
- Follow all architectural decisions exactly as documented in this file
- Use implementation patterns from the Consistency Rules section for every file created
- Respect module boundaries — never inline business logic in route handlers
- Address the 3 Important Gaps in the first implementation stories

**First Implementation Priority:**
1. Add `polyline` to `requirements.txt`
2. Add `GOOGLE_MAPS_JS_KEY` to `.env.example`
3. Extract `api/pricing.py` from `gaz_saver.py`
4. Create `app.py` Flask factory + `run.sh`
