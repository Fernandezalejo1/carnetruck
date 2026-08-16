from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Carnetruck API"
    api_prefix: str = "/api/v1"

    # Base de datos
    database_url: str = "postgresql+psycopg://carnetruck:carnetruck@localhost:5432/carnetruck"

    # Seguridad
    jwt_secret: str = "cambia-este-secreto-en-produccion"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 720

    # Comportamiento
    auto_create_tables: bool = True
    seed_demo: bool = False
    alert_eval_mode: str = "sync"  # sync | celery
    alert_cooldown_seconds: int = 600
    missing_signal_threshold_minutes: int = 60
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Celery / Redis
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # Notificaciones (n8n u otro webhook)
    n8n_webhook_url: str = ""
    n8n_webhook_token: str = ""

    # MQTT (opcional)
    mqtt_url: str = ""
    mqtt_topic: str = "carnetruck/+/readings"

    # PDF
    pdf_engine: str = "auto"  # auto | weasyprint | simple

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
