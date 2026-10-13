"""
Unit tests for the push-up rules engine (Issue #25).
Phase 1: angles must be measured in real frame geometry, whatever the frame aspect ratio.
Phase 2: HIP_SAG needs temporal confirmation, and live feedback is separate from history.
"""

import math
import os
import random
import subprocess
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.biomechanics.pushup_rules import (
    HIP_SAG,
    SAG_CONFIRM_FRAMES,
    SAG_RECOVERY_FRAMES,
    TRACKING_LOSS_FRAMES,
    TRACKING_LOST,
    PushupEvaluator,
    calculate_angle,
    evaluate_pushup_stream,
    is_hip_sagging,
)

FRAME_SIZES = {
    "16:9": (1280, 720),
    "4:3": (640, 480),
    "9:16": (720, 1280),
    "1:1": (1000, 1000),
}

RESULT_FIELDS = {"detected_error", "is_valid", "rep_count", "state"}  # Phase 1 contract
HISTORY_FIELDS = {"current_error", "rep_errors", "valid_rep_count"}  # added in Phase 2

LANDMARKS = ("shoulder", "elbow", "wrist", "hip", "ankle")
REP_STATES = ("DESCENDING", "BOTTOM", "ASCENDING")

# Frame codes used by build(): a posture (as a hip_drop), or a frame without usable landmarks
HIP_DROPS = {"C": 0.0, "S": 0.14, "M": 0.06, "K": -0.10}  # clean, sag, mild bend, pike
CUE_CODES = {None: "-", HIP_SAG: "S", TRACKING_LOST: "L"}

# Normalized landmarks from real 1280x720 benchmark frames (rounded to 4 decimals).
# valid_05.mp4 frame 77: true body angle 165.5 deg, read as 155.9 deg without correction.
VALID_05_FRAME_77 = {
    "shoulder": (0.7891, 0.5325), "elbow": (0.7314, 0.6536), "wrist": (0.7652, 0.8533),
    "hip": (0.5171, 0.6829), "ankle": (0.0793, 0.7201),
}
# valid_04.mp4 frame 226: true body angle 167.2 deg, read as 158.6 deg without correction.
VALID_04_FRAME_226 = {
    "shoulder": (0.7877, 0.5480), "elbow": (0.7237, 0.6603), "wrist": (0.7653, 0.8556),
    "hip": (0.5167, 0.6807), "ankle": (0.0742, 0.7170),
}
# sag_01.mp4 frame 100: true body angle 155.6 deg, a clear sag.
SAG_01_FRAME_100 = {
    "shoulder": (0.8039, 0.5174), "elbow": (0.7273, 0.6423), "wrist": (0.7664, 0.8365),
    "hip": (0.5574, 0.7104), "ankle": (0.1138, 0.7020),
}


def normalize(point_px, width, height):
    """Pixel point -> MediaPipe-style normalized point."""
    return (point_px[0] / width, point_px[1] / height)


def body_angle_for_drop(hip_drop):
    """True shoulder-hip-ankle angle of pushup_frame() for a given hip_drop."""
    return 180.0 - 2.0 * math.degrees(math.atan(2.0 * abs(hip_drop)))


def pushup_frame(width, height, elbow_deg, hip_drop=0.0):
    """
    Side-view push-up pose built in pixels with a known elbow angle, returned as
    normalized landmarks. hip_drop moves the hip off the shoulder-ankle line by that
    fraction of the line's length (positive = toward the floor, negative = pike).
    """
    body = 0.7 * width
    arm = 0.15 * body  # upper arm and forearm
    floor_y = 0.8 * height
    half = math.radians(elbow_deg) / 2.0

    wrist = (0.85 * width, floor_y)
    reach = 2.0 * arm * math.sin(half)
    shoulder = (wrist[0], floor_y - reach)
    elbow = (wrist[0] - arm * math.cos(half), floor_y - reach / 2.0)
    ankle = (wrist[0] - body, floor_y)

    dx, dy = ankle[0] - shoulder[0], ankle[1] - shoulder[1]
    length = math.hypot(dx, dy)
    nx, ny = -dy / length, dx / length
    if ny < 0:  # unit normal pointing toward the floor (y-down)
        nx, ny = -nx, -ny
    hip = (
        shoulder[0] + dx / 2.0 + hip_drop * length * nx,
        shoulder[1] + dy / 2.0 + hip_drop * length * ny,
    )

    points = {"shoulder": shoulder, "elbow": elbow, "wrist": wrist, "hip": hip, "ankle": ankle}
    return {name: normalize(p, width, height) for name, p in points.items()}


def rep_angles(reps, bottom_deg=80, top_deg=170):
    """Elbow angles for a plank hold, then `reps` cycles of top -> bottom -> top."""
    angles = [top_deg] * 3
    for _ in range(reps):
        angles += list(range(top_deg - 5, bottom_deg - 1, -5))
        angles += list(range(bottom_deg + 5, top_deg + 1, 5))
    return angles


def pushup_stream(width, height, reps, bottom_deg=80, top_deg=170, hip_drop=0.0):
    """Normalized landmark stream: plank hold, then `reps` cycles of top -> bottom -> top."""
    return [pushup_frame(width, height, a, hip_drop) for a in rep_angles(reps, bottom_deg, top_deg)]


def build(steps, width=1280, height=720):
    """
    Frames from (elbow_deg, code) steps. Codes:
      C clean   S hip sag   M mild bend (above the threshold)   K pike
      N pose not detected (None)   P pose detected without the ankle
    """
    frames = []
    for elbow_deg, code in steps:
        if code == "N":
            frames.append(None)
            continue
        frame = pushup_frame(width, height, elbow_deg, HIP_DROPS.get(code, 0.0))
        if code == "P":
            del frame["ankle"]
        frames.append(frame)
    return frames


