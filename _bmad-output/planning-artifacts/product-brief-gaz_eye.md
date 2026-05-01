---
title: "Product Brief: Gaz Eye"
status: "complete"
created: "2026-04-30"
updated: "2026-04-30"
inputs:
  - gaz_saver.py
  - stations.yaml
  - docs/project-overview.md
  - docs/architecture.md
  - _bmad-output/project-context.md
---

# Product Brief: Gaz Eye

## Executive Summary

Quebec drivers face an invisible tax every time they fill up on the road: they stop at whichever station is convenient, not whichever station is cheapest. The price difference between two stations 20 km apart on the same highway can be 8–12 cents per litre — $4–6 per tank, hundreds of dollars per year on a regular commute.

Gaz Eye is a personal web application that eliminates this guesswork. Enter your trip origin, destination, and remaining driving range. The app presents three alternative routes via Google Maps — including cross-province options (e.g., Montréal to Duhamel via Hawkesbury, ON vs. Highway 50 vs. Highway 15) — each annotated with the cheapest reachable Quebec gas station along that corridor and the estimated fuel cost. You choose the route that best balances drive time, traffic, and fuel savings — in a single screen.

The tool builds on an existing, proven CLI utility that already fetches real-time pricing from the Régie de l'énergie du Québec's public dataset — covering every gas station in the province, with GPS coordinates and current prices. Gaz Eye evolves this battle-tested pricing engine from a manual price-checker into an intelligent, route-aware trip advisor. Routes that cross into Ontario will show Quebec stations only — the user can factor in known cross-border price differences (typically ~5¢/L cheaper in Ontario) at their own discretion.

## The Problem

Planning a fuel-efficient road trip in Quebec today requires juggling three separate tools:

- **Station discovery is manual.** The existing CLI tool requires hand-entering station addresses into a YAML config file, found by browsing regieessencequebec.ca. Mismatched substrings produce silent failures.
- **No route awareness.** The current tool shows prices for pre-selected stations regardless of where you're actually driving. A cheap station 100 km off your route is useless information.
- **No range constraint.** There's no concept of "can I actually reach this station on my remaining fuel?" — the user mentally calculates range vs. distance, with no margin of error.
- **No route flexibility.** If you need to pass through a specific town (drop something off, pick someone up), there's no way to factor that into the fuel comparison.
- **Decision fragmentation.** Route choice (Google Maps), fuel pricing (Régie Essence), and range math (mental arithmetic) live in three separate places. The user is the integration layer.

The result: most of the time, you just stop wherever is convenient and pay whatever they charge.

## The Solution

Gaz Eye is a locally-hosted web application that combines route planning and fuel optimization into a single view:

1. **Input:** Origin, destination, remaining driving range (km), and optional intermediate waypoints to force a route through a specific location (e.g., "stop by Grenville")
2. **Routes:** Fetches 3 alternative routes via Google Maps Directions API, showing drive time and traffic conditions
3. **Station Discovery:** For each route, automatically identifies all Quebec gas stations within a configurable corridor (default: 2 km Haversine distance from the route polyline) using the Régie Essence Québec GeoJSON dataset. Stations on out-of-province segments of a route are not priced (data source is Quebec-only) but the route itself is still valid — the user evaluates cross-border pricing independently
4. **Autonomy Filtering:** Eliminates stations the user can't reach on remaining fuel, applying a configurable safety buffer (default: 10% of stated range or 15 km, whichever is greater)
5. **Recommendation:** For each route, recommends the cheapest reachable station and calculates savings vs. the most expensive reachable station on that route (i.e., "what you'd pay if you stopped at the worst option")
6. **Display:** Interactive map showing all three routes with station markers, prices, and a recommendation panel comparing per-route fuel cost at a glance

The user sees three routes — each with drive time, best fuel stop, and savings vs. the worst option — and picks the one that fits their priorities. Adding a waypoint forces at least one route through that location, so you can compare "my preferred route" against Google's alternatives.

## What Makes This Different

