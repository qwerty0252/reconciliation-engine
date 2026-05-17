from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_env: str = "development"
    secret_key: str = "changeme"
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://bankops:bankops_secret@localhost:5432/bankops_reconciliation"

    # RabbitMQ
    rabbitmq_url: str = "amqp://bankops:bankops_secret@localhost:5672/"
    rabbitmq_exchange: str = "bankops.transactions"
    rabbitmq_queue_ingestion: str = "bankops.ingestion"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Alert channels
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    alert_email_from: str = "alerts@bankops.io"
    alert_email_to: str = "ops@bankops.io"
    slack_webhook_url: str = ""

    # Reconciliation thresholds
    recon_schedule_minutes: int = 5
    recon_settlement_delay_hours: int = 24
    recon_reversal_delay_hours: int = 48
    recon_duplicate_window_seconds: int = 86400

    # Observability
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"


@lru_cache
def get_settings() -> Settings:
    return Settings()
