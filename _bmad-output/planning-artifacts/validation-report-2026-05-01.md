---
validationTarget: '_bmad-output/planning-artifacts/prd.md'
validationDate: '2026-05-01'
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/product-brief-gaz_eye.md
  - _bmad-output/planning-artifacts/product-brief-stale-price-filter.md
  - _bmad-output/project-context.md
  - docs/project-overview.md
  - docs/architecture.md
  - docs/development-guide.md
  - docs/source-tree-analysis.md
  - docs/index.md
validationStepsCompleted:
  - step-v-01-discovery
  - step-v-02-format-detection
  - step-v-03-density-validation
  - step-v-04-brief-coverage-validation
  - step-v-05-measurability-validation
  - step-v-06-traceability-validation
  - step-v-07-implementation-leakage-validation
  - step-v-08-domain-compliance-validation
  - step-v-09-project-type-validation
  - step-v-10-smart-validation
  - step-v-11-holistic-quality-validation
  - step-v-12-completeness-validation
validationStatus: COMPLETE
holisticQualityRating: '4/5 - Good'
overallStatus: Warning
---

# PRD Validation Report

**PRD Being Validated:** `_bmad-output/planning-artifacts/prd.md`
**Validation Date:** 2026-05-01

## Input Documents

- `_bmad-output/planning-artifacts/prd.md` ✓
- `_bmad-output/planning-artifacts/product-brief-gaz_eye.md` ✓
- `_bmad-output/planning-artifacts/product-brief-stale-price-filter.md` ✓
- `_bmad-output/project-context.md` ✓
- `docs/project-overview.md` ✓
- `docs/architecture.md` ✓
- `docs/development-guide.md` ✓
- `docs/source-tree-analysis.md` ✓
- `docs/index.md` ✓

## Validation Findings

## Format Detection

