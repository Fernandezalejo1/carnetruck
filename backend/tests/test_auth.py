"""Tests de autenticación."""

import pytest
from fastapi.testclient import TestClient


def test_login_success(client: TestClient):
    """Login con credenciales válidas devuelve token."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@carnetruck.com", "password": "admin123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "admin@carnetruck.com"


def test_login_wrong_password(client: TestClient):
    """Login con contraseña incorrecta devuelve 401."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@carnetruck.com", "password": "wrong"},
    )
    assert resp.status_code == 401


def test_login_nonexistent_user(client: TestClient):
    """Login con usuario inexistente devuelve 401."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "noexiste@test.com", "password": "test123"},
    )
    assert resp.status_code == 401


def test_me_without_token(client: TestClient):
    """GET /me sin token devuelve 401."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
