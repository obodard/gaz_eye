---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
status: complete
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
---

# gaz_eye - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for gaz_eye, decomposing the requirements from the PRD, UX Design, and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: User can enter a trip origin as a text address or place name
FR2: User can enter a trip destination as a text address or place name
FR3: User can enter remaining driving range in kilometers
FR4: User can add one or more optional intermediate waypoints to force a route through a specific location
FR5: User can remove a previously added waypoint
FR6: User can submit a trip query and receive results
FR7: System can fetch 3 alternative routes from Google Maps Directions API for the given origin, destination, and waypoints
FR8: System can display drive time and distance for each route
FR9: System can handle cross-province routes (e.g., Quebec ↔ Ontario) as valid alternatives
FR10: System can decode route polylines into geographic waypoints for corridor matching
FR11: System can fetch the complete Régie Essence Québec GeoJSON dataset (all Quebec gas stations with GPS coordinates and current prices)
FR12: System can identify all Quebec gas stations within a configurable corridor distance of a route polyline (default: 2 km, Haversine)
FR13: System can parse gas prices from the Régie Essence cent-string format into dollar values
FR14: System can handle unavailable or missing price data gracefully (display as "n/a", exclude from recommendations)
FR15: System can filter stations by the user's selected fuel type (Régulier, Super, or Diesel)
FR16: System can calculate the distance from the trip origin to each discovered station along the route
FR17: System can exclude stations that are beyond the user's remaining driving range minus a configurable safety buffer (default: 10% of range or 15 km, whichever is greater)
FR18: System can handle the case where no stations are reachable on a given route (display a clear message)
FR19: System can identify the cheapest reachable Quebec station for each route
FR20: System can identify the most expensive reachable Quebec station for each route
FR21: System can calculate savings per litre between the cheapest and most expensive reachable stations on each route
FR22: System can calculate total tank savings based on the configured tank size
FR23: System can rank the three routes by fuel cost to highlight the best option
FR24: User can view all three routes displayed simultaneously on an interactive map with visually distinct styling
FR25: User can view gas station markers on the map with price labels
FR26: User can distinguish between the recommended station and other stations on each route
FR27: User can interact with station markers to see station details (name, address, price, brand)
FR28: User can view a comparison panel showing all three routes side by side with drive time, best station, fuel price, and savings
FR29: User can see the savings amount (per litre and per tank) for each route's recommendation vs. worst option
FR30: User can see the Régie Essence data timestamp to assess price freshness
FR31: User can configure fuel type (Régulier / Super / Diesel)
FR32: User can configure tank size in litres
FR33: User can configure corridor distance (km from route polyline)
FR34: User can configure the autonomy safety buffer
FR35: System can display a meaningful error when the Régie Essence GeoJSON endpoint is unavailable
FR36: System can display a meaningful error when the Google Maps API returns no routes
FR37: System can handle Google Maps API errors (invalid addresses, quota exceeded) with user-friendly messages

### NonFunctional Requirements

NFR1: Route query results (3 routes + station discovery + recommendations) render within 5 seconds of user submission, given normal network conditions
NFR2: Map with 3 routes and up to 50 station markers renders without visible lag or jank
NFR3: Régie Essence GeoJSON dataset (gzip-compressed, all Quebec stations) is fetched and parsed within 3 seconds
NFR4: Corridor matching (Haversine distance for all stations against route polyline) completes within 1 second for a 300 km route
NFR5: Google Maps API key is stored server-side only — never exposed to the frontend or included in client-side source
NFR6: No user data is persisted, logged, or transmitted beyond the local machine
NFR7: Google Maps Directions API integration uses the `alternatives=true` parameter to request 3 routes per query
NFR8: Régie Essence GeoJSON endpoint integration handles both pre-decompressed JSON and raw gzip responses (dual-parse strategy)
NFR9: Régie Essence endpoint requires a browser-like User-Agent header — requests must include one to avoid being blocked
NFR10: Google Maps JavaScript API is used for map rendering to comply with Google Maps Platform Terms of Service

### Additional Requirements

