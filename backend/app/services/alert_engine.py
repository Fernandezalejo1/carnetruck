"""Motor de reglas: evalúa una lectura contra el rango del embarque.

No hace commit: el caller persiste y notifica. El cooldown evita tormentas de
alertas repetidas del mismo tipo en el mismo embarque.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import Alert, Reading, Shipment

SEVERIDADES = {
    "temp_fuera_rango": "critica",
    "puerta_abierta": "media",
    "tamper": "critica",
    "sin_señal": "critica",
    "bateria_baja": "media",
}


def _recent_alert_exists(db: Session, shipment_id: int, tipo: str, cooldown_seconds: int) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=cooldown_seconds)
    return (
        db.query(Alert)
        .filter(
            Alert.shipment_id == shipment_id,
            Alert.tipo == tipo,
            Alert.timestamp >= cutoff,
        )
        .first()
        is not None
    )


def evaluate_reading(db: Session, reading: Reading, shipment: Shipment) -> list[Alert]:
    """Evalúa reglas y devuelve las alertas nuevas (persistidas en la sesión, sin commit)."""
    settings = get_settings()
    created: list[Alert] = []
    now = datetime.now(timezone.utc)

    def _add(tipo: str, mensaje: str) -> None:
        if _recent_alert_exists(db, shipment.id, tipo, settings.alert_cooldown_seconds):
            return
        alert = Alert(
            shipment_id=shipment.id,
            reading_id=reading.id,
            tipo=tipo,
            severidad=SEVERIDADES.get(tipo, "media"),
            mensaje=mensaje,
            timestamp=now,
        )
        db.add(alert)
        created.append(alert)

    # 1) Temperatura fuera de rango (solo si el embarque define rango y hay lectura).
    if (
        reading.temperatura is not None
        and shipment.temp_min is not None
        and shipment.temp_max is not None
        and (reading.temperatura < shipment.temp_min or reading.temperatura > shipment.temp_max)
    ):
        _add(
            "temp_fuera_rango",
            f"Temperatura {reading.temperatura:.1f}°C fuera de rango "
            f"[{shipment.temp_min:.1f}, {shipment.temp_max:.1f}]°C",
        )

    # 2) Puerta abierta durante tránsito.
    if reading.puerta_abierta:
        _add("puerta_abierta", "Puerta del contenedor abierta durante tránsito")

    # 3) Tamper / manipulación.
    if reading.tamper:
        _add("tamper", "Evento de manipulación (tamper) detectado en el dispositivo")

    # 4) Batería baja (el device puede dejar de reportar = pérdida de cadena de frío).
    if reading.bateria is not None and reading.bateria < 10:
        _add("bateria_baja", f"Batería del dispositivo al {reading.bateria:.0f}%")

    return created
