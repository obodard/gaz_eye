# Story 3.5: Edge States, Error Handling & Responsive Layout

Status: done

## Story

As Olivier,
I want the app to handle low-range trips, unreachable-station routes, API failures, and mobile viewports gracefully,
So that I can rely on it in all scenarios — including a roadside low-fuel stop on a phone.

## Acceptance Criteria

**AC1:** Given I enter a range value ≤ 50 km, when the value is typed or changed, then the range input gains an amber border (`border-amber-400` or `border: 1.5px solid var(--warning)`) as a low-range indicator.

**AC2:** Given the API returns a route where `stations` is an empty array, when that route's card renders, then the card shows in a gray non-interactive state with message: "Nearest station is X km — Y km beyond your range" (using the nearest filtered station's distance and the shortfall); an inline amber banner appears above the cards: "N station(s) reachable · Z km buffer active" (positive framing).

**AC3:** Given all three routes have zero reachable stations, when cards render, then all three cards are in the gray no-stations state; the amber banner includes the additional suggestion: "Try increasing your range or widening the corridor in settings".

**AC4:** Given `POST /api/plan` returns HTTP 502, when the error response arrives, then an inline banner appears inside the cards panel with `bg-red-50 border-red-200 text-red-700` styling (`background: #FEF2F2; border: 1px solid #FECACA; color: #B91C1C`); the message reads "Could not load Google Maps routes. Try again." (for `error: "google_maps"`) or "Could not load Régie Essence pricing. Try again." (for `error: "regie_essence"`); the banner persists until the user submits a new trip — no auto-dismiss, no toast.

**AC5:** Given Google Maps returns fewer than 3 route alternatives, when cards render, then only 1 or 2 cards appear — no empty placeholder cards are shown for the missing routes.

**AC6:** Given the `data_timestamp` from the API response is more than 24 hours ago, when the footer timestamp renders, then the timestamp text colour changes to `var(--warning)` (amber) — no blocking UI, no banner.

**AC7:** Given a viewport < 768px, when I view the app, then the layout stacks vertically: form fields in a single column → cards panel (full width, `p-5` card padding) → map (`h-[300px]` fixed) → footer timestamp; the settings drawer renders as a full-width panel sliding up from the bottom instead of from the right; all interactive elements meet 44×44px minimum touch target: cards, "Find routes" button, gear icon (`p-3`), "+ Add waypoint" and "×" (`min-h-[44px]`).

## Tasks / Subtasks

- [x] Task 1: Low-range amber indicator on range input
  - [x] In `static/js/app.js`: add `input` event listener on `#range-km`
  - [x] If value ≤ 50: add `border: 1.5px solid var(--warning)` (or class `range-low`) to the input
  - [x] If value > 50 or empty: remove the amber styling
  - [x] Also trigger this check on page load if a saved range value is pre-populated from localStorage
- [x] Task 2: Implement full no-stations card state in `renderCard()` in `static/js/app.js`
  - [x] When `route.best_station === null` OR `route.stations.length === 0`:
    - Card background: `var(--bg)` (gray, not white)
    - Card border: `1px solid var(--border)`
    - Card left strip: gray (`#D1D5DB`), not route colour
    - Card cursor: `default` (non-interactive — no click handler)
    - Card content: route label + drive time + message: `"No reachable stations on this route"`
    - If API provides `nearest_station_km` and `range_shortfall_km` fields: render `"Nearest station is X km — Y km beyond your range"`
    - Do NOT add `state.setSelectedRoute` click listener on no-stations cards
  - [x] Note: The current API schema in Story 2.3 does NOT include `nearest_station_km` or `range_shortfall_km` fields. If those fields are absent from the response, just display `"No reachable stations on this route."` — do NOT crash trying to read missing fields
- [x] Task 3: Implement amber reachability banner
  - [x] Add `<div id="reachability-banner" hidden class="reachability-banner">` above `#route-cards` in `static/index.html`
  - [x] In `renderCards(routes)`: count routes with reachable stations (non-empty `stations` array)
  - [x] If any route has `stations.length === 0`: show banner with "N station(s) reachable · Z km buffer active" where N = count of routes WITH stations, Z = `buffer_km` from `state.settings.safety_buffer_km`
  - [x] If ALL routes have `stations.length === 0`: add additional text "Try increasing your range or widening the corridor in settings"
  - [x] If all routes have stations: hide banner
  - [x] CSS: `.reachability-banner { background: #FEF3C7; border: 1px solid #F59E0B; color: #92400E; border-radius: 6px; padding: 8px 12px; font-size: 13px; margin-bottom: 8px; }`
