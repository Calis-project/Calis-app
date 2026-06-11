# Product Spec

## Table of Contents

- [Product](#product)
- [Users](#users)
- [MVP Scope](#mvp-scope)
- [Core Experience](#core-experience)
  - [First Use](#first-use)
  - [Analysis](#analysis)
  - [Feedback](#feedback)
  - [History and Return](#history-and-return)
- [Privacy](#privacy)
- [Safety and Tone](#safety-and-tone)
- [Success](#success)

## Product

Calis App is a Next.js web app with PWA capabilities that helps people improve
calisthenics form at home through short-video analysis and supportive feedback.

```txt
Choose exercise -> record or upload -> analyze -> review feedback -> retry or save
```

The MVP tests whether users will submit a clip, trust structured feedback, and
apply it to a later attempt.

> Better form comes from small, repeatable corrections, not shame.

Calis App provides general fitness guidance. It is not a medical,
physiotherapy, bodybuilding, or generic chatbot product.

## Users

The primary users are beginner-to-intermediate, self-guided calisthenics users
who train at home and want:

- clear feedback without access to a coach
- gradual, low-pressure improvement
- safety-conscious guidance
- a simple record of attempts and recurring issues

## MVP Scope

Supported exercises:

- push-up
- squat
- plank
- lunge
- hollow hold

Required capabilities:

| Capability | Requirement |
|---|---|
| Exercise selection | Show only supported exercises |
| Setup guidance | Explain camera position, visibility, lighting, and safety |
| Video capture | Record or upload a short browser-compatible clip |
| Validation | Check exercise, format, duration, and size |
| Analysis | Produce confidence-scored, exercise-specific findings |
| Coaching | Explain approved findings without inventing evidence |
| Feedback | Show positive notes and one or two prioritized corrections |
| Retry | Let the user immediately record another attempt |
| History | Save metadata and feedback without retaining source video |
| Progress | Show attempts and improvement without score-first judgments |
| Safety | Validate supported scope and non-medical language |

Later features may include before-and-after comparison, reminders, manual notes,
broader exercise support, optional scoring, and consent-based video retention.

Out of scope:

- live form correction
- medical diagnosis, treatment, or rehabilitation
- workout or nutrition planning as the main flow
- social feeds, leaderboards, or competitive rankings
- wearables, long-form coaching chat, or advanced analytics dashboards
- raw video storage by default

## Core Experience

### First Use

Introduce the product promise, privacy posture, and safety limits. Collect only
the profile information needed for useful feedback, such as experience level,
focus exercises, sensitive areas, and consent.

### Analysis

1. Select a supported exercise.
2. Review recording and safety guidance.
3. Record or upload a short clip.
4. Validate and submit the media.
5. Process the clip and discard the source video.
6. Show feedback with confidence and prioritized corrections.
7. Retry, save the result, or review exercise guidance.

If the clip is unsuitable or evidence is weak, request another recording with
clear guidance instead of returning confident feedback.

### Feedback

Each result should contain:

- a short summary
- positive observations
- issue label and severity
- timestamp or approximate moment when available
- a plain-language explanation
- a concrete cue for the next attempt
- a safety flag when relevant
- visible confidence or uncertainty

Avoid an overall score in the MVP. The screen should focus attention on the
smallest useful correction rather than overwhelm the user.

### History and Return

History shows saved sessions by exercise and date, including feedback, repeated
issues, and positive observations. Progress is represented through attempts and
improvements rather than strict scores.

After a practice gap, the app may suggest one supported exercise and a short
attempt without asking the user to make up missed days.

## Privacy

- Use video only for the requested analysis.
- Discard source video and temporary frames after processing.
- Store required metadata and feedback, not raw media.
- Explain before submission what is processed, stored, and discarded.
- Require explicit opt-in before the first analysis.
- Require separate explicit consent for any future video retention.
- Separate movement data from direct identity.
- Never use footage for biometric identification.

Exercise footage is personal data when a person can be identified.
Movement-derived information may qualify as health data depending on its use.

Display:

> This app is not medical or physiotherapy advice.

## Safety and Tone

Display this safety message:

> This app provides general fitness guidance and AI-assisted form feedback. Stop
> if you feel pain, dizziness, or unusual discomfort. If you have a medical
> condition, injury, or concern, consult a qualified healthcare professional
> before starting exercise.

Feedback must:

- analyze only supported exercises and visible evidence
- acknowledge uncertainty caused by framing, lighting, occlusion, or motion
- use plain, supportive, non-judgmental language
- provide concrete corrections and easier variations when appropriate
- respect sensitive areas and recommend stopping when pain appears

Feedback must not diagnose, prescribe treatment, claim certainty about injury
risk, encourage training through pain, shame the user, or promise rapid results.

## Success

Track:

- first-analysis completion rate
- retry rate after feedback
- analysis completion and failure rates
- attempts per supported exercise
- reduction of repeated issues across saved attempts
- user trust in feedback
- Day 1, Day 7, Day 14, and Day 30 retention

The MVP is complete when a user can select a supported exercise, submit a short
video, receive safe structured feedback, retry, save metadata-only history, and
return later to review progress.
