"""Gemini API client for chat interactions."""

from dataclasses import dataclass
from typing import List, Dict, Optional

import requests


@dataclass
class GeminiModel:
    """Available Gemini models"""
    # Stable models (recommended for production)
    GEMINI_2_5_PRO = "gemini-2.5-pro"
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite"


class GeminiApiClient:
    """Client for interacting with Gemini API."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str):
        """Initialize the Gemini API client.

        Args:
            api_key: Google AI API key
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })

    def generate_content(
            self,
            prompt: str,
            model: str = GeminiModel.GEMINI_2_5_FLASH,
            conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """Generate content using Gemini API.

        Args:
            prompt: User prompt
            model: Model to use
            conversation_history: Previous conversation messages

        Returns:
            API response as dictionary

        Raises:
            Exception: If API request fails
        """
        url = f"{self.BASE_URL}/{model}:generateContent"
        params = {"key": self.api_key}

        # Build conversation contents
        contents = []
        if conversation_history:
            contents.extend(conversation_history)

        contents.append({
            "parts": [{"text": prompt}],
            "role": "user"
        })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048
            }
        }

        try:
            response = self.session.post(
                url,
                params=params,
                json=payload,
                timeout=60
            )

            # Set encoding explicitly
            response.encoding = 'utf-8'

            # Check status code
            if response.status_code != 200:
                error_text = response.text
                raise Exception(f"API error (status {response.status_code}): {error_text}")

            # Try to parse JSON response
            try:
                return response.json()
            except ValueError as e:
                raise Exception(f"Failed to parse JSON response: {str(e)}\nResponse text: {response.text[:200]}")

        except requests.exceptions.Timeout:
            raise Exception("Request timeout - API took too long to respond")
        except requests.exceptions.ConnectionError:
            raise Exception("Connection error - check your internet connection")
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")

    def extract_text(self, response: Dict) -> str:
        """Extract text from API response.

        Args:
            response: API response dictionary

        Returns:
            Extracted text content
        """
        try:
            candidates = response.get("candidates", [])
            if not candidates:
                return "No response from model"

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                return "No content in response"

            return parts[0].get("text", "Empty response")
        except (KeyError, IndexError) as e:
            return f"Error extracting response: {str(e)}"

    def close(self):
        """Close the HTTP session."""
        self.session.close()
