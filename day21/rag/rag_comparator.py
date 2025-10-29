"""
RAG comparison module for comparing model responses with and without retrieval.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import time
from core.gemini_client import GeminiApiClient
from pipeline.index_manager import ChromaIndexManager, SearchResult
from pipeline.embedding_generator import EmbeddingGenerator
from rag.reranker import Reranker


@dataclass
class ComparisonResult:
    """Result of RAG comparison."""
    question: str
    answer_without_reranking: str
    answer_with_reranking: str
    chunks_without_reranking: List[SearchResult]
    chunks_with_reranking: List[SearchResult]
    time_without_reranking: float
    time_with_reranking: float
    tokens_without_reranking: int
    tokens_with_reranking: int
    reranking_stats: Optional[Dict[str, Any]] = None


class RagComparator:
    """Compare model responses with and without RAG."""

    def __init__(
        self,
        gemini_client: GeminiApiClient,
        index_manager: ChromaIndexManager,
        embedding_generator: EmbeddingGenerator,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.7,
        top_k: int = 40,
        top_p: float = 0.95,
        max_output_tokens: int = 2048,
        use_reranking: bool = True,
        distance_threshold: float = 195.0,
        min_rerank_score: float = 5.0
    ):
        """
        Initialize RAG comparator.

        Args:
            gemini_client: Gemini API client
            index_manager: ChromaDB index manager
            embedding_generator: Embedding generator for queries
            model: Gemini model to use
            temperature: Sampling temperature
            top_k: Top-k sampling
            top_p: Top-p sampling
            max_output_tokens: Maximum output tokens
            use_reranking: Whether to use reranking (default: True)
            distance_threshold: L2 distance threshold for filtering (default: 195.0 for 1024d)
            min_rerank_score: Minimum rerank score to keep (default: 5.0)
        """
        self.gemini_client = gemini_client
        self.index_manager = index_manager
        self.embedding_generator = embedding_generator
        self.model = model
        self.temperature = temperature
        self.top_k = top_k
        self.top_p = top_p
        self.max_output_tokens = max_output_tokens
        self.use_reranking = use_reranking

        # Initialize reranker
        if use_reranking:
            self.reranker = Reranker(
                gemini_client=gemini_client,
                distance_threshold=distance_threshold,
                min_rerank_score=min_rerank_score
            )
        else:
            self.reranker = None

    def compare(
        self,
        question: str,
        collection_name: str,
        top_k: int = 3,
        system_instruction: Optional[str] = None,
        verbose: bool = False
    ) -> ComparisonResult:
        """
        Compare RAG responses WITHOUT reranking vs WITH reranking.

        Args:
            question: Question to ask
            collection_name: ChromaDB collection to search
            top_k: Number of chunks to retrieve (final count)
            system_instruction: Optional system instruction for the model
            verbose: Whether to print detailed reranking statistics

        Returns:
            ComparisonResult comparing filtered vs unfiltered RAG
        """
        # Generate embedding for the question
        question_embedding = self.embedding_generator.generate_embedding(question)

        # Retrieve more candidates for reranking
        initial_k = top_k * 7  # 20 candidates for top_k=3
        candidate_chunks = self.index_manager.search(
            query_embedding=question_embedding,
            collection_name=collection_name,
            top_k=initial_k
        )

        # Path 1: RAG WITHOUT reranking (just top-k from vector search)
        chunks_without_reranking = candidate_chunks[:top_k]
        start_time = time.time()
        answer_without_reranking = self._ask_with_rag(
            question,
            chunks_without_reranking,
            system_instruction
        )
        time_without_reranking = time.time() - start_time

        # Path 2: RAG WITH reranking (distance filtering + Gemini scoring)
        reranking_stats = None
        if self.reranker:
            chunks_with_reranking, reranking_stats = self.reranker.rerank(
                query=question,
                chunks=candidate_chunks,
                top_k=top_k,
                verbose=verbose
            )
        else:
            # Fallback if reranker not initialized
            chunks_with_reranking = chunks_without_reranking

        start_time = time.time()
        answer_with_reranking = self._ask_with_rag(
            question,
            chunks_with_reranking,
            system_instruction
        )
        time_with_reranking = time.time() - start_time

        # Estimate token counts (rough approximation: 1 token ≈ 4 characters)
        tokens_without_reranking = len(question + answer_without_reranking) // 4
        for chunk in chunks_without_reranking:
            tokens_without_reranking += len(chunk.text) // 4

        tokens_with_reranking = len(question + answer_with_reranking) // 4
        for chunk in chunks_with_reranking:
            tokens_with_reranking += len(chunk.text) // 4

        return ComparisonResult(
            question=question,
            answer_without_reranking=answer_without_reranking,
            answer_with_reranking=answer_with_reranking,
            chunks_without_reranking=chunks_without_reranking,
            chunks_with_reranking=chunks_with_reranking,
            time_without_reranking=time_without_reranking,
            time_with_reranking=time_with_reranking,
            tokens_without_reranking=tokens_without_reranking,
            tokens_with_reranking=tokens_with_reranking,
            reranking_stats=reranking_stats
        )

    def _ask_without_rag(self, question: str, system_instruction: Optional[str]) -> str:
        """
        Ask question without RAG (direct to model).

        Args:
            question: Question to ask
            system_instruction: Optional system instruction

        Returns:
            Model response
        """
        try:
            response = self.gemini_client.generate_content(
                prompt=question,
                model=self.model,
                system_instruction=system_instruction,
                temperature=self.temperature,
                top_k=self.top_k,
                top_p=self.top_p,
                max_output_tokens=self.max_output_tokens
            )
            return self.gemini_client.extract_text(response)
        except Exception as e:
            return f"Error: {str(e)}"

    def _ask_with_rag(
        self,
        question: str,
        chunks: List[SearchResult],
        system_instruction: Optional[str]
    ) -> str:
        """
        Ask question with RAG (retrieve context first).

        Args:
            question: Question to ask
            chunks: Retrieved context chunks
            system_instruction: Optional system instruction

        Returns:
            Model response with context
        """
        # Build context from retrieved chunks
        context = "\n\n".join([
            f"[Source: {chunk.source}, Chunk {chunk.chunk_index}]\n{chunk.text}"
            for chunk in chunks
        ])

        # Create prompt with context
        prompt = f"""Context information is below:
---
{context}
---

Based on the context information above, answer the following question.
Use the information from the context to provide a helpful answer.
If you can partially answer using the context, do so and note what's covered.
Only say you cannot answer if the context is completely unrelated to the question.

Question: {question}

Answer:"""

        try:
            response = self.gemini_client.generate_content(
                prompt=prompt,
                model=self.model,
                system_instruction=system_instruction,
                temperature=self.temperature,
                top_k=self.top_k,
                top_p=self.top_p,
                max_output_tokens=self.max_output_tokens
            )
            return self.gemini_client.extract_text(response)
        except Exception as e:
            return f"Error: {str(e)}"

    def batch_compare(
        self,
        questions: List[str],
        collection_name: str,
        top_k: int = 3,
        system_instruction: Optional[str] = None
    ) -> List[ComparisonResult]:
        """
        Compare multiple questions.

        Args:
            questions: List of questions
            collection_name: ChromaDB collection to search
            top_k: Number of chunks to retrieve
            system_instruction: Optional system instruction

        Returns:
            List of ComparisonResults
        """
        results = []
        for question in questions:
            result = self.compare(question, collection_name, top_k, system_instruction)
            results.append(result)
        return results
