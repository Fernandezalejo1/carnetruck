"""Tests de edge cases para la cadena de hashes SHA-256."""

from datetime import datetime, timezone

from app.services.integrity_hash import (
    chain_hash,
    document_hash,
    normalized_iso,
    sha256_hex,
)


def test_genesis_hash_is_deterministic():
    """El hash genesis es determinista."""
    h1 = sha256_hex("carnetruck-genesis-v1")
    h2 = sha256_hex("carnetruck-genesis-v1")
    assert h1 == h2
    assert len(h1) == 64


def test_chain_hash_order_matters():
    """El orden de los datos afecta el hash."""
    payload_a = {"temp": 5.0, "ts": "2026-01-01T00:00:00"}
    payload_b = {"temp": 5.0, "ts": "2026-01-01T00:00:01"}
    h1 = chain_hash(None, payload_a)
    h2 = chain_hash(None, payload_b)
    assert h1 != h2


def test_chain_hash_is_deterministic():
    """El mismo payload produce el mismo hash."""
    payload = {"temp": 5.0, "ts": "2026-01-01T00:00:00"}
    h1 = chain_hash(None, payload)
    h2 = chain_hash(None, payload)
    assert h1 == h2


def test_chain_hash_changes_with_previous():
    """Un hash diferente en la cadena produce un hash diferente."""
    payload = {"temp": 5.0}
    h1 = chain_hash("abc123", payload)
    h2 = chain_hash("def456", payload)
    assert h1 != h2


def test_chain_hash_tamper_detection():
    """Si se altera una lectura, el hash cambia."""
    reading1 = {"temp": 5.0, "ts": "2026-01-01T00:00:00"}
    reading2 = {"temp": 6.0, "ts": "2026-01-01T00:30:00"}
    reading2_tampered = {"temp": 99.0, "ts": "2026-01-01T00:30:00"}

    h1 = chain_hash(None, reading1)
    h2 = chain_hash(h1, reading2)
    h2_tampered = chain_hash(h1, reading2_tampered)
    assert h2 != h2_tampered


def test_document_hash_includes_metadata():
    """El hash del documento incluye los metadatos."""
    hashes = ["abc123", "def456"]
    meta1 = {"shipment_id": 1, "generated": "2026-01-01"}
    meta2 = {"shipment_id": 2, "generated": "2026-01-01"}
    h1 = document_hash(hashes, meta1)
    h2 = document_hash(hashes, meta2)
    assert h1 != h2


def test_document_hash_empty_readings():
    """El hash del documento funciona con lecturas vacías."""
    h = document_hash([], {"test": True})
    assert len(h) == 64


def test_normalized_iso_utc_naive():
    """normalized_iso convierte a UTC naive."""
    dt_with_tz = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = normalized_iso(dt_with_tz)
    assert result == "2026-01-01T12:00:00"


def test_normalized_iso_different_timezones():
    """Timezones diferentes pero mismo instante producen el mismo resultado."""
    from datetime import timedelta, timezone as tz
    # 15:00 UTC = mismo instante que 18:00 UTC+3
    dt_utc = datetime(2026, 1, 1, 15, 0, 0, tzinfo=timezone.utc)
    dt_plus3 = datetime(2026, 1, 1, 18, 0, 0, tzinfo=tz(timedelta(hours=3)))
    r1 = normalized_iso(dt_utc)
    r2 = normalized_iso(dt_plus3)
    assert r1 == r2
    assert r1 == "2026-01-01T15:00:00"


def test_canonical_json_sorted_keys():
    """canonical_json ordena las claves."""
    from app.services.integrity_hash import canonical_json
    payload = {"z": 1, "a": 2, "m": 3}
    result = canonical_json(payload)
    assert result == '{"a":2,"m":3,"z":1}'
