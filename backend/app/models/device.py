from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base
from .tenant import utcnow


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    imei: Mapped[str] = mapped_column(String(32), unique=True)
    alias: Mapped[str | None] = mapped_column(String(200))
    api_key: Mapped[str] = mapped_column(String(64), unique=True)
    estado: Mapped[str] = mapped_column(String(20), default="activo")  # activo | almacenado | mantenimiento
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    tenant = relationship("Tenant", back_populates="devices")
    shipments = relationship("Shipment", back_populates="device")
