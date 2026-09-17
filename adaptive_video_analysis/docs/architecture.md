# Architecture

## Goals

The pipeline optimizes three things independently:

1. **Evidence quality:** rapid phases and suspected mistakes receive denser
   temporal evidence.
2. **VLM context:** only a small timestamped subset reaches the provider.
3. **Measurability:** local frames, provider images, latency, and reduction are
   returned in diagnostics.

## Component boundaries

| Component | Responsibility | May make coaching claims? |
|---|---|---|
| Video scanner | Validation, sparse decoding, resize, JPEG encoding | No |
| Pose extractor | Landmarks and visibility | No |
| Local analyzer | Angles, phases, repetitions, candidate signals | No |
| Sampler | Coverage, phase, anomaly, and detail frame selection | No |
| Vision provider | Visible qualitative observations | Tentative only |
| Safety/result layer | Schema, timestamp, safety, priority, uncertainty | Final gate |

Rule signals deliberately use names such as
`body_line_deviation_candidate`. A single-camera pose estimate is not ground
truth, and candidate thresholds must not be surfaced as a diagnosis.

## Coarse-to-fine passes

The overview uses timeline coverage plus rep starts, bottoms, ends, high motion,
low visibility, and conservative exercise-specific candidate signals.

The provider may identify additional intervals. Those are clamped to the video
duration and merged with local intervals. The detail pass samples across the
merged intervals. Groq receives at most five images in each pass; Gemini uses
the configured eight-image overview and twelve-image detail budgets.

If no interval crosses the escalation threshold, the second pass is skipped.
If the local visibility gate fails, every external provider call is skipped and
the result requests another recording.

## Exercise coverage

Push-up and squat currently have explicit dynamic phase detection. Lunge uses
the same dynamic machinery provisionally. Plank and hollow hold currently
produce static timelines without repetition detection.

This does not mean the five exercises are equally validated. The implementation
surface is broad so data can flow through the same schemas, while calibration
should focus on push-up and squat first.

## Provider strategy

The VLM adapter receives JPEGs and compact JSON, not the original video. This
keeps provider behavior comparable between Gemini and Groq. A future benchmark
may add Gemini native video as a control arm, but it should not become the
source of truth without showing a measurable accuracy gain.

## Production hardening still required

- move MediaPipe into an outbound-network-blocked worker
- enforce request concurrency limits and authentication
- add encrypted provider/log metadata storage if persistence is needed
- add model/version pinning and scheduled provider compatibility tests
- calibrate thresholds per camera view and exercise
- add an expert-reviewed finding ontology and label aliases
- test demographic, device, clothing, lighting, occlusion, and mobility slices

