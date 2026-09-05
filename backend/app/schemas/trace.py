from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.schemas.plot import GeoJSONPolygon


class TraceProducer(BaseModel):
    full_name: str
    department: str
    municipality: str


class TraceFarm(BaseModel):
    name: str
    altitude_masl: Optional[int] = None


class TracePlot(BaseModel):
    name: str
    coffee_variety: str
    area_hectares: float
    geojson: GeoJSONPolygon


class TraceHarvest(BaseModel):
    harvest_date: date
    weight_kg: float
    moisture_percentage: Optional[float] = None


class TraceOut(BaseModel):
    """
    Public traceability record returned by GET /trace/{qr_uuid}.
    No authentication required — this is what the printed QR resolves to.
    """
    lot_code: str
    qr_uuid: UUID
    processing_method: str
    cupping_score: Optional[float] = None
    export_ready: bool
    created_at: datetime

    producer: TraceProducer
    farm: TraceFarm
    plot: TracePlot
    harvest: TraceHarvest

    verification_seal: str = Field(
        ...,
        description="Short deterministic seal derived from the lot's qr_uuid, shown as proof of an authentic CaféTrace SV record",
    )
