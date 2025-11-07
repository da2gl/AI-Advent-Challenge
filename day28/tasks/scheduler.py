"""Task scheduler for managing and executing background tasks."""

import schedule
import asyncio
import time
import json
from datetime import datetime
from typing import Dict
from .storage import TaskStorage


class TaskScheduler:
    """Manages task scheduling and execution."""

    def __init__(self, storage: TaskStorage, mcp_manager, gemini_client, console):
        """Initialize task scheduler.

        Args:
            storage: TaskStorage instance
            mcp_manager: MCP manager for tool execution
            gemini_client: Gemini API client for AI summaries
            console: Rich console for output
        """
        self.storage = storage
        self.mcp_manager = mcp_manager
        self.gemini_client = gemini_client
        self.console = console
        self.scheduler = schedule.Scheduler()
        self.task_jobs = {}  # task_id -> schedule.Job

    def load_tasks_from_db(self):
        """Load all enabled tasks from database and schedule them."""
        tasks = self.storage.get_enabled_tasks()

        for task in tasks:
            try:
                self._schedule_task(task)
            except Exception as e:
                self.console.print(
                    f"[red]✗ Failed to schedule task {task['id']}: {str(e)}[/red]"
                )

    def _schedule_task(self, task: Dict):
        """Schedule a single task.

        Args:
            task: Task dictionary
        """
        task_id = task['id']
        schedule_type = task['schedule_type']
        schedule_value = task['schedule_value']

        # Remove existing job if any
        if task_id in self.task_jobs:
            self.scheduler.cancel_job(self.task_jobs[task_id])

        # Schedule based on type
        if schedule_type == "interval":
            job = self._schedule_interval(schedule_value, task_id)
        elif schedule_type == "daily":
            job = self._schedule_daily(schedule_value, task_id)
        elif schedule_type == "weekly":
            job = self._schedule_weekly(schedule_value, task_id)
        else:
            raise ValueError(f"Unknown schedule type: {schedule_type}")

        if job:
            self.task_jobs[task_id] = job
            # Update next_run in database
            next_run = job.next_run
            if next_run:
                self.storage.update_task(task_id, {
                    'next_run': next_run.strftime('%Y-%m-%d %H:%M:%S')
                })

    def _schedule_interval(self, interval_value: str, task_id: int):
        """Schedule task with interval.

        Args:
            interval_value: e.g., "30 minutes", "1 hour"
            task_id: Task ID

        Returns:
            Scheduled job
        """
        parts = interval_value.split()
        if len(parts) != 2:
            raise ValueError(f"Invalid interval format: {interval_value}")

        amount = int(parts[0])
        unit = parts[1].lower()

        if unit in ['minute', 'minutes']:
            job = self.scheduler.every(amount).minutes.do(
                self._execute_task_sync, task_id
            )
        elif unit in ['hour', 'hours']:
            job = self.scheduler.every(amount).hours.do(
                self._execute_task_sync, task_id
            )
        elif unit in ['day', 'days']:
            job = self.scheduler.every(amount).days.do(
                self._execute_task_sync, task_id
            )
        else:
            raise ValueError(f"Unknown time unit: {unit}")

        return job

    def _schedule_daily(self, time_value: str, task_id: int):
        """Schedule task daily at specific time.

        Args:
            time_value: e.g., "10:00", "15:30"
            task_id: Task ID

        Returns:
            Scheduled job
        """
        job = self.scheduler.every().day.at(time_value).do(
            self._execute_task_sync, task_id
        )
        return job

    def _schedule_weekly(self, schedule_value: str, task_id: int):
        """Schedule task weekly.

        Args:
            schedule_value: e.g., "Monday 09:00"
            task_id: Task ID

        Returns:
            Scheduled job
        """
        parts = schedule_value.split()
        if len(parts) != 2:
            raise ValueError(f"Invalid weekly format: {schedule_value}")

        day = parts[0].lower()
        time_value = parts[1]

        day_map = {
            'monday': self.scheduler.every().monday,
            'tuesday': self.scheduler.every().tuesday,
            'wednesday': self.scheduler.every().wednesday,
            'thursday': self.scheduler.every().thursday,
            'friday': self.scheduler.every().friday,
            'saturday': self.scheduler.every().saturday,
            'sunday': self.scheduler.every().sunday
        }

        if day not in day_map:
            raise ValueError(f"Unknown day: {day}")

        job = day_map[day].at(time_value).do(
            self._execute_task_sync, task_id
        )
        return job

    def _execute_task_sync(self, task_id: int):
        """Synchronous wrapper for task execution (for schedule library).

        Args:
            task_id: Task ID
        """
        # Run async task execution in event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, create a task
                asyncio.create_task(self.execute_task(task_id))
            else:
                # If no loop, run in new loop
                asyncio.run(self.execute_task(task_id))
        except Exception as e:
            self.console.print(f"[red]✗ Error executing task {task_id}: {str(e)}[/red]")

    async def execute_task(self, task_id: int):
        """Execute a task.

        Args:
            task_id: Task ID
        """
        start_time = time.time()
        task = self.storage.get_task(task_id)

        if not task:
            self.console.print(f"[red]✗ Task {task_id} not found[/red]")
            return

        task_name = task['name']
        mcp_tool = task['mcp_tool']
        tool_args = task['tool_args']
        use_ai_summary = task['use_ai_summary']
        notification_level = task['notification_level']

        # Show notification based on level
        if notification_level in ['all', 'significant']:
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.console.print(f"\n[yellow][{timestamp}] 🔔 Task \"{task_name}\" started[/yellow]")

        try:
            # Execute MCP tool
            result = await self.mcp_manager.call_tool(mcp_tool, tool_args)

            # Extract result data
            raw_data = self._extract_mcp_result(result)

            # Generate AI summary if requested
            ai_summary = None
            if use_ai_summary and raw_data:
                ai_summary = await self._generate_ai_summary(task_name, raw_data)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Save to history
            self.storage.add_history({
                'task_id': task_id,
                'status': 'success',
                'duration_ms': duration_ms,
                'raw_data': raw_data,
                'ai_summary': ai_summary
            })

            # Update last_run
            self.storage.update_task(task_id, {
                'last_run': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

            # Show result notification
            if notification_level in ['all', 'significant']:
                self._display_task_result(task_name, ai_summary or raw_data, duration_ms)

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            # Save error to history
            self.storage.add_history({
                'task_id': task_id,
                'status': 'error',
                'duration_ms': duration_ms,
                'error_message': str(e)
            })

            # Show error (always show errors)
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.console.print(
                f"\n[red][{timestamp}] ✗ Task \"{task_name}\" failed: {str(e)}[/red]"
            )

    def _extract_mcp_result(self, result) -> str:
        """Extract clean data from MCP result.

        Args:
            result: MCP CallToolResult object

        Returns:
            Clean text or JSON string
        """
        try:
            if hasattr(result, 'content'):
                content_list = result.content
                if content_list and len(content_list) > 0:
                    first_content = content_list[0]
                    if hasattr(first_content, 'text'):
                        return first_content.text

            if hasattr(result, 'structured_content') and result.structured_content:
                return json.dumps(result.structured_content, indent=2)

            return str(result)
        except Exception:
            return str(result)

    async def _generate_ai_summary(self, task_name: str, raw_data: str) -> str:
        """Generate AI summary using Gemini.

        Args:
            task_name: Name of the task
            raw_data: Raw data from MCP tool

        Returns:
            AI-generated summary
        """
        try:
            prompt = f"""Analyze this data from the task "{task_name}" and provide a concise,
informative summary (2-3 sentences). Focus on key insights and actionable information.

Data:
{raw_data}

Provide only the summary, no additional commentary."""

            response = self.gemini_client.generate_content(
                prompt=prompt,
                temperature=0.7,
                max_output_tokens=300
            )

            summary = self.gemini_client.extract_text(response)
            return summary

        except Exception as e:
            return f"Failed to generate summary: {str(e)}"

    def _display_task_result(self, task_name: str, content: str, duration_ms: int):
        """Display task execution result.

        Args:
            task_name: Task name
            content: Result content
            duration_ms: Execution duration in milliseconds
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.console.print(f"\n{'=' * 60}", style="bright_cyan")
        self.console.print(f"📊 {task_name}", style="bold bright_cyan")
        self.console.print(f"🕒 {timestamp} | Duration: {duration_ms}ms", style="dim")
        self.console.print(f"{'=' * 60}", style="bright_cyan")

        # Try to display as JSON if possible
        try:
            json.loads(content.strip())
            self.console.print_json(content.strip())
        except (json.JSONDecodeError, TypeError):
            self.console.print(content)

        self.console.print(f"{'─' * 60}", style="dim")

    def add_task(self, task_data: Dict) -> int:
        """Add and schedule a new task.

        Args:
            task_data: Task configuration

        Returns:
            Task ID
        """
        task_id = self.storage.create_task(task_data)
        task = self.storage.get_task(task_id)
        self._schedule_task(task)
        return task_id

    def remove_task(self, task_id: int):
        """Remove a task and cancel its schedule.

        Args:
            task_id: Task ID
        """
        if task_id in self.task_jobs:
            self.scheduler.cancel_job(self.task_jobs[task_id])
            del self.task_jobs[task_id]

        self.storage.delete_task(task_id)

    def start_task(self, task_id: int):
        """Enable and schedule a task.

        Args:
            task_id: Task ID
        """
        self.storage.update_task(task_id, {'enabled': True})
        task = self.storage.get_task(task_id)
        if task:
            self._schedule_task(task)

    def stop_task(self, task_id: int):
        """Disable a task and cancel its schedule.

        Args:
            task_id: Task ID
        """
        if task_id in self.task_jobs:
            self.scheduler.cancel_job(self.task_jobs[task_id])
            del self.task_jobs[task_id]

        self.storage.update_task(task_id, {'enabled': False})

    async def run_task_now(self, task_id: int):
        """Execute a task immediately.

        Args:
            task_id: Task ID
        """
        await self.execute_task(task_id)

    def run_pending(self):
        """Run all pending scheduled tasks."""
        self.scheduler.run_pending()
