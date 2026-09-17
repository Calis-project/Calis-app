# Evaluation Protocol

Code correctness is not movement-analysis validity. Validation has three
separate levels.

## Level 1: automated engineering tests

These tests cover schema behavior, geometry, phase state machines, sampling
budgets, provider orchestration, safety filtering, and video decoding. They
should run on every change.

## Level 2: labelled clip benchmark

Each JSONL line describes one clip:

```json
{"id":"pushup_001","video":"videos/pushup_001.mp4","exercise":"push_up","expected_reps":5,"expected_usable":true,"expected_findings":[{"label":"body_line_deviation","timestamp_seconds":6.2}],"notes":"Side view; reviewed by coach AB."}
```

Keep the raw videos outside Git. Use pseudonymous IDs. Every finding should be
reviewed by at least one qualified calisthenics coach; disagreements should be
recorded rather than forced into false certainty.

Run the same manifest for:

- MediaPipe lite, full, and heavy
- 4, 8, and 12 local-analysis FPS
- local-only, Gemini single-pass, Gemini coarse-to-fine
- Groq single-pass and Groq coarse-to-fine
- optional Gemini native-video control

Do not tune and report on the same clips. Split by person, not by clip, so that
one person's appearance and recording setup cannot leak across train/calibration
and test sets.

## Level 3: product safety and usefulness

Human reviewers should separately score:

- whether the finding is visibly supported
- whether the timestamp is useful
- whether the cue is actionable
- whether uncertainty is appropriate
- whether any unsafe, medical, shaming, or overconfident language appears
- whether the user improves on a later attempt

Accuracy alone is insufficient. A system that returns fewer but well-supported
findings is preferable to one with high recall and many false corrections.

## Initial acceptance targets

These are hypotheses to revisit after the first labelled batch:

- usable-clip classification: at least 90%
- repetition count exact accuracy: at least 90% on usable dynamic clips
- prioritized-finding precision: at least 85%
- prioritized-finding recall: at least 70%
- unsafe or unsupported high-confidence findings: 0
- median provider images: no more than 20 for Gemini and 10 for Groq
- context reduction versus native frames: at least 95%

