"""Tests para certificados."""

from fastapi.testclient import TestClient


def test_certificate_requires_auth(client: TestClient):
    """Certificado requiere autenticación."""
    resp = client.get("/api/v1/shipments/1/certificate")
    assert resp.status_code == 401


def test_certificate_endpoint_exists(client: TestClient):
    """El endpoint de certificado existe."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@carnetruck.com", "password": "admin123"},
    )
    if resp.status_code == 200:
        token = resp.json()["access_token"]
        resp = client.get(
            "/api/v1/shipments/1/certificate",
            headers={"Authorization": f"Bearer {token}"},
        )
        # 404 porque no hay certificado para shipment 1
        assert resp.status_code in (404, 200)
