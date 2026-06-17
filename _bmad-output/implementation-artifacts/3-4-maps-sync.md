# Story 3.4: Google Maps Integration & Bidirectional Sync

Status: done

## Story

As Olivier,
I want all three routes drawn on the map with colour-coded polylines and recommended station markers, staying in sync with whichever card or route I select,
So that I can compare routes visually and make my selection from either the map or the cards.

## Acceptance Criteria

**AC1:** Given trip results are loaded, when the map renders, then three route polylines are drawn simultaneously in their route colours (Route A `--route-1` blue `#2563EB`, Route B `--route-2` purple `#9333EA`, Route C `--route-3` orange `#EA580C`) at 4px stroke weight.

**AC2:** Given trip results are loaded, when station markers render, then each recommended station has a custom `AdvancedMarkerElement` — circular pin in its route colour with a white fuel-pump SVG icon at 14px diameter; only the recommended (best) station per route is shown by default — other reachable stations are not shown as pins.

**AC3:** Given I hover over a station marker, when the tooltip appears, then it shows the station name and price formatted as `154.9 ¢/L`.

**AC4:** Given I click a route card, when `state.setSelectedRoute(index)` fires, then that route's polyline becomes 6px weight; other polylines dim to 40% opacity; that route's station marker enlarges to 20px diameter with a white border ring; the `routeSelected` CustomEvent triggers the visual update in `map.js` via a `document.addEventListener("routeSelected", ...)` listener.

**AC5:** Given I click a route polyline on the map, when the click is handled in `map.js`, then `state.setSelectedRoute(index)` is called with the matching route index; the corresponding card updates its visual state identically to having been clicked directly.

**AC6:** Given `map.js` is inspected, when the file is read, then `window.initMap` is assigned as `window.initMap = initMap` within `map.js` — never defined inline in `index.html`.

## Tasks / Subtasks

- [x] Task 1: Implement `renderRoutes(routes)` in `static/js/map.js`
  - [x] Clear existing polylines and markers on each call (`clearRoutes()` helper)
  - [x] For each route (index 0–2): create a `google.maps.Polyline` with `path` decoded from `route.polyline_encoded`, `strokeColor` from route colour array, `strokeWeight: 4`, `strokeOpacity: 1.0`
  - [x] Store polylines in module-scope array: `let polylines = [];`
  - [x] Add click listener to each polyline: `polyline.addListener("click", () => { import("./state.js").then(m => m.setSelectedRoute(index)); })`
  - [x] Fit map bounds to show all three routes: `map.fitBounds(combinedBounds)`
- [x] Task 2: Implement `renderMarkers(routes)` in `static/js/map.js`
  - [x] For each route: if `route.best_station === null`, skip (no marker)
  - [x] Create custom `AdvancedMarkerElement` pin for each best station:
    - Build pin HTML element: circular div in route colour, white fuel-pump SVG inside, `width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center;`
    - `new google.maps.marker.AdvancedMarkerElement({ position: { lat, lng }, map, content: pinElement, title: station.name })`
  - [x] Store markers in module-scope array: `let markers = [];`
  - [x] Store marker's route index on element: `pinElement.dataset.routeIndex = index`
  - [x] Hover InfoWindow: on `mouseover` on pinElement, open `google.maps.InfoWindow` with `"<b>{name}</b><br>{price} ¢/L"` content; on `mouseout`, close InfoWindow
- [x] Task 3: Implement `clearRoutes()` in `static/js/map.js`
  - [x] Set `polyline.setMap(null)` for each existing polyline
  - [x] Call `marker.map = null` for each existing AdvancedMarkerElement
  - [x] Reset `polylines = []`, `markers = []`
  - [x] Close any open InfoWindow
- [x] Task 4: Implement `updateSelection(selectedIndex)` in `static/js/map.js`
  - [x] For each polyline (index 0–2):
    - If selected: `polyline.setOptions({ strokeWeight: 6, strokeOpacity: 1.0 })`
    - If not selected: `polyline.setOptions({ strokeWeight: 4, strokeOpacity: 0.4 })`
  - [x] For each marker pin element (index 0–2):
    - If selected: resize pin to `width: 34px; height: 34px` + add white `border: 2px solid white` + add `box-shadow: 0 0 0 2px <routeColour>`
    - If not selected: reset to `width: 28px; height: 28px`, remove border
- [x] Task 5: Listen for `routeSelected` event in `map.js`
  - [x] `document.addEventListener("routeSelected", (event) => { updateSelection(event.detail.index); });`
  - [x] Attach this listener inside `initMap()` (or at module load — either is fine, but `map` must be initialized first)