- Brownfield restructuring: Extract `gaz_saver.py` into `api/pricing.py` as an importable module preserving `parse_price_value`, `fetch_stations`, and GeoJSON dual-parse logic verbatim — this is a prerequisite for all other backend work
- Polyline decoding: Use the `polyline` PyPI package (add to `requirements.txt`) instead of implementing the Google Encoded Polyline Algorithm from scratch
- Google Maps JS API key injection: `GOOGLE_MAPS_API_KEY` (single env var) must be injected into `index.html` at serve time via Jinja2 template rendering — not hardcoded in the static file
- API key isolation: `GOOGLE_MAPS_API_KEY` loaded from `.env` via `python-dotenv`; never included in any JSON response or frontend-accessible route (Jinja2 injection into the script src tag is the only frontend exposure)
- `distance_along_route()` semantics: Distance from origin to station is the cumulative distance along the route polyline to the nearest polyline point — not a straight-line distance; must be documented clearly in the implementation story
- Flask Blueprint pattern: All routes registered in `api/routes.py` via a Blueprint; `app.py` is a pure factory with zero routes
- Settings defaults: `DEFAULT_SETTINGS` and `SETTINGS_KEY = "gaz_eye_settings"` defined once in `state.js` only — never duplicated elsewhere
- `run.sh` launch script: Sets `FLASK_APP=app.py`, `FLASK_ENV=development`, loads `.env`, runs `flask run`; must warn if `GOOGLE_MAPS_API_KEY` is unset — single key used for both backend Directions API and frontend JS API injection
- Tests: `tests/` directory at project root with `pytest`; `test_pricing.py`, `test_geo.py`, `test_routes.py`; mock `requests.get` for all network calls
- `.gitignore` requirements: `.env`, `__pycache__/`, `*.pyc`

### UX Design Requirements

UX-DR1: Implement a split-pane layout — fixed-width cards panel (`w-96` / ~384px) on the left and a `flex-1` Google Maps container on the right; full-viewport height below the header; cards panel is scrollable
UX-DR2: Implement route colour coding — Route A: blue-600 (`#2563EB`), Route B: purple-600 (`#9333EA`), Route C: orange-600 (`#EA580C`); each colour ties the card's 4px left border strip to the map polyline visually
UX-DR3: Implement the `<RouteCard>` component with all 6 states: Default (white bg, gray-200 border), Hover (shadow-sm), Selected (2px route-colour border + ring-1, other cards opacity-50), Best-value (green-100 bg + green-500 border-2 + "Best value" badge), Best-value+selected, No-stations (gray bg + km shortfall message, non-interactive)
UX-DR4: Implement skeleton loading cards (card-shaped animated pulse blocks matching loaded card dimensions exactly); submit button disabled with spinner icon while loading; map shows semi-transparent overlay with centered spinner — no layout shift on results render
UX-DR5: Implement `<SettingsDrawer>` — right-side panel (`w-72`) sliding in from the right with 200ms ease `translateX` transition; 5 settings: fuel type toggle (Regular/Premium/Diesel), tank size number input, corridor radius slider (1–10 km), safety buffer slider (5–50 km), max alternatives toggle (2/3); all changes persist to localStorage `onChange` with no Save button required; close with × or click overlay
UX-DR6: Implement bidirectional map ↔ card sync: `state.setSelectedRoute(index)` fires `CustomEvent("routeSelected")`; both `map.js` and card components listen to this event; clicking a card or a map polyline both call `setSelectedRoute()`; selected route polyline bolds, other cards dim to opacity-50
UX-DR7: Implement inline waypoint field expansion: ghost `+ Add waypoint` text button below destination field; on click, appends a labeled text input with an inline `×` remove button; max 1 waypoint in MVP; `+ Add waypoint` button hides after one is added
UX-DR8: Implement custom `<StationMarker>` via `AdvancedMarkerElement` — circular pin in route colour with white fuel-pump icon SVG; selected marker larger (20px vs 14px) with white border ring; hover shows InfoWindow tooltip with station name + price
UX-DR9: Implement the low-range urgency state — amber border (`border-amber-400`) on the range field when range is low; inline amber banner inside cards panel ("X stations reachable · Y km buffer active"); route cards with no reachable stations in gray non-interactive state displaying "Nearest station is X km — Y km beyond your range"
UX-DR10: Implement data display formatting standards throughout the UI: price as `154.9 ¢/L` (never `$1.549`); drive time as `2 h 14 min`; distance as 1 decimal if < 10 km, no decimal if ≥ 10 km; dollar savings as `≈ Save $5.46` (only when tank size > 0); timestamp as `Updated Apr 29 at 23:15`
UX-DR11: Implement responsive/mobile layout — below 768px: stacked form → cards (full-width) → map (fixed 300px height); settings drawer becomes full-width bottom panel on mobile; form fields stack vertically; card padding increases to `p-5`; all interactive elements meet 44×44px minimum touch target
UX-DR12: Implement the initial empty state in the cards panel (before any trip is submitted): single muted prompt "Enter a trip above to see route options." — no empty card placeholders
UX-DR13: Implement the inline API error banner inside the cards panel: `bg-red-50 border-red-200 text-red-700` with message "Could not load [source]. Try again." — persistent until resolved, no toast notifications
UX-DR14: Apply the design token colour system as CSS custom properties: `--bg: #F9FAFB`, `--surface: #FFFFFF`, `--border: #E5E7EB`, `--text-primary: #111827`, `--text-secondary: #6B7280`, `--accent: #16A34A`, `--accent-light: #DCFCE7`, `--warning: #F59E0B`, `--error: #DC2626`
UX-DR15: Apply Inter (Google Fonts) typography system: drive time `text-2xl font-bold`, savings `text-xl font-bold`, price `text-lg font-semibold`, route label `text-base font-medium`, secondary data `text-sm`, timestamp `text-xs`
UX-DR16: Implement settings and last trip persistence via localStorage key `gaz_eye_settings`; on page load, pre-populate all form fields (including origin/destination) from last saved values

