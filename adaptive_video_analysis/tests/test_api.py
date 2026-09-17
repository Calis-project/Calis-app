from __future__ import annotations

from fastapi.testclient import TestClient

from calis_video.api import app


def test_health_endpoint_reports_supported_exercises() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert "push_up" in body["supported_exercises"]
    assert "squat" in body["supported_exercises"]

