"""HuggingFace Inference API client for text generation."""

from dataclasses import dataclass
from typing import Dict
import requests
import time


@dataclass
class HuggingFaceModel:
    """Available HuggingFace models with Inference API"""
    ARCH_ROUTER_1_5B = "katanemo/Arch-Router-1.5B:hf-inference"
    SMOLLM3_3B = "HuggingFaceTB/SmolLM3-3B:hf-inference"


class HuggingFaceClient:
    """Client for interacting with HuggingFace Inference API."""

    BASE_URL = "https://router.huggingface.co/v1/chat/completions"

    def __init__(self, api_key: str):
        """Initialize the HuggingFace API client.

        Args:
            api_key: HuggingFace API token
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    def generate_text(
            self,
            prompt: str,
            model: str = HuggingFaceModel.SMOLLM3_3B,
            max_new_tokens: int = 250,
            temperature: float = 0.7,
            top_p: float = 0.95,
            max_retries: int = 3,
            retry_delay: int = 30
    ) -> Dict:
        """Generate text using HuggingFace Inference API with retry logic.

        Args:
            prompt: User prompt
            model: Model to use
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds

        Returns:
            Dictionary with response, tokens, and timing info

        Raises:
            Exception: If API request fails after all retries
        """
        url = self.BASE_URL

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_new_tokens,
            "temperature": temperature,
            "top_p": top_p
        }

        last_error = None

        for attempt in range(max_retries):
            start_time = time.time()

            try:
                print(f"  Attempt {attempt + 1}/{max_retries}...")

                response = self.session.post(
                    url,
                    json=payload,
                    timeout=60
                )

                elapsed_time = time.time() - start_time

                # Handle model loading state (503)
                if response.status_code == 503:
                    try:
                        error_data = response.json()
                        if "loading" in error_data.get("error", "").lower():
                            print(f"  Model is loading, waiting {retry_delay}s...")
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay)
                                continue
                    except Exception:
                        pass

                # Handle 404 - model not found or not available
                if response.status_code == 404:
                    error_text = response.text
                    print("  Model not available via Inference API")
                    print(f"  Response: {error_text}")
                    raise Exception("Model not found (404). This model may not support Inference API.")

                # Handle other errors
                if response.status_code != 200:
                    error_text = response.text
                    print(f"  API error (status {response.status_code}): {error_text}")
                    last_error = f"API error (status {response.status_code}): {error_text}"

                    if attempt < max_retries - 1:
                        print(f"  Retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise Exception(last_error)

                result = response.json()

                # Extract generated text from chat completions format
                generated_text = result["choices"][0]["message"]["content"]

                # Extract usage info if available
                usage = result.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", self._estimate_tokens(prompt))
                completion_tokens = usage.get("completion_tokens", self._estimate_tokens(generated_text))
                total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

                return {
                    "text": generated_text,
                    "model": model,
                    "time_seconds": round(elapsed_time, 2),
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                }

            except requests.exceptions.Timeout:
                last_error = "Request timeout - API took too long to respond"
                print(f"  {last_error}")
                if attempt < max_retries - 1:
                    print(f"  Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise Exception(last_error)

            except requests.exceptions.ConnectionError:
                last_error = "Connection error - check your internet connection"
                print(f"  {last_error}")
                if attempt < max_retries - 1:
                    print(f"  Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise Exception(last_error)

            except requests.exceptions.RequestException as e:
                last_error = f"API request failed: {str(e)}"
                print(f"  {last_error}")
                if attempt < max_retries - 1:
                    print(f"  Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise Exception(last_error)

        # If we get here, all retries failed
        raise Exception(f"All {max_retries} attempts failed. Last error: {last_error}")

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation: 1 token ≈ 4 characters).

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        return len(text) // 4

    def close(self):
        """Close the HTTP session."""
        self.session.close()
