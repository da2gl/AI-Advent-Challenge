"""Apple Container MCP Server using FastMCP.

This MCP server provides tools for managing Apple Containers on macOS.
It wraps the 'container' CLI tool and exposes container management
capabilities through the Model Context Protocol using FastMCP framework.
"""

import subprocess
from typing import Optional

from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Apple Container Manager")


def run_container_command(args: list[str]) -> dict:
    """Execute a container CLI command and return parsed output.

    Args:
        args: Command arguments (without 'container' prefix)

    Returns:
        Dictionary with success status and result/error
    """
    import os

    try:
        # Get current environment and ensure proper XPC/launchd access
        env = os.environ.copy()

        # Make sure we have access to user's launchd session
        if 'XPC_SERVICE_NAME' not in env:
            # Get user's UID for launchd domain
            import pwd
            uid = os.getuid()
            username = pwd.getpwuid(uid).pw_name

            # Set environment to help with XPC connection
            env['USER'] = username
            env['HOME'] = os.path.expanduser('~')

        result = subprocess.run(
            ["container"] + args,
            capture_output=True,
            text=True,
            timeout=30,
            env=env
        )

        if result.returncode == 0:
            return {
                "success": True,
                "output": result.stdout.strip(),
                "error": None
            }
        else:
            return {
                "success": False,
                "output": None,
                "error": result.stderr.strip()
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": None,
            "error": "Command timeout after 30 seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "output": None,
            "error": str(e)
        }


@mcp.tool()
def list_containers(all: bool = True) -> dict:
    """List all containers (running and stopped).

    Args:
        all: Show all containers (default shows just running)

    Returns:
        Dictionary with success status and container list
    """
    args = ["list"]
    if all:
        args.append("--all")

    result = run_container_command(args)

    if result["success"]:
        return {
            "success": True,
            "containers": result["output"],
            "message": "Successfully listed containers"
        }
    else:
        return {
            "success": False,
            "error": result["error"],
            "message": "Failed to list containers"
        }


@mcp.tool()
def run_container(
        image: str,
        name: Optional[str] = None,
        detach: bool = True,
        ports: Optional[str] = None,
        env: Optional[list[str]] = None
) -> dict:
    """Run a new container from an image.

    Args:
        image: Container image to run (e.g., 'nginx:latest', 'postgres:15')
        name: Optional name for the container
        detach: Run container in background (detached mode)
        ports: Port mapping in format 'host:container' (e.g., '8080:80')
        env: Environment variables in format 'KEY=VALUE'

    Returns:
        Dictionary with success status, container ID, and IP address
    """
    args = ["run"]

    if detach:
        args.append("-d")

    if name:
        args.extend(["--name", name])

    if ports:
        args.extend(["-p", ports])

    if env:
        for env_var in env:
            args.extend(["-e", env_var])

    args.append(image)

    result = run_container_command(args)

    if result["success"]:
        container_id = result["output"]

        # Get container IP address by inspecting it
        import json
        import time

        # Wait a bit for container to initialize
        time.sleep(1)

        inspect_result = run_container_command(["inspect", container_id])
        ip_address = None

        if inspect_result["success"]:
            try:
                container_info = json.loads(inspect_result["output"])
                if container_info and len(container_info) > 0:
                    networks = container_info[0].get("networks", [])
                    if networks and len(networks) > 0:
                        ip_address = networks[0].get("address", "").split("/")[0]
            except (json.JSONDecodeError, KeyError, IndexError):
                pass

        response = {
            "success": True,
            "container_id": container_id,
            "message": f"Successfully started container from image '{image}'"
        }

        if ip_address:
            response["ip_address"] = ip_address
            response["message"] += f" at {ip_address}"

        return response
    else:
        return {
            "success": False,
            "error": result["error"],
            "message": f"Failed to run container from image '{image}'"
        }


@mcp.tool()
def stop_container(container: str) -> dict:
    """Stop a running container.

    Args:
        container: Container ID or name to stop

    Returns:
        Dictionary with success status
    """
    result = run_container_command(["stop", container])

    if result["success"]:
        return {
            "success": True,
            "message": f"Successfully stopped container '{container}'"
        }
    else:
        return {
            "success": False,
            "error": result["error"],
            "message": f"Failed to stop container '{container}'"
        }


