from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np


Point3 = Sequence[float]


def angle_degrees(a: Point3, vertex: Point3, c: Point3) -> float | None:
    """Return the smaller 3-D angle at ``vertex`` in degrees."""
    av = np.asarray(a, dtype=float) - np.asarray(vertex, dtype=float)
    cv = np.asarray(c, dtype=float) - np.asarray(vertex, dtype=float)
    denominator = float(np.linalg.norm(av) * np.linalg.norm(cv))
    if denominator <= 1e-9:
        return None
    cosine = float(np.clip(np.dot(av, cv) / denominator, -1.0, 1.0))
    return float(math.degrees(math.acos(cosine)))


def line_angle_from_vertical(a: Point3, b: Point3) -> float | None:
    """Absolute 2-D deviation of segment a->b from vertical."""
    dx = float(b[0] - a[0])
    dy = float(b[1] - a[1])
    length = math.hypot(dx, dy)
    if length <= 1e-9:
        return None
    return abs(math.degrees(math.atan2(dx, dy)))


def robust_median(values: Sequence[float | None]) -> float | None:
    usable = [float(value) for value in values if value is not None]
    return float(np.median(usable)) if usable else None


def moving_median(values: Sequence[float | None], window: int = 3) -> list[float | None]:
    if window < 1 or window % 2 == 0:
        raise ValueError("window must be a positive odd number")
    radius = window // 2
    result: list[float | None] = []
    for index in range(len(values)):
        start = max(0, index - radius)
        end = min(len(values), index + radius + 1)
        result.append(robust_median(values[start:end]))
    return result

