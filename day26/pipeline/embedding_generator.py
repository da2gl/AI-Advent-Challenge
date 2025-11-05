"""Embedding generation using Gemini API."""

import time
from typing import List, Optional
import requests


class EmbeddingGenerator:
    """Generate embeddings using Gemini text-embedding-004 model."""

    EMBEDDING_MODEL = "text-embedding-004"
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    EMBEDDING_DIMENSION = 768

    def __init__(self, api_key: str, batch_size: int = 100):
        """Initialize embedding generator.

        Args:
            api_key: Google AI API key
            batch_size: Number of texts to process in one batch (max 100)
        """
        self.api_key = api_key
        self.batch_size = min(batch_size, 100)  # Gemini API limit
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })

    def generate_embedding(self, text: str, retry_count: int = 3) -> Optional[List[float]]:
        """Generate embedding for a single text.

        Args:
            text: Input text
            retry_count: Number of retries on failure

        Returns:
            Embedding vector (768 dimensions) or None on failure
        """
        url = f"{self.BASE_URL}/{self.EMBEDDING_MODEL}:embedContent"
        params = {"key": self.api_key}

        payload = {
            "model": f"models/{self.EMBEDDING_MODEL}",
            "content": {
                "parts": [{"text": text}]
            }
        }

        for attempt in range(retry_count):
            try:
                response = self.session.post(
                    url,
                    params=params,
                    json=payload,
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    embedding = result.get("embedding", {}).get("values", [])
                    return embedding

                elif response.status_code == 429:  # Rate limit
                    wait_time = (attempt + 1) * 2
                    print(f"Rate limit hit, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                else:
                    print(f"API error ({response.status_code}): {response.text}")
                    return None

            except requests.exceptions.Timeout:
                print(f"Timeout on attempt {attempt + 1}/{retry_count}")
                if attempt < retry_count - 1:
                    time.sleep(1)
                    continue
                return None

            except requests.exceptions.RequestException as e:
                print(f"Request error: {str(e)}")
                return None

            except Exception as e:
                print(f"Unexpected error: {str(e)}")
                return None

        return None

    def generate_embeddings_batch(self, texts: List[str], retry_count: int = 3) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts in batch.

        Args:
            texts: List of input texts
            retry_count: Number of retries on failure

        Returns:
            List of embedding vectors (or None for failed items)
        """
        url = f"{self.BASE_URL}/{self.EMBEDDING_MODEL}:batchEmbedContents"
        params = {"key": self.api_key}

        # Build batch request
        requests_data = [
            {
                "model": f"models/{self.EMBEDDING_MODEL}",
                "content": {"parts": [{"text": text}]}
            }
            for text in texts
        ]

        payload = {"requests": requests_data}

        for attempt in range(retry_count):
            try:
                response = self.session.post(
                    url,
                    params=params,
                    json=payload,
                    timeout=60
                )

                if response.status_code == 200:
                    result = response.json()
                    embeddings = []

                    for emb_data in result.get("embeddings", []):
                        embedding = emb_data.get("values", [])
                        embeddings.append(embedding if embedding else None)

                    return embeddings

                elif response.status_code == 429:  # Rate limit
                    wait_time = (attempt + 1) * 2
                    print(f"Rate limit hit, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                else:
                    print(f"Batch API error ({response.status_code}): {response.text}")
                    return [None] * len(texts)

            except requests.exceptions.Timeout:
                print(f"Batch timeout on attempt {attempt + 1}/{retry_count}")
                if attempt < retry_count - 1:
                    time.sleep(2)
                    continue
                return [None] * len(texts)

            except requests.exceptions.RequestException as e:
                print(f"Batch request error: {str(e)}")
                return [None] * len(texts)

            except Exception as e:
                print(f"Unexpected batch error: {str(e)}")
                return [None] * len(texts)

        return [None] * len(texts)

    def generate_embeddings_for_chunks(self, chunks: List, show_progress: bool = True) -> List[Optional[List[float]]]:
        """Generate embeddings for text chunks with batching.

        Args:
            chunks: List of TextChunk objects
            show_progress: Whether to show progress

        Returns:
            List of embedding vectors
        """
        if not chunks:
            return []

        all_embeddings = []
        total_batches = (len(chunks) + self.batch_size - 1) // self.batch_size

        for batch_idx in range(0, len(chunks), self.batch_size):
            batch_chunks = chunks[batch_idx:batch_idx + self.batch_size]
            batch_texts = [chunk.text for chunk in batch_chunks]

            if show_progress:
                current_batch = (batch_idx // self.batch_size) + 1
                print(f"  Processing batch {current_batch}/{total_batches} ({len(batch_texts)} chunks)...")

            # Generate embeddings for batch
            embeddings = self.generate_embeddings_batch(batch_texts)
            all_embeddings.extend(embeddings)

            # Small delay to avoid rate limits
            if batch_idx + self.batch_size < len(chunks):
                time.sleep(0.5)

        return all_embeddings

    def validate_embeddings(self, embeddings: List[Optional[List[float]]]) -> dict:
        """Validate generated embeddings.

        Args:
            embeddings: List of embedding vectors

        Returns:
            Dictionary with validation statistics
        """
        total = len(embeddings)
        valid = sum(1 for emb in embeddings if emb and len(emb) == self.EMBEDDING_DIMENSION)
        invalid = sum(1 for emb in embeddings if not emb or len(emb) != self.EMBEDDING_DIMENSION)

        return {
            'total': total,
            'valid': valid,
            'invalid': invalid,
            'success_rate': (valid / total * 100) if total > 0 else 0
        }

    def close(self):
        """Close the HTTP session."""
        self.session.close()
