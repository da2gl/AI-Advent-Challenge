"""macOS native notification system using osascript."""

import subprocess
from typing import Optional


class MacOSNotifier:
    """Send native macOS notifications using osascript."""

    def __init__(self, enabled: bool = True):
        """Initialize macOS notifier.

        Args:
            enabled: Whether notifications are enabled (default: True)
        """
        self.enabled = enabled

    def _send_notification(
        self,
        title: str,
        message: str,
        sound: bool = False
    ):
        """Send a macOS notification.

        Args:
            title: Notification title
            message: Notification message
            sound: Whether to play a sound (default: False)
        """
        if not self.enabled:
            return

        try:
            # Escape quotes in message
            message = message.replace('"', '\\"')
            title = title.replace('"', '\\"')

            # Build AppleScript
            script = f'display notification "{message}" with title "{title}"'
            if sound:
                script += ' sound name "default"'

            # Execute via osascript
            subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                timeout=5
            )
        except Exception:
            # Silently fail if notification fails
            pass

    def notify_task_start(self, task_name: str):
        """Notify when a task starts execution.

        Args:
            task_name: Name of the task
        """
        self._send_notification(
            title="Task Started",
            message=f"🔄 {task_name}",
            sound=False
        )

    def notify_task_success(
        self,
        task_name: str,
        summary: Optional[str] = None,
        duration_ms: Optional[int] = None
    ):
        """Notify when a task completes successfully.

        Args:
            task_name: Name of the task
            summary: Optional summary of results
            duration_ms: Execution duration in milliseconds
        """
        message = f"✅ {task_name}"
        if duration_ms:
            message += f" ({duration_ms}ms)"
        if summary:
            # Truncate summary to fit notification
            max_len = 100
            if len(summary) > max_len:
                summary = summary[:max_len] + "..."
            message += f"\n{summary}"

        self._send_notification(
            title="Task Completed",
            message=message,
            sound=False
        )

    def notify_task_error(self, task_name: str, error: str):
        """Notify when a task fails with an error.

        Args:
            task_name: Name of the task
            error: Error message
        """
        # Truncate error to fit notification
        max_len = 100
        if len(error) > max_len:
            error = error[:max_len] + "..."

        self._send_notification(
            title="Task Failed",
            message=f"❌ {task_name}\n{error}",
            sound=True  # Play sound for errors
        )

    def enable(self):
        """Enable notifications."""
        self.enabled = True

    def disable(self):
        """Disable notifications."""
        self.enabled = False
