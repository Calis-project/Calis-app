# AI Movement Analysis Concepts and Tools

| Document status | Value |
|---|---|
| **Status** | Reference; non-normative |
| **Owns** | Stable terminology, technical concepts, and general limitations |
| **Does not own** | Product scope, supported exercises, safety policy, architecture selection, or delivery planning |
| **Last reviewed** | 2026-08-24 |
| **Precedence** | [Product Spec](PRODUCT_SPEC.md) governs product scope and safety; [Candidate Architecture Patterns and Evaluation Plan](CANDIDATE_ARCHITECTURE_PATTERNS_AND_EVALUATION_PLAN.md) governs pending architecture options and experiments. Those documents prevail if this guide conflicts with either. |

## Table of Contents

- [Purpose](#purpose)
- [Essential Concepts](#essential-concepts)
  - [Computer Vision and Pose Estimation](#computer-vision-and-pose-estimation)
  - [Common Pose Tools and Models](#common-pose-tools-and-models)
  - [2D Pose, 3D Pose, and Tracking](#2d-pose-3d-pose-and-tracking)
  - [Rep and Phase Tracking](#rep-and-phase-tracking)
  - [Biomechanics and Rule-Based Analysis](#biomechanics-and-rule-based-analysis)
  - [Confidence](#confidence)
  - [Quality Gates and Validation](#quality-gates-and-validation)
  - [VLMs, LLMs, and Hybrid Analysis](#vlms-llms-and-hybrid-analysis)
- [Composable Analysis Pipeline](#composable-analysis-pipeline)
- [Relevant Tools](#relevant-tools)
- [Limits and Safety](#limits-and-safety)

## Purpose

This guide defines concepts used when discussing AI-assisted movement analysis.
It does not select an implementation. See the
[Product Spec](PRODUCT_SPEC.md) for product requirements and the
[Candidate Architecture Patterns and Evaluation Plan](CANDIDATE_ARCHITECTURE_PATTERNS_AND_EVALUATION_PLAN.md)
for the options currently under evaluation.

The key distinction is:

- **Visual observation** describes visible movement, timing, framing, and
  alignment from video.
- **Pose estimation** converts images into structured body landmarks.
- **Movement analysis** turns observations or landmarks into confidence-scored
  findings using exercise-specific rules.
- **Language-model coaching** can explain approved findings in clear,
  supportive language.

These concepts concern fitness feedback rather than medical diagnosis or
physiotherapy advice. The Product Spec owns the applicable safety requirements.

## Essential Concepts

### Computer Vision and Pose Estimation

**Computer vision** extracts information from images and video. In movement
analysis, it can support exercise observation, phase estimation, and
body-position analysis.

**Pose model** is an AI model that detects a person's body position from an
image or video.

**Pose estimation** is the process of using a pose model to predict body
landmarks.

**Body landmarks** are detected points on the body, such as shoulders, elbows,
wrists, hips, knees, and ankles. Each point usually has coordinates and a
confidence or visibility value.

Pose estimation provides measurements; it does not by itself determine whether
an exercise is correct.

### Common Pose Tools and Models

- **MediaPipe Pose Landmarker** is Google's lightweight pose model and toolkit,
  commonly used in browsers and mobile apps.
- **MoveNet** is a fast TensorFlow pose model designed for real-time use.
- **YOLO-Pose** detects people and their body landmarks, and is commonly run on
  servers with GPU support.
- **OpenPose** is a compute-heavy pose system that can detect body, hand, and
  facial landmarks.

**Browser inference** runs the pose model on the user's device. **Server
inference** uploads the video or frames and runs the model on backend hardware.
MediaPipe and MoveNet support both and are commonly used in browsers. YOLO-Pose
is usually server-hosted but can use a compatible browser runtime. OpenPose is
normally server-hosted; browser use requires a custom build and is generally
impractical.

### 2D Pose, 3D Pose, and Tracking

**2D pose** locates landmarks on the image plane. It is practical for browser
use but sensitive to camera angle and perspective.

**3D pose** also estimates depth. With one consumer camera, depth is inferred
and is not equivalent to motion-capture-quality data.

**Tracking** connects observations across frames to estimate repetitions,
movement phases, tempo, and alignment changes. Occlusion, fast motion,
incomplete framing, or multiple people can reduce reliability.

### Rep and Phase Tracking

Pose landmarks can be tracked across frames to identify movement phases. A
**state machine** defines the expected sequence, such as standing, lowering,
bottom, rising, and standing for one squat repetition.

**Landmark smoothing** reduces frame-to-frame noise before angles, phases, or
repetitions are calculated. Requiring complete phase transitions is one way to
avoid counting partial repetitions.

### Biomechanics and Rule-Based Analysis

**Biomechanics** describes movement through measurements such as joint angles,
alignment, range of motion, velocity, and balance. Video-derived measurements
are approximations.

**Rule-based analysis** applies explicit exercise-specific logic to normalized
evidence. For example, a squat rule may evaluate estimated depth during the
bottom phase.

Exercise-specific rule sets can define valid phases, complete repetitions,
joint-angle or alignment thresholds, timing, and minimum landmark confidence.
Rules make findings repeatable and testable; threshold validation commonly uses
varied camera positions, body types, clothing, and movement variations.

### Confidence

Confidence expresses how certain a provider or analysis stage is about an
observation. Preserving it between stages allows later logic to distinguish
strong from weak evidence.

An uncertainty policy can map hidden or weak evidence to a retry request instead
of precise feedback. Confidence does not indicate that an exercise is safe or
correct.

### Quality Gates and Validation

A **pre-upload quality gate** uses browser checks or pose estimation to reject a
clip when required joints are hidden, framing is unsuitable, or confidence is
too low. A **confidence gate** similarly prevents uncertain evidence from
becoming a form finding.

Calibration compares rules and thresholds with varied, human-labeled clips.
Typical validation measures include incorrect findings, missed issues,
rep-count error, and appropriate rejection of low-quality clips.

### VLMs, LLMs, and Hybrid Analysis

A **vision-language model (VLM)** interprets visual content and language. For the
same task, a VLM may receive native video, individual images, or a storyboard
containing timestamped frames. Its useful outputs can include qualitative
observations about movement, context, equipment, framing, and image quality.

A **large language model (LLM)** can convert structured findings into concise
coaching. Schema-conforming output is not proof that a visual claim is correct,
so evidence and validation remain important.

A **hybrid approach** combines two or more analysis methods. Possible role
boundaries include:

- CV or pose estimation measures landmarks, phases, angles, and timing.
- A VLM interprets selected frames or video and broader visual context.
- Deterministic code normalizes evidence, applies rules, and validates outputs.
- An LLM or templates turn approved findings into user-facing language.

An architecture may use any subset of these components and assign their roles
differently. CV is repeatable but sensitive to camera position, occlusion,
landmark error, and rule quality. A VLM handles context more flexibly but may be
inconsistent or produce unsupported observations. Neither is ground truth.

## Composable Analysis Pipeline

The following is a vocabulary map, not a prescribed product pipeline. Optional
stages depend on the candidate being evaluated.

```txt
Camera or uploaded video
  -> media validation or quality gate (optional)
  -> CV measurements and/or selected frames or native video
  -> VLM observations (optional)
  -> normalization and deterministic analysis (optional)
  -> structured findings with evidence and confidence
  -> templates or language-model coaching (optional)
  -> output validation
  -> user feedback
```

| Stage | Responsibility |
|---|---|
| Capture | Record a short exercise clip |
| Input validation | Check duration, format, size, and basic media quality |
| CV or pose stage | Produce measurements or select evidence when included |
| VLM stage | Return evidence-linked visual observations when included |
| Analysis stage | Normalize evidence and apply deterministic rules when included |
| Coaching stage | Present approved findings using templates or an LLM |
| Output validation | Check structure, evidence references, and allowed content |

Explicit contracts between included stages help distinguish measured evidence,
model observations, validated findings, and presentation text.

## Relevant Tools

| Tool | Possible role |
|---|---|
| Browser MediaRecorder API | Browser video capture |
| Gemini video-capable model | VLM analysis of native video or image evidence |
| MediaPipe Pose Landmarker | Browser or server pose estimation and quality checks |
| MoveNet | Browser or server pose estimation |
| YOLO-Pose | Multi-person pose estimation, commonly server-hosted |
| OpenPose | Detailed pose estimation, commonly server-hosted |
| FFmpeg | Media conversion or frame extraction |
| CVAT or Label Studio | Test-data annotation and output review |

MMPose, TensorFlow.js, ONNX Runtime Web, and image-capable providers remain
possible research alternatives. Specific selections belong in the candidate
evaluation or a later accepted architecture decision. Versions, formats,
quotas, prices, browser support, and licenses can change and require verification
during implementation.

## Limits and Safety

This section summarizes technical limitations; it does not define product
policy. The [Product Spec](PRODUCT_SPEC.md) is authoritative for safety, privacy,
consent, retention, and user-facing claims.

- Camera angle, lighting, occlusion, clothing, framing, and motion speed affect
  accuracy.
- Single-camera measurements and model observations are estimates, not clinical
  or motion-capture-grade measurements.
- Sparse frame selection can miss fast transitions, extrema, or brief form
  issues.
- Pose landmarks can be incorrect even when their reported confidence is high.
- Structured VLM output can be syntactically valid while containing an
  unsupported visual claim.
- Exercise rules and confidence policies require validation with varied,
  human-labeled recordings.
- Sending frames or video to a provider creates different privacy and retention
  considerations from on-device processing.
