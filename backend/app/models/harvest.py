import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Date, DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.coffee_lot import CoffeeLot
    from app.models.plot import Plot


class Harvest(Base):
    """
    Harvest (Cosecha) entity representing a recurring harvest event tied to a Plot.
    """
    __tablename__ = "harvests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    plot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    harvest_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    weight_kg: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    moisture_percentage: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    plot: Mapped["Plot"] = relationship(
        "Plot",
        back_populates="harvests",
    )
    coffee_lots: Mapped[List["CoffeeLot"]] = relationship(
        "CoffeeLot",
        back_populates="harvest",
        cascade="all, delete-orphan",
        order_by="CoffeeLot.created_at",
    )

    def __repr__(self) -> str:
        return f"<Harvest id={self.id} plot_id={self.plot_id} date={self.harvest_date} weight_kg={self.weight_kg}>"
