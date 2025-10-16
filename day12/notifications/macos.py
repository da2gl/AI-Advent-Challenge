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
        sound: bool = False,
        critical: bool = False
    ):
        """Send a macOS notification.

        Args:
            title: Notification title
            message: Notification message
            sound: Whether to play a sound (default: False)
            critical: Whether to show as critical alert (more visible, default: False)
        """
        if not self.enabled:
            return

        try:
            # Escape quotes and special characters in message
            message = message.replace('"', '\\"').replace('$', '\\$')
            title = title.replace('"', '\\"').replace('$', '\\$')

            # Use display alert for critical notifications (more visible)
            if critical:
                # Display alert shows a modal dialog - very visible but blocking
                script = f'display alert "{title}" message "{message}"'
                if sound:
                    script += ' giving up after 5'  # Auto-dismiss after 5 seconds
            else:
                # Standard notification with subtitle for better visibility
                script = f'display notification "{message}" with title "{title}" subtitle "MCP Pipeline Agent"'
                if sound:
                    script += ' sound name "Glass"'  # More noticeable sound

            # Execute via osascript
            subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                timeout=10
            )

            # Also play a system sound for better visibility
            if sound:
                subprocess.run(
                    ['afplay', '/System/Library/Sounds/Glass.aiff'],
                    capture_output=True,
                    timeout=2
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
            sound=True  # Sound for better visibility
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
            sound=True,  # Sound for completion
            critical=False  # Not critical, use banner
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
            sound=True,  # Play sound for errors
            critical=True  # Show as critical alert for errors
        )

    def enable(self):
        """Enable notifications."""
        self.enabled = True

    def disable(self):
        """Disable notifications."""
        self.enabled = False
