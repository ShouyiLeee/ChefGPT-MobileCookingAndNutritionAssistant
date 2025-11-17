"""LLM client for interacting with AI models."""
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from app.core.config import settings


class LLMClient:
    """Unified client for LLM interactions."""

    def __init__(self):
        """Initialize LLM clients."""
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

        if settings.anthropic_api_key:
            self.anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        else:
            self.anthropic_client = None

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Get chat completion from LLM."""
        model = model or settings.openai_model

        if model.startswith("gpt"):
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""

        elif model.startswith("claude") and self.anthropic_client:
            # Convert messages format for Anthropic
            system_message = next((m["content"] for m in messages if m["role"] == "system"), None)
            user_messages = [m for m in messages if m["role"] != "system"]

            response = await self.anthropic_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message,
                messages=user_messages,
            )
            return response.content[0].text

        else:
            raise ValueError(f"Unsupported model: {model}")

    async def get_embedding(self, text: str, model: Optional[str] = None) -> List[float]:
        """Get text embedding."""
        model = model or settings.openai_embedding_model

        response = await self.openai_client.embeddings.create(
            model=model,
            input=text,
        )
        return response.data[0].embedding

    async def vision_completion(
        self,
        image_url: str,
        prompt: str,
        model: Optional[str] = None,
    ) -> str:
        """Get completion from vision model."""
        model = model or settings.vision_model

        response = await self.openai_client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            max_tokens=settings.vision_max_tokens,
        )
        return response.choices[0].message.content or ""


# Global LLM client instance
llm_client = LLMClient()