def plank(codes, width=1280, height=720):
    """Plank hold (elbow 170 deg) with one frame per code, e.g. plank("CCSSSCC")."""
    return build([(170, code) for code in codes], width, height)


def run(frames, width=1280, height=720):
    """Result after every frame, from a fresh evaluator."""
    evaluator = PushupEvaluator(width, height)
    return [evaluator.update(frame) for frame in frames]


def cues(results):
    """Live cue per frame as a string: '-' none, 'S' HIP_SAG, 'L' TRACKING_LOST."""
    return "".join(CUE_CODES[r["current_error"]] for r in results)


def phase1_reference(frames, width, height):
    """
    Frozen copy of the Phase 1 engine loop, kept as the oracle for movement state and
    rep count. Returns the per-frame (state, rep_count) trace and the Phase 1 result.
    """
    aspect_ratio = width / height
    state, rep_count, any_sag, trace = "IDLE", 0, False, []
    for frame in frames:
        if frame is not None and all(frame.get(name) for name in LANDMARKS):
            any_sag = any_sag or is_hip_sagging(frame["shoulder"], frame["hip"], frame["ankle"], aspect_ratio)
            elbow_angle = calculate_angle(frame["shoulder"], frame["elbow"], frame["wrist"], aspect_ratio)
            body_angle = calculate_angle(frame["shoulder"], frame["hip"], frame["ankle"], aspect_ratio)
            if state == "IDLE":
                if body_angle >= 160.0 and elbow_angle > 150.0:
                    state = "PLANK"
            elif state == "PLANK":
                if elbow_angle < 150.0:
                    state = "DESCENDING"
            elif state == "DESCENDING":
                if elbow_angle <= 90.0:
                    state = "BOTTOM"
                elif elbow_angle > 150.0:
                    state = "PLANK"
            elif state == "BOTTOM":
                if elbow_angle > 90.0:
                    state = "ASCENDING"
            elif state == "ASCENDING":
                if elbow_angle > 150.0:
                    state = "PLANK"
                    rep_count += 1
                elif elbow_angle <= 90.0:
                    state = "BOTTOM"
        trace.append((state, rep_count))
    result = {
        "detected_error": "HIP_SAG" if any_sag else None,
        "is_valid": not any_sag,
        "rep_count": rep_count,
        "state": state,
    }
    return trace, result


def rep_windows(steps, width=1280, height=720):
    """(first, last) frame index of every stretch the Phase 1 oracle spends inside a rep."""
    trace, _ = phase1_reference(build(steps, width, height), width, height)
    windows, start = [], None
    for i, (state, _) in enumerate(trace):
        if state in REP_STATES and start is None:
            start = i
        elif state not in REP_STATES and start is not None:
            windows.append((start, i - 1))
            start = None
    if start is not None:
        windows.append((start, len(trace) - 1))
    return windows


class CalculateAngleTest(unittest.TestCase):
    def test_known_angles_for_each_aspect_ratio(self):
        for label, (width, height) in FRAME_SIZES.items():
            vertex = (0.5 * width, 0.5 * height)
            radius = 0.2 * min(width, height)
            for expected in (30.0, 60.0, 90.0, 135.0, 160.0, 180.0):
                for start in (0.0, 25.0, 70.0, 200.0):
                    a, b = math.radians(start), math.radians(start + expected)
                    p1 = (vertex[0] + radius * math.cos(a), vertex[1] + radius * math.sin(a))
                    p3 = (vertex[0] + radius * math.cos(b), vertex[1] + radius * math.sin(b))
                    with self.subTest(aspect=label, angle=expected, start=start):
                        measured = calculate_angle(
                            normalize(p1, width, height),
                            normalize(vertex, width, height),
                            normalize(p3, width, height),
                            aspect_ratio=width / height,
                        )
                        self.assertAlmostEqual(measured, expected, places=6)

    def test_default_measures_points_as_given(self):
        self.assertAlmostEqual(calculate_angle((0.0, 1.0), (0.0, 0.0), (1.0, 0.0)), 90.0, places=6)

    def test_normalized_points_need_the_aspect_ratio(self):
        width, height = FRAME_SIZES["16:9"]
        vertex = (640.0, 360.0)
        p1 = (vertex[0] + 100.0, vertex[1] + 100.0)
        p3 = (vertex[0] - 100.0, vertex[1] + 100.0)
        points = [normalize(p, width, height) for p in (p1, vertex, p3)]

        self.assertAlmostEqual(calculate_angle(*points, aspect_ratio=width / height), 90.0, places=6)
        # The same right angle read on normalized axes comes out near 59 degrees
        self.assertGreater(abs(calculate_angle(*points) - 90.0), 20.0)

    def test_real_frame_body_and_elbow_angles(self):
        f = VALID_05_FRAME_77
        aspect_ratio = 1280 / 720
        self.assertAlmostEqual(calculate_angle(f["shoulder"], f["hip"], f["ankle"], aspect_ratio), 165.5, delta=0.2)
        self.assertAlmostEqual(calculate_angle(f["shoulder"], f["elbow"], f["wrist"], aspect_ratio), 123.0, delta=0.2)

    def test_synthetic_pose_angles_for_each_aspect_ratio(self):
        for label, (width, height) in FRAME_SIZES.items():
            for elbow_deg in (170, 120, 90, 80):
                for hip_drop in (0.0, 0.06, 0.14, -0.10):
                    with self.subTest(aspect=label, elbow=elbow_deg, hip_drop=hip_drop):
                        f = pushup_frame(width, height, elbow_deg, hip_drop)
                        aspect_ratio = width / height
                        self.assertAlmostEqual(
                            calculate_angle(f["shoulder"], f["elbow"], f["wrist"], aspect_ratio), elbow_deg, places=6
                        )
                        self.assertAlmostEqual(
                            calculate_angle(f["shoulder"], f["hip"], f["ankle"], aspect_ratio),
                            body_angle_for_drop(hip_drop),
                            places=6,
                        )


