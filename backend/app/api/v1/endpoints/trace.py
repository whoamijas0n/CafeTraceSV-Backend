import hashlib
import json
import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.models.coffee_lot import CoffeeLot
from app.models.farm import Farm
from app.models.harvest import Harvest
from app.models.plot import Plot
from app.models.producer import Producer
from app.models.user import User
from app.schemas.plot import GeoJSONPolygon
from app.schemas.trace import TraceFarm, TraceHarvest, TraceOut, TracePlot, TraceProducer

router = APIRouter()


def _make_verification_seal(qr_uuid: uuid.UUID) -> str:
    """
    Deterministic short seal derived from the qr_uuid, shown to reassure the
    person scanning the code that this record is genuinely served by
    CaféTrace SV (not a full cryptographic signature — just a display seal).
    """
    digest = hashlib.sha256(str(qr_uuid).encode("utf-8")).hexdigest()
    return f"CTSV-{digest[:12].upper()}"


@router.get(
    "/{qr_uuid}",
    response_model=TraceOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar expediente de trazabilidad (público, sin autenticación)",
    description="Endpoint público consultado al escanear el código QR impreso en el empaque. No requiere token de autenticación.",
)
async def get_trace_by_qr(
    qr_uuid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Public traceability lookup by qr_uuid. No auth required.
    """
    stmt = (
        select(
            CoffeeLot,
            Harvest,
            Plot,
            Farm,
            Producer,
            User,
            func.ST_AsGeoJSON(Plot.geometry).label("plot_geojson"),
        )
        .join(Harvest, CoffeeLot.harvest_id == Harvest.id)
        .join(Plot, Harvest.plot_id == Plot.id)
        .join(Farm, Plot.farm_id == Farm.id)
        .join(Producer, Farm.producer_id == Producer.id)
        .join(User, Producer.user_id == User.id)
        .where(CoffeeLot.qr_uuid == qr_uuid)
    )
    result = await db.execute(stmt)
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró ningún expediente de trazabilidad para este código QR.",
        )

    lot, harvest, plot, farm, producer, user, plot_geojson_raw = row
    geojson_data = json.loads(plot_geojson_raw) if isinstance(plot_geojson_raw, str) else plot_geojson_raw

    return TraceOut(
        lot_code=lot.lot_code,
        qr_uuid=lot.qr_uuid,
        processing_method=lot.processing_method,
        cupping_score=float(lot.cupping_score) if lot.cupping_score is not None else None,
        export_ready=lot.export_ready,
        created_at=lot.created_at,
        producer=TraceProducer(
            full_name=user.full_name,
            department=producer.department,
            municipality=producer.municipality,
        ),
        farm=TraceFarm(
            name=farm.name,
            altitude_masl=farm.altitude_masl,
        ),
        plot=TracePlot(
            name=plot.name,
            coffee_variety=plot.coffee_variety,
            area_hectares=float(plot.area_hectares),
            geojson=GeoJSONPolygon.model_validate(geojson_data),
        ),
        harvest=TraceHarvest(
            harvest_date=harvest.harvest_date,
            weight_kg=float(harvest.weight_kg),
            moisture_percentage=float(harvest.moisture_percentage) if harvest.moisture_percentage is not None else None,
        ),
        verification_seal=_make_verification_seal(lot.qr_uuid),
    )
