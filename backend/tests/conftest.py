import os
import sys
from pathlib import Path

# Configurar entorno ANTES de importar la app (settings se cachea).
os.environ["DATABASE_URL"] = "sqlite:///./test_carnetruck.db"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["ALERT_EVAL_MODE"] = "sync"
os.environ["ALERT_COOLDOWN_SECONDS"] = "0"
os.environ["SEED_DEMO"] = "false"
os.environ["AUTO_CREATE_TABLES"] = "false"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, engine, SessionLocal  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_db():
    """Esquema limpio por test con seed data."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Seed demo data for tests
    from app.seed import seed_demo_data
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()

    yield


@pytest.fixture()
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c
