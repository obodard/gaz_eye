---
baseline_commit: 83801f4f9d0767139379dfe72f7e3b441da37526
---

# Story 5.3: Route Context Injection

Status: review

## Story

As a developer,
I want `run.sh` updated to launch the ADK service alongside Flask, and `app.js` to silently inject current trip parameters into the ADK session after each successful plan query,
so that follow-up chat messages like "add a stop through Grenville" resolve correctly against the current trip without the user repeating origin and destination.

## Acceptance Criteria

**AC1:** Given `run.sh` is opened after this story, when the file is read, then it starts the ADK agent service with `adk api_server agent --port 5001 &` before starting Flask. The ADK process PID is stored in a variable (e.g., `ADK_PID=$!`). A `trap "kill $ADK_PID 2>/dev/null" EXIT` statement ensures the ADK process is killed when the script exits (Ctrl-C or normal termination). Flask is started last with `flask --app app run --debug` (blocking call). The existing `.env` loading and `GOOGLE_MAPS_API_KEY` unset warning are preserved unchanged.

**AC2:** Given `app.js` is inspected, when it processes a successful `POST /api/plan` response, then immediately after `renderCards()` completes, it fires a silent `POST /api/chat` with:
```json
{
  "message": "[TRIP CONTEXT] origin=\"<origin>\", destination=\"<destination>\", range_km=<range>, waypoints=<json_array>",
  "session_id": "<current session id from state.sessionId>",
  "is_context_update": true
}
```
`app.js` does not await or handle the response body of this context update — it is fire-and-forget. An HTTP 204 or HTTP 502 on the context update does not affect the UI in any way.

**AC3:** Given the context message format, when `app.js` formats it, then the message contains **only** origin, destination, range_km, and waypoints — never full route results, station prices, polylines, or drive times (keeps prompt tokens minimal and avoids sending detailed data outside localhost).

**AC4:** Given a page reload, when a new session starts, then `state.js` generates a new `sessionId = crypto.randomUUID()` — the old session's context is lost, which is acceptable for a single-user local tool.

**AC5:** Given `api/routes.py` receives a `POST /api/chat` request with `is_context_update: true`, when the handler processes it, then it proxies the message to ADK and returns HTTP 204 with no response body. This branch was already implemented in Story 5.2 — this story only verifies it works end-to-end with the context injection from `app.js`.

## Tasks / Subtasks

- [x] Task 1: Update `run.sh` to launch ADK service alongside Flask (AC1)
  - [x] Add `adk api_server agent --port 5001 &` before Flask start
  - [x] Store ADK PID: `ADK_PID=$!`
  - [x] Add `trap "kill $ADK_PID 2>/dev/null" EXIT` for cleanup
  - [x] Keep Flask start as the final blocking command
  - [x] Preserve existing `.env` loading and `GOOGLE_MAPS_API_KEY` warning

- [x] Task 2: Add `sessionId` to `state.js` (AC4)
  - [x] Add `export const sessionId = crypto.randomUUID();` at module level
  - [x] Ensure it is NOT persisted to localStorage — in-memory only, regenerated on page reload

- [x] Task 3: Add context injection in `app.js` after successful `/api/plan` (AC2, AC3)
  - [x] Import `sessionId` from `state.js`
  - [x] After `renderCards(data.routes)` in `submitTrip()`, fire silent `POST /api/chat`
  - [x] Build context message with only origin, destination, range_km, waypoints
  - [x] Set `is_context_update: true` in the request body
  - [x] Use `fetch()` without awaiting (fire-and-forget) — `.catch(() => {})` to suppress errors

- [x] Task 4: Verify context update flow end-to-end (AC5)
  - [x] Confirm Story 5.2's `is_context_update` branch returns HTTP 204
  - [x] Add test in `tests/test_routes.py` verifying context update proxy + 204 response (if not already covered)

## Dev Notes

### `run.sh` — Current State and Required Changes

Current `run.sh`:
```bash
#!/usr/bin/env bash
set -e
source .venv/bin/activate
if [ -z "${GOOGLE_MAPS_API_KEY}" ]; then
    echo "⚠ WARNING: GOOGLE_MAPS_API_KEY is not set. Route planning will not work."
fi
export FLASK_APP=app.py
export FLASK_DEBUG=1
flask run --debug
```

