/**
 * Chat panel module — handles message input, API calls, bubble rendering,
 * and action dispatch (form fill, map filter).
 */

import { sessionId } from "./state.js";
import { filterMarkers, restoreMarkers } from "./map.js";

// ---------------------------------------------------------------------------
// DOM references
// ---------------------------------------------------------------------------

let chatPanel, chatMessages, chatInput, chatSendBtn, chatToggle;

// ---------------------------------------------------------------------------
// Collapse / expand
// ---------------------------------------------------------------------------

function toggleChat() {
    const isCollapsed = chatPanel.classList.contains("chat-collapsed");
    if (isCollapsed) {
        chatPanel.classList.remove("chat-collapsed");
        chatPanel.classList.add("chat-expanded");
        chatToggle.textContent = "▼";
    } else {
        chatPanel.classList.remove("chat-expanded");
        chatPanel.classList.add("chat-collapsed");
        chatToggle.textContent = "▲";
    }
}

function expandChat() {
    if (chatPanel.classList.contains("chat-collapsed")) {
        chatPanel.classList.remove("chat-collapsed");
        chatPanel.classList.add("chat-expanded");
        chatToggle.textContent = "▼";
    }
}

// ---------------------------------------------------------------------------
// Bubble rendering (XSS-safe — uses textContent)
// ---------------------------------------------------------------------------

function appendBubble(text, type) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble chat-bubble-${type}`;
    bubble.textContent = text;
    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return bubble;
}

// ---------------------------------------------------------------------------
// Typing indicator
// ---------------------------------------------------------------------------

function showTypingIndicator() {
    const indicator = document.createElement("div");
    indicator.className = "typing-indicator";
    indicator.id = "typing-indicator";
    indicator.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
    chatMessages.appendChild(indicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTypingIndicator() {
    const indicator = document.getElementById("typing-indicator");
    if (indicator) indicator.remove();
}

// ---------------------------------------------------------------------------
// Form field flash animation
// ---------------------------------------------------------------------------

function flashField(el) {
    el.style.transition = "background-color 200ms ease-in";
    el.style.backgroundColor = "var(--accent-light)";
    setTimeout(() => {
        el.style.transition = "background-color 200ms ease-out";
        el.style.backgroundColor = "";
    }, 1000);
}

// ---------------------------------------------------------------------------
// Confirmation toast
// ---------------------------------------------------------------------------

function showToast(message) {
    const cardsPanel = document.getElementById("cards-panel");
    if (!cardsPanel) return;

    const toast = document.createElement("div");
    toast.className = "chat-toast";
    toast.textContent = message;
    cardsPanel.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 200);
    }, 4000);
}

// ---------------------------------------------------------------------------
// Action dispatch
// ---------------------------------------------------------------------------

function dispatchAction(response) {
    const { action, params, message } = response;

    switch (action) {
        case "submit_trip": {
            if (!params.origin || !params.destination) break;

            const originEl = document.getElementById("origin");
            const destEl = document.getElementById("destination");
            const rangeEl = document.getElementById("range-km");

            if (originEl) { originEl.value = params.origin; flashField(originEl); }
            if (destEl) { destEl.value = params.destination; flashField(destEl); }
            if (rangeEl && params.range_km != null) { rangeEl.value = params.range_km; flashField(rangeEl); }

            // Handle waypoints (max 1 in MVP)
            if (params.waypoints && params.waypoints.length > 0) {
                const container = document.getElementById("waypoint-container");
                const wpInput = document.getElementById("waypoint-0");
                const addBtn = document.getElementById("add-waypoint-btn");
                if (container && wpInput) {
                    container.hidden = false;
                    if (addBtn) addBtn.hidden = true;
                    wpInput.value = params.waypoints[0];
                    flashField(wpInput);
                }
            }

            // Programmatically submit the trip form
            document.getElementById("trip-form")?.dispatchEvent(
                new Event("submit", { bubbles: true, cancelable: true })
            );

            if (message) showToast(message);
            break;
        }

        case "add_waypoint": {
            const container = document.getElementById("waypoint-container");
            const wpInput = document.getElementById("waypoint-0");
            const addBtn = document.getElementById("add-waypoint-btn");

            if (container && wpInput) {
                container.hidden = false;
                if (addBtn) addBtn.hidden = true;
                wpInput.value = params.waypoint || "";
                flashField(wpInput);
            }

            // Re-submit the form with the new waypoint
            document.getElementById("trip-form")?.dispatchEvent(
                new Event("submit", { bubbles: true, cancelable: true })
            );

            if (message) showToast(message);
            break;
        }

        case "filter_stations_by_area":
            if (params.lat != null && params.lng != null) {
                filterMarkers(params.area_name || "", params.lat, params.lng);
            }
            break;

        case "clear_filter":
            restoreMarkers();
            break;

        case "chat_only":
        default:
            // Message already displayed in chat thread — no further action
            break;
    }
}

// ---------------------------------------------------------------------------
// Send message
// ---------------------------------------------------------------------------

async function sendMessage(text) {
    if (!text.trim()) return;

    // Show user bubble immediately
    appendBubble(text, "user");
    showTypingIndicator();

    // Disable input while waiting
    chatInput.value = "";
    chatInput.disabled = true;
    chatSendBtn.disabled = true;

    try {
        const resp = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: text,
                session_id: sessionId,
                is_context_update: false,
            }),
        });

        hideTypingIndicator();

        if (resp.status === 502) {
            appendBubble("Assistant unavailable — use the form to plan your trip.", "error");
        } else {
            const data = await resp.json();
            appendBubble(data.message || "…", "assistant");
            dispatchAction(data);
        }
    } catch {
        hideTypingIndicator();
        appendBubble("Assistant unavailable — use the form to plan your trip.", "error");
    }

    // Re-enable input
    chatInput.disabled = false;
    chatSendBtn.disabled = false;
    chatInput.focus();
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

function initChat() {
    chatPanel = document.getElementById("chat-panel");
    chatMessages = document.getElementById("chat-messages");
    chatInput = document.getElementById("chat-input");
    chatSendBtn = document.getElementById("chat-send-btn");
    chatToggle = document.getElementById("chat-toggle");

    if (!chatPanel || !chatInput) return;

    // Toggle expand/collapse
    chatToggle.addEventListener("click", toggleChat);

    // Expand on input focus
    chatInput.addEventListener("focus", expandChat);

    // Send on Enter
    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage(chatInput.value);
        }
    });

    // Send on button click
    chatSendBtn.addEventListener("click", () => {
        sendMessage(chatInput.value);
    });
}

export { initChat };

document.addEventListener("DOMContentLoaded", initChat);
