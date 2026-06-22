# Candidate Architecture Patterns and Evaluation Plan

*Prepared: June 11, 2026*

## Table of Contents

- [Purpose](#purpose)
- [Recommended Direction](#recommended-direction)
- [MVP and Later Scope](#mvp-and-later-scope)
- [Candidate Architecture Patterns](#candidate-architecture-patterns)
- [Architecture Decision Matrix](#architecture-decision-matrix)
- [Pose Technology Matrix](#pose-technology-matrix)
- [Recommended MVP Architecture](#recommended-mvp-architecture)
- [Exercise Scope](#exercise-scope)
- [Evaluation Plan](#evaluation-plan)
- [Proposed Acceptance Gates](#proposed-acceptance-gates)
- [Delivery Phases](#delivery-phases)
- [Questions for Final Decision](#questions-for-final-decision)
- [Current Technical Facts](#current-technical-facts)
- [Sources](#sources)

## Purpose

This document reconsiders the Calis App MVP from the beginning. Previous stack
decisions are treated as candidates rather than constraints.

The product still aims to give non-medical form feedback from short exercise
clips. Computer vision (CV) must have a meaningful MVP role. The architecture
should minimize unsupported feedback, raw-video exposure, operational cost, and
work that does not help validate the product.

No pose model, VLM, exercise count, coaching model, or deployment pattern is
final until the evaluation plan is completed.

## Recommended Direction

Start with:

1. Two exercises and one required camera view per exercise.
2. Browser-side MediaPipe Pose Landmarker running after recording.
3. A browser quality gate before any telemetry is submitted.
4. Timestamped landmarks sent to a TypeScript analysis API.
5. Deterministic rep, phase, and form rules on the server.
6. Template-based feedback with confidence and retry states.
7. No raw-video upload or VLM dependency in the first usable version.
8. An optional LLM wording experiment after deterministic findings are reliable.
9. A separately consented research flow for collecting labeled test clips.

This path gives CV a real analytical role while keeping the first system
testable, inexpensive, and privacy-conscious.

## MVP and Later Scope

| Capability | Initial MVP | Later |
|---|---|---|
| Exercises | Two exercises | Add exercises only after separate validation |
| Camera setup | One required view per exercise | Multiple views and automatic view detection |
| Recording | Guided 5-15 second recording | Longer clips, imports, and automatic trimming |
| Pose inference | Browser, after recording | Live framing guidance or server fallback |
| Quality gate | Required joints, one person, framing, motion, and landmark confidence | Lighting estimation, view classification, and device-specific tuning |
| Rep and phase tracking | One state machine per dynamic exercise | Tempo, pauses, asymmetry, and more movement variants |
| Form analysis | Two or three visible, testable findings per exercise | Larger rule catalog and personalized thresholds |
| Feedback | Templates from approved findings | LLM wording from approved findings only |
| Confidence | Finding confidence plus retry/abstain state | Calibrated confidence by exercise, device, and view |
| Results | Summary, rep count, positive note, and one correction | Comparisons, trends, and recurring issues |
| History | Anonymous session or local recent history | Accounts, cloud history, and progress reports |
| Raw video | Remains on device by default | Optional research upload with separate consent |
| Analytics | Quality failures, completion, latency, retries, and rule versions | Cohort analysis and experiment dashboards |
| Scoring | None | Consider only after calibration and user research |

Keep these outside the initial MVP:

- live form correction
- automatic exercise recognition
- more than one person
- arbitrary exercises
- medical or injury-risk judgments
- personalized biomechanics
- overall form scores
- workout generation
- social or competitive features
- CV and VLM fusion

## Candidate Architecture Patterns

### P1: Browser CV, Browser Rules, Template Feedback

```txt
Local video -> browser pose -> browser rules -> template feedback
```

The video and landmarks stay on the device. This is the smallest privacy-first
prototype, but central rule updates, observability, and cross-device debugging
are weaker.

### P2: Browser CV, Server Rules, Template Feedback

```txt
Local video -> browser pose -> quality gate -> landmark telemetry
  -> TypeScript rules -> template feedback
```

This is the recommended MVP pattern. Raw video stays on the device while rules,
confidence, result validation, and versioning remain centralized.

Browser telemetry is user-controlled and can be modified. That is acceptable for
personal feedback, but it must not later be treated as proof for competition,
certification, or rewards.

### P3: Browser CV, Server Rules, LLM Wording

```txt
Local video -> browser pose -> server rules -> approved findings
  -> LLM wording -> output validation
```

The LLM receives findings, not video or raw landmarks. It can improve tone but
does not improve the underlying movement evidence.

### P4: Browser CV with Selective VLM Escalation

```txt
Local video -> browser pose -> server rules
  -> high confidence: deterministic result
  -> selected low confidence: consented VLM analysis
```

This can test whether a VLM adds value on ambiguous clips. It adds raw-video
transfer, provider terms, variable cost, latency, and conflict handling.

### P5: Parallel CV and VLM Fusion

```txt
Video -> CV evidence + VLM observations -> fusion rules -> feedback
```

This is a research architecture, not a default reliability upgrade. Both sources
must be compared with human labels, and disagreements require explicit
resolution and calibrated confidence.

### P6: Server CV, Server Rules, Optional Coaching

```txt
Uploaded video -> server pose service -> server rules -> feedback
```

This gives consistent compute and centralized media decoding, but introduces
video upload, storage controls, GPU or CPU infrastructure, queues, and higher
privacy responsibility.

### P7: VLM Primary, CV Quality Gate

```txt
Browser CV quality gate -> uploaded video -> VLM observations
  -> deterministic validation -> feedback
```

This is fast to prototype across exercises but has weaker measurement
repeatability. Current Gemini video processing samples at 1 FPS by default,
which may miss fast exercise phases unless sampling is configured and tested.

## Pattern Technology Composition

Quick reference for the pattern families above:

Patterns describe architecture shapes; options describe the specific decision candidates scored in the matrix below.

| Pattern | CV | VLM | LLM |
|---|---|---|---|
| P1 Browser CV, browser rules | Yes | No | No |
| P2 Browser CV, server rules | Yes | No | No |
| P3 P2 + LLM wording | Yes | No | Yes, text only |
| P4 Selective VLM escalation | Yes | Yes, on low-confidence cases | No |
| P5 Parallel CV and VLM fusion | Yes | Yes | No |
| P6 Server CV | Yes, server-side | No | No |
| P7 VLM primary + CV gate | Yes, gate only | Yes, primary analyzer | No |

P3 keeps the analysis CV-based and only uses an LLM to rephrase approved findings. P4, P5, and P7 are the patterns that actually use a VLM for vision analysis. The recommended MVP, P2, uses CV only.

## Architecture Decision Matrix

Use a two-step decision process: hard gates first, then weighted scoring.
Scores below are planning estimates to prioritize implementation and evaluation.

### Step 1: Hard Gates (Must Pass)

| Gate | Minimum Requirement |
|---|---|
| Safety language gate | No unsupported medical or diagnostic claims in validation set |
| Evidence gate | Inadequate evidence must return retry or abstention |
| Repeatability gate | Same input and same rule/model version produce identical deterministic findings |
| Privacy gate | Must match selected product policy for whether raw video can leave device |

Any option that fails a gate is disqualified for MVP regardless of weighted score.

### Step 2: Weighted Criteria

| Criterion | Weight | Scoring Guidance (1-5) |
|---|---|---|
| Form-finding precision and safety reliability | 30% | 1=high hallucination risk, 5=high precision under holdout testing |
| Privacy and raw-video exposure | 20% | 1=always uploads video, 5=video remains local by default |
| Evidence repeatability | 15% | 1=non-repeatable outputs, 5=deterministic stable outputs |
| Variable cost per analyzed session | 10% | 1=high provider dependency, 5=low predictable cost |
| End-to-end latency (p50/p95) | 10% | 1=often slow, 5=consistently responsive |
| Build and calibration complexity | 10% | 1=very high complexity, 5=low implementation burden |
| Exercise expansion flexibility | 5% | 1=hard to extend, 5=easy to add validated exercise variants |

Weighted score formula:

Total score = sum of (criterion score × weight) across all weighted criteria.

### Decision Options Evaluated

| Option ID | Option Summary | Scope Label | Source Pattern |
|---|---|---|---|
| O1 | Browser CV quality gate plus browser landmarks, server deterministic rules, template feedback | MVP Candidate | P2 |
| O2 | O1 plus LLM wording constrained to approved findings | Post-MVP Candidate | P3 |
| O3 | O1 plus selective VLM escalation only for predefined low-confidence cases | Post-MVP Candidate | P4 |
| O4 | VLM-primary analysis with browser CV quality gate and deterministic post-validation | Research Candidate | P7 |
| O5 | Browser CV telemetry to server heuristics engine plus LLM coaching from structured findings | Post-MVP Candidate | Dani architecture (O5) |

Note: O5 is the option that represents Dani's described architecture (CV landmarks -> server biomechanical heuristics -> LLM coaching text).

### Planning Scores (Pre-Benchmark)

| Option ID | Precision and Safety (30%) | Privacy (20%) | Repeatability (15%) | Cost (10%) | Latency (10%) | Complexity (10%) | Expansion (5%) | Weighted Total (0-5) |
|---|---|---|---|---|---|---|---|---|
| O1 | 4.0 | 5.0 | 5.0 | 4.0 | 4.0 | 3.5 | 3.0 | 4.25 |
| O2 | 4.0 | 5.0 | 5.0 | 3.5 | 3.5 | 3.0 | 3.5 | 4.13 |
| O3 | 4.0 | 3.5 | 4.0 | 2.5 | 2.5 | 2.5 | 4.0 | 3.53 |
| O4 | 3.0 | 2.0 | 2.5 | 2.5 | 3.0 | 3.5 | 4.5 | 2.88 |
| O5 | 4.0 | 5.0 | 4.5 | 3.5 | 3.5 | 3.0 | 4.0 | 4.08 |

### Decision Readout

| Rank | Option ID | Why It Ranks Here |
|---|---|---|
| 1 | O1 | Best MVP baseline for privacy, repeatability, and controlled deterministic behavior |
| 2 | O2 | Strong near-term upgrade once deterministic findings are stable |
| 3 | O5 | Strong alternative with explicit heuristics layer; should be benchmarked directly against O1 |
| 4 | O3 | Promising for edge cases but adds cost, consent complexity, and routing risk |
| 5 | O4 | Fast for broad exercise coverage but weaker repeatability and privacy profile |

Recommended execution order: O1 as MVP baseline, then benchmark O5 in parallel as the primary alternative, then add O2 if wording quality needs improvement.

## Pose Technology Matrix

| Technology | Browser | Server | Typical Output | License Consideration | MVP Assessment |
|---|---|---|---|---|---|
| MediaPipe Pose Landmarker | Strong official web support | Possible | 33 image and world landmarks, visibility, optional masks | MediaPipe repository is Apache 2.0; verify notices for distributed model assets | Recommended first choice |
| MoveNet Lightning/Thunder | Strong through TensorFlow.js | Strong through TensorFlow | 17 body keypoints and confidence | Published model is Apache 2.0 | Benchmark as browser fallback |
| Ultralytics YOLO-Pose | Possible through export/runtime work | Strong | Person boxes, 17 default keypoints, confidence | AGPL-3.0 or Enterprise license | Avoid for first commercial MVP unless licensing is resolved |
| MMPose/RTMPose | Possible with custom export | Strong | Model-dependent keypoints and confidence | Toolkit is Apache 2.0; verify each model and dataset | Good later server candidate |
| OpenPose | Generally impractical | Strong but compute-heavy | Body, hand, face, and foot keypoints | Default use is non-commercial; commercial license is separate | Exclude from MVP |

MediaPipe is the practical default because it has an official JavaScript API,
video tracking, 33 landmarks, world-coordinate output, and a permissive
repository license. Its web task is currently labeled as a preview, so pin the
package and model versions and test upgrades. MoveNet should still be benchmarked
on target devices because its 17-keypoint models may be faster.

## Recommended MVP Architecture

```txt
Exercise selection and fixed camera instructions
  -> record a short clip
  -> decode locally
  -> MediaPipe in a Web Worker
  -> quality and confidence gate
  -> compress timestamped landmarks and capture metadata
  -> Next.js analysis endpoint
  -> exercise state machine and deterministic rules
  -> prioritized findings and confidence
  -> template feedback
  -> save metadata and result
```

### Browser Responsibilities

- recording and local playback
- local video decoding
- pose inference in a Web Worker
- required-joint and one-person checks
- framing, motion, and confidence checks
- landmark smoothing and telemetry compression
- immediate retry guidance
- deletion of raw local processing data after completion

MediaPipe web inference calls can block the main thread, so the implementation
should use a worker and benchmark actual target devices.

### Server Responsibilities

- validate exercise, consent, schema, telemetry size, and timestamps
- reject impossible or incomplete landmark sequences
- calculate normalized angles and distances
- identify movement phases through a state machine
- count complete repetitions
- apply exercise-specific rules
- combine quality, landmark, phase, and rule confidence
- return a retry when evidence is inadequate
- produce approved findings and template feedback
- store result metadata, model version, and rule version

### Optional LLM Boundary

An LLM may later rewrite approved findings into concise coaching. It must not
receive raw video, add findings, change severity, or override confidence. The
deterministic result must remain usable when the LLM is unavailable.

### Research Data Boundary

Production analysis should not require video upload. Create a separate research
flow where participants explicitly consent to temporary clip retention and
human annotation. Do not silently repurpose production videos for calibration.

## Exercise Scope

Recommended first exercises:

| Exercise | Required View | Initial Outputs | Why |
|---|---|---|---|
| Push-up | Side | Rep count, phases, approximate depth, body-line consistency | Core calisthenics movement with visible dynamic phases |
| Squat | Side | Rep count, phases, approximate depth, torso consistency | Tests a different joint chain and broadens product evidence |

Limit each exercise to two or three findings that are visible from the required
view. Do not attempt front-view knee tracking, hidden-joint claims, pain
assessment, or injury-risk prediction from a side-view clip.

If reducing technical risk is more important than exercise breadth, replace the
squat with a plank. This gives one dynamic exercise and one simpler static hold.

## Evaluation Plan

### 1. Define the Claim Catalog

For every finding, specify:

- required camera view and visible landmarks
- measurement or phase evidence
- rule and threshold
- minimum confidence
- retry conditions
- user-facing correction
- known unsupported variants

A finding without a human-labeling rubric must not ship.

### 2. Build a Calibration Dataset

Use two stages:

| Stage | Suggested Size | Purpose |
|---|---|---|
| Engineering spike | 40-60 varied clips per exercise | Test feasibility, camera guidance, model speed, and candidate rules |
| MVP validation | At least 150 varied clips per exercise | Calibrate rules and evaluate a participant-separated holdout set |

Include different phones, browsers, lighting, clothing, body proportions,
movement speeds, correct attempts, incorrect attempts, and deliberately unusable
recordings. These numbers are starting targets, not proof of population-wide
validity.

Use separate participants for calibration and final holdout testing. Otherwise,
rules may overfit individual movement patterns.

### 3. Create Human Reference Labels

Use at least two qualified reviewers for the holdout clips. Label:

- clip usability
- visible exercise and camera view
- repetition count
- movement phases
- approved form findings
- uncertain or unobservable findings

Resolve disagreements before comparing systems. Tool-to-tool agreement is not
accuracy.

### 4. Benchmark Pose Models

Run MediaPipe and MoveNet on the same clips and target devices. Compare:

- required-landmark coverage
- confidence dropouts
- coordinate jitter
- phase stability
- rep-count performance after equivalent rules
- processing time and memory
- worker failures and browser compatibility

Choose the model from measured product performance, not general model claims.

### 5. Validate Rules and Confidence

Measure:

- exact rep-count rate and mean absolute error
- phase detection precision, recall, and timing error
- finding precision and recall
- false confident findings
- quality-gate false acceptance and false rejection
- confidence calibration
- deterministic repeatability

Optimize high-confidence finding precision before recall. Missing a minor issue
is preferable to confidently inventing one.

### 6. Validate Product Experience

Measure:

- recording completion rate
- quality-gate rejection rate
- successful retry rate
- time from recording end to feedback
- user understanding of the correction
- user trust in the result
- second-attempt rate
- reported usefulness of the next result

A technically accurate system that repeatedly rejects normal users is not a
successful MVP.

### 7. Evaluate VLM Value Separately

After the CV baseline is stable, run a consented offline comparison:

| System | Evaluation |
|---|---|
| CV rules only | Baseline against human labels |
| VLM only | Same clips and label rubric |
| CV with selective VLM escalation | Test only predefined low-confidence cases |
| Parallel fusion | Test only if escalation shows complementary value |

Compare every system with human labels. Do not promote a system because it
agrees with another automated system.

## Proposed Acceptance Gates

These are initial decision targets and should be adjusted after the engineering
spike.

| Metric | Proposed Gate |
|---|---|
| Usable clips rejected by quality gate | 10% or less |
| Unusable clips correctly rejected | 85% or more |
| Exact rep count on accepted clips | 95% or more |
| High-confidence form finding precision | 90% or more |
| High-confidence form finding recall | 70% or more |
| Same input and rule version | Identical deterministic findings |
| Inadequate evidence | Always returns retry or abstention |
| Unsupported or medical claim | Zero in the validation set |
| Local processing failure | 5% or less on supported target devices |
| End-to-end latency | Set after device spike; report p50 and p95 |
| User-rated understandable feedback | 80% or more |

Failure to reach a gate should narrow the supported devices, views, exercises,
or findings before adding another model.

## Delivery Phases

### Phase 0: Feasibility

- implement local recording and worker-based MediaPipe
- test target phones and browsers
- define push-up and squat labeling rubrics
- collect the engineering-spike dataset
- decide whether MoveNet must remain a fallback

### Phase 1: Deterministic Vertical Slice

- quality gate
- landmark telemetry schema
- one exercise state machine
- rep counting
- one positive note and one correction
- confidence and retry
- template feedback
- operational metrics

Ship internally with one exercise before generalizing the rule system.

### Phase 2: MVP

- second exercise
- final holdout evaluation
- short recording guidance
- anonymous or local history
- user testing and retry loop
- explicit privacy and research consent

### Phase 3: Measured Enhancements

- optional LLM wording
- live framing guidance
- third exercise
- accounts and progress history
- selective VLM experiment
- server pose fallback only if device benchmarks justify it

## Questions for Final Decision

### Product

1. What is the primary MVP promise: reliable rep counting, form correction, or
   both?
2. Which two exercises matter most to the first users?
3. Will users accept one strict camera view and setup instructions per exercise?
4. Is post-recording feedback sufficient, or is live framing required?
5. Is one prioritized correction enough for the first result?
6. Which is worse for the product: missing an issue or reporting a false issue?

### Users and Devices

7. Which browsers and minimum phone classes must be supported?
8. Is desktop upload important, or is mobile recording the main flow?
9. Will the first launch serve users in the EEA, United Kingdom, or Switzerland?

### Privacy and Data

10. Must raw video always remain on the device in normal production use?
11. Can you recruit users who separately consent to temporary research-video
    upload and human review?
12. Do you need accounts and cloud history for product validation, or can recent
    history stay local?

### Feedback and AI

13. Is an LLM required for launch, or are carefully written templates acceptable?
14. If a VLM is used, may video be sent to a paid external provider?
15. Should VLM analysis be routine, user-requested, or only a research
    experiment?

### Delivery and Validation

16. What is the launch deadline and how many engineers are available?
17. Do you have access to a trainer, physiotherapist, or other qualified reviewer
    to define and label observable form findings?
18. How many participants and target devices can you recruit for validation?
19. Are the proposed acceptance gates strict enough for your risk tolerance?
20. Is the product commercial and closed-source, or can AGPL software be used?

The minimum answers needed to finalize the architecture are 1, 2, 3, 6, 7, 10,
11, 13, 16, 17, and 20.

## Current Technical Facts

These facts were verified on June 11, 2026 and may change:

- MediaPipe Pose Landmarker has an official JavaScript package, video mode,
  confidence controls, 33 landmarks, and world-coordinate output.
- The MediaPipe web task is currently labeled as a preview, so version pinning
  and regression testing are required.
- MediaPipe web detection calls are synchronous and should be moved off the main
  thread for video processing.
- MoveNet provides 17 keypoints and Lightning and Thunder variants intended for
  different latency and accuracy needs.
- Ultralytics pose models use AGPL-3.0 or Enterprise licensing.
- OpenPose is free for non-commercial use; commercial use requires separate
  licensing.
- Gemini supports video and timestamps, but File API video is sampled at 1 FPS
  by default. Fast action may lose detail unless sampling is configured and
  validated.
- Gemini video uses approximately 300 input tokens per second at default media
  resolution or 100 at low resolution before output tokens.
- Gemini structured output can enforce a supported JSON Schema subset.
- Gemini Files API uploads are retained for up to 48 hours unless manually
  deleted sooner.
- Gemini paid-service prompts and responses are not used to improve Google's
  products. Provider logging, processing location, and contract terms still
  require review.
- Gemini API clients made available to users in the EEA, Switzerland, or the
  United Kingdom may use only Paid Services under the current additional terms.

## Sources

- [MediaPipe Pose Landmarker for Web](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/web_js)
- [MediaPipe Apache 2.0 License](https://github.com/google-ai-edge/mediapipe/blob/master/LICENSE)
- [MoveNet Tutorial](https://www.tensorflow.org/hub/tutorials/movenet)
- [MoveNet Model and License](https://tfhub.dev/google/movenet/multipose/lightning/1)
- [Ultralytics Pose Documentation](https://docs.ultralytics.com/tasks/pose)
- [Ultralytics Licensing](https://docs.ultralytics.com/)
- [MMPose Repository and License](https://github.com/open-mmlab/mmpose)
- [OpenPose Repository and License Notice](https://github.com/CMU-Perceptual-Computing-Lab/openpose)
- [Gemini Video Understanding](https://ai.google.dev/gemini-api/docs/video-understanding)
- [Gemini Structured Outputs](https://ai.google.dev/gemini-api/docs/structured-output)
- [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini Files API](https://ai.google.dev/gemini-api/docs/files)
- [Gemini API Additional Terms](https://ai.google.dev/gemini-api/terms)