- [x] Task 4: Implement API error banner in `showError()` in `static/js/app.js`
  - [x] Add `<div id="error-banner" hidden class="error-banner">` inside `#cards-panel` in `static/index.html` (above `#reachability-banner` and `#route-cards`)
  - [x] Implement `showError(errorCode, message)`:
    ```
    if errorCode === "google_maps": message = "Could not load Google Maps routes. Try again."
    if errorCode === "regie_essence": message = "Could not load Régie Essence pricing. Try again."
    else: message = message or "An unexpected error occurred. Try again."
    ```
  - [x] Set `#error-banner` `textContent` and unhide it
  - [x] CSS: `.error-banner { background: #FEF2F2; border: 1px solid #FECACA; color: #B91C1C; border-radius: 6px; padding: 10px 12px; font-size: 13px; }`
  - [x] Call `hideError()` at the start of each new trip submission (before fetch)
- [x] Task 5: Implement stale timestamp warning in `static/js/app.js`
  - [x] After `renderCards()`, check if `data_timestamp` is more than 24 hours ago
  - [x] If stale: set `#data-timestamp` element colour to `var(--warning)` via `style.color`
  - [x] If not stale: reset `#data-timestamp` colour to `var(--text-secondary)`
- [x] Task 6: Handle < 3 route alternatives (AC5)
  - [x] `renderCards(routes)` already handles this correctly if implemented per Story 3.3 spec (it iterates `routes.forEach(...)` — 1 or 2 routes renders 1 or 2 cards)
  - [x] Verify: no `for (let i = 0; i < 3; i++)` hard-coded loop exists that would create empty cards
- [x] Task 7: Mobile responsive layout — CSS updates in `static/css/style.css`
  - [x] Form fields: `@media (max-width: 767px) { header { flex-wrap: wrap; height: auto; padding: 12px; } #trip-form inputs { width: 100%; } }`
  - [x] Cards panel: `@media (max-width: 767px) { #cards-panel { padding: 20px; } .route-card { padding: 20px; } }` (`p-5` = 20px)
  - [x] "Find routes" button: `min-height: 44px` at mobile
  - [x] Gear icon button: `padding: 12px` (`p-3`) at mobile for 44×44px tap target
  - [x] `+ Add waypoint` and `×` remove button: `min-height: 44px`
  - [x] Settings drawer (already mobile-specified in Story 3.2): confirm full-width bottom panel is implemented
- [x] Task 8: Verify no 3-card hardcoding anywhere in the codebase
  - [x] Check `renderCards`, `renderSkeletonCards`, and any map functions for hard-coded `3` when iterating routes
  - [x] Fix any found instances to use `routes.length` dynamically

## Dev Notes

### No-Stations Card: What API Fields are Available

The current `POST /api/plan` response schema (from Story 2.3) does NOT include `nearest_station_km` or `range_shortfall_km` fields on routes with empty stations. The AC says to display "Nearest station is X km — Y km beyond your range" — but **only if those fields exist in the response**. If they don't exist, display a safe fallback:

```javascript
function renderNoStationsCard(route, index) {
    const card = document.createElement("div");
    card.className = "route-card no-stations";
    
    let msg = "No reachable stations on this route.";
    if (route.nearest_station_km != null && route.range_shortfall_km != null) {
        msg = `Nearest station is ${route.nearest_station_km.toFixed(0)} km — ` +
              `${route.range_shortfall_km.toFixed(0)} km beyond your range`;
    }
    
    card.innerHTML = `
        <div class="route-label">${route.label}</div>
        <div class="drive-time">${formatDriveTime(route.drive_time_seconds)}</div>
        <div class="no-stations-msg">${msg}</div>
    `;
    return card;
}
```

This is defensive: the card works with or without the extra fields.

### Reachability Banner Logic

The banner counts routes with reachable stations, NOT total stations. A route with 5 stations but 0 after autonomy filtering counts as 0 reachable. The `stations` array in the API response already contains only reachable (autonomy-filtered) stations per Story 2.3:

```javascript
function updateReachabilityBanner(routes, bufferKm) {
    const banner = document.getElementById("reachability-banner");
    const routesWithStations = routes.filter(r => r.stations && r.stations.length > 0);
    const allEmpty = routesWithStations.length === 0;
    
    if (routes.some(r => !r.stations || r.stations.length === 0)) {
        let text = `${routesWithStations.length} route(s) with stations · ${bufferKm} km buffer active`;
        if (allEmpty) {
            text += " · Try increasing your range or widening the corridor in settings";
        }
        banner.textContent = text;
        banner.hidden = false;
    } else {
        banner.hidden = true;
    }
}
```

### Error Banner Message Mapping

```javascript
const ERROR_MESSAGES = {
    "google_maps": "Could not load Google Maps routes. Try again.",
    "regie_essence": "Could not load Régie Essence pricing. Try again.",
};

function showError(errorCode, _message) {
    const banner = document.getElementById("error-banner");
    banner.textContent = ERROR_MESSAGES[errorCode] || "An unexpected error occurred. Try again.";
    banner.hidden = false;
}
```

The `_message` parameter (from the API `message` field) is deliberately not shown to the user — it may contain internal error details. The user-facing message is a clean fixed string based on the error code.

### Stale Timestamp Check

