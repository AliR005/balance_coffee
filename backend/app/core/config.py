from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://balance:balance@localhost:5432/balance"
    test_database_url: str = "postgresql+asyncpg://balance:balance@localhost:5432/balance_test"
    default_currency: str = "RUB"
    cors_origins: str = "http://localhost:5173"
    staff_token_secret: str = "dev-only-change-me"
    staff_token_ttl_hours: int = 12
    log_level: str = "INFO"


settings = Settings()
