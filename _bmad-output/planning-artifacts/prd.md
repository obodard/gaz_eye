---
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-02b-vision
  - step-02c-executive-summary
  - step-03-success
  - step-04-journeys
  - step-05-domain-skipped
  - step-06-innovation-skipped
  - step-07-project-type
  - step-08-scoping
  - step-09-functional
  - step-10-nonfunctional
  - step-11-polish
  - step-12-complete
  - step-e-01-discovery
  - step-e-02-review
  - step-e-03-edit
releaseMode: phased
inputDocuments:
  - _bmad-output/planning-artifacts/product-brief-checkov.md
  - _bmad-output/planning-artifacts/product-brief-stale-price-filter.md
  - _bmad-output/project-context.md
  - docs/project-overview.md
  - docs/architecture.md
  - docs/development-guide.md
  - docs/source-tree-analysis.md
  - docs/index.md
workflowType: 'prd'
workflow: 'edit'
classification:
  projectType: web_app
  domain: general
  complexity: low
  projectContext: brownfield
lastEdited: '2026-06-01'
editHistory:
  - date: '2026-05-01'
    changes: 'Added Stale Price Anomaly Filter feature: Executive Summary differentiator bullet, 3 Measurable Outcomes, 5 MVP scope items, FR38-FR42 (Price Quality Filtering group), NFR11 (filter latency), updated Régie Essence freshness risk to Low'
  - date: '2026-05-09'
    changes: 'Extended Epic 4: FR43–FR47, bidirectional anomaly detection (expensive direction), worst_station in /api/plan response, red map marker for most expensive reachable station'
  - date: '2026-05-31'
    changes: 'Added Gemini Conversational Assistant feature (Epic 5): Executive Summary bullet, 3 user journeys (J5–J7), MVP scope items, FR48–FR63 (Conversational Assistant group), NFR12–NFR14, architecture considerations for Google ADK agent as separate service'
  - date: '2026-05-31'
    changes: 'PM alignment check after UX review: added FR67 (filter badge with click-to-clear on map) to close gap between UX-DR21 and FR60 chat-only clearing path'
  - date: '2026-06-01'
    changes: 'Architecture Enhancement Initiative (2026-05-31 review): Architecture Principles section added; FR68–FR75 (Operational Foundations + Agent Contract & Honesty); NFR15–NFR16 (frontend modularity); Technical Success + MVP scope updated; checkov.py references removed; Architecture Principles endorsed (mapping/pricing stay deterministic, agent-callable explanations deferred as future bet)'
---

# Product Requirements Document - checkov

**Author:** Olivier
**Date:** 2026-04-30

## Executive Summary

Checkov is a locally-hosted web application that optimizes fuel costs for road trips in Quebec. It replaces a fragmented workflow — Google Maps for routing, Régie Essence Québec for prices, mental arithmetic for range — with a single screen. The user enters an origin, destination, and remaining driving range; the app returns three alternative routes (including cross-province options via Ontario), each annotated with the cheapest reachable Quebec gas station and estimated savings.

The product grew from an existing Python CLI (`checkov.py`) that fetched and parsed real-time gas pricing from the Régie de l'énergie du Québec's public GeoJSON dataset. That CLI has since been superseded: its pricing logic lives in `api/pricing.py`, the canonical Régie Essence integration. The web product adds route-aware station discovery, fuel autonomy constraints, waypoint support, an interactive map, and a conversational assistant.

**Target user:** The developer (single user), driving urban, inter-city, and cross-province routes in Quebec — primarily the Montréal ↔ Duhamel / Mont-Tremblant corridor (~200 km), with Ontario route alternatives via Hawkesbury.

### What Makes This Special