After this story:
```bash
#!/usr/bin/env bash
set -e
source .venv/bin/activate
if [ -z "${GOOGLE_MAPS_API_KEY}" ]; then
    echo "⚠ WARNING: GOOGLE_MAPS_API_KEY is not set. Route planning will not work."
fi
export FLASK_APP=app.py
export FLASK_DEBUG=1

# Start ADK agent service in background
adk api_server agent --port 5001 &
ADK_PID=$!
trap "kill $ADK_PID 2>/dev/null" EXIT

flask --app app run --debug
```

**Key points:**
- `set -e` stays — if ADK fails to start, the script should not silently continue
- ADK is started BEFORE Flask (background process)
- `trap EXIT` ensures ADK is killed on any exit (Ctrl-C, error, normal exit)
- Flask command changed to `flask --app app run --debug` (explicit app specification)

### `state.js` — Adding `sessionId`

Current exports: `state`, `DEFAULT_SETTINGS`, `SETTINGS_KEY`, `loadSettings`, `saveSettings`, `setSelectedRoute`.

Add at module level (near the top, after constants):
```js
export const sessionId = crypto.randomUUID();
```

This is NOT written to localStorage. On page reload, a new UUID is generated and the old ADK session context is abandoned. This is acceptable for a single-user local tool.

### `app.js` — Context Injection Pattern

In the `submitTrip()` function, after `renderCards(data.routes)` and before `setSelectedRoute(0)`:

```js
// Silently inject trip context into ADK session (fire-and-forget)
fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
        message: `[TRIP CONTEXT] origin="${origin}", destination="${destination}", range_km=${rangeKm}, waypoints=${JSON.stringify(body.waypoints)}`,
        session_id: sessionId,
        is_context_update: true,
    }),
}).catch(() => {}); // Suppress errors — context injection is non-critical
```

**Critical:** Do NOT await this call. Do NOT handle the response. Any failure (ADK down, 502, timeout) is silently swallowed. The form-based workflow must never be affected by chat availability.

### Files to Modify

| File | Change |
|------|--------|
| `run.sh` | **UPDATE**: add ADK service launch + trap cleanup |
| `static/js/state.js` | **UPDATE**: add `sessionId` export |
| `static/js/app.js` | **UPDATE**: add context injection after successful plan |
| `tests/test_routes.py` | **UPDATE**: verify context update 204 (if not covered by Story 5.2) |

### Existing Code — DO NOT Modify

- `agent/` — created in Story 5.1, not touched here
- `api/routes.py` — the `is_context_update` branch was added in Story 5.2; do NOT modify it
- `static/js/map.js` — no changes
- `static/css/style.css` — no changes
- `static/index.html` — no changes

### Previous Story Intelligence (5.1, 5.2)

- Story 5.1 created the `agent/` package with `root_agent`
- Story 5.2 added `POST /api/chat` in `api/routes.py` with the `is_context_update: true` → 204 branch
- This story wires the frontend (`app.js`) to the backend (`/api/chat`) and updates the launch script (`run.sh`)

### Testing Considerations

- `run.sh` changes are script-level — tested manually by running the app
- `state.js` `sessionId` — verify it's a valid UUID format in browser console
- `app.js` context injection — test by observing ADK service logs showing the context message
- The `is_context_update` → 204 flow should already have a test from Story 5.2

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 5, Story 5.3]
- [Source: _bmad-output/planning-artifacts/architecture.md#Context injection protocol]
- [Source: run.sh — current state]
- [Source: static/js/state.js — current exports]
- [Source: static/js/app.js — submitTrip() function]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None

### Completion Notes List

- Updated `run.sh` to start ADK agent service before Flask with PID tracking and trap cleanup
- Added `sessionId = crypto.randomUUID()` export to `state.js` (in-memory only)
- Added fire-and-forget context injection in `app.js` after successful `/api/plan` response
- Context message includes only origin, destination, range_km, waypoints (minimal tokens, AC3)
- Context update 204 test already covered by Story 5.2
- Full suite 118 tests pass with no regressions

### File List

- `run.sh` — MODIFIED
- `static/js/state.js` — MODIFIED
- `static/js/app.js` — MODIFIED

### Change Log

- 2026-05-31: Story 5.3 implemented — ADK launch in run.sh, sessionId, and context injection
