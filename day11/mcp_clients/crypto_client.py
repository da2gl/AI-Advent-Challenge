"""MCP client for cryptocurrency data server."""

from .base import BaseMCPClient
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys


class CryptoMCPClient(BaseMCPClient):
    """Client for Crypto MCP server using FastMCP."""

    def __init__(self):
        """Initialize Crypto MCP client."""
        super().__init__("Crypto Data")

    async def connect(self) -> bool:
        """Connect to Crypto MCP server.

        Returns:
            True if connection successful

        Raises:
            Exception: If connection fails
        """
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "mcp_servers.crypto_server"],
            env=None
        )

        self.client_context = stdio_client(server_params)
        read_stream, write_stream = await self.client_context.__aenter__()

        self.client = ClientSession(read_stream, write_stream)
        await self.client.__aenter__()

        # Initialize connection
        await self.client.initialize()

        # Get available tools
        tools_response = await self.client.list_tools()
        self.tools = tools_response.tools

        self.connected = True
        return True
