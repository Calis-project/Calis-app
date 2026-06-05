# Technical Plan

## Architecture Summary

The MVP should be a Next.js App Router web app with PWA capabilities. Next.js provides the app structure, routing, API route handlers, and server-side AI calls. PWA capabilities add installability and mobile app-like behavior without creating a second app or duplicate backend.

The browser handles exercise selection, recording or upload, and feedback display through client components. Next.js route handlers own media validation, AI provider calls, result normalization, safety validation, persistence, and API key protection.

Default MVP flow:

```txt
Next.js App Router
-> client recording/upload component
-> route handler media validation
-> frame extraction or provider-supported video input
-> server-side vision model analysis
-> structured result normalization
-> safety and schema validation
-> discard source video
-> store analysis metadata and feedback
-> return checklist feedback to user
```

The MVP assumes app-managed backend Vision API credentials. API keys must use server-only environment variables and must never be exposed with `NEXT_PUBLIC_` or called from the frontend.

PWA is not a separate implementation track. It is a small set of capabilities added to the Next.js app, starting with a manifest, icons, installability, mobile-friendly shell, and minimal service worker behavior when needed.

## Next.js App Structure

Suggested routes:

```txt
app/
|-- analyze/
|-- exercises/
|-- history/
|-- profile/
|-- api/
|   |-- exercises/
|   |   `-- supported/route.ts
|   |-- analysis/
|   |   |-- video/route.ts
|   |   `-- [session_id]/route.ts
|   `-- progress/
|       `-- form-history/route.ts
|-- manifest.ts
public/
|-- icons/
```

Client components should handle camera access, recording controls, upload selection, local preview, and client-side media checks. Server route handlers should handle validation, transient media processing, Vision API calls, storage, and result delivery.

## Data Model

Core entities:

| Entity | Purpose | MVP |
|---|---|---|
| UserProfile | Stores experience, focus exercises, sensitive areas, and privacy preferences | Yes |
| SupportedExercise | Defines exercises that AI analysis can evaluate | Yes |
| FormAnalysisSession | Tracks one submitted video analysis attempt | Yes |
| FormAnalysisResult | Stores normalized AI feedback for a session | Yes |
| FormIssue | Stores one detected form issue | Yes |
| PracticeHistory | Aggregates saved attempts and repeated issues | Yes |
| AIRequestLog | Stores non-video operational metadata for debugging and cost tracking | Optional |
| WorkoutSession | Future workout flow | No |
| WorkoutCompletion | Future workout flow | No |

UserProfile:

```json
{
  "id": "user_001",
  "experience_level": "beginner",
  "focus_exercises": ["push_up", "squat", "plank"],
  "sensitive_areas": ["wrists"],
  "comeback_support_enabled": true,
  "video_retention_consent": false,
  "created_at": "2026-06-02T10:00:00Z",
  "updated_at": "2026-06-02T10:00:00Z"
}
```

SupportedExercise:

```json
{
  "id": "push_up",
  "name": "Push-up",
  "category": "upper_body",
  "difficulty": "beginner_to_intermediate",
  "setup_instructions": [
    "Place the camera to your side at about hip height.",
    "Keep your full body visible from head to feet.",
    "Record 3 to 6 controlled reps."
  ],
  "recording_guidance": {
    "recommended_duration_seconds": 15,
    "max_duration_seconds": 30,
    "preferred_angle": "side",
    "full_body_required": true
  },
  "common_mistakes": [
    "hips_sagging",
    "elbows_flared",
    "partial_range_of_motion",
    "head_dropping"
  ],
  "safety_notes": [
    "Stop if you feel wrist, shoulder, or lower-back pain."
  ],
  "ai_analysis_allowed": true
}
```

FormAnalysisSession:

```json
{
  "id": "fas_001",
  "user_id": "user_001",
  "exercise_id": "push_up",
  "status": "completed",
  "video_duration_seconds": 18,
  "source_video_retained": false,
  "created_at": "2026-06-02T10:00:00Z",
  "completed_at": "2026-06-02T10:00:25Z"
}
```

FormAnalysisResult:

```json
{
  "session_id": "fas_001",
  "overall_summary": "Your reps are controlled, but your hip position changes near the bottom of several reps.",
  "issues": [
    {
      "label": "Hips sagging",
      "severity": "medium",
      "timestamp_seconds": 9,
      "explanation": "Your hips appear to drop as you lower into the rep.",
      "correction": "Brace your core before each rep and stop the set when your body line changes.",
      "safety_related": true
    }
  ],
  "positive_notes": [
    "Your tempo is steady.",
    "Your hands stay planted consistently."
  ],
  "corrective_tips": [
    "Try an incline push-up for cleaner body alignment.",
    "Record from the side again so your body line is easy to review."
  ],
  "confidence": "medium",
  "model_metadata": {
    "provider": "backend_vision_api",
    "model": "configured_on_server",
    "analysis_version": "mvp_001"
  }
}
```

## Enums

```txt
experience_level: beginner, some_experience, intermediate
supported_exercise_id: push_up, squat, plank, lunge, hollow_hold
analysis_status: created, uploading, processing, completed, failed, rejected
difficulty: beginner, beginner_to_intermediate, intermediate
severity: low, medium, high
confidence: low, medium, high
video_source: recorded, uploaded
category: upper_body, lower_body, core, full_body
```

