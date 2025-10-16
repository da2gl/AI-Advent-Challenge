"""MCP client for pipeline server."""

import sys
from .base import BaseMCPClient
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class PipelineMCPClient(BaseMCPClient):
    """Client for Pipeline MCP server."""

    def __init__(self):
        """Initialize Pipeline MCP client."""
        super().__init__("Pipeline")

    async def connect(self) -> bool:
        """Connect to Pipeline MCP server.

        Returns:
            True if connection successful

        Raises:
            Exception: If connection fails
        """
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "mcp_servers.pipeline_server"],
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
