"""Groq API client for text generation."""

from dataclasses import dataclass
from typing import Dict
import requests
import time


@dataclass
class GroqModel:
    """Available Groq models"""
    LLAMA_3_1_8B = "llama-3.1-8b-instant"
    MIXTRAL_8X7B = "mixtral-8x7b-32768"
    LLAMA_3_3_70B = "llama-3.3-70b-versatile"


class GroqClient:
    """Client for interacting with Groq API."""

    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key: str):
        """Initialize the Groq API client.

        Args:
            api_key: Groq API key
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
            model: str = GroqModel.LLAMA_3_1_8B,
            max_tokens: int = 250,
            temperature: float = 0.7
    ) -> Dict:
        """Generate text using Groq API.

        Args:
            prompt: User prompt
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Dictionary with response, tokens, and timing info

        Raises:
            Exception: If API request fails
        """
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        start_time = time.time()

        try:
            response = self.session.post(
                self.BASE_URL,
                json=payload,
                timeout=60
            )

            elapsed_time = time.time() - start_time

            if response.status_code != 200:
                error_text = response.text
                raise Exception(f"API error (status {response.status_code}): {error_text}")

            result = response.json()

            # Extract data from response
            generated_text = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})

            return {
                "text": generated_text,
                "model": model,
                "time_seconds": round(elapsed_time, 2),
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            }

        except requests.exceptions.Timeout:
            raise Exception("Request timeout - API took too long to respond")
        except requests.exceptions.ConnectionError:
            raise Exception("Connection error - check your internet connection")
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")

    def close(self):
        """Close the HTTP session."""
        self.session.close()
