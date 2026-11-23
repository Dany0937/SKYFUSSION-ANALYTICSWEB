"""Servicio Principal FastAPI de Skyfussion Analytics.

Backend hidroclimático y de teledetección multitemporal (1969-2023).
Desplegable en Render con Python 3.11, arquitectura orientada a eventos y soporte para Gemini.
"""

from __future__ import annotations

import datetime
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

# Asegurar que el directorio raíz de backend esté en sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv()

from pipeline.runner import run_pipeline

app = FastAPI(
    title="Skyfussion Analytics API",
    description="Backend de monitoreo hidroclimático y teledetección multitemporal de la cuenca del Río Combeima",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuración de CORS dinámica
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*").strip()
if allowed_origins_env == "*" or not allowed_origins_env:
    origins = ["*"]
else:
    origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------------
# Schemas de Validación Pydantic
# -------------------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    area_name: str = Field(
        default="Río Combeima",
        min_length=1,
        max_length=120,
        description="Nombre descriptivo de la cuenca o área de estudio"
    )
    geometry: Optional[Any] = Field(
        default=None,
        description="Geometría opcional (GeoJSON Polygon/MultiPolygon, lista de coordenadas o KML). Si es None, usa Río Combeima."
    )
    years: List[int] = Field(
        default=[1969, 2023],
        description="Rango de años para análisis multitemporal [inicio, fin] entre 1969 y 2023"
    )
    scenario: Literal["normal", "seco", "humedo", "cambio_climatico"] = Field(
        default="normal",
        description="Escenario hidroclimático para la proyección de caudal"
    )

    @field_validator("years")
    @classmethod
    def validate_years_range(cls, v: List[int]) -> List[int]:
        if len(v) != 2:
            raise ValueError("years debe contener exactamente dos años: [año_inicio, año_fin]")
        if v[0] >= v[1]:
            raise ValueError("El año inicial debe ser estrictamente menor al año final")
        if v[0] < 1969 or v[1] > 2023:
            raise ValueError("El rango de años permitido está restringido entre 1969 y 2023")
        return v


class ApiResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]


# -------------------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------------------
@app.get("/health", tags=["Monitoreo"])
def health_check() -> Dict[str, Any]:
    """Endpoint de comprobación de salud para Render y orquestadores."""
    return {
        "status": "ok",
        "service": "skyfussion-analytics-backend",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "environment": {
            "demo_mode": os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes"),
            "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            "has_gemini_key": bool(os.getenv("GEMINI_API_KEY", "").strip()),
        }
    }


@app.get("/api/v1/combeima/default", response_model=ApiResponse, tags=["Hidrología"])
async def get_combeima_default() -> ApiResponse:
    """Carga instantánea del estudio hidroclimático base (1969–2023) para la Cuenca del Río Combeima."""
    try:
        output = await run_pipeline(
            area_name="Río Combeima (Cuenca Alta)",
            raw_geometry=None,
            years=[1969, 2023],
            scenario="normal",
        )
        return ApiResponse(
            success=True,
            data={
                "area_name": "Río Combeima (Cuenca Alta)",
                "metrics": output.metrics,
                "forecast": output.forecast,
                "report": output.report,
                "events": output.events,
                "geometry": output.geometry,
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ejecutando análisis base de Combeima: {str(e)}"
        )


@app.post("/api/v1/analyze", response_model=ApiResponse, tags=["Hidrología"])
async def analyze_area(request: AnalyzeRequest) -> ApiResponse:
    """Ejecuta el pipeline completo de análisis espectral, morfológico y de proyección."""
    try:
        output = await run_pipeline(
            area_name=request.area_name,
            raw_geometry=request.geometry,
            years=request.years,
            scenario=request.scenario,
        )
        return ApiResponse(
            success=True,
            data={
                "area_name": request.area_name,
                "metrics": output.metrics,
                "forecast": output.forecast,
                "report": output.report,
                "events": output.events,
                "geometry": output.geometry,
            }
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el procesamiento del pipeline: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
