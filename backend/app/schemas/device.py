from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DeviceCreate(BaseModel):
    imei: str = Field(min_length=5, max_length=32)
    alias: str | None = Field(default=None, max_length=200)
    estado: Literal["activo", "almacenado", "mantenimiento"] = "activo"
    # Obligatorio solo para superadmin (un admin lo hereda de su tenant).
    tenant_id: int | None = None


class DeviceUpdate(BaseModel):
    estado: Literal["activo", "almacenado", "mantenimiento"]


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    imei: str
    alias: str | None = None
    api_key: str
    estado: str
    created_at: datetime
