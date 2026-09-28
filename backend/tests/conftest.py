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

# --- SQLite de tests: sin fsync por transacción -------------------------------
# El seed demo encadena ~144 lecturas, cada una con commit. Con el journal
# durable por defecto eso hacía que la suite tardara ~25 min. Este pragma es
# solo para la base efímera de tests (no afecta dev ni producción).
from sqlalchemy import event as _sa_event  # noqa: E402


@_sa_event.listens_for(engine, "connect")
def _fast_sqlite_for_tests(dbapi_connection, connection_record):  # noqa: ANN001
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=MEMORY")
    cursor.execute("PRAGMA synchronous=OFF")
    cursor.close()


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
