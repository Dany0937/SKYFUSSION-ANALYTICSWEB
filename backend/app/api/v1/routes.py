"""Rutas v1.

Los valores de `/demo/metrics` son de demostración; las series de
`/series/demo` se leen del artefacto real de interpolación CRISP-DM.
"""

from __future__ import annotations

import csv
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from fastapi import APIRouter, HTTPException

from app.core.events import ANALYSIS_REQUESTED, event_bus
from app.core.llm import llm_provider
from app.schemas.metrics import (
    BandSummary,
    EnvMetrics,
    Envelope,
    IndexRequest,
    PipelineAccepted,
    SeriesPoint,
)
from app.services.indices import ndvi as calc_ndvi
from app.services.indices import ndwi as calc_ndwi
from app.services.indices import summarize

router = APIRouter(prefix="/api/v1")

PIPELINES: dict[str, str] = {}

INTERPOLATION_CSV = (
    Path(__file__).resolve().parents[3]
    / "reports"
    / "crisp_dm"
    / "tabla_interpolacion_15_puntos.csv"
)


@router.get("/demo/metrics", response_model=Envelope[EnvMetrics])
def demo_metrics() -> Envelope[EnvMetrics]:
    data = EnvMetrics(
        ndvi=0.75,
        ndwi=0.32,
        temperature=24.5,
        humidity=68.0,
        precipitation=12.4,
        flow_rate=45.2,
        alert_level="normal",
        timestamp=datetime.now(timezone.utc),
    )
    return Envelope(data=data)


@router.get("/series/demo", response_model=Envelope[list[SeriesPoint]])
def demo_series() -> Envelope[list[SeriesPoint]]:
    points: list[SeriesPoint] = []
    if INTERPOLATION_CSV.exists():
        with INTERPOLATION_CSV.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                value = row.get("Interp_PCHIP") or row.get("Interp_Lineal")
                if value:
                    points.append(SeriesPoint(label=row["fecha"], ndvi=float(value)))
    if not points:
        points = [SeriesPoint(label=f"M{i}", ndvi=0.75 + 0.00087 * i) for i in range(15)]
    return Envelope(data=points)


def _index_summary(index: str, body: IndexRequest) -> BandSummary:
    if len(body.band) != len(body.reference):
        raise HTTPException(status_code=400, detail="Las bandas deben tener la misma longitud")
    result = (
        calc_ndvi(body.band, body.reference)
        if index == "NDVI"
        else calc_ndwi(body.band, body.reference)
    )
    return BandSummary(index=index, **summarize(np.asarray(result)))


@router.post("/analysis/ndvi", response_model=Envelope[BandSummary])
def analysis_ndvi(body: IndexRequest) -> Envelope[BandSummary]:
    """`band` = NIR (B8); `reference` = rojo (B4)."""
    return Envelope(data=_index_summary("NDVI", body))


@router.post("/analysis/ndwi", response_model=Envelope[BandSummary])
def analysis_ndwi(body: IndexRequest) -> Envelope[BandSummary]:
    """`band` = verde (B3); `reference` = NIR (B8)."""
    return Envelope(data=_index_summary("NDWI", body))


@router.post("/pipeline/analyze", response_model=Envelope[PipelineAccepted], status_code=202)
def start_pipeline() -> Envelope[PipelineAccepted]:
    request_id = f"pipeline_{uuid.uuid4().hex[:12]}"
    event = event_bus.publish(ANALYSIS_REQUESTED, {"requestId": request_id})
    PIPELINES[request_id] = "accepted"
    return Envelope(data=PipelineAccepted(request_id=request_id, status="accepted", event=event["event_type"]))


@router.get("/pipeline/{request_id}/status", response_model=Envelope[dict[str, str]])
def pipeline_status(request_id: str) -> Envelope[dict[str, str]]:
    status = PIPELINES.get(request_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Solicitud desconocida")
    return Envelope(data={"request_id": request_id, "status": status})


@router.post("/reports/generate", response_model=Envelope[dict[str, str]])
def generate_report() -> Envelope[dict[str, str]]:
    narrative = llm_provider.generate(
        "Genera una ficha técnica breve sobre el estado hídrico del río Combeima."
    )
    event = event_bus.publish("report:ready", {"provider": llm_provider.provider})
    return Envelope(data={"narrative": narrative, "provider": llm_provider.provider, "event": event["event_type"]})