- [x] Task 6: Export `renderRoutes` and call it from `app.js` after results arrive
  - [x] In `map.js`: `export { renderRoutes, renderMarkers };`
  - [x] In `app.js`: `import { renderRoutes, renderMarkers } from "./map.js";`
  - [x] After `renderCards(data.routes)` succeeds: call `renderRoutes(data.routes)`, then `renderMarkers(data.routes)`
  - [x] Also call `clearRoutes()` at the start of each new trip submission (from `app.js` importing it)
- [x] Task 7: Implement `decodePolyline(encoded)` in `static/js/map.js`
  - [x] The `polyline_encoded` field from the API is a Google-encoded polyline string
  - [x] Use `google.maps.geometry.encoding.decodePath(encoded)` (part of the Maps JS API geometry library) to decode it into `LatLng` points
  - [x] Add `libraries=geometry` to the Maps JS CDN URL in `index.html`: `...&libraries=geometry&callback=initMap`
  - [x] Returns an array of `google.maps.LatLng` objects suitable for `google.maps.Polyline`
- [x] Task 8: Verify AdvancedMarkerElement map ID requirement
  - [x] Confirm `mapId: "chekov_map"` is set in `initMap()` (Story 3.1 already does this) — if it was skipped, add it now; AdvancedMarkerElement throws if Map has no `mapId`

## Dev Notes

### AdvancedMarkerElement Requires mapId

`google.maps.marker.AdvancedMarkerElement` is the modern replacement for the deprecated `google.maps.Marker`. It **requires** the parent `Map` to be instantiated with a `mapId`. This was documented as critical in Story 3.1. If Story 3.1 dev forgot to set `mapId: "chekov_map"` in `initMap()`, fix it here before adding markers.

```javascript
// map.js — initMap() must include mapId
map = new google.maps.Map(mapEl, {
    center: { lat: 46.8, lng: -71.2 },
    zoom: 7,
    mapId: "chekov_map",  // REQUIRED for AdvancedMarkerElement
});
```

### Geometry Library

The `google.maps.geometry.encoding.decodePath` function requires the geometry library to be loaded. Update the Maps CDN URL in `static/index.html`:

```html
<!-- Before: -->
<script async defer src="https://maps.googleapis.com/maps/api/js?key={{ google_maps_api_key }}&callback=initMap&loading=async"></script>

<!-- After: -->
<script async defer src="https://maps.googleapis.com/maps/api/js?key={{ google_maps_api_key }}&libraries=geometry&callback=initMap&loading=async"></script>
```

### Fuel-Pump SVG Icon

A simple SVG fuel pump icon (inline, white fill, ~16×16px):
```javascript
const fuelPumpSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="white">
  <path d="M18 5.5A2.5 2.5 0 0 1 20.5 8v8a1.5 1.5 0 0 1-3 0V8a.5.5 0 0 0-.5-.5H16V5.5h2zM5 3h8a2 2 0 0 1 2 2v14H3V5a2 2 0 0 1 2-2zm1 4v5h6V7H6z"/>
</svg>`;
```

### Custom Pin Element Construction

```javascript
function createPinElement(routeColour, size = 28) {
    const el = document.createElement("div");
    el.style.cssText = `
        width: ${size}px; height: ${size}px;
        background: ${routeColour};
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        cursor: pointer;
    `;
    el.innerHTML = fuelPumpSvg;
    return el;
}
```

### Polyline Click — Dynamic Import Pattern

Polyline click listeners need to call `state.setSelectedRoute()`. However, `map.js` should import from `state.js` at the top level to avoid dynamic import complexity:

```javascript
// map.js — top of file
import { setSelectedRoute } from "./state.js";
```

Then inside the polyline click handler:
```javascript
polyline.addListener("click", () => setSelectedRoute(routeIndex));
```

### InfoWindow — Singleton Pattern

Create ONE InfoWindow instance and reuse it (not one per marker — they all share):
```javascript
let infoWindow = null;  // module scope

// Inside initMap():
infoWindow = new google.maps.InfoWindow();

// In marker hover:
pinElement.addEventListener("mouseover", () => {
    infoWindow.setContent(`<b>${station.name}</b><br>${formatPrice(station.price_per_litre)}`);
    infoWindow.open({ map, anchor: advancedMarker });
});
pinElement.addEventListener("mouseout", () => infoWindow.close());
```

**Note:** `formatPrice` is defined in `app.js`. Either duplicate the formatter in `map.js` (simple) or export it from a shared utility. The clean solution is to define `formatPrice` in `state.js` (it has no DOM dependency) and import from there. For simplicity, a local copy in `map.js` is acceptable.

### AdvancedMarkerElement Usage Pattern

```javascript
import { setSelectedRoute } from "./state.js";

