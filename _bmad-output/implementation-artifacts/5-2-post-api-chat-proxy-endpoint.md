---
baseline_commit: 83801f4f9d0767139379dfe72f7e3b441da37526
---

# Story 5.2: POST /api/chat Proxy Endpoint

Status: review

## Story

As a developer,
I want a `POST /api/chat` endpoint in the Flask Blueprint that proxies user messages to the ADK agent service and returns a normalized `{action, params, message}` JSON response,
so that the frontend has a single, stable contract for all chat interactions regardless of ADK's internal event format.

## Acceptance Criteria

**AC1:** Given `api/routes.py` is inspected after this story, when the Blueprint routes are read, then `POST /api/chat` is registered on the Blueprint — zero chat-related code lives in `app.py`. The handler is a function named `chat_with_agent()` (or similar, `snake_case` verb-prefixed).

**AC2:** Given a `POST /api/chat` request with body `{"message": "Montréal to Duhamel, 180 km range", "session_id": "abc-123", "is_context_update": false}`, when the endpoint is called with the ADK service running, then Flask proxies to `http://localhost:5001/run` using `requests.post` with `timeout=10`. The ADK request body is:
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

**AC3:** Given the ADK service responds with an events list containing a `functionCall` part and a `text` part, when Flask normalizes the response, then it returns HTTP 200 with body:
```json
{
  "action": "submit_trip",
  "params": { "origin": "Montréal", "destination": "Duhamel", "range_km": 180, "waypoints": [] },
  "message": "Planning Montréal → Duhamel with 180 km range — loading routes."
}
```
The first `functionCall` part in the events list is used for `action` + `params`. The last `text` part in the events list is used for `message`.

**AC4:** Given the ADK service responds with only a `text` part and no `functionCall`, when Flask normalizes the response, then it returns HTTP 200 with body `{"action": "chat_only", "params": {}, "message": "<assistant text>"}`.

**AC5:** Given the `action` value from normalization, when the response is returned, then `action` is one of: `"submit_trip"`, `"add_waypoint"`, `"filter_stations_by_area"`, `"clear_filter"`, `"chat_only"` — never an arbitrary string.

**AC6:** Given the ADK service is unreachable or the 10-second timeout is exceeded, when `POST /api/chat` is called, then it returns HTTP 502 with body `{"error": "adk_agent", "message": "Assistant unavailable — use the form to plan your trip."}`. The form-based `/api/plan` workflow continues to function normally — no shared state between the two endpoints.

**AC7:** Given `GEMINI_API_KEY` from the environment, when `api/routes.py` is inspected, then `GEMINI_API_KEY` does not appear anywhere in the file — Flask never reads, forwards, or logs it.

**AC8:** Given a `POST /api/chat` request with `is_context_update: true`, when the handler processes it, then it proxies the message to ADK and returns HTTP 204 with no response body. This branch executes regardless of ADK's response content — the 204 is unconditional once ADK acknowledges the call.

## Tasks / Subtasks

- [x] Task 1: Add `POST /api/chat` route handler to `api/routes.py` (AC1, AC2)
  - [x] Add `ADK_SERVICE_URL = "http://localhost:5001"` constant at module level
  - [x] Create `chat_with_agent()` handler function registered as `@bp.route("/api/chat", methods=["POST"])`
  - [x] Extract `message`, `session_id`, and `is_context_update` from request body
  - [x] Build ADK request payload with `app_name`, `user_id`, `session_id`, `new_message`
  - [x] Proxy to `{ADK_SERVICE_URL}/run` with `requests.post(timeout=10)`

- [x] Task 2: Implement context update branch (AC8)
  - [x] Check `is_context_update` flag in request body
  - [x] If true, proxy to ADK and return HTTP 204 (no body), regardless of ADK response
  - [x] Catch ADK connection errors on context update — still return 204 (fire-and-forget from Flask perspective)

- [x] Task 3: Implement ADK response normalization (AC3, AC4, AC5)
  - [x] Parse ADK events list from response JSON
  - [x] Extract first `functionCall` part → `action` (function name) + `params` (function args)
  - [x] Extract last `text` part → `message`
  - [x] If no `functionCall` found, set `action = "chat_only"`, `params = {}`
  - [x] Validate `action` is one of the 5 allowed values; fallback to `"chat_only"` if unknown

- [x] Task 4: Implement error handling (AC6, AC7)
  - [x] Catch `requests.ConnectionError`, `requests.Timeout` → return HTTP 502
  - [x] Return `{"error": "adk_agent", "message": "Assistant unavailable — use the form to plan your trip."}`
  - [x] Ensure `GEMINI_API_KEY` never appears in any log statement, error message, or response

