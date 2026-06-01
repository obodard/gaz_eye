/**
 * gaz_eye SPA entry point.
 * Owns: form interaction, settings persistence, API calls, route card rendering,
 * error/reachability banners, loading states, and edge-case handling.
 */

import { state, loadSettings, saveSettings, DEFAULT_SETTINGS, setSelectedRoute, sessionId } from "./state.js";
import { renderRoutes, renderMarkers, clearRoutes } from "./map.js";

// Route colour CSS variables (matching --route-1/2/3 in style.css)
const ROUTE_COLOURS = ["var(--route-1)", "var(--route-2)", "var(--route-3)"];

// localStorage key for trip fields (separate from settings)
const TRIP_KEY = "gaz_eye_trip";

// User-facing error messages keyed by API error code
const ERROR_MESSAGES = {
    "google_maps": "Could not load Google Maps routes. Try again.",
    "regie_essence": "Could not load Régie Essence pricing. Try again.",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

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
 * Format drive time seconds as a human-readable string.
 */
function formatDriveTime(seconds) {
    if (!seconds) return "—";
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
        return `${hours} h ${String(minutes).padStart(2, "0")} min`;
    }
    return `${minutes} min`;
}

/**
 * Format savings in dollars/litre as a cents display string.
 */
function formatSavings(savingsPerLitre) {
    if (!savingsPerLitre || savingsPerLitre <= 0) return null;
    return `Save ${(savingsPerLitre * 100).toFixed(1)} ¢/L`;
}

/**
 * Format per-tank savings in dollars.
 */
function formatTankSavings(savingsPerTank) {
    if (!savingsPerTank || savingsPerTank <= 0) return null;
    return `≈ Save $${savingsPerTank.toFixed(2)}`;
}

/**
 * Format ISO 8601 timestamp for footer display.
 */
function formatTimestamp(isoString) {
    const d = new Date(isoString);
    return "Updated " +
        d.toLocaleDateString("en-CA", { month: "short", day: "numeric" }) +
        " at " +
        d.toLocaleTimeString("en-CA", { hour: "2-digit", minute: "2-digit", hour12: false });
}

/**
 * Escape HTML special characters to prevent XSS when inserting into innerHTML.
 */
function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/**
 * Return the index of the route with the highest savings_per_litre, or -1.
 */
function getBestValueIndex(routes) {
    let best = -1;
    let bestSavings = -Infinity;
    routes.forEach((route, i) => {
        if (route.best_station && (route.savings_per_litre || 0) > bestSavings) {
            bestSavings = route.savings_per_litre || 0;
            best = i;
        }
    });
    return best;
}

// ---------------------------------------------------------------------------
// Error banner
// ---------------------------------------------------------------------------

/**
 * Show a user-facing error message in the error banner.
 */
function showError(errorCode, _message) {
    const banner = document.getElementById("error-banner");
    if (!banner) return;
    banner.textContent = ERROR_MESSAGES[errorCode] || "An unexpected error occurred. Try again.";
    banner.hidden = false;
}

/**
 * Hide the error banner.
 */
function hideError() {
    const banner = document.getElementById("error-banner");
    if (banner) banner.hidden = true;
}

// ---------------------------------------------------------------------------
// Reachability banner
// ---------------------------------------------------------------------------

/**
 * Show/hide the amber reachability banner based on route station counts.
 */
