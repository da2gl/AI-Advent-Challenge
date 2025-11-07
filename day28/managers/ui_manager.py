"""UI manager for displaying messages and welcome screens."""

import json
from rich.console import Console
from rich.markdown import Markdown
from core.gemini_client import GeminiModel
from core.ollama_client import OllamaModel
from core.llm_provider import LLMProvider
from core.storage import SQLiteStorage


class UIManager:
    """Manages UI display operations."""

    GEMINI_MODELS = {
        "1": (GeminiModel.GEMINI_2_5_FLASH, "Gemini 2.5 Flash"),
        "2": (GeminiModel.GEMINI_2_5_FLASH_LITE, "Gemini 2.5 Flash Lite"),
        "3": (GeminiModel.GEMINI_2_5_PRO, "Gemini 2.5 Pro"),
    }

    OLLAMA_MODELS = {
        "1": (OllamaModel.QWEN_CODER, "Qwen 2.5 Coder Tools (7B)"),
    }

    def __init__(
        self,
        console: Console,
        storage: SQLiteStorage,
        provider: LLMProvider = LLMProvider.GEMINI
    ):
        """
        Initialize UI manager.

        Args:
            console: Rich console for output
            storage: SQLite storage for dialog info
            provider: LLM provider (Gemini or Ollama)
        """
        self.console = console
        self.storage = storage
        self.provider = provider

    def display_welcome(
        self,
        current_model: str,
        temperature: float,
        top_k: int,
        top_p: float,
        max_output_tokens: int,
        user_name: str = None
    ):
        """Display welcome message.

        Args:
            current_model: Current model being used
            temperature: Temperature setting
            top_k: Top K setting
            top_p: Top P setting
            max_output_tokens: Max output tokens setting
            user_name: User's name from profile (optional)
        """
        self.console.print("\n" + "=" * 60, style="bright_cyan")
        if user_name and user_name != "User":
            self.console.print(f"     AI Assistant - Welcome, {user_name}!", style="bold bright_cyan")
        else:
            self.console.print("     AI Assistant", style="bold bright_cyan")
        self.console.print("=" * 60, style="bright_cyan")
        self.console.print("\nDocument Management:", style="yellow")
        self.console.print("  /index <path> [--collection <name>] - Index documents", style="dim")
        self.console.print("  /search <query> [--collection <name>] - Search index", style="dim")
        self.console.print("  /list-collections - Show all collections", style="dim")
        self.console.print("\nChat Commands:", style="yellow")
        self.console.print("  /voice    - Record voice input and transcribe (press Enter to stop)", style="dim")
        self.console.print("  /resume   - Load previous dialog", style="dim")
        self.console.print("  /clear    - Delete current dialog & create new", style="dim")
        self.console.print("  /model    - Change model", style="dim")
        self.console.print("  /profile  - Manage user info (name, role, preferences, interests)", style="dim")
        self.console.print("  /system   - View/change system instruction", style="dim")
        self.console.print("  /settings - View/change generation settings", style="dim")
        self.console.print("  /compress - Compress conversation history", style="dim")
        self.console.print("  /tokens   - Show token statistics", style="dim")
        self.console.print("  /quit     - Exit chat", style="dim")
        self.console.print("  /help     - Show this help", style="dim")
        self.console.print("=" * 60, style="bright_cyan")

        self.console.print(f"Model: {self._get_model_name(current_model)}", style="dim")
        self.console.print(
            f"Temperature: {temperature} | TopK: {top_k} | "
            f"TopP: {top_p} | MaxTokens: {max_output_tokens}",
            style="dim"
        )
        self.console.print("=" * 60 + "\n", style="bright_cyan")

    def select_provider_and_model(self, current_model: str) -> tuple:
        """Display provider and model selection menu.

        Args:
            current_model: Currently selected model

        Returns:
            tuple: (provider, model) or (None, None) if no change
        """
        self.console.print("\n" + "=" * 50, style="bright_cyan")
        self.console.print("Select Provider:", style="yellow")
        self.console.print("=" * 50, style="bright_cyan")
        self.console.print("  1. Gemini (Cloud)", style="dim")
        self.console.print("  2. Ollama (Local)", style="dim")
        self.console.print("=" * 50, style="bright_cyan")

        provider_choice = input("\nSelect provider (1-2) or press Enter to keep current: ").strip()

        if provider_choice == "1":
            new_provider = LLMProvider.GEMINI
            models = self.GEMINI_MODELS
            provider_name = "Gemini"
        elif provider_choice == "2":
            new_provider = LLMProvider.OLLAMA
            models = self.OLLAMA_MODELS
            provider_name = "Ollama"
        else:
            # Keep current provider
            new_provider = self.provider
            models = self.GEMINI_MODELS if self.provider == LLMProvider.GEMINI else self.OLLAMA_MODELS
            provider_name = "Gemini" if self.provider == LLMProvider.GEMINI else "Ollama"

        # Show models for selected provider
        self.console.print("\n" + "=" * 50, style="bright_cyan")
        self.console.print(f"Available {provider_name} Models:", style="yellow")
        self.console.print("=" * 50, style="bright_cyan")
        for key, (model, name) in models.items():
            marker = "✓" if model == current_model else " "
            style = "green" if marker == "✓" else "dim"
            self.console.print(f"  [{marker}] {key}. {name}", style=style)
        self.console.print("=" * 50, style="bright_cyan")

        max_choice = len(models)
        choice = input(f"\nSelect model (1-{max_choice}) or press Enter to continue: ").strip()
        if choice in models:
            new_model = models[choice][0]
            self.console.print(f"✓ Changed to: {provider_name} - {models[choice][1]}", style="green")
            return new_provider, new_model

        return None, None

    def select_model(self, current_model: str) -> str:
        """Display model selection menu and return selected model.

        Args:
            current_model: Currently selected model

        Returns:
            Selected model (or current if no change)
        """
        # Get models for current provider
        models = self.GEMINI_MODELS if self.provider == LLMProvider.GEMINI else self.OLLAMA_MODELS
        provider_name = "Gemini" if self.provider == LLMProvider.GEMINI else "Ollama"

        self.console.print("\n" + "=" * 50, style="bright_cyan")
        self.console.print(f"Available {provider_name} Models:", style="yellow")
        self.console.print("=" * 50, style="bright_cyan")
        for key, (model, name) in models.items():
            marker = "✓" if model == current_model else " "
            style = "green" if marker == "✓" else "dim"
            self.console.print(f"  [{marker}] {key}. {name}", style=style)
        self.console.print("=" * 50, style="bright_cyan")

        max_choice = len(models)
        choice = input(f"\nSelect model (1-{max_choice}) or press Enter to continue: ").strip()
        if choice in models:
            new_model = models[choice][0]
            self.console.print(f"✓ Model changed to: {models[choice][1]}", style="green")
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
        # Search in both Gemini and Ollama models
        for _, (m, name) in self.GEMINI_MODELS.items():
            if m == model:
                return f"{name} (Gemini)"
        for _, (m, name) in self.OLLAMA_MODELS.items():
            if m == model:
                return f"{name} (Ollama)"
        return model
