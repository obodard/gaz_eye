# Deferred Work Log

## Deferred from: code review of 1-1-flask-scaffold (2026-05-01)

- **No `SECRET_KEY` configured** — `create_app()` never sets `app.config['SECRET_KEY']`; sessions and CSRF tokens will fail when added. Set a secret from env before any session-dependent features land.

---

## Deferred from: code review of 1-2-pricing-module (2026-05-01)

- **`float('inf')` not JSON serializable** — stations with unavailable prices have `price_per_litre = float('inf')`; `json.dumps` raises `ValueError` on this value. Must be filtered or replaced (e.g., `None`) before the API response layer in story 2.3.

---

## Deferred from: code review of 1-3-autonomy-recommendations (2026-05-01)

- **`distance_from_origin_km` missing defaults to `0.0`** — stations without this key are treated as being at the origin (distance 0) and always pass `filter_by_autonomy`. The pipeline must guarantee this field is set by the geospatial engine (story 2.1) before calling the filter function.

---

## Deferred from: code review of epic 2 (2026-05-01)

- **Module-level `app = create_app()` breaks factory pattern** — `load_dotenv()` runs at import time; tests cannot configure the environment before app creation. Standard pattern: call `create_app()` explicitly at startup, not at module level.
- **Module-level logger handler setup** — both `api/pricing.py` and `app.py` configure `StreamHandler` at module level; can produce duplicate log output under WSGI reload. Library modules should not add handlers.
- **O(n×m) performance in `find_stations_in_corridor`** — for each of ~3,000 Quebec stations, every polyline point is visited; for long routes (hundreds of points) this is a bottleneck. Consider bounding-box pre-filter or spatial index.
- **`distance_along_route` snaps to nearest polyline vertex, not nearest segment point** — for stations near a long edge midpoint, the cumulative distance reported can differ materially from the true route distance. Acceptable for MVP but limits accuracy at scale.
- **Unpinned dependencies** — `requests`, `python-dotenv`, `pyyaml`, `colorama`, `polyline` have no version constraints; build is non-reproducible. Acceptable per current project convention but worth pinning before production.
- **`colorama` leftover in `requirements.txt`** — imported in `gaz_saver.py` but not in any `api/` or `app.py` file. Low priority to clean up.

---

## Deferred from: code review of epic 3 (2026-05-01)

- **`max_alternatives` parameter ignored by backend** — `app.js` sends `max_alternatives` in the request body but `api/routes.py` never reads or applies it. All routes from Google Maps are returned regardless. Epic 2.3 backend responsibility; not introduced in Epic 3.
- **Empty `data_timestamp` shows garbage in footer** — if Régie Essence GeoJSON lacks `metadata.generated_at`, `data_timestamp` is `""`, `new Date("")` is `Invalid Date`, and the footer shows "Updated Invalid Date at Invalid Date". Upstream API contract; add a guard when `data_timestamp` is empty. Low likelihood, cosmetic only.

---

## Deferred from: code review of 4-1-stale-price-detection-engine (2026-05-01)

- **Coordinate equality self-exclusion may drop co-located stations from neighbor pool** — `not (s["lat"] == station["lat"] and s["lng"] == station["lng"])` in `detect_stale_prices` excludes all stations at the same coordinates, not just the candidate. Spec-compliant (`by identity or by lat/lng equality`); co-located stations are rare in Quebec. Consider switching to `s is not station` if co-location edge cases are observed in production.
- **`price_per_litre=None` in station dict not guarded in `valid_pool` comprehension** — `s.get("price_per_litre", float("inf"))` returns `None` if key exists with `None` value; `None != float("inf")` is `True`, so the station enters `valid_pool` and causes `statistics.median()` to raise `TypeError`. Not reachable with current `fetch_stations()` which always sets float or `float('inf')`.
- **O(C×N×K) linear haversine scan without spatial indexing** — for ~50 corridor stations × ~3,000 Quebec stations × up to 4 radii ≈ 600,000 haversine calls per request. Acceptable per current benchmarking; revisit if corridor station count grows beyond ~50 or total dataset exceeds 5,000.
- **`test_all_stations_not_mutated` does not assert corridor_stations input dicts are unchanged** — shallow copy guarantee is already verified for `all_stations`; verifying `corridor_stations` input dicts separately adds marginal coverage but was not required by AC7.

---

## Deferred from: code review of 4-2-exemptions-killswitch-route-integration (2026-05-01)

- **YAML config re-read from disk on every `/api/plan` request** — intentional design per dev notes (enables kill-switch without restart). File is ~40 lines; disk I/O cost negligible vs upstream network calls. Revisit if profiling shows this as a hot path.

---

## Deferred from: code review of 4-3-bidirectional-anomaly-detection & 4-4-most-expensive-station-map-marker (2026-05-10)

- **Marker Array Lifecycle Management** — markers pushed to global array but cleanup relies on `clearRoutes()` being called consistently. If routes re-render partially without full cleanup, memory leak or stale references possible. Pre-existing pattern in map.js (not introduced in 4.3/4.4); refactor opportunity for future spike.

- **Hard-Coded Marker Type String "worst"** — marker type ("best" vs "worst") uses string literals; typo could break silently. Pre-existing pattern for best markers; could be refactored to constants in future. Low practical risk given tight coupling in same module.

- **Route Colour Array Finite (only 3 colours)** — FIXED in code review. Backend `api/routes.py` limits `/api/plan` response to 3 alternatives (Google Maps spec); no runtime issue. Added modulo bounds check `ROUTE_COLOURS[routeIndex % ROUTE_COLOURS.length]` for defensive robustness if spec changes.
- **`builtins.open` mock in `TestPlanAnomalyFilter` intercepts all `open()` calls in handler** — if `plan()` ever opens an additional file, tests will silently feed it YAML content. Acceptable for current single-file-open handler; tighten to `api.routes.open` or use `mock_open` on `_CONFIG_PATH` specifically when the handler grows.
