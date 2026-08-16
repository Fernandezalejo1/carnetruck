from datetime import datetime, timedelta, timezone

from app.db import SessionLocal
from app.models import Alert, Device, Reading, Shipment, Tenant
from app.schemas.ingest import ReadingPayload
from app.services.alert_engine import evaluate_reading
from app.services.ingest_service import ingest_reading


def _setup():
    db = SessionLocal()
    tenant = Tenant(nombre="T", pais="AR")
    db.add(tenant)
    db.flush()
    device = Device(tenant_id=tenant.id, imei="12345", api_key="k1")
    db.add(device)
    db.flush()
    shipment = Shipment(
        device_id=device.id, tenant_id=tenant.id, numero_contenedor="CNT-1",
        destino_pais="China", mercado="CN", tipo_producto="congelado",
        temp_min=-20.0, temp_max=-15.0,
    )
    db.add(shipment)
    db.commit()
    return db, tenant, device, shipment


def _reading(db, shipment, device, ts, temp=None, door=False, tamper=False, battery=None):
    payload = ReadingPayload(
        timestamp=ts, temperatura=temp, puerta_abierta=door, tamper=tamper, bateria=battery
    )
    reading, alerts, dup = ingest_reading(db, shipment, device, payload, ts)
    assert not dup
    return reading, alerts


def test_temp_out_of_range_creates_alert():
    db, _t, device, shipment = _setup()
    try:
        r, alerts = _reading(db, shipment, device, datetime.now(timezone.utc), temp=-10.0)
        assert any(a.tipo == "temp_fuera_rango" for a in alerts)
        assert alerts[0].severidad == "critica"
    finally:
        db.close()


def test_temp_in_range_no_alert():
    db, _t, device, shipment = _setup()
    try:
        r, alerts = _reading(db, shipment, device, datetime.now(timezone.utc), temp=-18.0)
        assert alerts == []
    finally:
        db.close()


def test_door_and_tamper_alerts():
    db, _t, device, shipment = _setup()
    try:
        _r, alerts = _reading(
            db, shipment, device, datetime.now(timezone.utc), temp=-18.0, door=True, tamper=True
        )
        tipos = {a.tipo for a in alerts}
        assert {"puerta_abierta", "tamper"} <= tipos
    finally:
        db.close()


def test_low_battery_alert():
    db, _t, device, shipment = _setup()
    try:
        _r, alerts = _reading(db, shipment, device, datetime.now(timezone.utc), temp=-18.0, battery=5.0)
        assert any(a.tipo == "bateria_baja" for a in alerts)
    finally:
        db.close()


def test_duplicate_reading_returns_duplicate():
    db, _t, device, shipment = _setup()
    try:
        ts = datetime.now(timezone.utc)
        _r, _a = _reading(db, shipment, device, ts, temp=-10.0)
        reading, alerts, dup = ingest_reading(
            db, shipment, device, ReadingPayload(timestamp=ts, temperatura=-10.0), ts
        )
        assert dup
        assert alerts == []
    finally:
        db.close()


def test_hash_chain_linked():
    db, _t, device, shipment = _setup()
    try:
        base = datetime.now(timezone.utc) - timedelta(minutes=10)
        r1, _ = _reading(db, shipment, device, base, temp=-18.0)
        r2, _ = _reading(db, shipment, device, base + timedelta(minutes=1), temp=-18.0)
        assert r2.hash_anterior == r1.hash_actual
        assert r2.hash_actual != r1.hash_actual
        # recomputar sobre la base de datos da el mismo resultado
        reread = db.get(Reading, r1.id)
        from app.schemas.ingest import ReadingPayload as RP

        from app.services.ingest_service import payload_to_canonical
        from app.services.integrity_hash import chain_hash

        canonical = payload_to_canonical(
            RP(timestamp=reread.timestamp, temperatura=reread.temperatura),
            reread.shipment_id, reread.timestamp,
        )
        assert chain_hash(None, canonical) == reread.hash_actual
    finally:
        db.close()
