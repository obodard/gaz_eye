# Story 3.2: Trip Form & Settings Persistence

Status: done

## Story

As Olivier,
I want to fill in my trip details and settings with them remembered between sessions,
So that repeat trips require zero re-entry and I can adjust corridor or fuel preferences without losing my trip context.

## Acceptance Criteria

**AC1:** Given the app is open, when I view the header, then it contains: Origin text input, Destination text input, Range number input (km), a ghost "+ Add waypoint" button below the destination field, a "Find routes" primary button (`bg-gray-900 text-white rounded-lg`), and a gear icon button (`p-2 rounded-lg hover:bg-gray-100`).

**AC2:** Given I click "+ Add waypoint", when the field appears, then a labeled "Waypoint" text input appears inline below the destination field with an inline "×" remove button; the "+ Add waypoint" button is hidden (max 1 waypoint in MVP).

**AC3:** Given a waypoint field is visible, when I click "×", then the waypoint field is removed and the "+ Add waypoint" button reappears.

**AC4:** Given I click the gear icon, when the settings drawer opens, then a `w-72` panel slides in from the right with 200ms `ease` `translateX` transition; an overlay (`bg-black/20`) covers only the map area (not the cards panel); the drawer contains: Fuel type button-group toggle (Regular / Premium / Diesel), Tank size `<input type="number">` (min 1, max 200), Corridor radius `<input type="range">` (1–10 km) with live value label, Safety buffer `<input type="range">` (5–50 km) with live value label, Max alternatives button-group toggle (2 / 3), and a "Reset to defaults" ghost text link.

**AC5:** Given I change any setting value, when the change event fires, then the new value is immediately written to `localStorage` under key `checkov_settings` — no Save button required; `DEFAULT_SETTINGS` and `SETTINGS_KEY = "checkov_settings"` are defined only in `state.js` and never duplicated elsewhere.

**AC6:** Given I click "Reset to defaults", when the link is clicked, then all settings revert to: `fuel_type: "Régulier"`, `tank_litres: 60`, `corridor_km: 2.0`, `safety_buffer_km: 15`, `max_alternatives: 3`; `localStorage` is updated immediately.

**AC7:** Given I close and reopen the browser, when the page loads, then all form fields (origin, destination, range, waypoint if set) and all drawer settings are pre-populated from the last saved `localStorage` values.

**AC8:** Given I click outside the drawer overlay or click "×" in the drawer header, when the drawer closes, then it slides out with 200ms ease and the overlay disappears.

**AC9:** Given the drawer animation implementation, when the code is inspected, then the open/close animation is implemented using vanilla JS (`element.classList.add/remove` or `element.style.transform`) — Alpine.js must NOT be introduced; it conflicts with the Architecture constraint of no JS frameworks.

## Tasks / Subtasks

- [x] Task 1: Update `static/index.html` — replace placeholder header with full trip form
  - [x] Origin `<input type="text" id="origin" placeholder="Origin">` with `autocomplete="off"`
  - [x] Destination `<input type="text" id="destination" placeholder="Destination">` with `autocomplete="off"`
  - [x] Range `<input type="number" id="range-km" placeholder="Range (km)" min="1" max="2000">`
  - [x] `<button id="add-waypoint-btn" type="button">+ Add waypoint</button>` — ghost style
  - [x] `<div id="waypoint-container" hidden>` with `<input type="text" id="waypoint-0">` and `<button id="remove-waypoint-0" type="button">×</button>`
  - [x] `<button id="find-routes-btn" type="submit">Find routes</button>` — primary style
  - [x] `<button id="settings-btn" type="button" aria-label="Settings">⚙</button>`
  - [x] Wrap form fields in `<form id="trip-form">` (but do NOT use native submit — Story 3.3 will handle via `addEventListener("submit", ...)`)
- [x] Task 2: Add settings drawer HTML to `static/index.html`
  - [x] `<div id="settings-overlay" class="map-overlay hidden">` — covers map area only
  - [x] `<div id="settings-drawer" class="settings-drawer">` — positioned absolute, translated off-screen initially
  - [x] Drawer header: title "Settings" + `<button id="close-settings-btn">×</button>`
  - [x] Fuel type button group: 3 buttons (`id="fuel-regular"`, `id="fuel-premium"`, `id="fuel-diesel"`) with `data-value` attributes
  - [x] Tank size: `<input type="number" id="tank-litres" min="1" max="200">`
  - [x] Corridor: `<input type="range" id="corridor-km" min="1" max="10" step="0.5">` + `<span id="corridor-km-label"></span>`
  - [x] Safety buffer: `<input type="range" id="safety-buffer-km" min="5" max="50" step="5">` + `<span id="safety-buffer-km-label"></span>`
  - [x] Max alternatives: button group `id="max-2"` and `id="max-3"` with `data-value` attributes
  - [x] `<button id="reset-settings-btn" type="button">Reset to defaults</button>` — ghost/text style
