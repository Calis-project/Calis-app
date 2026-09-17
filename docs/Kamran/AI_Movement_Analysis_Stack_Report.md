# AI Movement Analysis Stack: Superseded Gemini-First Proposal

*Prepared: June 2026*

> [!IMPORTANT]
> **Status:** Superseded historical proposal; not a current architecture decision.
>
> **Owns:** The rationale and assumptions of the June 2026 Gemini-first proposal.
>
> **Does not own:** Current product scope, pending architecture evaluation, or an
> accepted implementation architecture.
>
> **Last reviewed:** 24 August 2026.
>
> **Precedence:** [Product Spec](PRODUCT_SPEC.md) owns current product scope, and
> [Candidate Architecture Patterns and Evaluation Plan](CANDIDATE_ARCHITECTURE_PATTERNS_AND_EVALUATION_PLAN.md)
> owns the pending architecture comparison. Those documents prevail wherever
> this historical report conflicts with them.
>
> All architecture and requirement language below describes the June 2026
> proposal unless explicitly stated otherwise.

## Table of Contents

- [Objective](#objective)
- [Proposed Stack](#proposed-stack)
- [Proposed MVP Architecture](#proposed-mvp-architecture)
- [Responsibility Boundaries](#responsibility-boundaries)
- [CV and VLM Roles](#cv-and-vlm-roles)
- [Proposed Technology Stack](#proposed-technology-stack)
- [Analysis Engine Requirements](#analysis-engine-requirements)
- [Operational Requirements](#operational-requirements)
- [Privacy and Safety](#privacy-and-safety)

## Objective

The June 2026 proposal assumed a fixed supported-exercise catalog. Its proposed
MVP would test whether users understand structured form feedback and use it to
improve later attempts.

This document preserves that superseded stack proposal for historical context.
For current product scope, see [Product Spec](PRODUCT_SPEC.md). For the pending
architecture comparison, see
[Candidate Architecture Patterns and Evaluation Plan](CANDIDATE_ARCHITECTURE_PATTERNS_AND_EVALUATION_PLAN.md).
Definitions are available in
[AI Movement Analysis Concepts and Tools](AI_MOVEMENT_ANALYSIS_CONCEPTS.md).

## Proposed Stack

The June 2026 proposal specified:

1. A Gemini video-capable model for temporal visual observations.
2. A TypeScript analysis engine for normalization, exercise rules, confidence,
   and feedback prioritization.
3. An LLM coaching layer that explains structured analysis evidence only.
4. Schema, evidence, supported-exercise, and safety validation before display.
5. Transient video processing with deletion after analysis.

The proposal preferred Gemini native video because it preserves more motion,
tempo, and transition context than manually selected frames. Provider
observations remain estimates and must not be presented as pose-grade or
clinical measurements.

Representative frames sent to an image-capable provider are the fallback when
native video is unavailable. Frame sampling can miss important movement between
frames.

The proposal deferred browser-side MediaPipe to a later pre-submission quality
gate for framing, body visibility, and clip usability. It is not the primary
analyzer. Any future server-side pose estimation should run as a Python sidecar
rather than replace the Next.js backend.

## Proposed MVP Architecture

```txt
Record or upload a short clip
  -> client and server media validation
  -> transient Gemini video input
  -> normalized provider observations
  -> deterministic analysis engine
  -> structured analysis evidence
  -> LLM coaching
  -> safety and schema validation
  -> checklist feedback
  -> source video discarded
```

The proposal kept the complete MVP in one Next.js App Router codebase. Route
handlers protect provider credentials and coordinate validation, provider
calls, analysis, coaching, persistence, and response delivery.

## Responsibility Boundaries

| Component | Required Output |
|---|---|
| Vision provider | Timestamps, estimated reps and phases, media quality, approximate movement evidence, and confidence |
| Analysis engine | Normalized issues, positive findings, evidence, severity, priority, and confidence |
| Coaching layer | Concise explanations and corrective cues derived from analysis evidence |
| Final validator | Supported, evidence-consistent, non-medical, and schema-valid feedback |

The analysis engine is the source of truth. The coaching layer must not add,
remove, or change findings, measurements, severity, priority, or confidence.

When evidence is insufficient, the system should request a better clip rather
than return confident feedback. Unsupported exercises must be rejected rather
than analyzed generically.

## CV and VLM Roles

| Component | Role |
|---|---|
| Computer vision and pose models | Extract landmarks and support measurable checks such as visibility, joint angles, phases, and repetitions |
| Vision-language model | Interpret video context and return structured temporal observations without claiming pose-grade precision |
| Analysis engine | Validate either source, apply approved exercise rules, combine confidence, and remain the source of truth |

In this proposal, Gemini was the primary observation provider. Browser-side pose
estimation remains a later quality gate; it may become an analysis input only
after validation against human-labeled clips.

## Proposed Technology Stack

| Layer | Choice |
|---|---|
| Application | Next.js App Router, TypeScript, and PWA support |
| Client media | Browser MediaRecorder API and file upload |
| Backend | Next.js route handlers |
| Vision provider | Gemini video-capable model behind a server-side adapter |
| Provider fallback | Representative frames for an image-capable provider |
| Analysis engine | TypeScript normalization, rules, confidence, and prioritization |
| Coaching | Server-side LLM receiving analysis evidence only |
| Storage | Analysis metadata and feedback linked to a pseudonymous identifier |
| Video handling | Transient processing and deletion |
| Later quality gate | Browser-side MediaPipe |

The exact model, SDK, formats, sampling behavior, quotas, pricing, and retention
controls must be verified during implementation. The architecture must not
depend on a fixed model version, free tier, or temporary commercial terms.

## Analysis Engine Requirements

- Support approved rules for all five MVP exercises.
- Treat reps, phases, angles, and alignment as confidence-scored estimates.
- Combine media quality, provider confidence, and rule confidence.
- Return positive findings and one or two prioritized corrections.
- Use varied test clips and exercise-specific acceptance criteria.
- Return a supportive retry when evidence is inadequate.

The MVP should avoid score-first judgments.

## Operational Requirements

- Benchmark representative 10-30 second clips for cost, latency, and reliability.
- Test provider sampling against fast movement and transitions.
- Enforce upload duration, size, format, rate, and concurrency limits.
- Record latency, failure reasons, and estimated cost without storing raw media.
- Keep provider selection behind a server-side adapter.

## Privacy and Safety

An identifiable exercise video is personal data. Movement-derived fitness data
may qualify as health data depending on its use. Calis App must not use exercise
footage for biometric identification.

| Control | MVP Requirement |
|---|---|
| Raw video and temporary frames | Process transiently and discard after analysis |
| Stored history | Keep required metadata and feedback, not source media |
| Identity | Separate direct identity from movement data |
| Consent | Obtain explicit opt-in before the first analysis |
| Future retention | Require separate explicit consent |
| Provider disclosure | Explain what is sent, stored, and discarded |
| Credentials | Keep provider keys server-side |
| Logs | Never include raw media |
| Disclaimer | Display: "This app is not medical or physiotherapy advice." |

Feedback must describe observable movement, acknowledge uncertainty, and avoid
diagnosis, medical claims, unsafe advice, and unsupported certainty. Provider
terms, processing locations, and retention controls must be reviewed before
launch.