### FR Coverage Map

FR1: Epic 3 — Trip form: origin input
FR2: Epic 3 — Trip form: destination input
FR3: Epic 3 — Trip form: range input (km)
FR4: Epic 3 — Inline waypoint field expansion
FR5: Epic 3 — Waypoint × remove button
FR6: Epic 3 — "Find routes" form submission
FR7: Epic 2 — Google Maps Directions API fetch (alternatives=true)
FR8: Epic 2 — Drive time + distance from API response
FR9: Epic 2 — Cross-province route passthrough
FR10: Epic 2 — Polyline decode via `polyline` PyPI package
FR11: Epic 1 — Régie Essence GeoJSON fetch (dual-parse gzip/JSON)
FR12: Epic 2 — Haversine corridor matching against decoded polylines
FR13: Epic 1 — Cent-string price parsing (parse_price_value)
FR14: Epic 1 — Graceful handling of missing/unavailable prices
FR15: Epic 1 — Fuel type filter (Régulier/Super/Diesel)
FR16: Epic 1 — distance_along_route() from origin to station
FR17: Epic 1 — Autonomy filter: range − safety buffer
FR18: Epic 1 — Empty stations[] response case
FR19: Epic 1 — Cheapest reachable station per route
FR20: Epic 1 — Most expensive reachable station per route
FR21: Epic 1 — Savings per litre calculation
FR22: Epic 1 — Savings per tank calculation
FR23: Epic 1 — Route ranking by fuel cost
FR24: Epic 3 — 3 routes on map with distinct colour-coded polylines
FR25: Epic 3 — Station markers with price labels
FR26: Epic 3 — Recommended vs. other station visual distinction
FR27: Epic 3 — Station marker click → station detail tooltip
FR28: Epic 3 — 3-route comparison cards panel
FR29: Epic 3 — Savings ¢/L and $/tank on cards
FR30: Epic 3 — Régie Essence data timestamp display
FR31: Epic 3 — Fuel type setting in SettingsDrawer
FR32: Epic 3 — Tank size setting in SettingsDrawer
FR33: Epic 3 — Corridor distance setting in SettingsDrawer
FR34: Epic 3 — Safety buffer setting in SettingsDrawer
FR35: Epic 3 — Régie Essence error inline banner
FR36: Epic 3 — No routes found inline message
FR37: Epic 3 — Google Maps API error handling (invalid address, quota)

## Epic List

### Epic 1: Project Foundation & Pricing Engine

The Flask application scaffold and the complete Quebec gas station pricing pipeline are operational. `gaz_saver.py` is migrated into an importable `api/pricing.py` module, the Régie Essence GeoJSON can be fetched, parsed (dual-format), filtered by fuel type, and autonomy-filtered against a known driving range. The recommendation engine (cheapest/worst station, savings ¢/L, savings $/tank, route ranking) is fully implemented and unit-tested. The backend structure is in place for all subsequent epics.

**FRs covered:** FR11, FR13, FR14, FR15, FR16, FR17, FR18, FR19, FR20, FR21, FR22, FR23
**NFRs addressed:** NFR5 (API key server-side only), NFR6 (no data persistence beyond local), NFR8 (dual-parse gzip/JSON), NFR9 (User-Agent header)
**Architecture/UX requirements:** Brownfield extraction of gaz_saver.py → api/pricing.py, Flask Blueprint scaffold, app.py pure factory, run.sh, .env + python-dotenv (single GOOGLE_MAPS_API_KEY), requirements.txt, tests/test_pricing.py

---

### Epic 2: Route Planning API

A single `POST /api/plan` request returns three alternative Google Maps routes, each decorated with reachable Quebec gas stations, the cheapest recommendation, and savings — fully testable via `curl`. The geospatial engine (polyline decode + Haversine corridor + cumulative distance-along-route) is implemented, the `/api/plan` endpoint wires all components together, and the backend is 100% complete.

