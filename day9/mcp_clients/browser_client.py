"""Browser MCP client using mcp-server-browser-use."""

import asyncio
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp import ClientSession
from .base import BaseMCPClient


class BrowserMCPClient(BaseMCPClient):
    """Client for browser automation MCP server.

    Requires ANTHROPIC_API_KEY environment variable.
    """

    def __init__(self):
        """Initialize browser MCP client."""
        super().__init__("Browser")

    async def connect(self) -> bool:
        """Connect to browser MCP server.

        Returns:
            True if connection successful

        Raises:
            Exception: If connection fails
        """
        try:
            # Configure connection to browser MCP server
            server_params = StdioServerParameters(
                command="python",
                args=["-m", "mcp_server_browser_use"],
                env=None
            )

            # Connect to server with timeout
            try:
                # Create and enter stdio context - keep it alive
                self._stdio_context = stdio_client(server_params)
                self.read_stream, self.write_stream = await asyncio.wait_for(
                    self._stdio_context.__aenter__(), timeout=10.0
                )

                # Create and enter session context - keep it alive
                self._session_context = ClientSession(
                    self.read_stream, self.write_stream
                )
                self.session = await asyncio.wait_for(
                    self._session_context.__aenter__(), timeout=5.0
                )

                # Initialize connection with timeout
                await asyncio.wait_for(
                    self.session.initialize(), timeout=5.0
                )

                # Get list of available tools with timeout
                tools_response = await asyncio.wait_for(
                    self.session.list_tools(), timeout=5.0
                )
                self.tools = tools_response.tools
                self.connected = True

                return True
            except asyncio.TimeoutError:
                msg = "Connection timeout - MCP server not responding"
                raise Exception(msg)

        except Exception as e:
            self.connected = False
            msg = f"Failed to connect to Browser MCP server: {str(e)}"
            raise Exception(msg)
