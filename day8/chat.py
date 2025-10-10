"""Console chat interface for Gemini API."""

import json
import os
import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.live import Live

from conversation import ConversationHistory
from gemini_client import GeminiApiClient, GeminiModel
from text_manager import TextManager
from demo import DemoMode


class ConsoleChat:
    """Console-based chat interface."""

    MODELS = {
        "1": (GeminiModel.GEMINI_2_5_FLASH, "Gemini 2.5 Flash (Fast & Balanced)"),
        "2": (GeminiModel.GEMINI_2_5_FLASH_LITE, "Gemini 2.5 Flash Lite (Ultra Fast)"),
        "3": (GeminiModel.GEMINI_2_5_PRO, "Gemini 2.5 Pro (Most Advanced)")
    }

    DEFAULT_SYSTEM_INSTRUCTION = None

    def __init__(self):
        """Initialize chat interface."""
        self.api_key = self._get_api_key()
        self.client = GeminiApiClient(self.api_key)
        self.conversation = ConversationHistory()
        self.current_model = GeminiModel.GEMINI_2_5_FLASH
        self.system_instruction = self.DEFAULT_SYSTEM_INSTRUCTION
        self.console = Console()

        # Generation settings
        self.temperature = 0.7
        self.top_k = 40
        self.top_p = 0.95
        self.max_output_tokens = 2048

    @staticmethod
    def _get_api_key() -> str:
        """Get API key from environment or user input.

        Returns:
            API key string
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("GEMINI_API_KEY not found in environment.")
            api_key = input("Enter your Gemini API key: ").strip()
            if not api_key:
                print("Error: API key is required")
                sys.exit(1)
        return api_key

    def select_model(self):
        """Display model selection menu and set current model."""
        self.console.print("\n" + "=" * 50, style="bright_cyan")
        self.console.print("Available Models:", style="yellow")
        self.console.print("=" * 50, style="bright_cyan")
        for key, (_, name) in self.MODELS.items():
            marker = "✓" if self.MODELS[key][0] == self.current_model else " "
            style = "green" if marker == "✓" else "dim"
            self.console.print(f"  [{marker}] {key}. {name}", style=style)
        self.console.print("=" * 50, style="bright_cyan")

        choice = input("\nSelect model (1-3) or press Enter to continue: ").strip()
        if choice in self.MODELS:
            self.current_model = self.MODELS[choice][0]
            self.console.print(f"✓ Model changed to: {self.MODELS[choice][1]}", style="green")
            # Clear history when changing models
            self.conversation.clear()
            self.console.print("✓ Conversation history cleared", style="green")

    def display_welcome(self):
        """Display welcome message."""
        self.console.print("\n" + "=" * 50, style="bright_cyan")
        self.console.print("     GEMINI CHAT - AI Assistant", style="bold bright_cyan")
        self.console.print("=" * 50, style="bright_cyan")
        self.console.print("Commands:", style="yellow")
        self.console.print("  /model    - Change model", style="dim")
        self.console.print("  /system   - View/change system instruction", style="dim")
        self.console.print("  /settings - View/change generation settings", style="dim")
        self.console.print("  /compress - Compress conversation history", style="bright_yellow")
        self.console.print("  /tokens   - Show token statistics", style="bright_yellow")
        self.console.print("  /demo     - Run compression demo (reduced limits)", style="bright_magenta")
        self.console.print("  /clear    - Clear conversation history", style="dim")
        self.console.print("  /quit     - Exit chat", style="dim")
        self.console.print("  /help     - Show this help", style="dim")
        self.console.print("=" * 50, style="bright_cyan")
        self.console.print(f"Current model: {self._get_model_name()}", style="green")
        self.console.print(
            f"Temperature: {self.temperature} | TopK: {self.top_k} | "
            f"TopP: {self.top_p} | MaxTokens: {self.max_output_tokens}",
            style="dim"
        )
        if self.system_instruction:
            if len(self.system_instruction) > 50:
                instruction_preview = self.system_instruction[:50] + "..."
            else:
                instruction_preview = self.system_instruction
            self.console.print(f"System instruction: {instruction_preview}", style="dim")
        else:
            self.console.print("System instruction: None", style="dim")
        self.console.print("=" * 50 + "\n", style="bright_cyan")

    def _get_model_name(self) -> str:
        """Get human-readable name of current model."""
        for _, (model, name) in self.MODELS.items():
            if model == self.current_model:
                return name
        return self.current_model

    def _print_response(self, text: str):
        """Print response with JSON formatting if applicable.

        Args:
            text: Response text to print
        """
        # Try to parse as JSON and print with rich formatting
        try:
            json.loads(text.strip())  # Validate JSON
            self.console.print()  # New line after "Assistant: "
            self.console.print_json(text.strip())
        except (json.JSONDecodeError, TypeError):
            # Not JSON, print as markdown with rich
            self.console.print()  # New line after "Assistant: "
            self.console.print(Markdown(text))

    def manage_system_instruction(self):
        """Display and optionally change system instruction."""
        self.console.print("\n" + "=" * 50, style="bright_cyan")
        self.console.print("System Instruction Management", style="yellow")
        self.console.print("=" * 50, style="bright_cyan")
        self.console.print(f"Current: {self.system_instruction}", style="dim")
        self.console.print("=" * 50, style="bright_cyan")

        choice = input("\nEnter new instruction (or press Enter to keep current): ").strip()
        if choice:
            self.system_instruction = choice
            self.console.print("✓ System instruction updated", style="green")
            # Clear history when changing system instruction
            self.conversation.clear()
            self.console.print("✓ Conversation history cleared", style="green")

    def manage_generation_settings(self):
        """Display and optionally change generation settings."""
        self.console.print("\n" + "=" * 50, style="bright_cyan")
        self.console.print("Generation Settings", style="yellow")
        self.console.print("=" * 50, style="bright_cyan")
        self.console.print(f"1. Temperature:       {self.temperature} (0.0-2.0, higher = more creative)", style="dim")
        self.console.print(f"2. Top K:             {self.top_k} (1-100)", style="dim")
        self.console.print(f"3. Top P:             {self.top_p} (0.0-1.0)", style="dim")
        self.console.print(f"4. Max Output Tokens: {self.max_output_tokens}", style="dim")
        self.console.print("=" * 50, style="bright_cyan")

        choice = input("\nSelect setting to change (1-4) or press Enter to skip: ").strip()

        if choice == "1":
            new_val = input(f"Enter new temperature (current: {self.temperature}): ").strip()
            try:
                val = float(new_val)
                if 0.0 <= val <= 2.0:
                    self.temperature = val
                    self.console.print(f"✓ Temperature set to {val}", style="green")
                else:
                    self.console.print("✗ Temperature must be between 0.0 and 2.0", style="red")
            except ValueError:
                self.console.print("✗ Invalid number", style="red")
        elif choice == "2":
            new_val = input(f"Enter new top K (current: {self.top_k}): ").strip()
            try:
                val = int(new_val)
                if val >= 1:
                    self.top_k = val
                    self.console.print(f"✓ Top K set to {val}", style="green")
                else:
                    self.console.print("✗ Top K must be at least 1", style="red")
            except ValueError:
                self.console.print("✗ Invalid number", style="red")
        elif choice == "3":
            new_val = input(f"Enter new top P (current: {self.top_p}): ").strip()
            try:
                val = float(new_val)
                if 0.0 <= val <= 1.0:
                    self.top_p = val
                    self.console.print(f"✓ Top P set to {val}", style="green")
                else:
                    self.console.print("✗ Top P must be between 0.0 and 1.0", style="red")
            except ValueError:
                self.console.print("✗ Invalid number", style="red")
        elif choice == "4":
            new_val = input(f"Enter new max output tokens (current: {self.max_output_tokens}): ").strip()
            try:
                val = int(new_val)
                if val >= 1:
                    self.max_output_tokens = val
                    self.console.print(f"✓ Max output tokens set to {val}", style="green")
                else:
                    self.console.print("✗ Max tokens must be at least 1", style="red")
            except ValueError:
                self.console.print("✗ Invalid number", style="red")

    def show_token_stats(self):
        """Display detailed token statistics."""
        stats = self.conversation.get_compression_stats()

        self.console.print("\n" + "=" * 60, style="bright_cyan")
        self.console.print("Token Statistics", style="yellow")
        self.console.print("=" * 60, style="bright_cyan")

        # Display progress bar
        progress = TextManager.format_token_usage(
            stats['total_tokens'],
            stats['max_tokens']
        )
        self.console.print(f"Context Usage: {progress}", style="bold")

        self.console.print(f"\nMessages in history: {stats['message_count']}", style="dim")
        self.console.print(f"Total tokens used: {stats['total_tokens']:,}", style="dim")
        self.console.print(f"Maximum context: {stats['max_tokens']:,}", style="dim")
        self.console.print(f"Percentage used: {stats['percentage']:.1f}%", style="dim")
        self.console.print(f"Compressed: {'Yes' if stats['compressed'] else 'No'}", style="dim")

        if stats['should_compress']:
            self.console.print("\n⚠️  Warning: Context usage is high!", style="yellow")
            self.console.print("💡 Tip: Use /compress to free up space", style="bright_yellow")

        self.console.print("=" * 60, style="bright_cyan")

    def compress_conversation(self):
        """Compress conversation history."""
        self.console.print("\n🔄 Compressing conversation history...", style="yellow")

        try:
            # Show spinner during compression API call
            spinner = Spinner("dots", text="Compressing...", style="yellow")
            with Live(spinner, console=self.console, transient=True):
                result = self.conversation.compress_history(self.client)

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
                self.console.print(f"Compression ratio: {result['compression_ratio']:.1%}", style="dim")
                self.console.print("=" * 60, style="bright_cyan")
                self.console.print("\n✓ Conversation compressed successfully!", style="green")

        except Exception as e:
            self.console.print(f"\n✗ Compression failed: {str(e)}", style="red")

    def run_demo(self):
        """Run demonstration mode with reduced token limits."""
        demo = DemoMode(self.client, self.conversation, self.console)
        demo.run(
            self.current_model,
            self.system_instruction,
            self.temperature,
            self.top_k,
            self.top_p,
            self.max_output_tokens
        )

    def handle_command(self, command: str) -> bool:
        """Handle special commands.

        Args:
            command: Command string (starting with /)

        Returns:
            True if should continue, False if should exit
        """
        command = command.lower().strip()

        if command == "/quit":
            self.console.print("\nGoodbye!", style="bold bright_cyan")
            return False
        elif command == "/clear":
            self.conversation.clear()
            self.console.print("✓ Conversation history cleared", style="green")
        elif command == "/model":
            self.select_model()
        elif command == "/system":
            self.manage_system_instruction()
        elif command == "/settings":
            self.manage_generation_settings()
        elif command == "/tokens":
            self.show_token_stats()
        elif command == "/compress":
            self.compress_conversation()
        elif command == "/demo":
            self.run_demo()
        elif command == "/help":
            self.display_welcome()
        else:
            self.console.print(f"Unknown command: {command}", style="red")
            self.console.print("Type /help for available commands", style="dim")

        return True

    def chat_loop(self):
        """Main chat loop."""
        self.display_welcome()

        while True:
            try:
                # Get user input with colored prompt
                self.console.print("\n", end="")
                self.console.print("You: ", style="bold bright_blue", end="")
                user_input = input().strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    if not self.handle_command(user_input):
                        break
                    continue

                # Check if input text is too long and needs compression
                prompt_to_send = user_input
                if ConversationHistory.should_compress_input(user_input):
                    input_tokens = TextManager.estimate_tokens(user_input)
                    self.console.print(
                        f"\n[yellow]⚠️  Input too long ({input_tokens:,} tokens)! Compressing...[/yellow]"
                    )
                    try:
                        # Show spinner during input compression
                        spinner = Spinner("dots", text="Compressing input...", style="yellow")
                        with Live(spinner, console=self.console, transient=True):
                            summary_result = TextManager.summarize_text(
                                text=user_input,
                                client=self.client,
                                max_tokens=2000,  # Compress to max 2000 tokens
                                language="mixed",
                                timeout=15  # 15 second timeout (faster failure)
                            )
                        prompt_to_send = summary_result['summary']
                        self.console.print(
                            f"[green]✓ Compressed input: {input_tokens:,} → "
                            f"{summary_result['summary_tokens']:,} tokens[/green]"
                        )
                    except Exception as e:
                        self.console.print(f"[red]✗ Compression failed: {str(e)}[/red]")
                        self.console.print("[yellow]Sending original text...[/yellow]")

                # Add user message to history (use compressed version if available)
                self.conversation.add_user_message(prompt_to_send)

                # Send request to Gemini with loading animation
                spinner = Spinner("dots", text="Thinking...", style="bright_magenta")
                with Live(spinner, console=self.console, transient=True):
                    response = self.client.generate_content(
                        prompt=prompt_to_send,
                        model=self.current_model,
                        conversation_history=self.conversation.get_history(),
                        system_instruction=self.system_instruction,
                        temperature=self.temperature,
                        top_k=self.top_k,
                        top_p=self.top_p,
                        max_output_tokens=self.max_output_tokens
                    )

                # Show Assistant label after spinner
                self.console.print("Assistant: ", style="bold bright_magenta", end="")

                # Extract and display response
                assistant_text = self.client.extract_text(response)
                self._print_response(assistant_text)

                # Display token usage if available
                usage = self.client.extract_usage_metadata(response)
                if usage:
                    self.conversation.add_tokens(usage['total_tokens'])

                    # Show detailed token breakdown
                    self.console.print(
                        f"\n[dim]Tokens: {usage['prompt_tokens']} prompt + "
                        f"{usage['response_tokens']} response = "
                        f"{usage['total_tokens']} total[/dim]"
                    )

                    # Show context usage with progress bar
                    progress = TextManager.format_token_usage(
                        self.conversation.total_tokens,
                        ConversationHistory.MAX_CONTEXT_TOKENS
                    )
                    self.console.print(f"[dim]Context: {progress}[/dim]")

                    # Auto-compress if approaching limit
                    if self.conversation.should_compress():
                        self.console.print(
                            "\n[yellow]⚠️  Context limit reached! Auto-compressing...[/yellow]"
                        )
                        try:
                            # Show spinner during compression API call
                            spinner = Spinner("dots", text="Compressing conversation history...", style="yellow")
                            with Live(spinner, console=self.console, transient=True):
                                result = self.conversation.compress_history(self.client)

                            if result['messages_compressed'] > 0:
                                self.console.print(
                                    f"[green]✓ Compressed {result['messages_compressed']} messages, "
                                    f"saved {result['tokens_saved']:,} tokens[/green]"
                                )
                            else:
                                self.console.print(
                                    f"[dim]ℹ {result.get('message', 'No compression needed')}[/dim]"
                                )
                        except Exception as e:
                            self.console.print(
                                f"[red]✗ Auto-compression failed: {str(e)}[/red]\n"
                                f"[dim]Try reducing message length or clearing history with /clear[/dim]"
                            )

                # Add assistant message to history
                self.conversation.add_assistant_message(assistant_text)

            except KeyboardInterrupt:
                print("\n\nInterrupted by user")
                confirm = input("Do you want to exit? (y/n): ").strip().lower()
                if confirm == "y":
                    break
            except Exception as e:
                print(f"\n✗ Error: {str(e)}")
                print("Please try again or type /quit to exit")

        # Cleanup
        self.client.close()

    def run(self):
        """Start the chat application."""
        try:
            self.chat_loop()
        except Exception as e:
            print(f"Fatal error: {str(e)}")
            sys.exit(1)


def main():
    """Entry point for the chat application."""
    chat = ConsoleChat()
    chat.run()


if __name__ == "__main__":
    main()
