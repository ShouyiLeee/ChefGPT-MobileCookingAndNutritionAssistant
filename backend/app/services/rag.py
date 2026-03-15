"""
RAG (Retrieval-Augmented Generation) service for ChefGPT.

Architecture:
  - Community recipe corpus: mocks/recipes.json (30 Vietnamese recipes)
  - Embeddings: Gemini text-embedding-004 (768-dim)
  - Vector store: in-memory numpy array (cosine similarity)
  - Cache: mocks/recipe_embeddings.json (avoids re-generating on every restart)

Usage:
  await rag_service.initialize()          # once in lifespan
  recipes = await rag_service.search("canh chua cá", k=5)
  context = await rag_service.get_context(["cà chua", "trứng"], ["chay"])
"""
import json
import os
import time
from pathlib import Path
from typing import Optional

import numpy as np
from google import genai
from loguru import logger

from app.core.config import settings

_EMBED_MODEL = "text-embedding-005"
_MOCK_DIR = Path(__file__).parent.parent / "mocks"
_RECIPES_PATH = _MOCK_DIR / "recipes.json"
_EMBED_CACHE_PATH = _MOCK_DIR / "recipe_embeddings.json"


class RecipeRAGService:
    """
    In-memory RAG over 30 community recipes.
    Embeddings are generated once (Gemini API) and cached to disk.
    """

    def __init__(self) -> None:
        self._recipes: list[dict] = []
        self._embeddings: Optional[np.ndarray] = None  # shape (N, 768)
        self._ready = False

    # ── Initialization ─────────────────────────────────────────────────────────

    async def initialize(self) -> None:
        """Load recipes + build embedding index. Call once in app lifespan."""
        if not _RECIPES_PATH.exists():
            logger.warning("RAG: recipes.json not found at {}", _RECIPES_PATH)
            return

        with open(_RECIPES_PATH, encoding="utf-8") as f:
            self._recipes = json.load(f)

        logger.info("RAG: loaded {} community recipes", len(self._recipes))

        # Try disk cache first
        if await self._load_cache():
            return

        # Cache miss → generate via Gemini API
        if not settings.gemini_api_key and not settings.gemini_api_keys:
            logger.warning("RAG: no Gemini API key — skipping embedding generation")
            return

        await self._build_index()

    async def _load_cache(self) -> bool:
        """Load cached embeddings from disk. Returns True if valid cache found."""
        if not _EMBED_CACHE_PATH.exists():
            return False
        try:
            with open(_EMBED_CACHE_PATH, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("count") != len(self._recipes):
                logger.info("RAG: cache stale (recipe count mismatch), rebuilding")
                return False
            self._embeddings = np.array(data["embeddings"], dtype=np.float32)
            self._ready = True
            logger.info("RAG: loaded embeddings from cache ({})", _EMBED_CACHE_PATH.name)
            return True
        except Exception as e:
            logger.warning("RAG: failed to load embedding cache: {}", e)
            return False

    async def _build_index(self) -> None:
        """Generate embeddings for all community recipes and cache to disk."""
        logger.info("RAG: generating embeddings for {} recipes via Gemini...", len(self._recipes))
        t0 = time.perf_counter()

        key = settings.gemini_keys_list[0] if settings.gemini_keys_list else settings.gemini_api_key
        client = genai.Client(api_key=key)

        embeddings: list[list[float]] = []
        for recipe in self._recipes:
            text = self._recipe_to_text(recipe)
            try:
                result = await client.aio.models.embed_content(
                    model=_EMBED_MODEL, contents=text
                )
                embeddings.append(result.embeddings[0].values)
            except Exception as e:
                logger.error("RAG: embedding failed for recipe '{}': {}", recipe.get("title"), e)
                # Use zero vector as fallback so index stays aligned
                embeddings.append([0.0] * 768)

        self._embeddings = np.array(embeddings, dtype=np.float32)

        # Save cache
        try:
            _MOCK_DIR.mkdir(parents=True, exist_ok=True)
            with open(_EMBED_CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(
                    {"count": len(self._recipes), "embeddings": self._embeddings.tolist()},
                    f,
                )
            logger.info("RAG: embeddings cached to {}", _EMBED_CACHE_PATH.name)
        except Exception as e:
            logger.warning("RAG: could not write embedding cache: {}", e)

        elapsed = round((time.perf_counter() - t0) * 1000)
        logger.info("RAG: index built in {}ms", elapsed)
        self._ready = True

    # ── Public API ─────────────────────────────────────────────────────────────

    async def search(self, query: str, k: int = 5) -> list[dict]:
        """
        Semantic search over community recipes.
        Returns up to k recipes sorted by cosine similarity descending.
        """
        if not self._ready or self._embeddings is None:
            logger.debug("RAG: not ready, skipping search")
            return []
        if not query.strip():
            return []

        try:
            key = settings.gemini_keys_list[0] if settings.gemini_keys_list else settings.gemini_api_key
            client = genai.Client(api_key=key)
            result = await client.aio.models.embed_content(
                model=_EMBED_MODEL, contents=query
            )
            query_emb = np.array(result.embeddings[0].values, dtype=np.float32)
        except Exception as e:
            logger.warning("RAG: query embedding failed: {}", e)
            return []

        # Cosine similarity: (N,768) @ (768,) / (norm_N * norm_query)
        norms = np.linalg.norm(self._embeddings, axis=1) * np.linalg.norm(query_emb)
        norms = np.where(norms == 0, 1e-9, norms)  # avoid division by zero
        scores = (self._embeddings @ query_emb) / norms

        top_k_idx = int(min(k, len(self._recipes)))
        indices = np.argsort(scores)[::-1][:top_k_idx]

        results = []
        for idx in indices:
            recipe = dict(self._recipes[int(idx)])
            recipe["score"] = round(float(scores[idx]), 4)
            results.append(recipe)

        return results

    def keyword_search(
        self,
        query: str = "",
        cuisine: Optional[str] = None,
        difficulty: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """
        Keyword + filter search over community recipes (no embeddings needed).
        Matches query against title, description, tags, and ingredients.
        """
        q = query.lower().strip()
        results = []
        for r in self._recipes:
            # Apply hard filters first
            if cuisine and r.get("cuisine", "").lower() != cuisine.lower():
                continue
            if difficulty and r.get("difficulty", "").lower() != difficulty.lower():
                continue
            if category and r.get("category", "").lower() != category.lower():
                continue
            # Keyword match
            if q:
                haystack = " ".join([
                    r.get("title", ""),
                    r.get("description", ""),
                    " ".join(r.get("tags", [])),
                    " ".join(r.get("ingredients", [])),
                ]).lower()
                if q not in haystack:
                    continue
            results.append(r)

        return results[offset : offset + limit]

    async def get_context(
        self,
        ingredients: list[str],
        filters: list[str],
        k: int = 3,
    ) -> str:
        """
        Retrieve top-k similar community recipes and format them as LLM context.
        Used to ground Gemini's recipe suggestions with real examples.
        """
        query = f"{', '.join(ingredients)} {' '.join(filters)}".strip()
        recipes = await self.search(query, k=k)
        if not recipes:
            return ""

        lines = ["**Tham khảo công thức cộng đồng (dùng để cải thiện gợi ý):**"]
        for r in recipes:
            ing_preview = ", ".join(r.get("ingredients", [])[:6])
            lines.append(
                f"- **{r['title']}**: {r['description']} "
                f"(nguyên liệu chính: {ing_preview})"
            )
        return "\n".join(lines)

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _recipe_to_text(recipe: dict) -> str:
        """Convert recipe dict to a single searchable string for embedding."""
        parts = [
            recipe.get("title", ""),
            recipe.get("description", ""),
            recipe.get("cuisine", ""),
            recipe.get("category", ""),
            " ".join(recipe.get("tags", [])),
            " ".join(recipe.get("ingredients", [])[:12]),
        ]
        return " | ".join(p for p in parts if p)

    @property
    def ready(self) -> bool:
        return self._ready

    @property
    def recipe_count(self) -> int:
        return len(self._recipes)


# Singleton — initialized in app lifespan
rag_service = RecipeRAGService()
