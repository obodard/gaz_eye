---
title: "Product Brief: Stale Price Anomaly Filter"
project: checkov
status: "complete"
created: "2026-05-01"
updated: "2026-05-01"
inputs:
  - api/pricing.py
  - api/routes.py
  - stations.yaml
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/product-brief-checkov.md
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/project-context.md
---

# Product Brief: Stale Price Anomaly Filter

## Executive Summary

checkov's route-first architecture already holds the entire Quebec fuel dataset — ~3,000 stations — in memory for every `/api/plan` request. No other Quebec fuel price tool does this. Most apps are station-first: they look up prices on demand and have no spatial context. checkov, because it builds full trip corridors, possesses the one thing needed to make price data trustworthy: the ability to compare every station to its neighbors at the moment of query.

That capability is currently unused. Gas stations in Quebec are legally required to report their prices to the Régie de l'énergie, but enforcement of update frequency is lax. Some stations — particularly independent operators — go days or weeks without updating their listing. When fuel prices rise regionally, these stations retain a stale (artificially low) price in the public GeoJSON feed, silently distorting any recommendation system that treats all prices as equally valid.

The Stale Price Anomaly Filter activates checkov's latent spatial advantage. Before recommendations are built, each station's price is compared to its geographic neighbors (density-adaptive radius, robust to both urban density and rural sparsity). Stations priced significantly below their local median are flagged as likely stale and excluded. Silent. Logged. Zero API changes. Just recommendations that can be trusted.

## The Problem

The `/api/plan` endpoint recommends the cheapest reachable station per corridor segment. This logic is correct when all prices are current — and silently wrong when they aren't.

The failure mode: a station that last updated 72 hours ago at 158.9¢/L now shows as cheapest in a corridor where the market has moved to 165¢/L. The recommendation engine routes the user toward it. The user arrives and pays current market price — or discovers the station has no posted price at all. The app has given confidently wrong guidance.

This is not a rare edge case. The Régie de l'énergie's own data freshness is documented as a medium-severity risk in checkov's product brief. User communities in r/montreal and r/Quebec regularly describe this exact failure from GasBuddy and Prix-Essence.ca. It is the known, systematic failure mode of every app that consumes regulatory fuel data without validation — and none of checkov's competitors have solved it.

The primary corridor at risk: Montréal → Laurentians (Mont-Tremblant, Duhamel). Rural independent stations in this zone are the most likely to have stale prices and the least likely to be caught by a naive filter, because their neighbors are sparse and far apart.

## The Solution

Before recommendations are built, run a spatial anomaly check over the full station dataset:

1. **For each station**, find geographic neighbors using a density-adaptive radius:
   - Start at 5 km; expand to 10 km, 20 km, 50 km until a minimum of 5 neighbors are found
   - If fewer than 5 neighbors exist within 50 km, skip the filter for that station (cannot establish a reliable local median)
2. **Compute the local median price** across those neighbors
3. **If the station's price is more than the anomaly threshold below the local median** (configurable, default 5¢/L = 0.05 $/L), mark it as anomalous by setting `price_per_litre` to `float('inf')` — the existing sentinel for unavailable prices — and log the exclusion
4. **Log the exclusion** with: station name, station price, local median, neighbor count, radius used, and the Régie data timestamp — structured, auditable, without user disruption

Anomalous stations are automatically excluded by the existing `build_recommendation()` function, which already filters on the `float('inf')` sentinel. Zero changes to existing function signatures or API response structure.

**Structural discounter exemption:** An `anomaly_filter_exemptions` list in `stations.yaml` holds name substrings (case-insensitive) for known structural discounters — e.g., `"costco"`, `"olco"`. Stations matching any exemption pattern bypass anomaly detection entirely and remain full recommendation candidates. These operators are legitimately priced 5–8¢/L below neighbors; they are the correct answer, not a data problem.

**Kill switch:** An `anomaly_filter_enabled` flag in `stations.yaml` (default: `true`) allows the filter to be disabled instantly without a code change or deploy, if unexpected exclusion behavior is observed.

