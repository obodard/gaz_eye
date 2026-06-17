---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
  - epic-4-price-quality-filtering-2026-05-01
  - epic-4-expensive-station-visibility-2026-05-09
  - epic-5-conversational-assistant-2026-05-31
status: complete
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
lastModified: '2026-05-31'
changeLog:
  - date: '2026-05-01'
    changes: 'Added Epic 4: Price Quality Filtering — FR38–FR42 + NFR11, Stories 4.1–4.2 (detect_stale_prices engine, exemptions/kill-switch/route integration)'
  - date: '2026-05-09'
    changes: 'Extended Epic 4: FR43–FR47 + Stories 4.3–4.4 — bidirectional anomaly detection (expensive direction), worst_station in /api/plan response, red map marker for most expensive station'
  - date: '2026-05-31'
    changes: 'Added Epic 5: Conversational Assistant — FR48–FR66 + NFR12–NFR14, Stories 5.1–5.5 (ADK agent definition, /api/chat proxy endpoint, route context injection, chat box component, chat state management & action dispatch)'
  - date: '2026-05-31'
    changes: 'PM alignment check after UX review: added FR67 (filter badge with click-to-clear on map) to close gap between UX-DR21 and FR60 chat-only clearing path; updated Epic 5 FRs covered and FR Coverage Map'
---

# chekov - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for chekov, decomposing the requirements from the PRD, UX Design, and Architecture into implementable stories.

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

### Price Quality Filtering

FR38: System can detect stations priced more than a configurable threshold (default: 5¢/L) below their local geographic median price and exclude them from recommendations by setting their price to the unavailable sentinel (`float('inf')`)
FR39: System can compute a local median price for each station using a density-adaptive neighbor radius: starting at 5 km and expanding to 10 km, 20 km, then 50 km until a minimum of 5 neighbors are found; stations with fewer than 5 neighbors within 50 km bypass the filter
FR40: System can exempt stations matching configurable name substrings (case-insensitive, defined in `stations.yaml`) from anomaly detection, treating them as full recommendation candidates regardless of their price relative to neighbors
FR41: System can disable the anomaly filter entirely via a boolean flag (`anomaly_filter_enabled`) in `stations.yaml` without a code deploy
FR42: System can emit a structured log entry for each excluded station containing: station name, station price, local median, neighbor count, radius used, and Régie Essence data timestamp
FR43: System can detect stations priced more than a configurable threshold above their local geographic median and exclude them from the most-expensive selection by setting their price to the unavailable sentinel (`float('inf')`)
FR44: Anomaly detection is bidirectional — stations priced anomalously below OR above the local geographic median are both excluded from recommendations using the same threshold constant and exemption list
FR45: System can include the most expensive non-anomalous reachable station (`worst_station`) per route in the `/api/plan` response, using the post-filter station list so stale high prices do not inflate savings calculations
FR46: System can display the most expensive reachable station per route on the map as a distinct red circular marker alongside the cheapest station marker, using a warning-colour pin to differentiate it from the route-colour cheapest pin
FR47: User can hover a most-expensive station marker to see the station name and price; the marker enlarges when its route is selected, matching the selection behaviour of the cheapest station marker

### Conversational Assistant

FR48: System displays a persistent chat panel alongside the map and route cards, accessible at all times regardless of trip state
FR49: User can type natural-language messages into the chat panel to initiate trips, modify routes, or filter the map display
FR50: System displays assistant responses in the chat panel with confirmation of the action taken (e.g., "Added Grenville as a waypoint — refreshing routes.")
FR51: When the user describes a trip via chat (e.g., "Montréal to Duhamel, 180 km range"), the ADK agent extracts origin, destination, and optional range/waypoints into structured parameters
FR52: After extraction, the frontend auto-fills the trip form fields with the extracted values and automatically submits the plan request — no manual click required
FR53: If the agent cannot extract a required field (origin or destination), it responds in the chat asking the user to clarify, rather than submitting an incomplete request
FR54: When the user requests adding a waypoint via chat (e.g., "add a route through Grenville"), the ADK agent extracts the waypoint location and returns an `add_waypoint` action
FR55: The frontend appends the extracted waypoint to the current trip parameters, preserving existing origin, destination, and range, and re-submits the plan request
FR56: Waypoint addition via chat works identically whether the original trip was submitted via the form or via chat
FR57: When the user requests a geographic price filter via chat (e.g., "show only the prices in Tremblant"), the ADK agent extracts the area name and returns a `filter_stations_by_area` action with the area name and approximate coordinates
FR58: The frontend filters map station markers to display only stations within a reasonable radius of the specified area — all other markers are hidden
FR59: Geographic map filters apply to station markers only; route polylines, route cards, and savings recommendations remain unchanged
FR60: User can clear a geographic filter via chat (e.g., "show all stations") to restore the full marker display
FR61: A dedicated Google ADK agent handles all chat interactions, running as a separate service with its own process
FR62: The Flask backend exposes a `/api/chat` endpoint that proxies user messages to the ADK agent service and relays structured responses to the frontend
FR63: The ADK agent uses the Gemini API for natural language understanding, intent classification, and parameter extraction
FR64: The ADK agent defines structured tools (`submit_trip`, `add_waypoint`, `filter_stations_by_area`, `clear_filter`) that map to chekov UI actions
FR65: The ADK agent returns JSON responses containing `action` (the tool/intent name), `params` (extracted values), and `message` (a human-readable confirmation to display in the chat)
FR66: The ADK agent maintains conversation context within a session so follow-up messages (e.g., "now add Grenville") resolve against the current trip state without requiring the user to repeat origin/destination
FR67: When a geographic station filter is active, a filter badge appears on the map container displaying the filtered area name and a clickable "Show all" link; clicking the link clears the filter and restores all station markers without requiring chat interaction

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
NFR11: Anomaly filter processing (spatial median computation over the full Quebec station dataset, ~3,000 stations) completes within 100ms wall-clock time
NFR12: Chat round-trip (user message → Flask proxy → ADK agent → Gemini API → structured response → UI action) completes within 5 seconds under normal network conditions
NFR13: The ADK agent service is started alongside the Flask backend via the existing `run.sh` entry point (single launch command)
NFR14: Gemini API key is stored server-side only — consumed by the ADK agent process, never exposed to the frontend or included in client-side source

