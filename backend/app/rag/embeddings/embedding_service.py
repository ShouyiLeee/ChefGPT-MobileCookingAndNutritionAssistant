"""Embedding service for generating text embeddings."""
from typing import List
import asyncio
from openai import AsyncOpenAI
from app.core.config import settings
from loguru import logger


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self):
        """Initialize the embedding service."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_embedding_model
        self.dimension = settings.embedding_dimension
        self.batch_size = 100  # Process embeddings in batches

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector
        """
        try:
            # Clean and truncate text if needed (model has token limits)
            cleaned_text = self._clean_text(text)

            response = await self.client.embeddings.create(
                model=self.model,
                input=cleaned_text,
            )

            embedding = response.data[0].embedding

            # Verify dimension
            if len(embedding) != self.dimension:
                logger.warning(
                    f"Embedding dimension mismatch: expected {self.dimension}, got {len(embedding)}"
                )

            return embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = []

        # Process in batches to avoid rate limits
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            batch_embeddings = await self._generate_batch(batch)
            embeddings.extend(batch_embeddings)

            # Small delay to respect rate limits
            if i + self.batch_size < len(texts):
                await asyncio.sleep(0.1)

        return embeddings

    async def _generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        try:
            cleaned_texts = [self._clean_text(text) for text in texts]

            response = await self.client.embeddings.create(
                model=self.model,
                input=cleaned_texts,
            )

            return [data.embedding for data in response.data]

        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise

    def _clean_text(self, text: str) -> str:
        """
        Clean and prepare text for embedding.

        Args:
            text: Input text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = " ".join(text.split())

        # Truncate if too long (approximate token limit)
        # OpenAI's text-embedding-3-large supports up to 8191 tokens
        # Rough estimate: 1 token ≈ 4 characters
        max_chars = 8191 * 4
        if len(text) > max_chars:
            text = text[:max_chars]
            logger.warning(f"Text truncated to {max_chars} characters")

        return text

    async def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
    ) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0 to 1)
        """
        import numpy as np

        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Compute cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))


# Global embedding service instance
embedding_service = EmbeddingService()
