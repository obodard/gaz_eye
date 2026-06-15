---
title: "PM Input: Architecture Enhancement Initiative"
project: gaz_eye
status: "draft"
audience: "John (BMad PM)"
author: "Winston (System Architect)"
created: "2026-05-31"
inputs:
  - _bmad-output/architecture-review-2026-05-31.md
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/architecture.md
purpose: |
  Hand-off from System Architect to Product Manager. Distills the 2026-05-31
  architecture review into PRD-ready inputs (problem statements, goals,
  non-goals, scope candidates, success criteria, sequencing guidance) so John
  can update the PRD and draft the epic(s) needed to land these changes.
---

# PM Input — Architecture Enhancement Initiative

## 1. Why You're Reading This

I completed a full architecture review of gaz_eye on 2026-05-31 ([architecture-review-2026-05-31.md](../architecture-review-2026-05-31.md)). The codebase is sound, but I surfaced a set of structural, operational, and conceptual gaps that warrant **product-level decisions** — not just engineering chores — because they affect: cost-to-serve, agent UX trust, deploy readiness, and future feature velocity.

This document gives you what you need to:
1. Decide which findings deserve PRD-level commitment.
2. Frame them as user/business outcomes (not engineering tasks).
3. Draft the epic(s) to land them.

I am **not prescribing scope** — I'm prescribing the decisions you need to make.

---

## 2. Headline Themes (the "what changed" for the PRD)

Five themes emerged. Each is a candidate PRD section or epic. They are independent — you can pick any subset.

### Theme A — Operational Readiness ("Make it deployable & affordable")

**Problem framing for PRD:**
> Today every trip plan triggers two upstream API calls (Régie Essence + Google Maps) and one disk read. The app works for a single developer; it will not survive a launch announcement, a Reddit post, or a single bot scrape. The ADK service URL is hardcoded to localhost — the first deploy will fail. There is no way to correlate a user-reported error with backend logs.

**Product outcomes to commit to:**
- gaz_eye can serve N concurrent users without exceeding Y Régie Essence requests per minute.
- A user-reported issue can be traced end-to-end in under 5 minutes.
- Deploying to a non-localhost environment requires zero code changes.

**Candidate non-goals:** auto-scaling, CDN, multi-region. (Premature for current traffic.)

---

### Theme B — Agent Contract Unification ("One source of truth for what the assistant can do")

**Problem framing for PRD:**
> The conversational assistant exposes four actions (`submit_trip`, `add_waypoint`, `filter_stations_by_area`, `clear_filter`). Each is defined in **three independent places**: the ADK tool stub, the backend whitelist, and the frontend dispatcher. Any change requires editing three files in lockstep, and drift is silent — the agent could ask for a parameter the frontend ignores, or vice versa. This blocks adding new agent capabilities safely.

**Product outcomes to commit to:**
- Adding a new assistant capability is a single-file change.
- An agent action with a malformed payload is rejected with a diagnosable error, not silently misapplied.
- Frontend, backend, and agent share a single contract definition.

**Why this is a PRD-level decision, not a refactor:** it determines the **rate at which new agent features can ship**. Every future agent capability (route explanation, anomaly Q&A, trip post-mortems, multi-stop planning) compounds the cost of leaving this as-is.

---

### Theme C — Agent State Honesty ("Stop force-feeding the assistant context behind the user's back")

**Problem framing for PRD:**
> When a user submits a trip via the form, the frontend silently POSTs the trip parameters to the chat endpoint as if the user had typed them. This pollutes the conversation transcript with messages the user never wrote, and inverts the agent's natural model (push notifications instead of tool calls). The assistant cannot reason honestly about "what does the user currently have on screen?" because that information arrives out-of-band.

**Product outcomes to commit to:**
- The assistant's transcript reflects only what the user actually wrote or saw.
- When the assistant needs to know "what's the current trip?", it asks for it via a tool call.
- Trip state is owned by a session store, not by a side-channel POST.

