from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    success: bool = True
    data: T


class EnvMetrics(BaseModel):
    ndvi: float = Field(ge=-1, le=1)
    ndwi: float = Field(ge=-1, le=1)
    temperature: float
    humidity: float
    precipitation: float
    flow_rate: float
    alert_level: str
    timestamp: datetime


class SeriesPoint(BaseModel):
    label: str
    ndvi: float


class IndexRequest(BaseModel):
    band: list[float] = Field(min_length=1)
    reference: list[float] = Field(min_length=1)


class BandSummary(BaseModel):
    index: str
    mean: float
    min: float
    max: float
    std: float


class PipelineAccepted(BaseModel):
    request_id: str
    status: str
    event: str
