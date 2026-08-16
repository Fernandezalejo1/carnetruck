from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Device, Shipment
from ..schemas.ingest import IngestResponse, ReadingPayload
from ..services.ingest_service import ingest_reading, normalize_ts
from .deps import get_device_by_key

router = APIRouter(prefix="/ingest", tags=["ingest"])


def _resolve_shipment(db: Session, device: Device, payload: ReadingPayload) -> Shipment:
    if payload.shipment_id is not None:
        shipment = (
            db.query(Shipment)
            .filter(Shipment.id == payload.shipment_id, Shipment.device_id == device.id)
            .first()
        )
        if shipment is None:
            raise HTTPException(status_code=404, detail="Embarque no encontrado para este dispositivo")
        return shipment
    shipment = (
        db.query(Shipment)
        .filter(Shipment.device_id == device.id, Shipment.estado == "en_transito")
        .order_by(Shipment.created_at.desc())
        .first()
    )
    if shipment is None:
        raise HTTPException(status_code=400, detail="El dispositivo no tiene un embarque activo")
    return shipment


@router.post("", response_model=IngestResponse, status_code=201)
def ingest(
    payload: ReadingPayload,
    device: Device = Depends(get_device_by_key),
    db: Session = Depends(get_db),
) -> IngestResponse:
    shipment = _resolve_shipment(db, device, payload)
    ts = normalize_ts(payload.timestamp)
    reading, alerts, duplicate = ingest_reading(db, shipment, device, payload, ts)
    return IngestResponse(
        status="duplicate" if duplicate else "ok",
        reading_id=reading.id,
        hash_actual=reading.hash_actual,
        alerts=[a.id for a in alerts],
    )
