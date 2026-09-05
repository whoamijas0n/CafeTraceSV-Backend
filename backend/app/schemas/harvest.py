from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class HarvestBase(BaseModel):
    """
    Base harvest (cosecha) schema.
    """
    harvest_date: date = Field(
        ...,
        description="Date the harvest took place",
        example="2026-11-15",
    )
    weight_kg: float = Field(
        ...,
        gt=0,
        description="Total harvested weight in kilograms",
        example=450.5,
    )
    moisture_percentage: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Moisture percentage of the harvested coffee cherries",
        example=12.5,
    )
    notes: Optional[str] = Field(
        None,
        max_length=2000,
        description="Free-form notes about this harvest",
        example="Corte de temporada, buen estado fitosanitario",
    )


class HarvestCreate(HarvestBase):
    """
    Schema for registering a new harvest on an existing plot.
    """
    plot_id: UUID = Field(..., description="ID of the plot this harvest belongs to")


class HarvestUpdate(BaseModel):
    """
    Schema for updating an existing harvest.
    """
    harvest_date: Optional[date] = None
    weight_kg: Optional[float] = Field(None, gt=0)
    moisture_percentage: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = Field(None, max_length=2000)


class HarvestOut(HarvestBase):
    """
    Schema for serialized harvest output.
    """
    id: UUID
    plot_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
