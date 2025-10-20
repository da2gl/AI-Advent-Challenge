"""Filesystem MCP Client for code analysis."""

import asyncio
import os
from typing import List, Dict, Optional

from fastmcp import Client

from .base import BaseMCPClient


class FilesystemClient(BaseMCPClient):
    """Client for interacting with Filesystem MCP server."""

    def __init__(self):
        """Initialize filesystem client."""
        super().__init__("Filesystem")

    async def connect(self) -> bool:
        """Connect to filesystem MCP server.

        Returns:
            True if connection successful

        Raises:
            Exception: If connection fails
        """
        try:
            # Get absolute path to filesystem_server.py
            current_dir = os.path.dirname(os.path.abspath(__file__))
            server_path = os.path.join(
                os.path.dirname(current_dir),
                "mcp_servers",
                "filesystem_server.py"
            )

            # Connect to filesystem MCP server using FastMCP
            try:
                self.client_context = Client({
                    "mcpServers": {
                        "filesystem": {
                            "command": "python",
                            "args": [server_path]
                        }
                    }
                })
                self.client = await asyncio.wait_for(
                    self.client_context.__aenter__(), timeout=10.0
                )

                # Get list of available tools
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
            msg = f"Failed to connect to Filesystem MCP server: {str(e)}"
            raise Exception(msg)

    async def get_project_tree(
            self,
            path: str,
            max_depth: int = 3
    ) -> Dict:
        """Get directory tree structure.

        Args:
            path: Root directory path to scan
            max_depth: Maximum depth to traverse

        Returns:
            Dictionary with tree structure and statistics
        """
        return await self.call_tool("get_project_tree", {
            "path": path,
            "max_depth": max_depth
        })

    async def get_file_list(
            self,
            path: str,
            extensions: Optional[List[str]] = None
    ) -> Dict:
        """Get list of files with metadata.

        Args:
            path: Directory path to scan
            extensions: Optional list of file extensions to filter

        Returns:
            Dictionary with file list and metadata
        """
        args = {"path": path}
        if extensions:
            args["extensions"] = extensions

        return await self.call_tool("get_file_list", args)

    async def read_file(self, file_path: str) -> Dict:
        """Read single file content.

        Args:
            file_path: Path to file to read

        Returns:
            Dictionary with file content and metadata
        """
        return await self.call_tool("read_file", {
            "file_path": file_path
        })

    async def read_multiple_files(
            self,
            file_paths: List[str],
            max_total_size: int = 500000
    ) -> Dict:
        """Read multiple files at once.

        Args:
            file_paths: List of file paths to read
            max_total_size: Maximum total size in bytes

        Returns:
            Dictionary with all files content and metadata
        """
        return await self.call_tool("read_multiple_files", {
            "file_paths": file_paths,
            "max_total_size": max_total_size
        })

    async def search_in_files(
            self,
            path: str,
            pattern: str,
            extensions: Optional[List[str]] = None
    ) -> Dict:
        """Search for pattern in files.

        Args:
            path: Directory path to search in
            pattern: Regular expression pattern to search for
            extensions: Optional list of file extensions to search

        Returns:
            Dictionary with search results
        """
        args = {
            "path": path,
            "pattern": pattern
        }
        if extensions:
            args["extensions"] = extensions

        return await self.call_tool("search_in_files", args)

    async def get_file_info(self, file_path: str) -> Dict:
        """Get detailed file information.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file metadata
        """
        return await self.call_tool("get_file_info", {
            "file_path": file_path
        })
