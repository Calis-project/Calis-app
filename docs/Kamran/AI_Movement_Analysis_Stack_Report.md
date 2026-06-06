# AI Movement Analysis - Stack Analysis and Decision Report

## Table of Contents

- [1. Objective and Authority](#1-objective-and-authority)
- [2. Available Approaches](#2-available-approaches)
  - [2.1 Native Video Vision API](#21-native-video-vision-api)
  - [2.2 Frame-Sampling Providers](#22-frame-sampling-providers)
  - [2.3 Browser Pose Estimation](#23-browser-pose-estimation)
- [3. Recommended MVP Architecture](#3-recommended-mvp-architecture)
- [4. Conceptual Data Contracts](#4-conceptual-data-contracts)
- [5. The Core Product: The Analysis Engine](#5-the-core-product-the-analysis-engine)
- [6. Recommended MVP Stack](#6-recommended-mvp-stack)
- [7. Cost and Operational Considerations](#7-cost-and-operational-considerations)
- [8. Privacy and Data Protection](#8-privacy-and-data-protection)
- [9. Conclusion](#9-conclusion)

*Prepared: June 2026*

## 1. Objective and Authority

Calis App analyzes short exercise videos and returns post-session coaching for
push-ups, squats, planks, lunges, and hollow holds. The MVP must validate whether
users trust structured form feedback and use it to improve a later attempt.

This report records the current AI stack decision. The authoritative product and
implementation boundaries are defined in
[Roadmap and Decisions](ROADMAP_AND_DECISIONS.md) and
[Technical Plan](TECHNICAL_PLAN.md). For beginner-friendly definitions, see
[AI Movement Analysis Concepts and Tools](AI_MOVEMENT_ANALYSIS_CONCEPTS.md).

## 2. Available Approaches

### 2.1 Native Video Vision API

A video-capable model receives the short clip and exercise instructions directly.
This preserves more temporal context than manually selecting a small set of
frames and supports timestamped observations about motion, tempo, and
transitions.

[Gemini video-capable models](https://ai.google.dev/gemini-api/docs/video-understanding)
are the preferred MVP provider. Native video input does not imply continuous
pose tracking or laboratory-grade measurement. The provider may sample frames
internally, so sampling configuration and confidence must be tested with fast
exercise movement before implementation choices are finalized.

The provider should return structured observations, not final user-facing
coaching. Reps, phases, alignment, and joint-angle evidence remain estimates and
must carry confidence into the analysis engine.

### 2.2 Frame-Sampling Providers

[OpenAI image-capable models](https://platform.openai.com/docs/guides/images-vision)
and [Anthropic Claude image-capable models](https://docs.anthropic.com/en/docs/build-with-claude/vision)
can receive representative frames when their current APIs do not provide
suitable native video input. They can also generate coaching from structured
analysis evidence.

Frame sampling is an MVP fallback, not the preferred path. It can miss movement
between selected frames, including tempo changes, transitions, push-up depth,
and lunge instability. Provider capabilities and supported input types must be
verified against official documentation at implementation time.

### 2.3 Browser Pose Estimation

[MediaPipe Pose Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/web_js)
and similar tools can produce body landmarks in the browser. This can support
precise-looking calculations, but accuracy still depends on camera angle,
visibility, clothing, motion, and device performance.

Browser-side MediaPipe is deferred to the Later Roadmap as a pre-submission
quality gate. Its intended role is to detect unusable framing, insufficient
full-body visibility, or poor clip quality before upload. It is not the primary
MVP analyzer.

If server-side pose estimation becomes necessary later, it should be introduced
as a Python sidecar microservice rather than replacing the Next.js backend.

## 3. Recommended MVP Architecture

```txt
User records or uploads a short clip
  -> client-side duration and format checks
  -> Next.js route handler validation
  -> transient Gemini native video input
  -> normalized provider observations
  -> deterministic analysis engine
  -> structured analysis evidence
  -> LLM coaching layer
  -> safety and schema validation
  -> checklist feedback
  -> source video discarded
```

The Vision provider observes the clip. The analysis engine normalizes evidence,
evaluates exercise-specific rules, calculates confidence, and prioritizes
findings. The LLM coaching layer explains only that structured evidence and must
not invent or alter observations, measurements, severity, or confidence.

The full flow remains in one Next.js App Router codebase. Route handlers protect
provider credentials and orchestrate validation, provider calls, analysis,
coaching, persistence, and response delivery.

## 4. Conceptual Data Contracts

These contracts describe responsibility boundaries rather than final public API
schemas.

### Provider Observations

```json
{
  "exercise": "squat",
  "media_quality": {
    "full_body_visible": true,
    "camera_view": "side",
    "confidence": "medium"
  },
  "estimated_reps": 8,
  "observations": [
    {
      "timestamp_seconds": 7,
      "phase": "bottom",
      "alignment_or_angle_evidence": "depth appears reduced",
      "confidence": "medium"
    }
  ]
}
```

Provider observations contain timestamps, estimated reps or phases, approximate
alignment or angle evidence, media-quality indicators, and confidence. They do
not contain final coaching.

### Analysis Evidence

```json
{
  "exercise": "squat",
  "issues": [
    {
      "type": "insufficient_depth",
      "severity": "medium",
      "evidence": ["depth appears reduced near 00:07"],
      "confidence": "medium",
      "priority": 1
    }
  ],
  "positive_findings": [
    {
      "type": "controlled_tempo",
      "confidence": "medium"
    }
  ]
}
```

Analysis evidence contains normalized issues, positive findings, severity,
supporting evidence, confidence, and priority. It is the source of truth for
what the user-facing response may say.

### Coaching Output

```json
{
  "summary": "Your tempo looks controlled. On the next attempt, focus on a little more depth.",
  "corrections": [
    {
      "issue": "insufficient_depth",
      "cue": "Lower only as far as you can while keeping the movement controlled."
    }
  ]
}
```

Coaching output contains explanations and corrective cues derived from analysis
evidence. It cannot add, remove, or change measurements, findings, severity, or
confidence.

## 5. The Core Product: The Analysis Engine

The analysis engine is the product's core decision layer, not the provider call
or the coaching text generator.

| Responsibility | MVP Behavior |
|---|---|
| Observation normalization | Convert provider output into a stable internal shape |
| Rep and phase handling | Treat provider counts and phases as confidence-scored estimates |
| Alignment and angle evidence | Use approximate evidence without claiming pose-grade precision |
| Exercise rules | Evaluate approved rules for each supported exercise |
| Confidence scoring | Combine media quality, observation confidence, and rule confidence |
| Feedback prioritization | Surface the most useful one or two next-attempt cues |
| Failure handling | Request a better clip when evidence is insufficient |

Rules should be implemented and evaluated for all five supported MVP exercises,
with exercise-specific acceptance criteria and varied test clips. Coverage can
be developed incrementally, but unsupported exercises must be rejected rather
than analyzed generically.

The MVP avoids score-first feedback. Results should emphasize positive findings,
prioritized corrections, confidence, and a supportive retry.

## 6. Recommended MVP Stack

| Layer | Recommended Choice |
|---|---|
| Application | Next.js App Router with TypeScript and PWA capabilities |
| Client media | Browser MediaRecorder API and upload input |
| Backend orchestration | Next.js route handlers; no separate MVP backend |
| Vision provider | Gemini video-capable model through a server-side adapter |
| Provider fallback | Representative frames for an image-capable provider |
| Analysis engine | TypeScript normalization, exercise rules, confidence, and prioritization |
| Coaching layer | Server-side LLM receiving structured analysis evidence only |
| Validation | Schema, evidence consistency, supported-exercise, and safety checks |
| Storage | Analysis metadata and feedback linked through a pseudonymous user identifier |
| Video handling | Transient processing and deletion after analysis |
| Later quality gate | Browser-side MediaPipe before submission |

The exact provider model, SDK, supported formats, sampling options, quotas,
pricing, and free-tier limits must be verified at implementation time. Planning
documents should not pin model versions or depend on temporary commercial terms.

## 7. Cost and Operational Considerations

The main variable costs are video-provider input, coaching output, temporary
media processing, storage, and application hosting. Native video requests may
consume substantially more provider tokens than text-only coaching.

Before implementation:

- benchmark representative 10-30 second clips for cost, latency, and reliability
- test provider-side video sampling for each supported exercise
- verify current model availability, quotas, and data-retention controls
- enforce upload duration, size, format, rate, and concurrency limits
- record provider latency, failure reason, and estimated cost without raw media
- keep provider selection behind a server-side adapter

No exact price, token count, free-tier promise, or fixed performance rate should
be treated as an architectural assumption.

## 8. Privacy and Data Protection

An identifiable exercise video is personal data under the GDPR.
Movement-derived fitness information may constitute data concerning health, and
therefore special-category personal data, depending on the inferences and
processing context. Biometric data receives special-category treatment when it
is processed to uniquely identify a person; Calis App must not use exercise
footage for biometric identification.

| Data or Control | MVP Requirement |
|---|---|
| Raw video | Process transiently and discard after analysis |
| Temporary frames | Discard after analysis when fallback extraction is used |
| Stored history | Keep metadata and feedback, not raw video |
| User identity | Separate direct identity from movement data with a pseudonymous identifier |
| Provider disclosure | Explain what is sent, processed, stored, and discarded |
| User consent | Obtain explicit opt-in before the first analysis |
| Future retention | Require separate explicit consent |
| Credentials | Keep provider keys in server-only environment variables |
| Logs | Never include raw media |
| Disclaimer | Display: "This app is not medical or physiotherapy advice." |

These controls support purpose limitation, data minimisation, storage
limitation, and privacy by design. Provider terms, processing locations, and
retention controls must be reviewed before launch.

## 9. Conclusion

The MVP uses Gemini native video input for temporal observations, a deterministic
analysis engine for normalized and confidence-scored exercise evidence, and an
LLM coaching layer for supportive explanations. This architecture stays within
one Next.js App Router deployment and treats source video as transient.

MediaPipe remains useful, but later: it is a browser-side quality gate for
framing, visibility, and clip usability rather than the primary analyzer.
Provider estimates must never be presented as clinical, pose-grade, or certain,
and the coaching layer must remain constrained by analysis evidence.

Provider capabilities and commercial terms change frequently. Verify the
specific model, SDK, input support, sampling behavior, quotas, and pricing at
implementation time.
