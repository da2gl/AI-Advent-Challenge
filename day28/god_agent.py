"""
God Agent - Ultimate AI Assistant
Combines all features from previous days into one comprehensive system
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

# Core components
from core.gemini_client import GeminiApiClient, GeminiModel
from core.ollama_client import OllamaApiClient
from core.storage import SQLiteStorage
from mcp_integration.manager import MCPManager

# RAG components
from managers.rag_manager import RagManager
from managers.index_manager import IndexManager

# Task management
from tasks.scheduler_apscheduler import APTaskScheduler
from tasks.storage import TaskStorage
from notifications.macos import MacOSNotifier

# Code analysis
from pipeline.code_analyzer import MetadataExtractor, StaticAnalyzer, QualityAssessor

# Deployment
from pipeline.deploy_pipeline import DeploymentPipeline

# Voice input
from managers.speech_manager import SpeechManager

# User profile
from core.user_profile import UserProfile


@dataclass
class AgentCapabilities:
    """Agent capabilities configuration"""
    llm_enabled: bool = True
    rag_enabled: bool = True
    mcp_enabled: bool = True
    voice_enabled: bool = True
    tasks_enabled: bool = True
    code_analysis_enabled: bool = True
    deployment_enabled: bool = True
    notifications_enabled: bool = True


@dataclass
class AgentState:
    """Current state of the God Agent"""
    active_modules: List[str] = field(default_factory=list)
    task_count: int = 0
    conversation_count: int = 0
    uptime_seconds: float = 0
    last_activity: Optional[datetime] = None


class GodAgent:
    """
    God Agent - Ultimate AI Personal Assistant

    Combines all capabilities:
    - Multi-provider LLM (Gemini + Ollama)
    - RAG with semantic reranking
    - MCP tool integration (file ops, testing)
    - Background task scheduling
    - Code analysis and quality assessment
    - Deployment automation
    - Voice input
    - User personalization
    - Notifications
    """

    def __init__(
        self,
        gemini_api_key: str,
        groq_api_key: Optional[str] = None,
        llm_provider: str = "gemini",
        capabilities: Optional[AgentCapabilities] = None,
        console=None
    ):
        """
        Initialize God Agent

        Args:
            gemini_api_key: Google AI API key
            groq_api_key: Groq API key (for voice)
            llm_provider: LLM provider to use ('gemini' or 'ollama')
            capabilities: Agent capabilities configuration
            console: Rich console for output
        """
        self.console = console
        self.capabilities = capabilities or AgentCapabilities()
        self.state = AgentState()
        self.start_time = datetime.now()

        # Store API keys for runtime provider switching
        self.gemini_api_key = gemini_api_key
        self.groq_api_key = groq_api_key

        # Initialize storage
        self.storage = SQLiteStorage("data/god_agent.db")

        # Initialize LLM provider
        if self.capabilities.llm_enabled:
            if llm_provider == "gemini":
                self.llm_client = GeminiApiClient(gemini_api_key)
                self.llm_provider_name = "Gemini"
                self.state.active_modules.append("LLM: Gemini")
            else:
                self.llm_client = OllamaApiClient()
                self.llm_provider_name = "Ollama"
                self.state.active_modules.append("LLM: Ollama")
        else:
            self.llm_client = None

        # Initialize RAG
        if self.capabilities.rag_enabled and gemini_api_key:
            self.index_manager = IndexManager(
                console=console,
                api_key=gemini_api_key,
                persist_directory="data/chroma_db"
            )
            self.index_manager._init_pipeline()

            # Get or create Gemini client for RAG (reranking requires Gemini)
            if llm_provider == "gemini" and self.llm_client:
                gemini_client = self.llm_client
            else:
                gemini_client = GeminiApiClient(gemini_api_key)

            self.rag_manager = RagManager(
                console=console,
                gemini_client=gemini_client,
                indexing_pipeline=self.index_manager.indexing_pipeline
            )
            self.state.active_modules.append("RAG")
        else:
            self.index_manager = None
            self.rag_manager = None

        # Initialize MCP
        if self.capabilities.mcp_enabled:
            self.mcp_manager = MCPManager()
            self.state.active_modules.append("MCP Tools")
        else:
            self.mcp_manager = None

        # Initialize voice input
        if self.capabilities.voice_enabled and groq_api_key:
            try:
                self.audio_manager = SpeechManager(groq_api_key, console=console)
                self.state.active_modules.append("Voice Input")
            except Exception:
                self.audio_manager = None
        else:
            self.audio_manager = None

        # Initialize user profile
        self.profile_manager = UserProfile()
        self.state.active_modules.append("User Profile")

        # Initialize notifications
        if self.capabilities.notifications_enabled:
            self.notifier = MacOSNotifier(enabled=True)
            self.state.active_modules.append("Notifications")
        else:
            self.notifier = None

        # Initialize task scheduler
        if self.capabilities.tasks_enabled:
            self.task_storage = TaskStorage("data/god_agent_tasks.db")
            self.task_scheduler = APTaskScheduler(
                storage=self.task_storage,
                mcp_manager=self.mcp_manager,
                gemini_client=self.llm_client if llm_provider == "gemini" else None,
                console=console,
                notifier=self.notifier
            )
            self.state.active_modules.append("Task Scheduler")
        else:
            self.task_scheduler = None
            self.task_storage = None

        # Initialize code analyzer
        if self.capabilities.code_analysis_enabled:
            self.metadata_extractor = MetadataExtractor()
            self.static_analyzer = StaticAnalyzer()
            self.quality_assessor = QualityAssessor()
            self.state.active_modules.append("Code Analysis")
        else:
            self.metadata_extractor = None
            self.static_analyzer = None
            self.quality_assessor = None

        # Initialize deployment pipeline
        if self.capabilities.deployment_enabled:
            self.deployment_pipeline = DeploymentPipeline(
                gemini_client=self.llm_client if llm_provider == "gemini" else None
            )
            self.state.active_modules.append("Deployment")
        else:
            self.deployment_pipeline = None

        self._log_initialization()

    def _log_initialization(self):
        """Log successful initialization"""
        if self.console:
            self.console.print("\n[bold green]═══════════════════════════════════════════════════════════[/bold green]")
            self.console.print("[bold cyan]           🤖 GOD AGENT INITIALIZED 🤖                    [/bold cyan]")
            self.console.print("[bold green]═══════════════════════════════════════════════════════════[/bold green]\n")
            self.console.print(f"[yellow]LLM Provider:[/yellow] {self.llm_provider_name}")
            self.console.print(f"[yellow]Active Modules:[/yellow] {len(self.state.active_modules)}")
            for module in self.state.active_modules:
                self.console.print(f"  ✓ {module}")
            self.console.print()

    async def start(self):
        """Start all async components"""
        # Start task scheduler
        if self.task_scheduler:
            self.task_scheduler.start()

        # Connect MCP clients (non-critical, may fail in Docker/restricted environments)
        if self.mcp_manager:
            try:
                await self.mcp_manager.connect_all()
            except (FileNotFoundError, RuntimeError, Exception) as e:
                # MCP connection is optional - log but don't fail
                if self.console:
                    self.console.print(f"[yellow]Warning: MCP connection failed: {e}[/yellow]")
                    self.console.print("[dim]MCP features will be unavailable[/dim]")

        # RAG is already initialized in __init__
        self.state.last_activity = datetime.now()

    async def stop(self):
        """Stop all async components"""
        # Stop task scheduler
        if self.task_scheduler:
            self.task_scheduler.stop()

        # Disconnect MCP clients (ignore shutdown errors)
        if self.mcp_manager:
            try:
                await self.mcp_manager.disconnect_all()
            except (RuntimeError, Exception):
                # Ignore errors during shutdown (common with MCP clients)
                pass

        if self.console:
            self.console.print("\n[yellow]God Agent stopped[/yellow]")

    # ═══════════════════════════════════════════════════════════
    # CORE CHAT FUNCTIONALITY
    # ═══════════════════════════════════════════════════════════

    async def chat(
        self,
        message: str,
        conversation_history: Optional[List[Dict]] = None,
        use_rag: bool = True,
        temperature: float = 0.7
    ) -> str:
        """
        Process a chat message

        Args:
            message: User message
            conversation_history: Previous conversation
            use_rag: Whether to use RAG for context
            temperature: LLM temperature

        Returns:
            Assistant response
        """
        self.state.last_activity = datetime.now()
        self.state.conversation_count += 1

        # Retrieve context from RAG if enabled
        context = None
        if use_rag and self.rag_manager:
            results = self.rag_manager.search_context(query=message, top_k=3)
            if results:
                context = self.rag_manager.format_context_for_prompt(results)

        # Build system instruction with user profile
        system_instruction = self.profile_manager.get_system_instruction()

        # Add RAG context if available
        if context:
            system_instruction += f"\n\nRelevant context from knowledge base:\n{context}"

        # Generate response
        if self.llm_provider_name == "Gemini":
            response = self.llm_client.generate_content(
                prompt=message,
                model=GeminiModel.GEMINI_2_5_FLASH,
                system_instruction=system_instruction,
                conversation_history=conversation_history,
                temperature=temperature,
                max_output_tokens=4096
            )
            return self.llm_client.extract_text(response)
        else:
            # Ollama - uses same interface as Gemini
            from core.ollama_client import OllamaModel
            response = self.llm_client.generate_content(
                prompt=message,
                model=OllamaModel.QWEN_CODER,
                system_instruction=system_instruction,
                conversation_history=conversation_history,
                temperature=temperature,
                max_output_tokens=4096
            )
            return self.llm_client.extract_text(response)

    def switch_llm_provider(self, new_provider: str) -> bool:
        """
        Switch LLM provider at runtime

        Args:
            new_provider: 'gemini' or 'ollama'

        Returns:
            True if switched successfully, False otherwise
        """
        if not self.capabilities.llm_enabled:
            return False

        if new_provider == self.llm_provider_name.lower():
            if self.console:
                self.console.print(f"[yellow]Already using {self.llm_provider_name}[/yellow]")
            return False

        try:
            # Remove old provider from active modules
            old_module = f"LLM: {self.llm_provider_name}"
            if old_module in self.state.active_modules:
                self.state.active_modules.remove(old_module)

            # Switch provider
            if new_provider == "gemini":
                if not self.gemini_api_key:
                    if self.console:
                        self.console.print("[red]Error: Gemini API key not available[/red]")
                    return False
                self.llm_client = GeminiApiClient(self.gemini_api_key)
                self.llm_provider_name = "Gemini"
                self.state.active_modules.append("LLM: Gemini")

                # Update RAG reranker if using Gemini
                if self.rag_manager and hasattr(self.rag_manager, 'rag_client'):
                    if hasattr(self.rag_manager.rag_client, 'reranker'):
                        from rag.reranker import Reranker
                        self.rag_manager.rag_client.reranker = Reranker(gemini_client=self.llm_client)

            elif new_provider == "ollama":
                self.llm_client = OllamaApiClient()
                self.llm_provider_name = "Ollama"
                self.state.active_modules.append("LLM: Ollama")

                # Disable Gemini reranker for Ollama
                if self.rag_manager and hasattr(self.rag_manager, 'rag_client'):
                    if hasattr(self.rag_manager.rag_client, 'reranker'):
                        self.rag_manager.rag_client.reranker = None
            else:
                if self.console:
                    self.console.print(f"[red]Unknown provider: {new_provider}[/red]")
                return False

            if self.console:
                self.console.print(f"[green]✓ Switched to {self.llm_provider_name}[/green]")

            return True

        except Exception as e:
            if self.console:
                self.console.print(f"[red]Error switching provider: {e}[/red]")
            return False

    # ═══════════════════════════════════════════════════════════
    # TASK MANAGEMENT
    # ═══════════════════════════════════════════════════════════

    def create_task(self, task_config: Dict) -> int:
        """Create a new scheduled task"""
        if not self.task_scheduler:
            raise RuntimeError("Task scheduler not enabled")
        return self.task_scheduler.add_task(task_config)

    def list_tasks(self) -> List[Dict]:
        """List all tasks"""
        if not self.task_storage:
            return []
        return self.task_storage.get_all_tasks()

    def get_task_history(self, task_id: int, limit: int = 10) -> List[Dict]:
        """Get task execution history"""
        if not self.task_storage:
            return []
        return self.task_storage.get_task_history(task_id, limit=limit)

    async def run_task_now(self, task_id: int):
        """Run a task immediately"""
        if not self.task_scheduler:
            raise RuntimeError("Task scheduler not enabled")
        await self.task_scheduler.run_task_now(task_id)

    def remove_task(self, task_id: int):
        """Remove a task"""
        if not self.task_scheduler:
            raise RuntimeError("Task scheduler not enabled")
        self.task_scheduler.remove_task(task_id)

    # ═══════════════════════════════════════════════════════════
    # CODE ANALYSIS
    # ═══════════════════════════════════════════════════════════

    async def analyze_code(self, code: str, file_path: str) -> Dict[str, Any]:
        """
        Analyze code quality and generate recommendations

        Args:
            code: Source code to analyze
            file_path: File path (for language detection)

        Returns:
            Analysis results with quality score and recommendations
        """
        if not self.capabilities.code_analysis_enabled:
            raise RuntimeError("Code analysis not enabled")

        # Extract metadata
        metadata = self.metadata_extractor.extract(code, file_path)

        # Static analysis
        static_analysis = self.static_analyzer.analyze(code, metadata)

        # Quality assessment
        quality_score, recommendations = self.quality_assessor.assess(metadata, static_analysis)

        # Generate AI documentation if Gemini available
        ai_documentation = ""
        if self.llm_provider_name == "Gemini":
            prompt = f"""Analyze this {metadata.language} code and provide:
