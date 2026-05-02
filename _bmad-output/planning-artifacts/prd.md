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
  - _bmad-output/planning-artifacts/product-brief-gaz_eye.md
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
lastEdited: '2026-05-01'
editHistory:
  - date: '2026-05-01'
    changes: 'Added Stale Price Anomaly Filter feature: Executive Summary differentiator bullet, 3 Measurable Outcomes, 5 MVP scope items, FR38-FR42 (Price Quality Filtering group), NFR11 (filter latency), updated Régie Essence freshness risk to Low'
---

# Product Requirements Document - gaz_eye

**Author:** Olivier
**Date:** 2026-04-30

## Executive Summary

Gaz Eye is a locally-hosted web application that optimizes fuel costs for road trips in Quebec. It replaces a fragmented workflow — Google Maps for routing, Régie Essence Québec for prices, mental arithmetic for range — with a single screen. The user enters an origin, destination, and remaining driving range; the app returns three alternative routes (including cross-province options via Ontario), each annotated with the cheapest reachable Quebec gas station and estimated savings.

The tool evolves an existing Python CLI (`gaz_saver.py`, 270 LOC) that already fetches and parses real-time gas pricing from the Régie de l'énergie du Québec's public GeoJSON dataset. The new product adds route-aware station discovery, fuel autonomy constraints, waypoint support, and an interactive map — while reusing the battle-tested pricing pipeline.

**Target user:** The developer (single user), driving urban, inter-city, and cross-province routes in Quebec — primarily the Montréal ↔ Duhamel / Mont-Tremblant corridor (~200 km), with Ontario route alternatives via Hawkesbury.

### What Makes This Special

- **Route-first, not station-first.** The question is "which route has the cheapest gas?" — not "where's cheap gas near me?" Three routes, each with its best fuel stop, compared in one view.
- **Quebec-native data moat.** Government-mandated real-time pricing for every station in the province — free, reliable, with GPS coordinates. No API key, no scraping, no stale crowd-sourced data.
- **Zero curation.** No manually maintained station lists. Every station within a configurable corridor of the route is discovered automatically.
- **Waypoint flexibility.** Force a route through a specific location (e.g., Grenville) and compare it against Google's alternatives — factoring in fuel cost for each option.
- **Fully private.** Runs locally on a laptop — no accounts, no cloud, no location tracking.
- **Data you can trust.** Before recommendations are built, every station's price is validated against its geographic neighbors. Stations priced anomalously below the local median (likely stale Régie listings) are silently excluded — no UI noise, no user action required. Known structural discounters (Costco, Olco) are explicitly exempted. Competitors cannot do this without an extra network call or cache layer; gaz_eye already holds the full dataset in memory.

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

### Measurable Outcomes

- 100% of stations along the Montréal ↔ Duhamel corridor (via all three route options) are correctly discovered and priced
- Autonomy filtering never recommends a station beyond the stated range minus safety buffer
- Cross-province routes (via Hawkesbury, ON) display correctly with Quebec-only station pricing
- Zero false positives on exempted structural discounters (Costco, Olco) — confirmed from day one
- Anomaly filter overhead < 100ms wall-clock on the full ~3,000-station Quebec dataset
- Anomaly filter can be disabled and re-enabled via `stations.yaml` without a code deploy

## Product Scope

### MVP (Phase 1)

**Core User Journeys Supported:** All four (Friday commute, waypoint detour, low fuel urgency, urban quick check)

**Must-Have Capabilities:**

- Web UI: origin, destination, range (km), optional waypoint(s)
- Google Maps Directions API: 3 alternative routes (including cross-province)
- Automatic Quebec station discovery within configurable corridor (default 2 km, Haversine)
- Real-time pricing from Régie Essence Québec GeoJSON (Quebec stations only)
- Spatial stale-price anomaly detection: density-adaptive geographic median filter (5–50 km radius, minimum 5 neighbors) excludes stations priced anomalously below their local median before recommendations are built
- Structural discounter exemption list (`anomaly_filter_exemptions` in `stations.yaml`) — case-insensitive substring patterns for legitimately-cheap operators (e.g., Costco, Olco)
- Anomaly filter kill switch (`anomaly_filter_enabled` in `stations.yaml`) — disables filter instantly without a code deploy
- Structured per-exclusion log entry (station name, price, local median, neighbor count, radius, data timestamp)
- Fuel autonomy constraint with configurable safety buffer (default: 10% of range or 15 km, whichever is greater)
- Per-route recommendation: cheapest reachable Quebec station
- Savings comparison: cheapest vs. most expensive reachable station on each route
- Interactive map with routes and station markers
- Configurable fuel type (Régulier / Super / Diesel) and tank size
- Settings panel for corridor distance and safety buffer

### Phase 2 (Growth)

- Driving detour time calculation (actual driving distance to station, not crow-flies)
- Out-of-province gas pricing integration (Ontario data sources)
- Station price history and trend visualization
- Cached/offline mode with last-known prices

