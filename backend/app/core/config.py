"""Application configuration."""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "ChefGPT"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    secret_key: str = "change-this-secret-key"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # Database (SQLite for dev — set postgresql:// URL for production)
    database_url: str = "sqlite:///./chefgpt.db"

    # Supabase (Auth only)
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_key: str = ""

    # JWT
    jwt_secret_key: str = "change-this-jwt-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Gemini 2.5 Flash (Google AI Studio — free tier)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # File Storage
    max_upload_size: int = 10_485_760  # 10MB
    allowed_image_extensions: List[str] = ["jpg", "jpeg", "png", "webp"]

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8080"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    # Logging
    log_level: str = "INFO"


# Global settings instance
settings = Settings()
