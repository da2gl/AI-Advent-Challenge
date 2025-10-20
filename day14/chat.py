"""Console chat interface for AI-powered code analysis with Filesystem MCP."""

import asyncio
import json
import os
import sys

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.table import Table

from core.conversation import ConversationHistory
from core.gemini_client import GeminiApiClient, GeminiModel
from mcp_clients import MCPManager

# Fix encoding for stdin/stdout on Windows and other platforms
if sys.stdin.encoding != 'utf-8':
    sys.stdin.reconfigure(encoding='utf-8')
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


class CodeAnalysisChat:
    """Console-based chat interface for code analysis with Filesystem MCP."""

    MODELS = {
        "1": (
            GeminiModel.GEMINI_2_5_FLASH,
            "Gemini 2.5 Flash (Fast & Balanced)"
        ),
        "2": (
            GeminiModel.GEMINI_2_5_FLASH_LITE,
            "Gemini 2.5 Flash Lite (Ultra Fast)"
        ),
        "3": (
            GeminiModel.GEMINI_2_5_PRO,
            "Gemini 2.5 Pro (Most Advanced)"
        )
    }

    DEFAULT_SYSTEM_INSTRUCTION = None

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
        # Increased for large outputs (project trees, code analysis)
        self.max_output_tokens = 8192

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

    async def connect_to_filesystem(self):
        """Connect to Filesystem MCP server."""
        try:
            self.console.print(
                "\n[yellow]Connecting to Filesystem MCP server...[/yellow]"
            )
            spinner = Spinner("dots", text="Connecting...", style="yellow")
            with Live(spinner, console=self.console, transient=True):
                await self.mcp_manager.connect_client("filesystem")

            client = self.mcp_manager.get_client("filesystem")
            self.console.print(
                "[green]✓ Connected to Filesystem MCP server[/green]"
            )
            self.console.print(
                f"[dim]Found {len(client.get_tools())} tools[/dim]"
            )
        except Exception as e:
            self.console.print(
                f"[red]✗ Failed to connect to Filesystem server: "
                f"{str(e)}[/red]"
            )
            self.console.print(
                "[red]Application cannot continue without "
                "filesystem access[/red]"
            )
            sys.exit(1)

    def display_welcome(self):
        """Display welcome message."""
        self.console.print("\n" + "=" * 70, style="bright_cyan")
        self.console.print(
            "     AI CODE ANALYSIS ASSISTANT WITH FILESYSTEM MCP",
            style="bold bright_cyan"
        )
        self.console.print("=" * 70, style="bright_cyan")
        self.console.print("Commands:", style="yellow")
        self.console.print(
            "  /mcp          - Show MCP server status and tools",
            style="dim"
        )
        self.console.print(
            "  /model        - Change AI model",
            style="dim"
        )
        self.console.print(
            "  /system       - View/change system instruction",
            style="dim"
        )
        self.console.print(
            "  /settings     - View/change generation settings",
            style="dim"
        )
        self.console.print(
            "  /tokens       - Show token statistics",
            style="dim"
        )
        self.console.print(
            "  /compress     - Compress conversation history",
            style="dim"
        )
        self.console.print(
            "  /clear        - Clear conversation history",
            style="dim"
        )
        self.console.print(
            "  /help         - Show this help",
            style="dim"
        )
        self.console.print(
            "  /quit         - Exit chat",
            style="dim"
        )
        self.console.print("=" * 70, style="bright_cyan")
        self.console.print(
            f"Current model: {self._get_model_name()}",
            style="green"
        )
        self.console.print("MCP Server: [green]Filesystem (6 tools)[/green]")
        self.console.print(
            f"Settings: Temp={self.temperature} | TopK={self.top_k} | "
            f"TopP={self.top_p} | MaxTokens={self.max_output_tokens}",
            style="dim"
        )
        self.console.print("=" * 70 + "\n", style="bright_cyan")

        # Show example usage
        self.console.print("[bold yellow]Example prompts:[/bold yellow]")
        self.console.print(
            "  • Analyze the day7 folder for bugs",
            style="dim"
        )
        self.console.print(
            "  • Show me the structure of the day13 project",
            style="dim"
        )
        self.console.print(
            "  • Find potential security issues in day10",
            style="dim"
        )
        self.console.print(
            "  • Search for unclosed resources in day11\n",
            style="dim"
        )

    def _get_model_name(self) -> str:
        """Get human-readable name of current model."""
        for _, (model, name) in self.MODELS.items():
            if model == self.current_model:
                return name
        return self.current_model

    def show_mcp_status(self):
        """Display MCP server status and available tools."""
        self.console.print("\n" + "=" * 70, style="bright_cyan")
        self.console.print(
            "Filesystem MCP Server - Available Tools",
            style="yellow"
        )
        self.console.print("=" * 70, style="bright_cyan")

        client = self.mcp_manager.get_client("filesystem")
        if not client:
            self.console.print("[red]✗ Not connected to Filesystem server[/red]")
            return

        tools = client.get_tools()

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Tool", style="green", width=20)
        table.add_column("Description", style="dim")

        for tool in tools:
            table.add_row(tool["name"], tool["description"])

        self.console.print(table)
        self.console.print(
            f"\n[green]Total: {len(tools)} tools available[/green]"
        )
        self.console.print("=" * 70, style="bright_cyan")

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

        choice = input(
            "\nSelect model (1-3) or press Enter to continue: "
        ).strip()
        if choice in self.MODELS:
            self.current_model = self.MODELS[choice][0]
            self.console.print(
                f"✓ Model changed to: {self.MODELS[choice][1]}",
                style="green"
            )
            self.conversation.clear()
            self.console.print("✓ Conversation history cleared", style="green")

    def show_token_stats(self):
        """Display detailed token usage statistics."""
        stats = self.conversation.get_token_stats()

        self.console.print("\n" + "=" * 50, style="bright_cyan")
        self.console.print("Token Usage Statistics", style="yellow")
        self.console.print("=" * 50, style="bright_cyan")

        self.console.print(
            f"Total tokens: [bold]{stats['total_tokens']:,}[/bold]"
        )
        self.console.print(f"  Prompt tokens: {stats['prompt_tokens']:,}")
        self.console.print(f"  Response tokens: {stats['response_tokens']:,}")
        self.console.print(f"\nContext limit: {stats['max_context_tokens']:,}")
        self.console.print(f"Remaining: {stats['remaining_tokens']:,}")

        usage_percent = (stats['total_tokens'] / stats['max_context_tokens']) * 100
        if usage_percent >= 80:
            color = "red"
        elif usage_percent >= 60:
            color = "yellow"
        else:
            color = "green"

        self.console.print(f"Usage: [{color}]{usage_percent:.1f}%[/{color}]")
        self.console.print("=" * 50, style="bright_cyan")

    def _extract_mcp_result(self, result) -> str:
        """Extract clean data from MCP CallToolResult.

        Args:
            result: MCP CallToolResult object or dict

        Returns:
            Clean JSON string or text content
        """
        try:
            # If it's a FastMCP CallToolResult object
            if hasattr(result, 'content'):
                content_list = result.content
                if content_list and len(content_list) > 0:
                    first_content = content_list[0]
                    # Extract text from TextContent
                    if hasattr(first_content, 'text'):
                        return first_content.text

            # If it has structured_content (dict)
            if (hasattr(result, 'structured_content')
                    and result.structured_content):
                return json.dumps(result.structured_content, indent=2)

            # If it has data attribute
            if hasattr(result, 'data') and result.data:
                return json.dumps(result.data, indent=2)

            # Fallback to string representation
            return str(result)
        except Exception:
            # If extraction fails, return string representation
            return str(result)

    async def process_user_message(self, user_input: str):
        """Process user message with multi-turn function calling.

        Args:
            user_input: User's message text
        """
        # Add user message to history
        self.conversation.add_user_message(user_input)

        # Get tools for Gemini
        tools = self.mcp_manager.get_all_tools_for_gemini()

        # Multi-turn function calling loop
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Show spinner while waiting for response
            spinner = Spinner("dots", text="Thinking...", style="cyan")
            with Live(spinner, console=self.console, transient=True):
                # Generate response
                # Iteration 1: send prompt + empty history (user message via prompt)
                # Iteration 2+: send no prompt + full history (includes user, function calls, responses)
                if iteration == 1:
                    # First iteration: use prompt, history excludes current user message
                    conv_history = self.conversation.get_history()
                    prompt = user_input
                else:
                    # Subsequent iterations: use full history, no new prompt
                    conv_history = self.conversation.history
                    prompt = None

                response = self.client.generate_content(
                    prompt=prompt,
                    model=self.current_model,
                    conversation_history=conv_history,
                    system_instruction=self.system_instruction,
                    temperature=self.temperature,
                    top_k=self.top_k,
                    top_p=self.top_p,
                    max_output_tokens=self.max_output_tokens,
                    timeout=120,
                    tools=tools
                )

            # Track tokens
            usage = self.client.extract_usage_metadata(response)
            if usage:
                self.conversation.add_token_usage(usage)

            # Check if response contains function calls
            if self.client.has_function_calls(response):
                function_calls = self.client.extract_function_calls(response)

                # Deduplicate function calls (Gemini sometimes returns duplicates)
                seen = set()
                unique_calls = []
                for fc in function_calls:
                    # Create a hashable key from function name and args
                    key = (fc['name'], json.dumps(fc['args'], sort_keys=True))
                    if key not in seen:
                        seen.add(key)
                        unique_calls.append(fc)

                if len(function_calls) != len(unique_calls):
                    self.console.print(
                        f"[dim]Note: Removed {len(function_calls) - len(unique_calls)} duplicate function call(s)[/dim]"
                    )

                function_calls = unique_calls

                # Add model's function call message to history
                model_content = response['candidates'][0]['content']
                self.conversation.history.append(model_content)

                # Execute each function call sequentially
                for func_call in function_calls:
                    tool_name = func_call['name']
                    tool_args = func_call['args']

                    self.console.print(f"\n🔧 [bold yellow]Calling tool:[/bold yellow] {tool_name}")

                    # Pretty print arguments
                    if tool_args:
                        self.console.print("[dim]Arguments:[/dim]")
                        for key, value in tool_args.items():
                            if isinstance(value, (list, dict)):
                                value_str = json.dumps(value, indent=2)
                            else:
                                value_str = str(value)
                            self.console.print(f"  [cyan]{key}[/cyan]: {value_str}", style="dim")

                    try:
                        # Call tool via MCPManager
                        result = await self.mcp_manager.call_tool(tool_name, tool_args)
                        result_data = self._extract_mcp_result(result)

                        self.console.print("[green]✓ Tool executed successfully[/green]")

                        # Show brief result summary (parse JSON if needed)
                        try:
                            parsed_data = json.loads(result_data) if isinstance(result_data, str) else result_data
                            if isinstance(parsed_data, dict):
                                if "success" in parsed_data and not parsed_data["success"]:
                                    self.console.print(f"[red]Error: {parsed_data.get('error', 'Unknown')}[/red]")
                                elif "tree" in parsed_data:
                                    self.console.print("[dim]Received project tree structure[/dim]")
                                elif "files" in parsed_data and isinstance(parsed_data["files"], list):
                                    self.console.print(f"[dim]Received {len(parsed_data['files'])} file(s)[/dim]")
                                elif "content" in parsed_data:
                                    lines = len(parsed_data.get("content", "").split('\n'))
                                    self.console.print(f"[dim]Read file with {lines} lines[/dim]")
                        except (json.JSONDecodeError, TypeError):
                            pass  # Not JSON or can't parse, skip summary

                        # Add function result to history
                        self.conversation.history.append({
                            "role": "function",
                            "parts": [{
                                "functionResponse": {
                                    "name": tool_name,
                                    "response": {"result": result_data}
                                }
                            }]
                        })

                    except Exception as e:
                        error_msg = str(e)
                        self.console.print(f"[red]✗ Tool execution failed: {error_msg}[/red]")

                        # Add error to history
                        self.conversation.history.append({
                            "role": "function",
                            "parts": [{
                                "functionResponse": {
                                    "name": tool_name,
                                    "response": {"error": error_msg, "success": False}
                                }
                            }]
                        })

                # Continue loop to get final text response
                continue

            else:
                # Final text response - add to history and display
                assistant_text = self.client.extract_text(response)

                # Check if text is empty
                if not assistant_text or assistant_text.strip() == "":
                    self.console.print("\n[yellow]⚠ Warning: AI returned empty text response[/yellow]")
                    self.console.print("[dim]Try rephrasing your question or use /clear to reset conversation.[/dim]")

                self.conversation.add_assistant_message(assistant_text)

                self.console.print("\n[bold green]Assistant:[/bold green]")
                self.console.print(Markdown(assistant_text))

                # Display token usage
                if usage:
                    self.console.print(
                        f"\n[dim]Tokens: {usage['prompt_tokens']} prompt + "
                        f"{usage['response_tokens']} response = "
                        f"{usage['total_tokens']} total[/dim]"
                    )

                    from core.text_manager import TextManager
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

                break

        if iteration >= max_iterations:
            self.console.print("\n[yellow]⚠ Max iterations reached. Conversation may be incomplete.[/yellow]")

    async def chat_loop(self):
        """Main chat loop."""
        while True:
            try:
                user_input = input("\n\nYou: ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith('/'):
                    await self.handle_command(user_input)
                    continue

                # Check if history needs compression
                if self.conversation.should_compress():
                    self.console.print("\n[yellow]⚠ Context limit approaching, compressing history...[/yellow]")
                    await self.compress_history()

                # Process user message
                await self.process_user_message(user_input)

            except KeyboardInterrupt:
                self.console.print("\n\n[yellow]Chat interrupted. Type /quit to exit or continue chatting.[/yellow]")
            except Exception as e:
                self.console.print(f"\n[red]Error: {str(e)}[/red]")

    async def handle_command(self, command: str):
        """Handle slash commands."""
        cmd = command.lower().split()[0]

        if cmd == '/quit':
            self.console.print("\n[yellow]Disconnecting from MCP servers...[/yellow]")
            await self.mcp_manager.disconnect_all()
            self.console.print("[green]Goodbye![/green]\n")
            sys.exit(0)

        elif cmd == '/help':
            self.display_welcome()

        elif cmd == '/mcp':
            self.show_mcp_status()

        elif cmd == '/model':
            self.select_model()

        elif cmd == '/tokens':
            self.show_token_stats()

        elif cmd == '/clear':
            self.conversation.clear()
            self.console.print("[green]✓ Conversation history cleared[/green]")

        elif cmd == '/compress':
            await self.compress_history()

        elif cmd == '/system':
            self.handle_system_instruction()

        elif cmd == '/settings':
            self.handle_settings()

        else:
            self.console.print(f"[red]Unknown command: {command}[/red]")
            self.console.print("[dim]Type /help for available commands[/dim]")

    def handle_system_instruction(self):
        """View or change system instruction."""
        self.console.print("\n" + "=" * 70, style="bright_cyan")
        self.console.print("System Instruction", style="yellow")
        self.console.print("=" * 70, style="bright_cyan")
        self.console.print(self.system_instruction, style="dim")
        self.console.print("=" * 70, style="bright_cyan")

        self.console.print("\n1. Keep current")
        self.console.print("2. Reset to default")
        self.console.print("3. Enter new instruction")

        choice = input("\nSelect option (1-3): ").strip()

        if choice == "2":
            self.system_instruction = self.DEFAULT_SYSTEM_INSTRUCTION
            self.console.print("[green]✓ Reset to default instruction[/green]")
        elif choice == "3":
            self.console.print("\n[yellow]Enter new system instruction (end with Ctrl+D or Ctrl+Z):[/yellow]")
            lines = []
            try:
                while True:
                    line = input()
                    lines.append(line)
            except EOFError:
                pass
            new_instruction = "\n".join(lines).strip()
            if new_instruction:
                self.system_instruction = new_instruction
                self.console.print("[green]✓ System instruction updated[/green]")

    def handle_settings(self):
        """View or change generation settings."""
        self.console.print("\n" + "=" * 50, style="bright_cyan")
        self.console.print("Generation Settings", style="yellow")
        self.console.print("=" * 50, style="bright_cyan")
        self.console.print(f"Temperature: {self.temperature} (0.0-2.0)")
        self.console.print(f"Top K: {self.top_k} (1-100)")
        self.console.print(f"Top P: {self.top_p} (0.0-1.0)")
        self.console.print(f"Max Output Tokens: {self.max_output_tokens}")
        self.console.print("=" * 50, style="bright_cyan")

        if input("\nChange settings? (y/n): ").strip().lower() == 'y':
            try:
                temp = input(f"Temperature [{self.temperature}]: ").strip()
                if temp:
                    self.temperature = float(temp)

                topk = input(f"Top K [{self.top_k}]: ").strip()
                if topk:
                    self.top_k = int(topk)

                topp = input(f"Top P [{self.top_p}]: ").strip()
                if topp:
                    self.top_p = float(topp)

                maxtok = input(f"Max Output Tokens [{self.max_output_tokens}]: ").strip()
                if maxtok:
                    self.max_output_tokens = int(maxtok)

                self.console.print("[green]✓ Settings updated[/green]")
            except ValueError:
                self.console.print("[red]Invalid input, settings unchanged[/red]")

    async def compress_history(self):
        """Compress conversation history using Gemini."""
        self.console.print("[yellow]Compressing conversation history...[/yellow]")

        try:
            summary = await self.conversation.compress_history(self.client, self.current_model)
            self.console.print(f"[green]✓ History compressed. Summary: {summary[:100]}...[/green]")
        except Exception as e:
            self.console.print(f"[red]Failed to compress history: {str(e)}[/red]")

    async def run(self):
        """Run the chat application."""
        await self.connect_to_filesystem()
        self.display_welcome()
        await self.chat_loop()


async def main():
    """Main entry point."""
    chat = CodeAnalysisChat()
    await chat.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExiting...")
