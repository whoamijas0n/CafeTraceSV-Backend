import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_db
from app.models.coffee_lot import CoffeeLot
from app.models.farm import Farm
from app.models.harvest import Harvest
from app.models.plot import Plot
from app.models.producer import Producer
from app.models.user import User
from app.schemas.coffee_lot import CoffeeLotCreate, CoffeeLotOut, CoffeeLotUpdate

router = APIRouter()


async def _get_harvest_with_owner(db: AsyncSession, harvest_id: uuid.UUID):
    stmt = (
        select(Harvest, Producer)
        .join(Plot, Harvest.plot_id == Plot.id)
        .join(Farm, Plot.farm_id == Farm.id)
        .join(Producer, Farm.producer_id == Producer.id)
        .where(Harvest.id == harvest_id)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cosecha no encontrada.",
        )
    return row[0], row[1]


def _check_write_permission(producer: Producer, current_user: User) -> None:
    if producer.user_id != current_user.id and current_user.role not in ["ADMIN", "TECNICO"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes autorización para gestionar lotes de esta cosecha.",
        )


@router.post(
    "",
    response_model=CoffeeLotOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un lote de café",
    description="Arma un lote comercial trazable a partir de una cosecha existente. Genera automáticamente el qr_uuid público.",
)
async def create_coffee_lot(
    lot_in: CoffeeLotCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new commercial coffee lot from a harvest.
    """
    _, producer = await _get_harvest_with_owner(db, lot_in.harvest_id)
    _check_write_permission(producer, current_user)

    stmt = select(CoffeeLot).where(CoffeeLot.lot_code == lot_in.lot_code)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un lote registrado con este código.",
        )

    new_lot = CoffeeLot(
        harvest_id=lot_in.harvest_id,
        lot_code=lot_in.lot_code,
        processing_method=lot_in.processing_method,
        cupping_score=lot_in.cupping_score,
    )

    db.add(new_lot)
    await db.flush()
    await db.refresh(new_lot)

    return new_lot


@router.get(
    "/harvest/{harvest_id}",
    response_model=List[CoffeeLotOut],
    status_code=status.HTTP_200_OK,
    summary="Listar lotes de una cosecha",
    description="Retorna todos los lotes comerciales generados a partir de una cosecha.",
)
async def list_lots_by_harvest(
    harvest_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    stmt = select(CoffeeLot).where(CoffeeLot.harvest_id == harvest_id).order_by(CoffeeLot.created_at)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get(
    "/{lot_id}",
    response_model=CoffeeLotOut,
    status_code=status.HTTP_200_OK,
    summary="Obtener detalle de un lote (autenticado)",
    description="Retorna los datos internos de un lote por su ID interno (no confundir con el endpoint público /trace/{qr_uuid}).",
)
async def get_coffee_lot(
    lot_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    stmt = select(CoffeeLot).where(CoffeeLot.id == lot_id)
    result = await db.execute(stmt)
    lot = result.scalar_one_or_none()

    if not lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lote no encontrado.",
        )

    return lot


@router.put(
    "/{lot_id}",
    response_model=CoffeeLotOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar un lote de café",
    description="Actualiza el método de procesamiento, puntaje de catación o estado de exportación de un lote.",
)
async def update_coffee_lot(
    lot_id: uuid.UUID,
    lot_in: CoffeeLotUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    stmt = select(CoffeeLot).where(CoffeeLot.id == lot_id)
    result = await db.execute(stmt)
    lot = result.scalar_one_or_none()

    if not lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lote no encontrado.",
        )

    _, producer = await _get_harvest_with_owner(db, lot.harvest_id)
    _check_write_permission(producer, current_user)

    update_data = lot_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lot, field, value)

    await db.flush()
    await db.refresh(lot)

    return lot