**PRD Structure (all ## Level 2 headers):**
1. Executive Summary
2. Project Classification
3. Success Criteria
4. Product Scope
5. User Journeys
6. Web Application Specific Requirements
7. Project Strategy
8. Functional Requirements
9. Non-Functional Requirements

**BMAD Core Sections Present:**
- Executive Summary: Present ✓
- Success Criteria: Present ✓
- Product Scope: Present ✓
- User Journeys: Present ✓
- Functional Requirements: Present ✓
- Non-Functional Requirements: Present ✓

**Format Classification:** BMAD Standard
**Core Sections Present:** 6/6

## Information Density Validation

**Anti-Pattern Violations:**

**Conversational Filler:** 0 occurrences

**Wordy Phrases:** 0 occurrences

**Redundant Phrases:** 0 occurrences

**Total Violations:** 0

**Severity Assessment:** Pass

**Recommendation:** PRD demonstrates excellent information density. Direct, dense language throughout — "System can..." and "User can..." FR patterns, no passive filler. User Journey narratives are appropriately functional rather than padded.

## Product Brief Coverage

**Product Briefs:** `product-brief-gaz_eye.md`, `product-brief-stale-price-filter.md`

### Coverage Map — product-brief-gaz_eye.md

**Vision Statement:** Fully Covered — Executive Summary
**Target Users:** Fully Covered — Executive Summary + Journey 1
**Problem Statement (5 pain points):** Fully Covered — "What Makes This Special" + User Journeys
**Key Features (routes, corridor, autonomy, map, savings):** Fully Covered — FR1–FR37
**Goals/Objectives (5 success criteria):** Fully Covered — Success Criteria section
**Differentiators (5 bullets):** Fully Covered — "What Makes This Special" + anomaly filter bullet
**Scope (In/Out):** Fully Covered — Product Scope section
**Technical Risks (6 rows):** Fully Covered — Risk Mitigation table

### Coverage Map — product-brief-stale-price-filter.md

**Vision (spatial anomaly detection):** Fully Covered — "Data you can trust" bullet + FR38–FR42
**Problem (stale prices distort recommendations):** Partially Covered — implicit in FR38; not stated as standalone problem statement (acceptable for additive feature, no severity concern)
**Density-adaptive radius (5→50 km, ≥5 neighbors):** Fully Covered — FR39
**float('inf') sentinel exclusion:** Fully Covered — FR38
**Structural discounter exemption list:** Fully Covered — FR40 + Product Scope
**Kill switch (anomaly_filter_enabled):** Fully Covered — FR41
**Structured log entry:** Fully Covered — FR42
**Success criterion: ≥1 logged exclusion confirmed as true positive in 4 weeks:** Not Found — **Moderate gap** (operational validation criterion present in brief, absent from PRD Measurable Outcomes)
**Known limitations (clustered staleness, price-drop inversion):** Not Found — **Informational gap** (brief explicitly calls these out; PRD has no constraints/limitations section)
**Configurable threshold constant (ANOMALY_THRESHOLD_CAD):** Not Found — Informational (implementation detail; appropriate to omit from PRD)

### Coverage Summary

**Overall Coverage:** ~95%
**Critical Gaps:** 0
**Moderate Gaps:** 1 — anomaly filter 4-week true-positive validation criterion not in Measurable Outcomes
**Informational Gaps:** 2 — known limitations (clustered staleness, price-drop inversion) not captured; anomaly threshold constant omitted (acceptable)

**Recommendation:** PRD provides strong coverage of both product briefs. Add the 4-week operational validation criterion to Measurable Outcomes and consider a brief "Known Limitations" note for clustered staleness and price-drop inversion.

## Measurability Validation

### Functional Requirements

**Total FRs Analyzed:** 42

**Format Violations:** 0
All 42 FRs use `[Actor] can [capability]` pattern correctly.

**Subjective Adjectives Found:** 1
- FR37: "user-friendly messages" — should use a specific, testable descriptor (e.g., "display an error message identifying the failure type")

**Vague Quantifiers Found:** 0

**Implementation Leakage:** 9 (informational)
- FR7: "Google Maps Directions API" named (capability-relevant, low concern)
- FR10: "route polylines" — algorithmic term in capability statement
- FR11: "GeoJSON dataset" — data format in capability statement
- FR12: "Haversine" — distance algorithm named
- FR13: "cent-string format" — internal data format detail
- FR38: "`float('inf')` sentinel" — Python-specific implementation value
- FR39: **Warning** — Full density-adaptive algorithm steps (5→10→20→50 km expansion, minimum 5 neighbors) described as an FR; this specifies implementation, not just capability. The testable capability is "density-adaptive radius that expands until sufficient neighbors are found."
- FR40: "`stations.yaml`" file named
- FR41: "boolean flag (`anomaly_filter_enabled`) in `stations.yaml`" — both data type and config file named

**FR Violations Total:** 2 Warning (FR37, FR39) + 9 Informational

### Non-Functional Requirements

**Total NFRs Analyzed:** 11

**Missing Metrics:** 1
- NFR2: "renders without visible lag or jank" — no numeric criterion. Should specify a measurable threshold (e.g., "initial render completes within 500ms" or "maintains ≥30fps during pan/zoom")

**Implementation Leakage in NFRs:** 4 (Warning — these belong in Architecture)
- NFR7: Specifies `alternatives=true` API parameter value — this is an integration implementation detail
- NFR8: "dual-parse strategy" (gzip fallback) — implementation approach, not a quality attribute
- NFR9: "browser-like User-Agent header" — integration constraint, belongs in Architecture
- NFR10: "Google Maps JavaScript API is used for map rendering to comply with ToS" — SDK choice forced as NFR; the ToS compliance requirement is valid but the mechanism belongs in Architecture

**NFR Violations Total:** 5 Warning (NFR2 + NFR7/8/9/10)

### Overall Assessment

**Total Requirements:** 53 (42 FR + 11 NFR)
**Total Warning-Level Violations:** 7 (FR37, FR39, NFR2, NFR7, NFR8, NFR9, NFR10)
**Total Informational Violations:** 9 (implementation leakage in FRs)

**Severity:** Warning (5–10 violations)

**Recommendation:** Refine FR37 to remove "user-friendly." Rework FR39 to state the capability rather than the algorithm. Consider moving NFR7–NFR10 to the Architecture document as integration constraints — their content is more precise there. Add a numeric metric to NFR2.

## Traceability Validation

### Chain Validation

**Executive Summary → Success Criteria:** Intact ✓
Vision (route+fuel comparison, anomaly filter data trustworthiness) maps cleanly to all Success Criteria sections including new Measurable Outcomes for the anomaly filter.

**Success Criteria → User Journeys:** Intact ✓
All 4 criteria groups (three-route comparison, reachable stations, waypoint, no stations.yaml) are exercised by the 4 User Journeys. Anomaly filter trustworthiness criteria are implicitly supported by Journeys 1 and 3.

**User Journeys → Functional Requirements:** Partial gap — Warning
FR1–FR37 all trace to at least one User Journey via the Journey Requirements Summary table.
**FR38–FR42 (Price Quality Filtering) are not covered by any User Journey.** No journey describes a stale-price scenario, a filtered station, or the anomaly detection operating. These FRs trace to Executive Summary and Measurable Outcomes (valid business-objective traceability) but lack a User Journey source.

**Scope → FR Alignment:** Intact ✓
Every MVP scope item maps to corresponding FRs. No scope items without FRs; no FRs outside MVP scope.

### Orphan Elements

**Orphan Functional Requirements:** 5 (FR38, FR39, FR40, FR41, FR42)
These requirements have no User Journey that triggers or exercises them. They trace to the Executive Summary "Data you can trust" bullet and Measurable Outcomes, but the chain Executive Summary → Success Criteria → User Journey → FR is broken at the User Journey link.

**Unsupported Success Criteria:** 0

**User Journeys Without FRs:** 0

### Traceability Matrix

| FR Group | Source Journey | Status |
|---|---|---|
| FR1–FR6 Trip Input | J1, J2, J3, J4 | ✓ Covered |
| FR7–FR10 Route Discovery | J1, J2, J3, J4 | ✓ Covered |
| FR11–FR15 Station Discovery | J1, J2, J3, J4 | ✓ Covered |
| FR38–FR42 Price Quality Filtering | None | ⚠ No User Journey |
| FR16–FR18 Autonomy Filtering | J1, J3 | ✓ Covered |
| FR19–FR23 Recommendation Engine | J1, J2, J3, J4 | ✓ Covered |
| FR24–FR27 Map Visualization | J1, J2, J3, J4 | ✓ Covered |
| FR28–FR30 Recommendation Display | J1, J2, J3, J4 | ✓ Covered |
| FR31–FR34 Configuration | J1, J2, J3, J4 | ✓ Covered |
| FR35–FR37 Error Handling | J3 primary | ✓ Covered |

**Total Traceability Issues:** 1 (1 FR group — 5 FRs — lacking User Journey source)

**Severity:** Warning

**Recommendation:** Add a brief "Journey 5: Trustworthy Recommendation" scenario to User Journeys — e.g., Olivier loads the app on a corridor where one station's price is anomalously low, the filter silently excludes it, and the recommendation reflects current market pricing. This closes the FR38–FR42 traceability gap and makes the anomaly filter's value concrete.

## Implementation Leakage Validation

### Leakage by Category

**Frontend Frameworks:** 0 violations ✓
**Backend Frameworks:** 0 violations ✓
**Databases:** 0 violations ✓
**Cloud Platforms:** 0 violations ✓
**Infrastructure:** 0 violations ✓
**Libraries:** 0 violations ✓

**Other Implementation Details:** 10 violations

*New anomaly filter FRs (Warning):*
- FR38: `` `float('inf')` sentinel`` — Python-specific implementation value; capability statement should say "exclude from recommendations" without specifying the mechanism
- FR39: Algorithm expansion steps (5→10→20→50 km sequence) — specifies HOW the radius is computed, not WHAT the system must do. Rewrite: "System can compute a local median price using a density-adaptive neighbor search that expands radius until a minimum of 5 neighbors are found (up to 50 km)"
- FR40: `` `stations.yaml` `` file name — implementation artifact; capability is "configurable exemption list" without naming the config file
- FR41: "boolean flag (`anomaly_filter_enabled`) in `stations.yaml`" — data type and file name both leaked; capability is "anomaly filter can be disabled without a code deploy"

*Existing FRs (Informational — capability-relevant or minor):*
- FR12: "Haversine" — distance formula named; the capability ("configurable corridor distance from route") is clear regardless
- FR13: "cent-string format" — internal data representation from the upstream source; acceptable context for this personal tool
- FR7: "Google Maps Directions API" — capability-defining service; acceptable boundary case

*NFRs (Warning — these belong in Architecture):*
- NFR7: `` `alternatives=true` parameter`` — API parameter value, not a quality attribute
- NFR8: "dual-parse strategy" — implementation approach, not an NFR
- NFR9: "browser-like User-Agent header" — HTTP integration detail
- NFR10: "Google Maps JavaScript API is used for map rendering" — SDK choice; ToS compliance is a valid constraint, but this specific SDK decision belongs in Architecture

### Summary

**Total Implementation Leakage Violations:** 10
- **Warning:** 6 (FR38, FR39, FR40, FR41, NFR7, NFR8, NFR9, NFR10 — split into 2 FR + 4 NFR)
- **Informational:** 3 (FR12, FR13, FR7)

**Severity:** Warning (2–5 meaningful violations)

**Recommendation:** Rephrase FR38–FR41 to remove Python-specific values, algorithm steps, and config file names — express capabilities only. Move NFR7–NFR10 to the Architecture document as Integration Constraints; replace them in the NFR section with the observable quality attribute (e.g., "System supports requests for 3 alternative routes per query").

## Domain Compliance Validation

**Domain:** General
**Complexity:** Low (general/standard)
**Assessment:** N/A — No special domain compliance requirements

**Note:** gaz_eye is a personal utility with no regulated domain requirements (no healthcare, fintech, GovTech, etc.).

## Project-Type Compliance Validation

**Project Type:** web_app

### Required Sections

**Browser Matrix:** Present ✓ — "Latest Chrome or Safari on macOS only (single user's laptop)"
**Responsive Design:** Present ✓ — "Desktop-first; mobile layout is a nice-to-have but not required" (scoped decision, explicitly documented)
**Performance Targets:** Present ✓ — NFR1 (5s end-to-end), NFR3 (3s GeoJSON fetch), NFR4 (1s corridor matching), NFR11 (100ms anomaly filter)
**SEO Strategy:** Present ✓ — "Not applicable — locally hosted, no public URL" (explicitly scoped out)
**Accessibility Level:** Present ✓ — "Not a priority for v1 (single user, personal tool)" (explicitly scoped out)

### Excluded Sections (Should Not Be Present)

**native_features:** Absent ✓
**cli_commands:** Absent ✓ (gaz_saver.py CLI is the predecessor tool, not referenced as a requirement)

### Compliance Summary

**Required Sections:** 5/5 present
**Excluded Sections Present:** 0
**Compliance Score:** 100%

**Severity:** Pass

**Recommendation:** Full web_app project-type compliance. All required sections are present and accounted for — including explicit N/A scoping for SEO and accessibility, which is appropriate for a personal locally-hosted tool.

## SMART Requirements Validation

**Total Functional Requirements:** 42

### Scoring Summary

**All scores ≥ 3:** 85.7% (36/42)
**All scores ≥ 4:** 83.3% (35/42)
**Overall Average Score:** ~4.3/5.0

### Flagged FRs (any score < 3)

| FR | Specific | Measurable | Attainable | Relevant | Traceable | Avg | Flag |
|----|----------|------------|------------|----------|-----------|-----|------|
| FR37 | 3 | 2 | 5 | 5 | 4 | 3.8 | M < 3 |
| FR38 | 4 | 4 | 5 | 5 | 2 | 4.0 | T < 3 |
| FR39 | 2 | 4 | 5 | 5 | 2 | 3.6 | S < 3, T < 3 |
| FR40 | 4 | 4 | 5 | 5 | 2 | 4.0 | T < 3 |
| FR41 | 3 | 5 | 5 | 5 | 2 | 4.0 | T < 3 |
| FR42 | 5 | 5 | 5 | 5 | 2 | 4.4 | T < 3 |

*FR1–FR36 (excluding FR37): All scores ≥ 3 across all SMART criteria.*
*Legend: 1=Poor, 3=Acceptable, 5=Excellent. Flag = any score < 3.*

### Improvement Suggestions

**FR37:** Replace "user-friendly messages" with specific behavior — e.g., "display an error message identifying the error type (invalid address, quota exceeded, unavailable) and a suggested corrective action."

**FR38:** Traceability (T=2) — add User Journey 5 (stale-price scenario) to close the gap. Also remove `` `float('inf')` sentinel`` — rewrite ending as "...and exclude them from recommendations." The exclusion mechanism belongs in Architecture.

**FR39:** (1) Rewrite as capability: "System can compute a density-adaptive local median price by expanding the neighbor search radius until a minimum neighbor count is found, up to a maximum radius; stations below the minimum neighbor threshold bypass the filter." Remove specific km values — those are architecture/config. (2) Add User Journey 5 to close Traceable gap.

**FR40:** Add User Journey 5. Remove "`stations.yaml`" — rewrite as "configurable name-based exemption list."

**FR41:** Replace "boolean flag (`anomaly_filter_enabled`) in `stations.yaml`" with "configurable toggle." Add User Journey 5.

**FR42:** Add User Journey 5 to close Traceable gap. (Content is otherwise excellent — specific, measurable, attainable, relevant.)

### Overall Assessment

**Flagged FRs:** 6/42 (14.3%)
**Severity:** Warning (10–30% flagged)

**Root cause:** Five of the six flags (FR38–FR42) share the same root cause — no User Journey source. All five are cured by a single fix: add Journey 5 (stale-price correction scenario) to the User Journeys section. The remaining flag (FR37) is a standalone word-choice fix.

**Recommendation:** Add User Journey 5, fix FR37 wording, and clean implementation references from FR38–FR41. This resolves all 6 flagged items.

## Holistic Quality Assessment

### Document Flow & Coherence

**Assessment:** Good

**Strengths:**
- Cohesive narrative arc — personal problem, concrete solution, competitive moat, phased delivery
- "What Makes This Special" is a strong, scannable executive hook
- User Journey scenarios are specific and realistic (named protagonist, real corridor, real range numbers)
- Journey Requirements Summary table is an excellent cross-reference artifact
- Risk table at appropriate depth for a personal tool — not over-engineered

**Areas for Improvement:**
- "Project Strategy" / Risk Mitigation section sits between User Journeys and Functional Requirements — slightly interrupts the flow from journeys to requirements. Moving it to after NFRs would improve readability.

### Dual Audience Effectiveness

**For Humans:**
- Executive-friendly: Excellent — "What Makes This Special" conveys value proposition in 30 seconds
- Developer clarity: Strong — Implementation Considerations, NFRs, and risk table give concrete signals
- Designer clarity: Good — 4 concrete journey scenarios with named user, specific routes, and explicit capability tables
- Stakeholder decision-making: Clear — Phase 1/2/3 phasing and risk table support scope decisions

**For LLMs:**
- Machine-readable structure: Strong — consistent headers, numbered FRs, grouped by function, cross-reference tables
- UX readiness: Good — 4 journeys sufficient for UX generation; a 5th journey (anomaly filter scenario) would make the data-trust requirement actionable for a UX designer
- Architecture readiness: Excellent — Integration Considerations, NFRs, and risk table provide direct architecture signals
- Epic/Story readiness: Very good — FR groups (Trip Input, Route Discovery, Station Discovery, Price Quality Filtering, Autonomy, Recommendation, Map, Display, Config, Errors) map directly to epics

**Dual Audience Score:** 4/5

### BMAD PRD Principles Compliance

| Principle | Status | Notes |
|---|---|---|
| Information Density | Met ✓ | 0 anti-pattern violations |
| Measurability | Partial | NFR2 ("visible lag or jank") has no numeric metric; FR37 uses "user-friendly" |
| Traceability | Partial | FR38–FR42 trace to Executive Summary but have no User Journey source |
| Domain Awareness | Met ✓ | N/A appropriately documented for general/personal-tool domain |
| Zero Anti-Patterns | Met ✓ | 0 filler, 0 wordy phrases, 0 redundant phrases |
| Dual Audience | Met ✓ | Effective for both human stakeholders and LLM consumption |
| Markdown Format | Met ✓ | Proper structure, ## headers, tables, numbered FRs |

**Principles Met:** 5/7

### Overall Quality Rating

**Rating:** 4/5 — Good

*Strong, production-quality PRD with two specific fixes needed to reach Excellent.*

### Top 3 Improvements

1. **Add User Journey 5: "Trustworthy Recommendation on a Stale-Price Corridor"**
   Olivier uses gaz_eye on the Montréal → Laurentians corridor. One station appears cheapest by 7¢/L. The anomaly filter silently excludes it (price below local median). The recommendation reflects current market pricing without user intervention. Olivier arrives at the recommended station and pays the displayed price.
   *Why:* Closes the traceability gap for FR38–FR42, fixes all 5 SMART T-flags, and makes the anomaly filter's value concrete for both designers and LLMs consuming this PRD.

2. **Move NFR7–NFR10 to Architecture as Integration Constraints; replace with observable NFRs**
   NFR7 (`alternatives=true`), NFR8 (dual-parse strategy), NFR9 (User-Agent header), NFR10 (Google Maps JS API SDK choice) are implementation decisions, not quality attributes. They belong in the Architecture doc as integration constraints. Replace in the PRD with the observable quality: e.g., "System supports fetching 3 alternative route options per trip query" and "System handles Régie Essence endpoint failures gracefully."
   *Why:* Removes the largest implementation leakage cluster (4 NFRs) and improves Architecture-readiness for LLM consumers.

3. **Add 4-week operational validation criterion + Known Limitations note to anomaly filter coverage**
   Add to Measurable Outcomes: "After 4 weeks of operation, at least one logged exclusion is manually confirmed as a true positive by cross-referencing against a secondary source on the same day."
   Add a brief Known Limitations paragraph (or bullets in Scope/Out section): "Clustered staleness — if all stations in a rural corridor are simultaneously stale, the local median is also stale and the filter finds no anomaly. Price-drop inversion — stations that update quickly during a price drop will be priced below slower-updating neighbors and may be incorrectly excluded."
   *Why:* Closes the moderate brief-coverage gap, sets a concrete field-validation bar for the anomaly filter, and surfaces the two documented failure modes for architecture and implementation consumers.

### Summary

**This PRD is:** A high-quality, information-dense document that effectively communicates the gaz_eye vision and requirements — with a single root-cause fix (User Journey 5) that would resolve the majority of remaining findings in a single edit.

**To make it great:** Implement the 3 improvements above.

## Completeness Validation

### Template Completeness

**Template Variables Found:** 0 ✓
No unfilled template variables remaining. One intentional `TBD` marker (line 224: web framework choice deferred to architecture phase) — appropriate, not a completeness gap.

### Content Completeness by Section

**Executive Summary:** Complete ✓
**Success Criteria:** Complete ✓ — User, Business, Technical, and Measurable Outcomes all present
**Product Scope:** Complete ✓ — MVP, Phase 2, Phase 3, and Out-of-scope all defined
**User Journeys:** Complete ✓ — 4 concrete journeys + Journey Requirements Summary table (Journey 5 is a quality improvement recommendation, not a completeness gap)
**Functional Requirements:** Complete ✓ — 42 FRs in 10 named groups
**Non-Functional Requirements:** Complete ✓ — 11 NFRs across Performance, Security, Integration

### Section-Specific Completeness

**Success Criteria Measurability:** All measurable ✓ — Measurable Outcomes contain numeric criteria
**User Journeys Coverage:** Complete for the single-user product ✓ — 4 scenarios covering happy path, waypoint, urgency, and urban cases
**FRs Cover MVP Scope:** Yes ✓ — all MVP scope items map to at least one FR
**NFRs Have Specific Criteria:** Some — NFR2 ("without visible lag or jank") lacks a numeric metric

### Frontmatter Completeness

**stepsCompleted:** Present ✓ (15 steps recorded including edit and validation)
**classification:** Present ✓ (projectType: web_app, domain: general, complexity: low)
**inputDocuments:** Present ✓ (9 source documents tracked)
**lastEdited / editHistory:** Present ✓ (2026-05-01 with change summary)

**Frontmatter Completeness:** 5/5 ✓

### Completeness Summary

**Overall Completeness:** 98% (all sections complete; 1 NFR metric gap)
**Critical Gaps:** 0
**Minor Gaps:** 1 (NFR2 missing numeric metric)

**Severity:** Pass

**Recommendation:** PRD is essentially complete. Address NFR2 metric as part of the broader NFR cleanup recommended in step 7 (moving NFR7–NFR10 to Architecture).
