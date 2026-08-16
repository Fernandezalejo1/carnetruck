from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base
from .tenant import utcnow


class Shipment(Base):
    __tablename__ = "shipments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "numero_contenedor", name="uq_shipment_container_per_tenant"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    numero_contenedor: Mapped[str] = mapped_column(String(50))
    destino_pais: Mapped[str] = mapped_column(String(100))
    mercado: Mapped[str] = mapped_column(String(2))  # CN | EU | US
    tipo_producto: Mapped[str] = mapped_column(String(20))  # fresco | congelado
    temp_min: Mapped[float | None] = mapped_column(Float)
    temp_max: Mapped[float | None] = mapped_column(Float)
    fecha_salida: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fecha_llegada_estimada: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estado: Mapped[str] = mapped_column(String(20), default="en_transito")  # en_transito | entregado | rechazado
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    device = relationship("Device", back_populates="shipments")
    tenant = relationship("Tenant", back_populates="shipments")
    readings = relationship("Reading", back_populates="shipment", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="shipment", cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="shipment", cascade="all, delete-orphan")
