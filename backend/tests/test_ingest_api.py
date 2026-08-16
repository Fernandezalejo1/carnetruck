import secrets
from datetime import datetime, timedelta, timezone

from app.db import SessionLocal
from app.models import Device, Shipment, Tenant, User
from app.security import hash_password


def _seed_tenant(db, nombre="Frigo A", email="a@test.com", role="admin"):
    """Crea tenant + user + device + shipment; devuelve valores planos."""
    tenant = Tenant(nombre=nombre, pais="AR")
    db.add(tenant)
    db.flush()
    user = User(tenant_id=tenant.id, email=email, hashed_password=hash_password("pass123"), role=role)
    device = Device(tenant_id=tenant.id, imei=secrets.token_hex(8), api_key=secrets.token_hex(16))
    db.add_all([user, device])
    db.flush()
    shipment = Shipment(
        device_id=device.id, tenant_id=tenant.id, numero_contenedor="CNT-" + nombre.replace(" ", ""),
        destino_pais="China", mercado="CN", tipo_producto="congelado",
        temp_min=-20.0, temp_max=-15.0, estado="en_transito",
    )
    db.add(shipment)
    db.commit()
    return {
        "tenant_id": tenant.id,
        "user_id": user.id,
        "device_id": device.id,
        "api_key": device.api_key,
        "shipment_id": shipment.id,
    }


def _login(client, email, password="pass123"):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_login_and_me(client):
    db = SessionLocal()
    try:
        _seed_tenant(db)
    finally:
        db.close()
    token = _login(client, "a@test.com")
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "a@test.com"


def test_login_wrong_password(client):
    r = client.post("/api/v1/auth/login", json={"email": "nadie@test.com", "password": "x"})
    assert r.status_code == 401


def test_ingest_requires_device_key(client):
    r = client.post("/api/v1/ingest", json={"temperatura": -18.0})
    assert r.status_code == 401


def test_ingest_bad_device_key(client):
    r = client.post(
        "/api/v1/ingest", json={"temperatura": -18.0}, headers={"X-Device-Key": "nope"}
    )
    assert r.status_code == 401


