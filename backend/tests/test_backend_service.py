"""Suite de pruebas automatizadas para el backend completo de Skyfussion Analytics."""

import sys
from pathlib import Path

# Agregar carpeta backend a sys.path
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from fastapi.testclient import TestClient

from main import app
from pipeline.event_bus import EventBus, PipelineStage
from pipeline.runner import run_pipeline
from skills.geo_parser import parse_geometry, DEFAULT_COMBEIMA_COORDINATES
from skills.vision_analyzer import (
    calculate_ndvi,
    calculate_ndwi,
    analyze_multitemporal_vision,
)
from skills.caudal_predictor import project_caudal_series
from skills.reporting_agent import (
    generate_local_fallback_report,
    generate_hydrological_report,
)


@pytest.fixture
def client():
    return TestClient(app)


# -------------------------------------------------------------------------
# 1. Pruebas de EventBus y Trazabilidad
# -------------------------------------------------------------------------
def test_event_bus_sequential_trace():
    bus = EventBus()
    for stage in bus.EXPECTED_SEQUENCE:
        bus.emit(stage, payload={"stage_name": stage.value})

    trace = bus.get_trace()
    assert len(trace) == 5
    expected_names = [s.value for s in bus.EXPECTED_SEQUENCE]
    actual_names = [t["stage"] for t in trace]
    assert actual_names == expected_names


# -------------------------------------------------------------------------
# 2. Pruebas de geo_parser
# -------------------------------------------------------------------------
def test_geo_parser_default_basin():
    parsed = parse_geometry(None)
    assert parsed.is_default is True
    assert parsed.area_ha > 10000
    assert parsed.geometry_type == "Polygon"
    assert parsed.geojson["type"] == "Polygon"


def test_geo_parser_custom_polygon():
    custom_coords = [
        [-75.25, 4.40],
        [-75.20, 4.40],
        [-75.20, 4.45],
        [-75.25, 4.45],
        [-75.25, 4.40],
    ]
    parsed = parse_geometry(custom_coords)
    assert parsed.is_default is False
    assert parsed.area_ha > 0
    assert len(parsed.bbox) == 4


def test_geo_parser_point_buffer():
    point_coord = [-75.23, 4.42]
    parsed = parse_geometry(point_coord)
    assert parsed.is_default is False
    assert parsed.area_ha > 0
    assert parsed.geometry_type == "Polygon"


# -------------------------------------------------------------------------
# 3. Pruebas de vision_analyzer
# -------------------------------------------------------------------------
def test_spectral_indices_calculation():
    import numpy as np
    green = np.array([[0.5, 0.6], [0.4, 0.5]])
    nir = np.array([[0.1, 0.2], [0.7, 0.8]])
    red = np.array([[0.2, 0.3], [0.1, 0.1]])

    ndwi = calculate_ndwi(green, nir)
    assert np.all(ndwi >= -1.0) and np.all(ndwi <= 1.0)
    # En pixel (0,0): green=0.5, nir=0.1 -> NDWI > 0 (agua)
    assert ndwi[0, 0] > 0

    ndvi = calculate_ndvi(red, nir)
    assert np.all(ndvi >= -1.0) and np.all(ndvi <= 1.0)
    # En pixel (1,0): red=0.1, nir=0.7 -> NDVI > 0 (vegetación)
    assert ndvi[1, 0] > 0


def test_vision_multitemporal_analysis():
    metrics = analyze_multitemporal_vision(years=[1969, 2023])
    assert -1.0 <= metrics.ndwi_mean <= 1.0
    assert -1.0 <= metrics.ndvi_mean <= 1.0
    assert isinstance(metrics.channel_width_change_pct, float)
    assert metrics.initial_mean_width_px > 0
    assert metrics.final_mean_width_px > 0


# -------------------------------------------------------------------------
# 4. Pruebas de caudal_predictor
# -------------------------------------------------------------------------
def test_caudal_predictor_metrics_and_series():
    forecast = project_caudal_series(years=[1969, 2023], area_ha=12450.75, scenario="normal")
    assert forecast.r2 == 0.66
    assert forecast.rmse == 0.07
    assert len(forecast.dates) == len(forecast.caudal_m3s)
    assert len(forecast.dates) > 0
    assert all(q >= 0 for q in forecast.caudal_m3s)


