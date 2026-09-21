"""
Pose Keypoints Extraction Pipeline (MediaPipe) - Sprint 01
Extracts (x, y) coordinates for pushup analysis meeting < 35ms/frame DoD.
"""

import os
import sys
import time
import urllib.request
from typing import Dict, List, Optional, Tuple

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"


def get_model_path() -> str:
    """Finds local model file or downloads it once to user cache."""
    candidates = [
        os.path.join(os.path.dirname(__file__), "pose_landmarker_lite.task"),
        os.path.join(os.path.dirname(__file__), "..", "..", "mediapipe_pose", "pose_landmarker_lite.task"),
        os.path.join(os.path.expanduser("~"), ".cache", "calis", "pose_landmarker_lite.task"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path

    cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "calis")
    os.makedirs(cache_dir, exist_ok=True)
    target = os.path.join(cache_dir, "pose_landmarker_lite.task")
    if not os.path.isfile(target):
        print("[INFO] Downloading pose_landmarker_lite.task for CPU inference...")
        req = urllib.request.Request(MODEL_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp, open(target, "wb") as f:
            f.write(resp.read())
    return target


def extract_landmarks(
    video_path: str,
    model_path: Optional[str] = None,
) -> List[Optional[Dict[str, Tuple[float, float]]]]:
    """
    Extracts keypoint coordinates per frame for pushup analysis.
    Returns: list of dicts containing 'shoulder', 'elbow', 'wrist', 'hip', 'ankle'
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    resolved_model = model_path or get_model_path()
    base_options = python.BaseOptions(model_asset_path=resolved_model)
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
    )

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Unable to open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    fps = fps if (fps and fps > 0) else 30.0

    all_frames_landmarks: List[Optional[Dict[str, Tuple[float, float]]]] = []
    latencies = []
    last_timestamp_ms = -1

    with vision.PoseLandmarker.create_from_options(options) as landmarker:
        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Monotonically increasing timestamp required by MediaPipe VIDEO mode
            timestamp_ms = max(int((frame_idx / fps) * 1000), last_timestamp_ms + 1)
            last_timestamp_ms = timestamp_ms

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            t0 = time.perf_counter()
            result = landmarker.detect_for_video(mp_image, timestamp_ms)
            latencies.append((time.perf_counter() - t0) * 1000.0)

            if result.pose_landmarks and len(result.pose_landmarks) > 0:
                lm = result.pose_landmarks[0]
                # Sagittal view: determine visible side facing the camera
                # Left: 11 (shoulder), 13 (elbow), 15 (wrist), 23 (hip), 27 (ankle)
                # Right: 12, 14, 16, 24, 28
                left_vis = sum(lm[i].visibility for i in [11, 13, 15, 23, 27])
                right_vis = sum(lm[i].visibility for i in [12, 14, 16, 24, 28])
                offset = 0 if left_vis >= right_vis else 1

                all_frames_landmarks.append({
                    "shoulder": (float(lm[11 + offset].x), float(lm[11 + offset].y)),
                    "elbow": (float(lm[13 + offset].x), float(lm[13 + offset].y)),
                    "wrist": (float(lm[15 + offset].x), float(lm[15 + offset].y)),
                    "hip": (float(lm[23 + offset].x), float(lm[23 + offset].y)),
                    "ankle": (float(lm[27 + offset].x), float(lm[27 + offset].y)),
                })
            else:
                all_frames_landmarks.append(None)

            frame_idx += 1

    cap.release()

    if latencies:
        avg_ms = sum(latencies) / len(latencies)
        print(f"Processed {len(latencies)} frames | Avg CPU latency: {avg_ms:.2f} ms/frame (< 35ms DoD: {'PASS' if avg_ms < 35.0 else 'FAIL'})")

    return all_frames_landmarks


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Add `print` here to see landmarks
        extract_landmarks(sys.argv[1])
    else:
        print("Usage: python src/vision/pose_extractor.py <path_to_video.mp4>")