const ROUTE_COLOURS = ["#2563EB", "#9333EA", "#EA580C"];

async function createAdvancedMarker(station, routeIndex, mapInstance) {
    // AdvancedMarkerElement is in the marker library loaded with Maps JS
    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");
    const pinEl = createPinElement(ROUTE_COLOURS[routeIndex]);
    
    const marker = new AdvancedMarkerElement({
        position: { lat: station.lat, lng: station.lng },
        map: mapInstance,
        content: pinEl,
        title: station.name,
    });
    
    pinEl.addEventListener("mouseover", () => {
        infoWindow.setContent(`<b>${station.name}</b><br>${(station.price_per_litre * 100).toFixed(1)} ¢/L`);
        infoWindow.open({ map: mapInstance, anchor: marker });
    });
    pinEl.addEventListener("mouseout", () => infoWindow.close());
    pinEl.addEventListener("click", () => setSelectedRoute(routeIndex));
    
    return { marker, pinEl, routeIndex };
}
```

**Alternative:** Use `google.maps.importLibrary("marker")` instead of the CDN `libraries=` param. Either approach works — the `libraries=geometry` URL param is still needed for polyline decoding.

### Fitting Map Bounds

After rendering all polylines, fit the map to show all routes:
```javascript
function fitMapToRoutes(routes) {
    const bounds = new google.maps.LatLngBounds();
    routes.forEach(route => {
        const path = google.maps.geometry.encoding.decodePath(route.polyline_encoded);
        path.forEach(pt => bounds.extend(pt));
    });
    map.fitBounds(bounds, 40);  // 40px padding
}
```

### Route Colour Palette

Use hex values directly in JS (not CSS vars, as CSS vars aren't accessible in JS context of Polyline options):

```javascript
const ROUTE_COLOURS = [
    "#2563EB",  // Route A — blue-600 (--route-1)
    "#9333EA",  // Route B — purple-600 (--route-2)
    "#EA580C",  // Route C — orange-600 (--route-3)
];
```

### Architecture Compliance Checklist

- ✅ `window.initMap = initMap` in `map.js` — never in `index.html`
- ✅ `state.setSelectedRoute()` is the trigger for ALL selection changes — polyline clicks call it
- ✅ `document.addEventListener("routeSelected", ...)` in `map.js` for receiving selection updates
- ✅ `AdvancedMarkerElement` used (not deprecated `google.maps.Marker`)
- ✅ `mapId: "chekov_map"` set in Map constructor
- ✅ Only `best_station` per route shown as a marker (not all reachable stations)
- ✅ Route colours from `ROUTE_COLOURS` hex array (matching CSS custom properties)
- ✅ `clearRoutes()` called on each new trip submission to avoid stale polylines/markers
- ✅ `libraries=geometry` added to Maps CDN URL for polyline decoding

### What NOT to Touch

- `api/routes.py`, `api/pricing.py`, `api/geo.py` — no changes
- `chekov.py` — must remain 100% unchanged
- `static/js/state.js` — no changes (already complete)
- `static/css/style.css` — minimal/no changes needed for this story
- Existing tests — no changes

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6

### Completion Notes List

- All 8 tasks complete. renderRoutes() decodes polylines via google.maps.geometry.encoding.decodePath and draws Polylines with route colours; fitBounds fits all routes. renderMarkers() creates AdvancedMarkerElement pins with fuel-pump SVG, InfoWindow on hover/mouseout. clearRoutes() clears all polylines and markers. updateSelection() adjusts stroke weight/opacity and pin size/border on routeSelected event. Polyline click calls setSelectedRoute(). map.js imports setSelectedRoute from state.js at top level. app.js imports renderRoutes, renderMarkers, clearRoutes from map.js. libraries=geometry added to Maps CDN URL.

### File List

- `static/js/map.js` — UPDATE (renderRoutes, renderMarkers, clearRoutes, updateSelection, routeSelected listener)
- `static/js/app.js` — UPDATE (import renderRoutes/renderMarkers/clearRoutes, call after trip submission)
- `static/index.html` — UPDATE (add `libraries=geometry` to Maps CDN URL)

### Change Log

- 2026-05-01: Implemented Google Maps bidirectional sync as part of Epic 3 batch implementation.
- 2026-05-10: Code review identified marker size discrepancy (implemented 28px/34px vs spec 14px/20px). Corrected to 14px/20px per spec during Story 4.4 review for consistency. UX review confirmed 14px is appropriate for simple gas station markers.