- **Route-first, not station-first.** The question is "which route has the cheapest gas?" — not "where's cheap gas near me?" Three routes, each with its best fuel stop, compared in one view.
- **Quebec-native data moat.** Government-mandated real-time pricing for every station in the province — free, reliable, with GPS coordinates. No API key, no scraping, no stale crowd-sourced data.
- **Zero curation.** No manually maintained station lists. Every station within a configurable corridor of the route is discovered automatically.
- **Waypoint flexibility.** Force a route through a specific location (e.g., Grenville) and compare it against Google's alternatives — factoring in fuel cost for each option.
- **Fully private.** Runs locally on a laptop — no accounts, no cloud, no location tracking.
- **Talk to your trip.** A conversational assistant powered by Gemini lets the user modify routes, add waypoints, filter station markers, or start a trip entirely in natural language — no form clicking required. The assistant is a dedicated Google ADK agent that interprets intent and dispatches structured actions to the existing trip engine.
- **Data you can trust.** Before recommendations are built, every station's price is validated against its geographic neighbors. Stations priced anomalously below **or above** the local median (likely stale Régie listings) are silently excluded in both directions — preventing inflated savings from unrealistically cheap stations, and preventing the worst-station benchmark from being set by a stale high-price outlier. Known structural discounters (Costco, Olco) are explicitly exempted in both directions. The most expensive non-anomalous reachable station is displayed on the map as a distinct red marker, giving immediate visual context for the savings spread on each route. Competitors cannot do this without an extra network call or cache layer; checkov already holds the full dataset in memory.

## Project Classification

- **Type:** Web application (locally-hosted)
- **Domain:** General / personal utility
- **Complexity:** Low (single user, no auth, no compliance)
- **Context:** Brownfield — extending an existing CLI tool with proven pricing engine

## Success Criteria

### User Success

- Enter any trip (urban, inter-city, or cross-province) and receive a three-route comparison with fuel recommendations — no mental math, no tab-switching
- Recommended stations are always reachable within the stated driving range (safety buffer enforced)
- Adding a waypoint (e.g., Grenville) produces a valid route comparison against Google's unforced alternatives
- Never need to manually edit `stations.yaml` again — all station discovery is automatic

### Business Success

- Not applicable — personal tool. Success = the developer uses it instead of the manual workflow for every trip.

### Technical Success

