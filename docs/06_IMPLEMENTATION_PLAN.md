# 06 — Implementation Plan

## Recommended Branch

Create a branch from `Develop`:

```bash
git checkout Develop
git pull
git checkout -b docs/mvp-foundation-ai-ready
```

After adding docs:

```bash
git add .
git commit -m "Add MVP product docs with future AI roadmap"
git push -u origin docs/mvp-foundation-ai-ready
```

Then open a pull request into `Develop`.

## Suggested Repo Structure

```txt
Calis-app/
├── README.md
├── AGENTS.md
├── docs/
│   ├── 00_PRODUCT_BRIEF.md
│   ├── 01_MVP_SCOPE.md
│   ├── 02_USER_PERSONAS.md
│   ├── 03_APP_FLOWS.md
│   ├── 04_DATA_MODEL.md
│   ├── 05_AI_FUTURE_ROADMAP.md
│   ├── 06_IMPLEMENTATION_PLAN.md
│   ├── 07_SAFETY_AND_TONE.md
│   └── 08_DECISION_LOG.md
```

## MVP Build Order

### Step 1 — Project Setup

Set up:

- frontend framework
- backend if needed
- database or local storage
- routing
- basic layout

### Step 2 — Data Models

Implement:

- UserProfile
- Exercise
- WorkoutTemplate
- WorkoutSession
- WorkoutCompletion
- FeedbackEntry

### Step 3 — Exercise Seed Data

Create initial exercises:

- wall push-up
- sit-to-stand
- step jack
- knee plank
- dead bug
- glute bridge
- shoulder rolls
- marching in place
- calf raises
- gentle mobility exercises

Each exercise should have:

- difficulty
- equipment
- space
- noise
- impact
- easier alternative
- harder alternative
- safety notes

### Step 4 — Onboarding

Build onboarding screens:

- fitness level
- goal
- minimum time
- space
- noise
- equipment
- sensitive areas

Save user profile.

### Step 5 — Rule-Based Workout Generator

Implement logic:

```txt
profile + daily_state + missed_days
→ filter exercises
→ select template
→ create workout session
```

### Step 6 — Today Screen

Show:

- greeting
- “What kind of day is it?”
- Minimum workout
- Standard workout
- Extended workout
- Comeback message if needed

### Step 7 — Workout Session

Build:

- workout overview
- exercise screen
- timer/reps
- easier alternative
- pause/skip
- completion button

### Step 8 — Completion Tracking

Save:

- workout date
- duration
- type
- comeback flag
- minimum flag
- alternatives used
- feedback

### Step 9 — Comeback Mode

Detect missed days.

Show gentle restart session.

Track comeback completion.

### Step 10 — Progress Dashboard

Show:

- workouts this week
- active days
- minimum workouts
- comeback completions
- total minutes
- energy feedback

## AI-Ready Implementation Rules

It is okay to include these defaults:

```json
{
  "generated_by": "rule_based",
  "ai_enabled": false,
  "ai_assisted": false
}
```

Do not implement:

- real AI requests
- API key form
- AI service
- prompt templates
- AI chat screen

until specifically planned.

## Development Priority

Focus on:

1. Fast prototype
2. Clear user flow
3. Good tone
4. Working Comeback Mode
5. Simple workout generation

Do not over-engineer early.
