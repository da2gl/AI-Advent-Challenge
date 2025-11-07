"""RAG client for searching documents with reranking."""

from typing import List
from pipeline.index_manager import ChromaIndexManager, SearchResult
from pipeline.embedding_generator import EmbeddingGenerator
from .reranker import Reranker


class RagClient:
    """RAG client for document search with mandatory reranking."""

    def __init__(
        self,
        index_manager: ChromaIndexManager,
        embedding_generator: EmbeddingGenerator,
        reranker: Reranker
    ):
        """
        Initialize RAG client.

        Args:
            index_manager: ChromaDB index manager
            embedding_generator: Embedding generator for queries
            reranker: Reranker for scoring and filtering results
        """
        self.index_manager = index_manager
        self.embedding_generator = embedding_generator
        self.reranker = reranker

    def search(
        self,
        question: str,
        collection_name: str = "default",
        top_k: int = 5,
        initial_k: int = 20
    ) -> List[SearchResult]:
        """
        Search for relevant documents with reranking.

        Args:
            question: User question
            collection_name: Collection to search in
            top_k: Number of results to return after reranking
            initial_k: Number of initial candidates to retrieve from ChromaDB

        Returns:
            List of reranked relevant chunks
        """
        # Generate embedding for question
        question_embedding = self.embedding_generator.generate_embedding(question)

        # Search for initial candidates (more than top_k to allow reranker to filter)
        initial_chunks = self.index_manager.search(
            query_embedding=question_embedding,
            collection_name=collection_name,
            top_k=initial_k
        )

        if not initial_chunks:
            return []

        # Rerank the candidates using Gemini
        reranked_chunks, stats = self.reranker.rerank(
            query=question,
            chunks=initial_chunks,
            top_k=top_k,
            verbose=False  # Set to True for debugging
        )

        return reranked_chunks if reranked_chunks else []
