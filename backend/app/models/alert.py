from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base
from .tenant import utcnow


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipments.id"), index=True)
    reading_id: Mapped[int | None] = mapped_column(ForeignKey("readings.id"))
    tipo: Mapped[str] = mapped_column(String(30))  # temp_fuera_rango | puerta_abierta | tamper | sin_señal | bateria_baja
    severidad: Mapped[str] = mapped_column(String(10))  # critica | media
    mensaje: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    resuelta: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    resuelto_por: Mapped[str | None] = mapped_column(String(255))
    notificado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    shipment = relationship("Shipment", back_populates="alerts")
    reading = relationship("Reading")
