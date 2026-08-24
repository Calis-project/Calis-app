# Candidate Architecture Patterns and Evaluation Plan

*Prepared: June 11, 2026; updated: August 24, 2026*

> **Status:** Active architecture evaluation — decision pending
>
> **Owns:** Candidate patterns, option definitions, evidence packages, scoring,
> experiments, and architecture acceptance gates
>
> **Does not own:** Product scope, supported exercises, UX requirements, privacy
> policy, safety language, or an accepted production architecture
>
> **Last reviewed:** August 24, 2026
>
> **Precedence:** [Product Spec](PRODUCT_SPEC.md) controls product requirements.
> No production architecture is final until a separate architecture decision is
> accepted. The next implementation spike is O6-N; that is not an acceptance
> decision.

## Table of Contents

- [Purpose and Boundaries](#purpose-and-boundaries)
- [Candidate Architecture Patterns](#candidate-architecture-patterns)
- [Media Evidence Packaging Strategies](#media-evidence-packaging-strategies)
- [Storyboard Evidence Contract](#storyboard-evidence-contract)
- [Pattern Technology Composition](#pattern-technology-composition)
- [Architecture Decision Matrix](#architecture-decision-matrix)
- [Pose Technology Matrix](#pose-technology-matrix)
- [Evaluation Plan](#evaluation-plan)
- [Proposed Acceptance Gates](#proposed-acceptance-gates)
- [Open Architecture Inputs](#open-architecture-inputs)
- [Current Technical Facts](#current-technical-facts)
- [Sources](#sources)

## Purpose and Boundaries

This document compares possible AI movement-analysis architectures. Previous
stack decisions are treated as candidates rather than constraints.

The [Product Spec](PRODUCT_SPEC.md) is the only authority for product behavior
and supported exercises. Architecture validation may proceed one exercise at a
time without redefining that product scope.

No pose model, VLM, CV role, coaching model, media package, or deployment pattern
is final until the evaluation plan is completed. O1 remains a comparison
baseline because it is deterministic; O6-N is the next spike because it isolates
the fixed-rate storyboard/VLM hypothesis without pose CV.

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

This is the deterministic comparison baseline. Raw video stays on the device
while rules, confidence, result validation, and versioning remain centralized.

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

This can test whether a VLM adds value on ambiguous clips. It adds consented
identifiable-media transfer through native video or selected frames, provider
terms, variable cost, latency, and conflict handling.

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
Browser CV quality gate -> uploaded video or uniform storyboard -> VLM observations
  -> deterministic validation -> feedback
```

This is fast to prototype across exercises but has weaker measurement
repeatability. With native video, current Gemini processing samples at 1 FPS by
default, which may miss fast exercise phases unless sampling is configured and
tested.

### P8: CV-Directed Storyboard with Structured Fusion

```txt
Local video -> browser pose at an adequate cadence -> smoothing and state machine
  -> deterministic phase, extrema, velocity, and rule-event selection
  -> bounded timestamped storyboard plus compact CV manifest
  -> one VLM request -> deterministic fusion and abstention -> feedback
```

This pattern gives CV an analytical role rather than using it only as a quality
gate. CV remains authoritative for numeric angles, repetition boundaries,
movement phases, and timing. The VLM receives selected raw frames for qualitative
visible context and must cite supplied frame IDs for every accepted observation.

P8 is narrower than general P5 fusion. It constructs one bounded evidence
package first, then asks the VLM to complement that package. It does not treat
agreement between CV and the VLM as proof. Automatic validation can reject
unknown frame IDs, out-of-catalog observation codes, missing required phases,
and deterministic conflicts. Whether the cited pixels truly support a visual
claim still requires human-labeled holdout evaluation.

### P9: VLM Primary, No Pose CV

```txt
Local video -> deterministic fixed-rate frame extraction and storyboard
  -> VLM observations -> deterministic validation -> feedback
```

This pattern uses no pose estimation, exercise measurements, or CV quality gate.
Frame extraction, timestamps, resizing, and collage construction organize the
media but do not interpret the exercise. O6-N uses this pattern to isolate the
value and limitations of a VLM-only storyboard path.

## Media Evidence Packaging Strategies

Evidence packaging is separate from the architecture pattern. The same routing
pattern can use different media payloads, so a contact sheet is not by itself a
new analysis architecture.

| Package | Construction | Main Benefit | Main Limitation |
|---|---|---|---|
| E1 Native video | Send the bounded source clip and configure provider video processing | Preserves the provider's video pathway and avoids client storyboard logic | Provider sampling may miss fast motion; raw video leaves the device |
| E2 Uniform timestamped storyboard | Deterministic local sampling at a tested cadence such as 1 FPS; ordered tiles and an exact timestamp manifest | One bounded image payload with client-controlled frame identity and timing | Uniform sampling can miss turns and brief faults; shrinking many tiles removes body detail |
| E3 CV-directed event storyboard | Run pose at a higher cadence, then select phase turns, extrema, rule events, and limited coverage frames | Spends the visual budget on biomechanically informative moments | More browser compute, state-machine work, and calibration risk |

An exercise-specific pose crop can preserve more person pixels at a smaller
canvas size, but it must keep enough margin for hands, feet, bars, benches, and
the floor. Store the crop transform in the manifest and benchmark crops against
uncropped frames. Cropping and collaging do not anonymize the person.

One request can already contain multiple image parts. Therefore, putting frames
in one collage is not required to get one request and one response. Benchmark at
least these payloads on the selected provider and model:

1. Native video in one request.
2. Selected frames as separate image parts in one request.
3. The same selected frames packed into one or a small bounded number of sheets.
4. A CV-directed sheet with a compact CV manifest.

`O3-S` below means the O3 selective-escalation architecture using a focused E3
storyboard rather than sending native video. It is an evaluation configuration,
not a new top-level option.

Choose invocation cadence separately from the payload:

| Cadence | Request/response count | Tradeoff |
|---|---|---|
| Per set or clip | One pair for every analyzed set | Supports immediate retry but pays request overhead every set |
| End-of-workout batch | One pair for several bounded set packages | Fewer round trips, but later feedback and a larger failure domain; visual tokens do not disappear |
| Selective escalation (O3-S) | Zero for confident CV-only sets; one pair only for predefined uncertain cases | Best expected average efficiency if routing recall and abstention are reliable |

Do not batch without a hard session-level media and token bound. Preserve a
separate set ID, frame namespace, and manifest for each set so evidence cannot
leak across sets.

Request count, uploaded bytes, and input tokens are different quantities. JPEG
quality mainly changes transfer size. Visual token use depends on the chosen
model, processed dimensions, tiling, and media-resolution setting. A collage
saves tokens only when it is processed as fewer or lower-resolution visual
units, which also makes each person smaller. Use the provider's token-counting
and usage metadata rather than assuming that one JPEG is cheaper than several
images or native video.

For an initial evaluation cohort of 5-15 second clips, test a fixed maximum of
12 visual tiles per request, a minimum usable person size per tile, and 0.5, 1,
and 2 FPS. These are experiment settings, not product requirements. If the
source produces more evidence than the bound permits, select or split
deterministically; never keep shrinking an unbounded collage.

## Storyboard Evidence Contract

Every tile receives a stable ID such as `F07`. The exact decoded source-media
time is stored as `timestampMs`; it must not be inferred from the tile index or
from wall-clock processing time. Render a readable ID and timestamp on the tile
as a cue, but treat the manifest value as authoritative. The VLM returns frame
IDs, and the server resolves them to timestamps and rejects unknown IDs. This is
more reliable than asking the model to reproduce timestamps as free-form text.

Use separate clocks during local video processing. MediaPipe may require a
monotonically increasing inference timestamp, while evidence must use the
decoded frame presentation time. Where available, use video-frame metadata such
as `requestVideoFrameCallback().metadata.mediaTime`; otherwise record and test a
documented media-time fallback. Playback stalls, playback-rate changes, and
dropped processing frames must not change evidence timestamps.

For completed recorded or imported clips processed locally, prefer a
deterministic two-pass analysis: first collect the pose timeline and calibration
range, then freeze the thresholds and derive phases, true extrema, velocities,
and selected frames. This prevents thresholds from moving while the same
repetition is being labeled. Robust percentiles may later replace raw global
extrema if landmark spikes distort calibration.

Keep detailed CV data in structured text rather than drawing many small labels
over the body. A compact evidence package can use this shape:

```json
{
  "storyboardVersion": "1",
  "setId": "SET01",
  "exerciseId": "push_up",
  "sourceDurationMs": 11240,
  "strategy": "cv_directed_v1",
  "source": {
    "widthPx": 1920,
    "heightPx": 1080,
    "rotationDeg": 0,
    "mirrored": false,
    "cropRectPx": { "x": 160, "y": 0, "width": 1440, "height": 1080 }
  },
  "sheets": [
    {
      "sheetId": "SH01",
      "rows": 3,
      "columns": 4,
      "cellIndexBase": 0,
      "readingOrder": "row_major"
    }
  ],
  "calibration": {
    "angleId": "mean_elbow",
    "angleConvention": "smaller_angle_is_more_flexed",
    "velocityConvention": "positive_toward_max_angle",
    "observedMinAngleDeg": 78.4,
    "observedMaxAngleDeg": 166.8,
    "flexedThresholdDeg": 100,
    "extendedThresholdDeg": 150,
    "smoothingVersion": "angle_ema_v1",
    "rulesVersion": "push_up_v1"
  },
  "reps": [
    {
      "repId": 2,
      "startMs": 2210,
      "endMs": 3860,
      "repMinAngleDeg": 80.1,
      "repMaxAngleDeg": 164.9,
      "minAngleFrameId": "F07",
      "maxAngleFrameId": "F09"
    }
  ],
  "frames": [
    {
      "frameId": "F07",
      "sheetId": "SH01",
      "row": 1,
      "column": 2,
      "timestampMs": 2840,
      "repId": 2,
      "motionState": "min_angle_turn",
      "exercisePhase": "bottom",
      "jointState": "flexed",
      "angleDeg": 80.1,
      "angularVelocityDegS": 0.0,
      "poseEvidenceScore": 0.91,
      "selectedBecause": ["rep_min_angle", "rule_event"]
    }
  ]
}
```

Use mechanically unambiguous motion states:

- `toward_min_angle`
- `min_angle_turn`
- `toward_max_angle`
- `max_angle_turn`
- `hold`
- `unknown`

Map those states to exercise-specific words such as `descent`, `bottom`,
`ascent`, and `top`. Extended-to-flexed is not always a descent: a pull-up moves
toward elbow flexion while the body ascends. Keep measured extrema
(`observedMinAngleDeg`, `repMinAngleDeg`) separate from configured entry/exit
thresholds (`flexedThresholdDeg`, `extendedThresholdDeg`).

For E3, calculate angular velocity from the higher-cadence, smoothed angle
trajectory and source-media timestamps, not from the 1 FPS storyboard. Select a
small before/at/after window around peak speed when motion blur or temporal
context matters. A single lowest-speed sample is normally just a noisy turning
point. Represent a meaningful pause or stall as low absolute velocity sustained
for a configured dwell time. In this contract, positive velocity means the key
angle is increasing toward `observedMaxAngleDeg`; negative velocity means it is
decreasing toward `observedMinAngleDeg`.

`poseEvidenceScore` is a versioned deterministic quality heuristic derived from
landmark visibility and usable measurements. It is not a calibrated probability.
If a crop or orientation changes per frame, store a frame-level transform rather
than relying only on the shared source transform shown above.

A bounded selection policy should prioritize:

1. One setup and quality anchor.
2. True per-repetition minimum and maximum angle frames, found retrospectively
   after the repetition completes rather than at threshold crossings.
3. Frames supporting deterministic rule events or confidence failures.
4. Peak speed in each direction, preferably as a small local sequence, for only
   the repetitions where speed is relevant.
5. Uniform coverage frames to fill remaining temporal gaps.

Deduplicate nearby events and cap the package before rendering. The VLM response
should be a short structured object containing `status`, supported observation
codes, a model confidence label, and `evidenceFrameIds`. Rep counts, phases,
angles, and speed must come from CV in P8; the VLM must not recalculate or
override them.

```json
{
  "status": "ok",
  "observations": [
    {
      "code": "hip_sag",
      "modelConfidenceLabel": "high",
      "evidenceFrameIds": ["F07", "F11"]
    }
  ]
}
```

Resolve approved codes through deterministic coaching templates. This keeps the
normal path to one VLM request and one short response and avoids paying a second
LLM request merely to rewrite the same finding. Natural-language wording can be
tested later without changing the evidence contract.

A VLM's self-reported confidence label is not calibrated application confidence.
Do not expose or combine it as a probability until it is calibrated against
human labels for the exact exercise, view, payload, and model version.

As inspected on August 24, 2026, the current `VLM_scenarios` prototype is not
yet an E3 implementation. Its
`rep-peak` event is emitted at a flexed-threshold crossing rather than at the
true angle extremum, and uploaded-video state currently advances with a
wall-clock timestamp. Its current `topThreshold` and `bottomThreshold` names
also represent flexed-entry and extended-entry angle thresholds rather than
universally valid spatial top and bottom positions. These behaviors and names
must be replaced or separated before the prototype can produce authoritative
storyboard capture times, phase turns, or speed evidence.

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
| P8 CV-directed storyboard | Yes, analytical measurements and event selection | Yes, constrained visual complement | No separate LLM required |
| P9 VLM primary, no pose CV | No | Yes, primary analyzer | No |

P3 keeps the analysis CV-based and only uses an LLM to rephrase approved
findings. P4, P5, P7, P8, and P9 use a VLM for vision analysis. P8 differs from P7
because its CV layer supplies deterministic analytical evidence and selects the
visual moments; P7 uses CV only as a gate. P2 is the deterministic CV-only
comparison baseline, while P9 isolates VLM-only analysis; no pattern is accepted
yet.

## Architecture Decision Matrix

Use a two-step decision process: hard gates first, then weighted scoring.
Scores below are planning estimates to prioritize implementation and evaluation.

### Step 1: Hard Gates (Must Pass)

| Gate | Minimum Requirement |
|---|---|
| Safety language gate | No unsupported medical or diagnostic claims in validation set |
| Evidence gate | Inadequate evidence must return retry or abstention |
| Evidence traceability gate | Every accepted VLM finding uses payload-specific evidence: valid supplied frame IDs for E2/E3 or a validated timestamp/range for E1; deterministic-only findings cite versioned CV evidence |
| Temporal sufficiency gate | A claim requiring an uncaptured phase must return retry or abstention |
| Repeatability gate | Deterministic sampling, CV evidence, rules, and validation are identical for the same input and versions; VLM variants must meet a predeclared run-to-run stability target |
| Privacy gate | Must match the selected policy for identifiable video, frames, crops, and storyboard sheets leaving the device |
| Payload bound gate | Enforce maximum tiles, sheets, dimensions, bytes, and tokens; overflow uses deterministic selection, splitting, retry, or abstention |

Any option that fails a gate is ineligible for acceptance regardless of its
weighted score.

### Step 2: Weighted Criteria

| Criterion | Weight | Scoring Guidance (1-5) |
|---|---|---|
| Form-finding precision and safety reliability | 30% | 1=high hallucination risk, 5=high precision under holdout testing |
| Privacy and identifiable-media exposure | 20% | 1=always transfers full identifiable media, 5=video and derived images remain local by default |
| Evidence repeatability | 15% | 1=non-repeatable outputs, 5=deterministic stable outputs |
| Variable cost per analyzed session | 10% | 1=high provider dependency, 5=low predictable cost |
| End-to-end latency (p50/p95) | 10% | 1=often slow, 5=consistently responsive |
| Build and calibration complexity | 10% | 1=very high complexity, 5=low implementation burden |
| Exercise expansion flexibility | 5% | 1=hard to extend, 5=easy to add validated exercise variants |

Weighted score formula:

Total score = sum of (criterion score × weight) across all weighted criteria.

### Decision Options Evaluated

| Option ID | Option Summary | Scope Label | Source Pattern | Evidence Package |
|---|---|---|---|---|
| O1 | Browser CV quality gate plus browser landmarks, server deterministic rules, template feedback | Baseline Candidate | P2 | None |
| O2 | O1 plus LLM wording constrained to its approved deterministic findings, including any biomechanical heuristics | Candidate | P3 | None |
| O3 | O1 plus selective VLM escalation only for predefined low-confidence cases | Candidate | P4 | E1 by default; E3 in O3-S |
| O4 | VLM-primary analysis with browser CV quality gate and deterministic post-validation | Research Candidate | P7 | E1 |
| O6 | Browser CV quality gate plus fixed-rate timestamped storyboard, one bounded VLM request, and schema/evidence validation | Research Candidate | P7 | E2 |
| O6-N | Locally sample a 1 FPS baseline, pack reduced-resolution frames into one bounded timestamped storyboard, and make one VLM request without pose CV, CV measurements, or a CV quality gate | Next Spike Candidate | P9 | E2 |
| O7 | Higher-cadence browser CV selects and labels phase/event frames; bounded storyboard and CV evidence feed one constrained VLM request and deterministic fusion | Research Candidate | P8 | E3 |

O3 can use a focused E3 storyboard instead of native video for its predefined
low-confidence escalations. Track this evaluation configuration as `O3-S`; it is
not a separate architecture option. Because most successful O1 sessions make no
VLM call, O3-S may have the best average request and token efficiency if the
low-confidence router is accurate. O3's planning cost score below assumes its
default E1 escalation and does not score O3-S separately.

O6-N is O6 with the CV quality gate removed. Local decoding, frame extraction,
resizing, and collage creation are deterministic media processing, not exercise
CV. It is the next implementation spike and remains deliberately unscored until
its measured accuracy, latency, token use, cost, and repeatability are available.
Its baseline cadence is 1 FPS; 0.5 and 2 FPS remain comparison variants rather
than separate options.

### Planning Scores (Pre-Benchmark)

| Option ID | Precision and Safety (30%) | Privacy (20%) | Repeatability (15%) | Cost (10%) | Latency (10%) | Complexity (10%) | Expansion (5%) | Weighted Total (0-5) |
|---|---|---|---|---|---|---|---|---|
| O1 | 4.0 | 5.0 | 5.0 | 4.0 | 4.0 | 3.5 | 3.0 | 4.25 |
| O2 | 4.0 | 5.0 | 5.0 | 3.5 | 3.5 | 3.0 | 3.5 | 4.13 |
| O3 | 4.0 | 3.5 | 4.0 | 2.5 | 2.5 | 2.5 | 4.0 | 3.45 |
| O4 | 3.0 | 2.0 | 2.5 | 2.5 | 3.0 | 3.5 | 4.5 | 2.80 |
| O6 | 3.0 | 3.0 | 2.5 | 3.5 | 3.5 | 4.0 | 4.5 | 3.20 |
| O7 | 3.5 | 3.0 | 3.5 | 3.5 | 3.5 | 2.5 | 4.0 | 3.33 |

O6-N is intentionally absent from this planning-score table. Its next-spike
measurements should replace guesswork before it is ranked.

### Decision Readout

| Rank | Option ID | Why It Ranks Here |
|---|---|---|
| 1 | O1 | Strongest deterministic baseline for privacy, repeatability, and controlled behavior |
| 2 | O2 | Strong near-term upgrade once deterministic findings are stable |
| 3 | O3 | Promising for edge cases but adds cost, consent complexity, and routing risk |
| 4 | O7 | Higher information value per visual frame, but always sends imagery and adds CV selection and fusion complexity |
| 5 | O6 | Simple one-request VLM experiment with exact frame identity, but uniform sampling and collage resolution limit evidence quality |
| 6 | O4 | Fast for broad exercise coverage but weaker repeatability and privacy profile |

Evaluation order: implement O6-N/E2 next, then compare it with O6/E2 using the
same clips and frame payloads to isolate the CV quality gate's value. Preserve
O1 as the deterministic baseline and O4/E1 as the native-video control; evaluate
O7/E3 after the fixed-rate storyboard result is known. The planning scores are
hypotheses, not evidence that any architecture is accurate enough to accept.

## Pose Technology Matrix

| Technology | Browser | Server | Typical Output | License Consideration | Evaluation Note |
|---|---|---|---|---|---|
| MediaPipe Pose Landmarker | Strong official web support | Possible | 33 image and world landmarks, visibility, optional masks | MediaPipe repository is Apache 2.0; verify notices for distributed model assets | Primary browser CV benchmark |
| MoveNet Lightning/Thunder | Strong through TensorFlow.js | Strong through TensorFlow | 17 body keypoints and confidence | Published model is Apache 2.0 | Browser comparison candidate |
| Ultralytics YOLO-Pose | Possible through export/runtime work | Strong | Person boxes, 17 default keypoints, confidence | AGPL-3.0 or Enterprise license | Licensing must be resolved before product use |
| MMPose/RTMPose | Possible with custom export | Strong | Model-dependent keypoints and confidence | Toolkit is Apache 2.0; verify each model and dataset | Server-side comparison candidate |
| OpenPose | Generally impractical | Strong but compute-heavy | Body, hand, face, and foot keypoints | Default use is non-commercial; commercial license is separate | Not prioritized for evaluation |

MediaPipe is a practical first browser-CV benchmark because it has an official
JavaScript API, video tracking, 33 landmarks, world-coordinate output, and a
permissive repository license. Its web task is currently labeled as a preview,
so pin the package and model versions and test upgrades. MoveNet should still be
benchmarked on target devices because its 17-keypoint models may be faster.

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
- quality-gate false acceptance and false rejection, when a gate is present
- confidence calibration
- deterministic repeatability

Optimize high-confidence finding precision before recall. Missing a minor issue
is preferable to confidently inventing one.

### 6. Validate Product Experience

Measure:

- recording completion rate
- input-rejection and abstention rate
- successful retry rate
- time from recording end to feedback
- user understanding of the correction
- user trust in the result
- second-attempt rate
- reported usefulness of the next result

A technically accurate system that repeatedly rejects normal users is not an
acceptable architecture.

### 7. Evaluate VLM Value Separately

Run a consented offline comparison, preserving CV rules as a control when they
are available:

| System | Evaluation |
|---|---|
| CV rules only | Baseline against human labels |
| O4/E1 native-video VLM | Same clips and label rubric; test default and configured sampling where supported |
| Uniform-frame separate-parts control | Put the same frames used by O6 in one request without an E2 collage |
| O6-N/E2 VLM-only storyboard | Isolate the baseline accuracy, latency, and cost of fixed-rate frames without any pose CV contribution |
| O6/E2 uniform storyboard | Put those exact frames into a bounded timestamped sheet |
| O7/E3 event storyboard without CV labels | Isolate the value of event-frame selection |
| O7/E3 event storyboard with CV manifest | Measure the additional value and anchoring risk of structured CV evidence |
| O3-S selective escalation | Invoke E3 only for predefined low-confidence cases and report average calls per session |
| General parallel fusion | Test only if constrained escalation or O7 shows complementary value |

Compare every system with human labels. Do not promote a system because it
agrees with another automated system.

Hold the clips, finding rubric, output schema, and maximum output tokens fixed.
Run both equal-frame and equal-input-token comparisons. For each configuration,
measure:

- high-confidence finding precision and recall
- repetition and phase-event coverage, including fast and slow repetitions
- brief-fault recall and false confident findings
- valid frame-ID citation rate and frame-to-timestamp resolution
- pixels per person and duplicate-frame rate
- VLM run-to-run stability on identical inputs
- API requests per session and response count
- uploaded bytes, actual input/output tokens, and provider-reported cost
- client processing time plus end-to-end p50 and p95 latency
- retry and abstention rates

Test fixed-rate sampling at 0.5, 1, and 2 FPS rather than treating 1 FPS as an
established optimum. Test event selection with and without speed frames. A
storyboard wins only if its measured product accuracy remains acceptable at a
meaningfully lower cost or latency than the native-video and separate-frame
controls.

## Proposed Acceptance Gates

These are initial decision targets and should be adjusted after the engineering
spike.

Metrics that name a pre-analysis quality gate apply only to options containing
one. O6-N must instead satisfy the all-option evidence, abstention, and payload
gates; the absence of a CV gate is not an automatic pass.

| Metric | Proposed Gate |
|---|---|
| Usable clips rejected by a pre-analysis quality gate (gate-bearing options) | 10% or less |
| Unusable clips correctly rejected by a pre-analysis quality gate (gate-bearing options) | 85% or more |
| Exact rep count on accepted clips | 95% or more |
| High-confidence form finding precision | 90% or more |
| High-confidence form finding recall | 70% or more |
| Same input and rule version | Identical deterministic findings |
| Same input and storyboard versions | Identical selected frame IDs, source timestamps, tile ordering, and applicable manifest fields |
| VLM evidence references | Storyboards cite valid frame IDs; native video cites validated timestamp ranges; otherwise reject the finding |
| Claim requires a missing phase | Always returns retry or abstention for that claim |
| Phase-dependent accepted findings | 100% include the required captured phases; otherwise reject or abstain |
| VLM run-to-run stability | At least 90% exact agreement on status and accepted finding-code set across three identical runs |
| Configured payload bounds | 100% of provider requests remain within the versioned tile, sheet, dimension, byte, and token caps |
| Inadequate evidence | Always returns retry or abstention |
| Unsupported or medical claim | Zero in the validation set |
| Local processing failure | 5% or less on supported target devices |
| End-to-end latency | Set after device spike; report p50 and p95 |
| User-rated understandable feedback | 80% or more |

Failure to reach a gate should narrow the evaluated claim, capture view, or
supported-device assumptions before adding another model. Any proposed product
scope change belongs in the [Product Spec](PRODUCT_SPEC.md).

## Open Architecture Inputs

The [Product Spec](PRODUCT_SPEC.md) owns product decisions. Architecture
acceptance still needs these implementation and evaluation inputs:

1. Which supported exercise from the Product Spec is the first O6-N validation
   cohort?
2. Which browsers and minimum phone classes must the experiment cover?
3. What p95 latency, provider-cost, and upload-size budgets apply per set?
4. May identifiable derived frames be sent to the selected provider under the
   product's privacy and consent requirements?
5. How many human-labeled participants and clips are available for calibration
   and a participant-separated holdout?
6. Which provider/model/version will be pinned for the first comparison?

## Current Technical Facts

These facts were initially verified on June 11, 2026. Storyboard-specific
Gemini facts were rechecked on August 24, 2026. All may change:

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
- Gemini token accounting is model- and media-resolution-specific. Current
  documentation exposes media-resolution controls and token-counting APIs; use
  those for the exact configured model instead of relying on one fixed rate.
- Image token use depends on processed resolution and tiling. Combining frames
  into one large image does not guarantee a token reduction, and reducing JPEG
  quality does not by itself guarantee fewer visual tokens.
- Multiple images can be sent in one multimodal request, so a collage is not
  required to reduce the request count to one.
- Gemini structured output can enforce a supported JSON Schema subset, but a
  schema-valid value can still be semantically wrong and requires application
  validation.
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
- [Gemini Image Understanding](https://ai.google.dev/gemini-api/docs/image-understanding)
- [Gemini Media Resolution](https://ai.google.dev/gemini-api/docs/generate-content/media-resolution)
- [Gemini Token Counting](https://ai.google.dev/gemini-api/docs/generate-content/tokens)
- [Gemini Structured Outputs](https://ai.google.dev/gemini-api/docs/structured-output)
- [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini Files API](https://ai.google.dev/gemini-api/docs/files)
- [Gemini API Additional Terms](https://ai.google.dev/gemini-api/terms)