- [x] Task 3: Add settings drawer CSS to `static/css/style.css`
  - [x] `.settings-drawer { position: fixed; top: 0; right: 0; height: 100%; width: 288px; background: var(--surface); transform: translateX(100%); transition: transform 200ms ease; z-index: 100; padding: 16px; box-shadow: -2px 0 8px rgba(0,0,0,0.1); }`
  - [x] `.settings-drawer.open { transform: translateX(0); }`
  - [x] `.map-overlay { position: absolute; inset: 0; background: rgba(0,0,0,0.2); z-index: 50; }` (relative to `#map` container)
  - [x] Mobile override: drawer becomes full-width bottom panel (`width: 100%; height: auto; bottom: 0; right: 0; top: auto; transform: translateY(100%)`) at `< 768px`
  - [x] `.settings-drawer.open` at mobile: `transform: translateY(0)`
  - [x] Button group active state: `.btn-group button.active { background: #111827; color: white; }`
- [x] Task 4: Update `static/js/app.js` — form & settings interaction
  - [x] Import `{ state, loadSettings, saveSettings, DEFAULT_SETTINGS }` from `./state.js`
  - [x] `initForm()` — on DOMContentLoaded: call `loadSettings()`, then pre-populate all form inputs from `state.settings` and localStorage-saved trip fields (`origin`, `destination`, `range_km`, `waypoint`)
  - [x] Add waypoint: `#add-waypoint-btn` click → show `#waypoint-container`, hide button
  - [x] Remove waypoint: `#remove-waypoint-0` click → hide `#waypoint-container`, show `#add-waypoint-btn`, clear waypoint input value
  - [x] Settings open: `#settings-btn` click → add class `open` to `#settings-drawer`, show `#settings-overlay`
  - [x] Settings close: `#close-settings-btn` click and `#settings-overlay` click → remove class `open`, hide overlay
  - [x] Fuel type buttons: click on any fuel button → update `active` class, call `saveSettings({ fuel_type: value })`
  - [x] Tank size input: `change` event → `saveSettings({ tank_litres: parseInt(value) })`
  - [x] Corridor slider: `input` event → update `#corridor-km-label`, `saveSettings({ corridor_km: parseFloat(value) })`
  - [x] Safety buffer slider: `input` event → update `#safety-buffer-km-label`, `saveSettings({ safety_buffer_km: parseInt(value) })`
  - [x] Max alternatives buttons: click → update `active` class, `saveSettings({ max_alternatives: parseInt(value) })`
  - [x] Reset defaults: `#reset-settings-btn` click → `saveSettings({ ...DEFAULT_SETTINGS })`, repopulate all drawer inputs from DEFAULT_SETTINGS
  - [x] Trip field persistence: save `origin`, `destination`, `range_km`, `waypoint` to localStorage on `change` event (separate from settings — use `localStorage.setItem("checkov_trip", JSON.stringify({...}))`)
  - [x] `initForm()` also loads `checkov_trip` from localStorage to pre-populate trip fields on reload

## Dev Notes

### No JS Framework — Vanilla Only

The architecture document is explicit: **no Alpine.js, no Vue, no React**. All interactivity must be vanilla JS. Any AI agent tempted to add Alpine.js (or any JS framework CDN) must resist — it breaks the architecture constraint. The drawer animation uses only `classList.add/remove` and a CSS `transition`.

### localStorage Keys

Two separate keys are used:
- `checkov_settings` (`SETTINGS_KEY` from `state.js`) — fuel type, tank size, corridor, safety buffer, max alternatives
- `checkov_trip` — trip-specific fields (origin, destination, range_km, waypoint) stored by `app.js`