```javascript
function updateTimestampDisplay(isoString) {
    const el = document.getElementById("data-timestamp");
    const ts = new Date(isoString);
    const now = new Date();
    const ageHours = (now - ts) / (1000 * 60 * 60);
    
    el.textContent = formatTimestamp(isoString);
    el.style.color = ageHours > 24 ? "var(--warning)" : "var(--text-secondary)";
}
```

### Mobile Touch Targets — 44×44px

All critical interactive elements need explicit minimum sizes on mobile. The most commonly missed ones:
- Gear icon: default `p-2` = 8px padding → button is ~24px. Change to `p-3` (12px) on mobile for ~48px with the icon.
- "×" remove waypoint button: often a small inline button. Use `min-width: 44px; min-height: 44px` in mobile CSS.
- `+ Add waypoint`: ensure it has `min-height: 44px` on mobile.

### Error Handling: Non-JSON Responses

If the server returns a non-JSON response (e.g., unexpected 500 error), `response.json()` will throw. The fetch handler must be wrapped:

```javascript
async function submitTrip(body) {
    try {
        const response = await fetch("/api/plan", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        
        let data;
        try {
            data = await response.json();
        } catch {
            showError("internal", "Server returned an unexpected response");
            return;
        }
        
        if (!response.ok) {
            showError(data.error, data.message);
            return;
        }
        
        renderCards(data.routes);
        renderRoutes(data.routes);
        renderMarkers(data.routes);
        updateTimestampDisplay(data.data_timestamp);
        state.setSelectedRoute(0);
    } catch (err) {
        showError("internal", err.message);
    } finally {
        setLoading(false);
    }
}
```

### Architecture Compliance Checklist

- ✅ `#error-banner` exclusively owned and updated by `app.js`
- ✅ Error messages shown to user are fixed strings — raw API `message` field never displayed
- ✅ `hideError()` called at start of each new submission
- ✅ Stale timestamp: CSS colour change only, no banner/blocking UI
- ✅ No hard-coded `3` in route iteration loops
- ✅ No-stations cards are non-interactive (no click listener, no `setSelectedRoute`)
- ✅ Mobile tap targets ≥ 44×44px for all interactive elements
- ✅ `data_timestamp` colour change uses CSS custom property `var(--warning)` not hard-coded hex

### What NOT to Touch

- `api/routes.py`, `api/pricing.py`, `api/geo.py` — no changes
- `gaz_saver.py` — must remain 100% unchanged
- `static/js/state.js`, `static/js/map.js` — no changes needed for this story
- Existing tests — no changes

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6

### Completion Notes List

- All 8 tasks complete. Low-range amber border on range input (≤50 km, also checked on pre-populate). Full no-stations card with defensive fallback for missing nearest_station_km/range_shortfall_km. Amber reachability banner with correct route/buffer count and all-empty extra message. Red error banner with ERROR_MESSAGES map (google_maps, regie_essence, fallback). Stale timestamp (>24h) renders in var(--warning). renderCards iterates routes.length dynamically — no hardcoded 3. Full mobile responsive CSS: single-column form, 100% cards panel, 300px map, drawer slides from bottom. All touch targets ≥44px verified.

### File List

- `static/js/app.js` — UPDATE (low-range, full no-stations card, reachability banner, error banner, stale timestamp)
- `static/index.html` — UPDATE (reachability-banner and error-banner divs in #cards-panel)
- `static/css/style.css` — UPDATE (banner styles, mobile touch targets, route-card no-stations)

### Change Log

- 2026-05-01: Implemented edge states, error handling, and responsive layout as part of Epic 3 batch implementation.

Original section below:

### Agent Model Used

Claude Sonnet 4.6

### Completion Notes List

### File List

- `static/js/app.js` — UPDATE (showError, hideError, no-stations card, reachability banner, stale timestamp, low-range indicator, mobile touch targets)
- `static/css/style.css` — UPDATE (error-banner, reachability-banner styles, no-stations card, mobile responsive touch targets)
- `static/index.html` — UPDATE (add #error-banner div, #reachability-banner div with correct positions)

### Review Findings

- [x] [Review][Patch] P4 — `#empty-state` permanently lost after first submission — `renderSkeletonCards()` calls `container.innerHTML = ""`, removing `#empty-state` from the DOM. Subsequent calls to `document.getElementById("empty-state")` return null; the empty-state message can never be shown again. Fix: move `#empty-state` outside `#route-cards` (as sibling inside `#cards-panel`), or manage via explicit createElement. [static/js/app.js — renderCards(), static/index.html]
- [x] [Review][Patch] P5 — Skeleton cards remain visible after API error — `setLoading(false)` restores button/spinner but does not clear `#route-cards`. Error paths (non-JSON response, fetch exception) exit `submitTrip` before `renderCards` runs, leaving 3 skeleton cards + error banner visible simultaneously. Fix: clear `#route-cards` in `setLoading(false)` or at error entry points. [static/js/app.js — setLoading(), submitTrip()]
