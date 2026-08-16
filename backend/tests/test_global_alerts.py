from app.db import SessionLocal
from tests.test_ingest_api import _login, _seed_tenant


def test_global_alerts_endpoint(client):
    db = SessionLocal()
    try:
        seed = _seed_tenant(db)
        api_key = seed["api_key"]
    finally:
        db.close()

    # Lectura fuera de rango → genera alerta
    from datetime import datetime, timezone

    client.post(
        "/api/v1/ingest",
        json={"timestamp": datetime.now(timezone.utc).isoformat(), "temperatura": -10.0},
        headers={"X-Device-Key": api_key},
    )

    token = _login(client, "a@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    r = client.get("/api/v1/alerts", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["tipo"] == "temp_fuera_rango"

    r = client.get("/api/v1/alerts", params={"resuelta": "true"}, headers=headers)
    assert r.json() == []
