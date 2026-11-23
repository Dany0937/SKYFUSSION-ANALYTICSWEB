# Backend — Skyfussion Analytics

Python + FastAPI + OpenCV + inferencia + Gemini API (con fallback OpenAI/Ollama). Despliegue objetivo: **Render** (`render.yaml`).

## Ejecución local

```bash
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Pruebas: `pytest -q tests/test_smoke.py`

## Estructura

| Ruta | Contenido |
|---|---|
| `app/` | API FastAPI, contratos Pydantic, bus de eventos y proveedor LLM |
| `agents/` | Agentes Python (geoespacial, visión, oracle, reporting) |
| `skills/` | Módulos reutilizables (`geo_tools`, `vision_tools`, `ml_tools`) |
| `rnn_combeima/` | Experimentos RNN y reportes (`reports/resumen_final.csv`) |
| `reports/`, `data/`, `notebooks/`, `scripts/`, `tests/` | Artefactos CRISP-DM y reproducibilidad |
| `shared/` | Esquemas y consumidor de eventos (`EVENT_ALIASES` en `app/core/events.py`) |
| `archive/` | Sesiones 7-9 (evidencia histórica, no código activo) |
| `legacy/backend-node/` | API Node/Express anterior, conservada sin borrar |
| `docs/` | Planes y arquitectura originales (movidos desde la raíz) |

## Convención de métricas

Ninguna respuesta de la API debe presentar `0.66` como R². Ver `../PROJECT_SPEC.md` §0 y §7.