class HipSagTest(unittest.TestCase):
    def test_real_valid_frames_are_not_flagged(self):
        aspect_ratio = 1280 / 720
        for label, f in (("valid_05 frame 77", VALID_05_FRAME_77), ("valid_04 frame 226", VALID_04_FRAME_226)):
            with self.subTest(frame=label):
                self.assertFalse(is_hip_sagging(f["shoulder"], f["hip"], f["ankle"], aspect_ratio))
                # Regression guard: read on normalized axes, these frames fall under 160 degrees
                self.assertTrue(is_hip_sagging(f["shoulder"], f["hip"], f["ankle"]))

    def test_real_sag_frame_is_still_flagged(self):
        f = SAG_01_FRAME_100
        self.assertTrue(is_hip_sagging(f["shoulder"], f["hip"], f["ankle"], 1280 / 720))

    def test_verdict_is_the_same_for_each_aspect_ratio(self):
        cases = (
            (0.14, True),    # 148.7 deg, hip toward the floor
            (0.06, False),   # 166.3 deg, hip toward the floor but above the 160 deg threshold
            (0.0, False),    # straight body
            (-0.14, False),  # 148.7 deg pike: hip above the shoulder-ankle line
        )
        for label, (width, height) in FRAME_SIZES.items():
            for elbow_deg in (170, 120, 80):
                for hip_drop, expected in cases:
                    with self.subTest(aspect=label, elbow=elbow_deg, hip_drop=hip_drop):
                        f = pushup_frame(width, height, elbow_deg, hip_drop)
                        self.assertEqual(
                            is_hip_sagging(f["shoulder"], f["hip"], f["ankle"], width / height), expected
                        )


class EvaluatePushupStreamTest(unittest.TestCase):
    def test_counts_full_depth_reps_for_each_aspect_ratio(self):
        for label, (width, height) in FRAME_SIZES.items():
            with self.subTest(aspect=label):
                result = evaluate_pushup_stream(pushup_stream(width, height, reps=3), width, height)
                self.assertTrue(RESULT_FIELDS <= set(result))
                self.assertEqual(result["rep_count"], 3)
                self.assertEqual(result["state"], "PLANK")
                self.assertIsNone(result["detected_error"])
                self.assertTrue(result["is_valid"])

    def test_shallow_reps_are_not_counted_for_each_aspect_ratio(self):
        for label, (width, height) in FRAME_SIZES.items():
            with self.subTest(aspect=label):
                stream = pushup_stream(width, height, reps=3, bottom_deg=100)
                result = evaluate_pushup_stream(stream, width, height)
                self.assertEqual(result["rep_count"], 0)
                self.assertIsNone(result["detected_error"])

    def test_wrong_frame_size_changes_the_rep_count(self):
        # Full-depth reps in a 16:9 frame are lost if the frame is treated as square
        width, height = FRAME_SIZES["16:9"]
        self.assertEqual(evaluate_pushup_stream(pushup_stream(width, height, reps=3), 1, 1)["rep_count"], 0)
        # Shallow reps in a 9:16 frame are wrongly counted if the frame is treated as square
        width, height = FRAME_SIZES["9:16"]
        shallow = pushup_stream(width, height, reps=3, bottom_deg=100)
        self.assertEqual(evaluate_pushup_stream(shallow, 1, 1)["rep_count"], 3)

    def test_sustained_sag_is_detected_for_each_aspect_ratio(self):
        for label, (width, height) in FRAME_SIZES.items():
            with self.subTest(aspect=label):
                stream = pushup_stream(width, height, reps=2, hip_drop=0.14)
                result = evaluate_pushup_stream(stream, width, height)
                self.assertEqual(result["detected_error"], "HIP_SAG")
                self.assertFalse(result["is_valid"])

    def test_mild_bend_above_threshold_is_not_flagged(self):
        for label, (width, height) in FRAME_SIZES.items():
            with self.subTest(aspect=label):
                stream = pushup_stream(width, height, reps=3, hip_drop=0.06)
                result = evaluate_pushup_stream(stream, width, height)
                self.assertIsNone(result["detected_error"])
                self.assertTrue(result["is_valid"])
                self.assertEqual(result["rep_count"], 3)

    def test_missing_landmarks_are_skipped(self):
        width, height = FRAME_SIZES["16:9"]
        clean = pushup_stream(width, height, reps=2)
        expected = evaluate_pushup_stream(clean, width, height)
        self.assertEqual(expected["rep_count"], 2)

        without_ankle = {k: v for k, v in clean[0].items() if k != "ankle"}
        hip_is_none = dict(clean[0], hip=None)
        gappy = [None, {}, without_ankle, hip_is_none]
        for frame in clean:
            gappy += [frame, None, without_ankle]
        self.assertEqual(evaluate_pushup_stream(gappy, width, height), expected)

    def test_stream_without_usable_frames(self):
        idle = {
            "detected_error": None, "is_valid": True, "rep_count": 0, "state": "IDLE",
            "current_error": None, "rep_errors": [], "valid_rep_count": 0,
        }
        for label, stream in (("empty", []), ("all None", [None] * 5), ("all incomplete", [{}, {"hip": (0.5, 0.5)}])):
            with self.subTest(stream=label):
                self.assertEqual(evaluate_pushup_stream(stream, 1280, 720), idle)

    def test_invalid_frame_size_is_rejected(self):
        stream = pushup_stream(1280, 720, reps=1)
        for width, height in ((0, 720), (1280, 0), (-1280, 720)):
            with self.subTest(width=width, height=height):
                with self.assertRaises(ValueError):
                    evaluate_pushup_stream(stream, width, height)


