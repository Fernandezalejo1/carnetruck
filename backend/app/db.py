from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import get_settings

settings = get_settings()

_engine_kwargs = {"pool_pre_ping": True}
if settings.database_url.startswith("sqlite"):
    # SQLite (tests / dev sin Docker): permitir acceso multi-hilo y activar FKs.
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.database_url, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_timescale(session) -> None:
    """Convierte la tabla `readings` en una hypertable de TimescaleDB (best-effort).

    Solo aplica cuando la base es PostgreSQL con la extensión disponible; en caso
    contrario (Postgres vanilla, SQLite) no hace nada y el sistema funciona igual.
    """
    if not settings.database_url.startswith("postgres"):
        return
    try:
        session.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
        session.execute(
            text(
                "SELECT create_hypertable('readings', 'timestamp',"
                " if_not_exists => TRUE, migrate_data => TRUE)"
            )
        )
        session.commit()
    except Exception:
        session.rollback()
