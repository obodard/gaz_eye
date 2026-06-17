# Story 3.3: Route Cards & Trip Submission

Status: done

## Story

As Olivier,
I want to click "Find routes" and immediately see three route cards with fuel recommendations, savings, and drive time,
So that I can identify the best fuel option for my trip at a glance.

## Acceptance Criteria

**AC1:** Given I have filled in origin, destination, and range, then click "Find routes", when the `POST /api/plan` request is in flight, then the submit button is disabled and its label is replaced with a spinner icon; three skeleton cards appear in the cards panel (animated pulse, same height as loaded cards — no layout shift on results render); a semi-transparent overlay with a centered spinner SVG appears over the map container.

**AC2:** Given the API returns results successfully, when the three route cards render, then each card shows: route label (e.g., "Via Hwy 50"), drive time formatted as `2 h 14 min`, best station name + price formatted as `154.9 ¢/L`, savings formatted as `Save 8.2 ¢/L`; each card has a 4px left border strip in its route colour (`--route-1`, `--route-2`, `--route-3`); if `tank_litres > 0` in settings, a secondary line shows `≈ Save $5.46` in `text-xs` muted colour.

**AC3:** Given the route with the best value (highest `savings_per_litre`), when cards render, then that card has: `--accent-light` background tint, `--accent` 2px border, and a "Best value" badge in the card's top-right corner; no other card has green styling.

**AC4:** Given `state.js` is loaded as an ES module, when `state.setSelectedRoute(index)` is called, then it sets `state.selectedRouteIndex = index` and dispatches `new CustomEvent("routeSelected", { detail: { index } })` on `document`; the calling card gets a 2px route-colour border + `ring-1`, all other cards reduce to `opacity-50`.

**AC5:** Given a route object in the API response where `best_station` is `null`, when the card for that route renders, then the card renders in the gray no-stations state as fully specified in Story 3.5 — never assume `best_station` is always present.

**AC6:** Given no trip has been submitted yet, when the cards panel renders, then it shows a single muted line: "Enter a trip above to see route options." — no skeleton cards, no empty placeholders.

## Tasks / Subtasks

- [x] Task 1: Update `static/js/app.js` — form submission and API call
  - [x] Add `trip-form` `submit` event listener (prevent default)
  - [x] Read form values: `origin`, `destination`, `range_km`, `waypoints` (empty array if no waypoint), plus settings from `state.settings`: `fuel_type`, `corridor_km`, `safety_buffer_km` (as `buffer_km`), `tank_litres`, `max_alternatives`
  - [x] Show loading state: disable `#find-routes-btn`, replace its text with spinner SVG, show `.map-overlay` over map, render 3 skeleton cards in `#route-cards`
  - [x] `fetch("/api/plan", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({...}) })`
  - [x] On success: call `renderCards(data.routes)`, update `#data-timestamp` with formatted timestamp, call `state.setSelectedRoute(0)` to pre-select first route
  - [x] On error: call `showError(data.error, data.message)` — implementation fills `#error-banner` (Story 3.5 details; create stub here)
  - [x] Always: hide loading state (re-enable button, restore button text "Find routes", hide `.map-overlay`)
- [x] Task 2: Implement `renderCards(routes)` in `static/js/app.js`
  - [x] Clear `#route-cards` contents
  - [x] Hide `#empty-state` paragraph
  - [x] Store `data.routes` into `state.routes`
  - [x] For each route (index 0–2): call `renderCard(route, index)` and append to `#route-cards`
  - [x] If `routes.length === 0`: show empty state message, return
