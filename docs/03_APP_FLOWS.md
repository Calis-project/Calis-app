# 03 — App Flows

## Navigation Structure

Suggested MVP navigation:

1. Today
2. Progress
3. Exercises
4. Profile

Future AI settings can later be added under:

5. Settings → AI Features

## Flow 1 — First Launch

### Goal

Introduce the product philosophy.

### Steps

1. User opens app.
2. App shows welcome screen.
3. App explains the core promise.
4. User starts onboarding.

### Example Copy

> Welcome to Calis.
>
> You do not need a perfect workout. You just need a way to come back.

## Flow 2 — Onboarding

### Goal

Collect constraints and preferences.

### Steps

1. Ask fitness level.
2. Ask main goal.
3. Ask realistic minimum time.
4. Ask available space.
5. Ask noise limitation.
6. Ask equipment.
7. Ask sensitive areas.
8. Save user profile.

### Required Questions

- What is your current fitness level?
- What do you want help with?
- On a difficult day, how much time can you realistically give?
- How much space do you have?
- Do you need quiet workouts?
- What equipment do you have?
- Any areas you want to be careful with?

## Flow 3 — Today Screen

### Goal

Help the user start quickly.

### Steps

1. User opens Today.
2. App checks missed days.
3. If needed, show Comeback Mode.
4. Otherwise, ask: “What kind of day is it?”
5. Show three workout cards.
6. User starts one workout.

### Workout Cards

- Minimum
- Standard
- Extended

## Flow 4 — Workout Session

### Goal

Guide user through the workout.

### Steps

1. Show workout overview.
2. Show exercise.
3. Show instructions.
4. Show timer or reps.
5. Allow pause.
6. Allow easier version.
7. Allow skip.
8. Continue to next exercise.
9. Finish session.

## Flow 5 — Completion

### Goal

Record completion and encourage user.

### Steps

1. User finishes workout.
2. App records completion.
3. App asks feedback.
4. App updates progress.
5. App shows supportive message.

### Feedback

- difficulty: easy / okay / hard / too hard
- energy after: lower / same / better

### Example Messages

- “A short workout is still a workout.”
- “You showed up today. That matters.”
- “Good work. Small progress counts.”

## Flow 6 — Comeback Mode

### Goal

Help users restart after missed days.

### Trigger

Comeback Mode activates after a defined number of missed days.

### Steps

1. User opens app after missed days.
2. App detects break.
3. App shows supportive comeback message.
4. App recommends gentle restart workout.
5. User completes workout.
6. App records comeback completion.
7. App updates Return Chain.

### Example Copy

> Welcome back. No need to make up for missed days. Let’s restart gently.

## Flow 7 — Return Chain

### Goal

Reward returning, not perfection.

### Steps

1. User completes workout.
2. App checks if previous days were missed.
3. If yes, record return event.
4. Show positive return feedback.

### Example Copy

> Return logged. Coming back is part of the habit.

## Flow 8 — Progress Dashboard

### Goal

Show progress without shame.

### Suggested Cards

- workouts this week
- minimum workouts completed
- comeback sessions completed
- active days this month
- total minutes moved
- energy improvement

### Avoid

- red failure states
- “you are behind”
- body comparison
- aggressive calorie focus

## Future Flow — AI Workout Adaptation

Not part of MVP.

Future flow:

1. User selects today’s state.
2. App sends limited context to AI.
3. AI suggests adaptation from approved exercises.
4. Rule-based validator checks output.
5. App shows safe result or fallback workout.

## Future Flow — AI Comeback Coach

Not part of MVP.

Future flow:

1. User returns after missed days.
2. App asks AI for short supportive message.
3. App validates tone and safety.
4. App shows message and comeback workout.
