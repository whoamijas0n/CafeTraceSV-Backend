import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationOut

router = APIRouter()


@router.post(
    "",
    response_model=OrganizationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una organización",
    description="Da de alta una nueva organización (tenant/dueño). Debe existir antes de poder registrar cualquier usuario bajo ella. Endpoint público a propósito: es el primer paso, antes de que exista ningún usuario.",
)
async def create_organization(
    org_in: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new organization (tenant). No auth required — this is the entry
    point before any user exists for that organization.
    """
    new_org = Organization(name=org_in.name)

    db.add(new_org)
    await db.flush()
    await db.refresh(new_org)

    return new_org


@router.get(
    "/{organization_id}",
    response_model=OrganizationOut,
    status_code=status.HTTP_200_OK,
    summary="Obtener una organización por ID",
    description="Retorna los datos de una organización específica.",
)
async def get_organization(
    organization_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    stmt = select(Organization).where(Organization.id == organization_id)
    result = await db.execute(stmt)
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organización no encontrada.",
        )

    return org
