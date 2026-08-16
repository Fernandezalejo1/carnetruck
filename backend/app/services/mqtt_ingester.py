"""Ingestor MQTT opcional (proceso independiente).

Suscribe a `carnetruck/{imei}/readings` y reenvía cada mensaje JSON al pipeline
de ingesta (mismo código que el endpoint HTTP). Se ejecuta con:
    python -m app.services.mqtt_ingester
"""

import json
import logging
import sys
import urllib.parse
from datetime import datetime, timezone

from ..config import get_settings
from ..db import SessionLocal
from ..models import Device, Shipment
from ..schemas.ingest import ReadingPayload
from .ingest_service import ingest_reading, normalize_ts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _parse_broker_url(url: str) -> tuple[dict, str]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("mqtt", "mqtts"):
        raise ValueError(f"MQTT_URL inválida: {url}")
    kwargs: dict = {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or (8883 if parsed.scheme == "mqtts" else 1883),
    }
    if parsed.username:
        kwargs["username"] = urllib.parse.unquote(parsed.username)
    if parsed.password:
        kwargs["password"] = urllib.parse.unquote(parsed.password)
    return kwargs, parsed.scheme


def _resolve_shipment(db, device: Device, shipment_id: int | None) -> Shipment | None:
    if shipment_id is not None:
        return (
            db.query(Shipment)
            .filter(Shipment.id == shipment_id, Shipment.device_id == device.id)
            .first()
        )
    return (
        db.query(Shipment)
        .filter(Shipment.device_id == device.id, Shipment.estado == "en_transito")
        .order_by(Shipment.created_at.desc())
        .first()
    )


def _handle_message(topic: str, raw: bytes) -> None:
    # Topic esperado: carnetruck/{imei}/readings
    parts = topic.split("/")
    if len(parts) < 3:
        logger.warning("Topic inesperado: %s", topic)
        return
    imei = parts[1]
    try:
        data = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        logger.warning("Payload no JSON en %s: %.200s", topic, raw)
        return

    db = SessionLocal()
    try:
        device = db.query(Device).filter(Device.imei == imei).first()
        if device is None:
            logger.warning("IMEI desconocido: %s", imei)
            return
        try:
            payload = ReadingPayload(**data)
        except Exception as exc:
            logger.warning("Payload inválido desde %s: %s", imei, exc)
            return
        shipment = _resolve_shipment(db, device, payload.shipment_id)
        if shipment is None:
            logger.warning("IMEI %s sin embarque activo", imei)
            return
        ts = normalize_ts(payload.timestamp)
        reading, _alerts, duplicate = ingest_reading(db, shipment, device, payload, ts)
        if not duplicate:
            logger.info("Lectura %s guardada (shipment %s, hash %s)", reading.id, shipment.id, reading.hash_actual[:12])
    finally:
        db.close()


def main() -> None:
    settings = get_settings()
    if not settings.mqtt_url:
        logger.error("MQTT_URL no configurado. Abortando.")
        sys.exit(0)

    import paho.mqtt.client as mqtt

    kwargs, scheme = _parse_broker_url(settings.mqtt_url)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if scheme == "mqtts":
        client.tls_set()

    def on_connect(client_, _userdata, _flags, reason_code, _props):
        if reason_code == 0:
            client_.subscribe(settings.mqtt_topic)
            logger.info("Conectado a %s, suscrito a %s", settings.mqtt_url, settings.mqtt_topic)
        else:
            logger.error("Conexión MQTT rechazada: %s", reason_code)

    def on_message(_client, _userdata, msg):
        _handle_message(msg.topic, msg.payload)

    client.on_connect = on_connect
    client.on_message = on_message
    if kwargs.get("username") is not None:
        client.username_pw_set(kwargs["username"], kwargs.get("password"))
    client.connect(kwargs["host"], kwargs["port"], keepalive=60)
    client.loop_forever()


if __name__ == "__main__":
    main()
