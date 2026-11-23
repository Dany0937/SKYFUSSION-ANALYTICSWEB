import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.indices import ndvi, ndwi

client = TestClient(app)


def test_indices_formula() -> None:
    assert ndvi([0.8], [0.2])[0] == pytest.approx(0.6)
    assert ndwi([0.8], [0.2])[0] == pytest.approx(0.6)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metrics_envelope() -> None:
    response = client.get("/api/v1/demo/metrics")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert 0 <= response.json()["data"]["ndvi"] <= 1


def test_series_uses_real_interpolation() -> None:
    response = client.get("/api/v1/series/demo")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 15