## API Interfaces

Conceptual MVP endpoints:

```txt
GET /api/exercises/supported
POST /api/analysis/video
GET /api/analysis/{session_id}
GET /api/progress/form-history
```

Next.js route handler mapping:

| Endpoint | Route handler |
|---|---|
| `GET /api/exercises/supported` | `app/api/exercises/supported/route.ts` |
| `POST /api/analysis/video` | `app/api/analysis/video/route.ts` |
| `GET /api/analysis/[session_id]` | `app/api/analysis/[session_id]/route.ts` |
| `GET /api/progress/form-history` | `app/api/progress/form-history/route.ts` |

`GET /api/exercises/supported`

- Returns only exercises with `ai_analysis_allowed = true`.
- Includes setup instructions, recording guidance, common mistakes, and safety notes.

`POST /api/analysis/video`

- Accepts `exercise_id`, `video_source`, and one short video file.
- Validates authentication or local user identity, exercise support, file type, file size, duration, and required metadata.
- Rejects unsupported exercises instead of asking AI to infer arbitrary movements.
- Calls the backend AI analysis pipeline.
- Discards the source video after processing.
- Stores `FormAnalysisSession` and `FormAnalysisResult`.

`GET /api/analysis/{session_id}`

- Returns session status and result when available.
- Never returns raw source video in the MVP.

`GET /api/progress/form-history`

- Returns saved analysis metadata, repeated issues, positive notes, and user-visible progress summaries.

## AI Analysis Pipeline

Backend steps:

1. Validate the selected exercise against `SupportedExercise`.
2. Validate media type, duration, size, and basic readability.
3. Extract representative frames or prepare provider-supported video input.
4. Send the exercise definition, user sensitive areas, safety constraints, and media input to the Vision API.
5. Require structured output matching `FormAnalysisResult`.
6. Validate issue labels, severity, timestamps, safety flags, and unsupported claims.
7. Remove or soften medical, diagnostic, or overconfident language.
8. Persist only session metadata and normalized feedback.
9. Delete transient source video and temporary frames.
10. Return checklist feedback to the frontend.

The prompt should instruct the model to:

- analyze only the selected supported exercise
- focus on visible form observations
- mention uncertainty when visibility is poor
- avoid diagnosis or medical advice
- provide practical corrections
- include positive notes
- avoid score-first feedback

If analysis fails, the backend should return a supportive failure state and suggest recording again with better angle, lighting, or full-body visibility.

## Alternative AI Strategies

Default: backend Vision API with app-managed key.

- Best user experience for MVP.
- Keeps credentials private.
- Allows consistent validation, logging, and safety checks.
- Requires backend infrastructure and cost controls.

Alternative: user-provided API key mode.

- Useful for developer builds, internal testing, or power users.
- Reduces platform cost but creates poor normal-user onboarding.
- Should be separated from production UX and clearly marked as developer mode.
- Still should route through backend validation when possible.

Alternative: local pose-estimation-first mode.

- Useful for privacy-sensitive or lower-cost experiments.
- Can detect simple angles, body landmarks, rep phases, and visibility quality.
- Produces less natural coaching feedback unless combined with rule-based cues or optional AI summaries.
- Could become a pre-check before Vision API calls to reduce failed submissions.

## Privacy, Security, and Cost Controls

MVP defaults:

- source videos are transient
- source videos are discarded after analysis
- temporary frames are discarded after analysis
- stored history contains only metadata and feedback
- frontend never receives provider credentials
- Vision API credentials are stored in server-only environment variables, never `NEXT_PUBLIC_`
- route handler logs must not include raw media

Operational controls:

- max duration per clip: 30 seconds
- supported formats should be browser-friendly, such as `mp4`, `mov`, or `webm`
- enforce upload size limits
- rate-limit analysis requests per user
- record provider latency, failure reason, and estimated cost without storing video
- provide a clear retry path when media quality is too poor

## MVP Build Order

1. Project setup: Next.js App Router, TypeScript, routing, route handlers, storage, and responsive app shell.
2. Supported exercise seed data: push-up, squat, plank, lunge, and hollow hold.
3. Profile setup: experience level, focus exercises, sensitive areas, and privacy acknowledgement.
4. Basic PWA setup: `app/manifest.ts`, icons, installability, and mobile-friendly shell.
5. Exercise selection and setup guidance.
6. Client recording or upload flow with duration and format validation.
7. Route handler analysis endpoint with transient media handling.
8. Vision API wrapper and structured output schema.
9. Result validator for safety, schema, supported exercises, and non-medical language.
10. Checklist feedback screen with positive notes, issues, severity, moments, and tips.
11. Retry and save-result flow.
12. Form history with repeated issues and supportive progress summaries.
13. Lightweight comeback support that recommends a simple practice attempt after gaps.

## Repository Docs

```txt
Calis-app/
|-- README.md
|-- docs/
|   |-- PRODUCT_SPEC.md
|   |-- TECHNICAL_PLAN.md
|   `-- ROADMAP_AND_DECISIONS.md
```

## Development Priority

Focus on the shortest reliable AI analysis loop in one Next.js codebase: supported exercise selection, clean client-side video capture, route-handler Vision API analysis, structured checklist feedback, transient video handling, and supportive retry. Do not build live feedback, broad workout generation, retained video libraries, social features, or medical guidance in the first MVP.