### Additional Requirements

- Brownfield restructuring: Extract `chekov.py` into `api/pricing.py` as an importable module preserving `parse_price_value`, `fetch_stations`, and GeoJSON dual-parse logic verbatim — this is a prerequisite for all other backend work
- Polyline decoding: Use the `polyline` PyPI package (add to `requirements.txt`) instead of implementing the Google Encoded Polyline Algorithm from scratch
- Google Maps JS API key injection: `GOOGLE_MAPS_API_KEY` (single env var) must be injected into `index.html` at serve time via Jinja2 template rendering — not hardcoded in the static file
- API key isolation: `GOOGLE_MAPS_API_KEY` loaded from `.env` via `python-dotenv`; never included in any JSON response or frontend-accessible route (Jinja2 injection into the script src tag is the only frontend exposure)
- `distance_along_route()` semantics: Distance from origin to station is the cumulative distance along the route polyline to the nearest polyline point — not a straight-line distance; must be documented clearly in the implementation story
- Flask Blueprint pattern: All routes registered in `api/routes.py` via a Blueprint; `app.py` is a pure factory with zero routes
- Settings defaults: `DEFAULT_SETTINGS` and `SETTINGS_KEY = "chekov_settings"` defined once in `state.js` only — never duplicated elsewhere
- `run.sh` launch script: Sets `FLASK_APP=app.py`, `FLASK_ENV=development`, loads `.env`, runs `flask run`; must warn if `GOOGLE_MAPS_API_KEY` is unset — single key used for both backend Directions API and frontend JS API injection
- Tests: `tests/` directory at project root with `pytest`; `test_pricing.py`, `test_geo.py`, `test_routes.py`; mock `requests.get` for all network calls
- `.gitignore` requirements: `.env`, `__pycache__/`, `*.pyc`
- ADK agent package: `agent/` directory at project root with `agent/__init__.py` (exports `root_agent`) and `agent/agent.py` (defines `root_agent`, `SYSTEM_INSTRUCTION`, 4 tool functions returning `{"ok": True}`)
- ADK separate service: `adk api_server agent --port 5001` launched in `run.sh` alongside Flask; ADK process PID stored, killed via `trap EXIT` on Ctrl-C
- Gemini API key isolation: `GEMINI_API_KEY` in `.env` (gitignored), consumed exclusively by the ADK agent process — Flask never reads, forwards, or logs it; `.env.example` updated with `GEMINI_API_KEY=`
- Chat proxy: `POST /api/chat` in `api/routes.py` proxies to `http://localhost:5001/run` via `requests.post(timeout=10)`; normalizes ADK events list to `{action, params, message}` schema
- Context injection protocol: `app.js` fires a silent `POST /api/chat` with `is_context_update: true` after each successful `/api/plan` response; `api/routes.py` detects this flag, proxies to ADK, and returns HTTP 204 — no body, no frontend UI update
- Session ID management: `state.js` generates `sessionId = crypto.randomUUID()` in memory on page load — in-memory only, never persisted in `localStorage`
- `chat.js` new module: owns chat panel input handling, message thread rendering, action dispatch (`submit_trip`, `add_waypoint`, `filter_stations_by_area`, `clear_filter`, `chat_only`)
- `map.js` extensions: `filterMarkers(area_name, lat, lng)` hides out-of-radius station markers; `restoreMarkers()` restores all hidden markers — both exported functions
- `requirements.txt` addition: `google-adk>=1.0`

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
UX-DR16: Implement settings and last trip persistence via localStorage key `chekov_settings`; on page load, pre-populate all form fields (including origin/destination) from last saved values
UX-DR17: Chat panel renders as a collapsible bottom section of the left column; default state is collapsed showing only the input bar (~48px height); expanded state overlays the cards panel up to 60% of available height; a small chevron handle above the input toggles collapse/expand; the panel is visible at all times regardless of trip state
UX-DR18: Chat user bubbles use `--text-primary` (#111827) background with white text and `border-radius: 12px 12px 0 12px`; assistant bubbles use `--surface` white background with `--border` border and `border-radius: 12px 12px 12px 0`; never use route colours for chat bubbles to avoid false visual association with route cards
UX-DR19: When chat dispatches an action-bearing response (`submit_trip`, `add_waypoint`), a brief confirmation toast appears at the bottom of the cards panel in `text-sm` `--text-secondary` style; the toast auto-dismisses after 4 seconds; `chat_only`, `filter_stations_by_area`, and `clear_filter` actions do not trigger a toast
UX-DR20: When chat auto-fills form fields via `submit_trip` or `add_waypoint` dispatch, the affected input fields flash with `--accent-light` (#DCFCE7) background (200ms ease-in, 800ms hold, 200ms ease-out) before the loading state activates, providing a visual bridge between chat input and form action
UX-DR21: When `filterMarkers()` is active, a dismissable filter badge appears top-left on the map container: "📍 [Area name] · Show all" with a clickable "Show all" link that calls `restoreMarkers()`; badge uses `--surface` background with `--border` border, `text-sm`, `border-radius: 8px`, semi-transparent backdrop; badge disappears when filter is cleared
UX-DR22: Below 768px, `#chat-panel` renders as a fixed-position bottom bar (`position: fixed; bottom: 0; width: 100%`) with the input field always visible; expanded state slides up covering the map area (not the cards); cards remain visible and scrollable above the chat panel

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
FR38: Epic 4 — detect_stale_prices(): threshold comparison + sentinel assignment
FR39: Epic 4 — detect_stale_prices(): density-adaptive neighbor radius (5→10→20→50 km)
FR40: Epic 4 — stations.yaml exemption list + detect_stale_prices() exemption bypass
FR41: Epic 4 — stations.yaml anomaly_filter_enabled kill switch + routes.py bypass guard
FR42: Epic 4 — structured log entry per excluded station (name, price, median, neighbors, radius, timestamp)
FR43: Epic 4 — detect_stale_prices() expensive-direction threshold: `station_price - local_median > threshold` → sentinel
FR44: Epic 4 — bidirectional anomaly detection using same threshold and exemption list for both cheap and expensive outliers
FR45: Epic 4 — `/api/plan` response includes `worst_station` object (post-anomaly-filter most expensive station) per route
FR46: Epic 4 — most expensive station rendered on map as red `AdvancedMarkerElement` circular pin alongside cheapest pin
FR47: Epic 4 — worst station marker hover tooltip + enlarge-on-route-select behaviour
FR48: Epic 5 — persistent `#chat-panel` in `index.html` accessible at all times regardless of trip state
FR49: Epic 5 — `chat.js` input field + send button for natural-language message entry
FR50: Epic 5 — `chat.js` renders assistant `message` confirmation in thread after action fires
FR51: Epic 5 — `agent/agent.py` `submit_trip` tool: extracts origin, destination, range_km, waypoints[]
FR52: Epic 5 — `chat.js` `submit_trip` dispatch: auto-fills form fields + programmatically submits `/api/plan`
FR53: Epic 5 — `SYSTEM_INSTRUCTION` clarifying-question rule prevents `submit_trip` call with missing origin/destination
FR54: Epic 5 — `agent/agent.py` `add_waypoint` tool: extracts waypoint location string
FR55: Epic 5 — `chat.js` `add_waypoint` dispatch: appends waypoint to form + re-submits `/api/plan`
FR56: Epic 5 — `add_waypoint` dispatch preserves existing form state (origin, destination, range) from either form or chat submission
FR57: Epic 5 — `agent/agent.py` `filter_stations_by_area` tool: extracts area_name, lat, lng
FR58: Epic 5 — `map.js` `filterMarkers(area_name, lat, lng)` hides station markers outside radius
FR59: Epic 5 — `filterMarkers()` leaves polylines, route cards, and savings calculations untouched
FR60: Epic 5 — `map.js` `restoreMarkers()` makes all previously hidden markers visible again
FR61: Epic 5 — `agent/` package: Google ADK agent running as separate service on `localhost:5001`
FR62: Epic 5 — `api/routes.py` `POST /api/chat`: Flask proxy to ADK service with 10s timeout + HTTP 502 on failure
FR63: Epic 5 — `agent/agent.py` `model="gemini-2.0-flash"` handles NL understanding and extraction
FR64: Epic 5 — `agent/agent.py` registers 4 structured tools on `root_agent`
FR65: Epic 5 — `api/routes.py` normalizes ADK events list to `{action, params, message}` JSON response
FR66: Epic 5 — `state.js` `sessionId` (UUID, in-memory) carried in every `POST /api/chat` request for session continuity
FR67: Epic 5 — `map.js` filter badge on map container when `filterMarkers()` active; clickable "Show all" link calls `restoreMarkers()`

## Epic List

### Epic 1: Project Foundation & Pricing Engine

The Flask application scaffold and the complete Quebec gas station pricing pipeline are operational. `chekov.py` is migrated into an importable `api/pricing.py` module, the Régie Essence GeoJSON can be fetched, parsed (dual-format), filtered by fuel type, and autonomy-filtered against a known driving range. The recommendation engine (cheapest/worst station, savings ¢/L, savings $/tank, route ranking) is fully implemented and unit-tested. The backend structure is in place for all subsequent epics.

**FRs covered:** FR11, FR13, FR14, FR15, FR16, FR17, FR18, FR19, FR20, FR21, FR22, FR23
**NFRs addressed:** NFR5 (API key server-side only), NFR6 (no data persistence beyond local), NFR8 (dual-parse gzip/JSON), NFR9 (User-Agent header)
**Architecture/UX requirements:** Brownfield extraction of chekov.py → api/pricing.py, Flask Blueprint scaffold, app.py pure factory, run.sh, .env + python-dotenv (single GOOGLE_MAPS_API_KEY), requirements.txt, tests/test_pricing.py

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

### Epic 4: Price Quality Filtering & Expensive Station Visibility

Every recommendation Olivier receives is backed by a spatially-validated price. Before any recommendation is built, `detect_stale_prices()` computes a density-adaptive geographic median for each station and silently excludes any station priced anomalously below **or above** its local neighborhood — preventing stale cheap prices from overstating savings, and stale high prices from inflating the cost differential. Known structural discounters (Costco, Olco) are explicitly exempted. The filter can be disabled instantly from `stations.yaml` without touching code.

Beyond backend quality, the map is extended to show the most expensive non-anomalous reachable station per route as a distinct red marker alongside the cheapest pin — giving Olivier immediate visual context for the savings spread without cluttering the map.

**FRs covered:** FR38, FR39, FR40, FR41, FR42, FR43, FR44, FR45, FR46, FR47
**NFRs addressed:** NFR11 (anomaly filter < 100ms on full dataset)
**Architecture requirements:** `detect_stale_prices()` extended with bidirectional threshold in `api/pricing.py`; `/api/plan` response extended with `worst_station` per route; `map.js` extended with red `AdvancedMarkerElement` for worst station; `ANOMALY_THRESHOLD_CAD = 0.05` covers both directions; `tests/test_pricing.py` and `tests/test_routes.py` extended

---

### Epic 5: Conversational Assistant

Olivier can type natural-language messages in a persistent chat panel to plan trips, add waypoints, and filter the map — without ever touching the form. A Google ADK agent backed by Gemini 2.0 Flash runs as a separate service (`localhost:5001`), classifies intent, extracts structured parameters, and returns a normalized `{action, params, message}` response. Flask proxies the exchange through `POST /api/chat`. Trip context is silently injected into the ADK session after each successful route plan so follow-up messages resolve correctly. If the ADK service is unavailable, the form-based workflow is unaffected.

**FRs covered:** FR48, FR49, FR50, FR51, FR52, FR53, FR54, FR55, FR56, FR57, FR58, FR59, FR60, FR61, FR62, FR63, FR64, FR65, FR66, FR67
**NFRs addressed:** NFR12 (5s chat round-trip), NFR13 (single `run.sh` launch), NFR14 (Gemini API key server-side only)
**UX-DRs addressed:** UX-DR17 (collapsible chat panel in left column), UX-DR18 (chat bubble styling — neutral colours, no route-colour interference), UX-DR19 (action confirmation toast), UX-DR20 (form field flash on chat auto-fill), UX-DR21 (active filter badge on map), UX-DR22 (mobile fixed-bottom chat bar)
**Architecture requirements:** `agent/` package (`agent.py` with `root_agent` + 4 tools + `SYSTEM_INSTRUCTION`, `__init__.py`); `api/routes.py` `POST /api/chat` proxy (10s timeout, HTTP 204 for context updates, HTTP 502 on ADK failure); `run.sh` updated (ADK on port 5001 + `trap EXIT`); `state.js` extended with `sessionId` (UUID, in-memory); `static/js/chat.js` new module (input, render, action dispatch); `map.js` extended with `filterMarkers()` + `restoreMarkers()`; `requirements.txt` + `google-adk>=1.0`; `.env.example` + `GEMINI_API_KEY=`

---

## Epic 1: Project Foundation & Pricing Engine

The Flask application scaffold and the complete Quebec gas station pricing pipeline are operational. `chekov.py` is migrated into an importable `api/pricing.py` module, the Régie Essence GeoJSON can be fetched, parsed (dual-format), filtered by fuel type, and autonomy-filtered against a known driving range. The recommendation engine (cheapest/worst station, savings ¢/L, savings $/tank, route ranking) is fully implemented and unit-tested. The backend structure is in place for all subsequent epics.

### Story 1.1: Flask Project Scaffold

As a developer,
I want a runnable Flask application skeleton with the correct project structure, launch script, and environment configuration,
So that I have a working foundation to build all subsequent backend and frontend features on.

**Acceptance Criteria:**

**Given** the repository is cloned and `.env` contains `GOOGLE_MAPS_API_KEY=<any value>`
**When** I run `./run.sh`
**Then** Flask starts at `http://localhost:5000` with debug/hot-reload enabled
**And** `GET /` returns HTTP 200 with placeholder HTML containing "chekov"
**And** a startup warning is printed to stdout if `GOOGLE_MAPS_API_KEY` is unset in the environment

**Given** the project structure after this story
**When** I inspect the repository
**Then** the following files exist: `app.py` (pure factory, zero `@app.route` decorators), `api/__init__.py`, `api/routes.py` (Blueprint registered in `app.py`, skeleton with no functional routes yet), `run.sh` (executable, sets `FLASK_APP=app.py` and `FLASK_ENV=development`, sources `.env`), `.env.example` (key names with empty values), `.gitignore` (includes `.env`, `__pycache__/`, `*.pyc`), and `requirements.txt` updated to include `flask==3.1.3` and `python-dotenv`
**And** `chekov.py` and `stations.yaml` are preserved entirely unchanged

### Story 1.2: Pricing Module — GeoJSON Fetch & Price Parsing

As a developer,
I want the Régie Essence GeoJSON fetch and price parsing logic extracted from `chekov.py` into an importable `api/pricing.py` module,
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

**Given** `chekov.py` exists after the extraction
**When** it is run directly (`python chekov.py`)
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
**Then** the new value is immediately written to `localStorage` under key `chekov_settings` — no Save button required
**And** `DEFAULT_SETTINGS` and `SETTINGS_KEY = "chekov_settings"` are defined only in `state.js` and never duplicated elsewhere

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

---

## Epic 4: Price Quality Filtering & Expensive Station Visibility

Every recommendation Olivier receives is backed by a spatially-validated price. Before any recommendation is built, `detect_stale_prices()` computes a density-adaptive geographic median for each station and silently excludes any station priced anomalously below **or above** its local neighborhood — preventing stale cheap prices from overstating savings, and stale high prices from inflating the cost differential. Known structural discounters (Costco, Olco) are explicitly exempted. The filter can be disabled instantly from `stations.yaml` without touching code.

Beyond backend quality, the map is extended to show the most expensive non-anomalous reachable station per route as a distinct red marker alongside the cheapest pin — giving Olivier immediate visual context for the savings spread without cluttering the map.

### Story 4.1: Stale Price Detection Engine

As a developer,
I want a pure `detect_stale_prices()` function in `api/pricing.py` that uses a density-adaptive spatial median to identify and exclude stale-priced stations,
So that the recommendation pipeline silently filters out Régie listings that are anomalously cheap relative to their geographic neighbors before any recommendation is built.

**Acceptance Criteria:**

**Given** `api/pricing.py` is imported
**When** the module is inspected
**Then** the constant `ANOMALY_THRESHOLD_CAD = 0.05` is defined at module level — not hardcoded inside any function and not duplicated elsewhere

**Given** a list of all Quebec stations (`all_stations`) each with `lat`, `lng`, and `price_per_litre` fields, a candidate station, a `threshold` value (default `ANOMALY_THRESHOLD_CAD`), and an empty exemption list
**When** `detect_stale_prices(corridor_stations, all_stations, threshold, exemptions)` is called
**Then** it returns a copy of `corridor_stations` where any station priced more than `threshold` below its local geographic median has its `price_per_litre` set to `float('inf')`
**And** the original station dicts in `all_stations` are not mutated

**Given** a candidate station and the `all_stations` dataset
**When** the density-adaptive radius logic runs inside `detect_stale_prices()`
**Then** it searches for neighbors at 5 km, then 10 km, then 20 km, then 50 km — stopping at the first radius that yields ≥5 neighbors (excluding the candidate itself)
**And** if fewer than 5 neighbors are found within 50 km, the station bypasses the filter entirely (its price is left unchanged)

**Given** a station where the local median price is 155.0¢/L and the station's price is 149.5¢/L (5.5¢/L below median, exceeding the 5¢/L default threshold)
**When** `detect_stale_prices()` processes this station
**Then** that station's `price_per_litre` is set to `float('inf')` in the returned list

**Given** a station where the local median price is 155.0¢/L and the station's price is 150.5¢/L (4.5¢/L below median, under the default threshold)
**When** `detect_stale_prices()` processes this station
**Then** that station's `price_per_litre` is unchanged

**Given** a station already having `price_per_litre == float('inf')` (price unavailable)
**When** `detect_stale_prices()` processes it
**Then** it is left unchanged — stations with no price data bypass the anomaly filter

**Given** `tests/test_pricing.py` contains tests for `detect_stale_prices()`
**When** `pytest tests/test_pricing.py` is run
**Then** all tests pass; tests cover:
- Station excluded at the default 5¢/L threshold (5 km neighbor radius)
- Station kept because it is only 4¢/L below median
- Station bypassed because fewer than 5 neighbors within 50 km
- Station bypassed because `price_per_litre == float('inf')`
- Density expansion: station has 3 neighbors at 5 km but ≥5 at 10 km — 10 km radius is used
- Empty `corridor_stations` list returns an empty list without error
- `all_stations` list is not mutated after the call

**Given** the full Quebec dataset (~3,000 stations) is passed as `all_stations`
**When** `detect_stale_prices()` processes it
**Then** total wall-clock time is < 100ms (satisfies NFR11); no external calls are made — all computation is in-memory using Haversine distances already available from `api/geo.py`

### Story 4.2: Exemptions, Kill Switch & Route Pipeline Integration

As a developer,
I want `stations.yaml` to carry the anomaly filter configuration, and the `/api/plan` route to invoke `detect_stale_prices()` at the correct pipeline position with full exemption and kill-switch support,
So that the filter operates transparently on every trip query, can exclude structural discounters legitimately, and can be disabled in seconds without a code deploy.

**Acceptance Criteria:**

**Given** `stations.yaml` is opened
**When** the file is inspected
**Then** it contains two new top-level keys:
- `anomaly_filter_enabled: true` (boolean, default `true`)
- `anomaly_filter_exemptions: ["costco", "olco"]` (list of lowercase name substrings)
**And** the existing `cities`, `settings` structure is completely unchanged

**Given** `detect_stale_prices()` is called with a non-empty `exemptions` list and a station whose name contains "Costco" (any case)
**When** the function runs
**Then** that station is not excluded regardless of its price relative to neighbors — exemption matching is case-insensitive substring matching

**Given** `anomaly_filter_enabled: true` in `stations.yaml` and a trip is requested via `POST /api/plan`
**When** the route handler in `api/routes.py` processes the request
**Then** `detect_stale_prices()` is called **after** `find_stations_in_corridor()` and **before** `filter_by_autonomy()` — this ordering is mandatory
**And** the `all_stations` full dataset (not just corridor stations) is passed as the second argument

**Given** `anomaly_filter_enabled: false` in `stations.yaml` and a trip is requested
**When** the route handler processes the request
**Then** `detect_stale_prices()` is NOT called — the pipeline proceeds directly from corridor matching to `filter_by_autonomy()`
**And** no code deploy is required to toggle this behaviour; editing `stations.yaml` is sufficient

**Given** `detect_stale_prices()` excludes a station (sets its price to `float('inf')`)
**When** the `chekov.pricing` logger emits the exclusion entry
**Then** the log message contains all of: station name, station `price_per_litre` (dollars), local median price (dollars), neighbor count used, radius used (km), and the Régie Essence `data_timestamp`
**And** the log is emitted at `INFO` level — it does not appear in the API response body

**Given** `api/routes.py` loads filter config from `stations.yaml`
**When** `anomaly_filter_exemptions` is missing from `stations.yaml`
**Then** the route handler defaults to an empty exemptions list and continues without error

**Given** `tests/test_routes.py` is run after this story
**When** `pytest tests/test_routes.py` is executed
**Then** all existing tests continue to pass
**And** new tests cover:
- Filter active (`anomaly_filter_enabled: true`): `detect_stale_prices()` is called with correct arguments (mocked)
- Filter disabled (`anomaly_filter_enabled: false`): `detect_stale_prices()` is NOT called
- Exemption list forwarded correctly to `detect_stale_prices()` when present in config
- Missing `anomaly_filter_exemptions` key defaults to empty list without error

### Story 4.3: Bidirectional Anomaly Detection — Expensive Station Filtering

As a developer,
I want `detect_stale_prices()` to also flag stations priced anomalously above their local geographic median as stale,
So that the `worst_station` in recommendations is always a legitimately high price and savings calculations are never inflated by stale Régie data in the expensive direction.

**Acceptance Criteria:**

**Given** a station where the local median price is 155.0¢/L and the station's price is 161.0¢/L (6.0¢/L above median, exceeding the 5¢/L default threshold)
**When** `detect_stale_prices()` processes this station
**Then** that station's `price_per_litre` is set to `float('inf')` in the returned list
**And** a structured log entry is emitted at INFO level containing: station name, station price, local median, neighbor count, radius used, and data timestamp — identical in format to cheap-direction exclusions

**Given** a station where the local median price is 155.0¢/L and the station's price is 159.4¢/L (4.4¢/L above median, under the default threshold)
**When** `detect_stale_prices()` processes this station
**Then** that station's `price_per_litre` is unchanged

**Given** a station whose name matches an entry in `anomaly_filter_exemptions` (case-insensitive substring)
**When** `detect_stale_prices()` processes it in the expensive direction
**Then** the station is not excluded regardless of how far above the local median its price is — exemptions apply bidirectionally

**Given** the same `ANOMALY_THRESHOLD_CAD = 0.05` constant
**When** `detect_stale_prices()` evaluates both directions
**Then** it uses `local_median - station_price > threshold` for the cheap direction and `station_price - local_median > threshold` for the expensive direction — same threshold, no new constant introduced

**Given** `tests/test_pricing.py` contains tests for the expensive direction
**When** `pytest tests/test_pricing.py` is run
**Then** all existing tests continue to pass
**And** new tests cover:
- Station excluded in the expensive direction (price > median + threshold)
- Station kept because it is only 4¢/L above median
- Exempted station not excluded even when priced well above median
- Station already `float('inf')` bypasses both directions
- Both cheap and expensive directions evaluated in a single `detect_stale_prices()` call

### Story 4.4: Most Expensive Station Map Marker

As Olivier,
I want to see the most expensive reachable gas station per route displayed on the map with a distinct red marker,
So that I can immediately see both the best deal and the worst deal on each route without leaving the map view.

**Acceptance Criteria:**

**Given** the `/api/plan` route handler builds each route's response
**When** the response JSON is serialised
**Then** each route object includes a `worst_station` field — a station dict (same schema as `best_station`: `name`, `address`, `price_per_litre`, `lat`, `lng`, `distance_from_route_km`, `distance_from_origin_km`) or `null` if no reachable stations exist
**And** `worst_station` is derived from the post-anomaly-filter station list so stale high prices cannot appear as the worst station

**Given** `worst_station` equals `best_station` (only one reachable station)
**When** the map renders
**Then** only one marker is drawn for that station — not two overlapping markers

**Given** `worst_station` is `null`
**When** the map renders
**Then** no worst-station marker is drawn for that route — no error is raised

**Given** trip results are loaded and `worst_station` is non-null and distinct from `best_station`
**When** the map renders for a route
**Then** a second `AdvancedMarkerElement` is drawn at the worst station's coordinates using the CSS custom property `--error` (`#DC2626`, red) as the pin background colour
**And** the pin uses the same white fuel-pump SVG icon as the best-station marker at 14px diameter
**And** the best-station pin retains its route colour (unchanged from Story 3.4)

**Given** I hover over a worst-station marker
**When** the InfoWindow tooltip appears
**Then** it shows the station name and price formatted as `154.9 ¢/L`, identical in format to the best-station tooltip

**Given** I click a route card or polyline and `state.setSelectedRoute(index)` fires
**When** the `routeSelected` event is handled in `map.js`
**Then** the selected route's worst-station marker enlarges to 20px diameter with a white border ring — same selection behaviour as the best-station marker
**And** worst-station markers for non-selected routes remain at 14px

**Given** `tests/test_routes.py` is run after this story
**When** `pytest tests/test_routes.py` is executed
**Then** all existing tests continue to pass
**And** a new test verifies that the success-case route response schema includes a `worst_station` field (non-null when reachable stations exist)
**And** a new test verifies that `worst_station` is `null` when `build_recommendation()` returns `worst_station: null`

---

## Epic 5: Conversational Assistant

Olivier can type natural-language messages in a persistent chat panel to plan trips, add waypoints, and filter the map — without ever touching the form. A Google ADK agent backed by Gemini 2.0 Flash runs as a separate service (`localhost:5001`), classifies intent, extracts structured parameters, and returns a normalized `{action, params, message}` response. Flask proxies the exchange through `POST /api/chat`. Trip context is silently injected into the ADK session after each successful route plan so follow-up messages resolve correctly. If the ADK service is unavailable, the form-based workflow is unaffected.

### Story 5.1: ADK Agent Definition & Gemini Client

As a developer,
I want the Google ADK agent package defined with the four chekov tools and the Gemini 2.0 Flash model configured,
So that the ADK service process can be started and will correctly classify intent and extract structured parameters from natural-language trip messages.

**Acceptance Criteria:**

**Given** the repository after this story
**When** I inspect the project structure
**Then** `agent/__init__.py` exists and exports `root_agent` (the ADK `Agent` instance)
**And** `agent/agent.py` exists and defines: `SYSTEM_INSTRUCTION` (string constant), four tool functions (`submit_trip`, `add_waypoint`, `filter_stations_by_area`, `clear_filter`), and `root_agent = Agent(name="chekov_assistant", model="gemini-2.0-flash", instruction=SYSTEM_INSTRUCTION, tools=[...])`
**And** `requirements.txt` includes `google-adk>=1.0`

**Given** `agent/agent.py` is inspected
**When** the four tool functions are read
**Then** `submit_trip(origin, destination, range_km=None, waypoints=None)` accepts the four trip parameters and returns `{"ok": True}`
**And** `add_waypoint(waypoint)` accepts one waypoint string and returns `{"ok": True}`
**And** `filter_stations_by_area(area_name, lat, lng)` accepts area name and coordinates and returns `{"ok": True}`
**And** `clear_filter()` accepts no arguments and returns `{"ok": True}`
**And** all four return `{"ok": True}` — actual action dispatch is the Flask proxy's responsibility, not the tool's

**Given** `SYSTEM_INSTRUCTION` is read
**When** its content is inspected
**Then** it includes all five behavioral rules:
1. Always call a tool when the user's intent clearly matches one of the four actions
2. If a required field is missing (origin or destination for `submit_trip`), ask one clarifying question — never call `submit_trip` with placeholder or fabricated values
3. Respond in the same language the user writes in (French or English)
4. After calling a tool, confirm the action in 1–2 sentences maximum
5. Do not invent station names, prices, or route details — the agent has no access to live data

**Given** `.env.example` is opened
**When** the file is read
**Then** it contains the line `GEMINI_API_KEY=` alongside the existing `GOOGLE_MAPS_API_KEY=`

**Given** `app.py` and `api/routes.py` are inspected
**When** they are read in full
**Then** neither file imports from `google.adk`, `google.generativeai`, `agent`, nor reads `GEMINI_API_KEY` from the environment
**And** `GEMINI_API_KEY` does not appear in any Flask source file — it is the ADK process's exclusive concern

---

### Story 5.2: POST /api/chat Proxy Endpoint

As a developer,
I want a `POST /api/chat` endpoint in the Flask Blueprint that proxies user messages to the ADK agent service and returns a normalized `{action, params, message}` JSON response,
So that the frontend has a single, stable contract for all chat interactions regardless of ADK's internal event format.

**Acceptance Criteria:**

**Given** `api/routes.py` is inspected after this story
**When** the Blueprint routes are read
**Then** `POST /api/chat` is registered on the Blueprint — zero chat-related code lives in `app.py`
**And** the handler is a function named `chat_with_agent()` (or similar, `snake_case` verb-prefixed)

**Given** a `POST /api/chat` request with body `{"message": "Montréal to Duhamel, 180 km range", "session_id": "abc-123", "is_context_update": false}`
**When** the endpoint is called with the ADK service running
**Then** Flask proxies to `http://localhost:5001/run` using `requests.post` with `timeout=10`
**And** the ADK request body is:
```json
{
  "app_name": "chekov_assistant",
  "user_id": "local_user",
  "session_id": "abc-123",
  "new_message": {
    "role": "user",
    "parts": [{ "text": "Montréal to Duhamel, 180 km range" }]
  }
}
```

**Given** the ADK service responds with an events list containing a `functionCall` part and a `text` part
**When** Flask normalizes the response
**Then** it returns HTTP 200 with body:
```json
{ "action": "submit_trip", "params": { "origin": "Montréal", "destination": "Duhamel", "range_km": 180, "waypoints": [] }, "message": "Planning Montréal → Duhamel with 180 km range — loading routes." }
```
**And** the first `functionCall` part in the events list is used for `action` + `params`
**And** the last `text` part in the events list is used for `message`

**Given** the ADK service responds with only a `text` part and no `functionCall`
**When** Flask normalizes the response
**Then** it returns HTTP 200 with body `{"action": "chat_only", "params": {}, "message": "<assistant text>"}`

**Given** the `action` value from normalization
**When** the response is returned
**Then** `action` is one of: `"submit_trip"`, `"add_waypoint"`, `"filter_stations_by_area"`, `"clear_filter"`, `"chat_only"` — never an arbitrary string

**Given** the ADK service is unreachable or the 10-second timeout is exceeded
**When** `POST /api/chat` is called
**Then** it returns HTTP 502 with body `{"error": "adk_agent", "message": "Assistant unavailable — use the form to plan your trip."}`
**And** the form-based `/api/plan` workflow continues to function normally — no shared state between the two endpoints

**Given** `GEMINI_API_KEY` from the environment
**When** `api/routes.py` is inspected
**Then** `GEMINI_API_KEY` does not appear anywhere in the file — Flask never reads, forwards, or logs it

---

### Story 5.3: Route Context Injection

As a developer,
I want `run.sh` updated to launch the ADK service alongside Flask, and `app.js` to silently inject current trip parameters into the ADK session after each successful plan query,
So that follow-up chat messages like "add a stop through Grenville" resolve correctly against the current trip without the user repeating origin and destination.

**Acceptance Criteria:**

**Given** `run.sh` is opened after this story
**When** the file is read
**Then** it starts the ADK agent service with `adk api_server agent --port 5001 &` before starting Flask
**And** the ADK process PID is stored in a variable (e.g., `ADK_PID=$!`)
**And** a `trap "kill $ADK_PID 2>/dev/null" EXIT` statement ensures the ADK process is killed when the script exits (Ctrl-C or normal termination)
**And** Flask is started last with `flask --app app run --debug` (blocking call)
**And** the existing `.env` loading and `GOOGLE_MAPS_API_KEY` unset warning are preserved unchanged

**Given** `app.js` is inspected
**When** it processes a successful `POST /api/plan` response
**Then** immediately after `renderCards()` completes, it fires a silent `POST /api/chat` with:
```json
{
  "message": "[TRIP CONTEXT] origin=\"<origin>\", destination=\"<destination>\", range_km=<range>, waypoints=<json_array>",
  "session_id": "<current session id from state.sessionId>",
  "is_context_update": true
}
```
**And** `app.js` does not await or handle the response body of this context update — it is fire-and-forget
**And** a HTTP 204 or HTTP 502 on the context update does not affect the UI in any way

**Given** `api/routes.py` receives a `POST /api/chat` request with `is_context_update: true`
**When** the handler processes it
**Then** it proxies the message to ADK (allowing ADK to append the context turn to session history) and returns HTTP 204 with no response body
**And** this branch executes regardless of ADK's response content — the 204 is unconditional once ADK acknowledges the call

**Given** the context message format
**When** `app.js` formats it
**Then** the message contains **only** origin, destination, range_km, and waypoints — never full route results, station prices, polylines, or drive times (keeps prompt tokens minimal and avoids sending detailed data outside localhost)

**Given** a page reload
**When** a new session starts
**Then** `state.js` generates a new `sessionId = crypto.randomUUID()` — the old session's context is lost, which is acceptable for a single-user local tool

---

### Story 5.4: Chat Box Component

As Olivier,
I want a persistent chat panel in the app where I can type natural-language messages and see the assistant's confirmations,
So that I can initiate or modify trips conversationally without needing to navigate the form directly.

**Acceptance Criteria:**

**Given** Flask is running and I navigate to `http://localhost:5000`
**When** the page loads
**Then** a `#chat-panel` section is visible at all times — it does not hide when a trip is submitted, while results are loading, or after results render
**And** the chat panel renders as a collapsible bottom section of the left column (cards panel):
  - Default state: **collapsed** — only the input bar (~48px height) with a chevron handle (▲), a text input (`#chat-input`, placeholder "Ask me to plan a trip…"), and a send button
  - Expanded state: overlays the cards panel upward, covering up to 60% of available height, showing the message thread (`#chat-messages`, scrollable) above the input bar; chevron points downward (▼)
**And** clicking the chevron or typing in the collapsed input expands the panel; clicking the chevron in expanded state collapses it

**Given** I type a message and press Enter or click the send button
**When** the message is submitted
**Then** my message appears immediately in `#chat-messages` as a right-aligned user bubble (uses `--text-primary` #111827 as background, white text, `border-radius: 12px 12px 0 12px`)
**And** a typing indicator (three animated dots) appears below the user bubble
**And** the `#chat-input` is cleared and disabled, the send button is disabled

**Given** the `POST /api/chat` response arrives
**When** the response is rendered
**Then** the typing indicator disappears
**And** the assistant's `message` from the response body appears as a left-aligned assistant bubble (`--surface` white background, `--border` border, `border-radius: 12px 12px 12px 0`)
**And** `#chat-input` is re-enabled and focused

**Given** the `POST /api/chat` returns HTTP 502
**When** the error is handled
**Then** the typing indicator disappears
**And** an error-styled assistant bubble appears with text "Assistant unavailable — use the form to plan your trip." (red-tinted, `--error` border)
**And** `#chat-input` is re-enabled — the user can try again

**Given** the chat panel layout on desktop (≥768px)
**When** I inspect the layout
**Then** the chat panel sits at the bottom of the left column (cards panel), with the collapsed input bar (~48px) always visible below the route cards
**And** when expanded, the chat thread overlays the cards panel upward (up to 60% of available height) — cards are still accessible by collapsing the chat
**And** `#chat-messages` is scrollable and auto-scrolls to the latest message on each new bubble

**Given** the chat panel layout on mobile (<768px)
**When** I inspect the layout
**Then** `#chat-panel` renders as a fixed-position bottom bar (`position: fixed; bottom: 0; width: 100%`)
**And** expanded state slides up covering the map area; cards remain visible and scrollable above

**Given** `style.css` is inspected
**When** the chat-related rules are read
**Then** user bubble, assistant bubble, and typing-indicator styles are present
**And** the typing indicator uses a CSS animation (e.g., `@keyframes bounce`) on three dot elements — no JavaScript-based animation

**Given** `static/js/chat.js` is loaded as an ES module
**When** its module boundary is inspected
**Then** it imports `state` from `state.js` (for `sessionId` and `setSelectedRoute`)
**And** it imports map functions (`filterMarkers`, `restoreMarkers`) from `map.js`
**And** it does not import from `app.js` — loading state and error banners remain exclusively owned by `app.js`

---

### Story 5.5: Chat State Management & Action Dispatch

As Olivier,
I want the chat assistant to automatically fill my trip form, add waypoints, and apply map filters based on my natural-language messages,
So that the chat panel is a fully capable alternative to the form — not just a text display.

**Acceptance Criteria:**

**Given** `state.js` is inspected after this story
**When** the module is read
**Then** it exports `sessionId` — a UUID string generated once via `crypto.randomUUID()` when the module is first imported
**And** `sessionId` is never written to `localStorage` — it lives in memory only; a page reload generates a new UUID
**And** `state.js` remains the exclusive owner of all `localStorage` access — `chat.js` does not call `localStorage` directly

**Given** `chat.js` receives a response with `action: "submit_trip"` and `params: { origin, destination, range_km, waypoints }`
**When** the dispatch runs
**Then** `chat.js` sets the `#origin`, `#destination`, and `#range` form input values from `params`
**And** each affected form field flashes with `--accent-light` (#DCFCE7) background (200ms ease-in, 800ms hold, 200ms ease-out) to visually bridge the chat action to the form update
**And** if `params.waypoints` is non-empty, `chat.js` appends the first waypoint to the waypoint input field (respecting the max-1-waypoint MVP rule)
**And** `chat.js` programmatically submits the trip form (equivalent to clicking "Find routes") — `app.js` loading state activates exactly as if the user had clicked the button
**And** a brief confirmation toast appears at the bottom of the cards panel in `text-sm` `--text-secondary` style showing the assistant's `message` text; the toast auto-dismisses after 4 seconds
**And** the route cards and map update with fresh results after the `/api/plan` response arrives

**Given** `chat.js` receives `action: "submit_trip"` but `params.origin` or `params.destination` is null or empty
**When** the dispatch runs
**Then** `chat.js` does NOT attempt form fill and does NOT submit `/api/plan`
**And** the assistant's `message` (a clarifying question from the agent) is displayed in the chat thread — `action: "chat_only"` behaviour applies

**Given** `chat.js` receives `action: "add_waypoint"` and `params: { waypoint: "Grenville" }`
**When** the dispatch runs
**Then** `chat.js` appends the waypoint to the trip form's waypoint input (creating it if not present, respecting max-1-waypoint rule)
**And** the waypoint form field flashes with `--accent-light` (#DCFCE7) background (200ms ease-in, 800ms hold, 200ms ease-out)
**And** the existing form values for origin, destination, and range are preserved unchanged
**And** `chat.js` programmatically re-submits the trip form — the route cards and map update with the waypoint-modified route
**And** a brief confirmation toast appears at the bottom of the cards panel showing the assistant's `message` text; the toast auto-dismisses after 4 seconds

**Given** `chat.js` receives `action: "filter_stations_by_area"` and `params: { area_name, lat, lng }`
**When** the dispatch runs
**Then** `chat.js` calls `map.filterMarkers(area_name, lat, lng)` — this is the only action taken; no form submission occurs
**And** station markers outside a ~25 km radius of `{ lat, lng }` are hidden on the map
**And** route polylines, route cards, savings recommendations, and best/worst station markers remain completely unchanged

**Given** `map.js` `filterMarkers(area_name, lat, lng)` is called
**When** the function executes
**Then** it iterates over all currently rendered station markers and hides any marker whose station's coordinates are more than 25 km from `{ lat, lng }` (Haversine)
**And** the function stores the set of hidden markers so `restoreMarkers()` can restore exactly those markers
**And** a filter badge appears top-left on the map container showing `📍 [area_name] · Show all` with a clickable "Show all" link that calls `restoreMarkers()`; badge uses `--surface` background, `--border` border, `text-sm`, `border-radius: 8px`

**Given** `chat.js` receives `action: "clear_filter"` and `params: {}`
**When** the dispatch runs
**Then** `chat.js` calls `map.restoreMarkers()`
**And** all previously hidden station markers become visible again on the map
**And** the filter badge on the map is removed

**Given** `chat.js` receives `action: "chat_only"` and `params: {}`
**When** the dispatch runs
**Then** only the assistant's `message` is displayed in the chat thread
**And** no form action, no map action, and no `/api/plan` request are triggered

**Given** `map.js` `filterMarkers` and `restoreMarkers` are inspected
**When** the module is read
**Then** both functions are exported (`export function filterMarkers(...)` and `export function restoreMarkers()`)
**And** neither function is defined inline in `index.html` or in any other module — `map.js` module ownership is preserved

