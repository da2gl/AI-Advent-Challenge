"""
RAG comparison module for comparing model responses with and without retrieval.
"""

from dataclasses import dataclass
from typing import List, Optional
import time
from core.gemini_client import GeminiApiClient
from pipeline.index_manager import ChromaIndexManager, SearchResult
from pipeline.embedding_generator import EmbeddingGenerator


@dataclass
class ComparisonResult:
    """Result of RAG comparison."""
    question: str
    answer_without_rag: str
    answer_with_rag: str
    retrieved_chunks: List[SearchResult]
    time_without_rag: float
    time_with_rag: float
    tokens_without_rag: int
    tokens_with_rag: int


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
        max_output_tokens: int = 2048
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
        """
        self.gemini_client = gemini_client
        self.index_manager = index_manager
        self.embedding_generator = embedding_generator
        self.model = model
        self.temperature = temperature
        self.top_k = top_k
        self.top_p = top_p
        self.max_output_tokens = max_output_tokens

    def compare(
        self,
        question: str,
        collection_name: str,
        top_k: int = 3,
        system_instruction: Optional[str] = None
    ) -> ComparisonResult:
        """
        Compare responses with and without RAG.

        Args:
            question: Question to ask
            collection_name: ChromaDB collection to search
            top_k: Number of chunks to retrieve
            system_instruction: Optional system instruction for the model

        Returns:
            ComparisonResult with both answers and metadata
        """
        # Answer without RAG
        start_time = time.time()
        answer_without_rag = self._ask_without_rag(question, system_instruction)
        time_without_rag = time.time() - start_time

        # Generate embedding for the question
        question_embedding = self.embedding_generator.generate_embedding(question)

        # Retrieve relevant chunks
        retrieved_chunks = self.index_manager.search(
            query_embedding=question_embedding,
            collection_name=collection_name,
            top_k=top_k
        )

        # Answer with RAG
        start_time = time.time()
        answer_with_rag = self._ask_with_rag(question, retrieved_chunks, system_instruction)
        time_with_rag = time.time() - start_time

        # Estimate token counts (rough approximation: 1 token ≈ 4 characters)
        tokens_without_rag = len(question + answer_without_rag) // 4
        tokens_with_rag = len(question + answer_with_rag) // 4
        for chunk in retrieved_chunks:
            tokens_with_rag += len(chunk.text) // 4

        return ComparisonResult(
            question=question,
            answer_without_rag=answer_without_rag,
            answer_with_rag=answer_with_rag,
            retrieved_chunks=retrieved_chunks,
            time_without_rag=time_without_rag,
            time_with_rag=time_with_rag,
            tokens_without_rag=tokens_without_rag,
            tokens_with_rag=tokens_with_rag
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

Given the context information above, please answer the following question.
If the answer is not in the context, say "I cannot answer based on the provided context."

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