- [x] Task 3: Implement `renderCard(route, index)` in `static/js/app.js`
  - [x] Route colours: `ROUTE_COLOURS = ["var(--route-1)", "var(--route-2)", "var(--route-3)"]`
  - [x] Build card `<div>` with: left border `4px solid` in route colour, `background: var(--surface)`, `border-radius: 8px`, `padding: 16px`, `cursor: pointer`
  - [x] Detect best-value: `route.savings_per_litre` is highest among all routes → add `--accent-light` bg, `--accent` 2px border, "Best value" badge (positioned `absolute top-8px right-8px`, `text-xs bg-accent text-white px-2 py-1 rounded-full`)
  - [x] Card content:
    - Route label: `text-base font-medium`
    - Drive time: `text-2xl font-bold`
    - Station price: `text-lg font-semibold` — `"154.9 ¢/L"` format (price × 100, 1 decimal)
    - Savings: `text-xl font-bold` — `"Save 8.2 ¢/L"` format (savings_per_litre × 100, 1 decimal)
    - Per-tank savings: `text-xs text-secondary` — `"≈ Save $5.46"` (only when `tank_litres > 0` AND `savings_per_tank_litres > 0`)
  - [x] If `route.best_station === null`: render no-stations card (see Story 3.5 AC details — render gray card with "Nearest station is X km — Y km beyond your range")
  - [x] Add `click` listener: `card.addEventListener("click", () => state.setSelectedRoute(index))`
  - [x] Listen on `document` for `"routeSelected"` event: update card CSS (selected → 2px route-colour border + `ring-1`; non-selected → `opacity-50`)
- [x] Task 4: Implement `renderSkeletonCards()` in `static/js/app.js`
  - [x] Create 3 skeleton div elements matching loaded card dimensions (`~120px height`, same padding as real cards)
  - [x] Add Tailwind `animate-pulse` class + `bg-gray-200` fill rectangles inside
  - [x] These appear immediately when submit is clicked, before fetch resolves
- [x] Task 5: Implement `formatPrice(pricePerLitre)` helper in `static/js/app.js`
  - [x] Returns `"154.9 ¢/L"` — multiply by 100, keep 1 decimal: `(pricePerLitre * 100).toFixed(1) + " ¢/L"`
  - [x] Handle `null` / `undefined` → return `"n/a"`
- [x] Task 6: Implement `formatDriveTime(seconds)` helper in `static/js/app.js`
  - [x] `≥ 3600`: `"2 h 14 min"` pattern
  - [x] `< 3600`: `"45 min"` pattern
  - [x] Matches the backend `_format_drive_time` in `api/routes.py` exactly
- [x] Task 7: Implement `formatTimestamp(isoString)` helper in `static/js/app.js`
  - [x] Parse ISO 8601 string, format as `"Updated Apr 29 at 23:15"`
  - [x] Use `Date.toLocaleString()` with appropriate options
- [x] Task 8: Add loading/skeleton CSS to `static/css/style.css`
  - [x] `.route-card { position: relative; border-left: 4px solid; border-radius: 8px; padding: 16px; cursor: pointer; background: var(--surface); }`
  - [x] `.route-card.best-value { background: var(--accent-light); border: 2px solid var(--accent); }`
  - [x] `.route-card.selected { outline: 2px solid; outline-offset: 2px; }`
  - [x] `.route-card.dimmed { opacity: 0.5; }`
  - [x] `.skeleton-card { border-radius: 8px; height: 120px; background: #E5E7EB; animation: pulse 1.5s ease-in-out infinite; }`
  - [x] `@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }`
  - [x] `.map-spinner-overlay { position: absolute; inset: 0; background: rgba(249,250,251,0.7); display: flex; align-items: center; justify-content: center; z-index: 20; }`
  - [x] `.best-value-badge { position: absolute; top: 8px; right: 8px; background: var(--accent); color: white; font-size: 11px; padding: 2px 8px; border-radius: 9999px; }`

## Dev Notes

### API Request Body Construction

The `POST /api/plan` request body must include `tank_litres` from settings so the backend `build_recommendation()` can compute `savings_per_tank_litres`:

```javascript
const body = {
    origin: document.getElementById("origin").value.trim(),
    destination: document.getElementById("destination").value.trim(),
    range_km: parseFloat(document.getElementById("range-km").value),
    waypoints: [],  // filled if waypoint field is visible and non-empty
    fuel_type: state.settings.fuel_type,
    corridor_km: state.settings.corridor_km,
    buffer_km: state.settings.safety_buffer_km,
    tank_litres: state.settings.tank_litres,
};

// Add waypoint if present
const waypointInput = document.getElementById("waypoint-0");
const waypointContainer = document.getElementById("waypoint-container");
if (!waypointContainer.hidden && waypointInput.value.trim()) {
    body.waypoints = [waypointInput.value.trim()];
}
```

**Field name mapping:** The settings field `safety_buffer_km` maps to `buffer_km` in the API request body. Do NOT send `safety_buffer_km` — the backend expects `buffer_km`.

