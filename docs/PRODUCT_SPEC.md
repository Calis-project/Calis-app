# Product Spec

## Product Summary

Calis App helps people exercise at home by making small workouts count and making it easy to return after missed days.

Core philosophy:

> You do not need a perfect workout. You just need to come back.

The app is realistic, supportive, home-based, beginner-friendly, low-pressure, consistency-focused, and future-ready for optional AI support. It is not a medical app, bodybuilding app, shame-based streak tracker, calorie-obsession app, or generic AI chatbot.

## Target Users

- Restarting users who often begin fitness routines, miss days, and need a simple way back.
- Busy beginners who have limited time, low confidence, and want short workouts.
- Apartment users who need quiet, low-impact, small-space options.
- Low-energy users who need very easy movement without pressure.
- Cautious movers who need sensitive-area support, easier alternatives, and safety notes.

## MVP Scope

Goal: validate whether a realistic, low-pressure home workout app can help users continue exercising and return after missed days.

The MVP should answer:

> Will users come back more often if the app gives them small workouts, supportive messages, and a clear comeback path?

Must-have features:

| Feature | Description |
|---|---|
| Onboarding | Collect fitness level, time, space, equipment, noise needs, and limitations |
| User Profile | Store user constraints and preferences |
| Exercise Library | Store safe, simple exercises with alternatives |
| Workout Generator | Rule-based generator using user constraints |
| Daily Workout Options | Show Minimum, Standard, and Extended options |
| Workout Session | Guide the user through a selected workout |
| Completion Tracking | Save completed workouts |
| Comeback Mode | Detect missed days and suggest a gentle restart |
| Return Chain | Track returns instead of strict streaks |
| Progress Dashboard | Show progress without guilt |
| Supportive Messages | Use calm, non-shaming copy |

Should-have features:

- simple notification preferences
- exercise browsing
- basic workout history
- energy before/after feedback
- difficulty feedback

Out of scope for the first MVP:

- AI API calls, AI chatbot, AI workout generation, and API key settings
- nutrition planning
- social media feed or public leaderboards
- wearable integration
- advanced analytics
- paid coaching marketplace
- body transformation tracking

## App Flows

Suggested MVP navigation:

1. Today
2. Progress
3. Exercises
4. Profile

First launch introduces the core promise, then starts onboarding.

Onboarding asks:

- What is your current fitness level?
- What do you want help with?
- On a difficult day, how much time can you realistically give?
- How much space do you have?
- Do you need quiet workouts?
- What equipment do you have?
- Any areas you want to be careful with?

Today screen:

1. User opens Today.
2. App checks missed days.
3. If needed, show Comeback Mode.
4. Otherwise, ask: "What kind of day is it?"
5. Show Minimum, Standard, and Extended workout options.
6. User starts one workout.

Workout session:

1. Show workout overview.
2. Show each exercise with instructions, timer or reps.
3. Allow pause, easier version, and skip.
4. Finish session and record completion.

Completion:

1. Save workout date, duration, type, comeback flag, minimum flag, alternatives used, and feedback.
2. Ask difficulty and energy-after feedback.
3. Update progress.
4. Show a supportive message.

## Workout Concepts

Daily options:

| Option | Duration | Purpose |
|---|---:|---|
| Minimum | 3-5 min | Keep the habit alive |
| Standard | 8-12 min | Balanced daily movement |
| Extended | 20-30 min | Stronger session for high-energy days |

Comeback Mode activates after missed days and recommends a gentle restart:

| Missed Days | Comeback Suggestion |
|---:|---|
| 3 days | 5-minute light full-body |
| 7 days | 3-5 minute mobility and easy strength |
| 14+ days | gentle restart session |

Example comeback message:

> Welcome back. No need to make up for missed days. Let's restart gently.

Return Chain rewards returning, not perfection. It tracks active days, return days, comeback completions, minimum workouts, and consistency over time.

## Success Metrics

Track:

- Day 1, Day 7, Day 14, and Day 30 retention
- completed minimum workouts
- Comeback Mode completions
- percentage of users who return after missed days
- average workouts per user per week
- user feedback on tone and difficulty

The MVP is done when a user can create a profile, get suitable workout options, complete a workout, use an easier alternative, miss several days, return through Comeback Mode, and see progress without guilt.

## Safety and Tone

Calis App provides general fitness guidance. It should not diagnose, treat, prescribe, or tell users to push through pain.

Required safety message:

> This app provides general fitness guidance. Stop if you feel pain, dizziness, or unusual discomfort. If you have a medical condition, injury, or concern, consult a qualified healthcare professional before starting exercise.

Exercise safety rules:

- prefer beginner-safe movements
- provide easier alternatives
- avoid high-impact exercises for comeback sessions
- respect sensitive areas
- suggest stopping if pain occurs
- include safety notes where needed

Comeback sessions should be easier than normal sessions. For longer breaks, use mobility, low-impact strength, gentle full-body movement, and short duration. Avoid high-intensity intervals, jumping, advanced movements, and long sessions.

Tone should be friendly, realistic, non-judgmental, simple, encouraging, and human.

Avoid phrases like:

- "No excuses"
- "You failed"
- "You lost your streak"
- "Go hard or go home"
- "Burn fat fast"
- "Crush your body"
- "Make up for missed days"
- "You are behind"

Prefer phrases like:

- "Small progress counts."
- "A short workout is still a workout."
- "You came back. That matters."
- "Today can be simple."
- "Let's restart gently."
- "No need to make up for missed days."
- "Choose the easier version if needed."
