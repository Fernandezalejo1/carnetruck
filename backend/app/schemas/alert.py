from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shipment_id: int
    reading_id: int | None = None
    tipo: str
    severidad: str
    mensaje: str
    timestamp: datetime
    resuelta: bool
    resuelto_por: str | None = None
    notificado_en: datetime | None = None


class AlertResolveOut(BaseModel):
    id: int
    resuelta: bool = True
    resuelto_por: str
