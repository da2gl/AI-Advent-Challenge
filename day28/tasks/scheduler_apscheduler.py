"""Enhanced task scheduler using APScheduler for production-ready scheduling."""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
import asyncio
import time
import json
from datetime import datetime
from typing import Dict
from .storage import TaskStorage


class APTaskScheduler:
    """Task scheduler using APScheduler for robust background execution."""

    def __init__(self, storage: TaskStorage, mcp_manager, gemini_client, console, notifier=None):
        """Initialize APScheduler-based task scheduler.

        Args:
            storage: TaskStorage instance
            mcp_manager: MCP manager for tool execution
            gemini_client: Gemini API client for AI summaries
            console: Rich console for output
            notifier: MacOSNotifier instance for notifications (optional)
        """
        self.storage = storage
        self.mcp_manager = mcp_manager
        self.gemini_client = gemini_client
        self.console = console
        self.notifier = notifier  # macOS notifier

        # Statistics
        self.stats = {
            'tasks_executed': 0,
            'tasks_failed': 0,
            'tasks_missed': 0,
            'started_at': None
        }

        # Configure job store (in-memory - SQLAlchemy can't pickle async objects)
        jobstores = {
            'default': MemoryJobStore()
        }

        # Configure executor (thread pool)
        executors = {
            'default': ThreadPoolExecutor(max_workers=5)  # Max 5 parallel tasks
        }

        # Configure job defaults
        job_defaults = {
            'coalesce': True,  # Combine multiple missed runs into one
            'max_instances': 3,  # Allow up to 3 concurrent runs of same task
            'misfire_grace_time': 300  # 5 minutes grace period for missed jobs
        }

        # Create scheduler
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )

        # Add event listeners for monitoring
        self.scheduler.add_listener(
            self._on_job_event,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED
        )

        self.task_jobs = {}  # task_id -> job_id mapping

    def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            self.stats['started_at'] = datetime.now()
            self.scheduler.start()

            # Load initial tasks
            self.load_tasks_from_db()

            # Add periodic task sync job (every 10 seconds)
            # Note: This runs in main thread, not ThreadPoolExecutor
            def sync_wrapper():
                """Wrapper to ensure sync runs in scheduler's thread."""
                try:
                    self.sync_tasks_from_db()
                except Exception as e:
                    self.console.print(f"[red]Sync error: {str(e)}[/red]")

            self.scheduler.add_job(
                func=sync_wrapper,
                trigger=IntervalTrigger(seconds=10),
                id="_sync_tasks",
                replace_existing=True,
                executor='default'  # Use default executor
            )

            self.console.print("[green]✓ APScheduler started[/green]")

    def stop(self):
        """Stop the scheduler gracefully."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            self.console.print("[yellow]APScheduler stopped[/yellow]")

    def load_tasks_from_db(self):
        """Load all enabled tasks from database and schedule them."""
        tasks = self.storage.get_enabled_tasks()

        for task in tasks:
            # Skip if already scheduled
            if task['id'] in self.task_jobs:
                continue

            try:
                self._schedule_task(task)
            except Exception as e:
                self.console.print(
                    f"[red]✗ Failed to schedule task {task['id']}: {str(e)}[/red]"
                )

        if len(tasks) > 0:
            self.console.print(
                f"[green]✓ Loaded {len(tasks)} task(s) from database[/green]"
            )

    def sync_tasks_from_db(self):
        """Sync tasks from database - add new, remove deleted, update changed."""
        db_tasks = self.storage.get_all_tasks()
        db_task_ids = {task['id'] for task in db_tasks}
        scheduled_task_ids = set(self.task_jobs.keys())

        # Remove deleted tasks
        for task_id in scheduled_task_ids - db_task_ids:
            self.remove_task(task_id)

        # Add or update tasks
        for task in db_tasks:
            task_id = task['id']
            if task['enabled']:
                # Schedule if not scheduled, or reschedule if already exists
                try:
                    self._schedule_task(task)
                except Exception as e:
                    import traceback
                    self.console.print(f"[red]✗ Failed to schedule task {task_id}: {str(e)}[/red]")
                    traceback.print_exc()
            else:
                # Remove from scheduler if disabled
                if task_id in self.task_jobs:
                    self.stop_task(task_id)

    def _schedule_task(self, task: Dict):
        """Schedule a single task using APScheduler.

        Args:
            task: Task dictionary
        """
        task_id = task['id']
        schedule_type = task['schedule_type']
        schedule_value = task['schedule_value']

        # Remove existing job if any
        if task_id in self.task_jobs:
            job_id = self.task_jobs[task_id]
            try:
                self.scheduler.remove_job(job_id)
            except Exception:
                pass

        # Create trigger based on schedule type
        if schedule_type == "interval":
            trigger = self._create_interval_trigger(schedule_value)
        elif schedule_type == "daily":
            trigger = self._create_daily_trigger(schedule_value)
        elif schedule_type == "weekly":
            trigger = self._create_weekly_trigger(schedule_value)
        else:
            raise ValueError(f"Unknown schedule type: {schedule_type}")

        # Add job to scheduler
        job = self.scheduler.add_job(
            func=self._execute_task_wrapper,
            trigger=trigger,
            args=[task_id],
            id=f"task_{task_id}",
            replace_existing=True,
            max_instances=3,  # Allow parallel execution
            misfire_grace_time=300
        )

        self.task_jobs[task_id] = job.id

        # Update next_run in database
        if job.next_run_time:
            self.storage.update_task(task_id, {
                'next_run': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
            })

    def _create_interval_trigger(self, interval_value: str):
        """Create interval trigger from string like '30 minutes'.

        Args:
            interval_value: Interval string (e.g., "5 seconds", "30 minutes", "1 hour")

        Returns:
            IntervalTrigger instance
        """
        parts = interval_value.split()
        if len(parts) != 2:
            raise ValueError(f"Invalid interval format: {interval_value}")

        amount = int(parts[0])
        unit = parts[1].lower().rstrip('s')  # Remove trailing 's' to normalize

        if unit == 'second':
            return IntervalTrigger(seconds=amount)
        elif unit == 'minute':
            return IntervalTrigger(minutes=amount)
        elif unit == 'hour':
            return IntervalTrigger(hours=amount)
        elif unit == 'day':
            return IntervalTrigger(days=amount)
        else:
            raise ValueError(f"Unknown time unit: {unit}")

    def _create_daily_trigger(self, time_value: str):
        """Create daily trigger from time string like '10:00'.

        Args:
            time_value: Time string (e.g., "10:00", "15:30")

        Returns:
            CronTrigger instance
        """
        hour, minute = map(int, time_value.split(':'))
        return CronTrigger(hour=hour, minute=minute)

    def _create_weekly_trigger(self, schedule_value: str):
        """Create weekly trigger from string like 'Monday 09:00'.

        Args:
            schedule_value: Schedule string (e.g., "Monday 09:00")

        Returns:
            CronTrigger instance
        """
        parts = schedule_value.split()
        if len(parts) != 2:
            raise ValueError(f"Invalid weekly format: {schedule_value}")

        day_of_week = parts[0].lower()
        hour, minute = map(int, parts[1].split(':'))

        day_map = {
            'monday': 'mon',
            'tuesday': 'tue',
            'wednesday': 'wed',
            'thursday': 'thu',
            'friday': 'fri',
            'saturday': 'sat',
            'sunday': 'sun'
        }

        if day_of_week not in day_map:
            raise ValueError(f"Unknown day: {day_of_week}")

        return CronTrigger(
            day_of_week=day_map[day_of_week],
            hour=hour,
            minute=minute
        )

    def _execute_task_wrapper(self, task_id: int):
        """Wrapper to run async task in sync context (for APScheduler).

        Args:
            task_id: Task ID
        """
        self.console.print(f"[cyan]>>> Task {task_id} execution started at {datetime.now()}[/cyan]")

        # Execute in separate event loop (in APScheduler thread)
        # This works because we don't need MCP clients - we only need storage/gemini
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.execute_task(task_id))
                self.console.print(f"[green]>>> Task {task_id} completed successfully[/green]")
            finally:
                loop.close()
        except Exception as e:
            self.console.print(f"[red]✗ Error executing task {task_id}: {str(e)}[/red]")
            import traceback
            traceback.print_exc()
            # Don't re-raise - task will be retried on next schedule

    async def execute_task(self, task_id: int):
        """Execute a task.

        Args:
            task_id: Task ID
        """
        start_time = time.time()
        task = self.storage.get_task(task_id)

        if not task:
            return

        task_name = task['name']
        mcp_tool = task['mcp_tool']
        tool_args = task['tool_args']
        use_ai_summary = task['use_ai_summary']
        notification_level = task['notification_level']

        try:
            # Execute MCP tool using shared mcp_manager
            # Note: We create a new MCP connection in each thread's event loop
            # This is safe because each APScheduler thread has its own loop
            from mcp_clients import MCPManager

            # Create temporary manager for this thread's event loop
            thread_mcp = MCPManager()

            # Determine which client type to use based on tool name
            client_type = None
            if 'crypto' in mcp_tool or 'bitcoin' in mcp_tool.lower():
                client_type = 'crypto'
            elif 'background' in mcp_tool or 'task' in mcp_tool.lower():
                client_type = 'background'

            # Connect to appropriate client
            if client_type:
                await thread_mcp.connect_client(client_type)
                result = await thread_mcp.call_tool(
                    mcp_tool, tool_args, client_type=client_type
                )
                await thread_mcp.disconnect_all()
            else:
                # If client type unknown, let manager search all clients
                raise ValueError(
                    f"Cannot determine MCP client type for tool: {mcp_tool}"
                )

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

            # Send notification with AI summary (only if summary exists and enabled)
            if self.notifier and notification_level in ['all', 'significant']:
                if ai_summary:
                    # Show only AI summary
                    self.notifier._send_notification(
                        title=task_name,
                        message=ai_summary,
                        sound=False
                    )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            # Save error to history
            self.storage.add_history({
                'task_id': task_id,
                'status': 'error',
                'duration_ms': duration_ms,
                'error_message': str(e)
            })

            # Send notification: task failed (always notify on errors)
            if self.notifier and notification_level != 'silent':
                self.notifier.notify_task_error(task_name, str(e))

            raise  # Re-raise for APScheduler

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
informative summary in exactly 2-3 short sentences. Focus on key insights and actionable information.

Data:
{raw_data}

Provide only the summary, no additional commentary."""

            response = self.gemini_client.generate_content(
                prompt=prompt,
                temperature=0.7,
                max_output_tokens=2048
            )

            summary = self.gemini_client.extract_text(response)
            return summary

        except Exception as e:
            return f"Failed to generate summary: {str(e)}"

    def _on_job_event(self, event):
        """Handle APScheduler job events for monitoring.

        Args:
            event: Job event from APScheduler
        """
        if event.code == EVENT_JOB_EXECUTED:
            self.stats['tasks_executed'] += 1
        elif event.code == EVENT_JOB_ERROR:
            self.stats['tasks_failed'] += 1
        elif event.code == EVENT_JOB_MISSED:
            self.stats['tasks_missed'] += 1
            self.console.print(f"[yellow]⚠ Task {event.job_id} missed its schedule[/yellow]")

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
            job_id = self.task_jobs[task_id]
            try:
                self.scheduler.remove_job(job_id)
            except Exception:
                pass
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
            job_id = self.task_jobs[task_id]
            try:
                self.scheduler.remove_job(job_id)
            except Exception:
                pass
            del self.task_jobs[task_id]

        self.storage.update_task(task_id, {'enabled': False})

    def pause_task(self, task_id: int):
        """Pause a task (keeps it scheduled but won't execute).

        Args:
            task_id: Task ID
        """
        if task_id in self.task_jobs:
            job_id = self.task_jobs[task_id]
            try:
                self.scheduler.pause_job(job_id)
                self.console.print(f"[yellow]Task {task_id} paused[/yellow]")
            except Exception as e:
                self.console.print(f"[red]Failed to pause task: {str(e)}[/red]")

    def resume_task(self, task_id: int):
        """Resume a paused task.

        Args:
            task_id: Task ID
        """
        if task_id in self.task_jobs:
            job_id = self.task_jobs[task_id]
            try:
                self.scheduler.resume_job(job_id)
                self.console.print(f"[green]Task {task_id} resumed[/green]")
            except Exception as e:
                self.console.print(f"[red]Failed to resume task: {str(e)}[/red]")

    async def run_task_now(self, task_id: int):
        """Execute a task immediately (doesn't affect schedule).

        Args:
            task_id: Task ID
        """
        await self.execute_task(task_id)

    def get_stats(self) -> Dict:
        """Get scheduler statistics.

        Returns:
            Dictionary with scheduler stats
        """
        uptime = 0
        if self.stats['started_at']:
            uptime = (datetime.now() - self.stats['started_at']).total_seconds()

        return {
            **self.stats,
            'uptime_seconds': uptime,
            'scheduler_running': self.scheduler.running,
            'active_jobs': len(self.task_jobs)
        }

    def run_pending(self):
        """Compatibility method - APScheduler handles this automatically."""
        pass  # APScheduler runs in background automatically
