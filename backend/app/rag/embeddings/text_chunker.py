"""Text chunking utilities for RAG pipeline."""
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""

    text: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any]


class TextChunker:
    """Utility for chunking text into smaller pieces."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the text chunker.

        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(
        self,
        text: str,
        metadata: Dict[str, Any] | None = None,
    ) -> List[TextChunk]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to chunks

        Returns:
            List of TextChunk objects
        """
        if not text:
            return []

        metadata = metadata or {}
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending
                sentence_ends = [". ", "! ", "? ", "\n\n"]
                best_break = end

                for i in range(end, max(start + self.chunk_size // 2, end - 100), -1):
                    for ending in sentence_ends:
                        if text[i : i + len(ending)] == ending:
                            best_break = i + len(ending)
                            break
                    if best_break != end:
                        break

                end = best_break

            # Extract chunk
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    TextChunk(
                        text=chunk_text,
                        chunk_index=chunk_index,
                        start_char=start,
                        end_char=end,
                        metadata=metadata.copy(),
                    )
                )
                chunk_index += 1

            # Move to next chunk with overlap
            start = end - self.chunk_overlap

            # Prevent infinite loop
            if start <= 0 or end >= len(text):
                break

        return chunks

    def chunk_by_paragraphs(
        self,
        text: str,
        metadata: Dict[str, Any] | None = None,
    ) -> List[TextChunk]:
        """
        Split text by paragraphs.

        Args:
            text: Text to chunk
            metadata: Optional metadata

        Returns:
            List of TextChunk objects
        """
        metadata = metadata or {}
        paragraphs = text.split("\n\n")
        chunks = []

        start_char = 0
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if para:
                chunks.append(
                    TextChunk(
                        text=para,
                        chunk_index=i,
                        start_char=start_char,
                        end_char=start_char + len(para),
                        metadata=metadata.copy(),
                    )
                )
            start_char += len(para) + 2  # Account for \n\n

        return chunks

    def chunk_by_sentences(
        self,
        text: str,
        max_sentences: int = 5,
        metadata: Dict[str, Any] | None = None,
    ) -> List[TextChunk]:
        """
        Split text into chunks of sentences.

        Args:
            text: Text to chunk
            max_sentences: Maximum sentences per chunk
            metadata: Optional metadata

        Returns:
            List of TextChunk objects
        """
        metadata = metadata or {}

        # Simple sentence splitting
        sentences = self._split_sentences(text)
        chunks = []

        start_char = 0
        for i in range(0, len(sentences), max_sentences):
            chunk_sentences = sentences[i : i + max_sentences]
            chunk_text = " ".join(chunk_sentences)

            chunks.append(
                TextChunk(
                    text=chunk_text,
                    chunk_index=i // max_sentences,
                    start_char=start_char,
                    end_char=start_char + len(chunk_text),
                    metadata=metadata.copy(),
                )
            )

            start_char += len(chunk_text) + 1

        return chunks

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import re

        # Simple sentence splitter
        sentences = re.split(r"[.!?]+\s+", text)
        return [s.strip() for s in sentences if s.strip()]


# Global chunker instance
text_chunker = TextChunker()
