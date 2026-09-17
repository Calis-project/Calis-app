from __future__ import annotations

import pytest

from calis_video.geometry import angle_degrees, moving_median


def test_angle_degrees_for_right_angle() -> None:
    assert angle_degrees((1, 0, 0), (0, 0, 0), (0, 1, 0)) == pytest.approx(90)


def test_angle_degrees_returns_none_for_zero_vector() -> None:
    assert angle_degrees((0, 0, 0), (0, 0, 0), (0, 1, 0)) is None


def test_moving_median_ignores_missing_values() -> None:
    assert moving_median([10.0, None, 30.0], window=3) == [10.0, 20.0, 30.0]