**FRs covered:** FR7, FR8, FR9, FR10, FR12
**NFRs addressed:** NFR3 (GeoJSON parsed within 3s), NFR4 (Haversine within 1s per 300 km route), NFR7 (alternatives=true)
**Architecture requirements:** api/geo.py (decode_polyline via `polyline` PyPI package, haversine, find_stations_in_corridor, distance_along_route — cumulative polyline distance), api/routes.py Blueprint wiring, tests/test_geo.py, tests/test_routes.py, GOOGLE_MAPS_API_KEY env var for Directions API

---

### Epic 3: Trip Planning SPA

Olivier can open `http://localhost:5000`, enter a trip (origin, destination, range, optional waypoint), and see three colour-coded route cards with fuel recommendations, savings, and a fully synced interactive map. Settings persist across sessions. Low-range urgency, empty states, and API errors are all handled gracefully. The product is complete and usable end-to-end.

**FRs covered:** FR1–FR6, FR24–FR37
**NFRs addressed:** NFR1 (5s full pipeline render), NFR2 (map render without lag), NFR10 (Google Maps JS API ToS compliance)
**UX-DRs addressed:** UX-DR1 through UX-DR16 (split-pane layout, route colour coding, RouteCard 6 states + skeleton, SettingsDrawer 5 settings, bidirectional map↔card sync, inline waypoint field, StationMarker custom pins, low-range urgency state, data formatting standards, responsive/mobile layout, empty state, error banner, design tokens, typography, localStorage persistence)
**Architecture requirements:** static/index.html as Jinja2 template (GOOGLE_MAPS_API_KEY injected into Maps JS script tag), state.js singleton (DEFAULT_SETTINGS, SETTINGS_KEY), map.js (window.initMap), app.js (loading state + error display ownership)

---

## Epic 1: Project Foundation & Pricing Engine

The Flask application scaffold and the complete Quebec gas station pricing pipeline are operational. `gaz_saver.py` is migrated into an importable `api/pricing.py` module, the Régie Essence GeoJSON can be fetched, parsed (dual-format), filtered by fuel type, and autonomy-filtered against a known driving range. The recommendation engine (cheapest/worst station, savings ¢/L, savings $/tank, route ranking) is fully implemented and unit-tested. The backend structure is in place for all subsequent epics.

### Story 1.1: Flask Project Scaffold

As a developer,
I want a runnable Flask application skeleton with the correct project structure, launch script, and environment configuration,
So that I have a working foundation to build all subsequent backend and frontend features on.

**Acceptance Criteria:**

**Given** the repository is cloned and `.env` contains `GOOGLE_MAPS_API_KEY=<any value>`
**When** I run `./run.sh`
**Then** Flask starts at `http://localhost:5000` with debug/hot-reload enabled
**And** `GET /` returns HTTP 200 with placeholder HTML containing "gaz_eye"
**And** a startup warning is printed to stdout if `GOOGLE_MAPS_API_KEY` is unset in the environment

**Given** the project structure after this story
**When** I inspect the repository
**Then** the following files exist: `app.py` (pure factory, zero `@app.route` decorators), `api/__init__.py`, `api/routes.py` (Blueprint registered in `app.py`, skeleton with no functional routes yet), `run.sh` (executable, sets `FLASK_APP=app.py` and `FLASK_ENV=development`, sources `.env`), `.env.example` (key names with empty values), `.gitignore` (includes `.env`, `__pycache__/`, `*.pyc`), and `requirements.txt` updated to include `flask==3.1.3` and `python-dotenv`
**And** `gaz_saver.py` and `stations.yaml` are preserved entirely unchanged

### Story 1.2: Pricing Module — GeoJSON Fetch & Price Parsing

As a developer,
I want the Régie Essence GeoJSON fetch and price parsing logic extracted from `gaz_saver.py` into an importable `api/pricing.py` module,
So that the backend can programmatically access live Quebec gas station data and prices without depending on the CLI entry point.

**Acceptance Criteria:**

**Given** `api/pricing.py` is imported
**When** `fetch_stations(fuel_type)` is called
**Then** it returns a list of station dicts from the Régie Essence GeoJSON endpoint, each containing at minimum `Address`, `Latitude`, `Longitude`, and the relevant price field for the given fuel type
**And** the function sends a browser-like `User-Agent` header with the HTTP request
**And** the function handles both pre-decompressed JSON and raw gzip responses (dual-parse: `json.loads()` first, fall back to `gzip.decompress()`)
**And** on network failure the function raises an exception (not `sys.exit()`) so callers can handle it
**And** stations with `IsAvailable: false` or missing price data have their price represented as `float('inf')`

**Given** a raw price string `"154.9¢"`
**When** `parse_price_value("154.9¢")` is called
**Then** it returns `1.549` (float, dollars per litre)

**Given** a missing or `None` price value
**When** `parse_price_value(None)` or `parse_price_value("")` is called
**Then** it returns `float('inf')` as the sentinel value

