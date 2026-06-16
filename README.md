# ⛽ Checkov — Régie Essence Québec

Checkov is your fuel-price navigator, named after Pavel Chekov, navigator of the Enterprise, because even starships need someone to say, “Keptin, I have found cheaper gas three sectors east.”
More seriously, it's a locally hosted web app for planning fuel-efficient road trips in Quebec. It combines Google Maps routing with live Régie Essence Québec fuel prices, then compares up to three route alternatives by drive time, reachable stations, and estimated fuel savings.

The app is built for a single local user. It runs a Flask backend, a vanilla JavaScript SPA, and an optional Gemini-powered Google ADK assistant.

## Features

- Route planning with Google Maps Directions API, including optional waypoints.
- Automatic Quebec gas-station discovery along each route corridor.
- Live Régie Essence Québec pricing from the public GeoJSON feed.
- Fuel autonomy filtering using remaining range and a safety buffer.
- Per-route best and worst reachable station recommendations.
- Savings estimates per litre and per tank.
- Bidirectional stale-price anomaly filtering for unusually cheap or expensive prices.
- Exemptions and kill switch for the anomaly filter via `stations.yaml`.
- Interactive Google Maps display with best and most expensive station markers.
- Chat assistant for trip submission, waypoint additions, and map station filtering.

## Requirements

- Python 3.9+
- A Google Maps API key with Directions API and Maps JavaScript API access.
- A Gemini API key if you want to use the chat assistant.

Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a local `.env` file:

```bash
GOOGLE_MAPS_API_KEY=your_google_maps_key
GEMINI_API_KEY=your_gemini_key
```

`GOOGLE_MAPS_API_KEY` is required for route planning and map rendering. `GEMINI_API_KEY` is only required for chat.

## Run

```bash
./run.sh
```

Then open:

```text
http://127.0.0.1:5000
```

`run.sh` starts the ADK agent service on port `5001`, then starts Flask in debug mode on port `5000`.

## Configuration

Most trip settings are controlled in the web UI and stored in browser `localStorage`:

- fuel type: `Régulier`, `Super`, or `Diesel`
- tank size
- corridor radius
- safety buffer
- maximum route alternatives

`stations.yaml` is still used for:

- legacy CLI station lists
- default legacy fuel/tank settings
- anomaly filter controls:

```yaml
anomaly_filter_enabled: true
anomaly_filter_exemptions: ["costco", "olco"]
```

The web app no longer requires manually curated station lists for route planning. Stations are discovered automatically from the Régie Essence Québec dataset.

## API

Primary endpoints:

- `POST /api/plan` - returns route alternatives with station recommendations.
- `POST /api/chat` - proxies chat messages to the local ADK agent.
- `GET /api/nearest_station` - returns the nearest station for a coordinate pair.

The backend fetches Régie Essence data before calling Google Maps, so Régie failures return before spending a Maps quota call.

## Legacy CLI

`checkov.py` remains in the repository as a standalone CLI. The current web app does not import it; the canonical pricing pipeline for the web app is `api/pricing.py`.

Run the legacy CLI with:

```bash
python3 checkov.py
```

## Project Status

This README reflects the BMAD artifacts last updated on 2026-06-15:

- `_bmad-output/planning-artifacts/prd.md`
- `_bmad-output/planning-artifacts/architecture.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/project-context.md`

BMAD sprint status marks Epics 1-5 complete: foundation, route planning API, SPA, price-quality filtering, and conversational assistant.
