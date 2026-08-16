from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Device, User
from ..schemas.device import DeviceCreate, DeviceOut, DeviceUpdate
from .deps import get_current_user, require_roles

router = APIRouter(prefix="/devices", tags=["devices"])

ADMIN_ROLES = ("superadmin", "admin")


def _tenant_filter(q, user: User):
    if user.tenant_id is not None:
        return q.filter(Device.tenant_id == user.tenant_id)
    return q


@router.get("", response_model=list[DeviceOut])
def list_devices(
    estado: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[DeviceOut]:
    q = _tenant_filter(db.query(Device), user)
    if estado:
        q = q.filter(Device.estado == estado)
    devices = q.order_by(Device.created_at.desc()).limit(limit).all()
    return [DeviceOut.model_validate(d) for d in devices]


@router.post("", response_model=DeviceOut, status_code=201)
def create_device(
    body: DeviceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*ADMIN_ROLES)),
) -> DeviceOut:
    import secrets

    tenant_id = body.tenant_id if user.tenant_id is None else user.tenant_id
    if tenant_id is None:
        raise HTTPException(status_code=400, detail="Superadmin debe indicar tenant_id")
    from ..models import Tenant

    if db.get(Tenant, tenant_id) is None:
        raise HTTPException(status_code=400, detail="Tenant inexistente")
    if db.query(Device).filter(Device.imei == body.imei).first() is not None:
        raise HTTPException(status_code=409, detail="Ya existe un dispositivo con ese IMEI")
    device = Device(
        tenant_id=tenant_id,
        imei=body.imei,
        alias=body.alias,
        api_key=secrets.token_hex(16),
        estado=body.estado,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return DeviceOut.model_validate(device)


@router.patch("/{device_id}", response_model=DeviceOut)
def update_device(
    device_id: int,
    body: DeviceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*ADMIN_ROLES)),
) -> DeviceOut:
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    if user.tenant_id is not None and device.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    device.estado = body.estado
    db.commit()
    db.refresh(device)
    return DeviceOut.model_validate(device)
