"""Punto de entrada FastAPI de Skyfussion Analytics."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import router as v1_router
from app.core.config import settings

app = FastAPI(
    title="Skyfussion Analytics API",
    description="Backend de monitoreo hidroclimático de la cuenca del río Combeima",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)


@app.get("/health", tags=["sistema"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}
