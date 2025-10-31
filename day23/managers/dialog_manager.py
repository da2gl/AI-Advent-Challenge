"""Dialog and conversation management."""

from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.spinner import Spinner
from rich.live import Live
from core.storage import SQLiteStorage
from core.conversation import ConversationHistory
from core.gemini_client import GeminiApiClient


class DialogManager:
    """Manages conversation dialogs and history."""

    def __init__(
        self,
        console: Console,
        storage: SQLiteStorage,
        gemini_client: GeminiApiClient
    ):
        """
        Initialize dialog manager.

        Args:
            console: Rich console for output
            storage: SQLite storage for persistence
            gemini_client: Gemini API client for compression
        """
        self.console = console
        self.storage = storage
        self.gemini_client = gemini_client
        self.conversation = None

    def create_new_dialog(self, current_model: str, silent: bool = False) -> ConversationHistory:
        """Create a new dialog and initialize conversation.

        Args:
            current_model: Current model being used
            silent: If True, don't print creation message

        Returns:
            New conversation history
        """
        dialog_id = self.storage.create_dialog(current_model)
        self.conversation = ConversationHistory(self.storage, dialog_id)
        if not silent:
            self.console.print(f"✓ Created new dialog #{dialog_id}", style="green")
        return self.conversation

    def resume_dialog(self):
        """Show dialog list and resume selected one."""
        dialogs = self.storage.list_dialogs()

        # Filter out empty dialogs (0 messages)
        dialogs = [d for d in dialogs if d['message_count'] > 0]

        if not dialogs:
            self.console.print("No previous dialogs found.", style="yellow")
            return

        # Display dialog list
        self.console.print("\n" + "=" * 70, style="bright_cyan")
        self.console.print("              AVAILABLE DIALOGS", style="yellow")
        self.console.print("=" * 70, style="bright_cyan")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Title", style="white", width=40)
        table.add_column("Messages", justify="center", width=8)
        table.add_column("Updated", style="dim", width=15)

        for idx, dialog in enumerate(dialogs, 1):
            # Calculate time ago (both in UTC to match SQLite CURRENT_TIMESTAMP)
            updated = datetime.fromisoformat(dialog['last_updated'])
            # Use modern UTC approach (Python 3.11+) or fallback to utcnow()
            try:
                from datetime import UTC
                now = datetime.now(UTC).replace(tzinfo=None)
            except ImportError:
                now = datetime.utcnow()
            delta = now - updated

            # Calculate total seconds including days
            total_seconds = delta.total_seconds()

            if total_seconds < 60:
                time_ago = "just now"
            elif total_seconds < 3600:
                time_ago = f"{int(total_seconds // 60)}m ago"
            elif total_seconds < 86400:  # Less than 24 hours
                time_ago = f"{int(total_seconds // 3600)}h ago"
            elif delta.days == 1:
                time_ago = "1 day ago"
            else:
                time_ago = f"{delta.days} days ago"

            # Mark current dialog
            marker = "[✓] " if dialog['id'] == self.conversation.dialog_id else ""
            title = marker + dialog['title']

            table.add_row(
                str(idx),
                title,
                str(dialog['message_count']),
                time_ago
            )

        self.console.print(table)
        self.console.print("=" * 70, style="bright_cyan")

        # Get user choice
        choice = input("\nSelect dialog number (or press Enter to cancel): ").strip()

        if not choice:
            return

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(dialogs):
                selected_dialog = dialogs[idx]

                # Load dialog
                self.conversation = ConversationHistory(self.storage, selected_dialog['id'])

                self.console.print(f"\n✓ Loaded dialog #{selected_dialog['id']}: {selected_dialog['title']}", style="green")
                self.console.print(f"📝 History restored: {selected_dialog['message_count']} messages", style="dim")
            else:
                self.console.print("Invalid dialog number", style="red")
        except ValueError:
            self.console.print("Invalid input", style="red")

    def clear_dialog(self, current_model: str):
        """Delete current dialog and create new one.

        Args:
            current_model: Current model being used
        """
        if not self.conversation.dialog_id:
            self.console.print("No active dialog to clear", style="yellow")
            return

        # Delete dialog without confirmation
        self.storage.delete_dialog(self.conversation.dialog_id)

        # Create new dialog silently
        self.conversation = self.create_new_dialog(current_model, silent=True)

    def compress_conversation(self):
        """Compress conversation history."""
        self.console.print("\n🔄 Compressing conversation history...", style="yellow")

        try:
            spinner = Spinner("dots", text="Compressing...", style="yellow")
            with Live(spinner, console=self.console, transient=True):
                result = self.conversation.compress_history(self.gemini_client)

            if result['messages_compressed'] == 0:
                self.console.print("ℹ️  " + result.get('message', 'Nothing to compress'), style="dim")
            else:
                self.console.print("\n" + "=" * 60, style="bright_cyan")
                self.console.print("Compression Results", style="green")
                self.console.print("=" * 60, style="bright_cyan")
                self.console.print(f"Messages compressed: {result['messages_compressed']}", style="dim")
                self.console.print(f"Tokens before: {result['tokens_before']:,}", style="dim")
                self.console.print(f"Tokens after: {result['tokens_after']:,}", style="dim")
                self.console.print(f"Tokens saved: {result['tokens_saved']:,}", style="bright_green bold")
                self.console.print("=" * 60, style="bright_cyan")
                self.console.print("\n✓ Conversation compressed successfully!", style="green")

        except Exception as e:
            self.console.print(f"\n✗ Compression failed: {str(e)}", style="red")

    def show_token_stats(self):
        """Display token statistics."""
        from core.text_manager import TextManager
        stats = self.conversation.get_compression_stats()

        self.console.print("\n" + "=" * 60, style="bright_cyan")
        self.console.print("Token Statistics", style="yellow")
        self.console.print("=" * 60, style="bright_cyan")

        progress = TextManager.format_token_usage(stats['total_tokens'], stats['max_tokens'])
        self.console.print(f"Context Usage: {progress}", style="bold")

        self.console.print(f"\nMessages in history: {stats['message_count']}", style="dim")
        self.console.print(f"Total tokens used: {stats['total_tokens']:,}", style="dim")
        self.console.print(f"Maximum context: {stats['max_tokens']:,}", style="dim")
        self.console.print(f"Percentage used: {stats['percentage']:.1f}%", style="dim")

        if stats['should_compress']:
            self.console.print("\n⚠️  Warning: Context usage is high!", style="yellow")
            self.console.print("💡 Tip: Use /compress to free up space", style="bright_yellow")

        self.console.print("=" * 60, style="bright_cyan")
