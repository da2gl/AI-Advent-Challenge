"""Base MCP client interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from mcp import ClientSession


class BaseMCPClient(ABC):
    """Abstract base class for MCP clients."""

    def __init__(self, name: str):
        """Initialize MCP client.

        Args:
            name: Human-readable name for this client
        """
        self.name = name
        self.session: Optional[ClientSession] = None
        self.read_stream = None
        self.write_stream = None
        self.tools: List[Any] = []
        self.connected = False
        self._stdio_context = None
        self._session_context = None

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
        import asyncio

        self.connected = False

        # Properly exit context managers in reverse order
        # Exit session context first
        if self._session_context is not None:
            try:
                # Shield from cancellation to ensure cleanup completes
                await asyncio.shield(
                    self._session_context.__aexit__(None, None, None)
                )
            except asyncio.CancelledError:
                # Handle cancellation - try to exit anyway
                try:
                    await self._session_context.__aexit__(
                        asyncio.CancelledError, None, None
                    )
                except Exception:
                    pass  # Ignore errors during forced cleanup
            except (Exception, GeneratorExit, BaseExceptionGroup):
                # Log but don't raise - we want to continue cleanup
                pass  # Silently handle cleanup errors
            finally:
                self._session_context = None
                self.session = None

        # Exit stdio context second
        if self._stdio_context is not None:
            try:
                # Shield from cancellation to ensure cleanup completes
                await asyncio.shield(
                    self._stdio_context.__aexit__(None, None, None)
                )
            except asyncio.CancelledError:
                # Handle cancellation - try to exit anyway
                try:
                    await self._stdio_context.__aexit__(
                        asyncio.CancelledError, None, None
                    )
                except Exception:
                    pass  # Ignore errors during forced cleanup
            except (Exception, GeneratorExit, BaseExceptionGroup):
                # Log but don't raise - we want to continue cleanup
                pass  # Silently handle cleanup errors
            finally:
                self._stdio_context = None
                self.read_stream = None
                self.write_stream = None

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

    def convert_tools_to_gemini_format(self) -> List[Dict[str, Any]]:
        """Convert MCP tools to Gemini function calling format.

        Returns:
            List of function declarations for Gemini API
        """
        gemini_functions = []

        for tool in self.tools:
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

    def _clean_schema_for_gemini(self, schema: Dict[str, Any]) -> Dict[str, Any]:
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

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Any:
        """Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool execution result

        Raises:
            Exception: If tool call fails
        """
        if not self.connected or not self.session:
            raise Exception(f"Not connected to {self.name} MCP server")

        try:
            result = await self.session.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            raise Exception(f"Tool call failed: {str(e)}")

    def is_connected(self) -> bool:
        """Check if connected to MCP server.

        Returns:
            True if connected, False otherwise
        """
        return self.connected
