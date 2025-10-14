"""Container MCP client using FastMCP."""

import asyncio

from fastmcp import Client

from .base import BaseMCPClient


class ContainerMCPClient(BaseMCPClient):
    """Client for Apple Container MCP server.

    Provides container management capabilities through MCP.
    """

    def __init__(self):
        """Initialize container MCP client."""
        super().__init__("Container")

    async def connect(self) -> bool:
        """Connect to container MCP server.

        Returns:
            True if connection successful

        Raises:
            Exception: If connection fails
        """
        try:
            # Get absolute path to container_server.py
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            server_path = os.path.join(
                os.path.dirname(current_dir),
                "mcp_servers",
                "container_server.py"
            )

            # Connect to container MCP server using FastMCP
            try:
                self.client_context = Client({
                    "mcpServers": {
                        "container": {
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
            msg = f"Failed to connect to Container MCP server: {str(e)}"
            raise Exception(msg)
