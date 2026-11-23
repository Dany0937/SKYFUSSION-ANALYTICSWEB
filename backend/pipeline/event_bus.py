"""Bus de eventos en memoria con trazabilidad secuencial de 5 estados para Skyfussion Analytics."""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class PipelineStage(str, Enum):
    AREA_DEFINED = "AREA_DEFINED"
    DATA_INGESTED = "DATA_INGESTED"
    ANALYSIS_COMPLETED = "ANALYSIS_COMPLETED"
    PREDICTION_READY = "PREDICTION_READY"
    REPORT_READY = "REPORT_READY"


class EventEntry(BaseModel):
    stage: PipelineStage
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    payload: Dict[str, Any] = Field(default_factory=dict)
    description: str = ""


class EventBus:
    """Bus de eventos ligero en memoria para trazar el ciclo de vida del pipeline."""

    EXPECTED_SEQUENCE = [
        PipelineStage.AREA_DEFINED,
        PipelineStage.DATA_INGESTED,
        PipelineStage.ANALYSIS_COMPLETED,
        PipelineStage.PREDICTION_READY,
        PipelineStage.REPORT_READY,
    ]

    def __init__(self) -> None:
        self._events: List[EventEntry] = []

    def emit(self, stage: PipelineStage | str, payload: Dict[str, Any] | None = None, description: str = "") -> EventEntry:
        """Registra un evento en la traza en memoria."""
        if isinstance(stage, str):
            stage = PipelineStage(stage)

        entry = EventEntry(
            stage=stage,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            payload=payload or {},
            description=description or f"Etapa {stage.value} completada exitosamente."
        )
        self._events.append(entry)
        return entry

    def get_trace(self) -> List[Dict[str, Any]]:
        """Retorna el log serializable de eventos."""
        return [event.model_dump() for event in self._events]

    def clear(self) -> None:
        """Limpia el log de eventos."""
        self._events.clear()

    @property
    def events(self) -> List[EventEntry]:
        return list(self._events)
