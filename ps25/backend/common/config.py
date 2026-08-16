"""Application configuration loaded from environment variables.

Uses Pydantic Settings for type-safe configuration management.
All values are read from .env or the deployment environment.
"""
from __future__ import annotations

import os
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration.

    Frozen decisions from SSOT 01 §3.3, SSOT 03 §15.3, and the
    Architectural Overrides:
      - JWT library: python-jose (python-jose[cryptography])
      - JWT algorithm: HS256
      - JWT secret: from environment variable
      - JWT lifetime: 7 days
    - Phone normalization: strip spaces/dashes, prepend +91 for bare
    10-digit Indian numbers, then validate against the frozen E.164-like
    India-only pattern
      - Phone normalization: strip non-digits, validate 10-digit Indian
      - OTP mock value: 123456 (6 digits, development only)
      - CORS: dev origin localhost:5173, prod via FRONTEND_URL env
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_reload: bool = True

    # --- Database ---
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ps25"

    # --- JWT (python-jose) ---
    # JWT_SECRET is required by the frozen environment-variable registry.
    jwt_secret_key: str = Field(
        ...,
        validation_alias="JWT_SECRET",
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_days: int = 7

    # --- CORS ---
    frontend_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173"

    # --- OTP Mock ---
    mock_otp: str = "123456"

    # --- LLM ---
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api"
    openrouter_model: str = "meta-llama/llama-70b-chat:latest"

    # --- Derived properties ---

    @property
    def cors_origin_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if self.app_env == "development":
            origins.append("http://localhost:5173")
        return origins

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()


def get_settings() -> Settings:
    """Dependency provider for settings."""
    return settings


if __name__ == "__main__":
    print(f"APP_ENV: {settings.app_env}")
    print(f"DATABASE_URL: {settings.database_url}")
    print(f"JWT_ALGORITHM: {settings.jwt_algorithm}")
    print(f"JWT_EXPIRE_DAYS: {settings.jwt_access_token_expire_days}")
    print(f"CORS_ORIGINS: {settings.cors_origin_list}")
    print(f"MOCK_OTP: {settings.mock_otp}")