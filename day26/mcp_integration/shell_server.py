#!/usr/bin/env python3
"""Simple MCP server for shell command execution."""

import asyncio
import json
import sys
from typing import Any


async def execute_command(command: str, args: list[str] = None, cwd: str = None) -> dict[str, Any]:
    """Execute a shell command.

    Args:
        command: Command to execute
        args: Command arguments
        cwd: Working directory

    Returns:
        Dict with stdout, stderr, and return code
    """
    if args is None:
        args = []

    full_command = [command] + args

    try:
        process = await asyncio.create_subprocess_exec(
            *full_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )

        stdout, stderr = await process.communicate()

        return {
            "stdout": stdout.decode('utf-8', errors='replace'),
            "stderr": stderr.decode('utf-8', errors='replace'),
            "returncode": process.returncode,
            "success": process.returncode == 0
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "success": False
        }


async def handle_request(request: dict):
    """Handle MCP request."""
    method = request.get("method")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "shell-server",
                    "version": "1.0.0"
                }
            }
        }

    elif method == "notifications/initialized":
        # This is a notification, no response needed
        return None

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "tools": [
                    {
                        "name": "execute_command",
                        "description": "Execute a shell command and return output",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "command": {
                                    "type": "string",
                                    "description": "Command to execute (e.g., 'pytest', 'python', 'ls')"
                                },
                                "args": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Command arguments"
                                },
                                "cwd": {
                                    "type": "string",
                                    "description": "Working directory (optional)"
                                }
                            },
                            "required": ["command"]
                        }
                    }
                ]
            }
        }

    elif method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "execute_command":
            result = await execute_command(
                command=arguments.get("command"),
                args=arguments.get("args", []),
                cwd=arguments.get("cwd")
            )

            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            }

    # Unknown method
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "error": {
            "code": -32601,
            "message": f"Method not found: {method}"
        }
    }


async def main():
    """Main server loop."""
    while True:
        try:
            # Read line from stdin
            line = await asyncio.get_event_loop().run_in_executor(
                None, sys.stdin.readline
            )

            if not line:
                break

            # Parse JSON-RPC request
            request = json.loads(line)

            # Handle request
            response = await handle_request(request)

            # Write response to stdout (skip if None - notifications don't need responses)
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

        except json.JSONDecodeError:
            continue
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.stderr.flush()


if __name__ == "__main__":
    asyncio.run(main())
