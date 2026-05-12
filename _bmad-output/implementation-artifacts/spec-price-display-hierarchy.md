---
title: 'Promote full-tank savings to primary display'
type: 'feature'
created: '2026-05-12'
status: 'done'
route: 'one-shot'
---

## Intent

**Problem:** The per-litre savings (e.g. "Save 12.0 ¢/L") was displayed prominently in large green text, while the full-tank dollar savings (e.g. "≈ Save $7.20") — the more decision-relevant figure — was rendered as small grey secondary text.

**Approach:** Swap the visual hierarchy: demote the ¢/L line to small grey and promote the $ full-tank savings to large bold green. When no tank size is configured (tankSavings is null), fall back to showing the ¢/L line prominently so the accent callout is never lost.

## Suggested Review Order

- [static/js/app.js](../../static/js/app.js#L313) — savings display block in `renderCard()`: verify style swap and null-fallback logic
