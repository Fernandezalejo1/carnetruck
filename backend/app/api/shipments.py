from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Alert, Reading, Shipment, User
from ..schemas.alert import AlertOut
from ..schemas.certificate import CertificateOut
from ..schemas.shipment import ReadingOut, ReadingPage, ShipmentCreate, ShipmentOut, ShipmentUpdate
from ..services.certificate_generator import generate_certificate
from .deps import get_current_user, require_roles

router = APIRouter(prefix="/shipments", tags=["shipments"])
alerts_router = APIRouter(prefix="/alerts", tags=["alerts"])

ADMIN_ROLES = ("superadmin", "admin")


def _tenant_filter(q, user: User):
    if user.tenant_id is not None:
        return q.filter(Shipment.tenant_id == user.tenant_id)
    return q


def _get_shipment(db: Session, user: User, shipment_id: int) -> Shipment:
    shipment = db.get(Shipment, shipment_id)
    if shipment is None:
        raise HTTPException(status_code=404, detail="Embarque no encontrado")
    if user.tenant_id is not None and shipment.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Embarque no encontrado")
    return shipment


@alerts_router.get("", response_model=list[AlertOut])
def list_all_alerts(
    tipo: str | None = None,
    resuelta: bool | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AlertOut]:
    """Alertas del tenant (todas los embarques), para el panel global."""
    q = db.query(Alert).join(Shipment)
    if user.tenant_id is not None:
        q = q.filter(Shipment.tenant_id == user.tenant_id)
    if tipo:
        q = q.filter(Alert.tipo == tipo)
    if resuelta is not None:
        q = q.filter(Alert.resuelta.is_(resuelta))
    alerts = q.order_by(Alert.timestamp.desc()).limit(limit).all()
    return [AlertOut.model_validate(a) for a in alerts]


def _to_out(db: Session, shipment: Shipment) -> ShipmentOut:
    latest = (
        db.query(Reading)
        .filter(Reading.shipment_id == shipment.id)
        .order_by(Reading.timestamp.desc())
        .first()
    )
    pending = (
        db.query(Alert)
        .filter(Alert.shipment_id == shipment.id, Alert.resuelta.is_(False))
        .count()
    )
    out = ShipmentOut.model_validate(shipment)
    out.latest_reading = ReadingOut.model_validate(latest) if latest else None
    out.alertas_sin_resolver = pending
    return out


@router.get("", response_model=list[ShipmentOut])
def list_shipments(
    estado: str | None = None,
    mercado: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ShipmentOut]:
    q = _tenant_filter(db.query(Shipment), user)
    if estado:
        q = q.filter(Shipment.estado == estado)
    if mercado:
        q = q.filter(Shipment.mercado == mercado.upper())
    shipments = q.order_by(Shipment.created_at.desc()).offset(offset).limit(limit).all()
    return [_to_out(db, s) for s in shipments]


@router.post("", response_model=ShipmentOut, status_code=201)
def create_shipment(
    body: ShipmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*ADMIN_ROLES)),
) -> ShipmentOut:
    from ..models import Device

    device = db.get(Device, body.device_id)
    if device is None:
        raise HTTPException(status_code=400, detail="Dispositivo inexistente")
    if user.tenant_id is not None and device.tenant_id != user.tenant_id:
        raise HTTPException(status_code=400, detail="El dispositivo no pertenece a su frigorífico")
    tenant_id = device.tenant_id

    # Un device no puede tener dos embarques en tránsito simultáneos.
    active = (
        db.query(Shipment)
        .filter(Shipment.device_id == body.device_id, Shipment.estado == "en_transito")
        .first()
    )
    if active is not None:
        raise HTTPException(status_code=400, detail="El dispositivo ya tiene un embarque en tránsito")

    shipment = Shipment(
        device_id=body.device_id,
        tenant_id=tenant_id,
        numero_contenedor=body.numero_contenedor.strip().upper(),
        destino_pais=body.destino_pais,
        mercado=body.mercado,
        tipo_producto=body.tipo_producto,
        temp_min=body.temp_min,
        temp_max=body.temp_max,
        fecha_salida=body.fecha_salida,
        fecha_llegada_estimada=body.fecha_llegada_estimada,
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    return _to_out(db, shipment)


@router.get("/{shipment_id}", response_model=ShipmentOut)
def get_shipment(
    shipment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ShipmentOut:
    shipment = _get_shipment(db, user, shipment_id)
    return _to_out(db, shipment)


@router.get("/{shipment_id}/readings", response_model=ReadingPage)
def list_readings(
    shipment_id: int,
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReadingPage:
    _get_shipment(db, user, shipment_id)  # valida tenant
    q = db.query(Reading).filter(Reading.shipment_id == shipment_id)
    if from_ is not None:
        q = q.filter(Reading.timestamp >= from_)
    if to is not None:
        q = q.filter(Reading.timestamp <= to)
    total = q.count()
    readings = q.order_by(Reading.timestamp.asc()).offset(offset).limit(limit).all()
    return ReadingPage(total=total, items=[ReadingOut.model_validate(r) for r in readings])


@router.get("/{shipment_id}/alerts", response_model=list[AlertOut])
def list_alerts(
    shipment_id: int,
    tipo: str | None = None,
    resuelta: bool | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AlertOut]:
    _get_shipment(db, user, shipment_id)
    q = db.query(Alert).filter(Alert.shipment_id == shipment_id)
    if tipo:
        q = q.filter(Alert.tipo == tipo)
    if resuelta is not None:
        q = q.filter(Alert.resuelta.is_(resuelta))
    alerts = q.order_by(Alert.timestamp.desc()).limit(limit).all()
    return [AlertOut.model_validate(a) for a in alerts]


@router.post("/{shipment_id}/alerts/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(
    shipment_id: int,
    alert_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AlertOut:
    _get_shipment(db, user, shipment_id)
    alert = db.get(Alert, alert_id)
    if alert is None or alert.shipment_id != shipment_id:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    alert.resuelta = True
    alert.resuelto_por = user.email
    db.commit()
    db.refresh(alert)
    return AlertOut.model_validate(alert)


@router.post("/{shipment_id}/finalizar", response_model=ShipmentOut)
def finalizar(
    shipment_id: int,
    body: ShipmentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*ADMIN_ROLES)),
) -> ShipmentOut:
    shipment = _get_shipment(db, user, shipment_id)
    shipment.estado = body.estado
    db.commit()
    # Al entregar, emitir el certificado automáticamente si no existe.
    if body.estado == "entregado":
        generate_certificate(db, shipment)
    db.refresh(shipment)
    return _to_out(db, shipment)


@router.post("/{shipment_id}/certificate", response_model=CertificateOut)
def generate(
    shipment_id: int,
    regenerate: bool = Query(default=False),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*ADMIN_ROLES)),
) -> CertificateOut:
    shipment = _get_shipment(db, user, shipment_id)
    cert = generate_certificate(db, shipment, regenerate=regenerate)
    return CertificateOut.model_validate(cert)


@router.get("/{shipment_id}/certificate", response_model=CertificateOut)
def latest_certificate(
    shipment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CertificateOut:
    _get_shipment(db, user, shipment_id)
    from ..models import Certificate

    cert = (
        db.query(Certificate)
        .filter(Certificate.shipment_id == shipment_id)
        .order_by(Certificate.generado_en.desc())
        .first()
    )
    if cert is None:
        raise HTTPException(status_code=404, detail="Aún no hay certificado para este embarque")
    return CertificateOut.model_validate(cert)