**Given** `gaz_saver.py` exists after the extraction
**When** it is run directly (`python gaz_saver.py`)
**Then** it still works correctly — the module extraction does not break the existing CLI

**Given** `tests/test_pricing.py` exists
**When** `pytest tests/test_pricing.py` is executed
**Then** all tests pass; `requests.get` is mocked throughout — the live Régie Essence endpoint is never called; tests cover `parse_price_value` with: valid cent-string, `None`, empty string, `¢`-only string, and a string without `¢`

### Story 1.3: Autonomy Filtering & Recommendation Engine

As a developer,
I want the backend to filter stations by driving autonomy and compute cheapest/worst recommendations with savings,
So that the `/api/plan` endpoint (built in Epic 2) can call these pure functions without containing any inline business logic.

**Acceptance Criteria:**

**Given** a list of stations each with `price_per_litre` and `distance_from_origin_km`, a `range_km` value, and a `buffer_km` value
**When** `filter_by_autonomy(stations, range_km, buffer_km)` is called
**Then** it returns only stations where `distance_from_origin_km <= range_km - buffer_km`
**And** if `buffer_km` is not provided, the default is `max(range_km * 0.10, 15)` km

**Given** a filtered list with zero stations
**When** `filter_by_autonomy(...)` is called
**Then** it returns an empty list without raising an error

**Given** a filtered list of reachable stations and a `tank_litres` value
**When** `build_recommendation(stations, tank_litres)` is called
**Then** it returns a dict with: `best_station` (dict, lowest `price_per_litre`), `worst_station` (dict, highest `price_per_litre`), `savings_per_litre` (float, difference between worst and best), `savings_per_tank` (float, `savings_per_litre * tank_litres`)
**And** stations with `price_per_litre == float('inf')` are excluded from best/worst selection

**Given** a list of per-route dicts each containing `savings_per_litre`
**When** `rank_routes(routes)` is called
**Then** it returns the same list with an added `rank` integer field where rank 1 = highest `savings_per_litre` (most savings = best value)

**Given** `tests/test_pricing.py` has tests for the new functions
**When** `pytest tests/test_pricing.py` is run
**Then** all tests pass; edge cases covered include: empty station list, all prices `float('inf')`, single station, two stations with identical prices, `tank_litres = 0`

---

## Epic 2: Route Planning API

A single `POST /api/plan` request returns three alternative Google Maps routes, each decorated with reachable Quebec gas stations, the cheapest recommendation, and savings — fully testable via `curl`. The geospatial engine (polyline decode + Haversine corridor + cumulative distance-along-route) is implemented, the `/api/plan` endpoint wires all components together, and the backend is 100% complete.

### Story 2.1: Geospatial Engine — Polyline Decode & Haversine Distance

As a developer,
I want the geospatial functions for decoding Google Maps encoded polylines and computing Haversine distances implemented and unit-tested,
So that corridor matching has a solid, independently-verified foundation before it is wired into the API endpoint.

**Acceptance Criteria:**

**Given** an encoded Google Maps polyline string
**When** `decode_polyline(encoded_string)` is called
**Then** it returns a list of `{"lat": float, "lng": float}` dicts representing the route path
**And** it uses the `polyline` PyPI package (not a hand-rolled implementation)
**And** `polyline` is added to `requirements.txt`

**Given** two lat/lng coordinate pairs
**When** `haversine(lat1, lng1, lat2, lng2)` is called
**Then** it returns the great-circle distance in kilometres as a float
**And** the result for Montréal (45.5017, -73.5673) to Laval (45.6066, -73.7124) is within ±0.5 km of the expected value (~13.5 km)
**And** passing the same point twice returns `0.0`

**Given** `api/geo.py` exists with `decode_polyline` and `haversine`
**When** `pytest tests/test_geo.py` is run
**Then** all tests pass; tests cover: `decode_polyline` round-trip with a known polyline, `haversine` known-distance pair, `haversine` same-point edge case

### Story 2.2: Station Corridor Discovery & Route Distance

As a developer,
I want the system to find all Quebec stations within a configurable corridor of a route polyline and calculate each station's cumulative distance from the trip origin,
So that the autonomy filter in `pricing.py` receives correctly-distanced stations to work with.

**Acceptance Criteria:**

**Given** a list of decoded route polyline points, a list of all Quebec stations (each with `lat`, `lng`), and a `corridor_km` value
**When** `find_stations_in_corridor(polyline_points, all_stations, corridor_km)` is called
**Then** it returns only stations where the minimum Haversine distance to any polyline point is ≤ `corridor_km`
**And** each returned station includes a `distance_from_route_km` field with that minimum distance

**Given** an empty station list
**When** `find_stations_in_corridor(polyline_points, [], corridor_km)` is called
**Then** it returns an empty list without error