def test_ingest_full_flow_and_chain(client):
    db = SessionLocal()
    try:
        seed = _seed_tenant(db)
        api_key, shipment_id = seed["api_key"], seed["shipment_id"]
    finally:
        db.close()

    ts = datetime.now(timezone.utc) - timedelta(minutes=1)
    r = client.post(
        "/api/v1/ingest",
        json={"timestamp": ts.isoformat(), "temperatura": -18.0, "lat": -34.6, "lng": -58.4},
        headers={"X-Device-Key": api_key},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "ok"
    assert len(body["hash_actual"]) == 64
    hash1 = body["hash_actual"]

    # Segunda lectura (fuera de rango, otro timestamp) → alerta + hash encadenado
    ts2 = ts + timedelta(minutes=30)
    r2 = client.post(
        "/api/v1/ingest",
        json={"timestamp": ts2.isoformat(), "temperatura": -10.0},
        headers={"X-Device-Key": api_key},
    )
    assert r2.status_code == 201, r2.text
    assert len(r2.json()["alerts"]) == 1
    assert r2.json()["hash_actual"] != hash1

    # Duplicado (mismo timestamp) → status duplicate
    r3 = client.post(
        "/api/v1/ingest",
        json={"timestamp": ts2.isoformat(), "temperatura": -10.0},
        headers={"X-Device-Key": api_key},
    )
    assert r3.json()["status"] == "duplicate"
    assert r3.json()["alerts"] == []

    db = SessionLocal()
    try:
        from app.models import Reading

        readings = (
            db.query(Reading)
            .filter(Reading.shipment_id == shipment_id)
            .order_by(Reading.timestamp.asc())
            .all()
        )
        assert len(readings) == 2
        assert readings[0].hash_actual == hash1
        assert readings[1].hash_anterior == readings[0].hash_actual
        assert readings[1].hash_actual != readings[0].hash_actual
    finally:
        db.close()


def test_ingest_requires_active_shipment(client):
    db = SessionLocal()
    try:
        seed = _seed_tenant(db)
    finally:
        db.close()
    # El device no tiene embarque en tránsito si lo entregamos antes
    token = _login(client, "a@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    client.post(
        f"/api/v1/shipments/{seed['shipment_id']}/finalizar",
        json={"estado": "entregado"},
        headers=headers,
    )
    r = client.post(
        "/api/v1/ingest",
        json={"temperatura": -18.0},
        headers={"X-Device-Key": seed["api_key"]},
    )
    assert r.status_code == 400


def test_tenant_isolation(client):
    db = SessionLocal()
    try:
        s1 = _seed_tenant(db, "Frigo A", "a@test.com")
        s2 = _seed_tenant(db, "Frigo B", "b@test.com")
    finally:
        db.close()

    token_a = _login(client, "a@test.com")
    r = client.get("/api/v1/shipments", headers={"Authorization": f"Bearer {token_a}"})
    containers = [s["numero_contenedor"] for s in r.json()]
    assert "CNT-FrigoA" in containers
    assert "CNT-FrigoB" not in containers

    # El tenant A no puede ver el embarque del B
    r = client.get(f"/api/v1/shipments/{s2['shipment_id']}", headers={"Authorization": f"Bearer {token_a}"})
    assert r.status_code == 404


def test_certificate_generate_verify_and_pdf(client):
    db = SessionLocal()
    try:
        seed = _seed_tenant(db)
        api_key, shipment_id = seed["api_key"], seed["shipment_id"]
    finally:
        db.close()

    for i in range(5):
        ts = datetime.now(timezone.utc) - timedelta(minutes=30 * (5 - i))
        client.post(
            "/api/v1/ingest",
            json={"timestamp": ts.isoformat(), "temperatura": -18.0 if i % 2 == 0 else -10.0},
            headers={"X-Device-Key": api_key},
        )

    token = _login(client, "a@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post(f"/api/v1/shipments/{shipment_id}/certificate", headers=headers)
    assert r.status_code == 200, r.text
    cert = r.json()
    assert cert["cantidad_lecturas"] == 5
    assert cert["cantidad_alertas"] >= 1
    assert len(cert["hash_documento"]) == 64

    # Verificación de integridad
    r = client.get(f"/api/v1/certificates/{cert['id']}/verify", headers=headers)
    assert r.status_code == 200
    assert r.json()["valid"] is True

    # PDF descargable y empieza con %PDF
    r = client.get(f"/api/v1/certificates/{cert['id']}/pdf", headers=headers)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")

    # Tampering simulado: alterar una lectura → verify falla
    db = SessionLocal()
    try:
        from app.models import Reading

        rrow = db.query(Reading).filter(Reading.shipment_id == shipment_id).first()
        rrow.temperatura = 30.0
        db.commit()
    finally:
        db.close()
    r = client.get(f"/api/v1/certificates/{cert['id']}/verify", headers=headers)
    assert r.json()["valid"] is False


def test_finalizar_generates_certificate_automatically(client):
    db = SessionLocal()
    try:
        seed = _seed_tenant(db)
        api_key, shipment_id = seed["api_key"], seed["shipment_id"]
    finally:
        db.close()
    ts = datetime.now(timezone.utc)
    client.post("/api/v1/ingest", json={"timestamp": ts.isoformat(), "temperatura": -18.0},
                headers={"X-Device-Key": api_key})
    token = _login(client, "a@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post(f"/api/v1/shipments/{shipment_id}/finalizar", json={"estado": "entregado"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["estado"] == "entregado"
    r2 = client.get(f"/api/v1/shipments/{shipment_id}/certificate", headers=headers)
    assert r2.status_code == 200
