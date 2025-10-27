"""Console chat interface with persistent dialog storage."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.live import Live
from rich.table import Table
from rich.panel import Panel

from core.conversation import ConversationHistory
from core.gemini_client import GeminiApiClient, GeminiModel
from core.text_manager import TextManager
from core.storage import SQLiteStorage
from pipeline.pipeline_executor import IndexingPipeline


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

        # Document indexing pipeline
        self.indexing_pipeline = None  # Will be initialized on first use
        self.last_search_results = None

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
        self.console.print("\n" + "=" * 60, style="bright_cyan")
        self.console.print("     DOCUMENT INDEXING CHAT - AI Assistant", style="bold bright_cyan")
        self.console.print("=" * 60, style="bright_cyan")
        self.console.print("Document Indexing Commands:", style="yellow")
        self.console.print("  /index <path> [--collection <name>] - Index documents", style="bright_green")
        self.console.print("  /search <query> [--collection <name>] - Search index", style="bright_green")
        self.console.print("  /list-collections - Show all collections", style="green")
        self.console.print("  /delete-collection <name> - Delete collection", style="green")
        self.console.print("  /clear-index - Clear all indexed data", style="green")
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
            instruction_preview = self.system_instruction[:50] + "..." if len(self.system_instruction) > 50 else self.system_instruction
            self.console.print(f"System instruction: {instruction_preview}", style="dim")
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

                self.console.print(f"\n✓ Loaded dialog #{selected_dialog['id']}: {selected_dialog['title']}", style="green")
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

    def _init_indexing_pipeline(self):
        """Initialize indexing pipeline lazily"""
        if self.indexing_pipeline is None:
            self.indexing_pipeline = IndexingPipeline(
                api_key=self.api_key,
                persist_directory="data/chroma_db"
            )

    def index_documents(self, command_args: str):
        """Index documents from path"""
        # Parse arguments
        parts = command_args.split()
        if not parts:
            self.console.print("✗ Usage: /index <path> [--collection <name>]", style="red")
            return

        path = parts[0]
        collection_name = None

        # Look for --collection flag
        if "--collection" in parts:
            try:
                coll_idx = parts.index("--collection")
                if coll_idx + 1 < len(parts):
                    collection_name = parts[coll_idx + 1]
            except (ValueError, IndexError):
                pass

        # Default collection name from path
        if not collection_name:
            path_obj = Path(path)
            collection_name = path_obj.stem if path_obj.is_file() else path_obj.name
            # Sanitize collection name
            collection_name = collection_name.replace(" ", "_").replace("-", "_").lower()

        # Validate path
        path_obj = Path(path)
        if not path_obj.exists():
            self.console.print(f"✗ Path not found: {path}", style="red")
            return

        # Initialize pipeline
        self._init_indexing_pipeline()

        # Run indexing
        self.console.print(f"\n📚 Indexing: {path}", style="bright_cyan bold")
        self.console.print(f"Collection: {collection_name}", style="cyan")
        self.console.print("=" * 70, style="bright_cyan")

        try:
            result = self.indexing_pipeline.index_path(
                path=path,
                collection_name=collection_name,
                show_progress=True
            )

            if result.success:
                self.console.print("\n" + "=" * 70, style="bright_cyan")
                self.console.print("✓ Indexing complete!", style="green bold")
                self.console.print(f"  Documents loaded: {result.documents_loaded}", style="dim")
                self.console.print(f"  Chunks created: {result.chunks_created}", style="dim")
                self.console.print(f"  Embeddings generated: {result.embeddings_generated}", style="dim")
                self.console.print(f"  Documents indexed: {result.documents_indexed}", style="dim")
                self.console.print(f"\n💡 Try: /search \"your query\" --collection {collection_name}", style="bright_yellow")
            else:
                self.console.print(f"\n✗ Indexing failed: {result.error_message}", style="red")

        except Exception as e:
            self.console.print(f"\n✗ Indexing error: {str(e)}", style="red")

    def search_index(self, command_args: str):
        """Search in indexed documents"""
        # Parse arguments
        parts = command_args.split("--collection")

        if not parts or not parts[0].strip():
            self.console.print("✗ Usage: /search <query> [--collection <name>]", style="red")
            return

        query = parts[0].strip().strip('"').strip("'")
        collection_name = None

        if len(parts) > 1:
            collection_name = parts[1].strip()

        # Initialize pipeline
        self._init_indexing_pipeline()

        # Search
        self.console.print(f"\n🔍 Searching for: \"{query}\"", style="bright_cyan bold")
        if collection_name:
            self.console.print(f"Collection: {collection_name}", style="cyan")
        else:
            self.console.print("Collection: All collections", style="cyan")
        self.console.print("=" * 70, style="bright_cyan")

        try:
            spinner = Spinner("dots", text="Searching...", style="yellow")
            with Live(spinner, console=self.console, transient=True):
                results = self.indexing_pipeline.search(
                    query=query,
                    collection_name=collection_name,
                    top_k=5
                )

            if not results:
                self.console.print("\n✗ No results found", style="yellow")
                return

            # Store results
            self.last_search_results = results

            # Display results
            self.console.print(f"\n📋 Found {len(results)} results:\n", style="green bold")

            for idx, result in enumerate(results, 1):
                # Create result panel
                source_name = Path(result.source).name
                panel_content = f"[dim]{result.text[:300]}{'...' if len(result.text) > 300 else ''}[/dim]\n\n"
                panel_content += f"[cyan]Source:[/cyan] {source_name}\n"
                panel_content += f"[cyan]Chunk:[/cyan] {result.chunk_index} | [cyan]Distance:[/cyan] {result.distance:.4f}"

                panel = Panel(
                    panel_content,
                    title=f"Result {idx}",
                    border_style="bright_green" if idx == 1 else "green"
                )
                self.console.print(panel)

            self.console.print("\n💡 You can now ask AI questions about these results!", style="bright_yellow")

        except Exception as e:
            self.console.print(f"\n✗ Search error: {str(e)}", style="red")

    def list_collections(self):
        """List all collections"""
        self._init_indexing_pipeline()

        try:
            collections = self.indexing_pipeline.list_collections()

            if not collections:
                self.console.print("\n📚 No collections found", style="yellow")
                self.console.print("💡 Use /index <path> to create a collection", style="dim")
                return

            # Create table
            table = Table(title="📚 Collections", show_header=True, header_style="bold magenta")
            table.add_column("Name", style="cyan", width=30)
            table.add_column("Documents", justify="right", style="white", width=12)
            table.add_column("Metadata", style="dim", width=30)

            total_docs = 0
            for col in collections:
                total_docs += col.count
                metadata_str = ", ".join(f"{k}: {v}" for k, v in col.metadata.items() if k != "hnsw:space")
                table.add_row(col.name, str(col.count), metadata_str[:30])

            self.console.print("\n")
            self.console.print(table)
            self.console.print(f"\nTotal: {len(collections)} collections, {total_docs} documents", style="dim")

        except Exception as e:
            self.console.print(f"\n✗ Error listing collections: {str(e)}", style="red")

    def delete_collection(self, collection_name: str):
        """Delete a specific collection"""
        if not collection_name.strip():
            self.console.print("✗ Usage: /delete-collection <name>", style="red")
            return

        self._init_indexing_pipeline()

        try:
            success = self.indexing_pipeline.delete_collection(collection_name.strip())
            if success:
                self.console.print(f"✓ Collection '{collection_name}' deleted", style="green")
            else:
                self.console.print(f"✗ Failed to delete collection '{collection_name}'", style="red")
        except Exception as e:
            self.console.print(f"✗ Error: {str(e)}", style="red")

    def clear_all_index(self):
        """Clear all indexed data"""
        self._init_indexing_pipeline()

        # Confirm
        self.console.print("\n⚠️  Warning: This will delete ALL collections and indexed data!", style="yellow bold")
        confirm = input("Type 'yes' to confirm: ").strip().lower()

        if confirm != "yes":
            self.console.print("Cancelled", style="dim")
            return

        try:
            success = self.indexing_pipeline.clear_all()
            if success:
                self.console.print("✓ All indexed data cleared", style="green")
            else:
                self.console.print("✗ Failed to clear index", style="red")
        except Exception as e:
            self.console.print(f"✗ Error: {str(e)}", style="red")

    def handle_command(self, command: str) -> bool:
        """Handle special commands."""
        original_command = command.strip()
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
        elif command_lower == "/help":
            self.display_welcome()
        elif command_lower.startswith("/index "):
            # Extract arguments (preserve original case)
            args = original_command[7:].strip()
            if args:
                self.index_documents(args)
            else:
                self.console.print("✗ Usage: /index <path> [--collection <name>]", style="red")
        elif command_lower.startswith("/search "):
            # Extract arguments (preserve original case)
            args = original_command[8:].strip()
            if args:
                self.search_index(args)
            else:
                self.console.print("✗ Usage: /search <query> [--collection <name>]", style="red")
        elif command_lower == "/list-collections":
            self.list_collections()
        elif command_lower.startswith("/delete-collection "):
            collection_name = original_command[19:].strip()
            if collection_name:
                self.delete_collection(collection_name)
            else:
                self.console.print("✗ Usage: /delete-collection <name>", style="red")
        elif command_lower == "/clear-index":
            self.clear_all_index()
        else:
            self.console.print(f"Unknown command: {command_lower}", style="red")
            self.console.print("Type /help for available commands", style="dim")

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
                    self.console.print(f"\n[yellow]⚠️  Input too long ({input_tokens:,} tokens)! Compressing...[/yellow]")
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
                        self.console.print(f"[green]✓ Compressed: {input_tokens:,} → {summary_result['summary_tokens']:,} tokens[/green]")
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