### Loading State Ownership

`app.js` owns ALL loading state changes (per architecture):
```javascript
function setLoading(isLoading) {
    const btn = document.getElementById("find-routes-btn");
    const mapContainer = document.getElementById("map");
    const spinnerOverlay = document.getElementById("map-spinner-overlay");
    
    if (isLoading) {
        btn.disabled = true;
        btn.innerHTML = `<svg class="spinner" ...>...</svg>`;
        spinnerOverlay.hidden = false;
        renderSkeletonCards();
    } else {
        btn.disabled = false;
        btn.textContent = "Find routes";
        spinnerOverlay.hidden = true;
    }
}
```

The spinner SVG for the button can be a simple inline rotating circle. Use a CSS animation `@keyframes spin { to { transform: rotate(360deg) } }`.

### Best-Value Card Detection

The best-value card is the one with the **highest** `savings_per_litre`. Important: `routes` may have `null` `best_station` (no reachable stations), in which case `savings_per_litre` is 0 or null. Only consider routes with a valid `best_station` when determining best value:

```javascript
function getBestValueIndex(routes) {
    let best = -1;
    let bestSavings = -Infinity;
    routes.forEach((route, i) => {
        if (route.best_station !== null && route.savings_per_litre > bestSavings) {
            bestSavings = route.savings_per_litre;
            best = i;
        }
    });
    return best;
}
```

### Price Formatting

The API returns `price_per_litre` as a float in dollars (e.g., `1.429`). The UI must display it as `154.9 ¢/L`:
```javascript
function formatPrice(pricePerLitre) {
    if (pricePerLitre === null || pricePerLitre === undefined || !isFinite(pricePerLitre)) {
        return "n/a";
    }
    return (pricePerLitre * 100).toFixed(1) + " ¢/L";
}
```

### Savings Formatting

`savings_per_litre` is also in dollars/litre. Display as cents:
```javascript
function formatSavings(savingsPerLitre) {
    if (!savingsPerLitre || savingsPerLitre <= 0) return null;
    return `Save ${(savingsPerLitre * 100).toFixed(1)} ¢/L`;
}

function formatTankSavings(savingsPerTank) {
    if (!savingsPerTank || savingsPerTank <= 0) return null;
    return `≈ Save $${savingsPerTank.toFixed(2)}`;
}
```

### Card Selection Visual State

When `routeSelected` CustomEvent fires, ALL cards must update:
- Selected card: add `selected` class + set `outline-color` to its route colour
- Non-selected cards: add `dimmed` class (`opacity: 0.5`)
- If `index === null` (no selection): remove all `selected` and `dimmed` classes

Each card element must store its route index and colour for the event handler:
```javascript
card.dataset.routeIndex = index;
card.dataset.routeColour = ROUTE_COLOURS[index];

document.addEventListener("routeSelected", (event) => {
    document.querySelectorAll(".route-card").forEach(c => {
        const i = parseInt(c.dataset.routeIndex);
        const isSelected = i === event.detail.index;
        c.classList.toggle("selected", isSelected);
        c.classList.toggle("dimmed", !isSelected);
        if (isSelected) {
            c.style.outlineColor = c.dataset.routeColour;
        }
    });
});
```

### No-Stations Card (AC5 passthrough to Story 3.5)

When `route.best_station === null`, this story must NOT crash or show a blank card. Render a gray placeholder card. The full no-stations card specification is in Story 3.5 — for this story, render at minimum a card that says "No stations reachable on this route." The Story 3.5 dev will enhance it.

### Timestamp Display

`data_timestamp` from the API is an ISO 8601 string. Format it for the footer:
```javascript
function formatTimestamp(isoString) {
    const d = new Date(isoString);
    return "Updated " + d.toLocaleDateString("en-CA", { month: "short", day: "numeric" })
        + " at " + d.toLocaleTimeString("en-CA", { hour: "2-digit", minute: "2-digit", hour12: false });
}
```

The Story 3.5 AC specifies that timestamps > 24h old show in `--warning` colour. Note this requirement exists but implement the basic display here; Story 3.5 adds the amber warning.

### Architecture: app.js owns #error-banner