function updateReachabilityBanner(routes) {
    const banner = document.getElementById("reachability-banner");
    if (!banner) return;

    const bufferKm = state.settings ? state.settings.safety_buffer_km : 15;
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

// ---------------------------------------------------------------------------
// Timestamp display
// ---------------------------------------------------------------------------

/**
 * Render the data timestamp in the footer; amber if stale (> 24 h).
 */
function updateTimestampDisplay(isoString) {
    const el = document.getElementById("data-timestamp");
    if (!el) return;
    const ts = new Date(isoString);
    const ageHours = (new Date() - ts) / (1000 * 60 * 60);
    el.textContent = formatTimestamp(isoString);
    el.style.color = ageHours > 24 ? "var(--warning)" : "var(--text-secondary)";
}

// ---------------------------------------------------------------------------
// Loading state
// ---------------------------------------------------------------------------

/**
 * Toggle the loading state: spinner button, skeleton cards, map overlay.
 */
function setLoading(isLoading) {
    const btn = document.getElementById("find-routes-btn");
    const spinnerOverlay = document.getElementById("map-spinner-overlay");

    if (isLoading) {
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = `<svg class="btn-spinner" viewBox="0 0 24 24" fill="none"
                xmlns="http://www.w3.org/2000/svg" width="20" height="20">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3"
                    stroke-dasharray="60" stroke-dashoffset="30" stroke-linecap="round"/>
            </svg>`;
        }
        if (spinnerOverlay) spinnerOverlay.hidden = false;
        renderSkeletonCards();
    } else {
        if (btn) {
            btn.disabled = false;
            btn.textContent = "Find routes";
        }
        if (spinnerOverlay) spinnerOverlay.hidden = true;
        const container = document.getElementById("route-cards");
        if (container && container.querySelector(".skeleton-card")) {
            container.innerHTML = "";
            const emptyState = document.getElementById("empty-state");
            if (emptyState) emptyState.hidden = false;
        }
    }
}

// ---------------------------------------------------------------------------
// Skeleton cards
// ---------------------------------------------------------------------------

/**
 * Render animated skeleton placeholder cards in #route-cards.
 */
function renderSkeletonCards() {
    const container = document.getElementById("route-cards");
    if (!container) return;
    container.innerHTML = "";
    const emptyState = document.getElementById("empty-state");
    if (emptyState) emptyState.hidden = true;
    for (let i = 0; i < 3; i++) {
        const card = document.createElement("div");
        card.className = "skeleton-card";
        card.innerHTML = `
            <div style="background:#D1D5DB;height:16px;border-radius:4px;margin-bottom:8px;width:60%;"></div>
            <div style="background:#D1D5DB;height:24px;border-radius:4px;margin-bottom:8px;width:40%;"></div>
            <div style="background:#D1D5DB;height:16px;border-radius:4px;width:70%;"></div>
        `;
        container.appendChild(card);
    }
}

// ---------------------------------------------------------------------------
// Route cards
// ---------------------------------------------------------------------------

/**
 * Render a gray no-stations card when a route has no reachable stations.
 */
function renderNoStationsCard(route, index) {
    const card = document.createElement("div");
    card.className = "route-card no-stations";
    card.style.borderLeftColor = "#D1D5DB";
    card.style.background = "var(--bg)";
    card.style.border = "1px solid var(--border)";
    card.style.cursor = "default";

    let msg = "No reachable stations on this route.";
    if (route.nearest_station_km != null && route.range_shortfall_km != null) {
        msg = `Nearest station is ${route.nearest_station_km.toFixed(0)} km ` +
              `— ${route.range_shortfall_km.toFixed(0)} km beyond your range`;
    }

    card.innerHTML = `
        <div style="font-size:14px;font-weight:500;color:var(--text-secondary);margin-bottom:4px;">
            ${escapeHtml(route.label || `Route ${index + 1}`)}
        </div>
        <div style="font-size:22px;font-weight:700;color:var(--text-primary);margin-bottom:8px;">
            ${formatDriveTime(route.drive_time_seconds)}
        </div>
        <div style="font-size:13px;color:var(--text-secondary);">${msg}</div>
    `;
    return card;
}

/**
 * Render a single route card, including best-value highlighting and selection sync.
 */
