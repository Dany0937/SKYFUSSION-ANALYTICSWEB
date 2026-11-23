"""Orquestador desacoplado del pipeline hidroclimático para Skyfussion Analytics.

Ejecuta el ciclo de vida secuencial del análisis:
AREA_DEFINED -> DATA_INGESTED -> ANALYSIS_COMPLETED -> PREDICTION_READY -> REPORT_READY
y captura la trazabilidad de eventos en memoria.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from pipeline.event_bus import EventBus, PipelineStage
from skills.geo_parser import parse_geometry, ParsedGeometry
from skills.vision_analyzer import analyze_multitemporal_vision, VisionMetrics
from skills.caudal_predictor import project_caudal_series, CaudalForecast
from skills.reporting_agent import generate_hydrological_report, ReportOutput


@dataclass
class PipelineExecutionOutput:
    metrics: Dict[str, Any]
    forecast: Dict[str, Any]
    report: Dict[str, Any]
    events: List[Dict[str, Any]]
    geometry: Dict[str, Any]


async def run_pipeline(
    area_name: str = "Cuenca del Río Combeima",
    raw_geometry: Any = None,
    years: List[int] = [1969, 2023],
    scenario: str = "normal"
) -> PipelineExecutionOutput:
    """Ejecuta el pipeline completo de análisis espacial, espectral y predictivo."""
    bus = EventBus()

    # -------------------------------------------------------------
    # 1. ESTADO: AREA_DEFINED
    # -------------------------------------------------------------
    parsed_geo: ParsedGeometry = parse_geometry(raw_geometry)
    bus.emit(
        PipelineStage.AREA_DEFINED,
        payload={
            "area_name": area_name,
            "area_ha": parsed_geo.area_ha,
            "centroid": parsed_geo.centroid,
            "bbox": parsed_geo.bbox,
            "geometry_type": parsed_geo.geometry_type,
            "is_default_combeima": parsed_geo.is_default,
        },
        description=f"Área '{area_name}' delimitada y validada ({parsed_geo.area_ha:.2f} ha)."
    )

    # -------------------------------------------------------------
    # 2. ESTADO: DATA_INGESTED
    # -------------------------------------------------------------
    bus.emit(
        PipelineStage.DATA_INGESTED,
        payload={
            "period": {"start_year": min(years), "end_year": max(years)},
            "years_count": max(years) - min(years) + 1,
            "scenario": scenario,
            "sensor_bands": ["B3 (Green)", "B4 (Red)", "B8 (NIR)"],
            "spatial_resolution_meters": 10.0,
        },
        description=f"Datos multitemporales ({min(years)}-{max(years)}) preparados para procesamiento."
    )

    # -------------------------------------------------------------
    # 3. ESTADO: ANALYSIS_COMPLETED
    # -------------------------------------------------------------
    # El análisis morfológico se modula según el área
    intensity = max(0.5, min(parsed_geo.area_ha / 12450.75, 2.0))
    vision_metrics: VisionMetrics = analyze_multitemporal_vision(years=years, river_intensity=intensity)

    metrics_payload = {
        "ndwi_mean": vision_metrics.ndwi_mean,
        "ndvi_mean": vision_metrics.ndvi_mean,
        "channel_width_change_pct": vision_metrics.channel_width_change_pct,
        "initial_mean_width_px": vision_metrics.initial_mean_width_px,
        "final_mean_width_px": vision_metrics.final_mean_width_px,
        "water_coverage_initial_pct": vision_metrics.water_coverage_initial_pct,
        "water_coverage_final_pct": vision_metrics.water_coverage_final_pct,
    }

    bus.emit(
        PipelineStage.ANALYSIS_COMPLETED,
        payload=metrics_payload,
        description=(
            f"Análisis espectral y morfológico completado: "
            f"NDWI={vision_metrics.ndwi_mean}, NDVI={vision_metrics.ndvi_mean}, "
            f"Δ Ancho Cauce={vision_metrics.channel_width_change_pct:+.2f}%."
        )
    )

    # -------------------------------------------------------------
    # 4. ESTADO: PREDICTION_READY
    # -------------------------------------------------------------
    forecast_data: CaudalForecast = project_caudal_series(
        years=years,
        area_ha=parsed_geo.area_ha,
        scenario=scenario,  # type: ignore
    )

    forecast_payload = {
        "dates": forecast_data.dates,
        "caudal_m3s": forecast_data.caudal_m3s,
        "rmse": forecast_data.rmse,
        "r2": forecast_data.r2,
        "metadata": forecast_data.metadata,
    }

    bus.emit(
        PipelineStage.PREDICTION_READY,
        payload={
            "points_count": len(forecast_data.caudal_m3s),
            "rmse": forecast_data.rmse,
            "r2": forecast_data.r2,
            "mean_flow_m3s": forecast_data.metadata.get("mean_caudal_m3s"),
        },
        description=f"Proyección de caudal calculada (R²={forecast_data.r2}, RMSE={forecast_data.rmse})."
    )

    # -------------------------------------------------------------
    # 5. ESTADO: REPORT_READY
    # -------------------------------------------------------------
    report_output: ReportOutput = await generate_hydrological_report(
        metrics=metrics_payload,
        forecast=forecast_payload,
        area_name=area_name,
        scenario=scenario,
    )

    report_payload = report_output.to_dict()

    bus.emit(
        PipelineStage.REPORT_READY,
        payload={
            "alert_level": report_output.alert_level,
            "headline": report_output.headline,
            "provider": report_output.provider,
            "recommendations_count": len(report_output.recommendations),
        },
        description=f"Reporte hidrológico generado (Nivel: {report_output.alert_level}, Proveedor: {report_output.provider})."
    )

    return PipelineExecutionOutput(
        metrics=metrics_payload,
        forecast=forecast_payload,
        report=report_payload,
        events=bus.get_trace(),
        geometry=parsed_geo.geojson,
    )
