"""Reranker for filtering and re-scoring search results."""

from typing import List
import time
from pipeline.index_manager import SearchResult
from core.gemini_client import GeminiApiClient, GeminiModel


class Reranker:
    """Hybrid reranker with distance filtering and Gemini-based relevance scoring.

    The reranking process consists of three stages:
    1. Filter by distance threshold (cosine similarity)
    2. Score remaining candidates using Gemini API
    3. Filter by minimum rerank score and return top-k
    """

    def __init__(
        self,
        gemini_client: GeminiApiClient,
        distance_threshold: float = 195.0,
        min_rerank_score: float = 5.0,
        max_score: float = 10.0
    ):
        """Initialize the reranker.

        Args:
            gemini_client: Gemini API client for scoring
            distance_threshold: Maximum L2 distance to keep (lower = more strict)
                               Default 195.0 for 1024d embeddings (~10-15 candidates)
            min_rerank_score: Minimum rerank score to keep (0-10 scale)
            max_score: Maximum score on the scale (default 10.0)
        """
        self.gemini_client = gemini_client
        self.distance_threshold = distance_threshold
        self.min_rerank_score = min_rerank_score
        self.max_score = max_score

    def rerank(
        self,
        query: str,
        chunks: List[SearchResult],
        top_k: int = 3,
        verbose: bool = False
    ) -> tuple[List[SearchResult], dict]:
        """Rerank search results using hybrid filtering approach.

        Args:
            query: User's question
            chunks: List of candidate chunks from vector search
            top_k: Number of top results to return after reranking
            verbose: Whether to print detailed statistics

        Returns:
            Tuple of (reranked chunks, statistics dict)
        """
        stats = {
            'initial_count': len(chunks),
            'after_distance_filter': 0,
            'after_rerank_filter': 0,
            'final_count': 0,
            'reranking_time': 0.0
        }

        start_time = time.time()

        if verbose:
            print(f"\n{'=' * 60}")
            print("RERANKING PIPELINE")
            print(f"{'=' * 60}")
            print(f"Initial candidates: {len(chunks)}")

        # Stage 1: Filter by distance threshold
        filtered_by_distance = [
            chunk for chunk in chunks
            if chunk.distance < self.distance_threshold
        ]

        stats['after_distance_filter'] = len(filtered_by_distance)

        if verbose:
            print(f"\nStage 1: Distance Filtering (threshold < {self.distance_threshold})")
            print(f"  Kept: {len(filtered_by_distance)} chunks")
            print(f"  Removed: {len(chunks) - len(filtered_by_distance)} chunks")

        # If no chunks pass the filter, return empty with stats
        if not filtered_by_distance:
            stats['reranking_time'] = time.time() - start_time
            if verbose:
                print("\nNo chunks passed distance filter!")
                print(f"Total time: {stats['reranking_time']:.2f}s")
            return [], stats

        # Stage 2: Score with Gemini
        if verbose:
            print("\nStage 2: Gemini Relevance Scoring")

        scored_chunks = []
        for i, chunk in enumerate(filtered_by_distance):
            if verbose:
                print(f"  Scoring chunk {i + 1}/{len(filtered_by_distance)}...", end=" ")

            score = self._score_relevance(query, chunk.text, verbose)
            chunk.rerank_score = score
            scored_chunks.append(chunk)

            if verbose:
                print(f"Score: {score:.1f}/10")

            # Small delay to avoid rate limiting (especially on free tier)
            if i < len(filtered_by_distance) - 1:  # Don't delay after last chunk
                time.sleep(0.1)  # 100ms delay between requests

        # Stage 3: Filter by minimum rerank score
        final_chunks = [
            chunk for chunk in scored_chunks
            if chunk.rerank_score >= self.min_rerank_score
        ]

        stats['after_rerank_filter'] = len(final_chunks)

        if verbose:
            print(f"\nStage 3: Rerank Score Filtering (min score >= {self.min_rerank_score})")
            print(f"  Kept: {len(final_chunks)} chunks")
            print(f"  Removed: {len(scored_chunks) - len(final_chunks)} chunks")

        # Sort by rerank score (higher is better) and take top-k
        final_chunks.sort(key=lambda x: x.rerank_score, reverse=True)
        result = final_chunks[:top_k]

        stats['final_count'] = len(result)
        stats['reranking_time'] = time.time() - start_time

        if verbose:
            print(f"\nFinal Selection: Top-{top_k}")
            print(f"  Selected: {len(result)} chunks")
            for i, chunk in enumerate(result):
                print(f"    {i + 1}. Score: {chunk.rerank_score:.1f}/10, "
                      f"Distance: {chunk.distance:.3f}, "
                      f"Source: {chunk.source}")
            print(f"\nTotal reranking time: {stats['reranking_time']:.2f}s")
            print(f"{'=' * 60}\n")

        return result, stats

    def _score_relevance(self, query: str, document: str, verbose: bool = False) -> float:
        """Score document relevance to query using Gemini.

        Args:
            query: User's question
            document: Document text to score
            verbose: Whether to print errors

        Returns:
            Relevance score (0.0 - 10.0)
        """
        prompt = f"""Rate how relevant this document is to answering the question.

Question: {query}

Document: {document}

Rate from 0 (not relevant at all) to 10 (perfectly relevant and directly answers the question).
Respond with ONLY a single number between 0 and 10. Do not include any explanation or text."""

        try:
            response = self.gemini_client.generate_content(
                prompt=prompt,
                model=GeminiModel.GEMINI_2_5_FLASH_LITE,  # Use Lite to avoid thinking overhead
                temperature=0.0,  # Deterministic scoring
                max_output_tokens=50,
                timeout=30
            )

            # Extract text from response using client's method
            text = self.gemini_client.extract_text(response).strip()

            # Try to parse as float
            try:
                score = float(text)
                # Clamp to valid range
                score = max(0.0, min(self.max_score, score))
                return score
            except ValueError:
                # If parsing fails, try to extract first number
                import re
                numbers = re.findall(r'\d+\.?\d*', text)
                if numbers:
                    score = float(numbers[0])
                    score = max(0.0, min(self.max_score, score))
                    return score

                # If all else fails, return mid-range score
                if verbose:
                    print("(parse error, using 5.0)", end=" ")
                return 5.0

        except Exception as e:
            if verbose:
                print(f"(error: {str(e)[:30]}, using 5.0)", end=" ")
            return 5.0
