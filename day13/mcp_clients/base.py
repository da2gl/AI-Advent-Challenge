"""Base MCP client interface using FastMCP."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseMCPClient(ABC):
    """Abstract base class for MCP clients using FastMCP."""

    def __init__(self, name: str):
        """Initialize MCP client.

        Args:
            name: Human-readable name for this client
        """
        self.name = name
        self.client = None
        self.client_context = None
        self.tools: List[Any] = []
        self.connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to MCP server.

        Returns:
            True if connection successful

        Raises:
            Exception: If connection fails
        """
        pass

    async def disconnect(self):
        """Disconnect from MCP server."""
        self.connected = False
        if self.client_context is not None:
            try:
                await self.client_context.__aexit__(None, None, None)
            except Exception:
                pass
            finally:
                self.client_context = None
                self.client = None
        self.tools = []

    def get_tools(self) -> List[Any]:
        """Get list of available tools.

        Returns:
            List of MCP tools
        """
        return self.tools

    def get_tools_as_dict(self) -> List[Dict[str, Any]]:
        """Get tools as dictionaries for easier processing.

        Returns:
            List of tool dictionaries with name, description, and schema
        """
        tools_dict = []
        for tool in self.tools:
            desc = ""
            if hasattr(tool, 'description'):
                desc = tool.description
            tool_dict = {
                "name": tool.name,
                "description": desc,
            }
            if hasattr(tool, 'inputSchema'):
                tool_dict["inputSchema"] = tool.inputSchema
            tools_dict.append(tool_dict)
        return tools_dict

    def convert_tools_to_gemini_format(
        self, tools: List[Any]
    ) -> List[Dict[str, Any]]:
        """Convert MCP tools to Gemini function calling format.

        Args:
            tools: List of MCP tools

        Returns:
            List of function declarations for Gemini API
        """
        gemini_functions = []

        for tool in tools:
            desc = ""
            if hasattr(tool, 'description'):
                desc = tool.description
            function_declaration = {
                "name": tool.name,
                "description": desc,
            }

            # Add parameters if available
            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                # Clean schema for Gemini compatibility
                cleaned_schema = self._clean_schema_for_gemini(
                    tool.inputSchema
                )
                function_declaration["parameters"] = cleaned_schema

            gemini_functions.append(function_declaration)

        return gemini_functions

    def _clean_schema_for_gemini(
        self, schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Remove fields not supported by Gemini API.

        Args:
            schema: JSON Schema from MCP tool

        Returns:
            Cleaned schema compatible with Gemini
        """
        if not isinstance(schema, dict):
            return schema

        # Fields not supported by Gemini API
        unsupported_fields = {
            'exclusiveMaximum',
            'exclusiveMinimum',
            'additionalProperties',
            '$schema',
            'examples'
        }

        cleaned = {}
        for key, value in schema.items():
            # Skip unsupported fields
            if key in unsupported_fields:
                continue

            # Recursively clean nested objects
            if isinstance(value, dict):
                cleaned[key] = self._clean_schema_for_gemini(value)
            elif isinstance(value, list):
                cleaned[key] = [
                    self._clean_schema_for_gemini(item)
                    if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                cleaned[key] = value

        return cleaned

    def is_connected(self) -> bool:
        """Check if connected to MCP server.

        Returns:
            True if connected, False otherwise
        """
        return self.connected
