import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.harvest import Harvest


class CoffeeLot(Base):
    """
    CoffeeLot (Lote de café) entity representing a commercial traceable lot,
    generated from one Harvest. Carries the public qr_uuid used for the
    unauthenticated /trace/{qr_uuid} endpoint.
    """
    __tablename__ = "coffee_lots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    harvest_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("harvests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lot_code: Mapped[str] = mapped_column(
        String(60),
        unique=True,
        nullable=False,
        index=True,
        comment="e.g. SV-USU-2026-LOT01",
    )
    qr_uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        default=uuid.uuid4,
        index=True,
        comment="Public identifier encoded in the traceability QR code",
    )
    processing_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Lavado, Honey, Natural",
    )
    cupping_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    export_ready: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    harvest: Mapped["Harvest"] = relationship(
        "Harvest",
        back_populates="coffee_lots",
    )

    def __repr__(self) -> str:
        return f"<CoffeeLot id={self.id} lot_code={self.lot_code} qr_uuid={self.qr_uuid}>"
