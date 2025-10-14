"""Fetch MCP client using FastMCP."""

import asyncio
import os
from fastmcp import Client
from .base import BaseMCPClient


class FetchMCPClient(BaseMCPClient):
    """Client for HTTP fetch MCP server.

    No API key required. Python-based server using urllib.
    """

    def __init__(self):
        """Initialize fetch MCP client."""
        super().__init__("Fetch")

    async def connect(self) -> bool:
        """Connect to fetch MCP server.

        Returns:
            True if connection successful

        Raises:
            Exception: If connection fails
        """
        try:
            # Get absolute path to fetch_server.py
            current_dir = os.path.dirname(os.path.abspath(__file__))
            server_path = os.path.join(
                os.path.dirname(current_dir),
                "mcp_servers",
                "fetch_server.py"
            )

            # Connect to our custom fetch MCP server using FastMCP
            try:
                self.client_context = Client({
                    "mcpServers": {
                        "fetch": {
                            "command": "python",
                            "args": [server_path]
                        }
                    }
                })
                self.client = await asyncio.wait_for(
                    self.client_context.__aenter__(), timeout=10.0
                )

                # Get list of available tools (FastMCP returns list directly)
                self.tools = await asyncio.wait_for(
                    self.client.list_tools(), timeout=5.0
                )
                self.connected = True

                return True
            except asyncio.TimeoutError:
                msg = "Connection timeout - MCP server not responding"
                raise Exception(msg)

        except Exception as e:
            self.connected = False
            msg = f"Failed to connect to Fetch MCP server: {str(e)}"
            raise Exception(msg)
