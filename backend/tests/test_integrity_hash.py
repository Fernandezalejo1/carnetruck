from app.services.integrity_hash import canonical_json, chain_hash, document_hash, sha256_hex


def test_chain_deterministic():
    payload = {"temperatura": -18.0, "shipment_id": 1, "timestamp": "2026-01-01T00:00:00+00:00"}
    h1 = chain_hash(None, payload)
    h2 = chain_hash(None, payload)
    assert h1 == h2


def test_chain_genesis_and_linkage():
    p1 = {"a": 1}
    p2 = {"a": 2}
    first = chain_hash(None, p1)
    second = chain_hash(first, p2)
    # Distinto payload sobre el mismo prev → distinto hash.
    assert chain_hash(first, {"a": 3}) != second
    # El hash de una lectura incluye el hash anterior.
    assert sha256_hex(f"{first}|{canonical_json(p2)}") == second


def test_canonical_json_order_independent():
    assert canonical_json({"b": 2, "a": 1}) == canonical_json({"a": 1, "b": 2})


def test_document_hash_changes_with_readings():
    h1 = document_hash(["a" * 64, "b" * 64], {"n": 2})
    h2 = document_hash(["a" * 64, "c" * 64], {"n": 2})
    h3 = document_hash(["a" * 64, "b" * 64], {"n": 3})
    assert h1 != h2
    assert h1 != h3
    assert len(h1) == 64