class TemporalConfirmationTest(unittest.TestCase):
    """Live HIP_SAG cue: on after 3 consecutive sag frames, off after 3 consecutive clean frames."""

    def test_window_sizes_assumed_by_these_tests(self):
        self.assertEqual(SAG_CONFIRM_FRAMES, 3)
        self.assertEqual(SAG_RECOVERY_FRAMES, 3)
        self.assertGreater(TRACKING_LOSS_FRAMES, max(SAG_CONFIRM_FRAMES, SAG_RECOVERY_FRAMES))

    def test_one_and_two_frame_glitches_are_ignored(self):
        for label, (width, height) in FRAME_SIZES.items():
            for codes in ("CCCCSCCCC", "CCCCSSCCCC", "CCSCCSSCCSCC"):
                with self.subTest(aspect=label, codes=codes):
                    results = run(plank(codes, width, height), width, height)
                    self.assertEqual(cues(results), "-" * len(codes))
                    self.assertIsNone(results[-1]["detected_error"])
                    self.assertTrue(results[-1]["is_valid"])

    def test_glitches_inside_reps_change_nothing(self):
        steps = [(angle, "C") for angle in rep_angles(3)]
        clean = run(build(steps))[-1]
        for glitch in (1, 2):
            with self.subTest(glitch_frames=glitch):
                glitchy = list(steps)
                for first, last in rep_windows(steps):
                    for i in list(range(first + 2, first + 2 + glitch)) + list(range(last - 3, last - 3 + glitch)):
                        glitchy[i] = (glitchy[i][0], "S")
                results = run(build(glitchy))
                self.assertEqual(cues(results), "-" * len(glitchy))
                self.assertEqual(results[-1], clean)
                self.assertEqual(results[-1]["rep_errors"], [None, None, None])
                self.assertEqual(results[-1]["valid_rep_count"], 3)

    def test_sustained_sag_activates_on_the_third_frame(self):
        results = run(plank("CCCCCSSSSSS"))
        self.assertEqual(cues(results), "-------SSSS")
        self.assertEqual([r["detected_error"] for r in results], [None] * 7 + [HIP_SAG] * 4)
        self.assertEqual([r["is_valid"] for r in results], [True] * 7 + [False] * 4)

    def test_sag_at_the_start_and_end_of_a_stream(self):
        self.assertEqual(cues(run(plank("SSSS"))), "--SS")
        # Two sag frames at the very end are never confirmed
        results = run(plank("CCCCSS"))
        self.assertEqual(cues(results), "------")
        self.assertIsNone(results[-1]["detected_error"])
        self.assertTrue(results[-1]["is_valid"])

    def test_recovery_clears_the_cue_but_keeps_the_history(self):
        results = run(plank("CCCSSSSSCCCCC"))
        self.assertEqual(cues(results), "-----SSSSS---")
        self.assertIsNone(results[-1]["current_error"])
        self.assertEqual(results[-1]["detected_error"], HIP_SAG)
        self.assertFalse(results[-1]["is_valid"])

    def test_brief_clean_frames_do_not_clear_an_active_cue(self):
        self.assertEqual(cues(run(plank("SSSCSSCCSCCC"))), "--SSSSSSSSS-")

    def test_a_second_sag_reactivates_the_cue(self):
        self.assertEqual(cues(run(plank("SSSCCCSSSCCC"))), "--SSS---SSS-")

    def test_mild_bend_and_pike_never_raise_the_cue(self):
        for codes in ("CCMMMMMMCC", "CCKKKKKKCC"):
            with self.subTest(codes=codes):
                results = run(plank(codes))
                self.assertEqual(cues(results), "-" * len(codes))
                self.assertIsNone(results[-1]["detected_error"])


