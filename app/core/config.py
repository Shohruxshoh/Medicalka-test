"""Application configuration loaded from environment variables / .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All app settings. Values are read from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Mini Social Network API"
    debug: bool = False

    # PostgreSQL (async driver used by the application)
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/social"

    # Redis (used as cache and as the Celery broker)
    redis_url: str = "redis://redis:6379/0"

    # JWT / security
    jwt_secret: str = "dev-secret-change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Email verification
    verification_token_expire_hours: int = 24
    unverified_user_ttl_hours: int = 48

    # Views buffering (Redis write-behind)
    view_dedup_ttl_seconds: int = 3600
    view_flush_interval_seconds: int = 10

    # Post lifetime (Bonus): auto-delete posts older than this many days
    post_ttl_days: int = 30

    # Login rate limiting (Bonus)
    login_max_attempts: int = 5
    login_block_seconds: int = 300


# Single shared settings instance, imported across the app.
settings = Settings()
