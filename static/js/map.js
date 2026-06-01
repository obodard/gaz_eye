/**
 * Google Maps integration module.
 * Handles map initialisation, polyline rendering, marker placement, and bidirectional selection sync.
 * window.initMap is assigned at module level so the Maps CDN callback finds it after load.
 */

import { setSelectedRoute } from "./state.js";

const ROUTE_COLOURS = [
    "#2563EB",  // Route A — blue-600  (--route-1)
    "#9333EA",  // Route B — purple-600 (--route-2)
    "#EA580C",  // Route C — orange-600 (--route-3)
];

const WORST_STATION_COLOUR = "#DC2626";  // --error red

let map = null;
let polylines = [];
let markers = [];
let infoWindow = null;

const fuelPumpSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="white">
  <path d="M18 5.5A2.5 2.5 0 0 1 20.5 8v8a1.5 1.5 0 0 1-3 0V8a.5.5 0 0 0-.5-.5H16V5.5h2zM5 3h8a2 2 0 0 1 2 2v14H3V5a2 2 0 0 1 2-2zm1 4v5h6V7H6z"/>
</svg>`;

/**
 * Format price in dollars/litre as a cents display string.
 */
function formatPrice(pricePerLitre) {
    if (pricePerLitre === null || pricePerLitre === undefined || !isFinite(pricePerLitre)) {
        return "n/a";
    }
    return (pricePerLitre * 100).toFixed(1) + " ¢/L";
}

/**
 * Create a circular pin DOM element for an AdvancedMarkerElement.
 * Default size: 28px diameter; 34px when selected.
 */
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

/**
 * Initialise the Google Maps instance and attach to #map container.
 */
export function initMap() {
    const mapEl = document.getElementById("map");
    map = new google.maps.Map(mapEl, {
        center: { lat: 46.8, lng: -71.2 },
        zoom: 7,
        mapId: "gaz_eye_map",  // Required for AdvancedMarkerElement
    });
    infoWindow = new google.maps.InfoWindow();

    document.addEventListener("routeSelected", (event) => {
        updateSelection(event.detail.index);
    });
}

// CRITICAL: must be at module level so the Maps CDN callback finds it after load
window.initMap = initMap;

/**
 * Clear all existing polylines, markers, and close any open InfoWindow.
 */
export function clearRoutes() {
    polylines.forEach(p => p.setMap(null));
    markers.forEach(({ marker }) => { marker.map = null; });
    if (infoWindow) infoWindow.close();
    polylines = [];
    markers = [];
}

/**
 * Draw colour-coded polylines for all routes and fit map bounds to show them all.
 */
export function renderRoutes(routes) {
    clearRoutes();
    if (!map) return;

    const bounds = new google.maps.LatLngBounds();

    routes.forEach((route, index) => {
        if (!route.polyline_encoded) return;

        const path = google.maps.geometry.encoding.decodePath(route.polyline_encoded);
        path.forEach(pt => bounds.extend(pt));

        const polyline = new google.maps.Polyline({
            path,
            strokeColor: ROUTE_COLOURS[index],
            strokeWeight: 4,
            strokeOpacity: 1.0,
            map,
        });

        const routeIndex = index;
        polyline.addListener("click", () => setSelectedRoute(routeIndex));
        polylines.push(polyline);
    });

    if (!bounds.isEmpty()) {
        map.fitBounds(bounds, 40);
    }
}

/**
 * Place custom AdvancedMarkerElement pins for the best station on each route.
 */
export async function renderMarkers(routes) {
    if (!map) return;

    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");

    for (let index = 0; index < routes.length; index++) {
        const route = routes[index];

        // Best-station marker (route colour)
        if (route.best_station) {
            const station = route.best_station;
            const pinEl = createPinElement(ROUTE_COLOURS[index]);
            pinEl.dataset.routeIndex = index;

            const marker = new AdvancedMarkerElement({
                position: { lat: station.lat, lng: station.lng },
                map,
                content: pinEl,
                title: station.name,
            });

            pinEl.addEventListener("mouseover", () => {
                infoWindow.setContent(`<b>${station.name}</b><br>${formatPrice(station.price_per_litre)}`);
                infoWindow.open({ map, anchor: marker });
            });
            pinEl.addEventListener("mouseout", () => infoWindow.close());
            pinEl.addEventListener("click", () => setSelectedRoute(index));

            markers.push({ marker, pinEl, routeIndex: index, markerType: "best" });
        }

        // Worst-station marker (red) — only when non-null and distinct from best
        if (route.worst_station) {
            const ws = route.worst_station;
            const bs = route.best_station;
            // Validate coordinates are finite before comparison
            if (!ws.lat || !ws.lng || !isFinite(ws.lat) || !isFinite(ws.lng)) continue;
            // Use latitude-scaled tolerance: ~1 meter at 45°N (story location)
            const latTolerance = 1e-5 / Math.cos(bs && bs.lat ? bs.lat * Math.PI / 180 : 45 * Math.PI / 180);
            const isSameLocation = bs && isFinite(bs.lat) && isFinite(bs.lng) &&
                Math.abs(ws.lat - bs.lat) < 1e-5 &&
                Math.abs(ws.lng - bs.lng) < latTolerance;

            if (!isSameLocation) {
                const wsPinEl = createPinElement(WORST_STATION_COLOUR);
                wsPinEl.dataset.routeIndex = index;

                const wsMarker = new AdvancedMarkerElement({
                    position: { lat: ws.lat, lng: ws.lng },
                    map,
                    content: wsPinEl,
                    title: ws.name,
                });

                wsPinEl.addEventListener("mouseover", () => {
                    infoWindow.setContent(`<b>${ws.name}</b><br>${formatPrice(ws.price_per_litre)}`);
                    infoWindow.open({ map, anchor: wsMarker });
                });
                wsPinEl.addEventListener("mouseout", () => infoWindow.close());
                wsPinEl.addEventListener("click", () => setSelectedRoute(index));

                markers.push({ marker: wsMarker, pinEl: wsPinEl, routeIndex: index, markerType: "worst" });
            }
        }
    }
}

/**
 * Update polyline weights and marker sizes based on the selected route index.
 */
function updateSelection(selectedIndex) {
    polylines.forEach((polyline, i) => {
        if (i === selectedIndex) {
            polyline.setOptions({ strokeWeight: 6, strokeOpacity: 1.0 });
        } else {
            polyline.setOptions({ strokeWeight: 4, strokeOpacity: 0.4 });
        }
    });

    markers.forEach(({ pinEl, routeIndex, markerType }) => {
        const ringColour = markerType === "worst" ? WORST_STATION_COLOUR : ROUTE_COLOURS[routeIndex % ROUTE_COLOURS.length];
        if (routeIndex === selectedIndex) {
            pinEl.style.width = "34px";
            pinEl.style.height = "34px";
            pinEl.style.border = "2px solid white";
            pinEl.style.boxShadow = `0 0 0 2px ${ringColour}`;
        } else {
            pinEl.style.width = "28px";
            pinEl.style.height = "28px";
            pinEl.style.border = "";
            pinEl.style.boxShadow = "0 2px 4px rgba(0,0,0,0.3)";
        }
    });
}

// ---------------------------------------------------------------------------
// Marker filtering (Story 5.5)
// ---------------------------------------------------------------------------

let hiddenMarkers = [];

/**
 * Haversine distance in km between two lat/lng points.
 */
function haversineKm(lat1, lng1, lat2, lng2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) ** 2 +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLng / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

/**
 * Hide markers outside a 25 km radius of the given coordinates.
 * Show a filter badge on the map container.
 */
export function filterMarkers(areaName, lat, lng) {
    // Restore any previously hidden markers first
    restoreMarkers();

    markers.forEach((entry) => {
        const pos = entry.marker.position;
        if (!pos) return;
        const mLat = typeof pos.lat === "function" ? pos.lat() : pos.lat;
        const mLng = typeof pos.lng === "function" ? pos.lng() : pos.lng;
        const dist = haversineKm(lat, lng, mLat, mLng);
        if (dist > 25) {
            entry.marker.map = null;
            hiddenMarkers.push(entry);
        }
    });

    // Show filter badge
    let badge = document.getElementById("filter-badge");
    if (!badge) {
        badge = document.createElement("div");
        badge.id = "filter-badge";
        const mapEl = document.getElementById("map");
        if (mapEl) mapEl.appendChild(badge);
    }
    badge.innerHTML = "";
    badge.textContent = "";
    const textNode = document.createTextNode(`📍 ${areaName} · `);
    badge.appendChild(textNode);
    const clearLink = document.createElement("a");
    clearLink.href = "#";
    clearLink.textContent = "Show all";
    clearLink.addEventListener("click", (e) => {
        e.preventDefault();
        restoreMarkers();
    });
    badge.appendChild(clearLink);
}

/**
 * Restore all previously hidden markers and remove the filter badge.
 */
export function restoreMarkers() {
    hiddenMarkers.forEach((entry) => {
        entry.marker.map = map;
    });
    hiddenMarkers = [];

    const badge = document.getElementById("filter-badge");
    if (badge) badge.remove();
}
