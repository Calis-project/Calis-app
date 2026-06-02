# 01 — MVP Scope

## MVP Goal

Validate whether a realistic, low-pressure home workout app can help users continue exercising and return after missed days.

The MVP should answer:

> Will users come back more often if the app gives them small workouts, supportive messages, and a clear comeback path?

## MVP Must-Have Features

| Feature | Description |
|---|---|
| Onboarding | Collect fitness level, time, space, equipment, noise needs, and limitations |
| User Profile | Store user constraints and preferences |
| Exercise Library | Store safe, simple exercises with alternatives |
| Workout Generator | Rule-based generator using user constraints |
| Daily Workout Options | Show Minimum, Standard, and Extended options |
| Workout Session | Guide the user through a selected workout |
| Completion Tracking | Save completed workouts |
| Comeback Mode | Detect missed days and suggest gentle restart |
| Return Chain | Track returns instead of strict streaks |
| Progress Dashboard | Show progress without guilt |
| Supportive Messages | Use calm, non-shaming copy |

## MVP Should-Have Features

- simple notification preferences
- exercise browsing
- basic workout history
- energy before/after feedback
- difficulty feedback

## MVP Out of Scope

Do not implement these in the first MVP:

- AI API calls
- AI chatbot
- AI workout generation
- API key settings
- nutrition planning
- social media feed
- public leaderboards
- wearable integration
- advanced analytics
- paid coaching marketplace
- body transformation tracking

## MVP User Flow

1. User opens app.
2. User completes onboarding.
3. App creates a basic profile.
4. User sees today’s three workout options.
5. User chooses a workout.
6. User completes the workout.
7. App records completion.
8. App shows supportive feedback.
9. If user misses days, Comeback Mode activates.
10. User completes a gentle comeback workout.

## Daily Workout Options

| Option | Duration | Purpose |
|---|---:|---|
| Minimum | 3–5 min | Keep the habit alive |
| Standard | 8–12 min | Balanced daily movement |
| Extended | 20–30 min | Stronger session for high-energy days |

## Comeback Mode

Comeback Mode activates after missed days.

Suggested triggers:

| Missed Days | Comeback Suggestion |
|---:|---|
| 3 days | 5-minute light full-body |
| 7 days | 3–5 minute mobility and easy strength |
| 14+ days | gentle restart session |

Example message:

> Welcome back. No need to make up for missed days. Let’s restart gently.

## Return Chain

A normal streak breaks when the user misses a day.

Return Chain is different.

It tracks:

- active days
- return days
- comeback completions
- minimum workouts
- consistency over time

The goal is resilience, not perfection.

## MVP Success Metrics

Track:

- Day 1 retention
- Day 7 retention
- Day 14 retention
- Day 30 retention
- number of completed minimum workouts
- number of Comeback Mode completions
- percentage of users who return after missed days
- average workouts per user per week
- user feedback on tone and difficulty

## MVP Definition of Done

The MVP is done when a user can:

1. create a profile
2. get suitable workout options
3. complete a workout
4. use an easier alternative
5. miss several days
6. return through Comeback Mode
7. see progress without guilt