## Known Limitations

**Clustered staleness:** If all stations in a rural corridor have the same stale price — because they're all independents who last updated simultaneously — the local median is itself stale and the filter finds no anomaly. This is the most likely failure mode in the Laurentians specifically. Mitigation in a future iteration: compare the cluster median against a wider regional reference.

**Price-drop inversion:** The filter flags stations priced below their local median. During sharp price drops, stations that updated quickly will price *below* their slower-updating neighbors — and would be incorrectly flagged as anomalous. The filter implicitly assumes a rising-price context. This is accepted behavior for v1; its primary use case (rising prices, stale stations appearing cheap) is the significantly more common and more harmful case.

## What Makes This Different

No existing Quebec fuel price tool — GasBuddy, Prix-Essence.ca, Gasoline.ca — applies spatial anomaly detection to the Régie de l'énergie feed. All treat every listed price as equally valid. GasBuddy's crowdsourced approach is itself stale by design. The government's own NRCan disclaimer acknowledges that published fuel prices "may not reflect the most current prices."

The competitive moat here is architectural, not algorithmic. Competitors cannot add this filter without a second network call, a cache layer, or a spatial database query per request. checkov already has the data in memory. The filter is computationally free relative to what's already running.

The exemption list is a second quiet moat: checkov explicitly models Quebec's structural discount tier. The recommendations are correct for both genuinely-cheap stations and cheap-by-discount-design stations — a distinction no other app makes.

## Who This Serves

**Olivier** — sole user, planning fuel-optimized drives from Montréal through the Laurentians. The target corridors are exactly the zones where rural independent stations are most likely to have stale prices and where a 5–8¢/L misrouting has the highest cost (no nearby alternative).

## Success Criteria

- Zero false positives on exempted structural discounters (Costco, Olco) from day one
- After 4 weeks of operation, at least one logged exclusion manually confirmed as a true positive by cross-referencing the excluded station's price against a secondary source (Prix-Essence.ca or GasBuddy) on the same day
- No perceptible latency increase on `/api/plan` responses; filter overhead benchmarked at <100ms wall-clock on the full ~3,000-station dataset in the target runtime environment
- Filter can be disabled and re-enabled via `stations.yaml` without a code deploy

## Scope

**In scope (v1):**
- `detect_stale_prices(stations, all_stations, threshold, exemptions)` function in `api/pricing.py` — density-adaptive spatial median filter
- `anomaly_filter_exemptions` list in `stations.yaml` — case-insensitive substring patterns matched against station `name` field
- `anomaly_filter_enabled` boolean in `stations.yaml` — global kill switch
- `ANOMALY_THRESHOLD_CAD` constant in `api/pricing.py` (default: `0.05` $/L = 5¢/L)
- Structured log entry per excluded station via existing `checkov.pricing` logger
- Unit tests in `tests/test_pricing.py` — covering: normal exclusion, exemption bypass, sparse rural fallback (< 5 neighbors in 50km), price-drop inversion, kill switch

**Out of scope (v1):**
- Any UI or API response structure changes
- A distinct sentinel value separating "stale" from "unavailable" prices (tracked as future work)
- Time-based staleness detection using Régie last-update timestamps
- Ontario station coverage (Régie data is Quebec-only)
- Automated exemption list population or refresh
- Clustered-staleness detection via regional reference median

## Roadmap Thinking

The natural v2 is time-based staleness: if the Régie feed exposes a per-station last-update timestamp, combine it with the spatial signal — a station that is both cheaper than its neighbors *and* last updated 72+ hours ago is a near-certain stale. The spatial filter alone has false negatives at the margins; timestamp + spatial has almost none.

The exemption list, once it covers major chains by brand substring, becomes the foundation for a "discount chain only" routing mode — show me only Costco and Olco on this route. No additional data required; the classification is already done.

The per-station exclusion log, accumulated over months, becomes a reliability dataset: which stations in Quebec are chronic non-updaters. That is data no one else has.
