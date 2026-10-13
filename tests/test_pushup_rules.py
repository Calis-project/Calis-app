"""
Unit tests for the push-up rules engine geometry (Issue #25, Phase 1).
Angles must be measured in real frame geometry, whatever the frame aspect ratio.
"""

import math
import os
import subprocess
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.biomechanics.pushup_rules import calculate_angle, evaluate_pushup_stream, is_hip_sagging

FRAME_SIZES = {
    "16:9": (1280, 720),
    "4:3": (640, 480),
    "9:16": (720, 1280),
    "1:1": (1000, 1000),
}

RESULT_FIELDS = {"detected_error", "is_valid", "rep_count", "state"}

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


def pushup_stream(width, height, reps, bottom_deg=80, top_deg=170, hip_drop=0.0):
    """Normalized landmark stream: plank hold, then `reps` cycles of top -> bottom -> top."""
    angles = [top_deg] * 3
    for _ in range(reps):
        angles += list(range(top_deg - 5, bottom_deg - 1, -5))
        angles += list(range(bottom_deg + 5, top_deg + 1, 5))
    return [pushup_frame(width, height, a, hip_drop) for a in angles]


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
                self.assertEqual(set(result), RESULT_FIELDS)
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
        idle = {"detected_error": None, "is_valid": True, "rep_count": 0, "state": "IDLE"}
        for label, stream in (("empty", []), ("all None", [None] * 5), ("all incomplete", [{}, {"hip": (0.5, 0.5)}])):
            with self.subTest(stream=label):
                self.assertEqual(evaluate_pushup_stream(stream, 1280, 720), idle)

    def test_invalid_frame_size_is_rejected(self):
        stream = pushup_stream(1280, 720, reps=1)
        for width, height in ((0, 720), (1280, 0), (-1280, 720)):
            with self.subTest(width=width, height=height):
                with self.assertRaises(ValueError):
                    evaluate_pushup_stream(stream, width, height)


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
