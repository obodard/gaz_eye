# 🏗️ gaz_eye — Architecture Review & Enhancement Recommendations

**Reviewer:** Winston (System Architect)
**Date:** 2026-05-31
**Scope:** Full-stack review (Flask backend, vanilla JS SPA, ADK chat agent, orphaned CLI)
**Tone:** Trade-offs over verdicts. Pragmatic, not aspirational.

---

## TL;DR

gaz_eye is a **soundly built MVP**. Backend layering (geo / pricing / routes) is genuinely good — pure functions where it counts, low coupling, sensible error codes. The ADK chat agent is correctly decoupled as a microservice. The bones are right.

The pressure points are **operational** (no caching, every request hits two upstreams), **frontend modularity** (`app.js` is becoming a god module, `map.js` lives on globals), and a few **conceptual leaks** that will compound: ADK tools duplicate REST handlers, the "context update" silent POST is a smell, and `gaz_saver.py` is dead weight that duplicates `pricing.py`.

On the headline question — *should mapping adopt the same ADK pattern as chat?* **No, and the question itself conflates two orthogonal patterns.** Detail in §4.

---

## 1. What's Working

| Strength | Evidence |
|---|---|
| Backend layering | [api/geo.py](api/geo.py) is pure & side-effect free; [api/pricing.py](api/pricing.py) owns data & heuristics; [api/routes.py](api/routes.py) only orchestrates. |
| Graceful degradation | Anomaly filter exceptions are caught and logged, never block the request ([api/routes.py](api/routes.py)). ADK unavailability returns 502 with a fallback message, doesn't crash. |
| Config-driven kill switch | `anomaly_filter_enabled` and `anomaly_filter_exemptions` in [stations.yaml](stations.yaml) let ops disable bad heuristics without a redeploy. Underrated win. |
| Secrets hygiene | Google Maps key is masked in error strings before responding. |
| XSS discipline | Frontend uses `textContent` and an explicit `escapeHtml` helper consistently. |
| Agent decoupling | `routes.py` calls the ADK service over HTTP — it does **not** import `agent.agent`. The agent could be rewritten in another language tomorrow. |
| Density-adaptive anomaly detector | [api/pricing.py](api/pricing.py) `detect_stale_prices` — adaptive radii + corroboration bypass is genuinely thoughtful work. |

---

## 2. Consistency & Modularity Findings

### 2.1 Backend

| Finding | Severity | Where |
|---|---|---|
| `geo.find_stations_in_corridor` mutates input stations in place (adds `distance_from_route_km`). Callers must know. | Low | [api/geo.py](api/geo.py) |
| `pricing.rank_routes` mutates inputs in place too — same pattern but the rest of `pricing.py` returns new objects. Inconsistent. | Low | [api/pricing.py](api/pricing.py) |
| `_CONFIG_PATH` is a module-level constant in routes.py pointing at the YAML. Mixes "I orchestrate HTTP" with "I know about disk layout." | Low | [api/routes.py](api/routes.py) |
| `float('inf')` sentinel for missing prices is clever but spreads "magic value" semantics across modules. Frontend uses `isFinite()` to mirror it. Two patterns, same concept. | Low | [api/pricing.py](api/pricing.py), [static/js/app.js](static/js/app.js) |
| No request/response schema validation (no Pydantic, no JSON schema). Contracts live in code only. | Medium | API boundary |
| YAML is re-read from disk on every `/api/plan` call. No mtime check, no cache. | Low | [api/routes.py](api/routes.py) |

### 2.2 Frontend

| Finding | Severity | Where |
|---|---|---|
| `app.js` (~620 LOC) is doing form handling + card rendering + settings drawer + error banner + reachability banner + timestamp + skeleton + low-range indicator. God module forming. | Medium | [static/js/app.js](static/js/app.js) |
| `map.js` keeps `map`, `polylines`, `markers`, `infoWindow` as module-level mutable globals. Re-init or a second map instance would explode. | Medium | [static/js/map.js](static/js/map.js) |
| `chat.js` imports `filterMarkers` / `restoreMarkers` directly from `map.js`. Other interactions go through CustomEvents. Two conventions for the same problem. | Medium | [static/js/chat.js](static/js/chat.js), [static/js/map.js](static/js/map.js) |
| Backend error `message` is intentionally dropped on the frontend (`_message` argument). Safe by default — but you lose diagnostic value in dev. | Low | [static/js/app.js](static/js/app.js) |
| No type system at all on the frontend, no JSDoc on the contract objects (`route`, `station`, `action` payload). Contracts drift silently. | Medium | All `static/js/*.js` |

### 2.3 Cross-cutting

