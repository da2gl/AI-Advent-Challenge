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
            conversation_history: Optional[List[Dict]] = None,
            system_instruction: Optional[str] = None,
            temperature: float = 0.7,
            top_k: int = 40,
            top_p: float = 0.95,
            max_output_tokens: int = 2048,
            timeout: int = 60,
            tools: Optional[List[Dict]] = None
    ) -> Dict:
        """Generate content using Gemini API.

        Args:
            prompt: User prompt
            model: Model to use
            conversation_history: Previous conversation messages
            system_instruction: System instruction to guide model behavior
            temperature: Sampling temperature (0.0-2.0). Higher = more creative
            top_k: Top-k sampling parameter
            top_p: Top-p (nucleus) sampling parameter
            max_output_tokens: Maximum tokens in response
            timeout: Request timeout in seconds (default: 60)
            tools: List of function declarations for function calling

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
                "temperature": temperature,
                "topK": top_k,
                "topP": top_p,
                "maxOutputTokens": max_output_tokens
            }
        }

        # Add system instruction if provided
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        # Add tools/function declarations if provided
        if tools:
            payload["tools"] = [{"functionDeclarations": tools}]

        try:
            response = self.session.post(
                url,
                params=params,
                json=payload,
                timeout=timeout
            )

            # Set encoding explicitly
            response.encoding = 'utf-8'

            # Check status code
            if response.status_code != 200:
                error_text = response.text
                raise Exception(f"API error (status {response.status_code}): {error_text}")

            # Try to parse JSON response with explicit UTF-8 decoding
            try:
                import json
                content = response.content.decode('utf-8')
                return json.loads(content)
            except (ValueError, UnicodeDecodeError) as e:
                raise Exception(f"Failed to parse JSON response: {str(e)}\nResponse bytes: {response.content[:200]}")

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

            candidate = candidates[0]

            # Check finish reason
            finish_reason = candidate.get("finishReason")
            if finish_reason and finish_reason != "STOP":
                return self._get_block_reason(candidate, finish_reason)

            content = candidate.get("content", {})
            parts = content.get("parts", [])
            if not parts:
                return self._get_block_reason(candidate, finish_reason or "UNKNOWN")

            return parts[0].get("text", "Empty response")
        except (KeyError, IndexError) as e:
            return f"Error extracting response: {str(e)}"

    def has_function_calls(self, response: Dict) -> bool:
        """Check if response contains function calls.

        Args:
            response: API response dictionary

        Returns:
            True if response contains function calls
        """
        try:
            candidates = response.get("candidates", [])
            if not candidates:
                return False

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])

            for part in parts:
                if "functionCall" in part:
                    return True

            return False
        except (KeyError, IndexError):
            return False

    def extract_function_calls(self, response: Dict) -> List[Dict]:
        """Extract function calls from API response.

        Args:
            response: API response dictionary

        Returns:
            List of function calls with name and arguments
        """
        function_calls = []

        try:
            candidates = response.get("candidates", [])
            if not candidates:
                return function_calls

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])

            for part in parts:
                if "functionCall" in part:
                    func_call = part["functionCall"]
                    function_calls.append({
                        "name": func_call.get("name", ""),
                        "args": func_call.get("args", {})
                    })

        except (KeyError, IndexError):
            pass

        return function_calls

    def _get_block_reason(self, candidate: Dict, finish_reason: str) -> str:
        """Get detailed reason for blocked or empty response.

        Args:
            candidate: Candidate from API response
            finish_reason: Finish reason from candidate

        Returns:
            Detailed error message
        """
        reason_messages = {
            "SAFETY": "Content blocked by safety filters",
            "MAX_TOKENS": "Response stopped: maximum token limit reached",
            "RECITATION": "Content blocked: potential recitation detected",
            "OTHER": "Response stopped for other reasons",
        }

        base_message = reason_messages.get(finish_reason, f"Response stopped: {finish_reason}")

        # Add safety ratings details if available
        if finish_reason == "SAFETY":
            safety_ratings = candidate.get("safetyRatings", [])
            if safety_ratings:
                blocked_categories = []
                for rating in safety_ratings:
                    category = rating.get("category", "UNKNOWN")
                    probability = rating.get("probability", "UNKNOWN")
                    blocked = rating.get("blocked", False)

                    if blocked or probability in ["HIGH", "MEDIUM"]:
                        blocked_categories.append(f"{category} ({probability})")

                if blocked_categories:
                    base_message += f": {', '.join(blocked_categories)}"

        return base_message

    def extract_usage_metadata(self, response: Dict) -> Optional[Dict]:
        """Extract token usage metadata from API response.

        Args:
            response: API response dictionary

        Returns:
            Dictionary with token usage info or None if not available
        """
        try:
            usage = response.get("usageMetadata", {})
            if usage:
                return {
                    "prompt_tokens": usage.get("promptTokenCount", 0),
                    "response_tokens": usage.get("candidatesTokenCount", 0),
                    "total_tokens": usage.get("totalTokenCount", 0)
                }
        except (KeyError, TypeError):
            pass
        return None

    def close(self):
        """Close the HTTP session."""
        self.session.close()
