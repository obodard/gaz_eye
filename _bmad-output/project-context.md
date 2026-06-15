---
project_name: 'gaz_eye'
user_name: 'Olivier'
date: '2026-06-15'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'pricing_geo_rules', 'adk_rules', 'critical_rules']
status: 'complete'
rule_count: 52
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- **Python** 3.9+ (uses `dict[str, Any]`, `list[dict]` built-in generics)
- **Flask** 3.1.3 — app factory pattern, Blueprint routing, Jinja2 template serving
- **python-dotenv** — `.env` loading on startup; `GOOGLE_MAPS_API_KEY` required at runtime
- **requests** — HTTP client for GeoJSON fetch and Google Maps Directions API
- **pyyaml** — YAML config parser (`stations.yaml`)
- **colorama** — terminal output only in `gaz_saver.py` (not in Flask app)
- **polyline** — Google Maps encoded polyline decode/encode
- **google-adk ≥1.0** — ADK agent definition; runtime service at `http://localhost:5001`
- **Data source:** `https://regieessencequebec.ca/stations.geojson.gz` (public, no API key)
- **Maps API:** Google Maps Directions API (requires `GOOGLE_MAPS_API_KEY` env var)

## Critical Implementation Rules

### Language-Specific Rules

- **Type hints:** Use built-in generics (`dict[str, Any]`, `list[dict]`) — only import `Any`, `Optional` from `typing`; never import `Dict`, `List`, `Tuple` from typing
- **Logging:** Use named `logging.getLogger("gaz_eye.<module>")` — formatter is `%(message)s` only (no timestamps/levels). Add handler only if `not logger.handlers` to avoid duplicate output
- **Error contracts differ by module:**
  - `gaz_saver.py`: calls `sys.exit(1)` on fatal errors
  - `api/pricing.py`: raises `requests.RequestException` or `ValueError` — callers must catch
  - `api/routes.py`: catches exceptions and returns `jsonify({"error": ..., "message": ...})` with 4xx/5xx
- **`float('inf')` is the universal sentinel** for missing/unparseable/unavailable prices — check with `== float('inf')`, not `math.isinf()`, unless both +inf and -inf must be caught
- **`float('inf')` is not JSON-serializable** — convert to `None` before calling `jsonify()` (done in `routes.py` before building the response)
- **Path resolution:** Use `Path(__file__).parent` — never hardcoded absolute paths
- **`encoding="utf-8"` mandatory** when opening any file — French station names and addresses contain accented characters
- **f-strings only** — no `.format()` or `%` interpolation
- **`snake_case`** for functions/variables; **`UPPER_CASE`** for module-level constants
- **Docstrings:** One-line imperative mood on every function (e.g., `"Return the great-circle distance in km."`)
- **Imports:** stdlib → third-party → local, alphabetical within groups

### Flask & Architecture Rules

- **App factory pattern:** `create_app()` in `app.py` is the sole entry point — never instantiate `Flask()` outside it; never add `@app.route` in `app.py`
- **Blueprint-only routing:** All routes live in `api/routes.py` under the `bp` Blueprint; register with `app.register_blueprint(bp)`
- **SPA served via Jinja2 template:** `static/index.html` is rendered with `render_template("index.html", google_maps_api_key=...)` — `GOOGLE_MAPS_API_KEY` is injected server-side; never expose it in a JSON response
- **Module boundaries:**
  - `api/geo.py` — pure functions only, no network calls, no side effects
  - `api/pricing.py` — GeoJSON fetch + price logic; raises on failure
  - `api/routes.py` — HTTP layer only; orchestrates geo + pricing calls; handles all error responses
  - `agent/agent.py` — ADK agent definition only; tool functions return `{"ok": True}` (stubs)