1. Brief overview of what it does
2. Key design patterns used
3. Main strengths
4. Main weaknesses

Code:
{code[:2000]}  # Limit for context

Provide concise analysis in 4-5 sentences."""

            response = self.llm_client.generate_content(
                prompt=prompt,
                model=GeminiModel.GEMINI_2_5_FLASH,
                temperature=0.5,
                max_output_tokens=1024
            )
            ai_documentation = self.llm_client.extract_text(response)

        return {
            'metadata': {
                'language': metadata.language,
                'total_lines': metadata.total_lines,
                'code_lines': metadata.code_lines,
                'comment_lines': metadata.comment_lines,
                'functions': len(metadata.functions),
                'classes': len(metadata.classes)
            },
            'static_analysis': {
                'complexity_score': static_analysis.complexity_score,
                'issues': static_analysis.issues,
                'code_smells': static_analysis.code_smells
            },
            'quality_score': quality_score,
            'recommendations': recommendations,
            'ai_documentation': ai_documentation
        }

    # ═══════════════════════════════════════════════════════════
    # DEPLOYMENT
    # ═══════════════════════════════════════════════════════════

    def deploy(self, platform: str = 'railway') -> Dict:
        """
        Deploy application to cloud platform

        Args:
            platform: Target platform ('railway' or 'docker')

        Returns:
            Deployment result with stages and recommendations
        """
        if not self.deployment_pipeline:
            raise RuntimeError("Deployment not enabled")

        return self.deployment_pipeline.deploy(platform=platform)

    # ═══════════════════════════════════════════════════════════
    # VOICE INPUT
    # ═══════════════════════════════════════════════════════════

    def record_voice(self, duration: int = 5) -> Optional[str]:
        """
        Record voice input and transcribe

        Args:
            duration: Recording duration in seconds (currently ignored - uses default)

        Returns:
            Transcribed text or None
        """
        if not self.audio_manager:
            raise RuntimeError("Voice input not enabled")

        # Note: SpeechManager.record_and_transcribe() doesn't accept duration parameter
        # Uses default 5 seconds from SpeechManager
        return self.audio_manager.record_and_transcribe()

    # ═══════════════════════════════════════════════════════════
    # RAG MANAGEMENT
    # ═══════════════════════════════════════════════════════════

    async def index_document(self, content: str, metadata: Optional[Dict] = None) -> str:
        """Index a document in RAG"""
        if not self.index_manager:
            raise RuntimeError("RAG not enabled")

        # Create temporary file for indexing
        import tempfile
        doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        _filename = metadata.get('filename', f'{doc_id}.txt') if metadata else f'{doc_id}.txt'  # noqa: F841

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            # Index the file
            result = self.index_manager.indexing_pipeline.index_path(
                path=temp_path,
                collection_name='default',
                show_progress=False
            )
            return doc_id if result.success else None
        finally:
            # Clean up temp file
            import os
            os.unlink(temp_path)

    async def search_knowledge(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search knowledge base"""
        if not self.rag_manager:
            return []

        results = self.rag_manager.search_context(query=query, top_k=top_k)

        # Convert SearchResult objects to dicts for compatibility
        return [
            {
                'content': r.text if hasattr(r, 'text') else str(r),
                'score': r.rerank_score if hasattr(r, 'rerank_score') else 0,
                'source': r.source if hasattr(r, 'source') else ''
            }
            for r in results
        ]

    # ═══════════════════════════════════════════════════════════
    # MCP TOOLS
    # ═══════════════════════════════════════════════════════════

    async def call_tool(self, tool_name: str, arguments: Dict) -> Any:
        """Call an MCP tool"""
        if not self.mcp_manager:
            raise RuntimeError("MCP not enabled")

        return await self.mcp_manager.call_tool(tool_name, arguments)

    def list_available_tools(self) -> List[str]:
        """List all available MCP tools"""
        if not self.mcp_manager:
            return []

        return self.mcp_manager.list_available_tools()

    # ═══════════════════════════════════════════════════════════
    # STATUS & MONITORING
    # ═══════════════════════════════════════════════════════════

    def get_status(self) -> Dict:
        """Get current agent status"""
        uptime = (datetime.now() - self.start_time).total_seconds()

        status = {
            'uptime_seconds': uptime,
            'active_modules': self.state.active_modules,
            'conversation_count': self.state.conversation_count,
            'last_activity': self.state.last_activity.isoformat() if self.state.last_activity else None,
            'llm_provider': self.llm_provider_name
        }

        # Add task scheduler stats
        if self.task_scheduler:
            status['task_scheduler'] = self.task_scheduler.get_stats()

        # Add RAG stats
        if self.index_manager and self.index_manager.indexing_pipeline:
            collections = self.index_manager.indexing_pipeline.list_collections()
            status['rag'] = {'collections': collections}

        return status

    def print_status(self):
        """Print formatted status"""
        if not self.console:
            return

        status = self.get_status()

        self.console.print("\n[bold cyan]═══ God Agent Status ═══[/bold cyan]")
        self.console.print(f"[yellow]Uptime:[/yellow] {status['uptime_seconds']:.0f}s")
        self.console.print(f"[yellow]LLM Provider:[/yellow] {status['llm_provider']}")
        self.console.print(f"[yellow]Conversations:[/yellow] {status['conversation_count']}")
        self.console.print(f"[yellow]Active Modules:[/yellow] {len(status['active_modules'])}")

        if 'task_scheduler' in status:
            ts = status['task_scheduler']
            self.console.print("\n[cyan]Task Scheduler:[/cyan]")
            self.console.print(f"  Active Jobs: {ts['active_jobs']}")
            self.console.print(f"  Tasks Executed: {ts['tasks_executed']}")
            self.console.print(f"  Tasks Failed: {ts['tasks_failed']}")

        self.console.print()
