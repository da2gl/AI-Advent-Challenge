"""MCP Manager for connecting to external MCP servers and exposing tools to Gemini"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPManager:
    """Manages connections to MCP servers and tool execution"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize MCP Manager

        Args:
            config_path: Path to MCP configuration file. If None, uses default config.json
        """
        if config_path is None:
            config_path = Path(__file__).parent / "config.json"

        self.config_path = config_path
        self.clients: Dict[str, ClientSession] = {}
        self.client_exits: Dict[str, Any] = {}  # Store exit stack for cleanup
        self.tools: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """Load MCP server configuration from JSON file"""
        with open(self.config_path, 'r') as f:
            config = json.load(f)
            self.server_configs = config.get('mcpServers', {})

    async def connect_all(self):
        """Connect to all configured MCP servers"""
        for server_name in self.server_configs.keys():
            await self.connect_server(server_name)

    async def connect_server(self, server_name: str):
        """
        Connect to a specific MCP server

        Args:
            server_name: Name of the server from config
        """
        if server_name in self.clients:
            print(f"Already connected to {server_name}")
            return

        config = self.server_configs.get(server_name)
        if not config:
            raise ValueError(f"Server {server_name} not found in configuration")

        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=config['command'],
                args=config['args'],
                env=None
            )

            # Connect via stdio - returns async context manager
            stdio_ctx = stdio_client(server_params)
            read, write = await stdio_ctx.__aenter__()

            # Create session - also async context manager
            session_ctx = ClientSession(read, write)
            session = await session_ctx.__aenter__()
            await session.initialize()

            # Store session and contexts for cleanup
            self.clients[server_name] = session
            self.client_exits[server_name] = (session_ctx, stdio_ctx)

            # Get available tools
            tools_list = await session.list_tools()
            for tool in tools_list.tools:
                tool_key = f"{server_name}_{tool.name}"
                self.tools[tool_key] = {
                    'server': server_name,
                    'name': tool.name,
                    'description': tool.description,
                    'inputSchema': tool.inputSchema
                }

            print(f"Connected to {server_name}, loaded {len(tools_list.tools)} tools")

        except Exception as e:
            print(f"Error connecting to {server_name}: {e}")
            raise

    def get_tools_for_gemini(self) -> List[Dict[str, Any]]:
        """
        Convert MCP tools to Gemini function declarations format

        Returns:
            List of tool declarations in Gemini format
        """
        gemini_tools = []

        for tool_key, tool_info in self.tools.items():
            # Convert MCP tool schema to Gemini format
            gemini_tool = {
                'name': tool_key,
                'description': tool_info['description'] or "No description available",
                'parameters': tool_info.get('inputSchema', {
                    'type': 'object',
                    'properties': {},
                    'required': []
                })
            }

            # Clean up schema for Gemini compatibility
            gemini_tool = self._clean_schema_for_gemini(gemini_tool)
            gemini_tools.append(gemini_tool)

        return gemini_tools

    def _clean_schema_for_gemini(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove unsupported fields from tool schema for Gemini API

        Args:
            tool: Tool declaration with parameters

        Returns:
            Cleaned tool declaration
        """
        if 'parameters' in tool:
            params = tool['parameters']

            # Remove unsupported fields at top level
            params.pop('$schema', None)
            params.pop('additionalProperties', None)
            params.pop('examples', None)
            params.pop('default', None)

            # Recursively clean nested objects
            self._clean_schema_recursive(params)

        return tool

    def _clean_schema_recursive(self, schema: Dict[str, Any]):
        """Recursively clean schema object."""
        if not isinstance(schema, dict):
            return

        # Remove unsupported fields
        schema.pop('additionalProperties', None)
        schema.pop('examples', None)
        schema.pop('default', None)
        schema.pop('$schema', None)

        # Clean properties
        if 'properties' in schema and isinstance(schema['properties'], dict):
            for prop_value in schema['properties'].values():
                if isinstance(prop_value, dict):
                    self._clean_schema_recursive(prop_value)

        # Clean items (for arrays)
        if 'items' in schema and isinstance(schema['items'], dict):
            self._clean_schema_recursive(schema['items'])

        # Clean nested objects in anyOf, oneOf, allOf
        for key in ['anyOf', 'oneOf', 'allOf']:
            if key in schema and isinstance(schema[key], list):
                for item in schema[key]:
                    if isinstance(item, dict):
                        self._clean_schema_recursive(item)

    async def call_tool(self, tool_key: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute an MCP tool

        Args:
            tool_key: Full tool key (server_toolname)
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if tool_key not in self.tools:
            raise ValueError(f"Tool {tool_key} not found")

        tool_info = self.tools[tool_key]
        server_name = tool_info['server']
        tool_name = tool_info['name']

        if server_name not in self.clients:
            raise ValueError(f"Not connected to server {server_name}")

        session = self.clients[server_name]

        try:
            result = await session.call_tool(tool_name, arguments=arguments)
            return result
        except Exception as e:
            print(f"Error calling tool {tool_key}: {e}")
            raise

    async def disconnect_all(self):
        """Disconnect from all MCP servers.

        Note: We don't explicitly close connections as it causes async cleanup errors.
        The OS will clean up the child processes when the main process exits.
        """
        # Just clear our references, let garbage collection handle cleanup
        self.clients.clear()
        self.client_exits.clear()
        self.tools.clear()

    def list_available_tools(self) -> List[str]:
        """Get list of all available tool names"""
        return list(self.tools.keys())

    def get_tool_info(self, tool_key: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool"""
        return self.tools.get(tool_key)