- **Quebec-native data advantage.** The Régie de l'énergie publishes prices for every gas station in the province — a government-mandated, free, reliable dataset with no API key required. No scraping, no stale crowd-sourced reports. The GeoJSON endpoint is confirmed public and unauthenticated (requires only a standard User-Agent header).
- **Route-first, not station-first.** Unlike GasBuddy or Waze fuel features that show nearby cheap stations, Gaz Eye shows the cheapest station *on your actual driving path*. The question isn't "where's cheap gas near me?" — it's "which route has the cheapest gas?"
- **Three routes, one decision.** By presenting route alternatives with fuel costs baked in, the app turns a multi-tool decision into a single-screen comparison. You weigh time, traffic, and fuel cost together.
- **Zero curation.** No maintaining a list of favorite stations. Every station along every route is discovered automatically from the full provincial dataset.
- **Fully local, fully private.** Runs on your laptop — no accounts, no cloud, no location tracking. Your trip data never leaves your machine.

## Who This Serves

**Primary user:** A single Quebec driver (the developer) who drives a mix of urban, inter-city, and cross-province routes — primarily the Montréal ↔ Duhamel / Mont-Tremblant corridor (~200 km, with Ontario route alternatives via Hawkesbury) — and wants to minimize fuel costs without manual effort.

The tool runs locally on a macOS laptop. No multi-user infrastructure, authentication, or deployment complexity.

## Success Criteria

- User can input any trip (urban, inter-city, or cross-province) and receive route + fuel recommendations within a few seconds of API response time
- Recommended stations are always reachable within the remaining driving range (respecting safety buffer)
- Savings calculations match live Régie Essence data (within ¢0.1/L)
- The three-route comparison view is clear enough to make a decision without additional tools or mental math
- Eliminates the need to manually maintain `stations.yaml`

## Scope

**In (v1):**

- Web UI with origin / destination / range input (km) and optional waypoint(s) to force a route
- Google Maps Directions API integration for 3 alternative routes (including cross-province routes)
- Waypoint support to force routes through specific locations (e.g., Grenville area) — Google Maps treats these as intermediate stops, generating route alternatives that pass through the waypoint
- Automatic Quebec station discovery within a configurable corridor distance (default 2 km from route polyline, Haversine)
- Real-time pricing from Régie Essence Québec GeoJSON endpoint (Quebec stations only; out-of-province segments show routes without station pricing)
- Fuel autonomy constraint with configurable safety buffer
- Per-route recommendation: cheapest reachable Quebec station
- Savings comparison: cheapest vs. most expensive reachable station on each route
- Interactive map display with routes and station markers
- Configurable fuel type (Régulier / Super / Diesel) and tank size

**Out (v1):**

- Out-of-province gas pricing (Ontario, etc.) — user evaluates cross-border prices independently
- Station price history or trends
- Driving detour time calculation (corridor uses crow-flies distance, not driving distance)
- Mobile app
- Dynamic pricing APIs beyond Régie Essence
- User accounts or cloud deployment
- Route sharing or social features

## Technical Approach (High-Level)

- **Backend:** Python — reuses the existing pricing pipeline from `gaz_saver.py` (GeoJSON fetch, price parsing, delta calculations)
- **Frontend:** Web-based (framework TBD during architecture phase) with embedded Google Maps for route and station visualization
- **Routing API:** Google Maps Directions API (~$5/1,000 requests; at personal usage of a few queries/day, cost is negligible — well under $10/year)
- **Geospatial matching:** Haversine distance from decoded route polyline waypoints to station GPS coordinates in the GeoJSON dataset
- **Data source:** Régie Essence Québec public GeoJSON (`regieessencequebec.ca/stations.geojson.gz`), fetched fresh per query or cached briefly

## Key Technical Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Corridor matching accuracy — stations near highway off-ramps may be 1–2 km from the route polyline | High | Default corridor to 2 km; make configurable; validate against known corridor |
| Régie Essence data freshness — prices may lag by hours | Medium | Display data timestamp; user decides if acceptable |
| GeoJSON endpoint format change or unavailability (no SLA) | Medium | Graceful error handling; existing CLI's dual-parse strategy handles format variations |
| Google Maps terms of service — route display may require Google Maps SDK | Medium | Use Google Maps JavaScript API for map rendering (compliant by design) |
| Autonomy calculation assumes linear fuel consumption | Low | Safety buffer provides margin; user sets conservative range estimate |
| Cross-province routes show Quebec stations only — user has no priced data for Ontario segments | Low | By design: Régie Essence covers QC only; user knows Ontario is typically ~5¢/L cheaper and factors it in manually |