The `checkov_trip` key is managed in `app.js` directly (it's trip state, not settings). Do NOT put it in `state.js` or use the `saveSettings()` function for it.

### Settings Drawer Positioning

The drawer is `position: fixed` so it overlays the whole page. The overlay (`#settings-overlay`) must be `position: absolute` inside `#map` (or a wrapper around `#map`) so it covers only the map area, NOT the cards panel.

For this to work, the map container needs `position: relative`:
```css
#map {
    position: relative;
    flex: 1;
    min-height: 0;
}
```

And `#settings-overlay` is a child of `#map` in the HTML:
```html
<div id="map">
    <div id="settings-overlay" class="hidden"></div>
    <!-- Google Maps renders here -->
</div>
```

### Fuel Type Toggle HTML Pattern

```html
<div class="btn-group" role="group" aria-label="Fuel type">
    <button type="button" id="fuel-regular" data-value="Régulier" class="active">Regular</button>
    <button type="button" id="fuel-premium" data-value="Super">Premium</button>
    <button type="button" id="fuel-diesel" data-value="Diesel">Diesel</button>
</div>
```

The `data-value` matches the exact French strings used by the Régie Essence API (`"Régulier"`, `"Super"`, `"Diesel"`). These must match `fuel_type` values sent in `POST /api/plan` requests.

### Waypoint Max = 1

MVP only supports 1 waypoint. Do NOT implement a dynamic array of waypoints. The `#waypoint-container` is a single pre-rendered div that is shown/hidden. The `+ Add waypoint` button must be hidden once one waypoint is added.

### Slider with Live Label

Sliders need a `<span>` that updates on every `input` event (not `change` — `input` fires during drag):
```javascript
const corridorSlider = document.getElementById("corridor-km");
const corridorLabel = document.getElementById("corridor-km-label");
corridorSlider.addEventListener("input", () => {
    corridorLabel.textContent = `${corridorSlider.value} km`;
    saveSettings({ corridor_km: parseFloat(corridorSlider.value) });
});
```

### Mobile Drawer Behaviour

At `< 768px`, the drawer slides up from the bottom (full-width):
```css
@media (max-width: 767px) {
    .settings-drawer {
        width: 100%;
        height: auto;
        max-height: 70vh;
        top: auto;
        bottom: 0;
        right: 0;
        transform: translateY(100%);
        border-radius: 16px 16px 0 0;
        overflow-y: auto;
    }
    .settings-drawer.open {
        transform: translateY(0);
    }
}
```

### Files Modified in Story 3.1 to Update

- `static/index.html` — add form HTML, drawer HTML (significant structural additions)
- `static/css/style.css` — add drawer styles, button group styles, form input styles
- `static/js/app.js` — add all form/settings interaction logic

### Architecture Compliance Checklist

- ✅ `SETTINGS_KEY` and `DEFAULT_SETTINGS` only in `state.js` — `app.js` imports them
- ✅ No Alpine.js or any JS framework introduced
- ✅ Drawer animation via CSS `transition` + vanilla JS `classList`
- ✅ Fuel type `data-value` matches Régie Essence API strings (`"Régulier"`, `"Super"`, `"Diesel"`)
- ✅ Max 1 waypoint in MVP — no dynamic array
- ✅ `localStorage.setItem` for settings only called via `saveSettings()` from `state.js`
- ✅ `#error-banner` not touched by this story (ownership: `app.js` for Story 3.5)

### What NOT to Touch

- `api/routes.py`, `api/pricing.py`, `api/geo.py` — no changes
- `checkov.py` — must remain 100% unchanged
- `static/js/state.js` — no changes (already complete from Story 3.1)
- `static/js/map.js` — no changes (only `initMap` stub exists)

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6

### Completion Notes List

- All 4 tasks complete. Full trip form (origin, destination, range, waypoint add/remove) implemented in `static/index.html`. Settings drawer with all controls (fuel type button-group, tank, corridor slider, safety buffer slider, max alternatives, reset) added to HTML and CSS. `app.js` wired: initForm(), loadSettings(), populateSettingsDrawer(), closeSettingsDrawer(), per-field saveSettings() on change events, trip field persistence via checkov_trip localStorage key.

### File List

- `static/index.html` — UPDATE (full trip form HTML, settings drawer HTML)
- `static/css/style.css` — UPDATE (drawer, button group, form input, mobile touch targets)
- `static/js/app.js` — UPDATE (form/settings interaction logic, initForm, populateSettingsDrawer)

### Change Log

- 2026-05-01: Implemented trip form and settings persistence as part of Epic 3 batch implementation.