**Given** a list of decoded route polyline points and a station lat/lng
**When** `distance_along_route(polyline_points, station_lat, station_lng)` is called
**Then** it returns the cumulative sum of polyline segment lengths (km) up to the segment point nearest to the station
**And** this is NOT a straight-line distance from origin — it is the sum of Haversine segment distances along the polyline

**Given** `pytest tests/test_geo.py` is run after these functions are added
**Then** new tests pass covering: station exactly on polyline (included), station beyond corridor (excluded), empty station list, `distance_along_route` for station nearest first point (≈0), nearest last point (≈total route length), and a midpoint station

### Story 2.3: POST /api/plan Endpoint

As Olivier,
I want a single `POST /api/plan` endpoint that accepts my trip parameters and returns three routes each with fuel recommendations,
So that I can verify the complete backend pipeline is working end-to-end before building the frontend.

**Acceptance Criteria:**

**Given** a valid POST request `{"origin": "Montréal, QC", "destination": "Duhamel, QC", "range_km": 200, "waypoints": [], "fuel_type": "Régulier", "corridor_km": 2.0, "buffer_km": 15}`
**When** `POST /api/plan` is called with live credentials
**Then** it returns HTTP 200 with a JSON body containing `routes` (array of route objects) and `data_timestamp` (ISO 8601 string)
**And** each route object contains: `label` (string), `drive_time_seconds` (int), `drive_time_display` (string, e.g. `"2 h 14 min"`), `polyline_encoded` (string), `stations` (array), `best_station` (object or null), `savings_per_litre` (float), `savings_per_tank_litres` (float)
**And** each station object contains: `name`, `address`, `price_per_litre` (float), `distance_from_route_km` (float), `distance_from_origin_km` (float), `lat` (float), `lng` (float), `is_best` (bool)
**And** the `GOOGLE_MAPS_API_KEY` value does not appear anywhere in the response body

**Given** the Google Maps Directions API call fails (network error or HTTP error)
**When** `POST /api/plan` is called
**Then** it returns HTTP 502 with body `{"error": "google_maps", "message": "<reason>"}`

**Given** the Régie Essence GeoJSON fetch fails
**When** `POST /api/plan` is called
**Then** it returns HTTP 502 with body `{"error": "regie_essence", "message": "<reason>"}`

**Given** the request body is missing required fields (`origin`, `destination`, or `range_km`)
**When** `POST /api/plan` is called
**Then** it returns HTTP 400 with body `{"error": "internal", "message": "<description of missing field>"}`

**Given** all route handlers live in `api/routes.py` via the Blueprint
**When** `app.py` is inspected
**Then** it contains zero `@app.route` decorators — only Blueprint registration

**Given** the route response `label` field
**When** `api/routes.py` builds the response
**Then** the `label` value is populated from the Google Maps Directions API `summary` field on each route object (e.g., `"Via Hwy 50"`)

**Given** `pytest tests/test_routes.py` is run
**Then** all tests pass; `pricing.fetch_stations` and `requests.get` (for Google Maps) are both mocked; tests cover: success case (3 routes, correct schema), Google Maps 502, Régie Essence 502, missing required field 400

---

## Epic 3: Trip Planning SPA

Olivier can open `http://localhost:5000`, enter a trip (origin, destination, range, optional waypoint), and see three colour-coded route cards with fuel recommendations, savings, and a fully synced interactive map. Settings persist across sessions. Low-range urgency, empty states, and API errors are all handled gracefully. The product is complete and usable end-to-end.

### Story 3.1: SPA Shell & Design Foundation

As Olivier,
I want Flask to serve a structured HTML page with the full visual design system applied — tokens, typography, split-pane layout, and Google Maps initialised,
So that every subsequent frontend story has a complete, consistent visual foundation to build on.

**Acceptance Criteria:**

**Given** the Flask app is running
**When** I navigate to `http://localhost:5000`
**Then** Flask renders `static/index.html` as a Jinja2 template (via `render_template`), injecting `GOOGLE_MAPS_API_KEY` into the Google Maps JavaScript API CDN `<script>` tag `&key=` parameter
**And** the Google Maps JS API is loaded with `loading=async` and `callback=initMap`
**And** `window.initMap` is defined in `static/js/map.js` as `export function initMap() { ... }; window.initMap = initMap;` — never inline in `index.html`

**Given** the rendered page in a browser
**When** I inspect the stylesheet
**Then** all 12 design token CSS custom properties are defined on `:root`: `--bg: #F9FAFB`, `--surface: #FFFFFF`, `--border: #E5E7EB`, `--text-primary: #111827`, `--text-secondary: #6B7280`, `--accent: #16A34A`, `--accent-light: #DCFCE7`, `--route-1: #2563EB`, `--route-2: #9333EA`, `--route-3: #EA580C`, `--warning: #F59E0B`, `--error: #DC2626`
**And** Inter is loaded from Google Fonts
**And** Tailwind CSS is loaded via CDN

