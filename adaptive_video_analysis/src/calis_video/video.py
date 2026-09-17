from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import cv2
import numpy as np

from .config import Settings
from .pose import MediaPipePoseExtractor, derive_pose_metrics
from .schemas import FrameEvidence, VideoMetadata


class VideoValidationError(ValueError):
    pass


def probe_video(path: Path) -> VideoMetadata:
    if not path.is_file():
        raise VideoValidationError(f"Video does not exist: {path}")
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise VideoValidationError("OpenCV could not read the uploaded video")
    try:
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if fps <= 0 or width <= 0 or height <= 0:
            raise VideoValidationError("Video metadata is invalid or incomplete")
        duration = total_frames / fps if total_frames > 0 else 0.0
        if duration <= 0:
            raise VideoValidationError("Video duration could not be determined")
        return VideoMetadata(
            duration_seconds=duration,
            fps=fps,
            width=width,
            height=height,
            total_frames=total_frames,
            processed_frames=0,
        )
    finally:
        capture.release()


def validate_video(path: Path, settings: Settings) -> VideoMetadata:
    size = path.stat().st_size
    if size > settings.max_upload_bytes:
        limit_mb = settings.max_upload_bytes / (1024 * 1024)
        raise VideoValidationError(f"Video exceeds the {limit_mb:.0f} MB limit")
    metadata = probe_video(path)
    if metadata.duration_seconds > settings.max_video_seconds + 0.05:
        raise VideoValidationError(
            f"Video is {metadata.duration_seconds:.1f}s; the limit is "
            f"{settings.max_video_seconds:.0f}s"
        )
    return metadata


def _resize(frame: np.ndarray, max_dimension: int) -> np.ndarray:
    height, width = frame.shape[:2]
    scale = min(1.0, max_dimension / max(height, width))
    if scale >= 1.0:
        return frame
    return cv2.resize(
        frame,
        (max(1, round(width * scale)), max(1, round(height * scale))),
        interpolation=cv2.INTER_AREA,
    )


def scan_video(
    path: Path,
    settings: Settings,
    pose_extractor: MediaPipePoseExtractor,
) -> Iterator[FrameEvidence]:
    """Decode once, but run pose inference only at ``analysis_fps``."""
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise VideoValidationError("Could not open video for scanning")
    native_fps = float(capture.get(cv2.CAP_PROP_FPS)) or 30.0
    sample_period = 1.0 / settings.analysis_fps
    next_sample_seconds = 0.0
    frame_index = 0
    sample_index = 0
    previous_gray: np.ndarray | None = None
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            timestamp_seconds = frame_index / native_fps
            frame_index += 1
            if timestamp_seconds + (0.5 / native_fps) < next_sample_seconds:
                continue
            next_sample_seconds += sample_period

            resized = _resize(frame, settings.max_dimension)
            gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            motion_score = (
                0.0
                if previous_gray is None
                else float(np.mean(cv2.absdiff(previous_gray, gray)) / 255.0)
            )
            previous_gray = gray
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            pose = pose_extractor.detect(rgb, round(timestamp_seconds * 1000))
            metrics = derive_pose_metrics(
                pose, visibility_threshold=settings.min_landmark_visibility
            )
            ok, encoded = cv2.imencode(
                ".jpg",
                resized,
                [cv2.IMWRITE_JPEG_QUALITY, settings.jpeg_quality],
            )
            if not ok:
                continue
            yield FrameEvidence(
                index=sample_index,
                timestamp_seconds=timestamp_seconds,
                pose_confidence=pose.confidence if pose else 0.0,
                motion_score=motion_score,
                metrics=metrics,
                jpeg=encoded.tobytes(),
            )
            sample_index += 1
    finally:
        capture.release()

