from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base
from .tenant import utcnow


class Reading(Base):
    __tablename__ = "readings"
    __table_args__ = (
        UniqueConstraint("shipment_id", "timestamp", name="uq_reading_shipment_timestamp"),
        Index("ix_readings_shipment_time", "shipment_id", "timestamp"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipments.id"), index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    temperatura: Mapped[float | None] = mapped_column(Float)
    humedad: Mapped[float | None] = mapped_column(Float)
    lat: Mapped[float | None] = mapped_column(Float)
    lng: Mapped[float | None] = mapped_column(Float)
    puerta_abierta: Mapped[bool] = mapped_column(Boolean, default=False)
    vibracion: Mapped[bool] = mapped_column(Boolean, default=False)
    tamper: Mapped[bool] = mapped_column(Boolean, default=False)
    bateria: Mapped[float | None] = mapped_column(Float)
    fuente: Mapped[str] = mapped_column(String(10), default="nbm1")  # nbm1 | ble
    hash_actual: Mapped[str] = mapped_column(String(64))
    hash_anterior: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    shipment = relationship("Shipment", back_populates="readings")
