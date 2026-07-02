# Roadmap and Decisions

## Table of Contents

- [Product Direction](#product-direction)
- [MVP Roadmap](#mvp-roadmap)
- [Later Roadmap](#later-roadmap)
- [Non-Negotiable Constraints](#non-negotiable-constraints)
- [Decision Record](#decision-record)

## Product Direction

Calis App should first prove that users will record short exercise clips,
understand structured feedback, and improve through repeat attempts.

> Record a short calisthenics clip and get clear, supportive feedback for your
> next attempt.

Comeback and low-pressure consistency features support this analysis loop rather
than define the MVP.

## MVP Roadmap

1. Build one responsive Next.js App Router application with basic PWA support,
   profile setup, and server-side credentials.
2. Add push-up, squat, plank, lunge, and hollow hold with recording and safety
   guidance.
3. Support short browser recording or upload with client and server validation.
4. Process video transiently through a Gemini-first Vision provider adapter.
5. Normalize observations and apply exercise rules, confidence scoring, and
   feedback prioritization in the analysis engine.
6. Generate coaching from structured evidence only, then validate schema,
   supported scope, safety, and language.
7. Show checklist feedback with positive notes, retry, and save-result actions.
8. Add metadata-only history, repeated-issue summaries, and lightweight comeback
   prompts.

## Later Roadmap

- Browser-side MediaPipe quality checks for framing, visibility, and clip
  usability.
- Before-and-after comparison and a validated broader exercise library.
- Optional scoring or readiness indicators without false certainty or shame.
- Exercise explainers, comeback coaching, and weekly reflections.
- Workout generation from approved exercises.
- Optional video retention with separate explicit consent.
- Developer API-key mode, richer PWA features, and native mobile after demand is
  validated.

## Non-Negotiable Constraints

- Use after-recording analysis, not live feedback.
- Analyze only supported exercises and visible evidence.
- Keep provider credentials and AI calls server-side.
- Treat the analysis engine as the source of truth; coaching cannot alter
  evidence.
- Validate all output before display and request a better clip when confidence
  is inadequate.
- Store metadata and feedback, not raw video, by default.
- Avoid diagnosis, treatment, injury claims, unsafe advice, and shame-based
  language.
- Use one Next.js codebase for the MVP. Add a Python sidecar only if future
  server-side pose estimation requires it.

Implementation details are defined in [Technical Plan](TECHNICAL_PLAN.md).
Product behavior and safety requirements are defined in
[Product Spec](PRODUCT_SPEC.md).

## Decision Record

| ID | Decision | Reason |
|---|---|---|
| 001 | Center the MVP on AI-assisted form analysis | It is the product's primary differentiator and validation target |
| 002 | Use Next.js App Router with PWA capabilities | It supports the UI, route handlers, server-side AI calls, and installability in one stack |
| 002A | Treat PWA as an enhancement | PWA features belong in the same application, not a separate implementation |
| 003 | Analyze completed recordings instead of providing live feedback | Post-recording analysis is simpler, safer, and easier to validate |
| 004 | Limit the MVP to five exercises | A narrow scope keeps rules, prompts, and quality testable |
| 005 | Use a backend Gemini-first Vision provider adapter | Native video preserves temporal context while server integration protects credentials and centralizes controls |
| 006 | Process videos transiently and discard originals | Exercise footage is sensitive; the MVP needs results, not a raw video library |
| 007 | Use checklist feedback instead of score-first feedback | Specific corrections are more actionable and avoid false precision |
| 008 | Keep comeback support secondary | It should encourage return to practice without distracting from the analysis loop |
| 009 | Validate every AI response before display | Output must satisfy schema, evidence, exercise-scope, and safety rules |
| 010 | Defer MediaPipe to a later browser quality gate | It may reduce unusable submissions but is not the primary analyzer |
| 011 | Defer native mobile | Validate demand with the web experience before creating another client |
| 012 | Use no separate backend service for the MVP | Next.js route handlers cover orchestration; future pose workloads may use a sidecar |

Provider models, capabilities, quotas, pricing, and retention terms must be
verified during implementation rather than fixed in this decision record.
