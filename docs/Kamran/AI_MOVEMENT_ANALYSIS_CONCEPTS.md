# AI Movement Analysis Concepts and Tools

## Purpose

This guide defines the concepts needed to understand AI-assisted movement
analysis in Calis App. Product and implementation decisions remain authoritative
in [Roadmap and Decisions](ROADMAP_AND_DECISIONS.md),
[Technical Plan](TECHNICAL_PLAN.md), and
[AI Movement Analysis Stack Report](AI_Movement_Analysis_Stack_Report.md).

The key distinction is:

- **Visual observation** describes visible movement, timing, framing, and
  alignment from video.
- **Pose estimation** converts images into structured body landmarks.
- **Movement analysis** turns observations or landmarks into confidence-scored
  findings using exercise-specific rules.
- **LLM coaching** explains approved findings in clear, supportive language.

These components support fitness feedback, not medical diagnosis or
physiotherapy advice.

## Essential Concepts

### Computer Vision and Pose Estimation

**Computer vision** extracts information from images and video. In Calis App, it
supports exercise observation, movement-phase estimation, and body-position
analysis.

**Pose estimation** predicts body landmarks such as shoulders, elbows, hips,
knees, and ankles. A landmark normally includes image coordinates and a
confidence or visibility value.

Pose estimation provides measurements; it does not determine whether an
exercise is correct. That decision belongs to the analysis engine.

### 2D Pose, 3D Pose, and Tracking

**2D pose** locates landmarks on the image plane. It is practical for browser
use but sensitive to camera angle and perspective.

**3D pose** also estimates depth. With one consumer camera, depth is inferred
and should not be treated as motion-capture-quality data.

**Tracking** connects observations across frames to estimate repetitions,
movement phases, tempo, and alignment changes. Occlusion, fast motion,
incomplete framing, or multiple people can reduce reliability.

### Biomechanics and Rule-Based Analysis

**Biomechanics** describes movement through measurements such as joint angles,
alignment, range of motion, velocity, and balance. Video-derived measurements
are approximations.

**Rule-based analysis** applies explicit exercise-specific logic to normalized
evidence. For example, a squat rule may evaluate estimated depth during the
bottom phase.

Rules make findings repeatable and testable, but thresholds must be validated
across camera positions, body types, clothing, and movement variations.

### Confidence

Confidence expresses how certain a provider or analysis stage is about an
observation. Calis App must preserve confidence from visual observations through
analysis and final feedback.

When important evidence is uncertain or hidden, the app should request a better
recording instead of presenting precise feedback. Confidence does not indicate
that an exercise is safe or correct.

### VLMs, LLMs, and Hybrid Analysis

A **vision-language model (VLM)** interprets visual content and language. For the
MVP, a Gemini video-capable model provides temporal observations such as
estimated reps, phases, alignment, and media quality.

A **large language model (LLM)** converts structured findings into concise
coaching. It must not invent measurements, diagnoses, or unsupported issues.

Calis App uses a **hybrid approach**:

1. A VLM produces structured, confidence-scored observations.
2. The analysis engine normalizes observations and applies deterministic rules.
3. An LLM explains the resulting evidence.
4. Schema and safety checks validate the response before display.

## Calis App Pipeline

```txt
Camera or uploaded video
  -> client and server media validation
  -> Gemini video observations
  -> observation normalization
  -> exercise-specific analysis rules
  -> structured findings with confidence
  -> LLM coaching from findings only
  -> safety and schema validation
  -> checklist feedback
```

| Stage | Responsibility |
|---|---|
| Capture | Record a short exercise clip |
| Validation | Check exercise, duration, format, size, and basic media quality |
| Vision provider | Return timestamped observations, estimates, and confidence |
| Analysis engine | Normalize evidence, apply rules, and prioritize findings |
| Coaching layer | Explain only the approved findings |
| Final validation | Reject unsupported, unsafe, or invalid output |

The analysis engine is the source of truth for findings, severity, priority, and
confidence. The coaching layer may change wording, not evidence.

## Relevant Tools

| Tool | Role in Calis App |
|---|---|
| Browser MediaRecorder API | MVP video capture |
| Gemini video-capable model | Preferred MVP source of temporal observations |
| MediaPipe Pose Landmarker | Later browser quality gate for framing and body visibility |
| MoveNet | Possible alternative browser pose model |
| FFmpeg | Optional server-side media conversion or frame extraction |
| CVAT or Label Studio | Test-data annotation and output review |

OpenPose, MMPose, TensorFlow.js, ONNX Runtime Web, and image-capable providers
remain possible research or fallback options. They are not required for the MVP.
Specific models, versions, formats, quotas, prices, browser support, and licenses
must be verified during implementation.

## Recommended MVP Approach

1. Record short clips with the browser MediaRecorder API.
2. Validate media in a Next.js route handler.
3. Send the transient clip to Gemini through a server-side provider adapter.
4. Normalize observations, estimated reps and phases, media-quality indicators,
   and confidence.
5. Apply deterministic rules for push-ups, squats, planks, lunges, and hollow
   holds.
6. Give the LLM only structured analysis evidence.
7. Validate the coaching and show positive findings plus one or two corrections.
8. Discard raw video after processing and store only required metadata and
   feedback.

Browser-side MediaPipe is deferred to a later pre-submission quality gate. It is
not the primary MVP analyzer.

## Limits and Safety

- Camera angle, lighting, occlusion, clothing, framing, and motion speed affect
  accuracy.
- Single-camera measurements and provider observations are estimates, not
  clinical or pose-grade measurements.
- Fast movement requires testing because video providers may sample frames.
- Exercise rules require validation with varied recordings.
- Insufficient evidence should produce a retry request, not confident feedback.
- Feedback must describe visible movement and avoid diagnoses or medical advice.
- Raw video must be transient by default and excluded from logs.
- Movement data should be separated from direct identity.
- Users must explicitly opt in before their first analysis.
- Display: "This app is not medical or physiotherapy advice."
