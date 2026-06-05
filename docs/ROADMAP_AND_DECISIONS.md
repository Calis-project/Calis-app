# Roadmap and Decisions

## Product Direction

AI-assisted video form analysis is the MVP center of gravity. Calis App should first prove that users will record short clips, understand structured feedback, and improve their exercise quality through repeat attempts.

The previous habit, comeback, and low-pressure consistency concept remains important, but it becomes a supporting layer around the AI analysis loop rather than the primary MVP.

Core MVP promise:

> Record a short calisthenics clip and get clear, supportive feedback for your next attempt.

## MVP Roadmap

1. Next.js App Router foundation with responsive navigation and local account/profile flow.
2. Supported exercise list for push-up, squat, plank, lunge, and hollow hold.
3. Exercise setup guidance for camera angle, visibility, lighting, reps or hold length, and safety.
4. Browser recording or upload flow for short clips.
5. Backend media validation and transient video handling.
6. Backend Vision API integration with app-managed credentials.
7. Structured AI output for positive notes, form issues, severity, moments, corrections, and confidence.
8. Safety validator for supported exercise scope, non-medical wording, sensitive-area caution, and fallback handling.
9. Checklist feedback UI with retry and save-result actions.
10. Form history showing saved feedback, repeated issues, and supportive progress.
11. Comeback support as a lightweight prompt after missed practice days.

## Later Roadmap

Future AI and product features:

1. Local pose-estimation pre-checks for visibility, camera angle, rep phases, and simple landmark quality.
2. Before/after attempt comparison for the same exercise.
3. Broader exercise library with validation per exercise.
4. Optional score or readiness indicators, only if they do not create shame or false certainty.
5. AI exercise explainer for supported exercises and common mistakes.
6. AI comeback coach for gentle restart prompts after gaps.
7. AI weekly reflection that summarizes practice and repeated improvements.
8. Rule-based or AI-assisted workout generation from approved exercises.
9. Optional video retention with explicit consent.
10. Developer mode for user-provided API keys.
11. Mobile app camera experience if the Next.js web app validates demand.
12. Richer PWA behavior such as push reminders and offline practice packs.

## AI Safety and Architecture

AI must not:

- diagnose medical problems
- prescribe treatment
- claim it can detect injuries
- tell users to continue through pain
- analyze unsupported exercises as if they are supported
- generate unsafe exercise instructions
- ignore sensitive areas
- shame users
- promote rapid transformation
- use aggressive fitness language

AI should:

- analyze only approved supported exercises
- use visible evidence from the submitted clip
- state uncertainty when video quality, angle, or visibility is poor
- provide concrete next-attempt cues
- include positive notes
- suggest easier variations when appropriate
- recommend stopping if pain appears
- keep feedback supportive and non-judgmental

Recommended MVP architecture:

```txt
Next.js App Router
-> Client recording/upload components
-> Route handlers
-> Media validator
-> Temporary media processor
-> Vision API wrapper
-> Structured result parser
-> Safety validator
-> Analysis database
-> Checklist feedback response
```

AI should be called from Next.js route handlers or server-side modules, not directly from the frontend. App-managed API keys stay server-side and must not use `NEXT_PUBLIC_`.

## Decisions

Decision 001: Build the MVP around AI-assisted form analysis.

Why: The product direction has changed. The first version should validate the most differentiated value: short-video analysis that helps users correct exercise mistakes.

Decision 002: Use Next.js App Router with PWA capabilities for the first build.

Why: Next.js provides the app structure, routing, route handlers, and server-side AI integration. PWA capabilities add installability and mobile app-like behavior without creating a second app or duplicate backend.

Decision 002A: Treat PWA as an enhancement, not a separate implementation track.

Why: There should be one Next.js codebase. PWA features such as `manifest.ts`, icons, installability, and future service worker behavior are added to that app.

Decision 003: Use after-recording analysis, not live feedback.

Why: Post-recording analysis is simpler, safer, and easier to validate. Live feedback can be explored later if users trust and reuse the analysis flow.

Decision 004: Limit MVP analysis to five supported exercises.

Why: Push-up, squat, plank, lunge, and hollow hold are recognizable calisthenics movements with common form issues. A narrow list keeps prompts, validation, and feedback quality testable.

Decision 005: Use backend Vision API integration with app-managed credentials.

Why: Backend integration protects API keys, centralizes safety validation, supports cost controls, and creates a cleaner user experience.

Decision 006: Analyze videos transiently and discard originals by default.

Why: Form videos are sensitive. The MVP should store analysis results and metadata, not raw source videos, unless a future feature asks for explicit retention consent.

Decision 007: Use checklist plus tips instead of score-first feedback.

Why: Checklist feedback is more actionable and less judgmental. A score can create false certainty and may conflict with the supportive tone.

Decision 008: Keep comeback support as a secondary product layer.

Why: The low-pressure habit philosophy still differentiates Calis, but it should support returning to practice rather than dominate the AI analysis MVP.

Decision 009: Validate all AI output before showing it.

Why: The app needs predictable safety boundaries. Results should be checked for schema shape, supported exercise scope, medical claims, unsafe advice, and overly certain language.

Decision 010: Keep alternative AI strategies documented, not primary.

Why: User-provided keys and local pose-estimation-first workflows may be useful later, but they add complexity or reduce coaching quality for the initial user-facing MVP.

Decision 011: Defer native mobile until the AI video-analysis loop is validated.

Why: Native mobile may improve camera ergonomics later, but the first goal is to prove that users record clips, trust the feedback, and retry based on suggestions.
