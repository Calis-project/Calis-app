# Cue Text Matrix — HIP_SAG & NO_REP_DEPTH

Document ID: DOC-FB-001
Feature: Feedback Data Contract (rules engine → mobile client)
Related: `src/feedback/feedback_schema.json`, `src/feedback/pushup.py`, `docs/01_product/pushup_prd.md` (§3.1, §5)
Status: Ready for implementation — see §4 for required engine changes before this contract is fully satisfied

## 1. Purpose

This matrix is the single source of truth for the `cue_text` string the rules
engine must emit whenever `error_code` is `HIP_SAG` or `NO_REP_DEPTH`. Every
string below is final copy — implementers must not paraphrase, translate, or
append punctuation/emoji when populating `cue_text`.

Rules for all entries:
- Max 40 characters (matches `cue_text` schema constraint).
- Imperative, single-instruction phrasing — one correction per cue, never two.
- No numbers, joint names, or angle values in the text.
- Audio and on-screen banner text are identical strings; the client handles TTS/rendering, not rewording.

## 2. HIP_SAG

**Detected today** by `is_hip_sagging()` in `pushup.py`. Trigger is stricter
than the PRD's angle-only rule: it requires **both**
`body_angle < 160°` (via `calculate_angle(shoulder, hip, ankle)`) **and** the
hip's y-coordinate falling below the shoulder–ankle line (the vertical-
displacement check). This is a reasonable refinement over the PRD — it
reduces false positives from angle noise alone — but note it for the record
since it's a behavior change relative to PRD-EX-001 §3.1.

| Field | Value |
|---|---|
| `error_code` | `HIP_SAG` |
| `is_valid` | `false` |
| Trigger condition | `is_hip_sagging(shoulder, hip, ankle) == True` (angle **and** vertical-displacement check) |
| **`cue_text` (primary, default)** | `Core tight, lift hips` |
| Cue on first occurrence in a rep | `Engage your core` |
| Visual badge | Red banner: "Sagging Spine" |
| Severity | Blocking — rep should not count as valid while active |

## 3. NO_REP_DEPTH

**Not yet detected** by `pushup.py`. In the current state machine, a shallow
attempt maps to the `DESCENDING → PLANK` transition (the branch commented
`# Returned to plank without going deep enough`, triggered when
`elbow_angle > 150.0` without ever reaching `elbow_angle <= 90.0`). Today
that branch silently resets state and sets no error — the rep is neither
counted nor flagged. It needs to set `error_code = "NO_REP_DEPTH"` and
`is_valid = False` for that frame.

| Field | Value |
|---|---|
| `error_code` | `NO_REP_DEPTH` |
| `is_valid` | `false` |
| Trigger condition | State transition `DESCENDING → PLANK` without having passed through `BOTTOM` (i.e. `elbow_angle` rises back above `150.0°` without ever reaching `<= 90.0°`) |
| **`cue_text` (primary, default)** | `Go lower next rep` |
| Cue while still descending, before the abort (in-rep warning) | `Go lower` |
| Visual badge | Amber warning: "Insufficient Depth" |
| Severity | Non-blocking — attempt is excluded from `rep_count` and flagged in the session's form-adherence rate |

## 4. Engine Changes Required (pushup.py)

This contract cannot be fully satisfied by `pushup.py` as it stands. Filed
here so review of this PR also produces the follow-up tickets:

1. **Rename** `detected_error` → `error_code` in the return dict; map Python
   `None` → the string `"NONE"` (never emit `null`).
2. **Add `cue_text`** to the return dict, looked up from this matrix based on
   `error_code`.
3. **Implement `NO_REP_DEPTH`** in the `DESCENDING → PLANK` abort branch, per
   §3 above.
4. **Fix the sticky `is_valid`/`detected_error` flags** — both are currently
   set once and never reset, so a single early hip-sag frame invalidates the
   rest of the session/report. They need to reflect the *current* frame or
   *current* rep, not the whole stream, for live correction (PRD-EX-001
   Phase 3) to work.
5. **Convert from batch to streaming** — `evaluate_pushup_stream()` currently
   consumes the full landmark list and returns a single summary dict at the
   end. Real-time on-screen/audio cues require a message emitted per frame
   or per state transition (a generator or a callback), not one report after
   the set is over.
6. **`state` enum note**: `SETUP`, `PLANK_LOCK_IN`, and `SESSION_END` from
   PRD-EX-001 §4 (Phases 1, 2, 4) are not produced by this engine at all —
   confirm with the team whether those belong to an upstream
   calibration/session layer, since `pushup.py`'s own state machine only
   ever emits `IDLE`, `PLANK`, `DESCENDING`, `BOTTOM`, `ASCENDING`.

Items 3–5 block real-time use of `HIP_SAG`/`NO_REP_DEPTH` cues in the live
coaching flow; item 1–2 block the mobile client from consuming this output
at all under the current schema.