**Given** a desktop viewport (≥1024px)
**When** I view the page layout
**Then** it shows: a header bar (56px height, placeholder form area + placeholder gear icon), a main split-pane below (cards panel `w-96` fixed left, map container `flex-1` right, both filling remaining viewport height), and a footer row for the data timestamp
**And** the map container is visible and the Google Maps canvas renders (even if empty)

**Given** a viewport < 768px
**When** I view the page
**Then** the layout stacks vertically: header → cards panel (full width) → map (fixed `h-[300px]`) → footer

### Story 3.2: Trip Form & Settings Persistence

As Olivier,
I want to fill in my trip details and settings with them remembered between sessions,
So that repeat trips require zero re-entry and I can adjust corridor or fuel preferences without losing my trip context.

**Acceptance Criteria:**

**Given** the app is open
**When** I view the header
**Then** it contains: Origin text input, Destination text input, Range number input (km), a ghost "+ Add waypoint" button below the destination field, a "Find routes" primary button (`bg-gray-900 text-white rounded-lg`), and a gear icon button (`p-2 rounded-lg hover:bg-gray-100`)

**Given** I click "+ Add waypoint"
**When** the field appears
**Then** a labeled "Waypoint" text input appears inline below the destination field with an inline "×" remove button
**And** the "+ Add waypoint" button is hidden (max 1 waypoint in MVP)

**Given** a waypoint field is visible
**When** I click "×"
**Then** the waypoint field is removed and the "+ Add waypoint" button reappears

**Given** I click the gear icon
**When** the settings drawer opens
**Then** a `w-72` panel slides in from the right with 200ms `ease` `translateX` transition
**And** an overlay (`bg-black/20`) covers only the map area (not the cards panel)
**And** the drawer contains: Fuel type button-group toggle (Regular / Premium / Diesel), Tank size `<input type="number">` (min 1, max 200), Corridor radius `<input type="range">` (1–10 km) with live value label, Safety buffer `<input type="range">` (5–50 km) with live value label, Max alternatives button-group toggle (2 / 3), and a "Reset to defaults" ghost text link

**Given** I change any setting value
**When** the change event fires
**Then** the new value is immediately written to `localStorage` under key `gaz_eye_settings` — no Save button required
**And** `DEFAULT_SETTINGS` and `SETTINGS_KEY = "gaz_eye_settings"` are defined only in `state.js` and never duplicated elsewhere

**Given** I click "Reset to defaults"
**When** the link is clicked
**Then** all settings revert to: `fuel_type: "Régulier"`, `tank_litres: 60`, `corridor_km: 2.0`, `safety_buffer_km: 15`, `max_alternatives: 3`
**And** `localStorage` is updated immediately

**Given** I close and reopen the browser
**When** the page loads
**Then** all form fields (origin, destination, range, waypoint if set) and all drawer settings are pre-populated from the last saved `localStorage` values

**Given** I click outside the drawer overlay or click "×" in the drawer header
**When** the drawer closes
**Then** it slides out with 200ms ease and the overlay disappears

**Given** the drawer animation implementation
**When** the code is inspected
**Then** the open/close animation is implemented using vanilla JS (`element.classList.add/remove` or `element.style.transform`) — Alpine.js must NOT be introduced; it conflicts with the Architecture constraint of no JS frameworks

### Story 3.3: Route Cards & Trip Submission

As Olivier,
I want to click "Find routes" and immediately see three route cards with fuel recommendations, savings, and drive time,
So that I can identify the best fuel option for my trip at a glance.

**Acceptance Criteria:**

**Given** I have filled in origin, destination, and range, then click "Find routes"
**When** the `POST /api/plan` request is in flight
**Then** the submit button is disabled and its label is replaced with a spinner icon
**And** three skeleton cards appear in the cards panel (animated pulse, same height as loaded cards — no layout shift on results render)
**And** a semi-transparent overlay with a centered spinner SVG appears over the map container

**Given** the API returns results successfully
**When** the three route cards render
**Then** each card shows: route label (e.g., "Via Hwy 50"), drive time formatted as `2 h 14 min`, best station name + price formatted as `154.9 ¢/L`, savings formatted as `Save 8.2 ¢/L`
**And** each card has a 4px left border strip in its route colour (`--route-1`, `--route-2`, `--route-3`)
**And** if `tank_litres > 0` in settings, a secondary line shows `≈ Save $5.46` in `text-xs` muted colour

**Given** the route with the best value (highest `savings_per_litre`)
**When** cards render
**Then** that card has: `--accent-light` background tint, `--accent` 2px border, and a "Best value" badge in the card's top-right corner
**And** no other card has green styling

