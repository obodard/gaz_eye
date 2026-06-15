---
baseline_commit: 83801f4f9d0767139379dfe72f7e3b441da37526
---

# Story 5.4: Chat Box Component

Status: review

## Story

As Olivier,
I want a persistent chat panel in the app where I can type natural-language messages and see the assistant's confirmations,
so that I can initiate or modify trips conversationally without needing to navigate the form directly.

## Acceptance Criteria

**AC1:** Given Flask is running and I navigate to `http://localhost:5000`, when the page loads, then a `#chat-panel` section is visible at all times — it does not hide when a trip is submitted, while results are loading, or after results render. The chat panel renders as a collapsible bottom section of the left column (cards panel):
- Default state: **collapsed** — only the input bar (~48px height) with a chevron handle (▲), a text input (`#chat-input`, placeholder "Ask me to plan a trip…"), and a send button
- Expanded state: overlays the cards panel upward, covering up to 60% of available height, showing the message thread (`#chat-messages`, scrollable) above the input bar; chevron points downward (▼)
- Clicking the chevron or typing in the collapsed input expands the panel; clicking the chevron in expanded state collapses it

**AC2:** Given I type a message and press Enter or click the send button, when the message is submitted, then:
- My message appears immediately in `#chat-messages` as a right-aligned user bubble (uses `--text-primary` #111827 as background, white text, `border-radius: 12px 12px 0 12px`)
- A typing indicator (three animated dots) appears below the user bubble
- The `#chat-input` is cleared and disabled, the send button is disabled

**AC3:** Given the `POST /api/chat` response arrives, when the response is rendered, then:
- The typing indicator disappears
- The assistant's `message` from the response body appears as a left-aligned assistant bubble (`--surface` white background, `--border` border, `border-radius: 12px 12px 12px 0`)
- `#chat-input` is re-enabled and focused

**AC4:** Given the `POST /api/chat` returns HTTP 502, when the error is handled, then:
- The typing indicator disappears
- An error-styled assistant bubble appears with text "Assistant unavailable — use the form to plan your trip." (red-tinted, `--error` border)
- `#chat-input` is re-enabled — the user can try again

**AC5:** Given the chat panel layout on desktop (≥768px), when I inspect the layout, then the chat panel sits at the bottom of the left column (cards panel), with the collapsed input bar (~48px) always visible below the route cards. When expanded, the chat thread overlays the cards panel upward (up to 60% of available height). `#chat-messages` is scrollable and auto-scrolls to the latest message on each new bubble.

**AC6:** Given the chat panel layout on mobile (<768px), when I inspect the layout, then `#chat-panel` renders as a fixed-position bottom bar (`position: fixed; bottom: 0; width: 100%`). Expanded state slides up covering the map area; cards remain visible and scrollable above.

**AC7:** Given `style.css` is inspected, when the chat-related rules are read, then user bubble, assistant bubble, and typing-indicator styles are present. The typing indicator uses a CSS animation (e.g., `@keyframes bounce`) on three dot elements — no JavaScript-based animation.

**AC8:** Given `static/js/chat.js` is loaded as an ES module, when its module boundary is inspected, then it imports `state` from `state.js` (for `sessionId` and `setSelectedRoute`). It imports map functions (`filterMarkers`, `restoreMarkers`) from `map.js`. It does not import from `app.js` — loading state and error banners remain exclusively owned by `app.js`.

## Tasks / Subtasks

- [x] Task 1: Add `#chat-panel` HTML structure to `static/index.html` (AC1)
  - [x] Add `#chat-panel` section inside `#cards-panel` at the bottom (after `#route-cards`)
  - [x] Structure: chevron handle, `#chat-messages` container (scrollable), input bar with `#chat-input` and send button
  - [x] Default state: collapsed (CSS class `chat-collapsed`)
  - [x] Add `<script type="module" src="/static/js/chat.js"></script>` before the Maps CDN script

- [x] Task 2: Create `static/js/chat.js` module (AC2, AC3, AC4, AC8)
  - [x] Import `sessionId` from `state.js` and `filterMarkers`, `restoreMarkers` from `map.js`
  - [x] Implement `initChat()` — wire chevron toggle, input focus expand, Enter key submit, send button click
  - [x] Implement `sendMessage(text)`:
    - Append user bubble to `#chat-messages`
    - Show typing indicator
    - Clear and disable input
    - `POST /api/chat` with `{message, session_id: sessionId, is_context_update: false}`
    - On success: remove typing indicator, append assistant bubble with `response.message`
    - On HTTP 502: remove typing indicator, append error-styled bubble
    - Re-enable and focus input
  - [x] Implement `appendBubble(text, type)` — creates user/assistant/error bubble DOM
  - [x] Implement `showTypingIndicator()` / `hideTypingIndicator()`
  - [x] Auto-scroll `#chat-messages` on new bubble
  - [x] Export `initChat` and call from `DOMContentLoaded`

- [x] Task 3: Add chat panel CSS to `static/css/style.css` (AC5, AC6, AC7)
  - [x] Chat panel base styles: positioned at bottom of `#cards-panel`, collapsed state ~48px
  - [x] Expanded state: overlays upward, max 60% of available height
  - [x] User bubble: `--text-primary` background, white text, rounded corners `12px 12px 0 12px`
  - [x] Assistant bubble: `--surface` background, `--border` border, rounded corners `12px 12px 12px 0`
  - [x] Error bubble: red-tinted, `--error` border
  - [x] Typing indicator: `@keyframes bounce` CSS animation on 3 dot elements
  - [x] Mobile (<768px): `position: fixed; bottom: 0; width: 100%`

- [x] Task 4: Store chat response for action dispatch (preparation for Story 5.5) (AC3)
  - [x] After receiving the `POST /api/chat` response, return the parsed response object (action, params, message) for action dispatch
  - [x] DO NOT implement action dispatch in this story — that is Story 5.5's responsibility
  - [x] For now, only display the `message` in the chat thread

## Dev Notes

### HTML Structure for `#chat-panel`

The chat panel goes INSIDE `#cards-panel`, after `#route-cards`. This keeps it in the left column on desktop and naturally flows with the stacked layout on mobile.

```html
<!-- Chat panel — persistent at bottom of cards column -->
<div id="chat-panel" class="chat-collapsed">
    <button type="button" id="chat-toggle" aria-label="Toggle chat">▲</button>
    <div id="chat-messages"></div>
    <div id="chat-input-bar">
        <input type="text" id="chat-input" placeholder="Ask me to plan a trip…" autocomplete="off">
        <button type="button" id="chat-send-btn" aria-label="Send">➤</button>
    </div>
</div>
```

### `chat.js` Module Boundary

```js
import { sessionId } from "./state.js";
import { filterMarkers, restoreMarkers } from "./map.js";
// DO NOT import from app.js — loading state and error banners are app.js's responsibility
```

`chat.js` needs `filterMarkers` and `restoreMarkers` for Story 5.5's action dispatch, but the imports should be added now to establish the module boundary correctly.

### Typing Indicator HTML

```html
<div class="typing-indicator">
    <span class="dot"></span>
    <span class="dot"></span>
    <span class="dot"></span>
</div>
```

CSS animation — three dots that bounce sequentially:
```css
@keyframes bounce {
    0%, 60%, 100% { transform: translateY(0); }
    30% { transform: translateY(-6px); }
}
.typing-indicator .dot {
    animation: bounce 1.2s infinite;
}
.typing-indicator .dot:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator .dot:nth-child(3) { animation-delay: 0.4s; }
```

### Chat Bubble Styling (UX-DR18)

- **User bubble:** `background: var(--text-primary)` (#111827), `color: white`, `border-radius: 12px 12px 0 12px`, right-aligned (using `align-self: flex-end` in a flex column or `margin-left: auto`)
- **Assistant bubble:** `background: var(--surface)` (white), `border: 1px solid var(--border)`, `border-radius: 12px 12px 12px 0`, left-aligned
- **Error bubble:** Same as assistant but with `border-color: var(--error)` and light red background
- **Never use route colours** for chat bubbles — this is explicit in UX-DR18

### Chat Panel Collapse/Expand

- **Collapsed:** `#chat-messages` is `display: none` (or `max-height: 0; overflow: hidden`). Only the input bar is visible. Chevron shows ▲.
- **Expanded:** `#chat-messages` is visible, panel grows upward from the input bar using CSS `flex-direction: column-reverse` or absolute positioning. Chevron shows ▼.
- **Transition:** Use CSS transition on `max-height` or `height` (200ms ease) for smooth expand/collapse.

### Mobile Layout (UX-DR22)

Below 768px:
- `#chat-panel` uses `position: fixed; bottom: 0; left: 0; width: 100%; z-index: 40;`
- Collapsed: only input bar visible (48px)
- Expanded: slides up covering map area. Cards remain scrollable above.
- Must not conflict with existing settings drawer z-index (100)

### Files to Create/Modify

| File | Change |
|------|--------|
| `static/index.html` | **UPDATE**: add `#chat-panel` section inside `#cards-panel` + `chat.js` script tag |
| `static/js/chat.js` | **NEW**: chat module — input handling, message rendering, API calls |
| `static/css/style.css` | **UPDATE**: add chat panel, bubble, typing indicator, mobile styles |

### Existing Code — DO NOT Modify

- `static/js/app.js` — owns loading state, error banners, route cards. Chat does NOT control these.
- `static/js/map.js` — unchanged in this story (Story 5.5 adds `filterMarkers`/`restoreMarkers` exports if not already present)
- `api/routes.py` — `POST /api/chat` already implemented in Story 5.2
- `agent/` — no changes

### `map.js` — Required Exports for Chat

Story 5.5 needs `filterMarkers` and `restoreMarkers` from `map.js`. These functions are NEW — they will be created in Story 5.5. For Story 5.4, import them from `map.js` but **do not call them yet**. If the exports don't exist yet, `chat.js` should handle the missing imports gracefully (check if functions exist before calling).

**Important:** The current `map.js` does NOT export `filterMarkers` or `restoreMarkers`. These will be added in Story 5.5. The import in `chat.js` may need to be deferred or wrapped in a try/catch. Alternatively, add empty stubs in Story 5.4's `map.js` update.

### XSS Prevention

All chat bubble text content must be escaped before insertion into the DOM. Use `textContent` (not `innerHTML`) for message text, or implement the same `escapeHtml()` pattern used in `app.js`.

### Previous Story Intelligence (5.1, 5.2, 5.3)

- Story 5.1: `agent/` package created
- Story 5.2: `POST /api/chat` endpoint in `api/routes.py` — returns `{action, params, message}`
- Story 5.3: `state.js` exports `sessionId` + `app.js` context injection

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 5, Story 5.4]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#UX-DR17, UX-DR18, UX-DR22]
- [Source: static/index.html — current HTML structure]
- [Source: static/css/style.css — current design tokens and layout]
- [Source: static/js/app.js — module boundary, submitTrip function]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None

### Completion Notes List

- Added `#chat-panel` HTML with chevron toggle, message thread, and input bar inside `#cards-panel`
- Created `chat.js` ES module with initChat, sendMessage, appendBubble, typing indicator
- Uses textContent for XSS safety (never innerHTML for user/assistant text)
- Dispatches `chatAction` CustomEvent for Story 5.5 action dispatch
- Added complete CSS: collapsed/expanded states, user/assistant/error bubbles, bounce animation, filter badge, toast, mobile fixed bottom bar
- `chat.js` imports only `sessionId` from `state.js` (filterMarkers/restoreMarkers deferred to Story 5.5)
- Full suite 118 tests pass with no regressions

### File List

- `static/index.html` — MODIFIED
- `static/js/chat.js` — NEW
- `static/css/style.css` — MODIFIED

### Change Log

- 2026-05-31: Story 5.4 implemented — Chat box component with collapsible panel, message bubbles, and typing indicator
