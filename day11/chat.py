"""Console chat interface for Gemini API with Multi-MCP integration and Task Management."""

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
from core.text_manager import TextManager
from tasks import TaskStorage, APTaskScheduler
from notifications import MacOSNotifier

# Fix encoding for stdin/stdout on Windows and other platforms
if sys.stdin.encoding != 'utf-8':
    sys.stdin.reconfigure(encoding='utf-8')
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


class ConsoleChatWithMCP:
    """Console-based chat interface with multiple MCP servers."""

    MODELS = {
        "1": (GeminiModel.GEMINI_2_5_FLASH, "Gemini 2.5 Flash (Fast & Balanced)"),
        "2": (GeminiModel.GEMINI_2_5_FLASH_LITE, "Gemini 2.5 Flash Lite (Ultra Fast)"),
        "3": (GeminiModel.GEMINI_2_5_PRO, "Gemini 2.5 Pro (Most Advanced)")
    }

    DEFAULT_SYSTEM_INSTRUCTION = (
        "You are an AI assistant with access to cryptocurrency data and task management through MCP tools. "
        "You can get crypto prices, trending coins, and market summaries using CoinGecko API. "
        "You can also create, list, and manage background tasks using MCP tools like create_background_task. "
        "When user says something like 'Monitor Bitcoin every 1 minute with AI analysis', "
        "use create_background_task with schedule_type='interval', schedule_value='1 minutes' (PLURAL!), "
        "mcp_tool='get_crypto_by_symbol', tool_args={'symbol': 'btc', 'currency': 'usd'}, use_ai_summary=True. "
        "IMPORTANT: "
        "- schedule_value must use PLURAL form: '1 minutes', '30 minutes', '2 hours' (not '1 minute', '2 hour'). "
        "- For specific crypto: use get_crypto_by_symbol with symbol (btc, eth, sol, etc). "
        "- For top cryptos: use get_crypto_prices with limit parameter. "
        "- For trending: use get_trending_crypto (no args). "
        "Be helpful and provide clear explanations of what you're doing."
    )

    MCP_SERVER_DESCRIPTIONS = {
        "crypto": "Cryptocurrency data (CoinGecko)",
        "background": "Background task management"
    }

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

        # Task Management components (APScheduler-based)
        self.task_storage = TaskStorage("day11_tasks.db")

        # Initialize macOS notifier for task notifications
        self.notifier = MacOSNotifier(enabled=True)

        self.task_scheduler = APTaskScheduler(
            storage=self.task_storage,
            mcp_manager=self.mcp_manager,
            gemini_client=self.client,
            console=self.console,
            notifier=self.notifier
        )

        # Start APScheduler immediately
        self.task_scheduler.start()

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

        # Connect to background task manager server
        try:
            self.console.print("[yellow]Connecting to Background Task Manager...[/yellow]")
            spinner = Spinner("dots", text="Connecting...", style="yellow")
            with Live(spinner, console=self.console, transient=True):
                await self.mcp_manager.connect_client("background")

            client = self.mcp_manager.get_client("background")
            self.console.print("[green]✓ Connected to Background Task Manager[/green]")
            self.console.print(f"[dim]Found {len(client.get_tools())} tools[/dim]")
        except Exception as e:
            self.console.print(f"[red]✗ Failed to connect to Background server: {str(e)}[/red]")

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
        self.console.print("     GEMINI CHAT WITH MULTI-MCP SUPPORT", style="bold bright_cyan")
        self.console.print("=" * 60, style="bright_cyan")
        self.console.print("Commands:", style="yellow")
        self.console.print("  /mcp [server] - Show MCP servers (/mcp all for details)", style="dim")
        self.console.print("  /model        - Change model", style="dim")
        self.console.print("  /system       - View/change system instruction", style="dim")
        self.console.print("  /settings     - View/change generation settings", style="dim")
        self.console.print("  /compress     - Compress conversation history", style="dim")
        self.console.print("  /tokens       - Show token statistics", style="dim")
        self.console.print("  /clear        - Clear conversation history", style="dim")
        self.console.print("  /tasks        - Task management submenu", style="dim")
        self.console.print("  /quit         - Exit chat", style="dim")
        self.console.print("  /help         - Show this help", style="dim")
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

    def show_mcp_status(self, server_name: str = None):
        """Display MCP server status and available tools.

        Args:
            server_name: Specific server to show, 'all' for full details, None for summary
        """
        self.console.print("\n" + "=" * 60, style="bright_cyan")
        self.console.print("MCP Servers Status", style="yellow")
        self.console.print("=" * 60, style="bright_cyan")

        connected = self.mcp_manager.list_connected_clients()
        if not connected:
            self.console.print("[red]✗ Not connected to any MCP servers[/red]")
            self.console.print(
                "[dim]Available servers: fetch (HTTP), container (Apple)[/dim]"
            )
            self.console.print("=" * 60, style="bright_cyan")
            return

        # Show summary (default)
        if server_name is None:
            self.console.print(f"\n📡 [bold]Connected MCP Servers ({len(connected)}):[/bold]\n")

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
            self.console.print("\n[dim]Use '/mcp <name>' to see tools for specific server[/dim]")
            self.console.print("[dim]Use '/mcp all' to see all tools from all servers[/dim]")
            self.console.print("=" * 60, style="bright_cyan")
            return

        # Show all servers with full details
        if server_name == "all":
            all_tools = self.mcp_manager.get_all_tools_as_dict()
            for client_type, tools in all_tools.items():
                self._show_server_tools(client_type, tools)
            self.console.print("=" * 60, style="bright_cyan")
            return

        # Show specific server
        if server_name in connected:
            client = self.mcp_manager.get_client(server_name)
            tools = client.get_tools_as_dict()
            self._show_server_tools(server_name, tools, detailed=True)
            self.console.print("=" * 60, style="bright_cyan")
        else:
            self.console.print(f"[red]✗ Server '{server_name}' not connected[/red]")
            self.console.print(f"[dim]Connected servers: {', '.join(connected)}[/dim]")
            self.console.print("=" * 60, style="bright_cyan")

    def _show_server_tools(self, client_type: str, tools: list, detailed: bool = True):
        """Show tools for a specific server.

        Args:
            client_type: Type of MCP client
            tools: List of tool dictionaries
            detailed: Show detailed info including schemas
        """
        description = self.MCP_SERVER_DESCRIPTIONS.get(client_type, "")
        self.console.print(f"\n🔧 [green bold]{client_type.title()} MCP Server[/green bold]")
        if description:
            self.console.print(f"[dim]{description}[/dim]")
        self.console.print(f"[bold]Available tools: {len(tools)}[/bold]")
        self.console.print("─" * 60)

        for tool in tools:
            self.console.print(f"\n  • [cyan]{tool['name']}[/cyan]")
            self.console.print(f"    [dim]{tool['description']}[/dim]")

            if detailed and 'inputSchema' in tool and tool['inputSchema']:
                schema = tool['inputSchema']
                if 'properties' in schema and schema['properties']:
                    props = schema['properties']
                    required = schema.get('required', [])
                    self.console.print("    [yellow]Parameters:[/yellow]")
                    for prop_name, prop_info in props.items():
                        req_marker = "[red]*[/red]" if prop_name in required else " "
                        prop_type = prop_info.get('type', 'any')
                        prop_desc = prop_info.get('description', '')
                        self.console.print(f"      {req_marker} {prop_name} ({prop_type}): {prop_desc}", style="dim")

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
            if hasattr(result, 'structured_content') and result.structured_content:
                return json.dumps(result.structured_content, indent=2)

            # If it has data attribute
            if hasattr(result, 'data') and result.data:
                return json.dumps(result.data, indent=2)

            # Fallback to string representation
            return str(result)
        except Exception:
            # If extraction fails, return string representation
            return str(result)

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
        # Parse command and arguments
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
            # Enhanced /mcp command with arguments
            self.show_mcp_status(arg)
        elif cmd == "/model":
            self.select_model()
        elif cmd == "/system":
            self.manage_system_instruction()
        elif cmd == "/settings":
            self.manage_generation_settings()
        elif cmd == "/tokens":
            self.show_token_stats()
        elif cmd == "/compress":
            self.compress_conversation()
        elif cmd == "/tasks":
            self._handle_tasks_command(arg)
        elif cmd == "/help":
            self.display_welcome()
        else:
            self.console.print(f"Unknown command: {cmd}", style="red")
            self.console.print("Type /help for available commands", style="dim")

        return True

    # ===== TASK MANAGEMENT METHODS =====

    def _handle_tasks_command(self, arg: str = None):
        """Handle /tasks submenu.

        Args:
            arg: Command arguments
        """
        if not arg:
            self._show_tasks_menu()
            return

        parts = arg.split()
        subcmd = parts[0].lower()

        if subcmd == "list":
            self._show_tasks_list()
        elif subcmd == "add":
            self._add_task_interactive()
        elif subcmd == "remove" and len(parts) > 1:
            self._remove_task(int(parts[1]))
        elif subcmd == "start" and len(parts) > 1:
            self._start_task(int(parts[1]))
        elif subcmd == "stop" and len(parts) > 1:
            self._stop_task(int(parts[1]))
        elif subcmd == "pause" and len(parts) > 1:
            self._pause_task(int(parts[1]))
        elif subcmd == "resume" and len(parts) > 1:
            self._resume_task(int(parts[1]))
        elif subcmd == "run" and len(parts) > 1:
            asyncio.create_task(self._run_task_now(int(parts[1])))
        elif subcmd == "history" and len(parts) > 1:
            self._show_task_history(int(parts[1]))
        elif subcmd == "result" and len(parts) > 1:
            self._show_latest_result(int(parts[1]))
        elif subcmd == "status":
            self._show_scheduler_status()
        else:
            self.console.print("[red]Unknown tasks command. Type '/tasks' for help[/red]")

    def _show_tasks_menu(self):
        """Show tasks management menu."""
        self.console.print("\n" + "=" * 60, style="bright_cyan")
        self.console.print("TASK MANAGEMENT (APScheduler)", style="yellow")
        self.console.print("=" * 60, style="bright_cyan")
        self.console.print("Commands:", style="yellow")
        self.console.print("  /tasks list              - Show all tasks", style="dim")
        self.console.print("  /tasks add               - Create new task (interactive)", style="dim")
        self.console.print("  /tasks remove <id>       - Delete task", style="dim")
        self.console.print("  /tasks start <id>        - Enable task", style="dim")
        self.console.print("  /tasks stop <id>         - Disable task", style="dim")
        self.console.print("  /tasks pause <id>        - Pause task (keep scheduled)", style="dim")
        self.console.print("  /tasks resume <id>       - Resume paused task", style="dim")
        self.console.print("  /tasks run <id>          - Run task now", style="dim")
        self.console.print("  /tasks history <id>      - Show execution history", style="dim")
        self.console.print("  /tasks result <id>       - Get latest result", style="dim")
        self.console.print("  /tasks status            - Scheduler status", style="dim")
        self.console.print("=" * 60, style="bright_cyan")

        # Show current tasks summary
        tasks = self.task_storage.get_all_tasks()
        if tasks:
            enabled = sum(1 for t in tasks if t['enabled'])
            self.console.print(f"\nCurrent tasks: {len(tasks)} total, {enabled} active", style="dim")

    def _show_tasks_list(self):
        """Show all tasks."""
        tasks = self.task_storage.get_all_tasks()

        if not tasks:
            self.console.print("\n[yellow]No tasks configured[/yellow]")
            self.console.print("[dim]Use '/tasks add' to create your first task[/dim]")
            return

        self.console.print("\n" + "=" * 80, style="bright_cyan")
        self.console.print("BACKGROUND TASKS", style="yellow")
        self.console.print("=" * 80, style="bright_cyan")

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("ID", width=4, justify="center")
        table.add_column("Name", width=25)
        table.add_column("Schedule", width=15)
        table.add_column("MCP Tool", width=20)
        table.add_column("Status", width=10, justify="center")

        for task in tasks:
            status = "[green]✓ Active[/green]" if task['enabled'] else "[dim]⏸ Paused[/dim]"
            table.add_row(
                str(task['id']),
                task['name'],
                task['schedule_value'],
                task['mcp_tool'],
                status
            )

        self.console.print(table)
        self.console.print("=" * 80, style="bright_cyan")

    def _add_task_interactive(self):
        """Interactive task creation."""
        self.console.print("\n[yellow]Creating new background task...[/yellow]\n")

        try:
            # Task name
            name = input("Task name: ").strip()
            if not name:
                self.console.print("[red]Task name is required[/red]")
                return

            # Description
            description = input("Description (optional): ").strip()

            # Schedule type
            self.console.print("\nSchedule type:")
            self.console.print("  [1] Interval (every N minutes/hours)")
            self.console.print("  [2] Daily at specific time")
            self.console.print("  [3] Weekly at specific day/time")

            schedule_choice = input("Choose (1-3): ").strip()

            if schedule_choice == "1":
                schedule_type = "interval"
                schedule_value = input("Interval (e.g., '30 minutes', '1 hour'): ").strip()
            elif schedule_choice == "2":
                schedule_type = "daily"
                schedule_value = input("Time (e.g., '10:00', '15:30'): ").strip()
            elif schedule_choice == "3":
                schedule_type = "weekly"
                schedule_value = input("Day and time (e.g., 'Monday 09:00'): ").strip()
            else:
                self.console.print("[red]Invalid choice[/red]")
                return

            # MCP tool
            self.console.print("\nAvailable MCP tools:")
            self.console.print("  - get_crypto_prices (Get cryptocurrency prices)")
            self.console.print("  - get_trending_crypto (Get trending cryptocurrencies)")
            self.console.print("  - get_market_summary (Get global market summary)")

            mcp_tool = input("MCP tool name: ").strip()
            if not mcp_tool:
                self.console.print("[red]MCP tool is required[/red]")
                return

            # Tool arguments
            tool_args_str = input("Tool arguments as JSON (or press Enter for {}): ").strip()
            tool_args = json.loads(tool_args_str) if tool_args_str else {}

            # AI summary
            use_ai = input("Generate AI summaries? (Y/n): ").strip().lower()
            use_ai_summary = use_ai != 'n'

            # Notification level
            self.console.print("\nNotification level:")
            self.console.print("  [1] All - Show all executions")
            self.console.print("  [2] Errors - Only show errors")
            self.console.print("  [3] Significant - Only significant changes")
            self.console.print("  [4] Silent - Save to history only")

            notif_choice = input("Choose (1-4): ").strip()
            notification_level = {
                "1": "all",
                "2": "errors",
                "3": "significant",
                "4": "silent"
            }.get(notif_choice, "all")

            # Create task
            task_data = {
                "name": name,
                "description": description,
                "schedule_type": schedule_type,
                "schedule_value": schedule_value,
                "mcp_tool": mcp_tool,
                "tool_args": tool_args,
                "use_ai_summary": use_ai_summary,
                "notification_level": notification_level
            }

            task_id = self.task_scheduler.add_task(task_data)

            self.console.print(f"\n[green]✓ Task created! ID: {task_id}[/green]")
            task = self.task_storage.get_task(task_id)
            if task and task.get('next_run'):
                self.console.print(f"[dim]Next run: {task['next_run']}[/dim]")

        except json.JSONDecodeError:
            self.console.print("[red]Invalid JSON for tool arguments[/red]")
        except Exception as e:
            self.console.print(f"[red]Error creating task: {str(e)}[/red]")

    def _remove_task(self, task_id: int):
        """Remove a task."""
        try:
            task = self.task_storage.get_task(task_id)
            if not task:
                self.console.print(f"[red]Task {task_id} not found[/red]")
                return

            self.task_scheduler.remove_task(task_id)
            self.console.print(f"[green]✓ Task '{task['name']}' removed[/green]")
        except Exception as e:
            self.console.print(f"[red]Error removing task: {str(e)}[/red]")

    def _start_task(self, task_id: int):
        """Enable a task."""
        try:
            task = self.task_storage.get_task(task_id)
            if not task:
                self.console.print(f"[red]Task {task_id} not found[/red]")
                return

            self.task_scheduler.start_task(task_id)
            self.console.print(f"[green]✓ Task '{task['name']}' started[/green]")
        except Exception as e:
            self.console.print(f"[red]Error starting task: {str(e)}[/red]")

    def _stop_task(self, task_id: int):
        """Disable a task."""
        try:
            task = self.task_storage.get_task(task_id)
            if not task:
                self.console.print(f"[red]Task {task_id} not found[/red]")
                return

            self.task_scheduler.stop_task(task_id)
            self.console.print(f"[green]✓ Task '{task['name']}' stopped[/green]")
        except Exception as e:
            self.console.print(f"[red]Error stopping task: {str(e)}[/red]")

    def _pause_task(self, task_id: int):
        """Pause a task (APScheduler feature)."""
        try:
            task = self.task_storage.get_task(task_id)
            if not task:
                self.console.print(f"[red]Task {task_id} not found[/red]")
                return

            self.task_scheduler.pause_task(task_id)
            self.console.print(f"[yellow]⏸ Task '{task['name']}' paused[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Error pausing task: {str(e)}[/red]")

    def _resume_task(self, task_id: int):
        """Resume a paused task (APScheduler feature)."""
        try:
            task = self.task_storage.get_task(task_id)
            if not task:
                self.console.print(f"[red]Task {task_id} not found[/red]")
                return

            self.task_scheduler.resume_task(task_id)
            self.console.print(f"[green]▶ Task '{task['name']}' resumed[/green]")
        except Exception as e:
            self.console.print(f"[red]Error resuming task: {str(e)}[/red]")

    async def _run_task_now(self, task_id: int):
        """Run a task immediately."""
        try:
            task = self.task_storage.get_task(task_id)
            if not task:
                self.console.print(f"[red]Task {task_id} not found[/red]")
                return

            self.console.print(f"[yellow]Running task '{task['name']}'...[/yellow]")
            await self.task_scheduler.run_task_now(task_id)
        except Exception as e:
            self.console.print(f"[red]Error running task: {str(e)}[/red]")

    def _show_task_history(self, task_id: int):
        """Show task execution history."""
        try:
            task = self.task_storage.get_task(task_id)
            if not task:
                self.console.print(f"[red]Task {task_id} not found[/red]")
                return

            history = self.task_storage.get_task_history(task_id, limit=20)

            if not history:
                self.console.print(f"\n[yellow]No execution history for task '{task['name']}'[/yellow]")
                return

            self.console.print("\n" + "=" * 80, style="bright_cyan")
            self.console.print(f"TASK HISTORY: {task['name']}", style="yellow")
            self.console.print("=" * 80, style="bright_cyan")

            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Time", width=20)
            table.add_column("Status", width=10, justify="center")
            table.add_column("Duration", width=10, justify="right")
            table.add_column("Summary", width=35)

            for entry in history:
                status = "[green]✓[/green]" if entry['status'] == 'success' else "[red]✗[/red]"
                duration = f"{entry['duration_ms']}ms" if entry['duration_ms'] else "-"
                summary = entry['ai_summary'] or entry.get('error_message', '')[:35] or "-"

                table.add_row(
                    entry['run_time'],
                    status,
                    duration,
                    summary
                )

            self.console.print(table)
            self.console.print("=" * 80, style="bright_cyan")

        except Exception as e:
            self.console.print(f"[red]Error getting history: {str(e)}[/red]")

    def _show_latest_result(self, task_id: int):
        """Show latest task execution result."""
        try:
            task = self.task_storage.get_task(task_id)
            if not task:
                self.console.print(f"[red]Task {task_id} not found[/red]")
                return

            result = self.task_storage.get_latest_result(task_id)

            if not result:
                self.console.print(f"\n[yellow]No results yet for task '{task['name']}'[/yellow]")
                return

            self.console.print("\n" + "=" * 80, style="bright_cyan")
            self.console.print(f"LATEST RESULT: {task['name']}", style="yellow")
            self.console.print("=" * 80, style="bright_cyan")

            self.console.print(f"Time: {result['run_time']}", style="dim")
            self.console.print(
                f"Status: {'✓ Success' if result['status'] == 'success' else '✗ Error'}",
                style="green" if result['status'] == 'success' else "red"
            )
            self.console.print(f"Duration: {result['duration_ms']}ms", style="dim")

            if result.get('ai_summary'):
                self.console.print("\nAI Summary:", style="yellow")
                self.console.print(result['ai_summary'])

            if result.get('raw_data'):
                self.console.print("\nRaw Data:", style="yellow")
                try:
                    self.console.print_json(result['raw_data'])
                except Exception:
                    self.console.print(result['raw_data'])

            if result.get('error_message'):
                self.console.print("\nError:", style="red")
                self.console.print(result['error_message'])

            self.console.print("=" * 80, style="bright_cyan")

        except Exception as e:
            self.console.print(f"[red]Error getting result: {str(e)}[/red]")

    def _show_scheduler_status(self):
        """Show scheduler status."""
        self.console.print("\n" + "=" * 60, style="bright_cyan")
        self.console.print("SCHEDULER STATUS (APScheduler)", style="yellow")
        self.console.print("=" * 60, style="bright_cyan")

        stats = self.task_scheduler.get_stats()

        running = stats['scheduler_running']
        self.console.print(f"Scheduler: {'[green]✓ Running[/green]' if running else '[red]✗ Stopped[/red]'}")

        if stats['uptime_seconds'] > 0:
            uptime_str = f"{int(stats['uptime_seconds'] // 60)}m {int(stats['uptime_seconds'] % 60)}s"
            self.console.print(f"Uptime: {uptime_str}")

        self.console.print(f"Active jobs: {stats['active_jobs']}")
        self.console.print(f"Tasks executed: {stats['tasks_executed']}")
        self.console.print(f"Tasks failed: {stats['tasks_failed']}")
        self.console.print(f"Tasks missed: {stats['tasks_missed']}")

        self.console.print("=" * 60, style="bright_cyan")

    # ===== END TASK MANAGEMENT METHODS =====

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

                        # Extract clean result from MCP response
                        result_data = self._extract_mcp_result(result)

                        # Add function response to conversation
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
                    print("\n\nExiting...")
                    break
                except Exception as e:
                    print(f"\n✗ Error: {str(e)}")
                    print("Please try again or type /quit to exit")

        finally:
            # Stop APScheduler
            self.task_scheduler.stop()

            # Cleanup
            try:
                await asyncio.shield(self.mcp_manager.disconnect_all())
            except Exception:
                pass

            try:
                self.client.close()
            except Exception:
                pass

    async def run(self):
        """Start the chat application."""
        try:
            await self.chat_loop()
        except Exception as e:
            print(f"Fatal error: {str(e)}")
            sys.exit(1)


def main():
    """Entry point for the chat application."""
    chat = ConsoleChatWithMCP()
    asyncio.run(chat.run())


if __name__ == "__main__":
    main()
