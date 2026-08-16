import logging

from ..config import get_settings

logger = logging.getLogger(__name__)


def notify_alert(alert) -> None:
    """Fire-and-forget notificación (WhatsApp/email vía n8n webhook).

    Si no hay webhook configurado, registra la alerta en el log.
    """
    settings = get_settings()
    if not settings.n8n_webhook_url:
        logger.info("Alerta %s (severidad=%s) shipment=%s: %s", alert.tipo, alert.severidad, alert.shipment_id, alert.mensaje)
        return
    try:
        import httpx

        headers = {"Content-Type": "application/json"}
        if settings.n8n_webhook_token:
            headers["Authorization"] = f"Bearer {settings.n8n_webhook_token}"
        payload = {
            "tipo": alert.tipo,
            "severidad": alert.severidad,
            "mensaje": alert.mensaje,
            "shipment_id": alert.shipment_id,
            "timestamp": alert.timestamp.isoformat(),
        }
        resp = httpx.post(settings.n8n_webhook_url, json=payload, headers=headers, timeout=5)
        resp.raise_for_status()
    except Exception:
        logger.exception("Error notificando alerta %s", getattr(alert, "id", None))
