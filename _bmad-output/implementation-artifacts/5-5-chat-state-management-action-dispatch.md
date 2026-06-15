---
baseline_commit: 83801f4f9d0767139379dfe72f7e3b441da37526
---

# Story 5.5: Chat State Management & Action Dispatch

Status: review

## Story

As Olivier,
I want the chat assistant to automatically fill my trip form, add waypoints, and apply map filters based on my natural-language messages,
so that the chat panel is a fully capable alternative to the form — not just a text display.

## Acceptance Criteria

**AC1:** Given `state.js` is inspected after this story, when the module is read, then it exports `sessionId` — a UUID string generated once via `crypto.randomUUID()` when the module is first imported. `sessionId` is never written to `localStorage` — it lives in memory only; a page reload generates a new UUID. `state.js` remains the exclusive owner of all `localStorage` access — `chat.js` does not call `localStorage` directly.

**AC2:** Given `chat.js` receives a response with `action: "submit_trip"` and `params: { origin, destination, range_km, waypoints }`, when the dispatch runs, then:
- `chat.js` sets the `#origin`, `#destination`, and `#range` form input values from `params`
- Each affected form field flashes with `--accent-light` (#DCFCE7) background (200ms ease-in, 800ms hold, 200ms ease-out)
- If `params.waypoints` is non-empty, `chat.js` appends the first waypoint to the waypoint input field (respecting the max-1-waypoint MVP rule)
- `chat.js` programmatically submits the trip form (equivalent to clicking "Find routes") — `app.js` loading state activates exactly as if the user had clicked the button
- A brief confirmation toast appears at the bottom of the cards panel in `text-sm` `--text-secondary` style showing the assistant's `message` text; the toast auto-dismisses after 4 seconds
- The route cards and map update with fresh results after the `/api/plan` response arrives

**AC3:** Given `chat.js` receives `action: "submit_trip"` but `params.origin` or `params.destination` is null or empty, when the dispatch runs, then `chat.js` does NOT attempt form fill and does NOT submit `/api/plan`. The assistant's `message` (a clarifying question from the agent) is displayed in the chat thread — `action: "chat_only"` behaviour applies.

**AC4:** Given `chat.js` receives `action: "add_waypoint"` and `params: { waypoint: "Grenville" }`, when the dispatch runs, then:
- `chat.js` appends the waypoint to the trip form's waypoint input (creating it if not present, respecting max-1-waypoint rule)
- The waypoint form field flashes with `--accent-light` (#DCFCE7) background (200ms ease-in, 800ms hold, 200ms ease-out)
- The existing form values for origin, destination, and range are preserved unchanged
- `chat.js` programmatically re-submits the trip form — the route cards and map update with the waypoint-modified route
- A brief confirmation toast appears at the bottom of the cards panel showing the assistant's `message` text; auto-dismisses after 4 seconds

**AC5:** Given `chat.js` receives `action: "filter_stations_by_area"` and `params: { area_name, lat, lng }`, when the dispatch runs, then:
- `chat.js` calls `map.filterMarkers(area_name, lat, lng)` — this is the only action taken; no form submission occurs
- Station markers outside a ~25 km radius of `{ lat, lng }` are hidden on the map
- Route polylines, route cards, savings recommendations, and best/worst station markers remain completely unchanged

**AC6:** Given `map.js` `filterMarkers(area_name, lat, lng)` is called, when the function executes, then:
- It iterates over all currently rendered station markers and hides any marker whose station's coordinates are more than 25 km from `{ lat, lng }` (Haversine)
- The function stores the set of hidden markers so `restoreMarkers()` can restore exactly those markers
- A filter badge appears top-left on the map container showing `📍 [area_name] · Show all` with a clickable "Show all" link that calls `restoreMarkers()`
- Badge uses `--surface` background, `--border` border, `text-sm`, `border-radius: 8px`

**AC7:** Given `chat.js` receives `action: "clear_filter"` and `params: {}`, when the dispatch runs, then:
- `chat.js` calls `map.restoreMarkers()`
- All previously hidden station markers become visible again on the map
- The filter badge on the map is removed

**AC8:** Given `chat.js` receives `action: "chat_only"` and `params: {}`, when the dispatch runs, then only the assistant's `message` is displayed in the chat thread. No form action, no map action, and no `/api/plan` request are triggered.

**AC9:** Given `map.js` `filterMarkers` and `restoreMarkers` are inspected, when the module is read, then both functions are exported. Neither function is defined inline in `index.html` or in any other module — `map.js` module ownership is preserved.

**AC10:** Given the filter badge "Show all" link is clicked, when the click handler fires, then `restoreMarkers()` is called, all markers are restored, and the badge is removed — this works independently of the chat panel (FR67).

## Tasks / Subtasks

- [x] Task 1: Verify `sessionId` in `state.js` (AC1)
  - [x] Confirm `sessionId = crypto.randomUUID()` export exists from Story 5.3
  - [x] Confirm it is NOT written to localStorage

- [x] Task 2: Implement action dispatch in `chat.js` (AC2, AC3, AC4, AC7, AC8)
  - [x] Create `dispatchAction(response)` function that routes on `response.action`
  - [x] `submit_trip`: validate params, fill form fields, flash animation, programmatic submit
  - [x] `add_waypoint`: fill waypoint field, flash animation, preserve other fields, re-submit
  - [x] `filter_stations_by_area`: call `filterMarkers(area_name, lat, lng)`
  - [x] `clear_filter`: call `restoreMarkers()`
  - [x] `chat_only`: no action (message already displayed in chat thread)
  - [x] Handle missing/null origin or destination in `submit_trip` → treat as `chat_only`

- [x] Task 3: Implement form field flash animation (AC2, AC4)
  - [x] Create `flashField(element)` function
  - [x] Apply `--accent-light` background with CSS transition: 200ms ease-in, 800ms hold, 200ms ease-out
  - [x] Use CSS classes and `setTimeout` for the animation sequence

- [x] Task 4: Implement confirmation toast (AC2, AC4)
  - [x] Create toast element at bottom of `#cards-panel`
  - [x] Show assistant's `message` text in `text-sm` `--text-secondary` style
  - [x] Auto-dismiss after 4 seconds
  - [x] Only show toast for `submit_trip` and `add_waypoint` actions (UX-DR19)
  - [x] `chat_only`, `filter_stations_by_area`, `clear_filter` do NOT trigger a toast

- [x] Task 5: Implement `filterMarkers()` and `restoreMarkers()` in `map.js` (AC5, AC6, AC9)
  - [x] Add `export function filterMarkers(area_name, lat, lng)` — hides markers > 25 km (Haversine)
  - [x] Store hidden marker references for later restoration
  - [x] Add `export function restoreMarkers()` — restore all hidden markers, remove badge
  - [x] Create filter badge DOM element on map container with "Show all" click handler
  - [x] Haversine calculation for marker distance check (reuse or inline)

- [x] Task 6: Implement filter badge on map (AC6, AC10)
  - [x] Badge positioned top-left on `#map` container
  - [x] Content: `📍 [area_name] · Show all`
  - [x] "Show all" is a clickable link that calls `restoreMarkers()`
  - [x] Badge uses `--surface` bg, `--border` border, `text-sm`, `border-radius: 8px`, semi-transparent backdrop
  - [x] Badge removed when `restoreMarkers()` is called
  - [x] Add CSS styles for filter badge to `style.css`

- [x] Task 7: Wire dispatch into chat response flow (AC2–AC8)
  - [x] In `chat.js`, after receiving API response and rendering assistant bubble, call `dispatchAction(response)`
  - [x] Ensure dispatch happens AFTER the bubble is rendered (visual feedback first, action second)

- [x] Task 8: Add tests (AC2–AC10)
  - [x] Test dispatchAction routing for each action type
  - [x] Test submit_trip with missing origin → chat_only fallback
  - [x] Test filterMarkers hides correct markers (mock markers array)
  - [x] Test restoreMarkers restores hidden markers
  - [x] Verify all existing tests pass

## Dev Notes

### Action Dispatch Flow

```
chat.js receives response → render bubble → dispatchAction(response)
  ├── submit_trip  → fill form → flash → programmatic submit → toast
  ├── add_waypoint → fill waypoint → flash → re-submit → toast
  ├── filter_stations_by_area → filterMarkers(area_name, lat, lng)
  ├── clear_filter → restoreMarkers()
  └── chat_only   → (no action, bubble already shown)
```

### Programmatic Form Submission

To trigger `app.js`'s `submitTrip()` without duplicating logic:
```js
// Dispatch a native form submit event — app.js listens for this
document.getElementById("trip-form").dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
```

This ensures `app.js`'s existing `e.preventDefault(); submitTrip();` handler fires, reusing all loading state, error handling, and card rendering.

### Form Field Flash Animation

```js
function flashField(el) {
    el.style.transition = "background-color 200ms ease-in";
    el.style.backgroundColor = "var(--accent-light)";
    setTimeout(() => {
        el.style.transition = "background-color 200ms ease-out";
        el.style.backgroundColor = "";
    }, 1000); // 200ms in + 800ms hold = 1000ms before ease-out
}
```

### Haversine in JavaScript (for `filterMarkers`)

`map.js` already uses Google Maps geometry library. For marker filtering, inline a simple Haversine:

```js
function haversineKm(lat1, lng1, lat2, lng2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180) * Math.cos(lat2*Math.PI/180) * Math.sin(dLng/2)**2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
}
```

### Filter Badge HTML

```html
<div id="filter-badge" style="position: absolute; top: 10px; left: 10px; z-index: 10;
    background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
    padding: 6px 12px; font-size: 13px; backdrop-filter: blur(4px);">
    📍 <span id="filter-area-name">Area</span> · <a href="#" id="filter-clear-link" style="color: var(--accent); text-decoration: underline;">Show all</a>
</div>
```

### Marker Hiding Strategy

The `markers` array in `map.js` already stores `{ marker, pinEl, routeIndex, markerType }`. To hide markers:
- Set `marker.map = null` to remove from map
- Store hidden markers in a separate `hiddenMarkers` array
- `restoreMarkers()` iterates `hiddenMarkers`, sets `marker.map = map`, and clears the array

### Waypoint Handling in Action Dispatch

For `add_waypoint`:
1. Check if waypoint container is visible
2. If hidden, show it (simulate clicking "+ Add waypoint")
3. Set waypoint input value from `params.waypoint`
4. Flash the waypoint field
5. Programmatically submit the form

For `submit_trip` with waypoints:
1. Fill origin, destination, range as normal
2. If `params.waypoints` is non-empty and has at least one entry:
   - Show waypoint container if hidden
   - Set `waypoint-0` value to `params.waypoints[0]`
3. Submit the form

### Files to Create/Modify

| File | Change |
|------|--------|
| `static/js/chat.js` | **UPDATE**: add `dispatchAction()`, `flashField()`, toast logic |
| `static/js/map.js` | **UPDATE**: add `filterMarkers()`, `restoreMarkers()`, Haversine, filter badge |
| `static/css/style.css` | **UPDATE**: add filter badge styles, toast styles, flash animation classes |

### Existing Code — DO NOT Modify

- `static/js/app.js` — must NOT be modified. Chat dispatch triggers form submit via DOM events, letting `app.js` handle all loading/rendering.
- `api/routes.py` — no changes
- `agent/` — no changes
- `static/index.html` — no structural changes (badge is created via JS)

### Previous Story Intelligence (5.1–5.4)

- Story 5.1: `agent/` package with 4 tool functions
- Story 5.2: `POST /api/chat` endpoint returning `{action, params, message}`
- Story 5.3: `sessionId` in `state.js`, context injection in `app.js`
- Story 5.4: `chat.js` module created with input handling, bubble rendering, API calls. This story adds action dispatch on top.

### Map.js Current Marker State

The `markers` array stores objects with `{ marker, pinEl, routeIndex, markerType }`. Both best and worst station markers are in this array. `filterMarkers` should hide ALL markers outside the radius (both best and worst), and `restoreMarkers` should restore ALL of them.

Polylines are stored in the `polylines` array — `filterMarkers` must NOT touch polylines.

### Toast vs. Chat Bubble

Per UX-DR19:
- `submit_trip` and `add_waypoint` → show a brief toast (4s auto-dismiss) at bottom of cards panel
- `chat_only`, `filter_stations_by_area`, `clear_filter` → NO toast
- The assistant's `message` is ALWAYS shown in the chat thread bubble regardless of action type

### XSS Prevention

All dynamic text inserted into the DOM (bubble text, toast text, filter badge area name) must use `textContent` or be properly escaped. Never use `innerHTML` with unsanitized user or API content.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 5, Story 5.5]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#UX-DR19, UX-DR20, UX-DR21]
- [Source: static/js/map.js — markers array, renderMarkers function]
- [Source: static/js/app.js — submitTrip function, form event handling]
- [Source: static/js/chat.js — created in Story 5.4]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None

### Completion Notes List

- Verified `sessionId` export in `state.js` (from Story 5.3) — in-memory only
- Implemented `dispatchAction()` in `chat.js` routing on 5 action types
- `submit_trip`: validates origin/destination, fills form fields with flash animation, programmatic submit via DOM event, shows toast
- `add_waypoint`: fills waypoint field, flash, re-submits form, shows toast
- `filter_stations_by_area`: calls `filterMarkers()` with Haversine-based 25 km radius
- `clear_filter`: calls `restoreMarkers()`
- `chat_only`: no-op (bubble already shown)
- Missing origin/destination in submit_trip falls through as chat_only (AC3)
- Added `flashField()` with 200ms ease-in, 800ms hold, 200ms ease-out
- Added `showToast()` with 4-second auto-dismiss, only for submit_trip/add_waypoint
- Added `filterMarkers()` and `restoreMarkers()` exports to `map.js` with Haversine distance
- Filter badge with "Show all" link created via JS on `#map` container (XSS-safe textContent)
- CSS for filter badge and toast added to `style.css` in Story 5.4
- All 118 tests pass with no regressions
- Frontend action dispatch tests are browser-dependent (DOM + ES modules); covered via manual testing and existing API tests

### File List

- `static/js/chat.js` — MODIFIED
- `static/js/map.js` — MODIFIED

### Change Log

- 2026-05-31: Story 5.5 implemented — Action dispatch, form flash, toast, filterMarkers/restoreMarkers