| Finding | Severity |
|---|---|
| **No caching layer.** Every `/api/plan` = 1 Régie Essence fetch (~all of Quebec) + 1 Google Maps call + 1 disk YAML read. Régie data changes minutes-to-hours, not seconds. | **High** |
| **Duplicated GeoJSON fetch & price parsing** between [gaz_saver.py](gaz_saver.py) and [api/pricing.py](api/pricing.py). | Medium |
| **ADK_SERVICE_URL hardcoded** to `http://localhost:5001` in routes.py. Will bite the first deploy. | Medium |
| Logging is inconsistent — Python uses `logging`, JS has none. No request IDs to correlate frontend errors with backend logs. | Low |
| No HTTP cache headers on `/api/plan` (it's a POST anyway, but worth deciding). Static assets served via Flask, no CDN posture. | Low |

---

## 3. Critical Issues (ordered)

1. **Cold cache on every request.** Two upstream calls per `/api/plan`. Single-user dev hides this. First production traffic spike won't.
2. **`gaz_saver.py` is orphaned legacy code that duplicates `pricing.py`.** Either delete it, or extract a shared `regie_essence_client.py` and have both use it. Right now any fix to GeoJSON handling has to be made twice.
3. **`ADK_SERVICE_URL` hardcoded.** Move to env var, default to localhost.
4. **`app.js` god-module risk.** Split before it hits 1000 LOC and nobody dares touch it.
5. **`map.js` module globals.** Wrap in a `MapController` factory so state is owned and disposable.
6. **No schema validation on API boundary.** A typo in `submit_trip` params from the LLM could silently misfill the form.

---

## 4. The Big Question: Should Mapping Use an ADK Pattern Like Chat?

This is the most interesting question in the review, and the honest answer requires unpacking it. The "ADK pattern" actually bundles **two independent architectural decisions**:

> **Pattern A — LLM-as-reasoner:** Use a language model to interpret ambiguous input and pick a structured action.
>
> **Pattern B — Capability-as-microservice:** Run the capability in its own process, talk to it over HTTP, with a typed contract.

The chat feature uses both. They are not the same decision and they should be evaluated separately.

### 4.1 Pattern A (LLM reasoning) for mapping?

**Verdict: No, with one nuance.**

Mapping is **deterministic input → deterministic output**. Given an origin, destination, and corridor, the polyline decode and the corridor station filter have exactly one correct answer. Putting an LLM in that path would:

- Add 500–2000 ms of latency.
- Introduce non-determinism into a function that must be reproducible (savings calculations).
- Cost money on every plan request.
- Be impossible to unit test the way `find_stations_in_corridor` is today.

This is **boring technology done right**. Don't break it.

**The nuance:** there *are* reasoning-shaped problems lurking in the domain that an agent could legitimately own:

- **Smart route selection** — "balance savings vs. drive time vs. detour risk vs. station reliability." Today the user gets routes ranked by `savings_per_litre` only. A reasoning layer that explains *why* a route ranks where it does (and lets the user nudge weights conversationally) is plausibly valuable.
- **Anomaly explanation** — instead of silently hiding stale prices, a "Why was this station hidden?" tool the chat agent can call.
- **Trip post-mortems** — "You actually saved $X vs. nearest station; here's why route 2 would've been better."

In other words: **mapping shouldn't *be* an agent, but it should *expose tools* the agent can use.** Which leads us to Pattern B.

### 4.2 Pattern B (capability as microservice) for mapping?

**Verdict: Not yet, but the seams are worth knowing.**

The ADK service split is justified because:
- ADK has its own runtime (`google.adk` server, session storage).
- It calls out to Gemini, which has its own latency / failure profile.
- It needs to scale orthogonally to Flask (long-lived sessions vs. stateless plans).

None of those apply to pricing or geo today. They are pure-Python, fast, stateless, and a Flask process can handle them inline. Splitting them now would buy:
- A network hop per call (+5–20 ms)
- A second deployment target
- Cross-process serialization

…and would solve no current problem. **Premature service decomposition is just distributed coupling.**

**When the split *would* make sense:**
- `pricing` grows a cache backed by Redis and a periodic refresh job → that refresh job wants its own deployment, not Flask cron.
- The anomaly detector gets replaced by a real ML model with a heavyweight numpy/sklearn footprint → split it so Flask boot stays light.
- Multiple consumers (mobile app, a partner integration) need pricing without going through `/api/plan`.

Until one of those is true: keep them as Python modules. The current layering already gives you the *option* to extract them later — that's the win.

### 4.3 What the chat → mapping integration is actually missing

The real architectural smell isn't "mapping doesn't use ADK." It's that **chat and mapping share concepts without sharing contracts.**

Today the agent's tools (`submit_trip`, `add_waypoint`, `filter_stations_by_area`, `clear_filter`) are **stub functions returning `{"ok": True}`** ([agent/agent.py](agent/agent.py)). The real work is done client-side in [static/js/chat.js](static/js/chat.js)'s `dispatchAction()`, which manually parses the action and pokes form fields / calls map functions.

That means the tool definitions exist in **three places**:
1. Python stubs in `agent/agent.py` (for ADK schema introspection)
2. Whitelist `ALLOWED_ACTIONS` in `api/routes.py`
3. Switch statement in `static/js/chat.js`

Drift is inevitable. The fix isn't "mapping should be an agent." It's: **the tools the agent can call should be the same actions the frontend exposes, defined once.**

### 4.4 The "silent context update" is a code smell

When a trip is submitted, the frontend silently POSTs to `/api/chat` with `is_context_update=true` carrying the trip params, expecting a 204. This force-feeds the agent context the user never wrote.

A cleaner pattern: **the agent should have a `get_current_trip()` tool** that pulls from a session store when it needs context, instead of being notified out-of-band. That keeps the conversation log honest and makes the agent state-aware rather than push-fed.

---

## 5. Out-of-the-Box Recommendations

Ranked by leverage-per-effort, not by glamour.

### Tier 1 — Do these soon

1. **Single source of truth for agent actions.** Define each action as a Python dataclass/Pydantic model. Generate the ADK tool stub, the routes.py validator, and a JSON schema the frontend imports. Kills the three-place duplication in §4.3.
2. **Cache Régie Essence at the module level with TTL.** Even a 5-minute in-process cache eliminates the duplicate-fetch storm when a user adjusts settings and re-plans. Twenty lines of code.
3. **Cache YAML config with mtime check.** Re-read only if the file changed. Trivial.
4. **Delete or merge `gaz_saver.py`.** Extract `regie_essence_client.py` if you keep the CLI; otherwise delete. The duplication is a footgun.
5. **`MapController` class wrapping map.js globals.** No framework needed, just `function createMapController() { ... return { renderRoutes, renderMarkers, filterMarkers, ... } }`. Disposable, testable, two-map-ready.
6. **Env-var-driven `ADK_SERVICE_URL`.** `os.environ.get("ADK_SERVICE_URL", "http://localhost:5001")`. One-line ops unblock.

### Tier 2 — Plan for these

7. **Split `app.js`** into `form.js`, `cards.js`, `settings.js`, leave `app.js` as a thin bootstrap. Pre-empts the god-module trajectory.
8. **JSDoc the contract objects** (`Route`, `Station`, `AgentAction`). Free intellisense, free drift detection in editors that respect it.
9. **Pydantic models on `/api/plan` and `/api/chat`.** You already document the contracts in comments — make them executable.
10. **Replace the "silent context update" with a tool call.** Server keeps trip state per `session_id`; agent calls `get_current_trip()` when needed. Aligns with how the ADK SDK is designed.
11. **Server-Sent Events on `/api/chat`.** ADK responses can stream. Today the UI shows a typing indicator and waits 3–10s. SSE makes the assistant feel alive for free.
12. **Request IDs end-to-end.** UUID generated client-side, sent in `X-Request-Id`, logged on the backend. Without this, debugging a user-reported "it failed" requires guessing the timestamp.

### Tier 3 — Bigger bets, only if the problem appears

13. **Shareable trip URLs.** Push form state + selected route into the URL via History API. Free virality, free deep linking, free "send me your route" UX. Tiny code change, large UX dividend.
14. **Progressive `/api/plan` response.** Stream the route shapes first, then stations as they're scored. Today the user sees a spinner for the slowest call (Régie Essence). SSE or HTTP/2 push.
15. **Replace the in-process anomaly heuristic with an actual time-series view.** Today "stale" is inferred from spatial median deviation. If you start persisting price history (which you'll want anyway for retrospection), staleness becomes a direct measurement, not a guess. This is where a real ML model — and Pattern B microservice split — would finally earn its keep.
16. **Edge-cached Régie data.** A Cloudflare Worker pulling the GeoJSON every 5 minutes and serving from KV would take Régie Essence off your critical path entirely.
17. **TypeScript on the frontend.** Not urgent. But the cost grows linearly with JS LOC, and you're at 1290.
18. **Agent observability.** Log every tool call, params, and outcome. Today the agent is a black box once it answers — when a user says "it filled the wrong destination," you have no trace.

---

## 6. Summary Scorecard

| Dimension | Grade | Notes |
|---|---|---|
| Backend modularity | A− | Clean layers; minor leaky mutations |
| Frontend modularity | C+ | `app.js` god-module risk, `map.js` globals |
| Coupling | B | Chat ↔ map is the worst offender |
| Consistency | B− | Two patterns for missing prices, two patterns for chat↔map comms, error-handling style varies |
| Operational readiness | C | No caching, no request IDs, hardcoded service URL |
| Security posture | B+ | XSS guards, secret masking; no schema validation |
| Testability | B | Backend pure functions excellent; frontend has no seams |
| Conceptual integrity (agent ↔ app) | C | Tool definitions duplicated in 3 places; "context update" is a smell |

---

## 7. The One-Sentence Recommendation

**Don't make mapping an agent — make the agent's tools and the frontend's actions the same contract, cache the upstreams, and break up `app.js` before it breaks you.**

— Winston
