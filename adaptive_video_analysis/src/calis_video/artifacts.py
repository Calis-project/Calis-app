from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from .providers.base import ImageInput


def labeled_jpeg(image: ImageInput) -> bytes:
    frame = cv2.imdecode(np.frombuffer(image.jpeg, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        return image.jpeg
    label = f"{image.timestamp_seconds:.2f}s"
    cv2.rectangle(frame, (0, 0), (150, 32), (10, 10, 10), thickness=-1)
    cv2.putText(
        frame,
        label,
        (9, 23),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    ok, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 84])
    return encoded.tobytes() if ok else image.jpeg


def save_debug_artifacts(
    directory: Path,
    overview: list[ImageInput],
    detail: list[ImageInput],
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for group_name, images in (("overview", overview), ("detail", detail)):
        group = directory / group_name
        group.mkdir(exist_ok=True)
        for index, image in enumerate(images, 1):
            target = group / f"{index:02d}_{image.timestamp_seconds:.3f}s.jpg"
            target.write_bytes(labeled_jpeg(image))


def make_contact_sheet(images: list[ImageInput], columns: int = 4) -> bytes | None:
    if not images:
        return None
    decoded: list[np.ndarray] = []
    for image in images:
        data = labeled_jpeg(image)
        frame = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
        if frame is not None:
            decoded.append(frame)
    if not decoded:
        return None
    cell_width = 320
    cell_height = 200
    rows = (len(decoded) + columns - 1) // columns
    sheet = np.zeros((rows * cell_height, columns * cell_width, 3), dtype=np.uint8)
    for index, frame in enumerate(decoded):
        resized = cv2.resize(frame, (cell_width, cell_height))
        row, column = divmod(index, columns)
        sheet[
            row * cell_height : (row + 1) * cell_height,
            column * cell_width : (column + 1) * cell_width,
        ] = resized
    ok, encoded = cv2.imencode(".jpg", sheet, [cv2.IMWRITE_JPEG_QUALITY, 82])
    return encoded.tobytes() if ok else None

