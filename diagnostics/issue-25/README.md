# Issue #25 — HIP_SAG false-positive diagnosis: visual evidence

Diagnostic output only. No application code, thresholds, or dataset labels were
changed to produce these files.

## Findings

- **Cause of the false positives.** Angles are computed on MediaPipe's
  normalized coordinates. All 10 benchmark clips are 1280×720, so vertical
  offsets are stretched 1.78× relative to horizontal ones. A straight body
  reads about 7–9° more bent than it is, and elbow angles read up to 25–32°
  too high.
- **Effect of correcting it** (x × width, y × height, every threshold
  unchanged): the benchmark goes from 8/10 to **9/10**. `valid_04` and
  `valid_05` are no longer flagged, and rep counts match the visible reps in
  the valid clips.
- **Sag detection is 4/5.** `sag_03` is reported as VALID after the
  correction. Today it is caught only through 5 marginal frames (255–256 and
  309–311) that look the same as the false-positive frames in `valid_04` and
  `valid_05`.
- **The no-regression requirement is still unmet.** Issue #25 requires
  detection on all five sag clips. No body-angle or hip-drop threshold can flag
  `sag_03` without also flagging `valid_05`, which is worse on both measures
  (see table).
- **Temporal filtering does not fix this.** 3- and 5-frame mean or median
  smoothing, on landmarks or on angles, leaves the current pipeline at 8/10.
- **The sticky flag is not the cause.** The false triggers are mid-rep and
  recur in two separate reps of each clip.

Pixel-corrected values at the frame with the largest hip drop in each rep.
Hip drop is the hip's distance below the shoulder–ankle line as a percentage
of that line's length.

| Rep | Frame | Body angle | Hip drop | Mean hip drop over the rep |
|---|---|---|---|---|
| `sag_03` rep 3 | 256 | 166.8° | 5.5% | 3.6% |
| `sag_03` rep 4 | 310 | 167.9° | 5.0% | 4.0% |
| `valid_04` rep 3 | 226 | 167.2° | 5.3% | 3.6% |
| `valid_05` rep 1 | 77 | 165.5° | 6.1% | 4.4% |
| `sag_01` rep 2 (clear sag) | 106 | 153.6° | 10.9% | 8.7% |

## Open question for review

Is the HIP_SAG label on `sag_03` visually supported? In the stills, the torso
rises slightly ahead of the hips on the way up, the same mild pattern seen in
`valid_04` and `valid_05`. The clips have not been judged as moving video.

## How to read the overlays

- Red dots labeled SHOULDER, HIP, ANKLE: the landmarks the rule uses.
- Yellow line: shoulder–ankle reference line.
- Magenta line: the hip's offset from that line.
- Header: frame number, timestamp at the clip's real 30 fps, pixel-corrected
  body angle, hip drop, and elbow angle.

## Review order

1. [phase_comparison.jpg](phase_comparison.jpg) — five reps side by side at
   four phases (down, bottom, up, worst hip drop). Columns: `sag_03` rep 3,
   `sag_03` rep 4, `valid_04` rep 3, `valid_05` rep 1, `sag_01` rep 2.
   [phase_comparison_small.jpg](phase_comparison_small.jpg) is the same sheet
   at 40% size.
2. [sag_03_frame256_current-rule-trigger.png](sag_03_frame256_current-rule-trigger.png)
   and [sag_03_frame310_current-rule-trigger.png](sag_03_frame310_current-rule-trigger.png)
   — the worst frame of each flagged `sag_03` rep.
3. [sag_03_rep3_frames222-276.mp4](sag_03_rep3_frames222-276.mp4) and
   [sag_03_rep4_frames276-329.mp4](sag_03_rep4_frames276-329.mp4) — the two
   flagged reps in motion. Watch whether the hips visibly lag on the way up.
4. [valid_05_rep1_frames33-95.mp4](valid_05_rep1_frames33-95.mp4) — the valid
   rep with the largest hip drop, for direct comparison with step 3.
5. [sag_01_rep2_frames52-122.mp4](sag_01_rep2_frames52-122.mp4) — a clear sag
   for reference.

## All files

| File | Content |
|---|---|
| [phase_comparison.jpg](phase_comparison.jpg) | Phase-matched comparison sheet, full size |
| [phase_comparison_small.jpg](phase_comparison_small.jpg) | Same sheet at 40% size |
| [sag_03_rep3_frames222-276.mp4](sag_03_rep3_frames222-276.mp4) | `sag_03` rep 3, 7.40–9.20 s, contains trigger frames 255–256 |
| [sag_03_rep4_frames276-329.mp4](sag_03_rep4_frames276-329.mp4) | `sag_03` rep 4, 9.20–10.97 s, contains trigger frames 309–311 |
| [valid_04_rep3_frames182-245.mp4](valid_04_rep3_frames182-245.mp4) | `valid_04` rep 3, 6.07–8.17 s, contains false triggers 225–227 |
| [valid_05_rep1_frames33-95.mp4](valid_05_rep1_frames33-95.mp4) | `valid_05` rep 1, 1.10–3.17 s, contains false triggers 50–53, 72, 74–78 |
| [sag_01_rep2_frames52-122.mp4](sag_01_rep2_frames52-122.mp4) | `sag_01` rep 2, 1.73–4.07 s, reference sag |
| [sag_03_frame255_current-rule-trigger.png](sag_03_frame255_current-rule-trigger.png) | Trigger frame, 8.50 s |
| [sag_03_frame256_current-rule-trigger.png](sag_03_frame256_current-rule-trigger.png) | Trigger frame, 8.53 s |
| [sag_03_frame309_current-rule-trigger.png](sag_03_frame309_current-rule-trigger.png) | Trigger frame, 10.30 s |
| [sag_03_frame310_current-rule-trigger.png](sag_03_frame310_current-rule-trigger.png) | Trigger frame, 10.33 s |
| [sag_03_frame311_current-rule-trigger.png](sag_03_frame311_current-rule-trigger.png) | Trigger frame, 10.37 s |
