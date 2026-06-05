# Product Spec

## Product Summary

Calis App is a Next.js web app with PWA capabilities that helps people improve calisthenics exercise quality at home by analyzing short exercise videos and returning clear, supportive form feedback.

Core loop:

```txt
choose exercise -> record short video -> submit for AI analysis -> review checklist feedback -> retry or save progress
```

Core philosophy:

> Better form comes from small, repeatable corrections, not shame.

The app should feel practical, beginner-aware, privacy-conscious, and supportive. It is not a medical app, physical therapy app, bodybuilding app, shame-based scoring app, or generic AI chatbot.

PWA capabilities support the mobile experience through installability, quick return to practice, app-like navigation, and future reminders. They are not a separate product or codebase.

## Target Users

- Beginner-to-intermediate calisthenics users who train at home and want form feedback.
- Self-guided users who do not have a coach watching their technique.
- Users who want to improve core bodyweight exercises safely and gradually.
- Restarting users who need low-pressure progress tracking and encouragement after gaps.
- Cautious movers who need clear safety notes and reminders to stop when pain appears.

## MVP Scope

Goal: validate whether short-video AI analysis can help users recognize common form mistakes and improve exercise quality.

The MVP should answer:

> Will users record a short exercise clip, trust structured AI feedback, and use it to improve their next attempt?

Must-have features:

| Feature | Description |
|---|---|
| Supported Exercise List | Show the initial calisthenics exercises that can be analyzed |
| Exercise Setup Guidance | Explain camera angle, body position, visible range, and safety notes |
| Short Video Recording or Upload | Let users capture or upload a short clip from the browser |
| Video Validation | Check exercise selection, file type, duration, and size before submission |
| AI Form Analysis | Send the clip to a backend AI analysis service and receive structured feedback |
| Checklist Feedback | Show detected mistakes, severity, moments, and corrective tips |
| Positive Notes | Highlight what looked good so feedback does not feel purely negative |
| Retry Flow | Let users record another attempt after reviewing corrections |
| Form History | Save analysis results and metadata without retaining the source video |
| Supportive Progress | Track attempts and improvement without score-first or shame-based language |
| Safety Messaging | Make clear the app gives general fitness guidance, not medical advice |

Initial MVP exercises:

- push-up
- squat
- plank
- lunge
- hollow hold

Should-have features:

- before/after attempt comparison by checklist item
- difficulty feedback after analysis
- installable mobile web experience
- simple reminders to practice an exercise again
- lightweight comeback prompt after missed practice days
- manual notes for what the user wants to focus on next time

Out of scope for the first MVP:

- live real-time form correction
- medical diagnosis, injury treatment, or rehabilitation plans
- full workout generation as the main product flow
- nutrition planning
- social feeds, public leaderboards, or competitive rankings
- wearable integration
- long-form coaching chat
- retained raw video library by default
- advanced pose analytics dashboards

## App Flows

Suggested MVP navigation:

1. Analyze
2. History
3. Exercises
4. Profile

First launch introduces the core promise, privacy posture, and safety boundary, then starts a short profile setup.

Onboarding asks:

- What is your current calisthenics experience?
- Which exercises do you want to improve first?
- Do you have any areas you want to be careful with?
- Are you comfortable recording short clips for analysis?
- Do you want reminders or comeback support after missed practice days?

Analyze flow:

1. User selects a supported exercise.
2. App shows setup, camera, lighting, and safety guidance.
3. User records or uploads a short clip.
4. App validates duration, size, and format.
5. User submits the clip for analysis.
6. Backend analyzes the video and discards the source video after processing.
7. App shows structured feedback and suggested corrections.
8. User can retry, save the result, or view exercise guidance.

Feedback screen:

1. Show a short overall summary.
2. Show positive notes first or alongside corrections.
3. Show checklist items for detected issues.
4. For each issue, show severity, moment or timestamp when available, explanation, and correction.
5. Clearly mark safety-related feedback.
6. Offer one focused next attempt cue instead of overwhelming the user.

History flow:

1. User opens History.
2. App shows recent analysis sessions by exercise and date.
3. User can review saved AI feedback, common repeated issues, and positive notes.
4. App shows progress as practice attempts and improvements, not strict scores.

Comeback support:

1. If the user has not practiced recently, show a gentle return prompt.
2. Recommend one supported exercise and a short recording attempt.
3. Do not ask the user to make up missed days.

## Feedback Concepts

Checklist feedback should be structured and specific:

| Field | Purpose |
|---|---|
| Issue label | Name the form concern clearly |
| Severity | Help prioritize what matters most |
| Moment | Point to a timestamp or approximate part of the clip |
| Explanation | Explain what the AI observed in simple language |
| Correction | Give a concrete cue for the next attempt |
| Safety flag | Highlight feedback related to possible strain or risk |

Example issue:

```txt
Label: Hips dropping during plank
Severity: medium
Moment: around 8 seconds
Explanation: Your hips appear to lower as the hold continues.
Correction: Brace your core and shorten the hold before your position changes.
Safety related: true
```

The MVP should avoid score-first UX. A score can be explored later, but the first version should prioritize understandable corrections and user confidence.

## Privacy

Default MVP privacy posture:

- videos are used only for the requested analysis
- source videos are discarded after processing
- saved history stores metadata and feedback, not raw videos
- the app should make this behavior clear before recording or upload
- any future video retention must require explicit user consent

Stored history can include exercise ID, date, duration, analysis status, feedback, repeated issues, user notes, and whether the user saved the attempt.

## Success Metrics

Track:

- percentage of users who complete first video analysis
- percentage of users who record a retry after feedback
- analysis completion rate and failure rate
- average number of attempts per supported exercise
- repeated issue reduction across saved attempts
- user trust rating for AI feedback
- Day 1, Day 7, Day 14, and Day 30 retention
- comeback prompt completions after missed practice days

The MVP is done when a user can choose a supported exercise, record or upload a short video, receive structured AI feedback, retry after corrections, save analysis history without retaining the source video, and return later through a supportive progress flow.

## Safety and Tone

Calis App provides general fitness guidance. It should not diagnose, treat, prescribe, or tell users to push through pain.

Required safety message:

> This app provides general fitness guidance and AI-assisted form feedback. Stop if you feel pain, dizziness, or unusual discomfort. If you have a medical condition, injury, or concern, consult a qualified healthcare professional before starting exercise.

AI feedback must not:

- diagnose medical problems
- prescribe treatment
- claim certainty about injury risk
- tell users to continue through pain
- shame users for poor form
- promote rapid transformation
- use aggressive fitness language
- analyze unsupported exercises as if they are supported

AI feedback should:

- focus on common form observations
- use plain language
- give one or more concrete corrections
- suggest easier versions when appropriate
- respect sensitive areas from the user profile
- recommend stopping if pain appears
- keep confidence limits visible when feedback is uncertain

Avoid phrases like:

- "No excuses"
- "You failed"
- "Bad form"
- "Go hard or go home"
- "Crush your body"
- "Ignore the discomfort"
- "Perfect score"

Prefer phrases like:

- "Try this cue on the next attempt."
- "Small corrections add up."
- "Shorter, cleaner reps are still progress."
- "This is worth practicing gently."
- "Stop if this causes pain."
- "You came back. That matters."
