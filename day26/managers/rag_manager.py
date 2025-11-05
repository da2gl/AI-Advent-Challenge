"""RAG (Retrieval-Augmented Generation) manager."""

from pathlib import Path
from rich.console import Console
from core.gemini_client import GeminiApiClient
from pipeline.pipeline_executor import IndexingPipeline
from rag.rag_client import RagClient
from rag.reranker import Reranker


class RagManager:
    """Manages RAG operations - loading, searching, and context formatting."""

    def __init__(
        self,
        console: Console,
        gemini_client: GeminiApiClient,
        indexing_pipeline: IndexingPipeline
    ):
        """
        Initialize RAG manager.

        Args:
            console: Rich console for output
            gemini_client: Gemini API client for reranking
            indexing_pipeline: Indexing pipeline for document management
        """
        self.console = console
        self.gemini_client = gemini_client
        self.indexing_pipeline = indexing_pipeline
        self.rag_client = None

    def _init_rag_client(self):
        """Initialize RAG client with reranking."""
        if self.rag_client is None:
            # Create reranker
            reranker = Reranker(gemini_client=self.gemini_client)

            # Get embedding generator
            embedding_gen = self.indexing_pipeline.embedding_gen

            # Create RAG client
            self.rag_client = RagClient(
                index_manager=self.indexing_pipeline.index_manager,
                embedding_generator=embedding_gen,
                reranker=reranker
            )

    def is_rag_available(self) -> bool:
        """Check if RAG is ready to use.

        Returns:
            True if RAG client is initialized
        """
        if self.rag_client is None:
            self._init_rag_client()
        return self.rag_client is not None

    def search_context(
        self,
        query: str,
        collection_name: str = "default",
        top_k: int = 3
    ):
        """Search for relevant context in indexed documents.

        Args:
            query: Search query
            collection_name: Collection to search in
            top_k: Number of results to return

        Returns:
            List of relevant document chunks
        """
        if not self.is_rag_available():
            return []

        try:
            results = self.rag_client.search(
                question=query,
                collection_name=collection_name,
                top_k=top_k
            )
            return results
        except Exception as e:
            self.console.print(f"⚠ Search error: {str(e)}", style="yellow")
            return []

    def format_context_for_prompt(self, chunks) -> str:
        """Format retrieved chunks for inclusion in prompt.

        Args:
            chunks: List of SearchResult objects

        Returns:
            Formatted context string
        """
        if not chunks:
            return ""

        context_parts = []
        context_parts.append("=== RELEVANT CONTEXT ===\n")

        for i, chunk in enumerate(chunks, 1):
            # Get relevance score
            relevance = 1 - chunk.distance if hasattr(chunk, 'distance') else 0
            rerank_score = chunk.rerank_score if hasattr(chunk, 'rerank_score') else None

            # Format source info
            source = Path(chunk.source).name if hasattr(chunk, 'source') else "unknown"

            context_parts.append(f"\n[Source {i}: {source}")
            if rerank_score is not None:
                context_parts.append(f" | Relevance: {rerank_score:.1f}/10]")
            else:
                context_parts.append(f" | Relevance: {relevance:.2f}]")

            context_parts.append(f"\n{chunk.text}\n")

        context_parts.append("\n=== END CONTEXT ===\n\n")
        context_parts.append("Based on the context above, please answer the following question:\n\n")

        return "".join(context_parts)
