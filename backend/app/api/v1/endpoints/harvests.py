import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_db
from app.models.farm import Farm
from app.models.plot import Plot
from app.models.producer import Producer
from app.models.user import User
from app.schemas.harvest import HarvestCreate, HarvestOut, HarvestUpdate

router = APIRouter()


async def _get_plot_with_owner(db: AsyncSession, plot_id: uuid.UUID):
    """
    Helper: fetch a plot together with its owning producer, or raise 404.
    """
    stmt = (
        select(Plot, Producer)
        .join(Farm, Plot.farm_id == Farm.id)
        .join(Producer, Farm.producer_id == Producer.id)
        .where(Plot.id == plot_id)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parcela no encontrada.",
        )
    return row[0], row[1]


def _check_write_permission(producer: Producer, current_user: User) -> None:
    if producer.user_id != current_user.id and current_user.role not in ["ADMIN", "TECNICO"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes autorización para modificar cosechas de esta parcela.",
        )


@router.post(
    "",
    response_model=HarvestOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una cosecha",
    description="Registra una nueva cosecha sobre una parcela ya existente.",
)
async def create_harvest(
    harvest_in: HarvestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new harvest record tied to an existing plot.
    """
    from app.models.harvest import Harvest

    plot, producer = await _get_plot_with_owner(db, harvest_in.plot_id)
    _check_write_permission(producer, current_user)

    new_harvest = Harvest(
        plot_id=harvest_in.plot_id,
        harvest_date=harvest_in.harvest_date,
        weight_kg=harvest_in.weight_kg,
        moisture_percentage=harvest_in.moisture_percentage,
        notes=harvest_in.notes,
    )

    db.add(new_harvest)
    await db.flush()
    await db.refresh(new_harvest)

    return new_harvest


@router.get(
    "/plot/{plot_id}",
    response_model=List[HarvestOut],
    status_code=status.HTTP_200_OK,
    summary="Listar cosechas de una parcela",
    description="Retorna todas las cosechas registradas para una parcela, más recientes primero.",
)
async def list_harvests_by_plot(
    plot_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    from app.models.harvest import Harvest

    stmt = (
        select(Harvest)
        .where(Harvest.plot_id == plot_id)
        .order_by(Harvest.harvest_date.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get(
    "/{harvest_id}",
    response_model=HarvestOut,
    status_code=status.HTTP_200_OK,
    summary="Obtener detalle de una cosecha",
    description="Retorna los datos de una cosecha específica.",
)
async def get_harvest(
    harvest_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    from app.models.harvest import Harvest

    stmt = select(Harvest).where(Harvest.id == harvest_id)
    result = await db.execute(stmt)
    harvest = result.scalar_one_or_none()

    if not harvest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cosecha no encontrada.",
        )

    return harvest


@router.put(
    "/{harvest_id}",
    response_model=HarvestOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar una cosecha",
    description="Actualiza los datos de una cosecha existente.",
)
async def update_harvest(
    harvest_id: uuid.UUID,
    harvest_in: HarvestUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    from app.models.harvest import Harvest

    stmt = select(Harvest).where(Harvest.id == harvest_id)
    result = await db.execute(stmt)
    harvest = result.scalar_one_or_none()

    if not harvest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cosecha no encontrada.",
        )

    _, producer = await _get_plot_with_owner(db, harvest.plot_id)
    _check_write_permission(producer, current_user)

    update_data = harvest_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(harvest, field, value)

    await db.flush()
    await db.refresh(harvest)

    return harvest


@router.delete(
    "/{harvest_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una cosecha",
    description="Elimina una cosecha y los lotes de café que dependan únicamente de ella.",
)
async def delete_harvest(
    harvest_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    from app.models.harvest import Harvest

    stmt = select(Harvest).where(Harvest.id == harvest_id)
    result = await db.execute(stmt)
    harvest = result.scalar_one_or_none()

    if not harvest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cosecha no encontrada.",
        )

    _, producer = await _get_plot_with_owner(db, harvest.plot_id)
    _check_write_permission(producer, current_user)

    await db.delete(harvest)
    await db.flush()
