"""MCP server for background task management."""

import json
import os
from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("Background Task Manager")

# Get database path from environment or use default
DB_PATH = os.getenv("TASK_DB_PATH", "day11_tasks.db")


def _get_storage():
    """Get TaskStorage instance."""
    from tasks.storage import TaskStorage
    return TaskStorage(DB_PATH)


@mcp.tool()
def create_background_task(
    name: str,
    schedule_type: str,
    schedule_value: str,
    mcp_tool: str,
    tool_args: dict = None,
    description: str = "",
    use_ai_summary: bool = True,
    notification_level: str = "all"
) -> str:
    """Create a new background task that runs periodically.

    Args:
        name: Task name
        schedule_type: Type of schedule - "interval", "daily", or "weekly"
        schedule_value: Schedule value (e.g., "30 minutes", "10:00", "Monday 09:00")
        mcp_tool: MCP tool to execute
        tool_args: Arguments for the MCP tool (default: {})
        description: Task description (default: "")
        use_ai_summary: Generate AI summary of results (default: True)
        notification_level: Notification level - "all", "errors", "significant", or "silent" (default: "all")

    Returns:
        JSON string with task creation result
    """
    if tool_args is None:
        tool_args = {}

    try:
        storage = _get_storage()

        task_data = {
            "name": name,
            "description": description,
            "schedule_type": schedule_type,
            "schedule_value": schedule_value,
            "mcp_tool": mcp_tool,
            "tool_args": tool_args,
            "use_ai_summary": use_ai_summary,
            "notification_level": notification_level,
            "enabled": True  # Enable by default
        }

        # Create task in database
        task_id = storage.create_task(task_data)

        # Get created task details
        task = storage.get_task(task_id)

        result = {
            "success": True,
            "task_id": task_id,
            "name": task['name'],
            "schedule": f"{task['schedule_type']}: {task['schedule_value']}",
            "enabled": task['enabled'],
            "message": f"Task '{name}' created successfully with ID {task_id}. Scheduler will pick it up automatically."
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({
            "error": "Task creation failed",
            "message": str(e)
        }, indent=2)


@mcp.tool()
def list_background_tasks() -> str:
    """List all background tasks with their status.

    Returns:
        JSON string with all tasks
    """
    try:
        storage = _get_storage()
        tasks = storage.get_all_tasks()

        result = {
            "success": True,
            "count": len(tasks),
            "tasks": [
                {
                    "id": task['id'],
                    "name": task['name'],
                    "schedule": f"{task['schedule_type']}: {task['schedule_value']}",
                    "mcp_tool": task['mcp_tool'],
                    "enabled": task['enabled'],
                    "last_run": task.get('last_run'),
                    "next_run": task.get('next_run')
                }
                for task in tasks
            ]
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({
            "error": "Failed to list tasks",
            "message": str(e)
        }, indent=2)


@mcp.tool()
def get_task_details(task_id: int) -> str:
    """Get detailed information about a specific task.

    Args:
        task_id: Task ID

    Returns:
        JSON string requesting task details
    """
    result = {
        "action": "get_task",
        "task_id": task_id
    }

    return json.dumps(result, indent=2)


@mcp.tool()
def start_background_task(task_id: int) -> str:
    """Enable and start a background task.

    Args:
        task_id: Task ID

    Returns:
        JSON string with result
    """
    try:
        storage = _get_storage()
        task = storage.get_task(task_id)
        if not task:
            return json.dumps({"error": f"Task {task_id} not found"}, indent=2)

        storage.update_task(task_id, {'enabled': True})

        return json.dumps({
            "success": True,
            "task_id": task_id,
            "name": task['name'],
            "message": f"Task '{task['name']}' started successfully"
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def stop_background_task(task_id: int) -> str:
    """Stop a background task.

    Args:
        task_id: Task ID

    Returns:
        JSON string with result
    """
    try:
        storage = _get_storage()
        task = storage.get_task(task_id)
        if not task:
            return json.dumps({"error": f"Task {task_id} not found"}, indent=2)

        storage.update_task(task_id, {'enabled': False})

        return json.dumps({
            "success": True,
            "task_id": task_id,
            "name": task['name'],
            "message": f"Task '{task['name']}' stopped successfully"
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def remove_background_task(task_id: int) -> str:
    """Delete a background task permanently.

    Args:
        task_id: Task ID

    Returns:
        JSON string with result
    """
    try:
        storage = _get_storage()
        task = storage.get_task(task_id)
        if not task:
            return json.dumps({"error": f"Task {task_id} not found"}, indent=2)

        task_name = task['name']
        storage.delete_task(task_id)

        return json.dumps({
            "success": True,
            "task_id": task_id,
            "message": f"Task '{task_name}' removed successfully"
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def run_task_immediately(task_id: int) -> str:
    """Execute a task right now (doesn't affect schedule).

    Args:
        task_id: Task ID

    Returns:
        JSON string with result
    """
    try:
        storage = _get_storage()
        task = storage.get_task(task_id)
        if not task:
            return json.dumps({"error": f"Task {task_id} not found"}, indent=2)

        # Note: Immediate execution needs to be handled by main scheduler
        # We just return a message that it should be triggered
        msg = (
            f"Task '{task['name']}' will be executed by scheduler. "
            f"Use /tasks run {task_id} command for immediate execution."
        )
        return json.dumps({
            "success": True,
            "task_id": task_id,
            "name": task['name'],
            "message": msg
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_task_execution_history(
    task_id: int,
    limit: int = 10
) -> str:
    """Get execution history for a task.

    Args:
        task_id: Task ID
        limit: Maximum number of entries to return (default: 10)

    Returns:
        JSON string requesting task history
    """
    result = {
        "action": "get_task_history",
        "task_id": task_id,
        "limit": limit
    }

    return json.dumps(result, indent=2)


@mcp.tool()
def get_latest_task_result(task_id: int) -> str:
    """Get the most recent execution result with AI summary.

    Args:
        task_id: Task ID

    Returns:
        JSON string with latest result
    """
    try:
        storage = _get_storage()
        task = storage.get_task(task_id)
        if not task:
            return json.dumps({"error": f"Task {task_id} not found"}, indent=2)

        result = storage.get_latest_result(task_id)
        if not result:
            return json.dumps({
                "success": True,
                "task_id": task_id,
                "message": "No execution results yet"
            }, indent=2)

        return json.dumps({
            "success": True,
            "task_id": task_id,
            "task_name": task['name'],
            "run_time": result['run_time'],
            "status": result['status'],
            "duration_ms": result.get('duration_ms'),
            "ai_summary": result.get('ai_summary'),
            "error_message": result.get('error_message')
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def update_task_schedule(
    task_id: int,
    schedule_type: str = None,
    schedule_value: str = None
) -> str:
    """Update task scheduling.

    Args:
        task_id: Task ID
        schedule_type: New schedule type (optional)
        schedule_value: New schedule value (optional)

    Returns:
        JSON string with update command
    """
    updates = {}
    if schedule_type is not None:
        updates["schedule_type"] = schedule_type
    if schedule_value is not None:
        updates["schedule_value"] = schedule_value

    result = {
        "action": "update_task",
        "task_id": task_id,
        "updates": updates
    }

    return json.dumps(result, indent=2)


@mcp.tool()
def get_scheduler_status() -> str:
    """Get overall scheduler status and task counts.

    Returns:
        JSON string with scheduler status
    """
    try:
        storage = _get_storage()
        all_tasks = storage.get_all_tasks()
        enabled_tasks = [t for t in all_tasks if t['enabled']]

        return json.dumps({
            "success": True,
            "total_tasks": len(all_tasks),
            "enabled_tasks": len(enabled_tasks),
            "disabled_tasks": len(all_tasks) - len(enabled_tasks),
            "message": "Scheduler is running in main application. Use /tasks status for detailed stats."
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


if __name__ == "__main__":
    # Run the MCP server
    mcp.run(show_banner=False)
