"""Console chat interface with persistent dialog storage."""

import os
import sys
from pathlib import Path

from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live

from core.gemini_client import GeminiApiClient, GeminiModel
from core.storage import SQLiteStorage
from managers.index_manager import IndexManager
from managers.rag_manager import RagManager
from managers.dialog_manager import DialogManager
from managers.settings_manager import SettingsManager
from managers.ui_manager import UIManager


class ConsoleChat:
    """Console-based chat interface with SQLite persistence."""

    MODELS = {
        "1": (GeminiModel.GEMINI_2_5_FLASH, "Gemini 2.5 Flash (Fast & Balanced)"),
        "2": (GeminiModel.GEMINI_2_5_FLASH_LITE, "Gemini 2.5 Flash Lite (Ultra Fast)"),
        "3": (GeminiModel.GEMINI_2_5_PRO, "Gemini 2.5 Pro (Most Advanced)")
    }

    def __init__(self):
        """Initialize chat interface with managers."""
        self.api_key = self._get_api_key()
        self.gemini_client = GeminiApiClient(self.api_key)
        self.storage = SQLiteStorage("data/conversations.db")
        self.current_model = GeminiModel.GEMINI_2_5_FLASH
        self.console = Console()

        # Initialize managers
        self.index_manager = IndexManager(
            console=self.console,
            api_key=self.api_key
        )

        self.settings_manager = SettingsManager(console=self.console)

        self.ui_manager = UIManager(
            console=self.console,
            storage=self.storage
        )

        self.dialog_manager = DialogManager(
            console=self.console,
            storage=self.storage,
            gemini_client=self.gemini_client
        )

        # RAG manager will be initialized after index manager
        self.rag_manager = None

        # Clean up empty dialogs from previous sessions
        self.storage.delete_empty_dialogs()

        # Create new dialog on start (always, silently)
        self.dialog_manager.create_new_dialog(self.current_model, silent=True)

    def _init_rag_manager(self):
        """Initialize RAG manager lazily."""
        if self.rag_manager is None:
            # Ensure indexing pipeline is initialized
            self.index_manager._init_pipeline()
            self.rag_manager = RagManager(
                console=self.console,
                gemini_client=self.gemini_client,
                indexing_pipeline=self.index_manager.indexing_pipeline
            )

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

    def handle_command(self, command: str) -> bool:
        """Handle special commands.

        Args:
            command: Command string

        Returns:
            True if should quit, False otherwise
        """
        original_command = command.strip()
        command_lower = command.lower().strip()

        if command_lower == "/quit":
            self.console.print("\nGoodbye!", style="bold bright_cyan")
            return True

        elif command_lower == "/help":
            self.ui_manager.display_welcome(
                current_model=self.current_model,
                dialog_id=self.dialog_manager.conversation.dialog_id,
                temperature=self.settings_manager.temperature,
                top_k=self.settings_manager.top_k,
                top_p=self.settings_manager.top_p,
                max_output_tokens=self.settings_manager.max_output_tokens,
                system_instruction=self.settings_manager.system_instruction
            )

        elif command_lower == "/model":
            self.current_model = self.ui_manager.select_model(self.current_model)

        elif command_lower == "/resume":
            self.dialog_manager.resume_dialog()

        elif command_lower == "/clear":
            self.dialog_manager.clear_dialog(self.current_model)
            self.console.print("✓ Dialog cleared, new conversation started", style="green")

        elif command_lower == "/system":
            self.settings_manager.manage_system_instruction()

        elif command_lower == "/settings":
            self.settings_manager.manage_generation_settings()

        elif command_lower == "/compress":
            self.dialog_manager.compress_conversation()

        elif command_lower == "/tokens":
            self.dialog_manager.show_token_stats()

        # Document indexing commands
        elif command_lower.startswith("/index "):
            args = original_command[7:]  # Remove "/index "
            self.index_manager.index_documents(args)

        elif command_lower.startswith("/search "):
            args = original_command[8:]  # Remove "/search "
            self.index_manager.search_index(args)

        elif command_lower == "/list-collections":
            self.index_manager.list_collections()

        elif command_lower.startswith("/delete-collection "):
            collection_name = original_command[19:]  # Remove "/delete-collection "
            self.index_manager.delete_collection(collection_name)

        elif command_lower == "/clear-index":
            self.index_manager.clear_all()

        # RAG commands
        elif command_lower.startswith("/load-koog"):
            self._init_rag_manager()
            force = "--force" in command_lower
            self.rag_manager.load_koog(force=force)

        elif command_lower == "/koog-info":
            self._init_rag_manager()
            self.rag_manager.show_koog_info()

        else:
            self.console.print(f"Unknown command: {command}", style="red")
            self.console.print("Type /help to see available commands", style="dim")

        return False

    def chat_loop(self):
        """Main chat loop with automatic RAG integration."""
        while True:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()

                if not user_input:
                    continue

                # Check for commands
                if user_input.startswith("/"):
                    should_quit = self.handle_command(user_input)
                    if should_quit:
                        break
                    continue

                # Add user message to history
                self.dialog_manager.conversation.add_message("user", user_input)

                # Store original prompt for response
                prompt_to_send = user_input

                # Search RAG for relevant context (only if available)
                rag_chunks = []
                self._init_rag_manager()
                if self.rag_manager.is_rag_available():
                    spinner = Spinner("dots", text="Searching knowledge base...", style="yellow")
                    with Live(spinner, console=self.console, transient=True):
                        rag_chunks = self.rag_manager.search_context(prompt_to_send)

                # Format context and add to prompt
                if rag_chunks:
                    rag_context = self.rag_manager.format_context_for_prompt(rag_chunks)
                    final_prompt = rag_context + prompt_to_send + "\n\nAnswer:"
                else:
                    final_prompt = prompt_to_send

                # Generate response
                spinner = Spinner("dots", text="Thinking...", style="yellow")
                with Live(spinner, console=self.console, transient=True):
                    # Get conversation history (excludes last message)
                    history = self.dialog_manager.conversation.get_history()

                    # Generate response
                    response = self.gemini_client.generate_content(
                        prompt=final_prompt,
                        model=self.current_model,
                        conversation_history=history if history else None,
                        system_instruction=self.settings_manager.system_instruction,
                        temperature=self.settings_manager.temperature,
                        top_k=self.settings_manager.top_k,
                        top_p=self.settings_manager.top_p,
                        max_output_tokens=self.settings_manager.max_output_tokens
                    )

                # Extract text
                response_text = self.gemini_client.extract_text(response)

                # Print response
                self.console.print("\n", end="")
                self.console.print("AI:", style="bold green", end=" ")
                self.ui_manager.print_response(response_text)

                # Display sources if RAG was used, or indicate general knowledge
                if rag_chunks:
                    self.console.print(f"\n\n📚 Sources ({len(rag_chunks)} documents):", style="yellow bold")
                    for idx, chunk in enumerate(rag_chunks, 1):
                        source_name = Path(chunk.source).name
                        relevance = 1 - chunk.distance if hasattr(chunk, 'distance') else 0
                        rerank_score = chunk.rerank_score if hasattr(chunk, 'rerank_score') else None
                        if rerank_score is not None:
                            self.console.print(
                                f"  {idx}. {source_name} (Chunk {chunk.chunk_index}, "
                                f"relevance: {relevance:.2f}, rerank: {rerank_score:.1f}/10)",
                                style="dim"
                            )
                        else:
                            self.console.print(
                                f"  {idx}. {source_name} (Chunk {chunk.chunk_index}, relevance: {relevance:.2f})",
                                style="dim"
                            )
                else:
                    if self.rag_manager and self.rag_manager.is_rag_available():
                        self.console.print("\nℹ️  No relevant documents found. Answer based on general knowledge.", style="yellow dim")
                    else:
                        self.console.print("\nℹ️  RAG not loaded. Answer based on general knowledge.", style="yellow dim")
                        self.console.print("💡 Use /load-koog to enable document search", style="dim")

                # Add assistant response to history
                self.dialog_manager.conversation.add_message("model", response_text)

            except KeyboardInterrupt:
                self.console.print("\n\nInterrupted. Type /quit to exit.", style="yellow")
                continue
            except Exception as e:
                self.console.print(f"\nError: {str(e)}", style="red")
                import traceback
                traceback.print_exc()

    def run(self):
        """Run the chat interface."""
        self.ui_manager.display_welcome(
            current_model=self.current_model,
            dialog_id=self.dialog_manager.conversation.dialog_id,
            temperature=self.settings_manager.temperature,
            top_k=self.settings_manager.top_k,
            top_p=self.settings_manager.top_p,
            max_output_tokens=self.settings_manager.max_output_tokens,
            system_instruction=self.settings_manager.system_instruction
        )
        self.chat_loop()


def main():
    """Main entry point."""
    chat = ConsoleChat()
    chat.run()


if __name__ == "__main__":
    main()
