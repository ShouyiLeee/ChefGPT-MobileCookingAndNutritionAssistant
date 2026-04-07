"""
VisionMCPServer — tools for food image analysis.

Tools:
  recognize_ingredients_from_image — identify ingredients from a food image
  analyze_food_image               — full analysis: dish name + ingredients + nutrition estimate
"""
from __future__ import annotations

import base64
import json
import re
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from app.services.llm.base_llm import BaseLLM
    from app.services.tool_registry import ToolRegistry


class VisionMCPServer:
    """MCP server wrapping Gemini Vision capabilities for food images."""

    def __init__(self, llm_provider: "BaseLLM") -> None:
        self._llm = llm_provider

    def register_tools(self, registry: "ToolRegistry") -> None:
        registry.register("recognize_ingredients_from_image", self.recognize_ingredients_from_image)
        registry.register("analyze_food_image", self.analyze_food_image)
        logger.info("VisionMCPServer | registered 2 tools")

    # ── Tools ──────────────────────────────────────────────────────────────────

    async def recognize_ingredients_from_image(
        self,
        image_bytes: bytes,
        image_mime: str = "image/jpeg",
    ) -> dict:
        """
        Identify food ingredients visible in an image.
        Delegates to the existing LLM provider's vision capability.

        Args:
            image_bytes: Raw image bytes (JPEG, PNG, WEBP)
            image_mime: MIME type of the image

        Returns:
            {ingredients: list[str]}
        """
        logger.debug(
            "tool:recognize_ingredients_from_image | size={}KB mime={}",
            round(len(image_bytes) / 1024, 1), image_mime,
        )
        return await self._llm.recognize_ingredients(image_bytes)

    async def analyze_food_image(
        self,
        image_bytes: bytes,
        analysis_type: str = "full",
        image_mime: str = "image/jpeg",
    ) -> dict:
        """
        Perform a detailed analysis of a food image.

        Args:
            image_bytes: Raw image bytes
            analysis_type: What to analyze — "ingredients" | "dish_name" | "nutrition_estimate" | "full"
            image_mime: MIME type of the image

        Returns:
            {dish_name, ingredients, nutrition_estimate, description}
        """
        from google import genai
        from google.genai import types
        from app.core.config import settings

        logger.debug(
            "tool:analyze_food_image | size={}KB type={}",
            round(len(image_bytes) / 1024, 1), analysis_type,
        )

        type_instructions = {
            "ingredients": "Chỉ liệt kê các nguyên liệu nhìn thấy.",
            "dish_name": "Chỉ xác định tên món ăn.",
            "nutrition_estimate": "Chỉ ước tính dinh dưỡng (calories, protein, carbs, fat).",
            "full": "Xác định tên món, nguyên liệu, ước tính dinh dưỡng và mô tả ngắn.",
        }
        instruction = type_instructions.get(analysis_type, type_instructions["full"])

        prompt = f"""Phân tích ảnh thực phẩm. {instruction}

Trả về JSON (không có markdown):
{{
  "dish_name": "tên món ăn hoặc null",
  "ingredients": ["nguyên liệu 1", "nguyên liệu 2"],
  "nutrition_estimate": {{"calories": 350, "protein_g": 20, "carbs_g": 40, "fat_g": 10}} hoặc null,
  "description": "mô tả ngắn hoặc null"
}}"""

        key = settings.gemini_api_key
        if not key:
            return {"error": "No Gemini API key configured"}

        try:
            client = genai.Client(api_key=key)
            image_part = types.Part.from_bytes(data=image_bytes, mime_type=image_mime)
            config = types.GenerateContentConfig()
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, image_part],
                config=config,
            )
            text = re.sub(r"```(?:json)?\s*|\s*```", "", response.text or "").strip()
            result = json.loads(text)
            logger.info(
                "tool:analyze_food_image | type={} dish={} ingredients_count={}",
                analysis_type,
                result.get("dish_name"),
                len(result.get("ingredients", [])),
            )
            return result
        except Exception as e:
            logger.warning("tool:analyze_food_image | error={}", str(e)[:100])
            return {
                "dish_name": None,
                "ingredients": [],
                "nutrition_estimate": None,
                "description": None,
                "error": str(e)[:100],
            }
