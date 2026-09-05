from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class OrganizationBase(BaseModel):
    """
    Base organization (tenant) schema.
    """
    name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Organization / owner display name",
        example="Finca El Espino S.A.",
    )


class OrganizationCreate(OrganizationBase):
    """
    Schema for creating a new organization (tenant).
    """
    pass


class OrganizationUpdate(BaseModel):
    """
    Schema for updating an existing organization.
    """
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    is_active: Optional[bool] = None


class OrganizationOut(OrganizationBase):
    """
    Schema for serialized organization output.
    """
    id: UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
