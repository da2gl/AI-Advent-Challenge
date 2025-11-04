"""Console chat interface with persistent dialog storage."""

import os
import sys
import io
from pathlib import Path

from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live

# Fix encoding for stdin to handle non-ASCII characters (e.g., Russian, Chinese, etc.)
if sys.stdin.encoding != 'utf-8':
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

from core.gemini_client import GeminiApiClient, GeminiModel
from core.storage import SQLiteStorage
from core.user_profile import UserProfile
from managers.index_manager import IndexManager
from managers.rag_manager import RagManager
from managers.dialog_manager import DialogManager
from managers.settings_manager import SettingsManager
from managers.ui_manager import UIManager
from managers.speech_manager import SpeechManager


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

        # Initialize user profile for personalization
        self.user_profile = UserProfile()

        # Initialize managers
        self.index_manager = IndexManager(
            console=self.console,
            api_key=self.api_key
        )

        self.settings_manager = SettingsManager(
            console=self.console,
            user_profile=self.user_profile
        )

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

        # Speech manager will be initialized when /voice command is used
        self.speech_manager = None

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

    def _init_speech_manager(self):
        """Initialize Speech manager lazily (only when /voice is used)."""
        if self.speech_manager is None:
            groq_api_key = self._get_groq_api_key()
            self.speech_manager = SpeechManager(
                api_key=groq_api_key,
                console=self.console
            )

    def _handle_voice_input(self):
        """Handle voice input: record audio, transcribe, and process as text."""
        try:
            # Initialize speech manager if needed
            self._init_speech_manager()

            # Record and transcribe
            transcribed_text = self.speech_manager.record_and_transcribe()

            if not transcribed_text:
                self.console.print("[yellow]No text transcribed. Try again.[/yellow]")
                return

            # Process transcribed text as regular user input
            self.console.print()  # Add newline for better formatting

            # Add user message to history
            self.dialog_manager.conversation.add_message("user", transcribed_text)

            # Store original prompt for response
            prompt_to_send = transcribed_text

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

            # Display sources if RAG was used
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

            # Add assistant response to history
            self.dialog_manager.conversation.add_message("model", response_text)

        except Exception as e:
            self.console.print(f"\n[red]Voice input error: {str(e)}[/red]")
            import traceback
            traceback.print_exc()

    def _manage_profile(self):
        """Interactive user profile management - personal data only (not system instruction or generation settings)."""
        while True:
            self.console.print("\n" + "=" * 60, style="bright_cyan")
            self.console.print("User Profile Management", style="yellow bold")
            self.console.print("=" * 60, style="bright_cyan")

            # Display current profile
            profile = self.user_profile.get_user_profile()
            prefs = profile.get("preferences", {})

            self.console.print("\nCurrent Profile:", style="yellow")
            self.console.print(f"  Name:                 {profile.get('name', 'N/A')}", style="dim")
            self.console.print(f"  Role:                 {profile.get('role', 'N/A')}", style="dim")
            self.console.print(f"  Communication Style:  {profile.get('communication_style', 'N/A')}", style="dim")
            self.console.print(f"  Response Length:      {prefs.get('response_length', 'N/A')}", style="dim")
            self.console.print(f"  Code Style:           {prefs.get('code_style', 'N/A')}", style="dim")
            self.console.print(f"  Explanation Level:    {prefs.get('explanation_level', 'N/A')}", style="dim")

            interests = profile.get('interests', [])
            habits = profile.get('habits', [])
            if interests:
                self.console.print(f"  Interests:            {', '.join(interests)}", style="dim")
            if habits:
                self.console.print(f"  Habits:               {', '.join(habits)}", style="dim")

            self.console.print("\nActions:", style="yellow")
            self.console.print("  1. Edit name", style="dim")
            self.console.print("  2. Edit role", style="dim")
            self.console.print("  3. Edit communication style", style="dim")
            self.console.print("  4. Edit preferences", style="dim")
            self.console.print("  5. Manage interests", style="dim")
            self.console.print("  6. Manage habits", style="dim")
            self.console.print("  7. Reset to defaults", style="dim")
            self.console.print("  0. Back to chat", style="dim")
            self.console.print("=" * 60, style="bright_cyan")

            choice = input("\nSelect action (0-7): ").strip()

            if choice == "0":
                break
            elif choice == "1":
                new_name = input("Enter your name: ").strip()
                if new_name:
                    self.user_profile.update_profile_field("name", new_name)
                    self.settings_manager.system_instruction = self.user_profile.get_system_instruction()
                    self.console.print("✓ Name updated and saved", style="green")
            elif choice == "2":
                new_role = input("Enter your role (e.g., Developer, Student, etc.): ").strip()
                if new_role:
                    self.user_profile.update_profile_field("role", new_role)
                    self.settings_manager.system_instruction = self.user_profile.get_system_instruction()
                    self.console.print("✓ Role updated and saved", style="green")
            elif choice == "3":
                self.console.print("\nCommunication styles: casual, formal, friendly, professional")
                new_style = input("Enter communication style: ").strip()
                if new_style:
                    self.user_profile.update_profile_field("communication_style", new_style)
                    self.settings_manager.system_instruction = self.user_profile.get_system_instruction()
                    self.console.print("✓ Communication style updated and saved", style="green")
            elif choice == "4":
                self._edit_preferences()
            elif choice == "5":
                self._manage_interests()
            elif choice == "6":
                self._manage_habits()
            elif choice == "7":
                confirm = input("Are you sure you want to reset to defaults? (yes/no): ").strip().lower()
                if confirm == "yes":
                    self.user_profile.reset_to_defaults()
                    self.settings_manager.system_instruction = self.user_profile.get_system_instruction()
                    self.console.print("✓ Profile reset to defaults", style="green")
            else:
                self.console.print("Invalid choice", style="red")

    def _edit_preferences(self):
        """Edit user preferences submenu."""
        self.console.print("\nEdit Preferences:", style="yellow")
        self.console.print("  1. Response length (concise/detailed/balanced)")
        self.console.print("  2. Code style (clean/verbose/minimal)")
        self.console.print("  3. Explanation level (beginner/intermediate/advanced)")

        choice = input("\nSelect preference to edit (1-3): ").strip()

        if choice == "1":
            new_val = input("Response length (concise/detailed/balanced): ").strip()
            if new_val:
                self.user_profile.update_preference("response_length", new_val)
                self.settings_manager.system_instruction = self.user_profile.get_system_instruction()
                self.console.print("✓ Response length updated and saved", style="green")
        elif choice == "2":
            new_val = input("Code style (clean/verbose/minimal): ").strip()
            if new_val:
                self.user_profile.update_preference("code_style", new_val)
                self.settings_manager.system_instruction = self.user_profile.get_system_instruction()
                self.console.print("✓ Code style updated and saved", style="green")
        elif choice == "3":
            new_val = input("Explanation level (beginner/intermediate/advanced): ").strip()
            if new_val:
                self.user_profile.update_preference("explanation_level", new_val)
                self.settings_manager.system_instruction = self.user_profile.get_system_instruction()
                self.console.print("✓ Explanation level updated and saved", style="green")

    def _manage_interests(self):
        """Manage user interests."""
        profile = self.user_profile.get_user_profile()
        interests = profile.get('interests', [])

        self.console.print("\nCurrent interests:", style="yellow")
        if interests:
            for idx, interest in enumerate(interests, 1):
                self.console.print(f"  {idx}. {interest}", style="dim")
        else:
            self.console.print("  (none)", style="dim")

        self.console.print("\nActions: [a]dd, [r]emove, [b]ack")
        action = input("Choose action: ").strip().lower()

        if action == "a":
            new_interest = input("Enter new interest: ").strip()
            if new_interest:
                self.user_profile.add_interest(new_interest)
                self.settings_manager.system_instruction = self.user_profile.get_system_instruction()
                self.console.print("✓ Interest added and saved", style="green")
        elif action == "r":
            interest_to_remove = input("Enter interest to remove: ").strip()
            if interest_to_remove:
                self.user_profile.remove_interest(interest_to_remove)
                self.settings_manager.system_instruction = self.user_profile.get_system_instruction()
                self.console.print("✓ Interest removed and saved", style="green")

    def _manage_habits(self):
        """Manage user habits."""
        profile = self.user_profile.get_user_profile()
        habits = profile.get('habits', [])

        self.console.print("\nCurrent habits:", style="yellow")
        if habits:
            for idx, habit in enumerate(habits, 1):
                self.console.print(f"  {idx}. {habit}", style="dim")
        else:
            self.console.print("  (none)", style="dim")

        self.console.print("\nActions: [a]dd, [r]emove, [b]ack")
        action = input("Choose action: ").strip().lower()

        if action == "a":
            new_habit = input("Enter new habit: ").strip()
            if new_habit:
                self.user_profile.add_habit(new_habit)
                self.settings_manager.system_instruction = self.user_profile.get_system_instruction()
                self.console.print("✓ Habit added and saved", style="green")
        elif action == "r":
            habit_to_remove = input("Enter habit to remove: ").strip()
            if habit_to_remove:
                self.user_profile.remove_habit(habit_to_remove)
                self.settings_manager.system_instruction = self.user_profile.get_system_instruction()
                self.console.print("✓ Habit removed and saved", style="green")

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

    @staticmethod
    def _get_groq_api_key() -> str:
        """Get Groq API key from environment or user input."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("GROQ_API_KEY not found in environment.")
            api_key = input("Enter your Groq API key: ").strip()
            if not api_key:
                print("Error: Groq API key is required for voice input")
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
            profile = self.user_profile.get_user_profile()
            self.ui_manager.display_welcome(
                current_model=self.current_model,
                temperature=self.settings_manager.temperature,
                top_k=self.settings_manager.top_k,
                top_p=self.settings_manager.top_p,
                max_output_tokens=self.settings_manager.max_output_tokens,
                user_name=profile.get('name')
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

        elif command_lower == "/profile":
            self._manage_profile()

        elif command_lower == "/compress":
            self.dialog_manager.compress_conversation()

        elif command_lower == "/tokens":
            self.dialog_manager.show_token_stats()

        elif command_lower == "/voice":
            self._handle_voice_input()

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
            except UnicodeDecodeError as e:
                self.console.print("\n[red]Encoding error: Unable to decode input.[/red]")
                self.console.print("[yellow]Please ensure your terminal supports UTF-8 encoding.[/yellow]")
                self.console.print(f"[dim]Error details: {str(e)}[/dim]")
                continue
            except Exception as e:
                self.console.print(f"\nError: {str(e)}", style="red")
                import traceback
                traceback.print_exc()

    def run(self):
        """Run the chat interface."""
        # Display encoding info if not UTF-8
        if sys.stdin.encoding.lower() != 'utf-8':
            self.console.print(
                f"[yellow]Warning: Terminal encoding is {sys.stdin.encoding}, UTF-8 recommended[/yellow]"
            )

        profile = self.user_profile.get_user_profile()
        self.ui_manager.display_welcome(
            current_model=self.current_model,
            temperature=self.settings_manager.temperature,
            top_k=self.settings_manager.top_k,
            top_p=self.settings_manager.top_p,
            max_output_tokens=self.settings_manager.max_output_tokens,
            user_name=profile.get('name')
        )
        self.chat_loop()


def main():
    """Main entry point."""
    chat = ConsoleChat()
    chat.run()


if __name__ == "__main__":
    main()
