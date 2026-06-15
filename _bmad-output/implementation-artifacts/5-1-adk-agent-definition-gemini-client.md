---
baseline_commit: 83801f4f9d0767139379dfe72f7e3b441da37526
---

# Story 5.1: ADK Agent Definition & Gemini Client

Status: review

## Story

As a developer,
I want the Google ADK agent package defined with the four gaz_eye tools and the Gemini 2.0 Flash model configured,
so that the ADK service process can be started and will correctly classify intent and extract structured parameters from natural-language trip messages.

## Acceptance Criteria

**AC1:** Given the repository after this story, when I inspect the project structure, then `agent/__init__.py` exists and exports `root_agent` (the ADK `Agent` instance), and `agent/agent.py` exists and defines: `SYSTEM_INSTRUCTION` (string constant), four tool functions (`submit_trip`, `add_waypoint`, `filter_stations_by_area`, `clear_filter`), and `root_agent = Agent(name="gaz_eye_assistant", model="gemini-2.0-flash", instruction=SYSTEM_INSTRUCTION, tools=[...])`. `requirements.txt` includes `google-adk>=1.0`.

**AC2:** Given `agent/agent.py` is inspected, when the four tool functions are read, then:
- `submit_trip(origin, destination, range_km=None, waypoints=None)` accepts the four trip parameters and returns `{"ok": True}`
- `add_waypoint(waypoint)` accepts one waypoint string and returns `{"ok": True}`
- `filter_stations_by_area(area_name, lat, lng)` accepts area name and coordinates and returns `{"ok": True}`
- `clear_filter()` accepts no arguments and returns `{"ok": True}`
- All four return `{"ok": True}` — actual action dispatch is the Flask proxy's responsibility, not the tool's

**AC3:** Given `SYSTEM_INSTRUCTION` is read, when its content is inspected, then it includes all five behavioral rules:
1. Always call a tool when the user's intent clearly matches one of the four actions
2. If a required field is missing (origin or destination for `submit_trip`), ask one clarifying question — never call `submit_trip` with placeholder or fabricated values
3. Respond in the same language the user writes in (French or English)
4. After calling a tool, confirm the action in 1–2 sentences maximum
5. Do not invent station names, prices, or route details — the agent has no access to live data

**AC4:** Given `.env.example` is opened, when the file is read, then it contains the line `GEMINI_API_KEY=` alongside the existing `GOOGLE_MAPS_API_KEY=`.

**AC5:** Given `app.py` and `api/routes.py` are inspected, when they are read in full, then neither file imports from `google.adk`, `google.generativeai`, `agent`, nor reads `GEMINI_API_KEY` from the environment. `GEMINI_API_KEY` does not appear in any Flask source file — it is the ADK process's exclusive concern.

## Tasks / Subtasks

- [x] Task 1: Create `agent/` package directory (AC1)
  - [x] Create `agent/__init__.py` that imports and re-exports `root_agent` from `agent.agent`
  - [x] Create `agent/agent.py` with `SYSTEM_INSTRUCTION`, 4 tool functions, and `root_agent` Agent definition

- [x] Task 2: Define the four tool functions in `agent/agent.py` (AC2)
  - [x] `submit_trip(origin: str, destination: str, range_km: float | None = None, waypoints: list[str] | None = None) -> dict`
  - [x] `add_waypoint(waypoint: str) -> dict`
  - [x] `filter_stations_by_area(area_name: str, lat: float, lng: float) -> dict`
  - [x] `clear_filter() -> dict`

- [x] Task 3: Write `SYSTEM_INSTRUCTION` with the 5 behavioral rules (AC3)

- [x] Task 4: Update `.env.example` with `GEMINI_API_KEY=` (AC4)

- [x] Task 5: Add `google-adk>=1.0` to `requirements.txt` (AC1)

- [x] Task 6: Verify no ADK/Gemini imports in Flask files (AC5)

- [x] Task 7: Add unit tests for tool functions in `tests/test_agent.py` (AC1, AC2)
  - [x] Test each tool function returns `{"ok": True}` with valid args
  - [x] Test `submit_trip` with optional params (range_km=None, waypoints=None)
  - [x] Test `root_agent` is an `Agent` instance with correct name and model

