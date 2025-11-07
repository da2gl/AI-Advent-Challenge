#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
God Agent - CLI Interface
Simple chat interface using the unified GodAgent class
"""

import os
import sys
import asyncio
from pathlib import Path


# Suppress asyncio unhandled exception warnings for MCP cleanup
# These are harmless errors during shutdown
def suppress_mcp_cleanup_errors(event_loop, context):
    """Suppress MCP cleanup errors during asyncio shutdown."""
    message = context.get('message', '')
    if 'cancel scope' in message or 'Task was destroyed' in message:
        return  # Ignore MCP cleanup errors
    # For other errors, use default handler
    if event_loop.get_debug():
        event_loop.default_exception_handler(context)


# Set the exception handler for asyncio
asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())


# Set UTF-8 encoding for stdin/stdout
if sys.platform != 'win32':
    import locale
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except locale.Error:
        pass

from rich.console import Console  # noqa: E402
from rich.prompt import Prompt  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.markdown import Markdown  # noqa: E402

from god_agent import GodAgent, AgentCapabilities  # noqa: E402


class GodAgentCLI:
    """Command-line interface for God Agent."""

    def __init__(self):
        """Initialize CLI."""
        self.console = Console()
        self.agent = None
        self.conversation_history = []

        # Get API keys
        self.gemini_api_key = self._get_env_var("GEMINI_API_KEY", "Gemini API key")
        self.groq_api_key = os.getenv("GROQ_API_KEY")  # Optional

        # Get LLM provider
        self.llm_provider = os.getenv("LLM_PROVIDER", "gemini")

    def _get_env_var(self, var_name: str, display_name: str) -> str:
        """Get environment variable or prompt user."""
        value = os.getenv(var_name)
        if not value:
            self.console.print(f"[yellow]{var_name} not found in environment.[/yellow]")
            value = Prompt.ask(f"Enter your {display_name}")
            if not value:
                self.console.print(f"[red]Error: {display_name} is required[/red]")
                sys.exit(1)
        return value

    async def initialize(self):
        """Initialize God Agent."""
        self.console.print("\n[bold cyan]Initializing God Agent...[/bold cyan]\n")

        # Configure capabilities
        capabilities = AgentCapabilities(
            llm_enabled=True,
            rag_enabled=True,
            mcp_enabled=True,
            voice_enabled=bool(self.groq_api_key),
            tasks_enabled=True,
            code_analysis_enabled=True,
            deployment_enabled=True,
            notifications_enabled=True
        )

        # Create agent
        self.agent = GodAgent(
            gemini_api_key=self.gemini_api_key,
            groq_api_key=self.groq_api_key,
            llm_provider=self.llm_provider,
            capabilities=capabilities,
            console=self.console
        )

        # Start agent
        await self.agent.start()

        self.console.print("[bold green]✓ God Agent ready![/bold green]\n")

    def show_welcome(self):
        """Display welcome message."""
        welcome_text = """
# 🤖 God Agent - Ultimate AI Assistant

**Available Commands:**

**Chat & Dialog:**
- Just type to chat with AI
- `/voice` - Record voice input
- `/resume` - Load previous dialog
- `/clear` - Clear conversation
- `/compress` - Compress conversation history
- `/tokens` - Show token statistics

**RAG & Knowledge:**
- `/index <path>` - Index documents for RAG
- `/search <query>` - Search knowledge base

**Tasks:**
- `/tasks` - Manage scheduled tasks
- `/task create` - Create new task
- `/task list` - List all tasks

**Code Analysis:**
- `/analyze <file>` - Analyze code quality

**Deployment:**
- `/deploy` - Deploy application

**Settings:**
- `/model` - Change LLM model
- `/profile` - Manage user profile
- `/system` - View/change system instruction
- `/settings` - View/change generation settings

**System:**
- `/status` - Show system status
- `/tools` - List available MCP tools
- `/help` - Show this help
- `/exit` or `/quit` - Exit

**Current Settings:**
- Provider: {provider}