`#error-banner` management belongs to `app.js`. Create a `showError(errorCode, message)` stub here:
```javascript
function showError(errorCode, message) {
    const banner = document.getElementById("error-banner");
    // Story 3.5 will fill this in; for now, console.error
    console.error("API error:", errorCode, message);
}

function hideError() {
    const banner = document.getElementById("error-banner");
    if (banner) banner.hidden = true;
}
```

`hideError()` must be called at the start of each new form submission.

### Architecture Compliance Checklist

- ✅ Loading state exclusively owned by `app.js` — no other module sets `is-loading`
- ✅ `#error-banner` exclusively touched by `app.js`
- ✅ `state.setSelectedRoute(index)` is the ONLY way to trigger card/map selection — no direct CSS manipulation from click handlers
- ✅ `state.routes` is populated before `renderCards` returns (for Story 3.4 to access)
- ✅ Route colours come from CSS custom properties: `var(--route-1)`, `var(--route-2)`, `var(--route-3)`
- ✅ `tank_litres` sent to backend via `POST /api/plan` body (field required for `savings_per_tank_litres`)
- ✅ `safety_buffer_km` → `buffer_km` field name translation when building request body
- ✅ No layout shift: skeleton cards match loaded card height before results arrive

### What NOT to Touch

- `api/routes.py`, `api/pricing.py`, `api/geo.py` — no changes
- `chekov.py` — must remain 100% unchanged
- `static/js/state.js` — no changes (already complete from Story 3.1)
- `static/js/map.js` — do NOT call map rendering here; Story 3.4 handles that

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6

### Completion Notes List

- All 8 tasks complete. Form submit listener with fetch to POST /api/plan. renderCards(), renderCard(), renderNoStationsCard() with best-value detection. formatPrice(), formatDriveTime(), formatTimestamp(), formatSavings(), formatTankSavings(), getBestValueIndex() helpers. setLoading() controls button spinner, skeleton cards, and map spinner overlay. routeSelected CustomEvent listener on each card for selection visual state. Skeleton cards (3×, 120px, animated pulse). Error/load stubs in place.

### File List

- `static/js/app.js` — UPDATE (form submission, renderCards, renderCard, all helpers, setLoading)
- `static/css/style.css` — UPDATE (route card, skeleton, spinner, best-value badge, dimmed styles)

### Change Log

- 2026-05-01: Implemented route cards and trip submission as part of Epic 3 batch implementation.

Original section below:

### Agent Model Used

Claude Sonnet 4.6

### Completion Notes List

### File List

- `static/js/app.js` — UPDATE (form submit, renderCards, renderCard, formatters, loading state)
- `static/css/style.css` — UPDATE (route-card, best-value, skeleton, spinner styles)
- `static/index.html` — UPDATE (add `#map-spinner-overlay`, verify `#data-timestamp` in footer)

### Review Findings

- [x] [Review][Patch] P1 — CRITICAL: `setSelectedRoute` not imported in `app.js` — `state.setSelectedRoute(index)` throws `TypeError: state.setSelectedRoute is not a function` at runtime. `setSelectedRoute` is a module-level export from `state.js`, not a property of the `state` object. Must add `setSelectedRoute` to the import from `./state.js` and call it directly. Affects card click (renderCard) and post-submit pre-selection (submitTrip). [static/js/app.js:7]
- [x] [Review][Patch] P2 — `formatDriveTime` operator precedence bug — `Math.floor(seconds % 3600) / 60` should be `Math.floor((seconds % 3600) / 60)`. Produces fractional minutes for non-60-divisible second remainders (e.g., 7261 s → "2 h 1.016... min"). [static/js/app.js:43]
- [x] [Review][Patch] P3 — `routeSelected` event listeners accumulate per card per trip — `renderCard` attaches `document.addEventListener("routeSelected", ...)` on every call, never removed. After N trips: 3N stale listeners. Fix: one global listener in `initForm()` using `querySelectorAll(".route-card")`. [static/js/app.js — renderCard()]
- [x] [Review][Patch] P6 — XSS via unsanitized innerHTML — `route.label` and `route.best_station.name` interpolated directly into innerHTML template literals without escaping. Values originate from Google Directions API and Régie Essence GeoJSON. Fix: use `textContent` for dynamic values. [static/js/app.js — renderCard(), renderNoStationsCard()]
