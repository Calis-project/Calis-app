# Technical Plan

## Scope

Build the MVP as one Next.js App Router application with TypeScript and basic
PWA capabilities. Product behavior is defined in
[Product Spec](PRODUCT_SPEC.md), and scope decisions are defined in
[Roadmap and Decisions](ROADMAP_AND_DECISIONS.md).

## Architecture

The browser owns exercise selection, recording or upload, local preview, basic
media checks, and feedback display. Next.js route handlers own validation,
provider calls, analysis, coaching, persistence, and credentials.

```txt
Client recording or upload
  -> route handler media validation
  -> Gemini native video or fallback frames
  -> normalized provider observations
  -> analysis engine
  -> LLM coaching from analysis evidence
  -> safety and schema validation
  -> discard transient media
  -> store metadata and feedback
  -> return checklist result
```

| Component | Responsibility |
|---|---|
| Vision provider adapter | Obtain timestamped, confidence-scored observations |
| Analysis engine | Normalize evidence, apply exercise rules, calculate confidence, and prioritize findings |
| Coaching layer | Explain structured findings without changing the evidence |
| Result validator | Enforce schema, evidence consistency, supported scope, and safety |

The analysis engine is the source of truth for reps, phases, measurements,
issues, timestamps, severity, priority, and confidence. The coaching layer must
not receive raw video or unnormalized observations.

Provider credentials must remain in server-only environment variables and must
never use `NEXT_PUBLIC_`.

## App Structure

```txt
app/
|-- analyze/
|-- exercises/
|-- history/
|-- profile/
|-- api/
|   |-- exercises/supported/route.ts
|   |-- analysis/video/route.ts
|   |-- analysis/[session_id]/route.ts
|   `-- progress/form-history/route.ts
`-- manifest.ts
public/
`-- icons/
```

PWA work is limited initially to a manifest, icons, installability, and a
mobile-friendly shell.

## Data Model

| Entity | Required Data |
|---|---|
| `UserProfile` | Experience level, focus exercises, sensitive areas, consent, and comeback preference |
| `SupportedExercise` | ID, setup instructions, recording guidance, approved rules, common issues, and safety notes |
| `FormAnalysisSession` | User, exercise, status, source, duration, timestamps, and `source_video_retained: false` |
| `FormAnalysisResult` | Summary, issues, positive notes, corrections, confidence, and model metadata |
| `FormIssue` | Label, severity, evidence, timestamp, correction, confidence, priority, and safety flag |
| `AIRequestLog` | Optional provider, latency, failure reason, and estimated cost without media |

Form history is derived from saved sessions and results. Store movement data
under a pseudonymous user identifier rather than direct identity.

```txt
experience_level: beginner | some_experience | intermediate
exercise_id: push_up | squat | plank | lunge | hollow_hold
analysis_status: created | uploading | processing | completed | failed | rejected
severity: low | medium | high
confidence: low | medium | high
video_source: recorded | uploaded
```

## API

| Endpoint | Behavior |
|---|---|
| `GET /api/exercises/supported` | Return approved exercises with setup, recording, common-issue, and safety guidance |
| `POST /api/analysis/video` | Validate and analyze one short clip, save the result, and discard transient media |
| `GET /api/analysis/{session_id}` | Return session status and normalized result; never return source video |
| `GET /api/progress/form-history` | Return saved attempts, repeated issues, positive notes, and progress summaries |

`POST /api/analysis/video` accepts:

- `exercise_id`
- `video_source`
- one video file

It must validate identity, consent, supported exercise, media type, size,
duration, and readability. Unsupported exercises must be rejected before any
provider call.

## Analysis Pipeline

1. Validate consent, exercise, and media.
2. Create a processing session.
3. Send native video to the configured Gemini adapter; use representative frames
   only when native video is unavailable.
4. Request visible observations, media quality, estimated reps and phases,
   timestamps, and confidence.
5. Normalize the provider response into a stable internal schema.
6. Apply exercise-specific rules and calculate confidence and priority.
7. Return a retry state when evidence is inadequate.
8. Send structured analysis evidence to the coaching layer.
9. Validate coaching against the evidence, schema, and safety rules.
10. Store normalized metadata and feedback.
11. Delete source video and temporary frames in success and failure paths.
12. Return the result or a supportive retry response.

Provider instructions must limit analysis to the selected exercise and visible
evidence. Coaching must preserve confidence, include positive observations, and
avoid unsupported measurements or claims.

## Controls

### Media and Operations

- Maximum clip duration: 30 seconds.
- Support browser-friendly formats such as `mp4`, `mov`, and `webm`.
- Enforce file-size, request-rate, and concurrency limits.
- Benchmark 10-30 second clips for latency, cost, sampling, and reliability.
- Log operational metadata only; never log raw media.
- Keep provider selection behind an adapter.
- Verify model availability, formats, quotas, pricing, and retention terms
  during implementation.

### Privacy and Security

- Require explicit opt-in before the first analysis.
- Explain before submission what is processed, stored, and discarded.
- Treat source videos and extracted frames as transient.
- Store only required metadata and normalized feedback.
- Separate movement data from direct identity.
- Never use footage for biometric identification.
- Require separate consent for future raw-video retention.
- Keep all provider credentials server-side.

### Result Safety

- Reject unsupported exercises and invalid schemas.
- Reject or soften medical, diagnostic, unsafe, or overconfident language.
- Preserve evidence, confidence, and sensitive-area constraints.
- Return clear retry guidance for poor angle, lighting, visibility, or media
  quality.
- Display: "This app is not medical or physiotherapy advice."

## Later Extension

Browser-side MediaPipe may later reject unusable framing, incomplete body
visibility, or poor clip quality before upload. It is a quality gate, not the
primary analyzer.

If server-side pose estimation becomes necessary, add a Python sidecar service
without replacing the Next.js application backend.

## Build Order

1. Create the Next.js shell, routes, storage, profile, and minimal PWA setup.
2. Seed the five supported exercises and their guidance.
3. Build recording or upload with client-side validation.
4. Implement the analysis endpoint and transient media cleanup.
5. Add the Gemini-first provider adapter and normalized observation schema.
6. Implement exercise rules, confidence, prioritization, and retry handling.
7. Add evidence-constrained coaching and result validation.
8. Build checklist feedback with retry and save actions.
9. Add form history and repeated-issue summaries.
10. Add lightweight comeback support.
