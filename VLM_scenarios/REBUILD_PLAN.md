# App Rebuild Plan — Realtime CV / VLM / Hybrid Lab

> Locked decisions and architecture for rebuilding the app around three realtime-feedback modes. Supersedes the Phase 2 section of `ADDING_REAL_CV.md` (Phase 1 — editable CV data — shipped in commit `b1b90ba`).

---

## 1. Goal

Understand, by feel and by numbers, how three AI architectures behave for live exercise coaching:

| Tab | What runs | Feedback speed | Cost |
|---|---|---|---|
| **CV** | MediaPipe Pose in-browser: skeleton overlay, rep counting, form score, rule-based cues | instant (~30fps) | free |
| **VLM** | Snapshot/video → Gemini → coaching text | 2–4 s delay | per call |
| **Hybrid** | CV always on; Gemini called on triggers with CV-picked keyframes + CV numbers | instant numbers + occasional smart coaching | few calls/set |

## 2. Locked Decisions

- **3 tabs only** — the old 6-scenario upload workspace and its unused routes (`text`, `image`, `mock-cv`) are deleted. Git history keeps them.
- **Video input panel shared by all tabs**, with two sources:
  - **Upload** — file input, custom playback controls with a **scrubber**; CV counts along while the video plays, and scrubbing shows the pose overlay at any point (the main "understand CV" tool).
  - **Live** — webcam via `getUserMedia`.
- **Pose dots** (33 landmarks + skeleton lines) drawn on a canvas overlay in both sources.
- **Live CV readout**: rep count, rep phase, key joint angle, calibration state, body-line deviation, per-rep form scores.
- **Exercises**: pull-ups, push-ups, squats via dropdown; each has its own key joint and rep logic. Auto-detection later.
- **Self-calibrating thresholds** (the big design decision): rep boundaries are *percentages of the user's own observed range of motion* in the current session (~20% / 80% of min–max key angle), not fixed angles. Fixed angles are used only as fallback until the first rep calibrates the range. This makes thresholds adapt automatically to different people and camera angles.
- **Camera guidance**: UI hint to film side-on, full body in frame, ~2–3 m away.
- **Hybrid VLM triggers**: set-end (auto), form-drop over 2+ reps (auto, max once per set — cooldown protects the free tier), and a manual "Ask Coach" button.
- **VLM tab cadence**: manual "Analyze now" button; optional auto-snapshot toggle (default off, interval adjustable).
- **Session memory**: previous set summaries + last coaching advice are prepended to every hybrid prompt, so the coach remembers the session.
- **Gemini free tier for MVP**; token usage + latency logged per call (already implemented) for the cost KPI.
- **No separate LLM**: Gemini is both VLM and LLM — one call takes frames + CV numbers and returns coaching language.

## 3. Architecture

```
lib/cv/
  poseEngine.ts     MediaPipe PoseLandmarker loader (client-only, CDN wasm + model)
  poseMath.ts       landmark indices, joint-angle math, body-line deviation
  exercises.ts      per-exercise config: key joints, fallback angles, calibration %
  repCounter.ts     self-calibrating rep state machine, form scores, set-end +
                    form-drop events, set summary builder
  drawPose.ts       canvas skeleton rendering
lib/hooks/
  usePoseTracking.ts  rAF loop: detect → draw overlay → update counter → emit events
components/
  Workspace.tsx     3 tabs, mode logic, hybrid triggers, session memory
  VideoPanel.tsx    upload/live source toggle, video + canvas overlay, scrubber
  CvReadout.tsx     live CV numbers panel
  ResultPanel.tsx   (kept) latest Gemini response
  ComparisonTable.tsx (kept) run history: mode/trigger, model, tokens, ms
app/api/analyze/
  frames/  video/  hybrid/  (kept; hybrid validator updated to CvSetSummary)
  health/  (kept)
```

**CV data contract** (replaces `MockPoseData`): `CvSetSummary` — exercise, reps, formScores[], avgKeyAngleDeg, keyJoint, rangeOfMotionDeg, bodyLine, tempo, weakPoints[]. Built client-side by the rep counter, validated server-side, rendered into the Gemini prompt.

**Rep counting** (per exercise): smooth the key angle (moving average), track observed min/max, rep = angle crossing the 20%-of-range boundary (top) then the 80% boundary (bottom) — hysteresis prevents double counts. Form score per rep = weighted range-of-motion + body-line stability + tempo consistency. Set ends after ~6 s without a rep.

**Counting is gated**: the counter only advances while video plays (or camera is live). Scrubbing a paused video moves the dots and the angle readout but never corrupts the rep count.

## 4. Build Order

1. CV core: poseMath → exercises → repCounter (pure logic, no UI)
2. Pose engine + tracking hook + overlay drawing
3. VideoPanel (upload + scrubber + webcam)
4. Workspace with 3 tabs; CV readout
5. VLM mode (snapshot + upload paths, auto-toggle)
6. Hybrid triggers + keyframe ring buffer + session memory
7. Delete old scenario code/routes; typecheck, lint, build

## 5. Threshold Tuning Workflow (manual, v1)

1. Load a test video (`test-videos/`), pick the exercise, press play.
2. Compare CV rep count vs your eye count; scrub to any miscounted moment and watch the angle readout.
3. Report "counted N, should be M, extra/missing rep at 0:SS" — thresholds/smoothing get adjusted in `exercises.ts` (all tunable numbers live there, deliberately not hardcoded elsewhere).
4. Re-run the same video. Repeat per exercise.

## 6. v2 — Mode 4: VLM Auto-Calibration (not in this build)

The reverse hybrid: after a set, the VLM independently counts reps and judges rep depth from keyframes; disagreement with CV nudges the per-user thresholds within capped bounds, only when the VLM is consistent across 2–3 sets, with user veto. Runs post-set (never live), a few calls per calibration. The `exercises.ts` parameter design exists specifically so this can plug in without a rewrite.

## 7. Verification Checklist

- [ ] `npm run typecheck`, `lint`, `build` pass
- [ ] Upload `test-videos/pullups-gym.mp4` in CV tab → dots track the body, scrubber works while paused, rep count within ±1 of eye count during playback
- [ ] Push-ups and squats clips count sanely with their exercise selected
- [ ] Live webcam: dots + counter run; readout updates
- [ ] VLM tab: "Analyze now" (live) and upload analysis return coaching text with ms + tokens logged
- [ ] Hybrid: set-end fires exactly one auto call; form-drop fires at most once per set; Ask Coach works; second set's prompt contains first set's summary
- [ ] No Gemini calls ever fire from the CV tab