**User-visible benefit:** when the user later asks "what was that destination again?", the agent can answer correctly without the user having to repeat themselves — and without ever showing them a hallucinated "user message."

---

### Theme D — Frontend Modularity ("Prevent the god-module before it lands")

**Problem framing for PRD:**
> `app.js` is at ~620 lines and growing — it handles form logic, card rendering, settings drawer, error banner, reachability banner, timestamp, skeletons, and low-range indicators. `map.js` keeps Google Maps state in module-level globals, which prevents a second map instance and complicates teardown. New frontend features will start slowing down within the next 2–3 epics if left unchecked.

**Product outcomes to commit to:**
- A new frontend feature does not require touching a file > 400 LOC.
- The map can be unit-tested in isolation.
- Chat-to-map interactions go through one well-known channel, not direct function imports.

**This is the only theme that has no user-visible change.** Decide if you want to fund it now (cheap), defer (medium cost later), or skip (will not block any single feature but will tax all of them).

---

### Theme E — Legacy Cleanup ("Stop maintaining the same code twice")

**Problem framing for PRD:**
> `gaz_saver.py` is an orphaned 320-line CLI that duplicates the Régie Essence fetching and price-parsing logic now living in `api/pricing.py`. It is not imported by the Flask app. Any fix to the GeoJSON handling must be made twice or risk divergence.

**Decision required from product:** is `gaz_saver.py` still a deliverable (e.g. a cron-job artifact for self-hosters), or is it dead? If dead, delete it. If alive, extract a shared client and document the CLI as a first-class deliverable in the PRD.

---

## 3. The Headline Strategic Question

Found during the review and worth explicit PRD-level positioning:

> **Should other features (mapping, pricing) adopt the same "ADK agent + microservice" pattern as chat?**

**My architectural recommendation:** No, with one caveat. Mapping and pricing are deterministic and fast — wrapping them in an LLM or a separate service would add latency, cost, and non-determinism with zero benefit. **But the agent should be able to *call* them as tools** (e.g. "explain why route 2 ranked lower," "why was station X hidden as stale?"). This is Theme B's natural extension.

**What I need from you (PM):**
- Endorse or push back on this positioning so it can be written into the PRD's "Architecture Principles" section.
- Decide whether "agent-callable explanations" (route ranking rationale, anomaly Q&A) belongs on the near-term roadmap or is a future bet.

---

## 4. Suggested Epic Structure

This is a starting point, not a directive. Re-shape freely.

### Option 1 — Single mega-epic ("Foundations Hardening")
One epic, ~5 stories, covers Themes A + B + E. Simpler to track; risks getting stuck behind any one blocker.

### Option 2 — Two epics (**my recommended split**)

**Epic X — "Operational Foundations"** (Themes A + E)
- Story: Upstream response caching with TTL (Régie Essence, YAML config)
- Story: Environment-driven configuration (ADK service URL, future config)
- Story: End-to-end request correlation IDs
- Story: Decide & execute `gaz_saver.py` disposition (delete or extract shared client)
- *Why grouped:* all are pre-deploy hygiene with no user-visible feature change; ship them as one batch before the next user-facing epic.

**Epic Y — "Assistant Contract & Honesty"** (Themes B + C)
- Story: Single-source-of-truth action contract (shared schema, generated stubs/validators)
- Story: Replace silent context-update with session-backed `get_current_trip()` tool
- Story: Schema validation on `/api/plan` and `/api/chat` boundaries
- *Why grouped:* both unblock future agent capabilities; together they define how the assistant evolves.

**Theme D (Frontend Modularity)** — recommend handling as **continuous refactor inside whichever epic next touches `app.js` or `map.js`**, with a story-level "leave it better than you found it" acceptance criterion. Don't make it its own epic unless you want to fund it explicitly.

