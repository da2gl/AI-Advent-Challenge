"""MCP Manager for handling filesystem MCP client."""

from typing import Dict, Optional, Any, List

from .filesystem_client import FilesystemClient


class MCPManager:
    """Manager for MCP clients."""

    def __init__(self):
        """Initialize MCP manager."""
        self.clients: Dict[str, FilesystemClient] = {}

    async def connect_client(self, client_name: str):
        """Connect to an MCP client.

        Args:
            client_name: Name of the client to connect ('filesystem')

        Raises:
            ValueError: If client name is not supported
        """
        if client_name == "filesystem":
            client = FilesystemClient()
            await client.connect()
            self.clients[client_name] = client
        else:
            raise ValueError(f"Unsupported client: {client_name}")

    def get_client(self, client_name: str) -> Optional[FilesystemClient]:
        """Get connected client by name.

        Args:
            client_name: Name of the client

        Returns:
            Client instance or None if not connected
        """
        return self.clients.get(client_name)

    def get_all_tools(self) -> Dict:
        """Get all available tools from all connected clients.

        Returns:
            Dictionary mapping client names to their tools
        """
        all_tools = {}

        for name, client in self.clients.items():
            tools = client.get_tools()
            all_tools[name] = tools

        return all_tools

    async def disconnect_all(self):
        """Disconnect all MCP clients."""
        for client in self.clients.values():
            await client.disconnect()
        self.clients.clear()

    def get_all_tools_for_gemini(self) -> List[Dict[str, Any]]:
        """Get all tools formatted for Gemini API.

        Returns:
            List of function declarations for Gemini API
        """
        all_tools = []

        for client in self.clients.values():
            tools = client.get_tools()
            gemini_tools = client.convert_tools_to_gemini_format(tools)
            all_tools.extend(gemini_tools)

        return all_tools

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        client_type: Optional[str] = None
    ) -> Any:
        """Call an MCP tool with smart routing.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            client_type: Optional specific client to use

        Returns:
            Tool execution result

        Raises:
            Exception: If tool not found or execution fails
        """
        # If client_type specified, use that client directly
        if client_type:
            client = self.get_client(client_type)
            if not client:
                raise Exception(f"Client '{client_type}' not found")
            # Call tool directly via FastMCP client
            return await client.client.call_tool(tool_name, arguments)

        # Otherwise, search for tool in all connected clients
        for client_name, client in self.clients.items():
            tools = client.get_tools()
            tool_names = [tool.name for tool in tools]

            if tool_name in tool_names:
                # Call tool directly via FastMCP client
                return await client.client.call_tool(tool_name, arguments)

        raise Exception(
            f"Tool '{tool_name}' not found in any connected MCP server"
        )