function renderCard(route, index, bestIndex) {
    if (!route.best_station) {
        return renderNoStationsCard(route, index);
    }

    const isBest = index === bestIndex;
    const colour = ROUTE_COLOURS[index];

    const card = document.createElement("div");
    card.className = "route-card" + (isBest ? " best-value" : "");
    card.style.borderLeftColor = colour;
    card.dataset.routeIndex = index;
    card.dataset.routeColour = colour;

    const savings = formatSavings(route.savings_per_litre);
    const tankSavings = (state.settings && state.settings.tank_litres > 0)
        ? formatTankSavings(route.savings_per_tank_litres)
        : null;

    card.innerHTML = `
        ${isBest ? `<span class="best-value-badge">Best value</span>` : ""}
        <div style="font-size:14px;font-weight:500;color:var(--text-secondary);margin-bottom:4px;">
            ${escapeHtml(route.label || `Route ${index + 1}`)}
        </div>
        <div style="font-size:22px;font-weight:700;color:var(--text-primary);margin-bottom:4px;">
            ${formatDriveTime(route.drive_time_seconds)}
        </div>
        <div style="font-size:18px;font-weight:600;color:var(--text-primary);margin-bottom:2px;">
            ${formatPrice(route.best_station.price_per_litre)}
        </div>
        ${savings && !tankSavings
            ? `<div style="font-size:20px;font-weight:700;color:var(--accent);margin-bottom:2px;">${savings}</div>`
            : savings
            ? `<div style="font-size:12px;color:var(--text-secondary);margin-bottom:2px;">${savings}</div>`
            : ""}
        ${tankSavings
            ? `<div style="font-size:20px;font-weight:700;color:var(--accent);margin-bottom:2px;">${tankSavings}</div>`
            : ""}
        <div style="font-size:12px;color:var(--text-secondary);margin-top:4px;">
            ${escapeHtml(route.best_station.name || "")}
        </div>
    `;

    card.addEventListener("click", () => setSelectedRoute(index));

    return card;
}

/**
 * Render all route cards into #route-cards.
 */
function renderCards(routes) {
    const container = document.getElementById("route-cards");
    const emptyState = document.getElementById("empty-state");
    if (!container) return;

    container.innerHTML = "";
    state.routes = routes;

    if (!routes || routes.length === 0) {
        if (emptyState) emptyState.hidden = false;
        return;
    }

    if (emptyState) emptyState.hidden = true;

    const bestIndex = getBestValueIndex(routes);
    routes.forEach((route, index) => {
        container.appendChild(renderCard(route, index, bestIndex));
    });

    updateReachabilityBanner(routes);
}

// ---------------------------------------------------------------------------
// Low-range indicator
// ---------------------------------------------------------------------------

/**
 * Apply or remove the amber border on the range input based on value ≤ 50 km.
 */
function checkRangeLow(input) {
    const val = parseFloat(input.value);
    if (!isNaN(val) && val > 0 && val <= 50) {
        input.style.border = "1.5px solid var(--warning)";
        input.classList.add("range-low");
    } else {
        input.style.border = "";
        input.classList.remove("range-low");
    }
}

// ---------------------------------------------------------------------------
// Trip field persistence
// ---------------------------------------------------------------------------

/**
 * Persist trip fields (origin, destination, range, waypoint) to localStorage.
 */
function saveTripFields() {
    const waypointContainer = document.getElementById("waypoint-container");
    const trip = {
        origin: document.getElementById("origin")?.value || "",
        destination: document.getElementById("destination")?.value || "",
        range_km: document.getElementById("range-km")?.value || "",
        waypoint: (!waypointContainer?.hidden ? document.getElementById("waypoint-0")?.value : "") || "",
    };
    localStorage.setItem(TRIP_KEY, JSON.stringify(trip));
}

// ---------------------------------------------------------------------------
// Settings drawer
// ---------------------------------------------------------------------------

/**
 * Populate all settings drawer inputs from a settings object.
 */
