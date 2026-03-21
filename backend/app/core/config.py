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
    # Multiple keys for rotation — comma-separated. Falls back to gemini_api_key if empty.
    gemini_api_keys: str = ""

    # LLM Provider — "gemini" | "openai" | "anthropic"
    llm_provider: str = "gemini"

    # OpenAI (optional — set llm_provider=openai)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Anthropic (optional — set llm_provider=anthropic)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_recipes: int = 3600    # 1 hour
    cache_ttl_meal_plans: int = 1800  # 30 minutes

    # File Storage
    max_upload_size: int = 10_485_760  # 10MB
    allowed_image_extensions: List[str] = ["jpg", "jpeg", "png", "webp"]

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8080"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def gemini_keys_list(self) -> List[str]:
        """Return list of Gemini API keys for rotation."""
        if self.gemini_api_keys:
            return [k.strip() for k in self.gemini_api_keys.split(",") if k.strip()]
        if self.gemini_api_key:
            return [self.gemini_api_key]
        return []

    # MCP — Agentic layer (disabled by default, enable via MCP_ENABLED=true in .env)
    mcp_enabled: bool = False
    # Max tool-call iterations per agent turn (safety cap against runaway loops)
    mcp_max_tool_iterations: int = 5
    # Seconds allowed for CoordinatorAgent intent classification
    mcp_intent_timeout: float = 3.0
    # Seconds allowed per individual tool call
    mcp_tool_timeout: float = 8.0
    # Expose MCP HTTP/SSE endpoint at /mcp for external clients (e.g. Claude Desktop)
    mcp_expose_http_endpoint: bool = False

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/chefgpt.log"


# Global settings instance
settings = Settings()
