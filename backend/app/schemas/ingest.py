from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ReadingPayload(BaseModel):
    """Payload aceptado por POST /api/v1/ingest (NBM1 nativo o tag BLE)."""

    timestamp: datetime | None = None
    temperatura: float | None = None
    humedad: float | None = Field(default=None, ge=0, le=100)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    puerta_abierta: bool = False
    vibracion: bool = False
    tamper: bool = False
    bateria: float | None = Field(default=None, ge=0, le=100)
    fuente: Literal["nbm1", "ble"] = "nbm1"
    shipment_id: int | None = None
    client_msg_id: str | None = None


class IngestResponse(BaseModel):
    status: str  # ok | duplicate
    reading_id: int
    hash_actual: str
    alerts: list[int]