**Given** `state.js` is loaded as an ES module
**When** `state.setSelectedRoute(index)` is called
**Then** it sets `state.selectedRouteIndex = index` and dispatches `new CustomEvent("routeSelected", { detail: { index } })` on `document`
**And** the calling card gets a 2px route-colour border + `ring-1`, all other cards reduce to `opacity-50`

**Given** a route object in the API response where `best_station` is `null`
**When** the card for that route renders
**Then** the card renders in the gray no-stations state as fully specified in Story 3.5 — never assume `best_station` is always present

**Given** no trip has been submitted yet
**When** the cards panel renders
**Then** it shows a single muted line: "Enter a trip above to see route options." — no skeleton cards, no empty placeholders

### Story 3.4: Google Maps Integration & Bidirectional Sync

As Olivier,
I want all three routes drawn on the map with colour-coded polylines and recommended station markers, staying in sync with whichever card or route I select,
So that I can compare routes visually and make my selection from either the map or the cards.

**Acceptance Criteria:**

**Given** trip results are loaded
**When** the map renders
**Then** three route polylines are drawn simultaneously in their route colours (Route A `--route-1` blue, Route B `--route-2` purple, Route C `--route-3` orange) at 4px stroke weight

**Given** trip results are loaded
**When** station markers render
**Then** each recommended station has a custom `AdvancedMarkerElement` — circular pin in its route colour with a white fuel-pump SVG icon at 14px diameter
**And** only the recommended (best) station per route is shown by default — other reachable stations are not shown as pins

**Given** I hover over a station marker
**When** the tooltip appears
**Then** it shows the station name and price formatted as `154.9 ¢/L`

**Given** I click a route card
**When** `state.setSelectedRoute(index)` fires
**Then** that route's polyline becomes 6px weight; other polylines dim to 40% opacity
**And** that route's station marker enlarges to 20px diameter with a white border ring
**And** the `routeSelected` CustomEvent triggers the visual update in `map.js` via a `document.addEventListener("routeSelected", ...)` listener

**Given** I click a route polyline on the map
**When** the click is handled in `map.js`
**Then** `state.setSelectedRoute(index)` is called with the matching route index
**And** the corresponding card updates its visual state identically to having been clicked directly

**Given** `map.js` is inspected
**When** the file is read
**Then** `window.initMap` is assigned as `window.initMap = initMap` within `map.js` — never defined inline in `index.html`

### Story 3.5: Edge States, Error Handling & Responsive Layout

As Olivier,
I want the app to handle low-range trips, unreachable-station routes, API failures, and mobile viewports gracefully,
So that I can rely on it in all scenarios — including a roadside low-fuel stop on a phone.

**Acceptance Criteria:**

**Given** I enter a range value ≤ 50 km
**When** the value is typed or changed
**Then** the range input gains an amber border (`border-amber-400`) as a low-range indicator

**Given** the API returns a route where `stations` is an empty array
**When** that route's card renders
**Then** the card shows in a gray non-interactive state with message: "Nearest station is X km — Y km beyond your range" (using the nearest filtered station's distance and the shortfall)
**And** an inline amber banner appears above the cards: "N station(s) reachable · Z km buffer active" (positive framing)

**Given** all three routes have zero reachable stations
**When** cards render
**Then** all three cards are in the gray no-stations state
**And** the amber banner includes the additional suggestion: "Try increasing your range or widening the corridor in settings"

**Given** `POST /api/plan` returns HTTP 502
**When** the error response arrives
**Then** an inline banner appears inside the cards panel with `bg-red-50 border-red-200 text-red-700` styling
**And** the message reads "Could not load Google Maps routes. Try again." (for `error: "google_maps"`) or "Could not load Régie Essence pricing. Try again." (for `error: "regie_essence"`)
**And** the banner persists until the user submits a new trip — no auto-dismiss, no toast

**Given** Google Maps returns fewer than 3 route alternatives
**When** cards render
**Then** only 1 or 2 cards appear — no empty placeholder cards are shown for the missing routes

**Given** the `data_timestamp` from the API response is more than 24 hours ago
**When** the footer timestamp renders
**Then** the timestamp text colour changes to `--warning` (amber) — no blocking UI, no banner

**Given** a viewport < 768px
**When** I view the app
**Then** the layout stacks vertically: form fields in a single column → cards panel (full width, `p-5` card padding) → map (`h-[300px]` fixed) → footer timestamp
**And** the settings drawer renders as a full-width panel sliding up from the bottom instead of from the right
**And** all interactive elements meet 44×44px minimum touch target: cards, "Find routes" button, gear icon (`p-3`), "+ Add waypoint" and "×" (`min-h-[44px]`)
