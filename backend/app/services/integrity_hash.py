"""Integridad encadenada estilo blockchain ligero.

Cada lectura guarda `hash_actual = SHA256(hash_anterior | payload_canonical)`.
El payload canónico se serializa con claves ordenadas para que el hash sea
determinístico sin importar el orden en que lleguen los campos.
"""

import hashlib
import json
from datetime import datetime, timezone

GENESIS = "carnetruck-genesis-v1"


def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def normalized_iso(dt: datetime) -> str:
    """ISO-8601 estable y agnóstico a la base de datos (UTC, sin offset).

    SQLite pierde el tzinfo al round-trip; Postgres lo conserva. Normalizar
    a UTC-naive garantiza que el hash canónico sea idéntico en ambas.
    """
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.isoformat()


def canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def chain_hash(previous_hash: str | None, payload: dict) -> str:
    prev = previous_hash or sha256_hex(GENESIS)
    return sha256_hex(f"{prev}|{canonical_json(payload)}")


def document_hash(reading_hashes: list[str], extra: dict) -> str:
    """Hash del documento completo: cadena de hashes de lecturas + metadatos.

    Cualquier alteración de una lectura, su orden o los metadatos cambia el hash.
    """
    chain = "".join(reading_hashes)
    return sha256_hex(chain + "|" + canonical_json(extra))
