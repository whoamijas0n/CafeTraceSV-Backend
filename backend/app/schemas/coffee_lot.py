from datetime import datetime
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

ProcessingMethod = Literal["Lavado", "Honey", "Natural"]


class CoffeeLotBase(BaseModel):
    """
    Base coffee lot (lote de café) schema.
    """
    lot_code: str = Field(
        ...,
        min_length=3,
        max_length=60,
        description="Unique commercial lot code",
        example="SV-USU-2026-LOT01",
    )
    processing_method: ProcessingMethod = Field(
        ...,
        description="Processing method applied to this lot",
        example="Lavado",
    )
    cupping_score: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Cupping / quality score (SCA scale)",
        example=86.5,
    )


class CoffeeLotCreate(CoffeeLotBase):
    """
    Schema for creating a new commercial coffee lot from an existing harvest.
    """
    harvest_id: UUID = Field(..., description="ID of the harvest this lot is built from")


class CoffeeLotUpdate(BaseModel):
    """
    Schema for updating an existing coffee lot.
    """
    processing_method: Optional[ProcessingMethod] = None
    cupping_score: Optional[float] = Field(None, ge=0, le=100)
    export_ready: Optional[bool] = None


class CoffeeLotOut(CoffeeLotBase):
    """
    Schema for serialized coffee lot output.
    """
    id: UUID
    harvest_id: UUID
    qr_uuid: UUID
    export_ready: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