- [x] Task 5: Add tests in `tests/test_routes.py` for `/api/chat` (AC1–AC8)
  - [x] Test successful proxy with functionCall → normalized {action, params, message}
  - [x] Test text-only response → action "chat_only"
  - [x] Test ADK timeout → HTTP 502 with correct error body
  - [x] Test ADK connection refused → HTTP 502
  - [x] Test is_context_update=true → HTTP 204
  - [x] Test unknown action name → fallback to "chat_only"
  - [x] Verify all existing `/api/plan` tests still pass

## Dev Notes

### ADK API Server Response Format

The ADK `POST /run` endpoint returns a JSON body with this structure (ADK 2.x):
```json
{
  "result": "...",
  "events": [
    {
      "author": "chekov_assistant",
      "content": {
        "parts": [
          { "functionCall": { "name": "submit_trip", "args": { "origin": "Montréal", "destination": "Duhamel", "range_km": 180 } } }
        ]
      }
    },
    {
      "author": "chekov_assistant",
      "content": {
        "parts": [
          { "text": "Planning Montréal → Duhamel with 180 km range — loading routes." }
        ]
      }
    }
  ]
}
```

The normalization logic must:
1. Iterate through `events` list
2. For each event, iterate through `content.parts`
3. Find the FIRST part with a `functionCall` key → extract `name` as `action`, `args` as `params`
4. Find the LAST part with a `text` key → extract as `message`
5. If no `functionCall` is found, set `action = "chat_only"`, `params = {}`

### Existing Code in `api/routes.py` — Current State

The file already has:
- `import requests` (used for Google Maps API calls)
- `bp = Blueprint("api", __name__)` 
- `logger = logging.getLogger("chekov.routes")`
- Routes: `GET /` (serve_index) and `POST /api/plan` (plan)

The new `/api/chat` route should be added AFTER the existing `/api/plan` route.

### Allowed Action Values

Only these 5 action strings are valid:
- `"submit_trip"` — maps to tool function name
- `"add_waypoint"` — maps to tool function name
- `"filter_stations_by_area"` — maps to tool function name
- `"clear_filter"` — maps to tool function name
- `"chat_only"` — no tool was called, text-only response

Any other action name from ADK should be normalized to `"chat_only"` with the original message preserved.

### Files to Modify

| File | Change |
|------|--------|
| `api/routes.py` | **UPDATE**: add `POST /api/chat` route handler + ADK proxy + normalization |
| `tests/test_routes.py` | **UPDATE**: add tests for `/api/chat` endpoint |

### Existing Code — DO NOT Modify

- `app.py` — zero chat-related code
- `agent/` — created in Story 5.1, not imported here
- `static/js/` — frontend changes are in Stories 5.4 and 5.5
- The existing `POST /api/plan` handler — must remain unchanged

### Previous Story Intelligence (5.1)

Story 5.1 creates the `agent/` package. This story does NOT import from `agent/` — Flask proxies to the ADK service via HTTP, not via Python imports. The separation is intentional: Flask never touches `google.adk` or `GEMINI_API_KEY`.

### Testing Standards

- All tests in `tests/test_routes.py`
- Mock `requests.post` for ADK service calls (never hit the real ADK service)
- Existing tests mock `requests.get` for Google Maps — ensure no interference
- Test the normalization logic with various ADK response shapes
- Flask test client via `app.test_client()` pattern already established in existing tests

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 5, Story 5.2]
- [Source: _bmad-output/planning-artifacts/architecture.md#Chat proxy, ADK integration]
- [Source: api/routes.py — existing Blueprint structure]
- [Source: tests/test_routes.py — existing test patterns]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None

### Completion Notes List

- Added `ADK_SERVICE_URL` and `ALLOWED_ACTIONS` constants to `api/routes.py`
- Implemented `_normalize_adk_response()` helper to extract action/params/message from ADK events
- Implemented `chat_with_agent()` route handler with proxy, normalization, context update (204), and error handling (502)
- GEMINI_API_KEY never appears in Flask code (AC7)
- Added 8 tests covering all acceptance criteria
- Full suite 118 tests pass with no regressions

### File List

- `api/routes.py` — MODIFIED
- `tests/test_routes.py` — MODIFIED

### Change Log

- 2026-05-31: Story 5.2 implemented — POST /api/chat proxy endpoint with ADK normalization and error handling