class MissingLandmarksTest(unittest.TestCase):
    """A frame without all five landmarks is UNKNOWN: neither sag nor clean."""

    LOSS = TRACKING_LOSS_FRAMES
    SHORT_DROPOUTS = (1, 2, 3, 7, TRACKING_LOSS_FRAMES - 1)
    LONG_DROPOUTS = (TRACKING_LOSS_FRAMES, TRACKING_LOSS_FRAMES + 6)

    def lost(self, gap):
        """Cue during a dropout of `gap` frames that starts from a cue of None."""
        return "-" * min(gap, self.LOSS - 1) + "L" * max(0, gap - self.LOSS + 1)

    def test_unknown_frames_never_confirm_a_sag(self):
        for unknown in "NP":
            with self.subTest(unknown=unknown):
                results = run(plank("CCSS" + unknown * 6))
                self.assertEqual(cues(results), "-" * 10)
                self.assertIsNone(results[-1]["detected_error"])

    def test_dropout_restarts_a_pending_sag_confirmation(self):
        for gap in self.SHORT_DROPOUTS + self.LONG_DROPOUTS:
            for unknown in "NP":
                with self.subTest(gap=gap, unknown=unknown):
                    dropout = unknown * gap
                    # Two sag frames before and two after the dropout never add up to a confirmation
                    results = run(plank("CSS" + dropout + "SS"))
                    self.assertNotIn("S", cues(results))
                    self.assertIsNone(results[-1]["detected_error"])
                    # Three consecutive sag frames after the dropout do
                    results = run(plank("CSS" + dropout + "SSS"))
                    after = "--S" if gap < self.LOSS else "LLS"
                    self.assertEqual(cues(results), "---" + self.lost(gap) + after)
                    self.assertEqual(results[-1]["detected_error"], HIP_SAG)

    def test_single_unknown_frames_between_sag_frames_never_confirm(self):
        results = run(plank("CSNSNSNSNS"))
        self.assertEqual(cues(results), "-" * 10)
        self.assertIsNone(results[-1]["detected_error"])

    def test_dropout_restarts_a_pending_recovery(self):
        for gap in self.SHORT_DROPOUTS:
            for unknown in "NP":
                with self.subTest(gap=gap, unknown=unknown):
                    dropout = unknown * gap
                    # Two clean frames before and two after the dropout do not clear the warning
                    self.assertEqual(cues(run(plank("SSSCC" + dropout + "CC"))), "--SSS" + "S" * gap + "SS")
                    # Three consecutive clean frames after the dropout do
                    self.assertEqual(cues(run(plank("SSSCC" + dropout + "CCC"))), "--SSS" + "S" * gap + "SS-")

    def test_confirmed_warning_survives_a_short_dropout(self):
        for gap in self.SHORT_DROPOUTS:
            for unknown in "NP":
                with self.subTest(gap=gap, unknown=unknown):
                    results = run(plank("SSS" + unknown * gap + "SSS"))
                    self.assertEqual(cues(results), "--S" + "S" * gap + "SSS")

    def test_clean_cue_is_unchanged_by_a_short_dropout(self):
        for gap in self.SHORT_DROPOUTS:
            with self.subTest(gap=gap):
                self.assertEqual(cues(run(plank("CCC" + "N" * gap + "CCC"))), "-" * (gap + 6))

    def test_prolonged_tracking_loss_moves_the_cue_to_tracking_lost(self):
        for gap in self.LONG_DROPOUTS:
            for unknown in "NP":
                with self.subTest(gap=gap, unknown=unknown):
                    results = run(plank("CSSS" + unknown * gap))
                    self.assertEqual(cues(results), "---S" + "S" * (self.LOSS - 1) + "L" * (gap - self.LOSS + 1))
                    last = results[-1]
                    self.assertEqual(last["current_error"], TRACKING_LOST)
                    self.assertEqual(last["detected_error"], HIP_SAG)   # history survives
                    self.assertFalse(last["is_valid"])
                    self.assertEqual(last["state"], "PLANK")            # movement state untouched

    def test_cue_stays_lost_until_form_is_verified_again(self):
        lost = "N" * self.LOSS
        before = "-" * (self.LOSS - 1) + "L"
        # Clean form needs three consecutive clean frames before it is reported
        self.assertEqual(cues(run(plank(lost + "CCCC"))), before + "LL--")
        # A sag needs three consecutive sag frames, as usual
        self.assertEqual(cues(run(plank(lost + "SSSS"))), before + "LLSS")
        # Frames that do not agree verify nothing
        self.assertEqual(cues(run(plank(lost + "CSCCSCSSS"))), before + "LLLLLLLLS")
        # Another dropout restarts the verification
        self.assertEqual(cues(run(plank(lost + "CCNCCC"))), before + "LLLLL-")

    def test_warning_must_be_confirmed_again_after_tracking_loss(self):
        for gap in self.LONG_DROPOUTS:
            with self.subTest(gap=gap):
                results = run(plank("SSS" + "N" * gap + "SSSCCC"))
                lost = "S" * (self.LOSS - 1) + "L" * (gap - self.LOSS + 1)
                self.assertEqual(cues(results), "--S" + lost + "LLS" + "SS-")
                self.assertEqual(results[-1]["detected_error"], HIP_SAG)

    def test_pending_recovery_does_not_carry_over_a_tracking_loss(self):
        for gap in self.LONG_DROPOUTS:
            with self.subTest(gap=gap):
                results = run(plank("SSSCC" + "N" * gap + "CCC"))
                lost = "S" * (self.LOSS - 1) + "L" * (gap - self.LOSS + 1)
                self.assertEqual(cues(results), "--SSS" + lost + "LL-")

    def test_tracking_lost_without_any_error(self):
        last = run(plank("N" * self.LOSS))[-1]
        self.assertEqual(last["current_error"], TRACKING_LOST)
        self.assertIsNone(last["detected_error"])
        self.assertTrue(last["is_valid"])
        self.assertEqual(last["state"], "IDLE")
        self.assertEqual(last["rep_errors"], [])

    def test_tracking_loss_keeps_rep_history_and_rep_counting(self):
        steps = [(angle, "C") for angle in rep_angles(3)]
        (_, _), (first, last), (_, _) = rep_windows(steps)
        for i in range(first, first + 5):
            steps[i] = (steps[i][0], "S")
        middle = first + 8
        steps[middle:middle] = [(0, "N")] * (self.LOSS + 5)

        results = run(build(steps))
        self.assertIn("L", cues(results))
        self.assertEqual(results[-1]["rep_count"], 3)
        self.assertEqual(results[-1]["rep_errors"], [None, HIP_SAG, None])
        self.assertEqual(results[-1]["valid_rep_count"], 2)
        self.assertEqual(results[-1]["detected_error"], HIP_SAG)
        self.assertIsNone(results[-1]["current_error"])