## Dev Notes

### Critical: ADK 2.0 Breaking Changes

The latest `google-adk` on PyPI is **2.1.0** (released 2026-05-22). ADK 2.0 has **breaking changes** from 1.x:
- Import path: `from google.adk import Agent` (NOT `from google.adk.agents import Agent`)
- **Python 3.11+ is required** — the project's `project-context.md` says Python 3.9+, but the ADK dependency forces 3.11+. Ensure the dev environment meets this requirement.
- The `instruction` parameter is used (not `system_instruction` or `instructions`)
- Tool functions are plain Python functions passed as a list — no decorator needed in ADK 2.x

### Agent Definition Pattern (ADK 2.x)

```python
from google.adk import Agent

root_agent = Agent(
    name="gaz_eye_assistant",
    model="gemini-2.0-flash",
    instruction=SYSTEM_INSTRUCTION,
    tools=[submit_trip, add_waypoint, filter_stations_by_area, clear_filter],
)
```

### Tool Function Pattern

Tool functions are plain functions with type-annotated parameters. ADK inspects the function signatures to build tool schemas for Gemini. Each function MUST have a docstring (Gemini uses it to understand when to call the tool).

```python
def submit_trip(origin: str, destination: str, range_km: float | None = None, waypoints: list[str] | None = None) -> dict:
    """Submit a trip planning request with origin, destination, optional range and waypoints."""
    return {"ok": True}
```

### ADK API Server

The ADK CLI command `adk api_server agent --port 5001` serves the agent on port 5001. The `/run` endpoint accepts POST requests. This is NOT implemented in this story — Story 5.3 handles `run.sh` updates.

### Files to Create/Modify

| File | Change |
|------|--------|
| `agent/__init__.py` | **NEW**: package init, exports `root_agent` |
| `agent/agent.py` | **NEW**: agent definition, tools, system instruction |
| `requirements.txt` | **UPDATE**: add `google-adk>=1.0` |
| `.env.example` | **UPDATE**: add `GEMINI_API_KEY=` |
| `tests/test_agent.py` | **NEW**: unit tests for tool functions and agent definition |

### Existing Code — DO NOT Modify

- `app.py` — must remain a pure Flask factory with zero ADK imports
- `api/routes.py` — must NOT import from `agent` or read `GEMINI_API_KEY` (Story 5.2 adds the proxy)
- `api/pricing.py`, `api/geo.py` — unrelated, no changes

### Project Structure Notes

The `agent/` directory sits at project root alongside `api/`, `static/`, `tests/`. This matches the architecture spec: "`agent/` package: `agent/__init__.py` (exports `root_agent`) and `agent/agent.py`".

### Testing Standards

- Use `pytest` as the test runner
- Place tests in `tests/test_agent.py`
- Tests should verify tool function return values and `root_agent` attributes (name, model)
- No mocking of Gemini API needed — tool functions are pure functions returning `{"ok": True}`
- Do NOT test ADK's internal behavior or Gemini API calls

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 5, Story 5.1]
- [Source: _bmad-output/planning-artifacts/architecture.md#Agent package structure]
- [Source: _bmad-output/project-context.md#Language-Specific Rules]
- [Source: PyPI google-adk 2.1.0 — Python 3.11+ required, `from google.adk import Agent`]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None

### Completion Notes List

- Created `agent/__init__.py` exporting `root_agent`
- Created `agent/agent.py` with SYSTEM_INSTRUCTION (5 behavioral rules), 4 tool functions, and Agent definition using ADK 2.x API (`from google.adk import Agent`)
- Updated `.env.example` with `GEMINI_API_KEY=`
- Added `google-adk>=1.0` to `requirements.txt`
- Verified no ADK/Gemini imports in Flask files (AC5)
- All 15 agent tests pass, full suite 110 tests pass with no regressions

### File List

- `agent/__init__.py` — NEW
- `agent/agent.py` — NEW
- `.env.example` — MODIFIED
- `requirements.txt` — MODIFIED
- `tests/test_agent.py` — NEW

### Change Log

- 2026-05-31: Story 5.1 implemented — ADK agent package with 4 tool functions, system instruction, and unit tests
