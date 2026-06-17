/**
 * Application state and settings management.
 * SETTINGS_KEY and DEFAULT_SETTINGS are the single source of truth — never duplicated elsewhere.
 */

const SETTINGS_KEY = "chekov_settings";

/** Session ID for ADK chat — regenerated on each page load, never persisted. */
export const sessionId = crypto.randomUUID();

const DEFAULT_SETTINGS = {
    fuel_type: "Régulier",
    tank_litres: 60,
    corridor_km: 2.0,
    safety_buffer_km: 15,
    max_alternatives: 3,
};

const state = {
    routes: [],
    selectedRouteIndex: null,
    settings: null,
};

/**
 * Load settings from localStorage, falling back to DEFAULT_SETTINGS.
 */
export function loadSettings() {
    try {
        const raw = localStorage.getItem(SETTINGS_KEY);
        state.settings = raw
            ? { ...DEFAULT_SETTINGS, ...JSON.parse(raw) }
            : { ...DEFAULT_SETTINGS };
    } catch {
        state.settings = { ...DEFAULT_SETTINGS };
    }
    return state.settings;
}

/**
 * Merge partial settings update and persist to localStorage.
 */
export function saveSettings(partial) {
    state.settings = { ...state.settings, ...partial };
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(state.settings));
}

/**
 * Update selected route index and dispatch CustomEvent for map/card sync.
 */
export function setSelectedRoute(index) {
    state.selectedRouteIndex = index;
    document.dispatchEvent(new CustomEvent("routeSelected", { detail: { index } }));
}

export { state, DEFAULT_SETTINGS, SETTINGS_KEY };
