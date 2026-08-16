from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base
from .tenant import utcnow


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[int] = mapped_column(primary_key=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipments.id"), index=True)
    generado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    hash_documento: Mapped[str] = mapped_column(String(64))
    temp_min_registrada: Mapped[float | None] = mapped_column(Float)
    temp_max_registrada: Mapped[float | None] = mapped_column(Float)
    temp_promedio: Mapped[float | None] = mapped_column(Float)
    cantidad_alertas: Mapped[int] = mapped_column(Integer, default=0)
    cantidad_lecturas: Mapped[int] = mapped_column(Integer, default=0)
    url_pdf: Mapped[str | None] = mapped_column(String(300))
    pdf_bytes: Mapped[bytes | None] = mapped_column(LargeBinary)

    shipment = relationship("Shipment", back_populates="certificates")