- **ADK proxy pattern:** `/api/chat` proxies to the ADK service at `http://localhost:5001`; the payload format is `{appName, userId, sessionId, newMessage: {role, parts: [{text}]}}` — do not alter this shape
- **`is_context_update` flag:** When `body.get("is_context_update") is True`, the chat endpoint returns `204` immediately after forwarding — no response body, no error on ADK failure
- **API key masking:** When logging Google Maps errors, replace the raw API key with `***` — pattern: `str(exc).replace(api_key, "***")`
- **GeoJSON coordinates are `[lng, lat]`** (GeoJSON spec, not `[lat, lng]`) — always unpack as `coords[0]` = lng, `coords[1]` = lat
- **Station fetch before Maps API call:** In `/api/plan`, fetch Régie Essence data first; a Régie failure returns 502 before consuming a Google Maps quota call
- **`anomaly_filter_enabled` and `anomaly_filter_exemptions`** are read from `stations.yaml` at request time — not cached; default `True`/`[]` on YAML read failure

### Testing Rules

- **Runner:** `pytest` — test files in `tests/`, named `test_<module>.py`, classes named `Test<Subject>`
- **Flask test client:** Use `create_app()` + `app.config["TESTING"] = True` + `app.test_client()` — never import `app` directly as a module-level global in tests
- **Mock `GOOGLE_MAPS_API_KEY`:** Use `monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "test_api_key_dummy")` in the client fixture — tests must never require a real key
- **Never hit live endpoints:** Mock `requests.get` for all GeoJSON and Google Maps calls — use `unittest.mock.patch`
- **Mock `open()` for YAML config reads** in route tests — use `unittest.mock.mock_open` with valid YAML content
- **`_make_gm_response()` helper pattern:** Build minimal Google Maps response dicts with real encoded polylines (use `polyline_lib.encode(...)`) — fake polylines cause `decode_polyline` to fail silently
- **`float('inf')` in station fixtures:** Set `price_per_litre` to `float('inf')` (not `None`) when simulating unavailable prices — the JSON serialization to `null` happens in `routes.py`, not in test data
- **Test `detect_stale_prices` with a `valid_pool` broader than the corridor** — the function compares against `all_stations`, not `corridor_stations`
- **ADK tool functions are stubs:** `submit_trip`, `add_waypoint`, etc. always return `{"ok": True}` — test the return value, not side effects
- **`test_agent.py` imports from `agent.agent`** — do not import from `agent` package root (no re-export in `__init__.py`)

### Pricing & Geospatial Rules

- **Dual-parse GeoJSON:** Try `json.loads(resp.content)` first (endpoint may auto-decompress); fall back to `gzip.decompress()` — never assume one format
- **Price format:** API returns cent-strings with `¢` suffix (e.g., `"154.9¢"`) — strip symbol, divide by 100 for $/L; handle `None`, empty string, and `IsAvailable: false` → `float('inf')`
- **GeoJSON station name logic:** Use `brand` if non-empty and not `"Aucun"`, otherwise fall back to `address`
- **`fetch_stations()` returns `(stations, data_timestamp)`** — always unpack both; `data_timestamp` is passed to `detect_stale_prices` for logging
- **`filter_by_autonomy()` default buffer:** `max(range_km * 0.10, 15.0)` km — only override if `buffer_km` is explicitly passed by the client
- **`build_recommendation()` excludes `float('inf')` stations** — `best_station` and `worst_station` are `None` when no valid-price stations exist; callers must handle `None`
- **`rank_routes()` mutates in-place** — adds `rank` field (1 = highest `savings_per_litre`); returns the same list for chaining
- **`detect_stale_prices()` density-adaptive radii:** `[5, 10, 20, 50]` km — picks the smallest radius that yields ≥5 neighbors; stations with <5 neighbors within 50 km bypass the filter entirely
- **Corroboration bypass:** If ≥2 stations within 5 km have price within `ANOMALY_THRESHOLD_CAD` (0.05 CAD) of the flagged station, the station is NOT filtered — the price is considered real
- **Exemption matching is case-insensitive substring** against station `name` — e.g., exemption `"Costco"` matches `"Costco Laval"`
- **`haversine()` argument order is `(lat1, lng1, lat2, lng2)`** — not `(lng, lat)`; incorrect order produces wrong distances without raising an error
- **`distance_along_route()` returns cumulative path distance**, not straight-line distance from origin — used for `distance_from_origin_km` on each station
- **`find_stations_in_corridor()` adds `distance_from_route_km`** to each returned station dict (mutates a copy, not the original)
- **User-Agent header required** on GeoJSON fetch — requests without a browser-like UA may be blocked (defined as `_HEADERS` constant in `pricing.py`)

