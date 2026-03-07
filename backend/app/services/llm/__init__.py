"""LLM provider factory — selects backend from LLM_PROVIDER env var."""
from loguru import logger

from app.core.config import settings
from app.services.llm.base_llm import BaseLLM


def get_llm_provider() -> BaseLLM:
    """Return the configured LLM provider singleton."""
    provider = settings.llm_provider.lower()

    if provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set — required for LLM_PROVIDER=openai")
        from app.services.llm.openai_llm import OpenAILLM
        logger.info("LLM provider: OpenAI ({})", settings.openai_model)
        return OpenAILLM(api_key=settings.openai_api_key, model=settings.openai_model)

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set — required for LLM_PROVIDER=anthropic")
        from app.services.llm.anthropic_llm import AnthropicLLM
        logger.info("LLM provider: Anthropic ({})", settings.anthropic_model)
        return AnthropicLLM(api_key=settings.anthropic_api_key, model=settings.anthropic_model)

    # Default: Gemini
    from app.services.cache import cache_service
    from app.services.key_manager import GeminiKeyManager
    from app.services.llm.gemini_llm import GeminiLLM

    keys = settings.gemini_keys_list
    if not keys:
        raise RuntimeError(
            "No Gemini API key configured — set GEMINI_API_KEY or GEMINI_API_KEYS"
        )
    key_manager = GeminiKeyManager(api_keys=keys, cache=cache_service)
    logger.info("LLM provider: Gemini ({}, {} key(s))", settings.gemini_model, len(keys))
    return GeminiLLM(key_manager=key_manager, cache=cache_service)


# Singleton — imported by routers
llm_provider: BaseLLM = get_llm_provider()
