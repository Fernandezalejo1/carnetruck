"""Datos demo: frigorífico, usuarios, device, embarque y un viaje simulado.

Genera ~3 días de lecturas cada 30 min con una excursión de temperatura,
aperturas de puerta, un evento tamper y batería decreciente. Reutiliza el
pipeline real (ingest_reading) para que la cadena de hashes y las alertas
sean auténticas.
"""

import logging
import random
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from .models import Device, Shipment, Tenant, User
from .schemas.ingest import ReadingPayload
from .security import hash_password
from .services.ingest_service import ingest_reading

logger = logging.getLogger(__name__)

_DEMO_EMAILS = ("admin@carnetruck.com", "operador@carnetruck.com")


def _demo_exists(db: Session) -> bool:
    return db.query(Tenant).filter(Tenant.nombre == "Frigorífico Demo S.A.").first() is not None


def seed_demo_data(db: Session) -> None:
    if _demo_exists(db):
        return

    tenant = Tenant(nombre="Frigorífico Demo S.A.", pais="Argentina", contacto="demo@carnetruck.local")
    db.add(tenant)
    db.flush()

    db.add_all(
        [
            User(
                tenant_id=tenant.id,
                email="admin@carnetruck.com",
                hashed_password=hash_password("admin123"),
                full_name="Admin Demo",
                role="superadmin",
            ),
            User(
                tenant_id=tenant.id,
                email="operador@carnetruck.com",
                hashed_password=hash_password("operador123"),
                full_name="Operador Demo",
                role="operator",
            ),
        ]
    )

    device = Device(
        tenant_id=tenant.id,
        imei="352099123456789",
        alias="NBM1 – Contenedor 1",
        api_key=secrets.token_hex(16),
        estado="activo",
    )
    db.add(device)
    db.flush()

    now = datetime.now(timezone.utc)
    shipment = Shipment(
        device_id=device.id,
        tenant_id=tenant.id,
        numero_contenedor="MSKU1234567",
        destino_pais="China",
        mercado="CN",
        tipo_producto="congelado",
        temp_min=-20.0,
        temp_max=-15.0,
        fecha_salida=now - timedelta(days=3),
        fecha_llegada_estimada=now + timedelta(days=5),
        estado="en_transito",
    )
    db.add(shipment)
    db.commit()

    _simulate_trip(db, shipment, device, now)

    logger.info(
        "Seed demo listo. Login: %s / admin123 · device api_key: %s",
        _DEMO_EMAILS[0],
        device.api_key,
    )


def _simulate_trip(db: Session, shipment: Shipment, device: Device, now: datetime) -> None:
    random.seed(42)
    start = now - timedelta(days=3)
    steps = int(timedelta(days=3) / timedelta(minutes=30))
    # Buenos Aires → Shanghai (interpolación lineal simple).
    lat0, lng0, lat1, lng1 = -34.6, -58.4, 31.2, 121.5
    excursion_start = now - timedelta(hours=42)
    excursion_end = excursion_start + timedelta(hours=2)

    for i in range(steps):
        ts = start + timedelta(minutes=30 * i)
        frac = i / max(steps - 1, 1)
        lat = lat0 + (lat1 - lat0) * frac + random.uniform(-0.05, 0.05)
        lng = lng0 + (lng1 - lng0) * frac + random.uniform(-0.05, 0.05)

        if excursion_start <= ts <= excursion_end:
            temp = -10.0 + random.uniform(-1.0, 1.0)  # fuera de rango
        else:
            temp = -18.0 + random.uniform(-1.5, 1.5)

        payload = ReadingPayload(
            timestamp=ts,
            temperatura=round(temp, 2),
            humedad=round(70 + random.uniform(-5, 5), 1),
            lat=round(lat, 6),
            lng=round(lng, 6),
            puerta_abierta=abs(i - 20) < 1 or abs(i - 90) < 1,
            vibracion=random.random() < 0.03,
            tamper=abs(i - 60) < 1,
            bateria=round(max(0, 100 - frac * 25 - random.uniform(0, 2)), 1),
            fuente="nbm1",
        )
        ingest_reading(db, shipment, device, payload, ts)