function populateSettingsDrawer(settings) {
    const tankInput = document.getElementById("tank-litres");
    if (tankInput) tankInput.value = settings.tank_litres;

    const corridorSlider = document.getElementById("corridor-km");
    const corridorLabel = document.getElementById("corridor-km-label");
    if (corridorSlider) corridorSlider.value = settings.corridor_km;
    if (corridorLabel) corridorLabel.textContent = `${settings.corridor_km} km`;

    const bufferSlider = document.getElementById("safety-buffer-km");
    const bufferLabel = document.getElementById("safety-buffer-km-label");
    if (bufferSlider) bufferSlider.value = settings.safety_buffer_km;
    if (bufferLabel) bufferLabel.textContent = `${settings.safety_buffer_km} km`;

    document.querySelectorAll(".btn-group[aria-label='Fuel type'] button").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.value === settings.fuel_type);
    });

    document.querySelectorAll(".btn-group[aria-label='Max alternatives'] button").forEach(btn => {
        btn.classList.toggle("active", parseInt(btn.dataset.value) === settings.max_alternatives);
    });
}

/**
 * Close the settings drawer and hide its overlay.
 */
function closeSettingsDrawer() {
    document.getElementById("settings-drawer")?.classList.remove("open");
    document.getElementById("settings-overlay")?.classList.add("hidden");
}

// ---------------------------------------------------------------------------
// Form submission
// ---------------------------------------------------------------------------

/**
 * Submit trip form to POST /api/plan and render results.
 */
async function submitTrip() {
    hideError();

    const origin = (document.getElementById("origin")?.value || "").trim();
    const destination = (document.getElementById("destination")?.value || "").trim();
    const rangeKm = parseFloat(document.getElementById("range-km")?.value || "0");

    const body = {
        origin,
        destination,
        range_km: rangeKm,
        waypoints: [],
        fuel_type: state.settings.fuel_type,
        corridor_km: state.settings.corridor_km,
        buffer_km: state.settings.safety_buffer_km,
        tank_litres: state.settings.tank_litres,
        max_alternatives: state.settings.max_alternatives,
    };

    const waypointContainer = document.getElementById("waypoint-container");
    const waypointInput = document.getElementById("waypoint-0");
    if (waypointContainer && !waypointContainer.hidden && waypointInput?.value.trim()) {
        body.waypoints = [waypointInput.value.trim()];
    }

    setLoading(true);
    clearRoutes();

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
        await renderMarkers(data.routes);
        updateTimestampDisplay(data.data_timestamp);

        // Silently inject trip context into ADK session (fire-and-forget)
        fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: `[TRIP CONTEXT] origin="${origin}", destination="${destination}", range_km=${rangeKm}, waypoints=${JSON.stringify(body.waypoints || [])}`,
                session_id: sessionId,
                is_context_update: true,
            }),
        }).catch(() => {});

        setSelectedRoute(0);
    } catch (err) {
        showError("internal", err.message);
    } finally {
        setLoading(false);
    }
}

// ---------------------------------------------------------------------------
// Form initialisation
// ---------------------------------------------------------------------------

/**
 * Initialise form — load persisted settings and trip fields, wire all event listeners.
 */