def test_caudal_predictor_scenarios():
    f_normal = project_caudal_series(years=[2000, 2020], area_ha=10000, scenario="normal")
    f_seco = project_caudal_series(years=[2000, 2020], area_ha=10000, scenario="seco")
    f_humedo = project_caudal_series(years=[2000, 2020], area_ha=10000, scenario="humedo")

    mean_normal = f_normal.metadata["mean_caudal_m3s"]
    mean_seco = f_seco.metadata["mean_caudal_m3s"]
    mean_humedo = f_humedo.metadata["mean_caudal_m3s"]

    assert mean_seco < mean_normal < mean_humedo


# -------------------------------------------------------------------------
# 5. Pruebas de reporting_agent
# -------------------------------------------------------------------------
def test_reporting_agent_local_fallback():
    metrics = {"ndwi_mean": 0.12, "ndvi_mean": 0.58, "channel_width_change_pct": -8.4}
    forecast = {"metadata": {"mean_caudal_m3s": 38.5, "scenario": "normal"}}
    report = generate_local_fallback_report(metrics, forecast, "Río Combeima")

    assert report.alert_level in ("NORMAL", "PREVENTIVA", "CRITICA")
    assert len(report.headline) > 0
    assert len(report.narrative) > 0
    assert len(report.recommendations) >= 3


@pytest.mark.asyncio
async def test_reporting_agent_async_fallback_without_key():
    import os
    os.environ["DEMO_MODE"] = "true"
    metrics = {"ndwi_mean": 0.05, "ndvi_mean": 0.40, "channel_width_change_pct": -16.0}
    forecast = {"metadata": {"mean_caudal_m3s": 22.0, "scenario": "seco"}}
    report = await generate_hydrological_report(metrics, forecast, "Combeima")

    assert report.alert_level == "CRITICA"
    assert report.provider == "local_fallback"


# -------------------------------------------------------------------------
# 6. Pruebas de Endpoints FastAPI
# -------------------------------------------------------------------------
def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "skyfussion-analytics-backend"
    assert "environment" in data


def test_combeima_default_endpoint(client):
    response = client.get("/api/v1/combeima/default")
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    data = res["data"]

    # Validar presencia de todas las secciones
    assert "metrics" in data
    assert "forecast" in data
    assert "report" in data
    assert "events" in data
    assert "geometry" in data

    # Validar métricas requeridas
    assert "ndwi_mean" in data["metrics"]
    assert "ndvi_mean" in data["metrics"]
    assert "channel_width_change_pct" in data["metrics"]

    # Validar validación R² y RMSE
    assert data["forecast"]["r2"] == 0.66
    assert data["forecast"]["rmse"] == 0.07

    # Validar 5 etapas de eventos en orden
    events = data["events"]
    assert len(events) == 5
    stages = [e["stage"] for e in events]
    assert stages == [
        "AREA_DEFINED",
        "DATA_INGESTED",
        "ANALYSIS_COMPLETED",
        "PREDICTION_READY",
        "REPORT_READY",
    ]


def test_analyze_endpoint_valid_custom(client):
    payload = {
        "area_name": "Cuenca Test",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [[-75.30, 4.40], [-75.25, 4.40], [-75.25, 4.45], [-75.30, 4.45], [-75.30, 4.40]]
            ]
        },
        "years": [1980, 2015],
        "scenario": "humedo"
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    assert res["data"]["area_name"] == "Cuenca Test"
    assert len(res["data"]["events"]) == 5


def test_analyze_endpoint_invalid_years(client):
    # Año inicio >= año fin
    payload = {
        "area_name": "Error Test",
        "years": [2020, 1990],
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 422

    # Años fuera del rango 1969-2023
    payload2 = {
        "area_name": "Error Test",
        "years": [1950, 2025],
    }
    response2 = client.post("/api/v1/analyze", json=payload2)
    assert response2.status_code == 422
