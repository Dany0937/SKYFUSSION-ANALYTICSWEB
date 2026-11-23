"""Agente generador de reportes hidrológicos con Gemini y Fallback Local para Skyfussion Analytics.

Conecta con `google-genai` (modelo `gemini-2.5-flash`) mediante `GEMINI_API_KEY`.
Devuelve JSON estructurado estricto con:
- `alert_level`: "NORMAL" | "PREVENTIVA" | "CRITICA"
- `headline`: Resumen de impacto en una línea
- `narrative`: Análisis técnico-ambiental detallado
- `recommendations`: Lista de acciones prioritarias para comités de riesgo y gestión hídrica

Si `DEMO_MODE=true` o no existe API key, ejecuta un fallback local determinista y coherente.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional


AlertLevel = Literal["NORMAL", "PREVENTIVA", "CRITICA"]


@dataclass
class ReportOutput:
    alert_level: AlertLevel
    headline: str
    narrative: str
    recommendations: List[str]
    provider: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_level": self.alert_level,
            "headline": self.headline,
            "narrative": self.narrative,
            "recommendations": self.recommendations,
            "provider": self.provider,
        }


def _determine_local_alert_level(
    channel_width_change_pct: float,
    ndwi_mean: float,
    ndvi_mean: float,
    caudal_mean: float
) -> AlertLevel:
    """Evalúa umbrales de alerta hidrológica y morfológica según el marco de negocio."""
    # Reducción severa de ancho o estiaje crítico
    if channel_width_change_pct <= -15.0 or caudal_mean < 25.0:
        return "CRITICA"
    # Cambios moderados o erosión/reducción sensible
    if channel_width_change_pct <= -5.0 or channel_width_change_pct >= 12.0 or ndwi_mean < 0.0:
        return "PREVENTIVA"
    return "NORMAL"


def generate_local_fallback_report(
    metrics: Dict[str, Any],
    forecast: Dict[str, Any],
    area_name: str = "Cuenca del Río Combeima"
) -> ReportOutput:
    """Genera reporte local coherente sin depender de servicios externos."""
    width_change = metrics.get("channel_width_change_pct", -8.4)
    ndwi = metrics.get("ndwi_mean", 0.12)
    ndvi = metrics.get("ndvi_mean", 0.58)
    caudal_mean = forecast.get("metadata", {}).get("mean_caudal_m3s", 41.2)
    scenario = forecast.get("metadata", {}).get("scenario", "normal")

    alert_level = _determine_local_alert_level(width_change, ndwi, ndvi, caudal_mean)

    if alert_level == "CRITICA":
        headline = f"Alerta Crítica: Reducción severa en el cauce del {area_name} ({width_change:+.1f}%)"
        narrative = (
            f"El monitoreo hidroclimático y espectral sobre la zona '{area_name}' revela anomalías "
            f"hidrológicas severas. Se detecta una variación del {width_change:+.1f}% en el ancho efectivo "
            f"del cauce fluvial, con un caudal medio proyectado de {caudal_mean:.1f} m³/s bajo el escenario '{scenario}'. "
            f"El índice NDWI ({ndwi:.3f}) y NDVI ({ndvi:.3f}) evidencian una marcada presión por estrés hídrico "
            f"o degradación en la zona ribereña, requiriendo acción inmediata."
        )
        recommendations = [
            "Convocar de manera extraordinaria al Comité Municipal de Gestión del Riesgo de Desastres.",
            "Monitorear puntos de captación de acueducto aguas abajo (Ibagué) ante posible desabastecimiento.",
            "Desplegar inspección con drones y brigadas en terreno para descartar represamientos en la cuenca alta.",
            "Activar planes de contingencia para el uso regulado y prioritario de agua potable."
        ]
    elif alert_level == "PREVENTIVA":
        headline = f"Alerta Preventiva: Variación morfológica moderada detectada en {area_name} ({width_change:+.1f}%)"
        narrative = (
            f"El análisis de variabilidad multitemporal (1969–2023) en '{area_name}' muestra una alteración "
            f"del {width_change:+.1f}% en el ancho del cauce, con un índice NDWI promedio de {ndwi:.3f} y NDVI de {ndvi:.3f}. "
            f"Las proyecciones recurrentes indican un régimen de caudal medio de {caudal_mean:.1f} m³/s en escenario '{scenario}'. "
            f"Se identifican zonas con procesos de incisión y migración lateral que ameritan vigilancia continua."
        )
        recommendations = [
            "Intensificar la frecuencia de lectura de las estaciones hidrométricas de la cuenca.",
            "Verificar la estabilidad de taludes y defensas ribereñas en sectores con mayor erosión.",
            "Coordinar con la autoridad ambiental (CORTOLIMA) la revisión de licencias y extracciones de material.",
            "Mantener activo el sistema de alerta temprana ante variaciones en precipitaciones andinas."
        ]
    else:
        headline = f"Estado Normal: Estabilidad hidroclimática y cobertura en {area_name}"
        narrative = (
            f"La cuenca analizada '{area_name}' presenta estabilidad morfológica e hídrica en el periodo evaluado. "
            f"La variación del ancho de cauce ({width_change:+.1f}%) se encuentra dentro del rango de tolerancia natural. "
            f"El índice de vegetación NDVI ({ndvi:.3f}) refleja adecuada salud en las coberturas de bosque y pastizal, "
            f"mientras que el caudal proyectado ({caudal_mean:.1f} m³/s) mantiene el aporte hídrico regular."
        )
        recommendations = [
            "Continuar el monitoreo periódico satelital y de telemetría en estaciones fijas.",
            "Fomentar los programas de reforestación y conservación de ronda hídrica.",
            "Actualizar los modelos de pronóstico hidrológico con nuevas escenas satelitales."
        ]

    return ReportOutput(
        alert_level=alert_level,
        headline=headline,
        narrative=narrative,
        recommendations=recommendations,
        provider="local_fallback",
    )


async def generate_hydrological_report(
    metrics: Dict[str, Any],
    forecast: Dict[str, Any],
    area_name: str = "Cuenca del Río Combeima",
    scenario: str = "normal"
) -> ReportOutput:
    """Genera el reporte hidrológico mediante Gemini 2.5 Flash o Fallback Local."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    demo_mode = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")

    if demo_mode or not api_key:
        return generate_local_fallback_report(metrics, forecast, area_name)

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Prompt técnico con restricciones de JSON estricto
    prompt = f"""Eres un experto hidrólogo y analista de teledetección ambiental del sistema Skyfussion Analytics.
Analiza los siguientes resultados técnicos de la cuenca '{area_name}':
- Variación del ancho del cauce: {metrics.get('channel_width_change_pct', 0.0)}%
- Índice de Agua NDWI medio: {metrics.get('ndwi_mean', 0.0)}
- Índice de Vegetación NDVI medio: {metrics.get('ndvi_mean', 0.0)}
- Caudal medio proyectado: {forecast.get('metadata', {}).get('mean_caudal_m3s', 40.0)} m³/s
- Escenario climático evaluado: {scenario}
- Periodo analizado: 1969 - 2023

Debes responder ÚNICAMENTE con un objeto JSON válido con la siguiente estructura exacta:
{{
  "alert_level": "NORMAL" | "PREVENTIVA" | "CRITICA",
  "headline": "<Frase concisa de impacto en español, max 100 caracteres>",
  "narrative": "<Párrafo técnico explicativo en español, entre 60 y 140 palabras>",
  "recommendations": [
    "<Acción técnica o de gestión del riesgo 1>",
    "<Acción técnica o de gestión del riesgo 2>",
    "<Acción técnica o de gestión del riesgo 3>"
  ]
}}
"""

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            )
        )

        response_text = response.text or ""
        # Limpieza de posibles delimitadores markdown
        cleaned_text = re.sub(r"```(?:json)?", "", response_text).strip()
        data = json.loads(cleaned_text)

        alert_lvl: AlertLevel = data.get("alert_level", "NORMAL")
        if alert_lvl not in ("NORMAL", "PREVENTIVA", "CRITICA"):
            alert_lvl = "PREVENTIVA"

        return ReportOutput(
            alert_level=alert_lvl,
            headline=data.get("headline", f"Reporte de Monitoreo - {area_name}"),
            narrative=data.get("narrative", ""),
            recommendations=data.get("recommendations", []),
            provider=f"google-genai:{model_name}",
        )

    except Exception as e:
        # En caso de cualquier falla de conexión/cuota/parsing con Gemini, fallback local seguro
        fallback = generate_local_fallback_report(metrics, forecast, area_name)
        fallback.provider = f"local_fallback (gemini_error: {type(e).__name__})"
        return fallback