function initForm() {
    const settings = loadSettings();
    populateSettingsDrawer(settings);

    // Pre-populate trip fields from localStorage
    try {
        const raw = localStorage.getItem(TRIP_KEY);
        if (raw) {
            const trip = JSON.parse(raw);
            if (trip.origin) {
                const el = document.getElementById("origin");
                if (el) el.value = trip.origin;
            }
            if (trip.destination) {
                const el = document.getElementById("destination");
                if (el) el.value = trip.destination;
            }
            if (trip.range_km) {
                const el = document.getElementById("range-km");
                if (el) {
                    el.value = trip.range_km;
                    checkRangeLow(el);
                }
            }
            if (trip.waypoint) {
                const container = document.getElementById("waypoint-container");
                const input = document.getElementById("waypoint-0");
                const addBtn = document.getElementById("add-waypoint-btn");
                if (container && input && addBtn) {
                    input.value = trip.waypoint;
                    container.hidden = false;
                    addBtn.hidden = true;
                }
            }
        }
    } catch { /* ignore corrupted localStorage */ }

    // Waypoint add/remove
    document.getElementById("add-waypoint-btn")?.addEventListener("click", () => {
        document.getElementById("waypoint-container").hidden = false;
        document.getElementById("add-waypoint-btn").hidden = true;
    });
    document.getElementById("remove-waypoint-0")?.addEventListener("click", () => {
        document.getElementById("waypoint-container").hidden = true;
        document.getElementById("add-waypoint-btn").hidden = false;
        const input = document.getElementById("waypoint-0");
        if (input) input.value = "";
        saveTripFields();
    });

    // Settings drawer open/close
    document.getElementById("settings-btn")?.addEventListener("click", () => {
        document.getElementById("settings-drawer")?.classList.add("open");
        document.getElementById("settings-overlay")?.classList.remove("hidden");
    });
    document.getElementById("close-settings-btn")?.addEventListener("click", closeSettingsDrawer);
    document.getElementById("settings-overlay")?.addEventListener("click", closeSettingsDrawer);

    // Fuel type button group
    document.querySelectorAll(".btn-group[aria-label='Fuel type'] button").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".btn-group[aria-label='Fuel type'] button")
                .forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            saveSettings({ fuel_type: btn.dataset.value });
        });
    });

    // Tank size
    document.getElementById("tank-litres")?.addEventListener("change", (e) => {
        saveSettings({ tank_litres: parseInt(e.target.value) });
    });

    // Corridor radius slider
    const corridorSlider = document.getElementById("corridor-km");
    const corridorLabel = document.getElementById("corridor-km-label");
    corridorSlider?.addEventListener("input", () => {
        if (corridorLabel) corridorLabel.textContent = `${corridorSlider.value} km`;
        saveSettings({ corridor_km: parseFloat(corridorSlider.value) });
    });

    // Safety buffer slider
    const bufferSlider = document.getElementById("safety-buffer-km");
    const bufferLabel = document.getElementById("safety-buffer-km-label");
    bufferSlider?.addEventListener("input", () => {
        if (bufferLabel) bufferLabel.textContent = `${bufferSlider.value} km`;
        saveSettings({ safety_buffer_km: parseInt(bufferSlider.value) });
    });

    // Max alternatives button group
    document.querySelectorAll(".btn-group[aria-label='Max alternatives'] button").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".btn-group[aria-label='Max alternatives'] button")
                .forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            saveSettings({ max_alternatives: parseInt(btn.dataset.value) });
        });
    });

    // Reset to defaults
    document.getElementById("reset-settings-btn")?.addEventListener("click", () => {
        saveSettings({ ...DEFAULT_SETTINGS });
        populateSettingsDrawer(DEFAULT_SETTINGS);
    });

    // Trip field persistence
    ["origin", "destination", "range-km", "waypoint-0"].forEach(id => {
        document.getElementById(id)?.addEventListener("change", saveTripFields);
    });

    // Low-range amber indicator
    const rangeInput = document.getElementById("range-km");
    rangeInput?.addEventListener("input", () => checkRangeLow(rangeInput));

    // Form submission
    document.getElementById("trip-form")?.addEventListener("submit", (e) => {
        e.preventDefault();
        submitTrip();
    });

    // Single global listener for route card visual sync
    document.addEventListener("routeSelected", (event) => {
        document.querySelectorAll(".route-card").forEach(card => {
            const i = parseInt(card.dataset.routeIndex);
            const isSelected = i === event.detail.index;
            card.classList.toggle("selected", isSelected);
            card.classList.toggle("dimmed", !isSelected);
            if (isSelected) {
                card.style.outlineColor = card.dataset.routeColour;
            }
        });
    });
}

document.addEventListener("DOMContentLoaded", initForm);
