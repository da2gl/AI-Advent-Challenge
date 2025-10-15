"""MCP Manager for handling multiple MCP clients."""

from typing import Dict, List, Optional, Any
from .base import BaseMCPClient
from .crypto_client import CryptoMCPClient
from .background_client import BackgroundMCPClient


class MCPManager:
    """Manager for MCP clients."""

    AVAILABLE_CLIENTS = {
        "crypto": CryptoMCPClient,
        "background": BackgroundMCPClient,
    }

    def __init__(self):
        """Initialize MCP manager."""
        self.clients: Dict[str, BaseMCPClient] = {}
        self.active_client: Optional[str] = None

    async def connect_client(self, client_type: str) -> bool:
        """Connect to a specific MCP client.

        Args:
            client_type: Type of client to connect ("fetch" or "container")

        Returns:
            True if connection successful

        Raises:
            ValueError: If client type is unknown
            Exception: If connection fails
        """
        if client_type not in self.AVAILABLE_CLIENTS:
            available = ", ".join(self.AVAILABLE_CLIENTS.keys())
            raise ValueError(
                f"Unknown client type: {client_type}. "
                f"Available: {available}"
            )

        # Create client if not exists
        if client_type not in self.clients:
            client_class = self.AVAILABLE_CLIENTS[client_type]
            self.clients[client_type] = client_class()

        # Connect
        client = self.clients[client_type]
        await client.connect()

        # Set as active
        self.active_client = client_type

        return True

    async def disconnect_client(self, client_type: str):
        """Disconnect a specific MCP client.

        Args:
            client_type: Type of client to disconnect
        """
        if client_type in self.clients:
            await self.clients[client_type].disconnect()
            if self.active_client == client_type:
                self.active_client = None

    async def disconnect_all(self):
        """Disconnect all MCP clients."""
        for client in self.clients.values():
            await client.disconnect()
        self.active_client = None

    def get_active_client(self) -> Optional[BaseMCPClient]:
        """Get currently active MCP client.

        Returns:
            Active client or None
        """
        if self.active_client and self.active_client in self.clients:
            return self.clients[self.active_client]
        return None

    def get_client(self, client_type: str) -> Optional[BaseMCPClient]:
        """Get a specific MCP client.

        Args:
            client_type: Type of client to get

        Returns:
            Client or None if not connected
        """
        return self.clients.get(client_type)

    def list_connected_clients(self) -> List[str]:
        """List all connected clients.

        Returns:
            List of connected client types
        """
        return [
            client_type
            for client_type, client in self.clients.items()
            if client.is_connected()
        ]

    def get_all_tools(self) -> Dict[str, List[Any]]:
        """Get tools from all connected clients.

        Returns:
            Dictionary mapping client type to list of tools
        """
        all_tools = {}
        for client_type, client in self.clients.items():
            if client.is_connected():
                all_tools[client_type] = client.get_tools()
        return all_tools

    def get_all_tools_as_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get tools as dictionaries from all connected clients.

        Returns:
            Dictionary mapping client type to list of tool dictionaries
        """
        all_tools = {}
        for client_type, client in self.clients.items():
            if client.is_connected():
                all_tools[client_type] = client.get_tools_as_dict()
        return all_tools

    def get_all_tools_for_gemini(self) -> List[Dict[str, Any]]:
        """Get all tools from all connected clients in Gemini format.

        Returns:
            Combined list of function declarations for Gemini API
        """
        all_functions = []
        for client in self.clients.values():
            if client.is_connected():
                tools = client.get_tools()
                all_functions.extend(
                    client.convert_tools_to_gemini_format(tools)
                )
        return all_functions

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        client_type: Optional[str] = None
    ) -> Any:
        """Call a tool on a specific client or search through all clients.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            client_type: Type of client to use (None = search all clients)

        Returns:
            Tool execution result

        Raises:
            Exception: If no client available or tool call fails
        """
        # If client_type specified, use that client
        if client_type:
            client = self.get_client(client_type)
            if not client or not client.is_connected():
                raise Exception(f"Client {client_type} not connected")
            # Call tool via FastMCP client
            return await client.client.call_tool(tool_name, arguments)

        # Otherwise, search for tool in all connected clients
        for client_type, client in self.clients.items():
            if not client.is_connected():
                continue

            # Check if this client has the tool
            tools = client.get_tools_as_dict()
            tool_names = [tool["name"] for tool in tools]

            if tool_name in tool_names:
                # Call tool via FastMCP client
                return await client.client.call_tool(tool_name, arguments)

        # Tool not found in any client
        raise Exception(
            f"Tool '{tool_name}' not found in any connected MCP client"
        )
