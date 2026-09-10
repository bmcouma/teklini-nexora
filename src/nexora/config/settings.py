"""Centralized application configuration.

All configuration is sourced from environment variables so that no
secrets or environment-specific values are hard-coded into the codebase.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_name: str = "Teklini Nexora"
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    database_url: str = "sqlite:///./nexora.db"
    redis_url: str = "redis://localhost:6379/0"

    llm_provider: str = "heuristic"
    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_timeout_seconds: float = 20.0

    max_diagnostic_iterations: int = 3
    max_review_iterations: int = 2

    secret_key: str = Field(
        default="",
        validation_alias=AliasChoices("SECRET_KEY", "NEXORA_SECRET_KEY", "secret_key"),
    )
    api_key: str = Field(
        default="",
        validation_alias=AliasChoices("API_KEY", "NEXORA_API_KEY", "nexora_api_key"),
    )
    auth_required: bool = Field(
        default=False,
        validation_alias=AliasChoices("AUTH_REQUIRED", "NEXORA_AUTH_REQUIRED", "nexora_auth_required"),
    )

    @field_validator("secret_key")
    @classmethod
    def _validate_secret_key(cls, value: str) -> str:
        if value:
            return value
        return ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def requires_auth(self) -> bool:
        return self.auth_required and bool(self.api_key)

    def validate_security(self) -> None:
        if self.app_env.lower() in {"production", "prod"} and not self.secret_key:
            raise ValueError("SECRET_KEY must be set when APP_ENV is production")
        if self.auth_required and not self.api_key:
            raise ValueError("NEXORA_API_KEY must be set when NEXORA_AUTH_REQUIRED is true")


@lru_cache
def get_settings() -> Settings:
    return Settings()