### ADK Agent Rules

- **Model:** `gemini-2.5-flash-lite` — do not change without updating `agent/agent.py`
- **Tool functions are dispatch stubs:** `submit_trip`, `add_waypoint`, `filter_stations_by_area`, `clear_filter` all return `{"ok": True}` — the actual dispatch happens in the frontend JS after receiving the `action` field from `/api/chat`
- **`ALLOWED_ACTIONS` whitelist in `routes.py`:** Any `functionCall` name not in `{"submit_trip", "add_waypoint", "filter_stations_by_area", "clear_filter", "chat_only"}` is silently downgraded to `"chat_only"` — keep this set in sync with tool function names in `agent.py`
- **ADK response normalization (`_normalize_adk_response`):** Handles both `{"events": [...]}` and bare `[...]` list responses — always extract `functionCall` and `text` parts from `event.content.parts`
- **Session creation is best-effort:** `POST /apps/agent/users/local_user/sessions/{id}` failures are silently swallowed — the `/run` call handles missing sessions
- **ADK unavailability is non-fatal:** `ConnectionError`/`Timeout` on `/run` returns 502 with a user-friendly message (not a 500) — the frontend falls back to the trip form
- **Agent system prompt is bilingual:** Responds in the user's language (French or English) — never hardcode a language in the prompt
- **Do not add a fifth tool** without also adding it to `ALLOWED_ACTIONS` in `routes.py` and the frontend action dispatcher

### Critical Don't-Miss Rules

- **`worst_station` uses post-filter stations:** `worst_station` is derived from the `reachable` list (after anomaly filter) — a stale high price must never appear as `worst_station`
- **`is_best` flag is identity-based:** Set with `s is best_station` (object identity), not value equality — do not replace station dicts between `build_recommendation()` and the `is_best` assignment loop
- **`float('inf')` → `None` conversion is in the response loop:** It happens per-station in `routes.py` just before `jsonify` — do not convert earlier in the pipeline or `build_recommendation` will break
- **Google Maps `status` field:** Only `"OK"` and `"ZERO_RESULTS"` are acceptable non-error statuses — all others return 502; an absent/empty `status` is also treated as OK (some responses omit it)
- **`waypoints` join format:** Google Maps Directions API expects `"|".join(waypoints)` as a pipe-separated string in the `params` dict — not a list
- **Stale price log format is load-bearing:** The log line in `detect_stale_prices` includes `name`, `price`, `median`, `neighbors`, `radius`, and `data_timestamp` — preserve this format for observability
- **`stations.yaml` `anomaly_filter_exemptions` is a list** — but the code defensively wraps a non-list value in a list; preserve this guard when reading the config
- **No OOP in `api/` modules:** All functions are module-level; no classes. `gaz_saver.py` is also class-free
- **French content everywhere:** Station names, addresses, and user-facing messages may contain `é è ê à ù ç` — never strip or normalize; always `encoding="utf-8"`
- **`gaz_saver.py` is a standalone CLI** — it is NOT imported by the Flask app; changes to it do not affect the web application

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Update this file if new patterns emerge

**For Humans:**

- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review periodically for outdated rules
- Remove rules that become obvious over time

Last Updated: 2026-06-15

