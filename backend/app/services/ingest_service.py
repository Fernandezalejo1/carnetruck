"""Pipeline de ingesta compartido por HTTP, MQTT y seed.

Flujo: dedupe por (shipment_id, timestamp) → hash encadenado → persistir →
evaluar alertas (sync o vía Celery según ALERT_EVAL_MODE) → notificar.
"""

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import Alert, Device, Reading, Shipment
from .alert_engine import evaluate_reading
from .integrity_hash import chain_hash, normalized_iso
from .notifier import notify_alert


def payload_to_canonical(payload, shipment_id: int, ts: datetime) -> dict:
    return {
        "shipment_id": shipment_id,
        "timestamp": normalized_iso(ts),
        "temperatura": payload.temperatura,
        "humedad": payload.humedad,
        "lat": payload.lat,
        "lng": payload.lng,
        "puerta_abierta": payload.puerta_abierta,
        "vibracion": payload.vibracion,
        "tamper": payload.tamper,
        "bateria": payload.bateria,
        "fuente": payload.fuente,
    }


def normalize_ts(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def ingest_reading(
    db: Session,
    shipment: Shipment,
    device: Device,
    payload,
    ts: datetime,
) -> tuple[Reading, list[Alert], bool]:
    """Guarda la lectura y evalúa alertas. Devuelve (reading, alerts, is_duplicate)."""
    settings = get_settings()
    ts = normalize_ts(ts)

    def _find_existing() -> Reading | None:
        return (
            db.query(Reading)
            .filter(Reading.shipment_id == shipment.id, Reading.timestamp == ts)
            .first()
        )

    existing = _find_existing()
    if existing:
        return existing, [], True

    prev = (
        db.query(Reading)
        .filter(Reading.shipment_id == shipment.id)
        .order_by(Reading.timestamp.desc())
        .first()
    )
    canonical = payload_to_canonical(payload, shipment.id, ts)
    prev_hash = prev.hash_actual if prev else None

    reading = Reading(
        shipment_id=shipment.id,
        device_id=device.id,
        timestamp=ts,
        temperatura=payload.temperatura,
        humedad=payload.humedad,
        lat=payload.lat,
        lng=payload.lng,
        puerta_abierta=payload.puerta_abierta,
        vibracion=payload.vibracion,
        tamper=payload.tamper,
        bateria=payload.bateria,
        fuente=payload.fuente,
        hash_anterior=prev_hash,
        hash_actual=chain_hash(prev_hash, canonical),
    )
    db.add(reading)
    try:
        db.flush()
        db.commit()
    except IntegrityError:
        # Carrera: otra request insertó la misma lectura; tratar como duplicado.
        db.rollback()
        existing = _find_existing()
        if existing:
            return existing, [], True
        raise

    if settings.alert_eval_mode == "celery":
        from ..workers.tasks import evaluate_reading_task  # import tardío

        evaluate_reading_task.delay(reading.id)
        return reading, [], False

    alerts = evaluate_reading(db, reading, shipment)
    db.commit()
    for alert in alerts:
        notify_alert(alert)
    return reading, alerts, False
