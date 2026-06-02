# 05 — AI Future Roadmap

## Status

AI is future scope.

Do not build AI in the first MVP.

## AI Product Principle

AI should support the existing product philosophy:

> Help users continue, adapt, and come back.

AI should not become the main product.

## Recommended Strategy

```txt
Rule-based MVP first.
Optional AI support layer later.
```

## Future AI Features

### 1. AI Comeback Coach

Highest priority AI feature.

Purpose:

- personalize comeback messages
- suggest gentle restart plans
- reduce guilt after breaks

Example:

> Welcome back. You do not need to make up for missed days. Let’s restart with something small.

### 2. AI Workout Adapter

Purpose:

- adapt the three daily workout options
- use energy, time, equipment, space, and missed days
- select from approved exercises only

### 3. AI Exercise Explainer

Purpose:

- explain exercises simply
- suggest easier alternatives
- explain quiet versions
- answer basic form questions

Safety limit:

AI must not diagnose pain or injury.

### 4. AI Weekly Reflection

Purpose:

- summarize progress supportively
- highlight comebacks
- suggest realistic next step

### 5. AI Message Generator

Purpose:

- generate supportive messages
- maintain tone of voice
- avoid repeated static messages

## API Key Strategy

Possible future models:

| Model | Meaning | Pros | Cons |
|---|---|---|---|
| App-managed key | App owner pays for AI usage | Easy for users | Cost and abuse risk |
| User-provided key | User enters own API key | Lower cost | Too technical |
| Hybrid | Both options | Flexible | More complex |

Recommended:

- MVP: no AI
- AI beta: app-managed key
- developer mode: optional user-provided key
- production: decide later based on cost and users

## AI Safety Rules

AI must not:

- diagnose medical problems
- prescribe treatment
- tell users to continue through pain
- generate unsafe workouts
- ignore sensitive areas
- shame users
- promote rapid transformation
- use aggressive fitness language

AI should:

- choose from approved exercises
- suggest easier alternatives
- respect user constraints
- keep comeback sessions easy
- use supportive language

## AI Output Validation

Before showing AI-generated workout suggestions, validate:

- exercise IDs exist
- exercises are approved for AI
- user equipment matches
- user space matches
- quiet mode is respected
- sensitive areas are respected
- duration is acceptable
- intensity is appropriate

If validation fails, use rule-based fallback.

## Future AI Architecture

```txt
Frontend
→ Backend API
→ Rule-based workout engine
→ AI service wrapper
→ Safety validator
→ Exercise database
→ Workout response
```

AI should be called from the backend, not directly from the frontend, when using app-managed API keys.

## Future AI Files

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

## AI Implementation Order

1. Add AI settings model.
2. Add backend AI client.
3. Add prompt templates.
4. Add AI comeback message.
5. Add message validation.
6. Add AI workout adaptation.
7. Add workout safety validation.
8. Add weekly reflection.
9. Add API key management if needed.
