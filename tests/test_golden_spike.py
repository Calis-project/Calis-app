"""
Golden Spike End-to-End Integration Test
Evaluates Push-up Form Detection Accuracy on Benchmark Dataset
Target DoD: >= 90% Classification Accuracy
"""

import json
import os
import sys

REQUIRED_ACCURACY = 90.0

# اضافه کردن پوشه اصلی پروژه به مسیرهای پایتون (رفع باگ ایمپورت)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# بنچ‌مارک فقط با ماژول‌های واقعی معتبر است؛ در صورت خطای ایمپورت، بدون حالت MOCK متوقف می‌شود
try:
    from src.vision.pose_extractor import extract_landmarks_with_frame_size
    from src.biomechanics.pushup_rules import evaluate_pushup_stream
except ImportError as e:
    raise ImportError(
        f"[FAILED] Golden Spike benchmark not run: the real Vision/Biomechanics modules could not be imported ({e})."
    ) from e


def run_benchmark():
    dataset_dir = os.path.join(PROJECT_ROOT, "dataset", "raw")
    metadata_path = os.path.join(dataset_dir, "metadata.json")

    # بررسی وجود دیتاست
    if not os.path.exists(metadata_path):
        print(f"[INFO] metadata.json not found at {metadata_path}. Generating dummy test cases.")
        test_cases = [
            {"file": "valid_01.mp4", "ground_truth": "VALID"},
            {"file": "valid_02.mp4", "ground_truth": "VALID"},
            {"file": "sag_01.mp4", "ground_truth": "HIP_SAG"},
            {"file": "sag_02.mp4", "ground_truth": "HIP_SAG"},
        ]
    else:
        with open(metadata_path, "r", encoding="utf-8") as f:
            test_cases = json.load(f)

    correct_predictions = 0
    sag_detected = 0
    sag_samples = 0
    total_samples = len(test_cases)

    print(f"\n{'='*40}")
    print(f"RUNNING GOLDEN SPIKE BENCHMARK ({total_samples} samples)")
    print(f"{'='*40}")

    for case in test_cases:
        video_file = case["file"]
        ground_truth = case["ground_truth"]
        video_path = os.path.join(dataset_dir, video_file)

        # اجرای پایپ‌لاین
        landmarks, (frame_width, frame_height) = extract_landmarks_with_frame_size(video_path)
        result = evaluate_pushup_stream(landmarks, frame_width, frame_height)

        detected = "HIP_SAG" if result.get("detected_error") == "HIP_SAG" else "VALID"
        is_match = (detected == ground_truth)

        if is_match:
            correct_predictions += 1
            status = "PASS"
        else:
            status = "FAIL"

        if ground_truth == "HIP_SAG":
            sag_samples += 1
            sag_detected += is_match

        print(f"[{status}] File: {video_file} | Expected: {ground_truth} | Got: {detected}")

    accuracy = (correct_predictions / total_samples) * 100 if total_samples > 0 else 0
    print(f"{'='*40}")
    print(f"HIP_SAG CLIPS DETECTED: {sag_detected}/{sag_samples}")
    print(f"FINAL ACCURACY: {accuracy:.1f}% (Required: >= {REQUIRED_ACCURACY:.1f}%)")
    print(f"{'='*40}")

    if accuracy < REQUIRED_ACCURACY:
        print(f"[FAILED] Model accuracy below {REQUIRED_ACCURACY:.0f}% threshold.")
        return 1

    # دقت کلی کافی است؛ ولی تا وقتی همه کلیپ‌های sag تشخیص داده نشوند پذیرش کامل اعلام نمی‌شود
    if sag_detected < sag_samples:
        print(
            f"[PARTIAL] Accuracy threshold met, but HIP_SAG no-regression is NOT met "
            f"({sag_detected}/{sag_samples} detected). Full acceptance is not claimed."
        )
    else:
        print("[SUCCESS] Golden Spike Acceptance Criteria Met!")
    return 0


if __name__ == "__main__":
    sys.exit(run_benchmark())
