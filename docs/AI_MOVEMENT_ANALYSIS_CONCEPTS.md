# AI Movement Analysis Concepts and Tools

## Table of Contents

- [Purpose](#purpose)
- [Core Concepts](#core-concepts)
  - [Computer Vision](#computer-vision)
  - [Pose Estimation](#pose-estimation)
  - [Keypoints and Landmarks](#keypoints-and-landmarks)
  - [2D and 3D Pose](#2d-and-3d-pose)
  - [Tracking](#tracking)
  - [Biomechanics](#biomechanics)
  - [Rule-Based Analysis](#rule-based-analysis)
  - [Confidence Scores](#confidence-scores)
  - [Inference](#inference)
  - [Multimodal AI](#multimodal-ai)
  - [Vision-Language Models](#vision-language-models)
  - [Large Language Models](#large-language-models)
  - [Hybrid Analysis](#hybrid-analysis)
- [How the Concepts Connect in Calis App](#how-the-concepts-connect-in-calis-app)
- [Tools by Role](#tools-by-role)
  - [Video Capture and Processing](#video-capture-and-processing)
  - [Pose Estimation](#pose-estimation-tools)
  - [Browser Inference](#browser-inference)
  - [Visual Interpretation and Coaching](#visual-interpretation-and-coaching)
  - [Dataset Annotation and Evaluation](#dataset-annotation-and-evaluation)
- [Recommended Calis App Approach](#recommended-calis-app-approach)
- [Limits and Safety](#limits-and-safety)

## Purpose

This guide introduces the main concepts used in AI-assisted movement analysis and
shows where common tools fit. It is intended for technically curious beginners
and contributors to Calis App.

The current product architecture and implementation decisions are defined in
[Roadmap and Decisions](ROADMAP_AND_DECISIONS.md) and
[Technical Plan](TECHNICAL_PLAN.md). This guide explains the concepts behind
those decisions rather than defining a separate architecture.

The central distinction is:

- **Pose estimation** converts an image into structured body landmarks.
- **Visual observation** describes visible movement, timing, framing, and body
  alignment from video or sampled frames.
- **Movement analysis** converts normalized observations or landmarks over time
  into confidence-scored evidence and possible form issues.
- **A vision-language model (VLM)** interprets visual content in broader,
  less deterministic terms.
- **A large language model (LLM)** can turn structured findings into clear
  coaching language.

These components can support exercise feedback, but they do not make the app a
medical, diagnostic, or physiotherapy system.

## Core Concepts

### Computer Vision

**Computer vision** is the field of computing concerned with extracting useful
information from images and video. Tasks include recognizing objects, detecting
people, estimating body position, tracking movement, and describing a scene.

In Calis App, computer vision is the broad technical area that includes
interpreting exercise video, estimating movement phases, and locating relevant
body positions.

### Pose Estimation

**Pose estimation** predicts the positions of body joints or landmarks in an
image or video frame. A pose model may return coordinates for the shoulders,
elbows, wrists, hips, knees, ankles, and other points.

Pose estimation does not by itself decide whether an exercise is correct. It
provides structured measurements that a separate analysis layer can interpret.
Browser-side pose estimation is not the primary MVP analyzer in Calis App; it is
reserved for a later pre-submission quality gate.

### Keypoints and Landmarks

**Keypoints**, also called **landmarks**, are the body locations returned by a
pose-estimation model. A landmark commonly contains:

- an `x` and `y` image coordinate
- an optional depth or `z` estimate
- a visibility or confidence value

Landmarks can be connected into a simplified skeleton. A future Calis App pose
pipeline could use landmark sequences to calculate joint angles, movement
range, body alignment, and rep phases.

### 2D and 3D Pose

**2D pose estimation** locates landmarks on the image plane using horizontal and
vertical coordinates. It is comparatively simple and works well in browsers,
but camera angle and perspective can distort measurements.

**3D pose estimation** also attempts to estimate depth. A single-camera depth
value is normally inferred rather than directly measured, so it is not
equivalent to motion capture from calibrated cameras or physical sensors.

If pose estimation is added later, 2D landmarks with carefully specified camera
positions are more practical than treating estimated 3D coordinates as ground
truth.

### Tracking

**Tracking** connects detections or observations across consecutive frames so
the application can follow movement over time. Stable temporal evidence helps
estimate repetitions, movement phases, tempo, and changes in body alignment.

Tracking can fail when the body leaves the frame, joints are hidden, motion is
very fast, or multiple people are visible.

### Biomechanics

**Biomechanics** applies mechanical principles to human movement. Relevant
measurements can include joint angles, relative body alignment, range of motion,
velocity, and balance.

Video-derived biomechanics are approximations. Consumer camera footage, hosted
vision models, and pose models do not provide the precision of a calibrated
laboratory assessment. Calis App should present MVP rep, phase, and joint-angle
outputs as confidence-scored estimates, not clinical or pose-grade measurements.

### Rule-Based Analysis

**Rule-based analysis** applies explicit exercise-specific logic to normalized
evidence. For example, a squat rule could examine estimated knee and hip
positions near the bottom phase, while a push-up rule could monitor estimated
shoulder, elbow, hip, and ankle alignment.

Rules make feedback more repeatable and testable than asking a general-purpose
model to produce final coaching directly from raw video. Rules cannot make
approximate provider observations precise, so thresholds still need validation
across body types, camera positions, clothing, and movement variations.

### Confidence Scores

A **confidence score** estimates how certain a model or analysis stage is about
a prediction. A hosted vision provider may return confidence for an observation,
while pose tools often provide confidence or visibility for each landmark.

Calis App should carry confidence through provider observations, normalized
analysis evidence, and final feedback. If important movement evidence is
uncertain or hidden, the app should request a better recording instead of
producing precise-sounding feedback.

Confidence is not a probability that the exercise is safe or correct.

### Inference

**Inference** is the process of running a trained model on new input. In the MVP,
inference primarily means sending a short video to a hosted, video-capable vision
model. Later, it may also mean running a browser-side pose model to check
recording quality before submission.

Local inference improves privacy and can reduce API cost, while cloud inference
can provide larger models but requires network access and careful data handling.

### Multimodal AI

**Multimodal AI** can process more than one kind of input, such as text, images,
audio, or video. A multimodal system might receive exercise instructions
together with a short video or selected frames and return structured
observations.

Multimodal describes the supported input and output types; it does not guarantee
accurate pose measurement or exercise scoring.

### Vision-Language Models

A **vision-language model (VLM)** is a multimodal model that relates visual
content to language. It can describe images or video, answer questions about
visible content, and generate high-level observations.

For the Calis App MVP, a Gemini video-capable model is the preferred source of
temporal visual observations. Its estimated reps, phases, alignment, and angle
evidence must be normalized and confidence-scored before exercise rules use it.
A VLM should not be treated as a pose-grade joint-angle calculator or allowed to
produce unchecked final coaching directly from raw video.

### Large Language Models

A **large language model (LLM)** processes and generates language. Given
structured metrics and detected issues, an LLM can explain the result in a
supportive tone, prioritize a small number of corrections, and adapt wording for
beginners.

The analysis engine should determine the evidence. The LLM should explain that
evidence without inventing measurements, diagnoses, or unsupported conclusions.

### Hybrid Analysis

**Hybrid analysis** combines specialized and general-purpose components. The
current Calis App MVP design uses:

1. a video-capable vision provider for temporal observations
2. normalization and deterministic exercise rules for analysis evidence
3. an LLM coaching layer for user-friendly explanations
4. safety and schema validation before display

This separation keeps the evidence and coaching responsibilities testable.
Browser-side MediaPipe may be added later as a quality gate for camera angle,
full-body visibility, and clip usability, not as the primary analyzer.

## How the Concepts Connect in Calis App

```txt
Camera or uploaded video
  -> browser capture and client-side media checks
  -> Next.js route handler validation
  -> Gemini video-capable model
  -> normalized provider observations
  -> analysis engine rules and prioritization
  -> structured evidence with confidence
  -> LLM coaching from structured evidence only
  -> safety and schema validation
  -> checklist feedback shown to the user
```

Example responsibilities:

| Stage | Input | Output |
|---|---|---|
| Video capture | Camera stream or file | Short exercise recording |
| Server validation | Recording and exercise selection | Accepted media or supportive retry |
| Vision provider | Video and exercise instructions | Timestamped, confidence-scored observations |
| Observation normalization | Provider response | Stable internal observation shape |
| Analysis engine | Observations and exercise definition | Prioritized issues, positive findings, and evidence |
| Coaching generation | Analysis evidence | Concise user-facing explanations and cues |
| Validation | Generated feedback and evidence | Safe, supported result or retry request |

## Tools by Role

The tools below are representative options, not fixed dependencies. Exact
versions, model availability, browser support, licenses, quotas, and prices
should be verified during implementation.

### Video Capture and Processing

| Tool | Typical Role | Calis App Considerations |
|---|---|---|
| Browser MediaRecorder API | Record a camera or media stream in a web app | Natural fit for the Next.js client; output formats vary by browser |
| OpenCV | Read, transform, sample, and inspect images or video | Broad Python and C++ ecosystem; often better suited to backend experiments than a lightweight browser MVP |
| FFmpeg | Decode, convert, trim, and extract frames from media | Powerful server or command-line processing; requires careful resource limits and secure handling of uploaded files |

### Pose Estimation Tools

| Tool | Typical Role | Strengths | Tradeoffs |
|---|---|---|---|
| MediaPipe Pose Landmarker | Local body-landmark detection | Browser support, accessible setup, detailed landmark set | Accuracy depends strongly on visibility, camera position, and movement |
| MoveNet | Lightweight single- or multi-person pose estimation | Fast and suitable for interactive applications | Model and runtime integration require TensorFlow tooling |
| OpenPose | Multi-person body, hand, and face keypoints | Established research tool with broad keypoint coverage | Heavier setup and compute requirements |
| MMPose | Research and experimentation across many pose models | Flexible model collection and evaluation tooling | Python-focused and more complex than needed for an initial browser MVP |

### Browser Inference

| Tool | Typical Role | Calis App Considerations |
|---|---|---|
| TensorFlow.js | Run compatible machine-learning models in JavaScript | Useful for models such as MoveNet; performance varies by device and browser backend |
| ONNX Runtime Web | Run compatible Open Neural Network Exchange (ONNX) models in a browser | Offers flexibility across exported models; model conversion and operator support must be validated |

MediaPipe can also provide its own browser-oriented task runtime, so TensorFlow.js
or ONNX Runtime Web is not required when MediaPipe Pose Landmarker satisfies the
later pre-submission quality-gate use case.

### Visual Interpretation and Coaching

| Tool Family | Typical Role | Calis App Considerations |
|---|---|---|
| Google Gemini video-capable models | Native video interpretation and structured observation generation | Preferred MVP provider; test provider-side sampling and confidence on short exercise clips |
| OpenAI image-capable models | Image interpretation and language generation | Frame-sampling fallback or coaching from structured findings; verify current capabilities |
| Anthropic Claude image-capable models | Image interpretation and language generation | Frame-sampling fallback or coaching from structured findings; verify current capabilities |

Provider models change frequently. Calis App should select a currently supported
model through a server-side adapter and avoid coupling product behavior to one
version name. Native video input still involves provider-side frame sampling, so
the selected sampling configuration must be tested for fast exercise motion,
tempo, and transitions.

### Dataset Annotation and Evaluation

| Tool | Typical Role | Calis App Considerations |
|---|---|---|
| CVAT | Annotate images and video for computer-vision datasets | Useful for labeling movement phases, body regions, and expected form events |
| Label Studio | Configure general-purpose data-labeling workflows | Useful for human review of clips, issue labels, and model outputs |

These tools do not analyze exercise form by themselves. They help create and
review test data for validating the analysis engine.

## Recommended Calis App Approach

For a privacy-conscious and testable movement-analysis path:

1. Use the browser MediaRecorder API for short recordings.
2. Validate the selected exercise and media in a Next.js route handler.
3. Send the transient clip to a Gemini video-capable model through a server-side
   provider adapter.
4. Normalize timestamped observations, estimated reps and phases, approximate
   alignment or angle evidence, media-quality indicators, and confidence.
5. Apply deterministic rules for the five supported exercises: push-up, squat,
   plank, lunge, and hollow hold.
6. Send only structured analysis evidence to the LLM coaching layer.
7. Validate coaching against the evidence and safety rules before display.
8. Discard the raw video after processing and store only required metadata and
   feedback.

Browser-side MediaPipe is a later-roadmap pre-submission quality gate. It may
reject unusable framing, insufficient body visibility, or poor clip quality
before upload. MoveNet is a possible alternative if MediaPipe does not meet
browser performance or licensing needs. OpenPose and MMPose remain research or
future server-side pose-estimation options.

The analysis engine is the source of truth for findings, severity, priority, and
confidence. The LLM coaching layer may explain those findings, but it must not
add, remove, or change evidence.

The user experience should present checklist feedback, positive findings, and
one or two prioritized corrections rather than a score-first judgment.

## Limits and Safety

- Pose accuracy can degrade with poor lighting, occlusion, loose clothing,
  unusual camera angles, partial-body framing, fast movement, or floor exercises.
- A single camera cannot reliably recover every real-world depth measurement.
- Provider and landmark confidence must be considered before presenting
  movement estimates.
- Native video providers may sample frames internally, so fast movement and
  transitions require implementation-time sampling tests.
- Form rules require exercise-specific validation with varied test recordings.
- VLM and LLM output can be inconsistent or unsupported by the visible evidence.
- Feedback should describe observable movement, acknowledge uncertainty, and
  avoid diagnoses or medical advice.
- An identifiable exercise video is personal data. Movement-derived information
  may qualify as health data depending on its use, while biometric data receives
  special-category treatment when used for unique identification.
- Raw video must remain transient by default, and movement-derived data should
  be stored separately from direct identity.
- Explicit opt-in consent is required before the first analysis.
- Required disclaimer: "This app is not medical or physiotherapy advice."