### Phase 3 (Vision)

- Mobile-responsive or native mobile app
- Dynamic pricing APIs beyond Régie Essence
- Multi-province coverage (Ontario, New Brunswick)
- Route sharing

## User Journeys

### Journey 1: The Friday Evening Commute (Happy Path)

**Olivier** is leaving work in Montréal on a Friday evening, heading to his place near Duhamel for the weekend. His car shows about 180 km of range — enough to get there, but tight. He usually stops for gas somewhere along the way, but doesn't know which route has the best prices tonight.

He opens Gaz Eye on his laptop before leaving. Types "Montréal" as origin, "Duhamel" as destination, enters 180 km remaining range. The app loads three routes: Highway 50, Highway 15 through the Laurentians, and the cross-border route via Hawkesbury, ON.

Each route shows drive time, traffic conditions, and a recommended fuel stop with price. Highway 50 has a station at 1.42$/L near Lachute. The Hawkesbury route shows no Quebec station pricing on the Ontario segment — but the cheapest Quebec station before crossing is 1.45$/L. Highway 15 has a cluster of stations near Sainte-Agathe at 1.48$/L.

The savings panel shows: Highway 50's best stop saves $3.20 per tank vs. the worst option on that route. Olivier picks Highway 50 — slightly longer drive, but saves enough to cover the difference. He leaves knowing exactly where he'll stop.

### Journey 2: The Waypoint Detour (Forced Route)

Olivier needs to drop off a package in Grenville on his way to Duhamel. He enters the same trip but adds "Grenville, QC" as a waypoint.

Google Maps now generates routes that pass through Grenville. One route goes Montréal → Grenville → Highway 50 → Duhamel. Another takes Grenville → crosses to Hawkesbury → back into Quebec. The third stays entirely on the Quebec side via smaller roads.

Each route shows its best fuel stop. The Grenville-area route has a station at 1.43$/L — cheaper than anything on the direct Highway 15 route. Olivier sees that adding the Grenville stop only adds 12 minutes to his drive and actually gets him cheaper gas. Win-win.

### Journey 3: Low Fuel Urgency (Autonomy Constraint)

Olivier is already on the road near Brownsburg-Chatham with only 45 km of range left. He pulls over, opens Gaz Eye on his phone's browser (the laptop is running the server at home — he connects via local network, or he could have started it before leaving).

He enters his current location, destination "Mont-Tremblant", range "45 km". The app filters aggressively — most stations are out of range. Only 3 stations across all routes are reachable within the safety buffer (10% = 4.5 km margin).

The cheapest reachable station is 1.41$/L, 18 km ahead on his current route. The app highlights it clearly. No time for route comparison here — it's about "which station can I actually reach, and which one is cheapest?" The savings panel shows $2.85 vs. the most expensive reachable option.

### Journey 4: Urban Quick Check (Short Trip)

Olivier is driving across Montréal and wants to fill up on the way. He enters "Plateau, Montréal" → "Brossard", range "120 km". Plenty of fuel, no urgency.

Three short urban routes appear — all under 30 minutes. Each has multiple stations in the corridor. The cheapest is 1.39$/L on the route via Pont Jacques-Cartier. The most expensive is 1.52$/L near downtown. Savings: $6.50/tank. Even on a 20-minute city drive, the price difference is meaningful.

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
- Serve static frontend assets
- Google Maps API key management (server-side, not exposed to frontend)

### Implementation Considerations

- Reuse existing `gaz_saver.py` functions as a library (extract into importable module)
- Existing functional style (no classes) can be preserved for the backend logic layer
- New web-serving layer on top (Flask, FastAPI, or similar — TBD in architecture)
- Google Maps JavaScript API loaded in frontend for map rendering
- Google Maps Directions API called from backend (keeps API key server-side)

## Project Strategy

**MVP Approach:** Problem-solving MVP — deliver the core route+fuel comparison that replaces the fragmented manual workflow. If you can enter a trip and get three routes with fuel recommendations, the product is useful from day one.

**Resource Requirements:** Single developer (Olivier), working solo. Python backend + web frontend.

**Resource Contingency:** If time is short, the settings panel (corridor distance, safety buffer) can use config-file defaults instead of UI controls.

### Risk Mitigation

| Risk | Severity | Mitigation |
|------|----------|------------|
| Corridor matching accuracy (off-ramp stations 1-2 km from polyline) | High | Default 2 km corridor; configurable; validate against Montréal↔Duhamel corridor |
| Régie Essence data freshness (prices may lag hours) | Low | Spatial anomaly filter (FR38–FR42) detects and excludes stale outliers before recommendations; data timestamp displayed prominently for remaining stations |
| GeoJSON endpoint format change (no SLA) | Medium | Dual-parse strategy (JSON first, gzip fallback); graceful error display |
| Google Maps ToS compliance | Medium | Use Google Maps JavaScript API for rendering (compliant by design) |

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
