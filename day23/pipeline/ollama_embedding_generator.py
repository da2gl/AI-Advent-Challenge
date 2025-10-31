"""Embedding generation using Ollama local models."""

import time
from typing import List, Optional
import requests


class OllamaEmbeddingGenerator:
    """Generate embeddings using Ollama local models (mxbai-embed-large)."""

    EMBEDDING_MODEL = "mxbai-embed-large"
    BASE_URL = "http://localhost:11434"
    EMBEDDING_DIMENSION = 1024  # mxbai-embed-large uses 1024 dimensions

    def __init__(self, base_url: str = None, model: str = None, batch_size: int = 100):
        """Initialize Ollama embedding generator.

        Args:
            base_url: Ollama server URL (default: http://localhost:11434)
            model: Model name (default: mxbai-embed-large)
            batch_size: Number of texts to process in one batch
        """
        self.base_url = base_url or self.BASE_URL
        self.model = model or self.EMBEDDING_MODEL
        self.batch_size = batch_size
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })

    def generate_embedding(
        self,
        text: str,
        retry_count: int = 3
    ) -> Optional[List[float]]:
        """Generate embedding for a single text.

        Args:
            text: Input text
            retry_count: Number of retries on failure

        Returns:
            Embedding vector (1024 dimensions) or None on failure
        """
        url = f"{self.base_url}/api/embeddings"

        payload = {
            "model": self.model,
            "prompt": text
        }

        for attempt in range(retry_count):
            try:
                response = self.session.post(
                    url,
                    json=payload,
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    embedding = result.get("embedding", [])
                    return embedding

                else:
                    print(f"Ollama API error ({response.status_code}): {response.text}")
                    return None

            except requests.exceptions.Timeout:
                print(f"Timeout on attempt {attempt + 1}/{retry_count}")
                if attempt < retry_count - 1:
                    time.sleep(1)
                    continue
                return None

            except requests.exceptions.ConnectionError:
                print(f"Connection error: Is Ollama running at {self.base_url}?")
                return None

            except requests.exceptions.RequestException as e:
                print(f"Request error: {str(e)}")
                return None

            except Exception as e:
                print(f"Unexpected error: {str(e)}")
                return None

        return None

    def generate_embeddings_batch(
        self,
        texts: List[str],
        retry_count: int = 3
    ) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts.

        Note: Ollama doesn't have native batch API, so we process sequentially.

        Args:
            texts: List of input texts
            retry_count: Number of retries on failure

        Returns:
            List of embedding vectors (or None for failed items)
        """
        embeddings = []
        for text in texts:
            embedding = self.generate_embedding(text, retry_count)
            embeddings.append(embedding)
            # Small delay to avoid overwhelming local server
            time.sleep(0.01)

        return embeddings

    def generate_embeddings_for_chunks(
        self,
        chunks: List,
        show_progress: bool = True
    ) -> List[Optional[List[float]]]:
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
                print(f"  Processing batch {current_batch}/{total_batches} "
                      f"({len(batch_texts)} chunks)...")

            # Generate embeddings for batch
            embeddings = self.generate_embeddings_batch(batch_texts)
            all_embeddings.extend(embeddings)

        return all_embeddings

    def validate_embeddings(self, embeddings: List[Optional[List[float]]]) -> dict:
        """Validate generated embeddings.

        Args:
            embeddings: List of embedding vectors

        Returns:
            Dictionary with validation statistics
        """
        total = len(embeddings)
        valid = sum(1 for emb in embeddings
                    if emb and len(emb) == self.EMBEDDING_DIMENSION)
        invalid = sum(1 for emb in embeddings
                      if not emb or len(emb) != self.EMBEDDING_DIMENSION)

        return {
            'total': total,
            'valid': valid,
            'invalid': invalid,
            'success_rate': (valid / total * 100) if total > 0 else 0
        }

    def test_connection(self) -> bool:
        """Test connection to Ollama server.

        Returns:
            True if server is accessible and model is available
        """
        try:
            # Check if server is running
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                print(f"Ollama server not responding: {response.status_code}")
                return False

            # Check if model is available
            models = response.json().get("models", [])
            model_names = [m.get("name", "").split(":")[0] for m in models]

            if self.model not in model_names:
                print(f"Model '{self.model}' not found in Ollama.")
                print(f"Available models: {', '.join(model_names)}")
                print(f"\nRun: ollama pull {self.model}")
                return False

            return True

        except requests.exceptions.ConnectionError:
            print(f"Cannot connect to Ollama at {self.base_url}")
            print("Make sure Ollama is running: ollama serve")
            return False

        except Exception as e:
            print(f"Error testing Ollama connection: {str(e)}")
            return False

    def close(self):
        """Close the HTTP session."""
        self.session.close()
