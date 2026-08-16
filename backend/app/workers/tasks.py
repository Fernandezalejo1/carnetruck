"""Tareas Celery: evaluación async de lecturas y watchdog de sin_señal."""

from datetime import datetime, timedelta, timezone

from .celery_app import celery_app


@celery_app.task(name="app.workers.tasks.evaluate_reading")
def evaluate_reading_task(reading_id: int) -> None:
    from ..db import SessionLocal
    from ..models import Reading, Shipment
    from ..services.alert_engine import evaluate_reading
    from ..services.notifier import notify_alert

    db = SessionLocal()
    try:
        reading = db.get(Reading, reading_id)
        if reading is None:
            return
        shipment = db.get(Shipment, reading.shipment_id)
        if shipment is None:
            return
        alerts = evaluate_reading(db, reading, shipment)
        db.commit()
        for alert in alerts:
            notify_alert(alert)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.check_missing_signal")
def check_missing_signal() -> None:
    """Detecta embarques en tránsito sin lecturas recientes (sin_señal)."""
    from ..config import get_settings
    from ..db import SessionLocal
    from ..models import Alert, Reading, Shipment
    from ..services.alert_engine import _recent_alert_exists

    settings = get_settings()
    threshold = timedelta(minutes=settings.missing_signal_threshold_minutes)
    now = datetime.now(timezone.utc)

    db = SessionLocal()
    try:
        shipments = db.query(Shipment).filter(Shipment.estado == "en_transito").all()
        for shipment in shipments:
            last = (
                db.query(Reading)
                .filter(Reading.shipment_id == shipment.id)
                .order_by(Reading.timestamp.desc())
                .first()
            )
            if last is None:
                # Embarque recién creado sin lecturas: dar un margen de gracia.
                continue
            last_ts = last.timestamp
            if last_ts.tzinfo is None:
                last_ts = last_ts.replace(tzinfo=timezone.utc)
            if now - last_ts > threshold and not _recent_alert_exists(
                db, shipment.id, "sin_señal", settings.alert_cooldown_seconds
            ):
                alert = Alert(
                    shipment_id=shipment.id,
                    reading_id=last.id,
                    tipo="sin_señal",
                    severidad="critica",
                    mensaje=f"Sin lecturas desde {last_ts.strftime('%d/%m/%Y %H:%M')}",
                    timestamp=now,
                )
                db.add(alert)
                db.commit()
    finally:
        db.close()
