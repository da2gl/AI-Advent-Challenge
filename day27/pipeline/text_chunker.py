"""Text chunking utilities for splitting documents into smaller pieces."""

from dataclasses import dataclass
from typing import List
from datetime import datetime


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""
    text: str
    source: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: dict


class TextChunker:
    """Split text into overlapping chunks."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        """Initialize text chunker.

        Args:
            chunk_size: Target size of each chunk in characters
            overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

        if overlap >= chunk_size:
            raise ValueError("Overlap must be less than chunk_size")

    def chunk_document(self, document, additional_metadata: dict = None) -> List[TextChunk]:
        """Chunk a document into smaller pieces.

        Args:
            document: Document object with content and metadata
            additional_metadata: Additional metadata to add to each chunk

        Returns:
            List of TextChunk objects
        """
        if not document.content or not document.content.strip():
            return []

        # Prepare base metadata
        base_metadata = {
            'source': document.source,
            'file_type': document.file_type,
            'file_size': document.size,
            'indexed_at': datetime.now().isoformat()
        }

        if additional_metadata:
            base_metadata.update(additional_metadata)

        # Split into chunks
        chunks = []
        text = document.content
        start = 0
        chunk_index = 0

        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size

            # If this is not the last chunk, try to break at sentence boundary
            if end < len(text):
                end = self._find_break_point(text, start, end)

            # Extract chunk text
            chunk_text = text[start:end].strip()

            # Skip empty chunks
            if chunk_text:
                chunk_metadata = base_metadata.copy()
                chunk_metadata['chunk_index'] = chunk_index
                chunk_metadata['total_chars'] = len(chunk_text)

                chunks.append(TextChunk(
                    text=chunk_text,
                    source=document.source,
                    chunk_index=chunk_index,
                    start_char=start,
                    end_char=end,
                    metadata=chunk_metadata
                ))

                chunk_index += 1

            # Move start position (accounting for overlap)
            start = end - self.overlap

            # Avoid infinite loop if chunk is too small
            if start <= 0 or end >= len(text):
                break

        return chunks

    def _find_break_point(self, text: str, start: int, end: int) -> int:
        """Find a good breaking point near the end position.

        Tries to break at sentence boundaries, then word boundaries.

        Args:
            text: Full text
            start: Start position of current chunk
            end: Desired end position

        Returns:
            Adjusted end position
        """
        # Look ahead a bit to find sentence end
        search_end = min(end + 100, len(text))
        chunk = text[start:search_end]

        # Try to find sentence boundaries (. ! ?)
        sentence_endings = ['.', '!', '?', '\n\n']
        best_pos = end - start

        for ending in sentence_endings:
            # Find the last occurrence of the ending before the target position
            pos = chunk.rfind(ending, 0, end - start + 20)
            if pos != -1 and pos > (end - start) * 0.7:  # At least 70% of chunk size
                best_pos = pos + 1
                break

        # If no good sentence boundary, try word boundary
        if best_pos == end - start:
            # Look for last space before end
            pos = chunk.rfind(' ', 0, end - start)
            if pos != -1 and pos > (end - start) * 0.8:  # At least 80% of chunk size
                best_pos = pos

        return start + best_pos

    def chunk_multiple_documents(self, documents: List, additional_metadata: dict = None) -> List[TextChunk]:
        """Chunk multiple documents.

        Args:
            documents: List of Document objects
            additional_metadata: Additional metadata to add to each chunk

        Returns:
            List of all TextChunk objects
        """
        all_chunks = []

        for doc in documents:
            chunks = self.chunk_document(doc, additional_metadata)
            all_chunks.extend(chunks)

        return all_chunks

    def get_stats(self, chunks: List[TextChunk]) -> dict:
        """Get statistics about chunks.

        Args:
            chunks: List of TextChunk objects

        Returns:
            Dictionary with statistics
        """
        if not chunks:
            return {
                'total_chunks': 0,
                'total_chars': 0,
                'avg_chunk_size': 0,
                'min_chunk_size': 0,
                'max_chunk_size': 0,
                'sources': 0
            }

        chunk_sizes = [len(chunk.text) for chunk in chunks]
        sources = set(chunk.source for chunk in chunks)

        return {
            'total_chunks': len(chunks),
            'total_chars': sum(chunk_sizes),
            'avg_chunk_size': sum(chunk_sizes) // len(chunks),
            'min_chunk_size': min(chunk_sizes),
            'max_chunk_size': max(chunk_sizes),
            'sources': len(sources)
        }
