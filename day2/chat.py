"""Console chat interface for Gemini API."""

import json
import os
import sys

from rich.console import Console
from rich.markdown import Markdown

from conversation import ConversationHistory
from gemini_client import GeminiApiClient, GeminiModel


class ConsoleChat:
    """Console-based chat interface."""

    MODELS = {
        "1": (GeminiModel.GEMINI_2_5_FLASH, "Gemini 2.5 Flash (Fast & Balanced)"),
        "2": (GeminiModel.GEMINI_2_5_FLASH_LITE, "Gemini 2.5 Flash Lite (Ultra Fast)"),
        "3": (GeminiModel.GEMINI_2_5_PRO, "Gemini 2.5 Pro (Most Advanced)")
    }

    DEFAULT_SYSTEM_INSTRUCTION = """You must ALWAYS respond in strict JSON format.
Response format:
{
  "response": "your main response content",
  "type": "response_type",
  "confidence": 0.95,
  "metadata": {
    "timestamp": "ISO_timestamp",
    "source": "gemini"
  }
}
Do NOT add any text before or after the JSON. Only return valid JSON."""

    def __init__(self):
        """Initialize chat interface."""
        self.api_key = self._get_api_key()
        self.client = GeminiApiClient(self.api_key)
        self.conversation = ConversationHistory()
        self.current_model = GeminiModel.GEMINI_2_5_FLASH
        self.system_instruction = self.DEFAULT_SYSTEM_INSTRUCTION
        self.console = Console()

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
        print("\n" + "=" * 50)
        print("Available Models:")
        print("=" * 50)
        for key, (_, name) in self.MODELS.items():
            marker = "✓" if self.MODELS[key][0] == self.current_model else " "
            print(f"  [{marker}] {key}. {name}")
        print("=" * 50)

        choice = input("\nSelect model (1-3) or press Enter to continue: ").strip()
        if choice in self.MODELS:
            self.current_model = self.MODELS[choice][0]
            print(f"✓ Model changed to: {self.MODELS[choice][1]}")
            # Clear history when changing models
            self.conversation.clear()
            print("✓ Conversation history cleared")

    def display_welcome(self):
        """Display welcome message."""
        print("\n" + "=" * 50)
        print("     GEMINI CHAT - AI Assistant")
        print("=" * 50)
        print("Commands:")
        print("  /model   - Change model")
        print("  /system  - View/change system instruction")
        print("  /clear   - Clear conversation history")
        print("  /quit    - Exit chat")
        print("  /help    - Show this help")
        print("=" * 50)
        print(f"Current model: {self._get_model_name()}")
        print(f"System instruction: {self.system_instruction[:50]}...")
        print("=" * 50 + "\n")

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
            print()  # New line after "Assistant: "
            self.console.print_json(text.strip())
        except (json.JSONDecodeError, TypeError):
            # Not JSON, print as markdown with rich
            print()  # New line after "Assistant: "
            self.console.print(Markdown(text))

    def manage_system_instruction(self):
        """Display and optionally change system instruction."""
        print("\n" + "=" * 50)
        print("System Instruction Management")
        print("=" * 50)
        print(f"Current: {self.system_instruction}")
        print("=" * 50)

        choice = input("\nEnter new instruction (or press Enter to keep current): ").strip()
        if choice:
            self.system_instruction = choice
            print(f"✓ System instruction updated")
            # Clear history when changing system instruction
            self.conversation.clear()
            print("✓ Conversation history cleared")

    def handle_command(self, command: str) -> bool:
        """Handle special commands.

        Args:
            command: Command string (starting with /)

        Returns:
            True if should continue, False if should exit
        """
        command = command.lower().strip()

        if command == "/quit":
            print("\nGoodbye! 👋")
            return False
        elif command == "/clear":
            self.conversation.clear()
            print("✓ Conversation history cleared")
        elif command == "/model":
            self.select_model()
        elif command == "/system":
            self.manage_system_instruction()
        elif command == "/help":
            self.display_welcome()
        else:
            print(f"Unknown command: {command}")
            print("Type /help for available commands")

        return True

    def chat_loop(self):
        """Main chat loop."""
        self.display_welcome()

        while True:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    if not self.handle_command(user_input):
                        break
                    continue

                # Add user message to history
                self.conversation.add_user_message(user_input)

                # Send request to Gemini
                print("\nAssistant: ", end="", flush=True)
                response = self.client.generate_content(
                    prompt=user_input,
                    model=self.current_model,
                    conversation_history=self.conversation.get_history(),
                    system_instruction=self.system_instruction
                )

                # Extract and display response
                assistant_text = self.client.extract_text(response)
                self._print_response(assistant_text)

                # Display token usage if available
                usage = self.client.extract_usage_metadata(response)
                if usage:
                    self.conversation.add_tokens(usage['total_tokens'])
                    self.console.print(
                        f"\n[dim]Tokens: {usage['prompt_tokens']} prompt + "
                        f"{usage['response_tokens']} response = "
                        f"{usage['total_tokens']} total "
                        f"(session: {self.conversation.total_tokens})[/dim]"
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
