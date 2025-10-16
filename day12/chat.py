"""Console chat interface for Gemini API with MCP Pipeline support."""

import asyncio
import os
import sys

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.table import Table

from core.conversation import ConversationHistory
from core.gemini_client import GeminiApiClient, GeminiModel
from core.text_manager import TextManager
from mcp_clients.manager import MCPManager
from agent import PipelineAgent

# Fix encoding for stdin/stdout
if sys.stdin.encoding != 'utf-8':
    sys.stdin.reconfigure(encoding='utf-8')
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


class ConsoleChatWithPipeline:
    """Console chat with MCP servers and pipeline agent."""

    MODELS = {
        "1": (GeminiModel.GEMINI_2_5_FLASH, "Gemini 2.5 Flash (Fast & Balanced)"),
        "2": (GeminiModel.GEMINI_2_5_FLASH_LITE, "Gemini 2.5 Flash Lite (Ultra Fast)"),
        "3": (GeminiModel.GEMINI_2_5_PRO, "Gemini 2.5 Pro (Most Advanced)")
    }

    DEFAULT_SYSTEM_INSTRUCTION = (
        "You are an AI assistant with access to cryptocurrency data and file operations. "
        "You can analyze crypto prices, trends, and save reports to files. "
        "Be helpful and provide clear explanations."
    )

    MCP_SERVER_DESCRIPTIONS = {
        "crypto": "Cryptocurrency data (CoinGecko API)",
        "pipeline": "File operations (save, read files)"
    }

    def __init__(self):
        """Initialize chat interface."""
        self.api_key = self._get_api_key()
        self.client = GeminiApiClient(self.api_key)
        self.conversation = ConversationHistory()
        self.mcp_manager = MCPManager()
        self.pipeline_agent = None  # Lazy init
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
        """Get API key from environment."""
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
        # Connect to crypto server
        try:
            self.console.print("\n[yellow]Connecting to Crypto MCP server...[/yellow]")
            spinner = Spinner("dots", text="Connecting...", style="yellow")
            with Live(spinner, console=self.console, transient=True):
                await self.mcp_manager.connect_client("crypto")

            client = self.mcp_manager.get_client("crypto")
            self.console.print("[green]✓ Connected to Crypto MCP server[/green]")
            self.console.print(f"[dim]Found {len(client.get_tools())} tools[/dim]")
        except Exception as e:
            self.console.print(f"[red]✗ Failed to connect to Crypto server: {str(e)}[/red]")

        # Connect to pipeline server
        try:
            self.console.print("\n[yellow]Connecting to Pipeline MCP server...[/yellow]")
            spinner = Spinner("dots", text="Connecting...", style="yellow")
            with Live(spinner, console=self.console, transient=True):
                await self.mcp_manager.connect_client("pipeline")

            client = self.mcp_manager.get_client("pipeline")
            self.console.print("[green]✓ Connected to Pipeline MCP server[/green]")
            self.console.print(f"[dim]Found {len(client.get_tools())} tools[/dim]")
        except Exception as e:
            self.console.print(f"[red]✗ Failed to connect to Pipeline server: {str(e)}[/red]")

    def display_welcome(self):
        """Display welcome message."""
        self.console.print("\n" + "=" * 70, style="bright_cyan")
        self.console.print("   GEMINI CHAT WITH MCP PIPELINE AGENT", style="bold bright_cyan")
        self.console.print("=" * 70, style="bright_cyan")
        self.console.print("Commands:", style="yellow")
        self.console.print("  /pipeline <task> - Run pipeline agent for complex tasks", style="dim")
        self.console.print("  /mcp [server]    - Show MCP servers", style="dim")
        self.console.print("  /model           - Change model", style="dim")
        self.console.print("  /system          - View/change system instruction", style="dim")
        self.console.print("  /tokens          - Show token statistics", style="dim")
        self.console.print("  /clear           - Clear conversation history", style="dim")
        self.console.print("  /quit            - Exit chat", style="dim")
        self.console.print("  /help            - Show this help", style="dim")
        self.console.print("=" * 70, style="bright_cyan")
        self.console.print(f"Current model: {self._get_model_name()}", style="green")

        connected = self.mcp_manager.list_connected_clients()
        if connected:
            mcp_status = f"[green]Connected: {', '.join(connected)}[/green]"
        else:
            mcp_status = "[red]Not connected[/red]"
        self.console.print(f"MCP Servers: {mcp_status}")
        self.console.print("=" * 70 + "\n", style="bright_cyan")

    def _get_model_name(self) -> str:
        """Get human-readable name of current model."""
        for _, (model, name) in self.MODELS.items():
            if model == self.current_model:
                return name
        return self.current_model

    def select_model(self):
        """Display model selection menu."""
        self.console.print("\n" + "=" * 50, style="bright_cyan")
        self.console.print("Available Models:", style="yellow")
        for key, (_, name) in self.MODELS.items():
            marker = "✓" if self.MODELS[key][0] == self.current_model else " "
            style = "green" if marker == "✓" else "dim"
            self.console.print(f"  [{marker}] {key}. {name}", style=style)

        choice = input("\nSelect model (1-3) or press Enter: ").strip()
        if choice in self.MODELS:
            self.current_model = self.MODELS[choice][0]
            self.console.print(f"✓ Model changed to: {self.MODELS[choice][1]}", style="green")
            self.conversation.clear()

    def show_mcp_status(self, server_name: str = None):
        """Display MCP server status."""
        self.console.print("\n" + "=" * 60, style="bright_cyan")
        self.console.print("MCP Servers Status", style="yellow")
        self.console.print("=" * 60, style="bright_cyan")

        connected = self.mcp_manager.list_connected_clients()
        if not connected:
            self.console.print("[red]✗ Not connected to any MCP servers[/red]")
            return

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Server", style="green", width=12)
        table.add_column("Tools", justify="right", width=8)
        table.add_column("Description", style="dim")

        for client_type in connected:
            client = self.mcp_manager.get_client(client_type)
            tool_count = len(client.get_tools())
            description = self.MCP_SERVER_DESCRIPTIONS.get(client_type, "")
            table.add_row(f"✓ {client_type}", str(tool_count), description)

        self.console.print(table)
        self.console.print("=" * 60, style="bright_cyan")

    async def run_pipeline(self, task: str):
        """Run pipeline agent for a task."""
        # Lazy init pipeline agent
        if not self.pipeline_agent:
            self.pipeline_agent = PipelineAgent(self.api_key, enable_notifications=True)
            await self.pipeline_agent.connect_servers()

        self.console.print(f"\n[yellow]🚀 Running pipeline: {task}[/yellow]\n")

        try:
            result = await self.pipeline_agent.execute_task(task)

            if result['success']:
                self.console.print(
                    f"\n[green]✓ Pipeline completed in {result['iterations']} iterations![/green]"
                )
            else:
                self.console.print("\n[red]✗ Pipeline failed[/red]")

        except Exception as e:
            self.console.print(f"\n[red]✗ Pipeline error: {str(e)}[/red]")

    def show_token_stats(self):
        """Display token statistics."""
        stats = self.conversation.get_compression_stats()

        self.console.print("\n" + "=" * 60, style="bright_cyan")
        self.console.print("Token Statistics", style="yellow")
        self.console.print("=" * 60, style="bright_cyan")

        progress = TextManager.format_token_usage(
            stats['total_tokens'],
            stats['max_tokens']
        )
        self.console.print(f"Context Usage: {progress}", style="bold")
        self.console.print(f"Messages: {stats['message_count']}", style="dim")
        self.console.print(f"Total tokens: {stats['total_tokens']:,}", style="dim")
        self.console.print("=" * 60, style="bright_cyan")

    async def handle_command(self, command: str) -> bool:
        """Handle special commands."""
        parts = command.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None

        if cmd == "/quit":
            self.console.print("\nGoodbye!", style="bold bright_cyan")
            return False
        elif cmd == "/clear":
            self.conversation.clear()
            self.console.print("✓ Conversation history cleared", style="green")
        elif cmd == "/mcp":
            self.show_mcp_status(arg)
        elif cmd == "/model":
            self.select_model()
        elif cmd == "/tokens":
            self.show_token_stats()
        elif cmd == "/help":
            self.display_welcome()
        elif cmd == "/pipeline":
            if not arg:
                self.console.print("[red]Usage: /pipeline <task>[/red]", style="red")
                self.console.print(
                    "[dim]Example: /pipeline Analyze Bitcoin and save to btc.txt[/dim]"
                )
            else:
                await self.run_pipeline(arg)
        else:
            self.console.print(f"Unknown command: {cmd}", style="red")

        return True

    def _extract_mcp_result(self, result) -> str:
        """Extract clean data from MCP result."""
        try:
            if hasattr(result, 'content'):
                content_list = result.content
                if content_list and len(content_list) > 0:
                    first_content = content_list[0]
                    if hasattr(first_content, 'text'):
                        return first_content.text
            return str(result)
        except Exception:
            return str(result)

    async def process_user_message(self, user_input: str):
        """Process user message with MCP tools."""
        self.conversation.add_user_message(user_input)

        # Get all tools from connected MCP servers
        tools = self.mcp_manager.get_all_tools_for_gemini()

        # Function calling loop
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

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

            usage = self.client.extract_usage_metadata(response)
            if usage:
                self.conversation.add_tokens(usage['total_tokens'])

            if self.client.has_function_calls(response):
                function_calls = self.client.extract_function_calls(response)
                model_content = response['candidates'][0]['content']
                self.conversation.history.append(model_content)

                for func_call in function_calls:
                    tool_name = func_call['name']
                    tool_args = func_call['args']

                    self.console.print(f"\n[yellow]🔧 Calling: {tool_name}[/yellow]")

                    try:
                        result = await self.mcp_manager.call_tool(tool_name, tool_args)
                        self.console.print("[green]✓ Success[/green]")
                        result_data = self._extract_mcp_result(result)

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
                        self.console.print(f"[red]✗ Error: {e}[/red]")
                        self.conversation.history.append({
                            "role": "function",
                            "parts": [{
                                "functionResponse": {
                                    "name": tool_name,
                                    "response": {"error": str(e)}
                                }
                            }]
                        })

                continue

            else:
                self.console.print("\nAssistant: ", style="bold bright_magenta", end="")
                assistant_text = self.client.extract_text(response)
                self.console.print(Markdown(assistant_text))

                if usage:
                    self.console.print(f"\n[dim]Tokens: {usage['total_tokens']}[/dim]")

                self.conversation.add_assistant_message(assistant_text)
                break

    async def chat_loop(self):
        """Main chat loop."""
        self.display_welcome()
        await self.connect_to_mcp()

        try:
            while True:
                try:
                    self.console.print("\nYou: ", style="bold bright_blue", end="")
                    user_input = input().strip()

                    if not user_input:
                        continue

                    if user_input.startswith("/"):
                        if not await self.handle_command(user_input):
                            break
                        continue

                    await self.process_user_message(user_input)

                except KeyboardInterrupt:
                    print("\n\nExiting...")
                    break
                except Exception as e:
                    print(f"\n✗ Error: {str(e)}")

        finally:
            await self.mcp_manager.disconnect_all()
            if self.pipeline_agent:
                await self.pipeline_agent.disconnect_servers()
                self.pipeline_agent.close()
            self.client.close()

    async def run(self):
        """Start the chat application."""
        try:
            await self.chat_loop()
        except Exception as e:
            print(f"Fatal error: {str(e)}")
            sys.exit(1)


def main():
    """Entry point."""
    chat = ConsoleChatWithPipeline()
    asyncio.run(chat.run())


if __name__ == "__main__":
    main()
