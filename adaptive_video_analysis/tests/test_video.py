from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from calis_video.config import Settings
from calis_video.video import probe_video, scan_video


class NoPoseExtractor:
    def detect(self, _frame: np.ndarray, _timestamp_ms: int):
        return None


def _write_test_video(path: Path) -> None:
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        10.0,
        (160, 120),
    )
    assert writer.isOpened()
    for index in range(20):
        frame = np.full((120, 160, 3), index * 8, dtype=np.uint8)
        writer.write(frame)
    writer.release()


def test_probe_and_sparse_scan(tmp_path) -> None:
    video = tmp_path / "test.mp4"
    _write_test_video(video)
    metadata = probe_video(video)
    frames = list(
        scan_video(
            video,
            Settings(analysis_fps=4, max_dimension=160),
            NoPoseExtractor(),  # type: ignore[arg-type]
        )
    )
    assert metadata.duration_seconds == 2.0
    assert 7 <= len(frames) <= 9
    assert all(frame.jpeg for frame in frames)