- API response + computation + render completes within a few seconds of wall-clock time
- Savings calculations match live Régie Essence data (within ¢0.1/L accuracy)
- Corridor matching correctly identifies stations near highway off-ramps (2 km default, configurable)
- Graceful degradation when Régie Essence endpoint is slow or unavailable (display error, don't crash)
- Google Maps JavaScript API used for map rendering (ToS compliant)
- Régie Essence GeoJSON is cached with a configurable TTL; repeated plan requests within the TTL window make zero upstream Régie Essence calls
- All service endpoint addresses (ADK service URL, any future integrations) are externalized to environment variables; no service address is hardcoded in source
- 100% of `/api/plan` and `/api/chat` responses carry a unique request correlation ID echoed in backend logs
- Chat transcript contains zero auto-generated "user" messages; the assistant reads trip state via a `get_current_trip()` tool call when needed
- `checkov.py` is deleted; `api/pricing.py` is the single Régie Essence integration point
- No single JavaScript file exceeds 400 LOC; `app.js` is split into focused modules

### Measurable Outcomes

- 100% of stations along the Montréal ↔ Duhamel corridor (via all three route options) are correctly discovered and priced
- Autonomy filtering never recommends a station beyond the stated range minus safety buffer
- Cross-province routes (via Hawkesbury, ON) display correctly with Quebec-only station pricing
- Zero false positives on exempted structural discounters (Costco, Olco) — confirmed from day one, in both cheap and expensive anomaly directions
- Anomaly filter overhead < 100ms wall-clock on the full ~3,000-station Quebec dataset
- Anomaly filter can be disabled and re-enabled via `stations.yaml` without a code deploy
- Worst-station marker on the map always reflects a legitimately high price (never a stale outlier)

## Product Scope

### MVP (Phase 1)

**Core User Journeys Supported:** All four (Friday commute, waypoint detour, low fuel urgency, urban quick check)

**Must-Have Capabilities:**

- Web UI: origin, destination, range (km), optional waypoint(s)
- Google Maps Directions API: 3 alternative routes (including cross-province)
- Automatic Quebec station discovery within configurable corridor (default 2 km, Haversine)
- Real-time pricing from Régie Essence Québec GeoJSON (Quebec stations only)
- Spatial stale-price anomaly detection: density-adaptive geographic median filter (5–50 km radius, minimum 5 neighbors) excludes stations priced anomalously **below or above** their local median before recommendations are built — bidirectional filtering prevents both inflated savings (cheap stale outliers) and inflated cost-differentials (expensive stale outliers)
- Structural discounter exemption list (`anomaly_filter_exemptions` in `stations.yaml`) — case-insensitive substring patterns for legitimately-cheap operators (e.g., Costco, Olco); exemptions apply bidirectionally
- Anomaly filter kill switch (`anomaly_filter_enabled` in `stations.yaml`) — disables filter instantly without a code deploy
- Structured per-exclusion log entry (station name, price, local median, neighbor count, radius, data timestamp) emitted for both cheap and expensive exclusions
- Most expensive non-anomalous reachable station per route displayed on the map as a distinct red `AdvancedMarkerElement` pin alongside the cheapest station pin
- Fuel autonomy constraint with configurable safety buffer (default: 10% of range or 15 km, whichever is greater)
- Per-route recommendation: cheapest reachable Quebec station
- Savings comparison: cheapest vs. most expensive reachable station on each route
- Interactive map with routes and station markers
- Configurable fuel type (Régulier / Super / Diesel) and tank size
- Settings panel for corridor distance and safety buffer
- Conversational assistant chat panel (Gemini-powered via Google ADK agent) allowing natural-language trip initiation, waypoint addition, and map marker filtering
- Google ADK agent running as a separate service, proxied by the Flask backend
- Chat-driven trip initiation: user describes a trip in natural language → agent extracts parameters, auto-fills the form, and submits the plan request
- Chat-driven waypoint addition: user requests a route through a location → agent adds waypoint and re-submits
- Chat-driven map filtering: user requests station display for a specific area → agent filters map markers by geographic location

**Operational & Structural Foundations:**
- Régie Essence GeoJSON response caching with configurable TTL (default: 5 min) — repeated plan queries within the TTL window make zero upstream Régie Essence calls
- Environment-driven service configuration — ADK agent URL and all service addresses read from environment variables; no hardcoded addresses in source
- End-to-end request correlation IDs on all `/api/plan` and `/api/chat` responses
- Session-backed trip state — form submissions store trip parameters server-side; agent reads them via `get_current_trip()` tool (no silent form-to-chat POST)
- Single-source agent action contract — one schema definition drives ADK tool stubs, backend validation, and frontend dispatch for all 4 agent actions
- Schema validation on `/api/plan` and `/api/chat` boundaries with structured error responses
- `app.js` split into focused modules (≤400 LOC per file) as a dedicated modularization story
- `checkov.py` deleted — `api/pricing.py` is the sole Régie Essence integration

### Phase 2 (Growth)

- Driving detour time calculation (actual driving distance to station, not crow-flies)
- Out-of-province gas pricing integration (Ontario data sources)
- Station price history and trend visualization
- Cached/offline mode with last-known prices
- Agent-callable explanations: ask the assistant "why did route 2 rank lower?" or "why was station X excluded as stale?" — the agent calls existing pricing/geo functions and synthesizes a natural-language answer (requires single-source agent contract from Theme B to be in place)

### Phase 3 (Vision)

- Mobile-responsive or native mobile app
- Dynamic pricing APIs beyond Régie Essence
- Multi-province coverage (Ontario, New Brunswick)
- Route sharing

## User Journeys

### Journey 1: The Friday Evening Commute (Happy Path)

**Olivier** is leaving work in Montréal on a Friday evening, heading to his place near Duhamel for the weekend. His car shows about 180 km of range — enough to get there, but tight. He usually stops for gas somewhere along the way, but doesn't know which route has the best prices tonight.

He opens Checkov on his laptop before leaving. Types "Montréal" as origin, "Duhamel" as destination, enters 180 km remaining range. The app loads three routes: Highway 50, Highway 15 through the Laurentians, and the cross-border route via Hawkesbury, ON.

Each route shows drive time, traffic conditions, and a recommended fuel stop with price. Highway 50 has a station at 1.42$/L near Lachute. The Hawkesbury route shows no Quebec station pricing on the Ontario segment — but the cheapest Quebec station before crossing is 1.45$/L. Highway 15 has a cluster of stations near Sainte-Agathe at 1.48$/L.

The savings panel shows: Highway 50's best stop saves $3.20 per tank vs. the worst option on that route. Olivier picks Highway 50 — slightly longer drive, but saves enough to cover the difference. He leaves knowing exactly where he'll stop.

### Journey 2: The Waypoint Detour (Forced Route)

Olivier needs to drop off a package in Grenville on his way to Duhamel. He enters the same trip but adds "Grenville, QC" as a waypoint.

Google Maps now generates routes that pass through Grenville. One route goes Montréal → Grenville → Highway 50 → Duhamel. Another takes Grenville → crosses to Hawkesbury → back into Quebec. The third stays entirely on the Quebec side via smaller roads.

Each route shows its best fuel stop. The Grenville-area route has a station at 1.43$/L — cheaper than anything on the direct Highway 15 route. Olivier sees that adding the Grenville stop only adds 12 minutes to his drive and actually gets him cheaper gas. Win-win.

### Journey 3: Low Fuel Urgency (Autonomy Constraint)

Olivier is already on the road near Brownsburg-Chatham with only 45 km of range left. He pulls over, opens Checkov on his phone's browser (the laptop is running the server at home — he connects via local network, or he could have started it before leaving).

He enters his current location, destination "Mont-Tremblant", range "45 km". The app filters aggressively — most stations are out of range. Only 3 stations across all routes are reachable within the safety buffer (10% = 4.5 km margin).

The cheapest reachable station is 1.41$/L, 18 km ahead on his current route. The app highlights it clearly. No time for route comparison here — it's about "which station can I actually reach, and which one is cheapest?" The savings panel shows $2.85 vs. the most expensive reachable option.

### Journey 4: Urban Quick Check (Short Trip)

Olivier is driving across Montréal and wants to fill up on the way. He enters "Plateau, Montréal" → "Brossard", range "120 km". Plenty of fuel, no urgency.

Three short urban routes appear — all under 30 minutes. Each has multiple stations in the corridor. The cheapest is 1.39$/L on the route via Pont Jacques-Cartier. The most expensive is 1.52$/L near downtown. Savings: $6.50/tank. Even on a 20-minute city drive, the price difference is meaningful.

### Journey 5: Chat-Initiated Trip (Conversational Start)

Olivier opens Checkov and instead of filling the form, types into the chat panel: *"Montréal to Duhamel, 180 km range."*

The ADK agent extracts origin ("Montréal"), destination ("Duhamel"), and range (180 km). The form fields populate automatically and the plan request fires — no clicking required. Three routes appear on the map with fuel recommendations, exactly as if Olivier had filled the form manually.

Seeing the results, Olivier types: *"Add a stop through Grenville."* The agent recognizes a waypoint-addition intent, adds "Grenville, QC" as a waypoint, preserves the existing origin/destination/range, and re-submits. The map refreshes with Grenville-routed alternatives. Olivier compares fuel prices and picks the best option — all without touching the form.

### Journey 6: Chat Waypoint on Existing Trip (Form + Chat Hybrid)

Olivier fills in the trip form — Montréal to Duhamel, 180 km — and clicks Submit. Three routes load.

While reviewing the results, he realizes he wants to swing through Grenville. Instead of clearing the trip and re-entering everything, he types: *"Add a route through Grenville."*

The agent appends the waypoint, re-submits with the same parameters, and the map updates. The original routes are replaced with Grenville-passing alternatives. This is the same waypoint-addition action as Journey 5, but triggered from an existing form-submitted trip rather than a chat-initiated one.

### Journey 7: Chat-Driven Map Filtering (Price Exploration)

Olivier submitted Montréal → Duhamel and three routes are on screen. He notices station markers scattered across the full route and wants to focus on pricing near Mont-Tremblant.

He types: *"Show only the prices in Tremblant."*

The agent interprets this as a geographic filter request. Station markers on the map are filtered to display only stations in the Tremblant area — all other markers are hidden. The route cards and savings recommendations remain unchanged (the filter is visual only). Olivier can see at a glance what gas costs in Tremblant without the noise of stations 100 km away.

When he's done, he types *"Show all stations"* and the full marker set restores.

### Journey Requirements Summary

| Capability | Journeys | Priority |
|------------|----------|----------|
| Route fetching (3 alternatives via Google Maps) | All | MVP |
| Waypoint support (force route through location) | J2 | MVP |
| Station discovery within route corridor | All | MVP |
| Autonomy filtering with safety buffer | J1, J3 | MVP |
| Savings calculation (cheapest vs. worst) | All | MVP |
| Interactive map with routes + station markers | All | MVP |
| Cross-province route display (Ontario segments) | J1, J2 | MVP |
| Configurable corridor distance | J3, J4 | MVP |
| Configurable fuel type and tank size | All | MVP |
| Graceful handling of few/no reachable stations | J3 | MVP |
| Conversational assistant chat panel | J5, J6, J7 | MVP |
| Chat-driven trip initiation (NL → auto-fill + submit) | J5 | MVP |
| Chat-driven waypoint addition (append + re-submit) | J5, J6 | MVP |
| Chat-driven map marker filtering by location | J7 | MVP |
| Google ADK agent as separate service | J5, J6, J7 | MVP |

## Web Application Specific Requirements

### Project-Type Overview

Locally-hosted single-page web application (SPA) serving one user on a macOS laptop. No public deployment, no SEO, no multi-browser matrix. The app runs a Python backend and serves a web frontend accessed via `localhost`.

### Technical Architecture Considerations

- **SPA architecture** — single page with dynamic map and form updates; no server-side rendering needed
- **Browser support:** Latest Chrome or Safari on macOS only (single user's laptop)
- **SEO:** Not applicable — locally hosted, no public URL
- **Real-time:** Not required — user initiates queries, results are fetched on demand
- **Accessibility:** Not a priority for v1 (single user, personal tool)
- **Responsive design:** Desktop-first; mobile layout is a nice-to-have but not required

### Frontend Requirements

- Interactive map (Google Maps JavaScript API) displaying 3 routes simultaneously with distinct visual styling
- Station markers with price labels on the map
- Input form: origin, destination, range (km), optional waypoint(s)
- Recommendation panel: per-route comparison showing drive time, best station, price, and savings
- Settings panel: fuel type, tank size, corridor distance, safety buffer

### Backend Requirements

- Python HTTP server exposing API endpoints for the frontend:
  - Route calculation (proxy to Google Maps Directions API)
  - Station discovery (fetch Régie Essence GeoJSON, filter by corridor)
  - Price computation (reuse existing `parse_price_value` logic)
  - Chat proxy (forward user messages to the ADK agent service, relay structured responses)
- Serve static frontend assets
- Google Maps API key management (server-side, not exposed to frontend)
- Gemini API key management (server-side, consumed by the ADK agent only)

### ADK Agent Service

- A dedicated Google ADK agent runs as a separate process/service alongside the Flask backend
- The agent is built with the Google Agent Development Kit (ADK) and uses the Gemini API for natural language understanding
- The agent exposes a local API (HTTP or gRPC) that the Flask backend proxies to via `/api/chat`
- The agent defines structured tools corresponding to checkov actions:
  - **submit_trip**: extract origin, destination, range, and optional waypoints from natural language → return structured parameters
  - **add_waypoint**: extract a location name → return the waypoint to append
  - **filter_stations_by_area**: extract a geographic area name → return a filter descriptor (area name + approximate coordinates)
  - **clear_filter**: no parameters → signal the frontend to restore all markers
- The agent returns JSON responses with `action` (the tool name) and `params` (extracted values), which the frontend interprets to dispatch UI actions
- The agent maintains conversation context within a session so follow-up messages (e.g., "now add Grenville") resolve against the current trip state

### Implementation Considerations

- `checkov.py` has been deleted; `api/pricing.py` is the canonical Régie Essence client — do not reintroduce the standalone CLI
- Existing functional style (no classes) can be preserved for the backend logic layer
- New web-serving layer on top (Flask, FastAPI, or similar — TBD in architecture)
- Google Maps JavaScript API loaded in frontend for map rendering
- Google Maps Directions API called from backend (keeps API key server-side)

### Architecture Principles

- **Mapping and pricing stay deterministic.** Route-fetching, corridor-matching, and price-computation pipelines are fast synchronous Python functions. They are not wrapped in ADK agents or separate microservices — adding LLM non-determinism or extra network hops to these paths would increase latency and cost with no benefit.
- **The agent calls the app's logic as tools, not the other way around.** The conversational assistant accesses trip and pricing context exclusively through tool calls (e.g., `get_current_trip()`). Pricing and routing modules do not call the agent.
- **Agent-callable explanations are a future bet.** Capabilities such as "explain why route 2 ranked lower" or "why was station X excluded as stale?" are architecturally sound (the agent calls existing Python functions and synthesizes a natural-language answer) but deferred to Phase 2. They are not in scope for the current foundational epics.

## Project Strategy

**MVP Approach:** Problem-solving MVP — deliver the core route+fuel comparison that replaces the fragmented manual workflow. If you can enter a trip and get three routes with fuel recommendations, the product is useful from day one.

**Resource Requirements:** Single developer (Olivier), working solo. Python backend + web frontend.

**Resource Contingency:** If time is short, the settings panel (corridor distance, safety buffer) can use config-file defaults instead of UI controls.

### Risk Mitigation

| Risk | Severity | Mitigation |
|------|----------|------------|
| Corridor matching accuracy (off-ramp stations 1-2 km from polyline) | High | Default 2 km corridor; configurable; validate against Montréal↔Duhamel corridor |
| Régie Essence data freshness (prices may lag hours) | Low | Spatial anomaly filter (FR38–FR44) detects and excludes stale outliers in both directions before recommendations; data timestamp displayed prominently for remaining stations |
| GeoJSON endpoint format change (no SLA) | Medium | Dual-parse strategy (JSON first, gzip fallback); graceful error display |
| Google Maps ToS compliance | Medium | Use Google Maps JavaScript API for rendering (compliant by design) |
| Gemini API latency / availability | Medium | Chat is an enhancement — form-based workflow remains fully functional if the ADK agent or Gemini API is unavailable; timeout after 10 s with user-facing error in chat panel |
| ADK agent intent misclassification | Low | Scope limited to 4 structured tools; agent confirms action before dispatching; user can always fall back to the form |
| Régie Essence cache staleness | Low | TTL default 5 min; configurable; user sees data timestamp in UI (FR30) to assess price freshness |
| Session-state loss on server restart | Low | Single-user localhost tool; restart clears in-memory session — user re-submits the trip form |
| Agent action contract migration (3 definitions → 1) | Medium | Existing 4 tools remain functional during migration to single-source schema; schema-first validation deployed before old definitions are removed |

## Functional Requirements

### Trip Input

- FR1: User can enter a trip origin as a text address or place name
- FR2: User can enter a trip destination as a text address or place name
- FR3: User can enter remaining driving range in kilometers
- FR4: User can add one or more optional intermediate waypoints to force a route through a specific location
- FR5: User can remove a previously added waypoint
- FR6: User can submit a trip query and receive results

### Route Discovery

- FR7: System can fetch 3 alternative routes from Google Maps Directions API for the given origin, destination, and waypoints
- FR8: System can display drive time and distance for each route
- FR9: System can handle cross-province routes (e.g., Quebec ↔ Ontario) as valid alternatives
- FR10: System can decode route polylines into geographic waypoints for corridor matching

### Station Discovery

- FR11: System can fetch the complete Régie Essence Québec GeoJSON dataset (all Quebec gas stations with GPS coordinates and current prices)
- FR12: System can identify all Quebec gas stations within a configurable corridor distance of a route polyline (default: 2 km, Haversine)
- FR13: System can parse gas prices from the Régie Essence cent-string format into dollar values
- FR14: System can handle unavailable or missing price data gracefully (display as "n/a", exclude from recommendations)
- FR15: System can filter stations by the user's selected fuel type (Régulier, Super, or Diesel)

### Price Quality Filtering

- FR38: System can detect stations priced more than a configurable threshold (default: 5¢/L) below their local geographic median price and exclude them from recommendations by setting their price to the unavailable sentinel (`float('inf')`)
- FR39: System can compute a local median price for each station using a density-adaptive neighbor radius: starting at 5 km and expanding to 10 km, 20 km, then 50 km until a minimum of 5 neighbors are found; stations with fewer than 5 neighbors within 50 km bypass the filter
- FR40: System can exempt stations matching configurable name substrings (case-insensitive, defined in `stations.yaml`) from anomaly detection, treating them as full recommendation candidates regardless of their price relative to neighbors
- FR41: System can disable the anomaly filter entirely via a boolean flag (`anomaly_filter_enabled`) in `stations.yaml` without a code deploy
- FR42: System can emit a structured log entry for each excluded station containing: station name, station price, local median, neighbor count, radius used, and Régie Essence data timestamp
- FR43: System can detect stations priced more than a configurable threshold (default: 5¢/L) above their local geographic median price and exclude them from the worst-station selection by setting their price to the unavailable sentinel (`float('inf')`)
- FR44: Anomaly detection is bidirectional — stations priced anomalously below or above the local geographic median are both excluded using the same threshold constant and exemption list; a structured log entry is emitted for each exclusion in either direction
- FR45: System can include the most expensive non-anomalous reachable station (`worst_station`) per route in the `/api/plan` response, using the post-filter station list so stale high prices do not inflate savings calculations
- FR46: System can display the most expensive reachable station per route on the map as a distinct red `AdvancedMarkerElement` circular pin alongside the cheapest station pin, differentiating it visually from the route-colour cheapest pin
- FR47: User can hover a most-expensive station marker to see the station name and price; the marker enlarges when its route is selected, matching the selection behaviour of the cheapest station marker

### Autonomy Filtering

- FR16: System can calculate the distance from the trip origin to each discovered station along the route
- FR17: System can exclude stations that are beyond the user's remaining driving range minus a configurable safety buffer (default: 10% of range or 15 km, whichever is greater)
- FR18: System can handle the case where no stations are reachable on a given route (display a clear message)

### Recommendation Engine

- FR19: System can identify the cheapest reachable Quebec station for each route
- FR20: System can identify the most expensive reachable Quebec station for each route
- FR21: System can calculate savings per litre between the cheapest and most expensive reachable stations on each route
- FR22: System can calculate total tank savings based on the configured tank size
- FR23: System can rank the three routes by fuel cost to highlight the best option

### Map Visualization

- FR24: User can view all three routes displayed simultaneously on an interactive map with visually distinct styling
- FR25: User can view gas station markers on the map with price labels
- FR26: User can distinguish between the recommended station and other stations on each route
- FR27: User can interact with station markers to see station details (name, address, price, brand)
- FR46: User can view the most expensive reachable station per route as a distinct red circular marker on the map, shown alongside the cheapest station marker
- FR47: User can hover a most-expensive station marker to see its name and price; the marker enlarges on route selection, matching the cheapest station marker behaviour

### Recommendation Display

- FR28: User can view a comparison panel showing all three routes side by side with drive time, best station, fuel price, and savings
- FR29: User can see the savings amount (per litre and per tank) for each route's recommendation vs. worst option
- FR30: User can see the Régie Essence data timestamp to assess price freshness

### Configuration

- FR31: User can configure fuel type (Régulier / Super / Diesel)
- FR32: User can configure tank size in litres
- FR33: User can configure corridor distance (km from route polyline)
- FR34: User can configure the autonomy safety buffer

### Error Handling

- FR35: System can display a meaningful error when the Régie Essence GeoJSON endpoint is unavailable
- FR36: System can display a meaningful error when the Google Maps API returns no routes
- FR37: System can handle Google Maps API errors (invalid addresses, quota exceeded) with user-friendly messages

### Conversational Assistant (Chat)

#### Chat UI

- FR48: System displays a persistent chat panel alongside the map and route cards, accessible at all times regardless of trip state
- FR49: User can type natural-language messages into the chat panel to initiate trips, modify routes, or filter the map display
- FR50: System displays assistant responses in the chat panel with confirmation of the action taken (e.g., "Added Grenville as a waypoint — refreshing routes.")

#### Natural Language Trip Initiation

- FR51: When the user describes a trip via chat (e.g., "Montréal to Duhamel, 180 km range"), the ADK agent extracts origin, destination, and optional range/waypoints into structured parameters
- FR52: After extraction, the frontend auto-fills the trip form fields with the extracted values and automatically submits the plan request — no manual click required
- FR53: If the agent cannot extract a required field (origin or destination), it responds in the chat asking the user to clarify, rather than submitting an incomplete request

#### Natural Language Route Modification

- FR54: When the user requests adding a waypoint via chat (e.g., "add a route through Grenville"), the ADK agent extracts the waypoint location and returns an `add_waypoint` action
- FR55: The frontend appends the extracted waypoint to the current trip parameters, preserving existing origin, destination, and range, and re-submits the plan request
- FR56: Waypoint addition via chat works identically whether the original trip was submitted via the form (J6) or via chat (J5)

#### Natural Language Map Filtering

- FR57: When the user requests a geographic price filter via chat (e.g., "show only the prices in Tremblant"), the ADK agent extracts the area name and returns a `filter_stations_by_area` action with the area name and approximate coordinates
- FR58: The frontend filters map station markers to display only stations within a reasonable radius of the specified area — all other markers are hidden
- FR59: Geographic map filters apply to station markers only; route polylines, route cards, and savings recommendations remain unchanged
- FR60: User can clear a geographic filter via chat (e.g., "show all stations") to restore the full marker display
- FR67: When a geographic station filter is active, a filter badge appears on the map container displaying the filtered area name and a clickable "Show all" link; clicking the link clears the filter and restores all station markers without requiring chat interaction

#### ADK Agent Integration

- FR61: A dedicated Google ADK agent handles all chat interactions, running as a separate service with its own process
- FR62: The Flask backend exposes a `/api/chat` endpoint that proxies user messages to the ADK agent service and relays structured responses to the frontend
- FR63: The ADK agent uses the Gemini API for natural language understanding, intent classification, and parameter extraction
- FR64: The ADK agent defines structured tools (`submit_trip`, `add_waypoint`, `filter_stations_by_area`, `clear_filter`) that map to checkov UI actions
- FR65: The ADK agent returns JSON responses containing `action` (the tool/intent name), `params` (extracted values), and `message` (a human-readable confirmation to display in the chat)
- FR66: The ADK agent maintains conversation context within a session so follow-up messages (e.g., "now add Grenville") resolve against the current trip state without requiring the user to repeat origin/destination

### Operational Foundations

- FR68: System caches Régie Essence GeoJSON responses with a configurable TTL (default: 5 minutes); repeated `/api/plan` requests within the TTL window return the cached dataset without triggering an upstream Régie Essence call
- FR69: The ADK agent service URL and all external service endpoint addresses are read from environment variables at application startup; no service address is hardcoded in source code
- FR70: Every `/api/plan` and `/api/chat` response includes a unique request correlation ID (e.g., in an `X-Request-ID` response header and backend log entry) enabling end-to-end trace for a user-reported issue

### Agent Contract & Honesty

- FR71: A single schema source defines all agent action contracts (`submit_trip`, `add_waypoint`, `filter_stations_by_area`, `clear_filter`) — parameter names, types, and required fields — from which ADK tool stubs, backend validator, and frontend action dispatcher are all derived; adding a new agent action requires modifying this one file
- FR72: When the ADK agent returns an action payload with missing required parameters or incorrect types, the backend rejects it with a structured error response (including the request correlation ID) rather than silently misapplying partial data
- FR73: When the user submits a trip via the form, trip parameters are stored in a server-side session store; the frontend does not POST a synthetic "user" message to `/api/chat` as a side-effect of form submission
- FR74: When the ADK agent needs to know the current trip parameters to process a follow-up chat message, it calls a `get_current_trip()` tool that reads from the session store, rather than relying on data injected out-of-band by the frontend
- FR75: The chat transcript rendered to the user contains only messages the user explicitly typed; no auto-generated "user" messages appear in conversation history

## Non-Functional Requirements

### Performance

- NFR1: Route query results (3 routes + station discovery + recommendations) render within 5 seconds of user submission, given normal network conditions
- NFR2: Map with 3 routes and up to 50 station markers renders without visible lag or jank
- NFR3: Régie Essence GeoJSON dataset (gzip-compressed, all Quebec stations) is fetched and parsed within 3 seconds
- NFR4: Corridor matching (Haversine distance for all stations against route polyline) completes within 1 second for a 300 km route
- NFR11: Anomaly filter processing (spatial median computation over the full Quebec station dataset, ~3,000 stations) completes within 100ms wall-clock time

### Security

- NFR5: Google Maps API key is stored server-side only — never exposed to the frontend or included in client-side source
- NFR6: No user data is persisted, logged, or transmitted beyond the local machine

### Integration

- NFR7: Google Maps Directions API integration uses the `alternatives=true` parameter to request 3 routes per query
- NFR8: Régie Essence GeoJSON endpoint integration handles both pre-decompressed JSON and raw gzip responses (dual-parse strategy)
- NFR9: Régie Essence endpoint requires a browser-like User-Agent header — requests must include one to avoid being blocked
- NFR10: Google Maps JavaScript API is used for map rendering to comply with Google Maps Platform Terms of Service

### Conversational Assistant

- NFR12: Chat round-trip (user message → Flask proxy → ADK agent → Gemini API → structured response → UI action) completes within 5 seconds under normal network conditions
- NFR13: The ADK agent service is started alongside the Flask backend via the existing `run.sh` entry point (or equivalent single launch command)
- NFR14: Gemini API key is stored server-side only — consumed by the ADK agent process, never exposed to the frontend or included in client-side source

### Frontend Modularity

- NFR15: No single JavaScript file exceeds 400 LOC after the dedicated `app.js` modularization story ships; `app.js` is split into focused modules (form, cards, settings, UI state) with a single well-known entry point
- NFR16: Chat-to-map interactions are mediated through a single event bus or message channel; the chat module and map module do not directly import each other's functions
