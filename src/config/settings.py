"""Crisis-Cost Orchestrator configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Crisis-Cost Orchestrator"
    debug: bool = False

    # Service ports
    affordability_engine_port: int = 8001
    subsidy_orchestrator_port: int = 8002
    audit_ledger_port: int = 8003
    api_gateway_port: int = 8000

    # Affordability engine config
    encounter_frequency_divisor: int = 4
    critical_urgency_multiplier: float = 0.75

    # Audit ledger
    audit_enabled: bool = True

    # PostgreSQL
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "crisiscost"
    db_user: str = "coco"
    db_password: str = "coco_dev_password"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Temporal
    temporal_host: str = "localhost"
    temporal_port: int = 7233
    temporal_namespace: str = "default"

    class Config:
        env_prefix = "COCO_"
        env_file = ".env"


settings = Settings()
