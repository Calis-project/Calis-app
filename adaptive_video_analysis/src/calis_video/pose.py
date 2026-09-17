from __future__ import annotations

import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .geometry import angle_degrees, line_angle_from_vertical, robust_median


LANDMARK_NAMES = {
    0: "nose",
    11: "left_shoulder",
    12: "right_shoulder",
    13: "left_elbow",
    14: "right_elbow",
    15: "left_wrist",
    16: "right_wrist",
    23: "left_hip",
    24: "right_hip",
    25: "left_knee",
    26: "right_knee",
    27: "left_ankle",
    28: "right_ankle",
    29: "left_heel",
    30: "right_heel",
    31: "left_foot_index",
    32: "right_foot_index",
}

MODEL_URLS = {
    "lite": (
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
        "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
    ),
    "full": (
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
        "pose_landmarker_full/float16/1/pose_landmarker_full.task"
    ),
    "heavy": (
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
        "pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task"
    ),
}


@dataclass(slots=True)
class PoseSnapshot:
    normalized: np.ndarray
    world: np.ndarray
    visibility: np.ndarray

    @property
    def confidence(self) -> float:
        core = self.visibility[[11, 12, 23, 24, 25, 26, 27, 28]]
        return float(np.clip(np.mean(core), 0.0, 1.0))


def download_pose_model(target: Path, variant: str = "lite") -> Path:
    if variant not in MODEL_URLS:
        raise ValueError(f"Unknown model variant: {variant}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 1_000_000:
        return target
    partial = target.with_suffix(target.suffix + ".part")
    try:
        request = urllib.request.Request(
            MODEL_URLS[variant], headers={"User-Agent": "Calis-App/0.1"}
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            with partial.open("wb") as destination:
                while chunk := response.read(1024 * 1024):
                    destination.write(chunk)
        partial.replace(target)
    finally:
        partial.unlink(missing_ok=True)
    return target


class MediaPipePoseExtractor:
    """Small lifecycle wrapper around MediaPipe's video pose landmarker."""

    def __init__(
        self,
        model_path: Path,
        *,
        min_detection_confidence: float = 0.5,
        min_presence_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        if not model_path.exists():
            raise FileNotFoundError(
                f"Pose model not found at {model_path}. Run "
                "`calis-video download-model` or set CALIS_POSE_MODEL."
            )
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        self._mp = mp
        options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=min_detection_confidence,
            min_pose_presence_confidence=min_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = vision.PoseLandmarker.create_from_options(options)

    def close(self) -> None:
        self._landmarker.close()

    def __enter__(self) -> "MediaPipePoseExtractor":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def detect(self, rgb_frame: np.ndarray, timestamp_ms: int) -> PoseSnapshot | None:
        image = self._mp.Image(
            image_format=self._mp.ImageFormat.SRGB, data=rgb_frame
        )
        result = self._landmarker.detect_for_video(image, timestamp_ms)
        if not result.pose_landmarks or not result.pose_world_landmarks:
            return None
        normalized_landmarks = result.pose_landmarks[0]
        world_landmarks = result.pose_world_landmarks[0]
        normalized = np.asarray(
            [[point.x, point.y, point.z] for point in normalized_landmarks],
            dtype=np.float32,
        )
        world = np.asarray(
            [[point.x, point.y, point.z] for point in world_landmarks],
            dtype=np.float32,
        )
        visibility = np.asarray(
            [float(point.visibility or 0.0) for point in normalized_landmarks],
            dtype=np.float32,
        )
        return PoseSnapshot(normalized=normalized, world=world, visibility=visibility)


def _visible_angle(
    pose: PoseSnapshot, indices: tuple[int, int, int], threshold: float
) -> float | None:
    if min(float(pose.visibility[index]) for index in indices) < threshold:
        return None
    return angle_degrees(*(pose.world[index] for index in indices))


def derive_pose_metrics(
    pose: PoseSnapshot | None, visibility_threshold: float = 0.5
) -> dict[str, float | None]:
    if pose is None:
        return {
            "left_elbow_angle": None,
            "right_elbow_angle": None,
            "elbow_angle": None,
            "left_hip_angle": None,
            "right_hip_angle": None,
            "body_line_angle": None,
            "left_knee_angle": None,
            "right_knee_angle": None,
            "knee_angle": None,
            "knee_angle_asymmetry": None,
            "torso_deviation_vertical": None,
        }

    left_elbow = _visible_angle(pose, (11, 13, 15), visibility_threshold)
    right_elbow = _visible_angle(pose, (12, 14, 16), visibility_threshold)
    left_hip = _visible_angle(pose, (11, 23, 27), visibility_threshold)
    right_hip = _visible_angle(pose, (12, 24, 28), visibility_threshold)
    left_knee = _visible_angle(pose, (23, 25, 27), visibility_threshold)
    right_knee = _visible_angle(pose, (24, 26, 28), visibility_threshold)

    torso_values: list[float | None] = []
    for shoulder, hip in ((11, 23), (12, 24)):
        if min(pose.visibility[shoulder], pose.visibility[hip]) >= visibility_threshold:
            torso_values.append(
                line_angle_from_vertical(
                    pose.normalized[shoulder], pose.normalized[hip]
                )
            )

    asymmetry = (
        abs(left_knee - right_knee)
        if left_knee is not None and right_knee is not None
        else None
    )
    return {
        "left_elbow_angle": left_elbow,
        "right_elbow_angle": right_elbow,
        "elbow_angle": robust_median([left_elbow, right_elbow]),
        "left_hip_angle": left_hip,
        "right_hip_angle": right_hip,
        "body_line_angle": robust_median([left_hip, right_hip]),
        "left_knee_angle": left_knee,
        "right_knee_angle": right_knee,
        "knee_angle": robust_median([left_knee, right_knee]),
        "knee_angle_asymmetry": asymmetry,
        "torso_deviation_vertical": robust_median(torso_values),
    }