Type your message or command below:
        """.format(provider=self.agent.llm_provider_name if self.agent else self.llm_provider)

        md = Markdown(welcome_text)
        self.console.print(Panel(md, border_style="cyan", title="Welcome"))

    async def handle_command(self, command: str) -> bool:
        """Handle special commands.

        Args:
            command: Command string

        Returns:
            True if should exit, False otherwise
        """
        cmd = command.lower().strip()

        if cmd in ["/exit", "/quit"]:
            self.console.print("\n[bold cyan]Goodbye! 👋[/bold cyan]\n")
            return True

        elif cmd == "/help":
            self.show_welcome()

        elif cmd == "/status":
            self.agent.print_status()

        elif cmd == "/clear":
            self.conversation_history = []
            self.console.print("[green]✓ Conversation cleared[/green]")

        elif cmd == "/tools":
            tools = self.agent.list_available_tools()
            self.console.print(f"\n[bold]Available MCP Tools ({len(tools)}):[/bold]")
            for tool in tools:
                self.console.print(f"  • {tool}")
            self.console.print()

        elif cmd == "/voice":
            await self.handle_voice()

        elif cmd.startswith("/index "):
            path = command[7:].strip()
            await self.handle_index(path)

        elif cmd.startswith("/search "):
            query = command[8:].strip()
            await self.handle_search(query)

        elif cmd == "/tasks":
            await self.handle_tasks_menu()

        elif cmd == "/task list":
            await self.list_tasks()

        elif cmd == "/task create":
            await self.create_task()

        elif cmd.startswith("/analyze "):
            file_path = command[9:].strip()
            await self.analyze_file(file_path)

        elif cmd == "/analyze":
            self.console.print("[yellow]Usage: /analyze <file_path>[/yellow]")

        elif cmd == "/deploy":
            await self.handle_deploy()

        elif cmd == "/resume":
            await self.handle_resume()

        elif cmd == "/model":
            await self.handle_model()

        elif cmd == "/profile":
            await self.handle_profile()

        elif cmd == "/system":
            await self.handle_system()

        elif cmd == "/settings":
            await self.handle_settings()

        elif cmd == "/compress":
            await self.handle_compress()

        elif cmd == "/tokens":
            self.handle_tokens()

        else:
            self.console.print(f"[red]Unknown command: {command}[/red]")
            self.console.print("[dim]Type /help for available commands[/dim]")

        return False

    async def handle_voice(self):
        """Handle voice input."""
        try:
            self.console.print("[cyan]🎤 Recording (5 seconds)...[/cyan]")
            text = self.agent.record_voice(duration=5)

            if text:
                self.console.print(f"[green]Transcribed:[/green] {text}\n")
                # Process as regular message
                await self.process_message(text)
            else:
                self.console.print("[yellow]No text transcribed[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Voice error: {e}[/red]")

    async def handle_index(self, path: str):
        """Index documents for RAG."""
        try:
            path_obj = Path(path).expanduser()

            if not path_obj.exists():
                self.console.print(f"[red]Path not found: {path}[/red]")
                return

            self.console.print(f"[cyan]Indexing: {path}[/cyan]")

            if path_obj.is_file():
                with open(path_obj, 'r', encoding='utf-8') as f:
                    content = f.read()

                doc_id = await self.agent.index_document(
                    content,
                    metadata={'filename': path_obj.name, 'path': str(path_obj)}
                )
                self.console.print(f"[green]✓ Indexed: {doc_id}[/green]")

            elif path_obj.is_dir():
                count = 0
                for file_path in path_obj.rglob('*.txt'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    await self.agent.index_document(
                        content,
                        metadata={'filename': file_path.name, 'path': str(file_path)}
                    )
                    count += 1

                self.console.print(f"[green]✓ Indexed {count} files[/green]")

        except Exception as e:
            self.console.print(f"[red]Index error: {e}[/red]")

    async def handle_search(self, query: str):
        """Search knowledge base."""
        try:
            results = await self.agent.search_knowledge(query, top_k=5)

            if results:
                self.console.print(f"\n[bold]Search Results ({len(results)}):[/bold]\n")
                for i, result in enumerate(results, 1):
                    content = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
                    score = result.get('score', 0)
                    self.console.print(f"{i}. [dim](score: {score:.3f})[/dim]")
                    self.console.print(f"   {content}\n")
            else:
                self.console.print("[yellow]No results found[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Search error: {e}[/red]")

    async def handle_tasks_menu(self):
        """Show tasks management menu."""
        while True:
            self.console.print("\n[bold cyan]═══ Task Management ═══[/bold cyan]")
            self.console.print("1. List tasks")
            self.console.print("2. Create task")
            self.console.print("3. Run task now")
            self.console.print("4. Delete task")
            self.console.print("0. Back")

            choice = Prompt.ask("Select option", choices=["0", "1", "2", "3", "4"])

            if choice == "0":
                break
            elif choice == "1":
                await self.list_tasks()
            elif choice == "2":
                await self.create_task()
            elif choice == "3":
                task_id = int(Prompt.ask("Enter task ID"))
                await self.agent.run_task_now(task_id)
                self.console.print("[green]✓ Task triggered[/green]")
            elif choice == "4":
                task_id = int(Prompt.ask("Enter task ID"))
                self.agent.remove_task(task_id)
                self.console.print("[green]✓ Task deleted[/green]")

    async def list_tasks(self):
        """List all tasks."""
        tasks = self.agent.list_tasks()

        if not tasks:
            self.console.print("[yellow]No tasks found[/yellow]")
            return

        self.console.print(f"\n[bold]Tasks ({len(tasks)}):[/bold]\n")
        for task in tasks:
            status = "🟢" if task['enabled'] else "🔴"
            self.console.print(f"{status} [{task['id']}] {task['name']}")
            self.console.print(f"   Schedule: {task['schedule_type']} - {task['schedule_value']}")
            self.console.print(f"   Last run: {task.get('last_run', 'Never')}\n")

    async def create_task(self):
        """Create new task interactively."""
        self.console.print("\n[bold]Create New Task[/bold]\n")

        name = Prompt.ask("Task name")
        mcp_tool = Prompt.ask("MCP tool (e.g., crypto_get_price)")

        self.console.print("\nSchedule types: interval, daily, weekly")
        schedule_type = Prompt.ask("Schedule type", choices=["interval", "daily", "weekly"])

        if schedule_type == "interval":
            schedule_value = Prompt.ask("Interval (e.g., '5 minutes')")
        elif schedule_type == "daily":
            schedule_value = Prompt.ask("Time (e.g., '09:00')")
        else:  # weekly
            schedule_value = Prompt.ask("Day and time (e.g., 'Monday 09:00')")

        task_config = {
            'name': name,
            'mcp_tool': mcp_tool,
            'tool_args': {},
            'schedule_type': schedule_type,
            'schedule_value': schedule_value,
            'use_ai_summary': True,
            'notification_level': 'all',
            'enabled': True
        }

        task_id = self.agent.create_task(task_config)
        self.console.print(f"[green]✓ Task created with ID: {task_id}[/green]")

    async def analyze_file(self, file_path: str):
        """Analyze code file."""
        try:
            path_obj = Path(file_path).expanduser()

            if not path_obj.exists():
                self.console.print(f"[red]File not found: {file_path}[/red]")
                return

            with open(path_obj, 'r', encoding='utf-8') as f:
                code = f.read()

            self.console.print(f"[cyan]Analyzing: {path_obj.name}...[/cyan]\n")

            analysis = await self.agent.analyze_code(code, path_obj.name)

            # Display results
            score = analysis['quality_score']
            score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"

            self.console.print(f"[bold]Quality Score: [{score_color}]{score:.1f}/100[/{score_color}][/bold]\n")

            self.console.print("[bold]Metadata:[/bold]")
            self.console.print(f"  Language: {analysis['metadata']['language']}")
            self.console.print(f"  Lines: {analysis['metadata']['total_lines']} total, {analysis['metadata']['code_lines']} code")
            self.console.print(f"  Functions: {analysis['metadata']['functions']}")
            self.console.print(f"  Classes: {analysis['metadata']['classes']}\n")

            self.console.print("[bold]Static Analysis:[/bold]")
            self.console.print(f"  Complexity: {analysis['static_analysis']['complexity_score']}")
            self.console.print(f"  Issues: {len(analysis['static_analysis']['issues'])}")
            self.console.print(f"  Code Smells: {len(analysis['static_analysis']['code_smells'])}\n")

            if analysis['recommendations']:
                self.console.print("[bold]Recommendations:[/bold]")
                for rec in analysis['recommendations']:
                    self.console.print(f"  • {rec}")
                self.console.print()

            if analysis.get('ai_documentation'):
                self.console.print("[bold]AI Analysis:[/bold]")
                self.console.print(analysis['ai_documentation'])
                self.console.print()

        except Exception as e:
            self.console.print(f"[red]Analysis error: {e}[/red]")

    async def handle_deploy(self):
        """Handle deployment."""
        platform = Prompt.ask("Platform", choices=["railway", "docker"], default="railway")

        self.console.print(f"\n[cyan]Deploying to {platform}...[/cyan]\n")

        try:
            result = self.agent.deploy(platform=platform)

            # Show stages
            for stage in result['stages']:
                status_icon = {"success": "✓", "error": "✗", "pending": "○", "running": "▶"}.get(stage['status'], "?")
                color = {"success": "green", "error": "red", "pending": "dim", "running": "yellow"}.get(stage['status'], "white")

                self.console.print(f"[{color}]{status_icon} {stage['name']}: {stage['message']}[/{color}]")

            # Show validation issues if any
            if result.get('results', {}).get('validation_result'):
                validation = result['results']['validation_result']
                if hasattr(validation, 'issues') and validation.issues:
                    self.console.print("\n[bold yellow]Validation Issues:[/bold yellow]")
                    for i, issue in enumerate(validation.issues, 1):
                        severity = getattr(issue, 'severity', 'warning')
                        message = getattr(issue, 'message', str(issue))
                        self.console.print(f"  {i}. [{severity}] {message}")

                    # Show suggestions if available
                    if hasattr(validation, 'suggestions') and validation.suggestions:
                        self.console.print("\n[bold cyan]Suggestions:[/bold cyan]")
                        for suggestion in validation.suggestions:
                            self.console.print(f"  • {suggestion}")

            # Show build preparation errors if any
            if result.get('results', {}).get('build_result'):
                build = result['results']['build_result']
                if hasattr(build, 'success') and not build.success:
                    self.console.print("\n[bold red]Build Preparation Errors:[/bold red]")
                    if hasattr(build, 'error') and build.error:
                        self.console.print(f"  {build.error}")
                    if hasattr(build, 'errors') and build.errors:
                        for i, error in enumerate(build.errors, 1):
                            self.console.print(f"  {i}. {error}")

                # Show artifacts if successful
                elif hasattr(build, 'success') and build.success:
                    if hasattr(build, 'artifacts') and build.artifacts:
                        self.console.print(f"\n[bold green]Build Artifacts ({len(build.artifacts)}):[/bold green]")
                        for artifact in build.artifacts[:5]:  # Show first 5
                            self.console.print(f"  ✓ {artifact}")

            # Show deployment errors if any
            if result.get('results', {}).get('deployment_result'):
                deployment = result['results']['deployment_result']
                if hasattr(deployment, 'success') and not deployment.success:
                    self.console.print("\n[bold red]Deployment Errors:[/bold red]")
                    if hasattr(deployment, 'errors') and deployment.errors:
                        for i, error in enumerate(deployment.errors, 1):
                            self.console.print(f"  {i}. {error}")
                    # Also show logs for more context
                    if hasattr(deployment, 'logs') and deployment.logs:
                        self.console.print("\n[bold yellow]Deployment Logs:[/bold yellow]")
                        for log in deployment.logs[-10:]:  # Show last 10 logs
                            self.console.print(f"  {log}")

            # Show AI recommendations
            if result.get('results', {}).get('ai_recommendations'):
                from rich.markdown import Markdown
                self.console.print("\n[bold]AI Recommendations:[/bold]")
                # Parse and format recommendations properly
                recommendations = result['results']['ai_recommendations']
                if isinstance(recommendations, str):
                    # Use Rich Markdown for proper formatting
                    md = Markdown(recommendations)
                    self.console.print(md)
                else:
                    self.console.print(recommendations)

        except Exception as e:
            self.console.print(f"[red]Deployment error: {e}[/red]")

    async def handle_resume(self):
        """Load previous dialog."""
        self.console.print("[yellow]Resume feature: Load conversation history[/yellow]")
        # TODO: Implement dialog persistence and loading
        self.console.print("[dim]Note: Dialog persistence not yet implemented in God Agent[/dim]")

    async def handle_model(self):
        """Change LLM model."""
        self.console.print("\n" + "=" * 60, style="bright_cyan")
        self.console.print("     MODEL SELECTION", style="bold bright_cyan")
        self.console.print("=" * 60, style="bright_cyan")

        self.console.print(f"\n[bold]Current Provider:[/bold] {self.agent.llm_provider_name}")

        self.console.print("\n[bold]Available Providers:[/bold]")
        self.console.print("  1. Gemini (Cloud, fast, high quality)")
        self.console.print("  2. Ollama (Local, private, offline)")
        self.console.print("  0. Cancel")

        self.console.print("=" * 60, style="bright_cyan")

        choice = Prompt.ask("\nSelect option", choices=["0", "1", "2"], default="0")

        if choice == "0":
            return

        # Map choice to provider
        provider_map = {"1": "gemini", "2": "ollama"}
        new_provider = provider_map.get(choice)

        if new_provider:
            # Check if Ollama is available
            if new_provider == "ollama":
                import shutil
                if not shutil.which("ollama"):
                    self.console.print("\n[red]❌ Ollama not found![/red]")
                    self.console.print("[yellow]Install instructions:[/yellow]")
                    self.console.print("  1. Visit: https://ollama.ai")
                    self.console.print("  2. Install Ollama")
                    self.console.print("  3. Run: ollama pull qwen2.5-coder:7b-instruct")
                    return

            # Switch provider
            self.console.print(f"\n[cyan]Switching to {new_provider}...[/cyan]")
            success = self.agent.switch_llm_provider(new_provider)

            if success:
                self.console.print(f"\n[green]✓ Successfully switched to {self.agent.llm_provider_name}![/green]")
                self.console.print("[dim]You can continue chatting with the new provider[/dim]")
            else:
                self.console.print("\n[red]Failed to switch provider[/red]")

    async def handle_profile(self):
        """Manage user profile."""
        self.console.print("\n" + "=" * 60, style="bright_cyan")
        self.console.print("     USER PROFILE MANAGEMENT", style="bold bright_cyan")
        self.console.print("=" * 60, style="bright_cyan")

        profile = self.agent.profile_manager.get_user_profile()

        self.console.print("\n[bold]Current Profile:[/bold]")
        self.console.print(f"  • Name: {profile.get('name', 'User')}")
        self.console.print(f"  • Role: {profile.get('role', 'N/A')}")
        self.console.print(f"  • Communication Style: {profile.get('communication_style', 'casual')}")

        prefs = profile.get('preferences', {})
        if prefs:
            self.console.print("\n[bold]Preferences:[/bold]")
            for key, value in prefs.items():
                self.console.print(f"  • {key}: {value}")

        interests = profile.get('interests', [])
        if interests:
            self.console.print(f"\n[bold]Interests:[/bold] {', '.join(interests)}")

        self.console.print("\n" + "=" * 60, style="bright_cyan")
        self.console.print("[bold]Available Actions:[/bold]")
        self.console.print("  1. Change name")
        self.console.print("  2. Change role")
        self.console.print("  3. Change communication style")
        self.console.print("  4. Add interest")
        self.console.print("  5. Remove interest")
        self.console.print("  0. Back")
        self.console.print("=" * 60, style="bright_cyan")

        choice = Prompt.ask("\nSelect option", choices=["0", "1", "2", "3", "4", "5"], default="0")

        if choice == "1":
            name = Prompt.ask("Enter name")
            self.agent.profile_manager.update_profile_field('name', name)
            self.console.print("[green]✓ Name updated[/green]")

        elif choice == "2":
            role = Prompt.ask("Enter role")
            self.agent.profile_manager.update_profile_field('role', role)
            self.console.print("[green]✓ Role updated[/green]")

        elif choice == "3":
            self.console.print("\n[bold]Communication Styles:[/bold]")
            self.console.print("  1. Casual")
            self.console.print("  2. Professional")
            self.console.print("  3. Friendly")
            style_choice = Prompt.ask("Select style", choices=["1", "2", "3"])
            styles = {"1": "casual", "2": "professional", "3": "friendly"}
            self.agent.profile_manager.update_profile_field('communication_style', styles[style_choice])
            self.console.print("[green]✓ Style updated[/green]")

        elif choice == "4":
            interest = Prompt.ask("Enter interest to add")
            self.agent.profile_manager.add_interest(interest)
            self.console.print("[green]✓ Interest added[/green]")

        elif choice == "5":
            if interests:
                self.console.print("\n[bold]Current Interests:[/bold]")
                for i, interest in enumerate(interests, 1):
                    self.console.print(f"  {i}. {interest}")
                interest = Prompt.ask("Enter interest to remove")
                self.agent.profile_manager.remove_interest(interest)
                self.console.print("[green]✓ Interest removed[/green]")
            else:
                self.console.print("[yellow]No interests to remove[/yellow]")

    async def handle_system(self):
        """View/change system instruction."""
        self.console.print("\n[bold]Current System Instruction:[/bold]\n")

        instruction = self.agent.profile_manager.get_system_instruction()
        self.console.print(Panel(instruction, border_style="cyan"))

        if Prompt.ask("\nChange system instruction?", choices=["y", "n"], default="n") == "y":
            new_instruction = Prompt.ask("Enter new instruction")
            self.agent.profile_manager.update_system_instruction(new_instruction)
            self.console.print("[green]✓ System instruction updated[/green]")

    async def handle_settings(self):
        """View/change generation settings."""
        self.console.print("\n" + "=" * 60, style="bright_cyan")
        self.console.print("     GENERATION SETTINGS", style="bold bright_cyan")
        self.console.print("=" * 60, style="bright_cyan")

        settings = self.agent.profile_manager.get_generation_settings()

        self.console.print("\n[bold]Current Settings:[/bold]")
        self.console.print(f"  • Temperature: {settings.get('temperature', 0.7)} (0.0-2.0, creativity)")
        self.console.print(f"  • Top K: {settings.get('top_k', 40)} (token selection)")
        self.console.print(f"  • Top P: {settings.get('top_p', 0.95)} (0.0-1.0, nucleus sampling)")
        self.console.print(f"  • Max Tokens: {settings.get('max_output_tokens', 2048)} (response length)")

        self.console.print("\n" + "=" * 60, style="bright_cyan")
        self.console.print("[bold]Available Actions:[/bold]")
        self.console.print("  1. Change temperature")
        self.console.print("  2. Change top_k")
        self.console.print("  3. Change top_p")
        self.console.print("  4. Change max_output_tokens")
        self.console.print("  0. Back")
        self.console.print("=" * 60, style="bright_cyan")

        choice = Prompt.ask("\nSelect option", choices=["0", "1", "2", "3", "4"], default="0")

        if choice == "0":
            return

        setting_names = {
            "1": ("temperature", float, "0.0-2.0"),
            "2": ("top_k", int, "1-100"),
            "3": ("top_p", float, "0.0-1.0"),
            "4": ("max_output_tokens", int, "256-8192")
        }

        if choice in setting_names:
            name, type_func, range_hint = setting_names[choice]
            value = Prompt.ask(f"Enter {name} ({range_hint})")
            try:
                value = type_func(value)
                self.agent.profile_manager.update_generation_setting(name, value)
                self.console.print(f"[green]✓ {name} updated to {value}[/green]")
            except ValueError:
                self.console.print("[red]Invalid value - must be a number[/red]")

    async def handle_compress(self):
        """Compress conversation history."""
        if not self.conversation_history:
            self.console.print("[yellow]No conversation to compress[/yellow]")
            return

        original_count = len(self.conversation_history)
        self.console.print(f"[cyan]Compressing {original_count} messages...[/cyan]")

        # Simple compression: keep only last 10 messages
        if original_count > 10:
            self.conversation_history = self.conversation_history[-10:]
            self.console.print(f"[green]✓ Compressed to {len(self.conversation_history)} messages[/green]")
        else:
            self.console.print("[yellow]History already short enough[/yellow]")

    def handle_tokens(self):
        """Show token statistics."""
        self.console.print("\n[bold cyan]═══ Token Statistics ═══[/bold cyan]\n")

        total_messages = len(self.conversation_history)

        # Rough estimate: ~4 chars per token
        # Extract text from Gemini API format: {'role': 'user', 'parts': [{'text': '...'}]}
        total_chars = 0
        for msg in self.conversation_history:
            parts = msg.get('parts', [])
            if parts and isinstance(parts, list):
                text = parts[0].get('text', '')
                total_chars += len(str(text))

        estimated_tokens = total_chars // 4

        self.console.print(f"[bold]Messages:[/bold] {total_messages}")
        self.console.print(f"[bold]Total Characters:[/bold] {total_chars:,}")
        self.console.print(f"[bold]Estimated Tokens:[/bold] {estimated_tokens:,}")
        self.console.print("\n[dim]Note: Token counts are estimates (4 chars ≈ 1 token)[/dim]")

    async def process_message(self, message: str):
        """Process user message."""
        try:
            # Add to history (Gemini API format)
            self.conversation_history.append({
                'role': 'user',
                'parts': [{'text': message}]
            })

            # Get response
            self.console.print("[dim]Thinking...[/dim]")
            response = await self.agent.chat(
                message=message,
                conversation_history=self.conversation_history[:-1],  # Exclude current message
                use_rag=True,
                temperature=0.7
            )

            # Add to history (Gemini API format)
            self.conversation_history.append({
                'role': 'model',
                'parts': [{'text': response}]
            })

            # Display response
            self.console.print("\n[bold green]AI:[/bold green]\n")
            md = Markdown(response)
            self.console.print(md)
            self.console.print()

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            import traceback
            traceback.print_exc()

    async def chat_loop(self):
        """Main chat loop."""
        while True:
            try:
                # Get input with encoding error handling
                try:
                    user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()
                except UnicodeDecodeError:
                    self.console.print("[red]Error: Invalid character encoding. Please use UTF-8.[/red]")
                    self.console.print("[dim]Tip: Check your terminal encoding settings[/dim]")
                    continue

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    should_exit = await self.handle_command(user_input)
                    if should_exit:
                        break
                    continue

                # Process message
                await self.process_message(user_input)

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Interrupted. Type /exit to quit.[/yellow]")
                continue
            except EOFError:
                break
            except UnicodeDecodeError:
                self.console.print("[red]Error: Unicode decode error. Please check your terminal encoding.[/red]")
                continue
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                import traceback
                traceback.print_exc()

    async def run(self):
        """Run the CLI."""
        try:
            await self.initialize()
            self.show_welcome()
            await self.chat_loop()
        finally:
            # Cleanup
            if self.agent:
                try:
                    await self.agent.stop()
                except Exception:
                    # Ignore cleanup errors
                    pass


async def main():
    """Main entry point."""
    cli = GodAgentCLI()
    try:
        await cli.run()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        # Run with custom exception handler to suppress MCP cleanup errors
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_exception_handler(suppress_mcp_cleanup_errors)

        try:
            loop.run_until_complete(main())
        finally:
            # Suppress errors during cleanup
            import io
            old_stderr = sys.stderr
            try:
                # Redirect stderr to suppress MCP cleanup traceback
                sys.stderr = io.StringIO()
                try:
                    loop.run_until_complete(loop.shutdown_asyncgens())
                except Exception:
                    pass
                loop.close()
            finally:
                sys.stderr = old_stderr
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception:
        pass
