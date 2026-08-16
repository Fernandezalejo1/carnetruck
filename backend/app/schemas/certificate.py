from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CertificateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shipment_id: int
    numero_contenedor: str | None = None
    generado_en: datetime
    hash_documento: str
    temp_min_registrada: float | None = None
    temp_max_registrada: float | None = None
    temp_promedio: float | None = None
    cantidad_alertas: int
    cantidad_lecturas: int
    url_pdf: str | None = None


class CertificateVerifyOut(BaseModel):
    valid: bool
    stored_hash: str
    recomputed_hash: str
    detail: str