### Option 3 — Per-theme epics
Most granular, highest tracking overhead. Recommend against unless you need fine-grained release notes.

---

## 5. Sequencing Guidance

If you pick Option 2:
1. **Epic X first.** It unblocks deployment. Until it ships, every feature epic is theoretical because nothing can actually go live.
2. **Epic Y second.** It unblocks the next wave of agent features (and most of the post-MVP backlog leans on the assistant).
3. **Theme D** rides along as a non-negotiable acceptance criterion on any frontend-touching story.

**Hard dependency:** the agent-context honesty story (Theme C) depends on having request correlation IDs in place (Theme A), because debugging session-state issues without them is brutal.

---

## 6. Success Criteria Candidates (for the PRD)

Pick the ones that fit your style; rewrite freely.

| Theme | Candidate success metric |
|---|---|
| A — Operational | p95 `/api/plan` latency drops by ≥X% after caching; deploy to staging completes with zero code edits |
| A — Observability | 100% of `/api/plan` and `/api/chat` responses carry a request ID echoed in logs |
| B — Agent contract | Adding a new agent action requires modifying ≤1 file; CI fails if action stubs and validators drift |
| C — Agent honesty | Chat transcripts contain zero auto-generated "user" messages; assistant can answer "what's my current destination?" correctly after a form submit |
| D — Frontend | No JS file exceeds 400 LOC; map module is instantiable as a factory, not a singleton |
| E — Legacy | `gaz_saver.py` is either deleted or has zero duplicated code with `api/pricing.py` |

---

## 7. What I'm *Not* Recommending (yet)

So you can rule these in or out explicitly rather than them lurking as ambiguity:

- **TypeScript migration** — frontend is at 1290 LOC; cost grows linearly. Worth re-evaluating at ~2500 LOC.
- **Splitting pricing/geo into microservices** — premature; current Python modules are fast and stateless.
- **Real ML model for stale price detection** — current density-adaptive heuristic is working; revisit when price history persistence exists.
- **Cloudflare-edge-cached Régie data** — clear win, but ops overhead; defer until cache hit rate proves the need.
- **Streaming `/api/chat` (SSE)** — UX win, but additive; not a foundation issue.
- **Shareable trip URLs** — pure product feature, belongs in a product roadmap conversation, not this hand-off.

If any of these *should* be in scope, please add them — but they are product calls, not architecture calls.

---

## 8. Open Questions for You (John)

Before you draft the epic(s), I'd recommend deciding on these:

1. **`gaz_saver.py` disposition** — feature or legacy? (Required to scope Theme E.)
2. **Deploy target & timeline** — knowing this calibrates how aggressive Theme A needs to be (in-memory cache vs. Redis vs. external CDN).
3. **Agent roadmap appetite** — are we planning to grow the assistant's capabilities materially in the next 2 epics? If yes, Theme B is critical-path; if no, it can wait.
4. **Frontend refactor funding model** — explicit story vs. ride-along acceptance criterion? (Affects Theme D.)
5. **Public commitment** — do any of these themes need to be communicated to users/stakeholders (e.g. "we improved accuracy"), or are they purely internal?

---

## 9. Hand-Off Checklist

When you (John) pick this up, the natural flow is:

- [ ] Read [architecture-review-2026-05-31.md](../architecture-review-2026-05-31.md) for the full evidence behind each theme.
- [ ] Answer §8's open questions (drag me back in if you want to discuss).
- [ ] Decide which themes are in scope.
- [ ] Update [prd.md](prd.md) — add the chosen themes as features/requirements + the "Architecture Principles" stance from §3.
- [ ] Update [epics.md](epics.md) — create the epic(s) per your chosen option.
- [ ] Run `bmad-check-implementation-readiness` once epics are drafted so we catch contract gaps before stories.

---

**End of input.** I'm available for clarification, trade-off discussion, or to draft any technical sub-section you want included verbatim.

— Winston 🏗️
