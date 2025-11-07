"""Ollama API client for local LLM chat interactions."""

from dataclasses import dataclass
from typing import List, Dict, Optional
import json

import requests


@dataclass
class OllamaModel:
    """Available Ollama models (common ones)"""
    QWEN_CODER = "hhao/qwen2.5-coder-tools:7b"


class OllamaApiClient:
    """Client for interacting with local Ollama API."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        """Initialize the Ollama API client.

        Args:
            base_url: Ollama server base URL (default: http://localhost:11434)
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })

    def generate_content(
            self,
            prompt: str,
            model: str = OllamaModel.QWEN_CODER,
            conversation_history: Optional[List[Dict]] = None,
            system_instruction: Optional[str] = None,
            temperature: float = 0.7,
            top_k: int = 40,
            top_p: float = 0.95,
            max_output_tokens: int = 2048,
            timeout: int = 120,
            tools: Optional[List[Dict]] = None
    ) -> Dict:
        """Generate content using Ollama API.

        Args:
            prompt: User prompt
            model: Model to use (e.g., "llama3.2")
            conversation_history: Previous conversation messages
            system_instruction: System instruction to guide model behavior
            temperature: Sampling temperature (0.0-2.0). Higher = more creative
            top_k: Top-k sampling parameter
            top_p: Top-p (nucleus) sampling parameter
            max_output_tokens: Maximum tokens in response
            timeout: Request timeout in seconds (default: 120)
            tools: List of function declarations for function calling

        Returns:
            API response as dictionary (in Gemini-like format for compatibility)

        Raises:
            Exception: If API request fails
        """
        url = f"{self.base_url}/api/chat"

        # Convert conversation history to Ollama format
        messages = []

        # Add system message if provided
        if system_instruction:
            messages.append({
                "role": "system",
                "content": system_instruction
            })

        # Add conversation history
        if conversation_history:
            for msg in conversation_history:
                role = msg.get("role", "user")
                parts = msg.get("parts", [])

                # Handle function responses specially for Ollama
                if role == "function":
                    # Ollama expects role="tool" for function/tool responses
                    for part in parts:
                        if "functionResponse" in part:
                            func_resp = part["functionResponse"]
                            response_content = func_resp.get("response", {})

                            # Convert CallToolResult to dict if needed
                            if hasattr(response_content, '__dict__'):
                                content_list = ([{'type': c.type, 'text': c.text}
                                                 for c in response_content.content]
                                                if hasattr(response_content, 'content') else [])
                                response_content = {'content': content_list}

                            messages.append({
                                "role": "tool",
                                "content": json.dumps(response_content)
                            })
                    continue

                # Extract text content and function calls from parts
                text_parts = []
                tool_calls_data = []

                for part in parts:
                    if "text" in part:
                        text_parts.append(part["text"])
                    elif "functionCall" in part:
                        # Store function call data for Ollama format
                        func_call = part["functionCall"]
                        tool_calls_data.append({
                            "type": "function",
                            "function": {
                                "name": func_call.get("name", ""),
                                "arguments": func_call.get("args", {})
                            }
                        })

                # Map Gemini roles to Ollama roles
                ollama_role = "assistant" if role == "model" else role

                # Build message
                if text_parts or tool_calls_data:
                    message = {
                        "role": ollama_role,
                        "content": "\n".join(text_parts) if text_parts else ""
                    }
                    # Add tool_calls if present
                    if tool_calls_data:
                        message["tool_calls"] = tool_calls_data

                    messages.append(message)

        # Add current user prompt if provided
        if prompt:
            messages.append({
                "role": "user",
                "content": prompt
            })

        # Build payload
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_k": top_k,
                "top_p": top_p,
                "num_predict": max_output_tokens
            }
        }

        # Convert Gemini function declarations to Ollama tools format
        if tools:
            ollama_tools = []
            for tool in tools:
                ollama_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.get("name", ""),
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                }
                ollama_tools.append(ollama_tool)
            payload["tools"] = ollama_tools

        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=timeout
            )

            # Set encoding explicitly
            response.encoding = 'utf-8'

            # Check status code
            if response.status_code != 200:
                error_text = response.text
                raise Exception(f"Ollama API error (status {response.status_code}): {error_text}")

            # Parse Ollama response and convert to Gemini-like format
            ollama_response = response.json()

            # Convert to Gemini-compatible format
            return self._convert_to_gemini_format(ollama_response)

        except requests.exceptions.Timeout:
            raise Exception("Request timeout - Ollama took too long to respond")
        except requests.exceptions.ConnectionError:
            raise Exception("Connection error - is Ollama running? Try: ollama serve")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama API request failed: {str(e)}")

    def _convert_to_gemini_format(self, ollama_response: Dict) -> Dict:
        """Convert Ollama response to Gemini-compatible format.

        Args:
            ollama_response: Response from Ollama API

        Returns:
            Response in Gemini format for compatibility
        """
        message = ollama_response.get("message", {})
        content_text = message.get("content", "")
        tool_calls = message.get("tool_calls", [])

        # Build parts array
        parts = []

        # If no native tool calls, try to parse JSON from text (for Qwen and similar)
        if not tool_calls and content_text:
            parsed_tool_call = self._parse_tool_call_from_text(content_text)
            if parsed_tool_call:
                # Found a tool call in text
                parts.append({
                    "functionCall": {
                        "name": parsed_tool_call.get("name", ""),
                        "args": parsed_tool_call.get("arguments", {})
                    }
                })
            else:
                # No tool call found, just text
                parts.append({"text": content_text})
        else:
            # Add text if present (Llama 3.2 returns empty content when calling tools)
            if content_text:
                parts.append({"text": content_text})

            # Add function calls if present (native Ollama tool calls)
            if tool_calls:
                for tool_call in tool_calls:
                    function = tool_call.get("function", {})
                    # Parse arguments if it's a string
                    args = function.get("arguments", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except json.JSONDecodeError:
                            args = {}

                    parts.append({
                        "functionCall": {
                            "name": function.get("name", ""),
                            "args": args
                        }
                    })

        # Build Gemini-like response structure
        gemini_response = {
            "candidates": [
                {
                    "content": {
                        "parts": parts,
                        "role": "model"
                    },
                    "finishReason": "STOP"
                }
            ],
            "usageMetadata": {
                "promptTokenCount": ollama_response.get("prompt_eval_count", 0),
                "candidatesTokenCount": ollama_response.get("eval_count", 0),
                "totalTokenCount": ollama_response.get("prompt_eval_count", 0) + ollama_response.get("eval_count", 0)
            }
        }

        return gemini_response

    def _parse_tool_call_from_text(self, text: str) -> Optional[Dict]:
        """Parse tool call JSON from text content (for Qwen and similar models).

        Args:
            text: Text content that may contain JSON tool call

        Returns:
            Dict with name and arguments if found, None otherwise
        """
        import re

        # Try to find JSON in code blocks (```json ... ```)
        json_block_match = re.search(r'```(?:json)?\s*\n?(\{[^`]+\})\s*\n?```', text, re.DOTALL)
        if json_block_match:
            json_str = json_block_match.group(1)
        else:
            # Try to find raw JSON object
            json_match = re.search(r'(\{[^{}]*"name"[^{}]*"arguments"[^{}]*\})', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                return None

        try:
            tool_call = json.loads(json_str)
            if "name" in tool_call and "arguments" in tool_call:
                return tool_call
        except json.JSONDecodeError:
            pass

        return None

    def extract_text(self, response: Dict) -> str:
        """Extract text from API response.

        Args:
            response: API response dictionary (in Gemini format)

        Returns:
            Extracted text content
        """
        try:
            candidates = response.get("candidates", [])
            if not candidates:
                return "No response from model"

            candidate = candidates[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])

            if not parts:
                return "Empty response"

            # Extract and concatenate text from all parts
            text_parts = []
            for part in parts:
                if "text" in part:
                    text_parts.append(part["text"])

            if text_parts:
                return "".join(text_parts)
            else:
                return "Empty response"

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

    def is_available(self) -> bool:
        """Check if Ollama server is available.

        Returns:
            True if Ollama is running and accessible
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """List available Ollama models.

        Returns:
            List of model names
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return [model.get("name", "") for model in models]
        except Exception:
            pass
        return []
