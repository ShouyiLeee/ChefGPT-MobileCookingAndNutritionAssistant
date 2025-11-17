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
    secret_key: str

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # Database
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 0

    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_service_key: str

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    openai_embedding_model: str = "text-embedding-3-large"

    # Anthropic (Optional)
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-sonnet-20240620"

    # Redis (Optional)
    redis_url: str | None = None

    # File Storage
    max_upload_size: int = 10485760  # 10MB
    allowed_image_extensions: List[str] = ["jpg", "jpeg", "png", "webp"]
    upload_dir: str = "uploads"

    # CORS
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # Rate Limiting
    rate_limit_per_minute: int = 60

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Vision API
    vision_model: str = "gpt-4-vision-preview"
    vision_max_tokens: int = 300

    # RAG Settings
    embedding_dimension: int = 3072
    vector_search_limit: int = 10
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Celery (Optional)
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None


# Global settings instance
settings = Settings()
