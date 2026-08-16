from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .ingest import ReadingPayload


class ShipmentCreate(BaseModel):
    device_id: int
    numero_contenedor: str = Field(min_length=3, max_length=50)
    destino_pais: str = Field(min_length=2, max_length=100)
    mercado: Literal["CN", "EU", "US"]
    tipo_producto: Literal["fresco", "congelado"]
    temp_min: float | None = None
    temp_max: float | None = None
    fecha_salida: datetime | None = None
    fecha_llegada_estimada: datetime | None = None


class ShipmentUpdate(BaseModel):
    estado: Literal["entregado", "rechazado"]


class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    temperatura: float | None = None
    humedad: float | None = None
    lat: float | None = None
    lng: float | None = None
    puerta_abierta: bool = False
    vibracion: bool = False
    tamper: bool = False
    bateria: float | None = None
    fuente: str = "nbm1"
    hash_actual: str


class ShipmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    tenant_id: int
    numero_contenedor: str
    destino_pais: str
    mercado: str
    tipo_producto: str
    temp_min: float | None = None
    temp_max: float | None = None
    fecha_salida: datetime | None = None
    fecha_llegada_estimada: datetime | None = None
    estado: str
    created_at: datetime
    latest_reading: ReadingOut | None = None
    alertas_sin_resolver: int = 0


class ReadingPage(BaseModel):
    total: int
    items: list[ReadingOut]
