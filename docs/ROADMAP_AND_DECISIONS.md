# Roadmap and Decisions

## Future AI Roadmap

AI is future scope. Do not build AI in the first MVP.

AI should support the existing product philosophy:

> Help users continue, adapt, and come back.

AI should not become the main product. The recommended strategy is rule-based MVP first, optional AI support layer later.

Future AI features:

1. AI Comeback Coach: personalize comeback messages, suggest gentle restart plans, and reduce guilt after breaks.
2. AI Workout Adapter: adapt the three daily workout options using energy, time, equipment, space, and missed days while selecting from approved exercises only.
3. AI Exercise Explainer: explain exercises simply, suggest easier alternatives, explain quiet versions, and answer basic form questions without diagnosing pain or injury.
4. AI Weekly Reflection: summarize progress supportively, highlight comebacks, and suggest a realistic next step.
5. AI Message Generator: generate supportive messages, maintain tone of voice, and avoid repeated static messages.

Recommended API key strategy:

- MVP: no AI
- AI beta: app-managed key
- developer mode: optional user-provided key
- production: decide later based on cost and users

Future AI implementation order:

1. Add AI settings model.
2. Add backend AI client.
3. Add prompt templates.
4. Add AI comeback message.
5. Add message validation.
6. Add AI workout adaptation.
7. Add workout safety validation.
8. Add weekly reflection.
9. Add API key management if needed.

## AI Safety and Architecture

AI must not:

- diagnose medical problems
- prescribe treatment
- tell users to continue through pain
- generate unsafe workouts
- ignore sensitive areas
- shame users
- promote rapid transformation
- use aggressive fitness language

AI should choose from approved exercises, suggest easier alternatives, respect user constraints, keep comeback sessions easy, and use supportive language.

Before showing AI-generated workout suggestions, validate that exercise IDs exist, exercises are approved for AI, equipment and space match, quiet mode is respected, sensitive areas are respected, duration is acceptable, and intensity is appropriate. If validation fails, use a rule-based fallback.

Future AI architecture:

```txt
Frontend
-> Backend API
-> Rule-based workout engine
-> AI service wrapper
-> Safety validator
-> Exercise database
-> Workout response
```

AI should be called from the backend, not directly from the frontend, when using app-managed API keys.

Possible future files:

```txt
docs/API_KEY_MANAGEMENT.md
docs/PROMPT_DESIGN.md
docs/AI_SAFETY_RULES.md
docs/AI_WORKOUT_GENERATION.md
```

Possible future code structure:

```txt
src/ai/
  aiClient.ts
  promptTemplates.ts
  workoutAdapter.ts
  comebackCoach.ts
  weeklyReflection.ts
  safetyValidator.ts
  schemas.ts
```

## Decisions

Decision 001: Build the MVP without AI.

Why: The first goal is to validate the habit system with an exercise database, rule-based filtering, workout templates, Comeback Mode, Return Chain, and progress tracking. This keeps the first version simple, testable, and safer.

Decision 002: Keep AI future-compatible.

Why: Fields such as `ai_enabled`, `ai_allowed`, `generated_by`, `ai_assisted`, and `risk_level` make future AI integration easier without requiring AI now.

Decision 003: Treat Comeback Mode as a core MVP feature.

Why: The product should be differentiated by helping users return, not only by giving workouts.

Decision 004: Use Return Chain instead of a strict streak.

Why: Traditional streaks can create guilt when broken. Return Chain better supports realistic consistency.

Decision 005: Future AI should select or adapt from the approved exercise database.

Why: AI should not freely invent exercises. Approved exercises and validation keep AI suggestions safer and easier to test.