class RepAttributionTest(unittest.TestCase):
    """A rep is marked when it contains a frame of a confirmed sag run."""

    def setUp(self):
        self.steps = [(angle, "C") for angle in rep_angles(3)]
        self.windows = rep_windows(self.steps)
        self.assertEqual(len(self.windows), 3)
        (self.first1, self.last1), (self.first2, self.last2), (self.first3, self.last3) = self.windows
        # The plank hold between two reps must be long enough for the boundary cases below
        self.assertGreaterEqual(self.first2 - self.last1, 6)

    def sag(self, first, last):
        for i in range(first, last + 1):
            self.steps[i] = (self.steps[i][0], "S")

    def results(self):
        return run(build(self.steps))

    def test_error_in_one_rep_marks_only_that_rep(self):
        self.sag(self.first2, self.last2)
        last = self.results()[-1]
        self.assertEqual(last["rep_count"], 3)
        self.assertEqual(last["rep_errors"], [None, HIP_SAG, None])
        self.assertEqual(last["valid_rep_count"], 2)
        self.assertEqual(last["detected_error"], HIP_SAG)
        self.assertFalse(last["is_valid"])
        self.assertIsNone(last["current_error"])

    def test_one_or_two_sag_frames_at_the_end_of_a_rep_do_not_mark_it(self):
        self.sag(self.last1 - 1, self.last1)
        last = self.results()[-1]
        self.assertEqual(last["rep_errors"], [None, None, None])
        self.assertIsNone(last["detected_error"])

    def test_sag_confirmed_on_the_lockout_frame_marks_the_finished_rep(self):
        self.sag(self.last1 - 1, self.last1 + 1)
        results = self.results()
        self.assertEqual(results[self.last1]["rep_count"], 0)
        self.assertEqual(results[self.last1 + 1]["rep_count"], 1)
        self.assertEqual(results[self.last1 + 1]["rep_errors"], [HIP_SAG])
        self.assertEqual(results[-1]["rep_errors"], [HIP_SAG, None, None])

    def test_rep_is_classified_on_its_lockout_frame(self):
        lockout = self.last1 + 1
        clean = self.results()
        self.assertEqual(clean[lockout]["rep_count"], 1)
        self.assertEqual(clean[lockout]["rep_errors"], [None])
        self.assertEqual(clean[lockout]["valid_rep_count"], 1)

        self.sag(self.first1, self.last1)
        flagged = self.results()
        self.assertEqual(flagged[lockout]["rep_count"], 1)
        self.assertEqual(flagged[lockout]["rep_errors"], [HIP_SAG])
        self.assertEqual(flagged[lockout]["valid_rep_count"], 0)

    def test_sag_starting_on_the_last_frame_of_a_rep_holds_back_its_classification(self):
        self.sag(self.last1, self.last1 + 2)
        results = self.results()
        lockout = self.last1 + 1
        # Counted at lockout, but not classified while the sag run could still be confirmed
        self.assertEqual(results[lockout]["rep_count"], 1)
        self.assertEqual(results[lockout]["rep_errors"], [])
        self.assertEqual(results[lockout]["valid_rep_count"], 0)
        # Settled on the next frame, here as an error
        self.assertEqual(results[lockout + 1]["rep_errors"], [HIP_SAG])
        self.assertEqual(results[lockout + 1]["valid_rep_count"], 0)
        self.assertEqual(results[-1]["rep_errors"], [HIP_SAG, None, None])

    def test_held_back_classification_is_settled_as_valid_when_the_sag_ends(self):
        self.sag(self.last1, self.last1 + 1)
        results = self.results()
        lockout = self.last1 + 1
        self.assertEqual(results[lockout]["rep_errors"], [])
        self.assertEqual(results[lockout + 1]["rep_errors"], [None])
        self.assertEqual(results[lockout + 1]["valid_rep_count"], 1)
        self.assertIsNone(results[-1]["detected_error"])

    def test_dropout_settles_a_held_back_classification_as_valid(self):
        self.sag(self.last1, self.last1 + 3)
        lockout = self.last1 + 1
        self.steps[lockout + 1:lockout + 1] = [(0, "N")]
        results = self.results()
        self.assertEqual(results[lockout]["rep_errors"], [])
        self.assertEqual(results[lockout + 1]["rep_errors"], [None])      # the unknown frame ends the run
        self.assertEqual(results[-1]["rep_errors"], [None, None, None])
        self.assertIsNone(results[-1]["detected_error"])                  # two sag frames each side of the dropout

    def test_dropout_before_lockout_leaves_nothing_pending(self):
        self.sag(self.last1, self.last1 + 1)
        self.steps[self.last1 + 1:self.last1 + 1] = [(0, "N")]
        results = self.results()
        lockout = self.last1 + 2
        self.assertEqual(results[lockout]["rep_count"], 1)
        self.assertEqual(results[lockout]["rep_errors"], [None])

    def test_rep_counted_on_the_last_frame_can_end_unclassified(self):
        self.sag(self.last1, self.last1 + 1)
        frames = build(self.steps[:self.last1 + 2])     # the stream ends on the lockout frame
        last = evaluate_pushup_stream(frames, 1280, 720)
        self.assertEqual(last["rep_count"], 1)
        self.assertEqual(last["rep_errors"], [])
        self.assertEqual(last["valid_rep_count"], 0)
        self.assertIsNone(last["detected_error"])

    def test_unconfirmed_sag_at_the_end_of_a_rep_is_forgotten(self):
        self.sag(self.last1, self.last1 + 1)          # two frames, then clean
        self.sag(self.last1 + 3, self.last1 + 5)      # a separate run confirmed in the plank hold
        last = self.results()[-1]
        self.assertEqual(last["rep_errors"], [None, None, None])
        self.assertEqual(last["detected_error"], HIP_SAG)

    def test_sag_only_in_the_plank_hold_marks_no_rep(self):
        # Starts on the lockout frame itself, which is already outside the rep
        self.sag(self.last1 + 1, self.last1 + 4)
        results = self.results()
        self.assertEqual(results[self.last1 + 1]["rep_errors"], [None])
        last = results[-1]
        self.assertEqual(last["rep_errors"], [None, None, None])
        self.assertEqual(last["valid_rep_count"], 3)
        self.assertEqual(last["detected_error"], HIP_SAG)   # session history only
        self.assertFalse(last["is_valid"])

    def test_fading_cue_does_not_mark_the_next_rep(self):
        self.sag(self.first2 - 4, self.first2 - 2)
        results = self.results()
        # The cue is still active on the first frame of rep 2, which itself has no sag frame
        self.assertEqual(results[self.first2]["state"], "DESCENDING")
        self.assertEqual(results[self.first2]["current_error"], HIP_SAG)
        self.assertIsNone(results[self.first2 + 1]["current_error"])
        self.assertEqual(results[-1]["rep_errors"], [None, None, None])

    def test_sag_starting_before_a_rep_and_confirmed_in_it_marks_that_rep(self):
        self.sag(self.first2 - 2, self.first2)
        results = self.results()
        self.assertEqual(results[self.first2]["current_error"], HIP_SAG)
        self.assertEqual(results[-1]["rep_errors"], [None, HIP_SAG, None])

    def test_confirmed_sag_continuing_into_a_rep_marks_that_rep(self):
        self.sag(self.first2 - 5, self.first2)
        self.assertEqual(self.results()[-1]["rep_errors"], [None, HIP_SAG, None])

    def test_sag_spanning_two_reps_marks_both(self):
        self.sag(self.last1, self.first2)
        self.assertEqual(self.results()[-1]["rep_errors"], [HIP_SAG, HIP_SAG, None])

    def test_tracking_loss_drops_an_unconfirmed_sag_from_the_finished_rep(self):
        self.sag(self.last1, self.last1 + 4)
        self.steps[self.last1 + 2:self.last1 + 2] = [(0, "N")] * TRACKING_LOSS_FRAMES
        last = self.results()[-1]
        self.assertEqual(last["rep_errors"], [None, None, None])
        self.assertEqual(last["detected_error"], HIP_SAG)   # the run after the loss is confirmed on its own

    def test_abandoned_shallow_attempt_adds_no_rep_entry(self):
        shallow = list(range(165, 99, -5)) + list(range(105, 171, 5))
        steps = [(a, "C") for a in rep_angles(1)] + [(a, "S") for a in shallow] + [(a, "C") for a in rep_angles(1)]
        last = run(build(steps))[-1]
        self.assertEqual(last["rep_count"], 2)
        self.assertEqual(last["rep_errors"], [None, None])
        self.assertEqual(last["valid_rep_count"], 2)
        self.assertEqual(last["detected_error"], HIP_SAG)
        self.assertFalse(last["is_valid"])

    def test_rep_in_progress_at_the_end_of_the_stream_adds_no_rep_entry(self):
        steps = [(a, "C") for a in rep_angles(1)] + [(a, "S") for a in range(165, 79, -5)]
        last = run(build(steps))[-1]
        self.assertEqual(last["state"], "BOTTOM")
        self.assertEqual(last["rep_count"], 1)
        self.assertEqual(last["rep_errors"], [None])
        self.assertEqual(last["current_error"], HIP_SAG)
        self.assertEqual(last["detected_error"], HIP_SAG)

    def test_rep_count_includes_reps_with_errors(self):
        for label, (width, height) in FRAME_SIZES.items():
            with self.subTest(aspect=label):
                steps = [(170, "C")] * 3 + [(angle, "S") for angle in rep_angles(3)[3:]]
                last = run(build(steps, width, height), width, height)[-1]
                self.assertEqual(last["rep_count"], 3)
                self.assertEqual(last["rep_errors"], [HIP_SAG, HIP_SAG, HIP_SAG])
                self.assertEqual(last["valid_rep_count"], 0)


