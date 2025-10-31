"""UI manager for displaying messages and welcome screens."""

import json
from rich.console import Console
from rich.markdown import Markdown
from core.gemini_client import GeminiModel
from core.storage import SQLiteStorage


class UIManager:
    """Manages UI display operations."""

    MODELS = {
        "1": (GeminiModel.GEMINI_2_5_FLASH, "Gemini 2.5 Flash"),
        "2": (GeminiModel.GEMINI_2_5_FLASH_LITE, "Gemini 2.5 Flash Lite"),
        "3": (GeminiModel.GEMINI_2_5_PRO, "Gemini 2.5 Pro"),
    }

    def __init__(
        self,
        console: Console,
        storage: SQLiteStorage
    ):
        """
        Initialize UI manager.

        Args:
            console: Rich console for output
            storage: SQLite storage for dialog info
        """
        self.console = console
        self.storage = storage

    def display_welcome(
        self,
        current_model: str,
        dialog_id: int,
        temperature: float,
        top_k: int,
        top_p: float,
        max_output_tokens: int,
        system_instruction: str
    ):
        """Display welcome message.

        Args:
            current_model: Current model being used
            dialog_id: Current dialog ID
            temperature: Temperature setting
            top_k: Top K setting
            top_p: Top P setting
            max_output_tokens: Max output tokens setting
            system_instruction: System instruction text
        """
        self.console.print("\n" + "=" * 60, style="bright_cyan")
        self.console.print("     AI Assistant", style="bold bright_cyan")
        self.console.print("=" * 60, style="bright_cyan")
        self.console.print("\nDocument Management:", style="yellow")
        self.console.print("  /index <path> [--collection <name>] - Index documents", style="dim")
        self.console.print("  /search <query> [--collection <name>] - Search index", style="dim")
        self.console.print("  /list-collections - Show all collections", style="dim")
        self.console.print("  /load-koog [--force] - Load Koog docs (cached, use --force to reindex)", style="dim")
        self.console.print("  /koog-info - Show loaded docs & suggest questions", style="dim")
        self.console.print("\nChat Commands:", style="yellow")
        self.console.print("  /resume   - Load previous dialog", style="dim")
        self.console.print("  /clear    - Delete current dialog & create new", style="dim")
        self.console.print("  /model    - Change model", style="dim")
        self.console.print("  /system   - View/change system instruction", style="dim")
        self.console.print("  /settings - View/change generation settings", style="dim")
        self.console.print("  /compress - Compress conversation history", style="dim")
        self.console.print("  /tokens   - Show token statistics", style="dim")
        self.console.print("  /quit     - Exit chat", style="dim")
        self.console.print("  /help     - Show this help", style="dim")
        self.console.print("=" * 60, style="bright_cyan")

        # Show current dialog info
        if dialog_id:
            dialog_info = self.storage.get_dialog_info(dialog_id)
            if dialog_info:
                self.console.print(f"Dialog #{dialog_info['id']}: {dialog_info['title']}", style="green")
                self.console.print(f"Messages: {dialog_info['message_count']}", style="dim")

        self.console.print(f"Model: {self._get_model_name(current_model)}", style="dim")
        self.console.print(
            f"Temperature: {temperature} | TopK: {top_k} | "
            f"TopP: {top_p} | MaxTokens: {max_output_tokens}",
            style="dim"
        )
        if system_instruction:
            instruction_preview = system_instruction[:50] + "..." if len(system_instruction) > 50 else system_instruction
            self.console.print(f"System instruction: {instruction_preview}", style="dim")
        self.console.print("=" * 50 + "\n", style="bright_cyan")

    def select_model(self, current_model: str) -> str:
        """Display model selection menu and return selected model.

        Args:
            current_model: Currently selected model

        Returns:
            Selected model (or current if no change)
        """
        self.console.print("\n" + "=" * 50, style="bright_cyan")
        self.console.print("Available Models:", style="yellow")
        self.console.print("=" * 50, style="bright_cyan")
        for key, (model, name) in self.MODELS.items():
            marker = "✓" if model == current_model else " "
            style = "green" if marker == "✓" else "dim"
            self.console.print(f"  [{marker}] {key}. {name}", style=style)
        self.console.print("=" * 50, style="bright_cyan")

        choice = input("\nSelect model (1-3) or press Enter to continue: ").strip()
        if choice in self.MODELS:
            new_model = self.MODELS[choice][0]
            self.console.print(f"✓ Model changed to: {self.MODELS[choice][1]}", style="green")
            return new_model

        return current_model

    def print_response(self, text: str):
        """Print response with formatting.

        Args:
            text: Response text to print
        """
        try:
            json.loads(text.strip())
            self.console.print()
            self.console.print_json(text.strip())
        except (json.JSONDecodeError, TypeError):
            self.console.print()
            self.console.print(Markdown(text))

    def _get_model_name(self, model: str) -> str:
        """Get human-readable name of model.

        Args:
            model: Model constant

        Returns:
            Human-readable model name
        """
        for _, (m, name) in self.MODELS.items():
            if m == model:
                return name
        return model
