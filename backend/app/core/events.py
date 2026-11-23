"""Contrato unificado de eventos.

Conserva alias de las dos familias históricas:
- UPPER_SNAKE (adquisición, `shared/events/`)
- lower:colon (pipeline de agentes, `docs/.../03-agent-protocol.md`)
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .config import settings

ANALYSIS_REQUESTED = "analysis:requested"
DATA_INGESTED = "data:ingested"
ANALYSIS_COMPLETED = "analysis:completed"
PREDICTION_COMPLETED = "prediction:completed"
REPORT_READY = "report:ready"

IMAGENES_HISTORICAS_LISTAS = "IMAGENES_HISTORICAS_LISTAS"
IMAGEN_INDIVIDUAL_PROCESADA = "IMAGEN_INDIVIDUAL_PROCESADA"
GEOSPATIAL_AGENT_ERROR = "GEOSPATIAL_AGENT_ERROR"

EVENT_ALIASES = {
    "ANALYSIS_REQUESTED": ANALYSIS_REQUESTED,
    "DATA_INGESTED": DATA_INGESTED,
    "ANALYSIS_COMPLETED": ANALYSIS_COMPLETED,
    "PREDICTION_COMPLETED": PREDICTION_COMPLETED,
    "REPORT_READY": REPORT_READY,
}

Handler = Callable[[dict[str, Any]], None]


class EventBus:
    """Bus local en memoria con persistencia opcional en `.jsonl`.

    El backend de producción (RabbitMQ/Redis) se conecta en la capa de
    infraestructura; este bus mantiene el contrato y permite desarrollo local.
    """

    def __init__(self, storage_dir: str | None = None) -> None:
        self.storage_dir = Path(storage_dir or settings.event_dir)
        self._handlers: dict[str, list[Handler]] = {}

    def subscribe(self, event_type: str, handler: Handler) -> None:
        canonical = EVENT_ALIASES.get(event_type, event_type)
        self._handlers.setdefault(canonical, []).append(handler)

    def publish(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        canonical = EVENT_ALIASES.get(event_type, event_type)
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": canonical,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "backend-fastapi",
            "version": "1.0",
            "payload": payload,
        }
        if settings.event_backend == "local":
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            with (self.storage_dir / "events.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event, ensure_ascii=False) + "\n")
        for handler in self._handlers.get(canonical, []):
            handler(event)
        return event


event_bus = EventBus()