class BackwardCompatibilityTest(unittest.TestCase):
    """Phase 1 consumers keep working, and movement states / rep counts are untouched."""

    def scenario_streams(self, width, height):
        yield "clean reps", pushup_stream(width, height, reps=3)
        yield "shallow reps", pushup_stream(width, height, reps=3, bottom_deg=100)
        yield "sustained sag", pushup_stream(width, height, reps=2, hip_drop=0.14)
        yield "mild bend", pushup_stream(width, height, reps=3, hip_drop=0.06)
        yield "pike", pushup_stream(width, height, reps=2, hip_drop=-0.10)
        yield "empty", []
        yield "no pose", [None] * 40

    def random_stream(self, rng, width, height):
        steps, angle, code = [], 170.0, "C"
        for _ in range(rng.randint(40, 160)):
            angle = min(178.0, max(55.0, angle + rng.uniform(-18.0, 18.0)))
            if rng.random() < 0.2:
                code = rng.choice("CCCCSSMKNP")
            steps.append((angle, code))
        if rng.random() < 0.5:
            at = rng.randrange(len(steps))
            steps[at:at] = [(0, "N")] * rng.randint(TRACKING_LOSS_FRAMES, 2 * TRACKING_LOSS_FRAMES)
        return build(steps, width, height)

    def flickering_rep_stream(self, rng, width, height):
        """Full-depth reps where every frame is independently clean, sagging or missing."""
        return build([(angle, rng.choice("CCCSSSN")) for angle in rep_angles(6)], width, height)

    def test_existing_fields_keep_their_names_and_types(self):
        result = evaluate_pushup_stream(pushup_stream(1280, 720, reps=2), 1280, 720)
        self.assertEqual(set(result), RESULT_FIELDS | HISTORY_FIELDS)
        self.assertIsNone(result["detected_error"])
        self.assertIs(result["is_valid"], True)
        self.assertIsInstance(result["rep_count"], int)
        self.assertIsInstance(result["state"], str)
        flagged = evaluate_pushup_stream(pushup_stream(1280, 720, reps=2, hip_drop=0.14), 1280, 720)
        self.assertEqual(flagged["detected_error"], "HIP_SAG")
        self.assertIs(flagged["is_valid"], False)

    def test_phase1_fields_are_unchanged_when_sag_is_sustained_or_absent(self):
        for label, (width, height) in FRAME_SIZES.items():
            for name, frames in self.scenario_streams(width, height):
                with self.subTest(aspect=label, stream=name):
                    _, expected = phase1_reference(frames, width, height)
                    result = evaluate_pushup_stream(frames, width, height)
                    self.assertEqual({k: result[k] for k in RESULT_FIELDS}, expected)

    def test_states_and_rep_counts_match_phase1_on_every_frame(self):
        rng = random.Random(25)
        streams = []
        for width, height in FRAME_SIZES.values():
            streams += [(frames, width, height) for _, frames in self.scenario_streams(width, height)]
            streams += [(self.random_stream(rng, width, height), width, height) for _ in range(75)]
            streams += [(self.flickering_rep_stream(rng, width, height), width, height) for _ in range(25)]
        reps_seen = 0
        for frames, width, height in streams:
            expected, _ = phase1_reference(frames, width, height)
            results = run(frames, width, height)
            self.assertEqual([(r["state"], r["rep_count"]) for r in results], expected)
            reps_seen += expected[-1][1] if expected else 0
        self.assertGreater(reps_seen, 50)   # the random streams must actually exercise rep counting

    def test_batch_result_equals_the_last_frame_result(self):
        rng = random.Random(7)
        for _ in range(40):
            frames = self.random_stream(rng, 1280, 720)
            self.assertEqual(evaluate_pushup_stream(frames, 1280, 720), run(frames)[-1])

    def test_rep_history_is_consistent_on_every_frame(self):
        rng = random.Random(11)
        streams = [self.random_stream(rng, 1280, 720) for _ in range(40)]
        streams += [self.flickering_rep_stream(rng, 1280, 720) for _ in range(40)]
        held_back = 0
        for frames in streams:
            previous = None
            for result in run(frames):
                unclassified = result["rep_count"] - len(result["rep_errors"])
                self.assertIn(unclassified, (0, 1))
                self.assertEqual(result["valid_rep_count"], result["rep_errors"].count(None))
                self.assertEqual(result["is_valid"], result["detected_error"] is None)
                if result["current_error"] == HIP_SAG or HIP_SAG in result["rep_errors"]:
                    self.assertEqual(result["detected_error"], HIP_SAG)
                if previous is not None:
                    # Classified reps are only ever appended, never changed
                    self.assertEqual(result["rep_errors"][:len(previous["rep_errors"])], previous["rep_errors"])
                    # A held-back classification is settled on the very next frame
                    if previous["rep_count"] > len(previous["rep_errors"]):
                        self.assertEqual(len(result["rep_errors"]), previous["rep_count"])
                held_back += unclassified
                previous = result
        self.assertGreater(held_back, 5)   # the streams must actually exercise the held-back case

    def test_returned_results_are_independent_snapshots(self):
        evaluator = PushupEvaluator(1280, 720)
        for frame in pushup_stream(1280, 720, reps=1):
            result = evaluator.update(frame)
        result["rep_errors"].append("tampered")
        self.assertEqual(evaluator.result()["rep_errors"], [None])

    def test_evaluator_rejects_an_invalid_frame_size(self):
        for width, height in ((0, 720), (1280, 0), (-1280, 720)):
            with self.subTest(width=width, height=height):
                with self.assertRaises(ValueError):
                    PushupEvaluator(width, height)


class GoldenSpikeImportGuardTest(unittest.TestCase):
    def test_benchmark_fails_instead_of_mocking_when_modules_are_missing(self):
        script = os.path.join(PROJECT_ROOT, "tests", "test_golden_spike.py")
        for module in ("src.vision.pose_extractor", "src.biomechanics.pushup_rules"):
            with self.subTest(missing=module):
                # A None entry in sys.modules makes the import raise ImportError
                code = (
                    "import runpy, sys; "
                    f"sys.modules[{module!r}] = None; "
                    "runpy.run_path(sys.argv[1], run_name='__main__')"
                )
                proc = subprocess.run(
                    [sys.executable, "-c", code, script],
                    cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
                )
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn("Golden Spike benchmark not run", proc.stderr)
                self.assertNotIn("RUNNING GOLDEN SPIKE BENCHMARK", proc.stdout)
                self.assertNotIn("FINAL ACCURACY", proc.stdout)


if __name__ == "__main__":
    unittest.main()
