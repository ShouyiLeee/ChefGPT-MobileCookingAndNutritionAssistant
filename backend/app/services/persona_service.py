"""
PersonaService — Load và quản lý persona templates từ file JSON.
Singleton, được khởi tạo 1 lần khi startup.
"""

import json
from pathlib import Path
from typing import Any

from loguru import logger

PERSONAS_DIR = Path(__file__).parent.parent / "personas"


class PersonaService:
    def __init__(self) -> None:
        self._personas: dict[str, dict[str, Any]] = {}

    def load_all(self) -> None:
        """Đọc tất cả file JSON trong thư mục personas/ vào memory."""
        self._personas.clear()
        if not PERSONAS_DIR.exists():
            logger.warning("Personas directory not found | path={}", PERSONAS_DIR)
            return

        for json_file in sorted(PERSONAS_DIR.glob("*.json")):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                persona_id = data.get("id")
                if not persona_id:
                    logger.warning("Persona file missing 'id' field | file={}", json_file.name)
                    continue
                self._personas[persona_id] = data
                logger.debug("Persona loaded | id={} name={}", persona_id, data.get("name"))
            except Exception as e:
                logger.error("Failed to load persona file | file={} error={}", json_file.name, e)

        logger.info("Persona templates loaded | count={}", len(self._personas))

    def get(self, persona_id: str) -> dict[str, Any]:
        """Trả về full config của 1 persona. Raise ValueError nếu không tìm thấy."""
        if persona_id not in self._personas:
            raise ValueError(f"Persona not found: '{persona_id}'")
        return self._personas[persona_id]

    def list_all(self) -> list[dict[str, Any]]:
        """Trả về list metadata của tất cả personas (không bao gồm 'prompts' block)."""
        result = []
        for p in self._personas.values():
            item = {k: v for k, v in p.items() if k != "prompts"}
            result.append(item)
        return result

    def get_default(self) -> dict[str, Any]:
        """Trả về persona có is_default == true. Fallback: persona đầu tiên."""
        for p in self._personas.values():
            if p.get("is_default"):
                return p
        # Fallback nếu không có default được đánh dấu
        if self._personas:
            return next(iter(self._personas.values()))
        raise RuntimeError("No personas loaded")

    def exists(self, persona_id: str) -> bool:
        return persona_id in self._personas

    def all_ids(self) -> list[str]:
        return list(self._personas.keys())


# Singleton instance
persona_service = PersonaService()
