"""Console chat interface for Gemini API with Browser MCP integration."""

import asyncio
import json
import os
import sys

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.spinner import Spinner

from conversation import ConversationHistory
from gemini_client import GeminiApiClient, GeminiModel
from mcp_clients import MCPManager
from text_manager import TextManager

# Fix encoding for stdin/stdout on Windows and other platforms
if sys.stdin.encoding != 'utf-8':
    sys.stdin.reconfigure(encoding='utf-8')
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


class ConsoleChatWithBrowser:
    """Console-based chat interface with browser automation via MCP."""

    MODELS = {
        "1": (GeminiModel.GEMINI_2_5_FLASH, "Gemini 2.5 Flash (Fast & Balanced)"),
        "2": (GeminiModel.GEMINI_2_5_FLASH_LITE, "Gemini 2.5 Flash Lite (Ultra Fast)"),
        "3": (GeminiModel.GEMINI_2_5_PRO, "Gemini 2.5 Pro (Most Advanced)")
    }

    DEFAULT_SYSTEM_INSTRUCTION = (
        "You are an AI assistant with browser automation capabilities. "
        "You can navigate websites, click elements, fill forms, and extract information. "
        "When the user asks you to do something with a browser, use the appropriate browser tools. "
        "Be helpful and provide clear explanations of what you're doing."
    )

    def __init__(self):
        """Initialize chat interface."""
        self.api_key = self._get_api_key()
        self.client = GeminiApiClient(self.api_key)
        self.conversation = ConversationHistory()
        self.mcp_manager = MCPManager()
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

    async def connect_to_mcp(self):
        """Connect to MCP servers."""
        # Try to connect to fetch server first (no API key needed)
        try:
            self.console.print("\n[yellow]Connecting to Fetch MCP server...[/yellow]")
            spinner = Spinner("dots", text="Connecting...", style="yellow")
            with Live(spinner, console=self.console, transient=True):
                await self.mcp_manager.connect_client("fetch")

            client = self.mcp_manager.get_client("fetch")
            self.console.print("[green]✓ Connected to Fetch MCP server[/green]")
            self.console.print(f"[dim]Found {len(client.get_tools())} tools[/dim]")
        except Exception as e:
            self.console.print(f"[red]✗ Failed to connect to Fetch server: {str(e)}[/red]")

        # Try to connect to browser server (requires ANTHROPIC_API_KEY)
        try:
            self.console.print("\n[yellow]Connecting to Browser MCP server...[/yellow]")
            spinner = Spinner("dots", text="Connecting...", style="yellow")
            with Live(spinner, console=self.console, transient=True):
                await self.mcp_manager.connect_client("browser")

            client = self.mcp_manager.get_client("browser")
            self.console.print("[green]✓ Connected to Browser MCP server[/green]")
            self.console.print(f"[dim]Found {len(client.get_tools())} tools[/dim]")
        except Exception as e:
            self.console.print(f"[red]✗ Failed to connect to Browser server: {str(e)}[/red]")
            self.console.print("[yellow]Tip: Set ANTHROPIC_API_KEY to enable browser automation[/yellow]")

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
        self.console.print("\n" + "=" * 60, style="bright_cyan")
        self.console.print("     GEMINI CHAT WITH BROWSER AUTOMATION", style="bold bright_cyan")
        self.console.print("=" * 60, style="bright_cyan")
        self.console.print("Commands:", style="yellow")
        self.console.print("  /mcp      - Show MCP server status and available tools", style="dim")
        self.console.print("  /model    - Change model", style="dim")
        self.console.print("  /system   - View/change system instruction", style="dim")
        self.console.print("  /settings - View/change generation settings", style="dim")
        self.console.print("  /compress - Compress conversation history", style="dim")
        self.console.print("  /tokens   - Show token statistics", style="dim")
        self.console.print("  /clear    - Clear conversation history", style="dim")
        self.console.print("  /quit     - Exit chat", style="dim")
        self.console.print("  /help     - Show this help", style="dim")
        self.console.print("=" * 60, style="bright_cyan")
        self.console.print(f"Current model: {self._get_model_name()}", style="green")

        connected = self.mcp_manager.list_connected_clients()
        if connected:
            mcp_status = f"[green]Connected: {', '.join(connected)}[/green]"
        else:
            mcp_status = "[red]Not connected[/red]"
        self.console.print(f"MCP Servers: {mcp_status}")

        self.console.print(
            f"Temperature: {self.temperature} | TopK: {self.top_k} | "
            f"TopP: {self.top_p} | MaxTokens: {self.max_output_tokens}",
            style="dim"
        )
        if self.system_instruction:
            if len(self.system_instruction) > 70:
                preview = self.system_instruction[:70] + "..."
            else:
                preview = self.system_instruction
            self.console.print(f"System instruction: {preview}", style="dim")
        self.console.print("=" * 60 + "\n", style="bright_cyan")

    def _get_model_name(self) -> str:
        """Get human-readable name of current model."""
        for _, (model, name) in self.MODELS.items():
            if model == self.current_model:
                return name
        return self.current_model

    def show_mcp_status(self):
        """Display MCP server status and available tools."""
        self.console.print("\n" + "=" * 60, style="bright_cyan")
        self.console.print("MCP Servers Status", style="yellow")
        self.console.print("=" * 60, style="bright_cyan")

        connected = self.mcp_manager.list_connected_clients()
        if not connected:
            self.console.print("[red]✗ Not connected to any MCP servers[/red]")
            self.console.print(
                "[dim]Available servers: fetch (HTTP), browser (requires ANTHROPIC_API_KEY)[/dim]"
            )
        else:
            all_tools = self.mcp_manager.get_all_tools_as_dict()
            for client_type, tools in all_tools.items():
                self.console.print(f"\n[green]✓ {client_type.title()} MCP Server[/green]")
                self.console.print(f"[bold]Available tools: {len(tools)}[/bold]")
                self.console.print("-" * 60)

                for tool in tools:
                    self.console.print(f"\n[cyan]Tool: {tool['name']}[/cyan]")
                    self.console.print(f"[dim]Description: {tool['description']}[/dim]")
                    if 'inputSchema' in tool and tool['inputSchema']:
                        schema_str = json.dumps(tool['inputSchema'], indent=2)
                        if len(schema_str) > 200:
                            schema_str = schema_str[:200] + "..."
                        self.console.print(f"[dim]Schema: {schema_str}[/dim]")

        self.console.print("=" * 60, style="bright_cyan")

    def _print_response(self, text: str):
        """Print response with JSON formatting if applicable.

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
            self.conversation.clear()
            self.console.print("✓ Conversation history cleared", style="green")

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
        """Display detailed token statistics."""
        stats = self.conversation.get_compression_stats()

        self.console.print("\n" + "=" * 60, style="bright_cyan")
        self.console.print("Token Statistics", style="yellow")
        self.console.print("=" * 60, style="bright_cyan")

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
        elif command == "/mcp":
            self.show_mcp_status()
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
        elif command == "/help":
            self.display_welcome()
        else:
            self.console.print(f"Unknown command: {command}", style="red")
            self.console.print("Type /help for available commands", style="dim")

        return True

    async def process_user_message(self, user_input: str):
        """Process user message and handle function calling loop.

        Args:
            user_input: User's message
        """
        # Add user message to history
        self.conversation.add_user_message(user_input)

        # Get all tools from connected MCP servers
        tools = self.mcp_manager.get_all_tools_for_gemini()

        # Function calling loop
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Send request to Gemini
            spinner = Spinner("dots", text="Thinking...", style="bright_magenta")
            with Live(spinner, console=self.console, transient=True):
                response = self.client.generate_content(
                    prompt=user_input if iteration == 1 else "",
                    model=self.current_model,
                    conversation_history=self.conversation.get_history(),
                    system_instruction=self.system_instruction,
                    temperature=self.temperature,
                    top_k=self.top_k,
                    top_p=self.top_p,
                    max_output_tokens=self.max_output_tokens,
                    tools=tools
                )

            # Handle token usage
            usage = self.client.extract_usage_metadata(response)
            if usage:
                self.conversation.add_tokens(usage['total_tokens'])

            # Check if response contains function calls
            if self.client.has_function_calls(response):
                function_calls = self.client.extract_function_calls(response)

                # Add model's response with function calls to history
                # We need to add the raw model response before function results
                model_content = response['candidates'][0]['content']
                self.conversation.history.append(model_content)

                # Execute each function call
                for func_call in function_calls:
                    tool_name = func_call['name']
                    tool_args = func_call['args']

                    self.console.print(f"\n[yellow]🔧 Calling tool: {tool_name}[/yellow]")
                    self.console.print(f"[dim]Arguments: {json.dumps(tool_args, indent=2)}[/dim]")

                    try:
                        # Call MCP tool
                        text = "Executing {}...".format(tool_name)
                        spinner = Spinner("dots", text=text, style="yellow")
                        with Live(spinner, console=self.console, transient=True):
                            result = await self.mcp_manager.call_tool(
                                tool_name, tool_args
                            )

                        self.console.print("[green]✓ Tool executed successfully[/green]")

                        # Add function response to conversation
                        result_str = str(result)
                        # Gemini expects function responses in a specific format
                        self.conversation.history.append({
                            "role": "function",
                            "parts": [{
                                "functionResponse": {
                                    "name": tool_name,
                                    "response": {"result": result_str}
                                }
                            }]
                        })

                    except Exception as e:
                        self.console.print(f"[red]✗ Tool execution failed: {str(e)}[/red]")

                        # Add error response
                        self.conversation.history.append({
                            "role": "function",
                            "parts": [{
                                "functionResponse": {
                                    "name": tool_name,
                                    "response": {"error": str(e)}
                                }
                            }]
                        })

                # Continue loop to get final text response
                continue

            else:
                # No function calls, extract text response
                self.console.print("Assistant: ", style="bold bright_magenta", end="")
                assistant_text = self.client.extract_text(response)
                self._print_response(assistant_text)

                # Display token usage
                if usage:
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
                        self.console.print(
                            "\n[yellow]⚠️  Context limit reached! Auto-compressing...[/yellow]"
                        )
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

                # Add assistant message to history
                self.conversation.add_assistant_message(assistant_text)

                # Break the loop - we have final response
                break

    async def chat_loop(self):
        """Main chat loop."""
        self.display_welcome()

        # Try to connect to MCP
        await self.connect_to_mcp()

        try:
            while True:
                try:
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

                    # Process user message
                    await self.process_user_message(user_input)

                except KeyboardInterrupt:
                    # Exit immediately on Ctrl+C
                    print("\n\nExiting...")
                    break
                except Exception as e:
                    print(f"\n✗ Error: {str(e)}")
                    print("Please try again or type /quit to exit")

        finally:
            # Cleanup - handle errors gracefully
            # Use asyncio.shield to protect cleanup from cancellation
            try:
                await asyncio.shield(self.mcp_manager.disconnect_all())
            except Exception:
                pass  # Silently ignore cleanup errors

            try:
                self.client.close()
            except Exception:
                pass  # Silently ignore cleanup errors

    async def run(self):
        """Start the chat application."""
        try:
            await self.chat_loop()
        except Exception as e:
            print(f"Fatal error: {str(e)}")
            sys.exit(1)


def main():
    """Entry point for the chat application."""
    chat = ConsoleChatWithBrowser()
    asyncio.run(chat.run())


if __name__ == "__main__":
    main()
