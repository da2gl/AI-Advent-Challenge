"""Console chat interface with persistent dialog storage."""

import json
import os
import sys
from datetime import datetime

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.table import Table

from core.conversation import ConversationHistory
from core.gemini_client import GeminiApiClient, GeminiModel
from core.storage import SQLiteStorage
from core.text_manager import TextManager
from pipeline.deploy_pipeline import DeploymentPipeline


class ConsoleChat:
    """Console-based chat interface with SQLite persistence."""

    MODELS = {
        "1": (GeminiModel.GEMINI_2_5_FLASH, "Gemini 2.5 Flash (Fast & Balanced)"),
        "2": (GeminiModel.GEMINI_2_5_FLASH_LITE, "Gemini 2.5 Flash Lite (Ultra Fast)"),
        "3": (GeminiModel.GEMINI_2_5_PRO, "Gemini 2.5 Pro (Most Advanced)")
    }

    DEFAULT_SYSTEM_INSTRUCTION = None

    def __init__(self):
        """Initialize chat interface with storage."""
        self.api_key = self._get_api_key()
        self.client = GeminiApiClient(self.api_key)
        self.storage = SQLiteStorage("data/conversations.db")
        self.current_model = GeminiModel.GEMINI_2_5_FLASH
        self.system_instruction = self.DEFAULT_SYSTEM_INSTRUCTION
        self.console = Console()

        # Generation settings
        self.temperature = 0.7
        self.top_k = 40
        self.top_p = 0.95
        self.max_output_tokens = 2048

        self.pipeline = None  # Will be initialized on first use

        # Clean up empty dialogs from previous sessions
        self.storage.delete_empty_dialogs()

        # Create new dialog on start (always, silently)
        self.create_new_dialog(silent=True)

    def create_new_dialog(self, silent=False):
        """Create a new dialog and initialize conversation.

        Args:
            silent: If True, don't print creation message
        """
        dialog_id = self.storage.create_dialog(self.current_model)
        self.conversation = ConversationHistory(self.storage, dialog_id)
        if not silent:
            self.console.print(f"✓ Created new dialog #{dialog_id}", style="green")

    @staticmethod
    def _get_api_key() -> str:
        """Get API key from environment or user input."""
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

    def display_welcome(self):
        """Display welcome message."""
        self.console.print("\n" + "=" * 50, style="bright_cyan")
        self.console.print("     GEMINI CHAT - AI Assistant", style="bold bright_cyan")
        self.console.print("=" * 50, style="bright_cyan")
        self.console.print("Commands:", style="yellow")
        self.console.print("  /resume      - Load previous dialog", style="dim")
        self.console.print("  /clear       - Delete current dialog & create new", style="dim")
        self.console.print("  /model       - Change model", style="dim")
        self.console.print("  /system      - View/change system instruction", style="dim")
        self.console.print("  /settings    - View/change generation settings", style="dim")
        self.console.print("  /compress    - Compress conversation history", style="dim")
        self.console.print("  /tokens      - Show token statistics", style="dim")
        self.console.print("  /deploy      - Deploy (railway/docker)", style="dim")
        self.console.print("  /quit        - Exit chat", style="dim")
        self.console.print("=" * 50, style="bright_cyan")

        # Show current dialog info
        if self.conversation.dialog_id:
            dialog_info = self.storage.get_dialog_info(self.conversation.dialog_id)
            if dialog_info:
                self.console.print(f"Dialog #{dialog_info['id']}: {dialog_info['title']}", style="green")
                self.console.print(f"Messages: {dialog_info['message_count']}", style="dim")

        self.console.print(f"Model: {self._get_model_name()}", style="dim")
        self.console.print(
            f"Temperature: {self.temperature} | TopK: {self.top_k} | "
            f"TopP: {self.top_p} | MaxTokens: {self.max_output_tokens}",
            style="dim"
        )
        if self.system_instruction:
            preview = (self.system_instruction[:50] + "..."
                       if len(self.system_instruction) > 50
                       else self.system_instruction)
            self.console.print(f"System instruction: {preview}", style="dim")
        self.console.print("=" * 50 + "\n", style="bright_cyan")

    def _get_model_name(self) -> str:
        """Get human-readable name of current model."""
        for _, (model, name) in self.MODELS.items():
            if model == self.current_model:
                return name
        return self.current_model

    def _print_response(self, text: str):
        """Print response with formatting."""
        try:
            json.loads(text.strip())
            self.console.print()
            self.console.print_json(text.strip())
        except (json.JSONDecodeError, TypeError):
            self.console.print()
            self.console.print(Markdown(text))

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

                self.console.print(
                    f"\n✓ Loaded dialog #{selected_dialog['id']}: {selected_dialog['title']}",
                    style="green"
                )
                self.console.print(f"📝 History restored: {selected_dialog['message_count']} messages", style="dim")
            else:
                self.console.print("Invalid dialog number", style="red")
        except ValueError:
            self.console.print("Invalid input", style="red")

    def clear_dialog(self):
        """Delete current dialog and create new one."""
        if not self.conversation.dialog_id:
            self.console.print("No active dialog to clear", style="yellow")
            return

        # Delete dialog without confirmation
        self.storage.delete_dialog(self.conversation.dialog_id)

        # Create new dialog silently
        self.create_new_dialog(silent=True)

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

    def manage_generation_settings(self):
        """Display and optionally change generation settings."""
        self.console.print("\n" + "=" * 50, style="bright_cyan")
        self.console.print("Generation Settings", style="yellow")
        self.console.print("=" * 50, style="bright_cyan")
        self.console.print(f"1. Temperature:       {self.temperature} (0.0-2.0)", style="dim")
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
        """Display token statistics."""
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

    def compress_conversation(self):
        """Compress conversation history."""
        self.console.print("\n🔄 Compressing conversation history...", style="yellow")

        try:
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
                self.console.print("=" * 60, style="bright_cyan")
                self.console.print("\n✓ Conversation compressed successfully!", style="green")

        except Exception as e:
            self.console.print(f"\n✗ Compression failed: {str(e)}", style="red")

    def trigger_deployment(self, command: str):
        """Trigger deployment pipeline."""
        parts = command.split()
        platform = parts[1] if len(parts) > 1 else "railway"

        if platform not in ["railway", "docker"]:
            self.console.print(
                f"✗ Unknown platform: {platform}. Use: railway or docker",
                style="red"
            )
            return

        self.console.print("\n" + "=" * 60, style="bright_cyan")
        self.console.print("🚀 Deployment Pipeline", style="bold bright_cyan")
        self.console.print("=" * 60, style="bright_cyan")
        self.console.print(f"Platform: {platform}", style="dim")
        self.console.print("=" * 60 + "\n", style="bright_cyan")

        try:
            self._init_pipeline()

            # Run pipeline stages with progress updates
            self.console.print("📊 Running Pipeline Stages\n", style="bold bright_cyan")

            # Stage 1: Validation
            self.console.print("▶ Stage 1: Validation", style="yellow")
            spinner = Spinner("dots", text="Validating project...", style="yellow")
            with Live(spinner, console=self.console, transient=True):
                validation_result = self.pipeline.validator.validate()

            if validation_result.valid:
                self.console.print("✓ Stage 1: Validation - Project validated successfully", style="green")
                files_info = validation_result.project_info.get('files', {})
                self.console.print(f"  Python files: {files_info.get('python', 0)}", style="dim")
                self.console.print(f"  Total lines: {files_info.get('total_lines', 0)}", style="dim")
                if validation_result.warnings:
                    self.console.print(f"  Warnings: {len(validation_result.warnings)}", style="yellow")
                self.console.print()
            else:
                self.console.print(f"✗ Stage 1: Validation - Failed", style="red")
                for issue in validation_result.issues[:3]:
                    self.console.print(f"  • {issue}", style="red")
                self.console.print()
                return

            # Stage 2: Build Preparation
            self.console.print("▶ Stage 2: Build Preparation", style="yellow")
            spinner = Spinner("dots", text="Preparing build artifacts...", style="yellow")
            with Live(spinner, console=self.console, transient=True):
                build_result = self.pipeline.build_preparer.prepare(platform=platform)

            self.console.print(
                f"✓ Stage 2: Build Preparation - Generated {len(build_result.artifacts)} artifacts",
                style="green"
            )
            for artifact in build_result.artifacts[:5]:
                self.console.print(f"  • {artifact}", style="dim")
            if len(build_result.artifacts) > 5:
                self.console.print(f"  ... and {len(build_result.artifacts) - 5} more", style="dim")
            self.console.print()

            # Stage 3: AI Analysis
            self.console.print("▶ Stage 3: AI Analysis", style="yellow")
            spinner = Spinner("dots", text="Running AI analysis...", style="yellow")
            with Live(spinner, console=self.console, transient=True):
                ai_recommendations = self.pipeline._get_ai_recommendations(
                    validation_result, build_result, platform
                )
            self.console.print("✓ Stage 3: AI Analysis - Analysis complete\n", style="green")

            # Stage 4: Deployment
            self.console.print("▶ Stage 4: Deployment", style="yellow")
            spinner = Spinner("dots", text=f"Deploying to {platform}...", style="yellow")
            with Live(spinner, console=self.console, transient=True):
                deployment_result = self.pipeline.deployment_engine.deploy(
                    platform=platform
                )

            if deployment_result.success:
                deploy_msg = f"Deployed to {deployment_result.url or platform}"
                self.console.print(f"✓ Stage 4: Deployment - {deploy_msg}", style="green")
                self.console.print(f"  Platform: {platform}", style="dim")
                if deployment_result.logs:
                    self.console.print(f"  Logs: {len(deployment_result.logs)} entries", style="dim")
                self.console.print()
            else:
                self.console.print(f"✗ Stage 4: Deployment - Failed", style="red")
                if deployment_result.errors:
                    for error in deployment_result.errors[:3]:
                        self.console.print(f"  • {error}", style="red")
                self.console.print()

            # Show AI recommendations if available
            if ai_recommendations and not ai_recommendations.startswith('AI'):
                self.console.print("=" * 60, style="bright_cyan")
                self.console.print("🤖 AI Recommendations", style="bold bright_green")
                self.console.print("=" * 60, style="bright_cyan")
                md = Markdown(ai_recommendations)
                self.console.print(md)
                self.console.print("=" * 60 + "\n", style="bright_cyan")

            if deployment_result.success:
                self.console.print("✓ Deployment completed successfully!", style="bold green")
            else:
                self.console.print("✗ Deployment failed!", style="bold red")

            self.console.print("=" * 60, style="bright_cyan")

        except Exception as e:
            self.console.print(f"\n✗ Deployment error: {str(e)}", style="red")

    def _init_pipeline(self):
        """Initialize deployment pipeline lazily"""
        if self.pipeline is None:
            # Create wrapper for Gemini client
            class GeminiWrapper:
                def __init__(self, client):
                    self.client = client

                def generate_content(self, prompt: str) -> str:
                    response = self.client.generate_content(prompt)
                    return self.client.extract_text(response)

            self.pipeline = DeploymentPipeline(gemini_client=GeminiWrapper(self.client))

    def handle_command(self, command: str) -> bool:
        """Handle special commands."""
        command_lower = command.lower().strip()

        if command_lower == "/quit":
            self.console.print("\nGoodbye!", style="bold bright_cyan")
            return False
        elif command_lower == "/clear":
            self.clear_dialog()
        elif command_lower == "/resume":
            self.resume_dialog()
        elif command_lower == "/model":
            self.select_model()
        elif command_lower == "/system":
            self.manage_system_instruction()
        elif command_lower == "/settings":
            self.manage_generation_settings()
        elif command_lower == "/tokens":
            self.show_token_stats()
        elif command_lower == "/compress":
            self.compress_conversation()
        elif command_lower.startswith("/deploy"):
            self.trigger_deployment(command_lower)
        else:
            self.console.print(f"Unknown command: {command_lower}", style="red")

        return True

    def chat_loop(self):
        """Main chat loop."""
        self.display_welcome()

        while True:
            try:
                self.console.print("\n", end="")
                self.console.print("You: ", style="bold bright_blue", end="")
                user_input = input().strip()

                if not user_input:
                    continue

                if user_input.startswith("/"):
                    if not self.handle_command(user_input):
                        break
                    continue

                # Check if input needs compression
                prompt_to_send = user_input
                if ConversationHistory.should_compress_input(user_input):
                    input_tokens = TextManager.estimate_tokens(user_input)
                    self.console.print(
                        f"\n[yellow]⚠️  Input too long ({input_tokens:,} tokens)! "
                        f"Compressing...[/yellow]"
                    )
                    try:
                        spinner = Spinner("dots", text="Compressing input...", style="yellow")
                        with Live(spinner, console=self.console, transient=True):
                            summary_result = TextManager.summarize_text(
                                text=user_input,
                                client=self.client,
                                max_tokens=2000,
                                language="mixed",
                                timeout=15
                            )
                        prompt_to_send = summary_result['summary']
                        self.console.print(
                            f"[green]✓ Compressed: {input_tokens:,} → "
                            f"{summary_result['summary_tokens']:,} tokens[/green]"
                        )
                    except Exception as e:
                        self.console.print(f"[red]✗ Compression failed: {str(e)}[/red]")

                # Add user message to history (auto-saves to SQLite)
                self.conversation.add_user_message(prompt_to_send)

                # Generate response
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

                self.console.print("Assistant: ", style="bold bright_magenta", end="")

                assistant_text = self.client.extract_text(response)
                self._print_response(assistant_text)

                # Handle token usage
                usage = self.client.extract_usage_metadata(response)
                if usage:
                    self.conversation.add_tokens(usage['total_tokens'])

                    self.console.print(
                        f"\n[dim]Tokens: {usage['prompt_tokens']} prompt + "
                        f"{usage['response_tokens']} response = "
                        f"{usage['total_tokens']} total[/dim]"
                    )

                    progress = TextManager.format_token_usage(
                        self.conversation.total_tokens,
                        ConversationHistory.MAX_CONTEXT_TOKENS
                    )
                    self.console.print(f"[dim]Context: {progress}[/dim]")

                    # Auto-compress if needed
                    if self.conversation.should_compress():
                        self.console.print("\n[yellow]⚠️  Context limit reached! Auto-compressing...[/yellow]")
                        try:
                            spinner = Spinner("dots", text="Compressing...", style="yellow")
                            with Live(spinner, console=self.console, transient=True):
                                result = self.conversation.compress_history(self.client)
                            if result['messages_compressed'] > 0:
                                self.console.print(
                                    f"[green]✓ Compressed {result['messages_compressed']} messages, "
                                    f"saved {result['tokens_saved']:,} tokens[/green]"
                                )
                        except Exception as e:
                            self.console.print(f"[red]✗ Auto-compression failed: {str(e)}[/red]")

                # Add assistant message (auto-saves to SQLite)
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
        self.storage.close()

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