@mcp.tool()
def start_container(container: str) -> dict:
    """Start a stopped container.

    Args:
        container: Container ID or name to start

    Returns:
        Dictionary with success status
    """
    result = run_container_command(["start", container])

    if result["success"]:
        return {
            "success": True,
            "message": f"Successfully started container '{container}'"
        }
    else:
        return {
            "success": False,
            "error": result["error"],
            "message": f"Failed to start container '{container}'"
        }


@mcp.tool()
def inspect_container(container: str) -> dict:
    """Get detailed information about a container including IP address.

    Args:
        container: Container ID or name to inspect

    Returns:
        Dictionary with success status, container info, and parsed IP address
    """
    result = run_container_command(["inspect", container])

    if result["success"]:
        import json

        response = {
            "success": True,
            "info": result["output"],
            "message": f"Successfully inspected container '{container}'"
        }

        # Try to parse and extract useful information
        try:
            container_info = json.loads(result["output"])
            if container_info and len(container_info) > 0:
                info = container_info[0]

                # Extract IP address
                networks = info.get("networks", [])
                if networks and len(networks) > 0:
                    ip_address = networks[0].get("address", "").split("/")[0]
                    if ip_address:
                        response["ip_address"] = ip_address

                # Extract state
                state = info.get("status")
                if state:
                    response["state"] = state

                # Extract image
                image_ref = info.get("configuration", {}).get("image", {}).get("reference")
                if image_ref:
                    response["image"] = image_ref

        except (json.JSONDecodeError, KeyError, IndexError):
            pass

        return response
    else:
        return {
            "success": False,
            "error": result["error"],
            "message": f"Failed to inspect container '{container}'"
        }


@mcp.tool()
def get_logs(
        container: str,
        tail: int = 100,
        follow: bool = False
) -> dict:
    """Fetch logs from a container.

    Args:
        container: Container ID or name
        tail: Number of lines to show from the end of logs
        follow: Follow log output (stream logs)

    Returns:
        Dictionary with success status and logs
    """
    args = ["logs"]

    if not follow:
        args.extend(["--tail", str(tail)])
    else:
        args.append("--follow")

    args.append(container)

    result = run_container_command(args)

    if result["success"]:
        return {
            "success": True,
            "logs": result["output"],
            "message": (
                f"Successfully fetched logs from container '{container}'"
            )
        }
    else:
        return {
            "success": False,
            "error": result["error"],
            "message": f"Failed to get logs from container '{container}'"
        }


@mcp.tool()
def delete_container(container: str, force: bool = False) -> dict:
    """Delete (remove) a container.

    Args:
        container: Container ID or name to delete
        force: Force deletion of running container

    Returns:
        Dictionary with success status
    """
    args = ["delete"]
    if force:
        args.append("--force")
    args.append(container)

    result = run_container_command(args)

    if result["success"]:
        return {
            "success": True,
            "message": f"Successfully deleted container '{container}'"
        }
    else:
        return {
            "success": False,
            "error": result["error"],
            "message": f"Failed to delete container '{container}'"
        }


@mcp.tool()
def start_system() -> dict:
    """Start the Apple Container system service.

    This must be run before any container operations can be performed.
    The system service runs in the background and manages container lifecycle.

    Returns:
        Dictionary with success status
    """
    result = run_container_command(["system", "start"])

    if result["success"]:
        return {
            "success": True,
            "message": "Container system service started successfully"
        }
    else:
        return {
            "success": False,
            "error": result["error"],
            "message": "Failed to start container system service"
        }


@mcp.tool()
def stop_system() -> dict:
    """Stop the Apple Container system service.

    This will stop all running containers and shut down the system service.

    Returns:
        Dictionary with success status
    """
    result = run_container_command(["system", "stop"])

    if result["success"]:
        return {
            "success": True,
            "message": "Container system service stopped successfully"
        }
    else:
        return {
            "success": False,
            "error": result["error"],
            "message": "Failed to stop container system service"
        }


@mcp.tool()
def system_status() -> dict:
    """Check the status of the Apple Container system service.

    Returns:
        Dictionary with success status and system status info
    """
    result = run_container_command(["system", "status"])

    if result["success"]:
        return {
            "success": True,
            "status": result["output"],
            "message": "System status retrieved successfully"
        }
    else:
        return {
            "success": False,
            "error": result["error"],
            "message": "Failed to get system status"
        }


if __name__ == "__main__":
    mcp.run(show_banner=False)
