"""RAG (Retrieval-Augmented Generation) manager."""

from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live
from core.gemini_client import GeminiApiClient
from pipeline.pipeline_executor import IndexingPipeline
from pipeline.ollama_embedding_generator import OllamaEmbeddingGenerator
from rag.koog_loader import KoogLoader
from rag.rag_client import RagClient
from rag.reranker import Reranker


class RagManager:
    """Manages RAG operations - loading, searching, and context formatting."""

    def __init__(
        self,
        console: Console,
        gemini_client: GeminiApiClient,
        indexing_pipeline: IndexingPipeline
    ):
        """
        Initialize RAG manager.

        Args:
            console: Rich console for output
            gemini_client: Gemini API client for reranking
            indexing_pipeline: Indexing pipeline for document management
        """
        self.console = console
        self.gemini_client = gemini_client
        self.indexing_pipeline = indexing_pipeline
        self.koog_loader = None
        self.rag_client = None

    def load_koog(self, force: bool = False):
        """Load Koog documentation and index it with Ollama embeddings.

        Args:
            force: If True, force reindex even if collection exists
        """
        # Initialize Koog loader
        if self.koog_loader is None:
            self.koog_loader = KoogLoader()

        # Check if koog collection already exists
        try:
            existing_collections = self.indexing_pipeline.list_collections()
            koog_exists = any(col.name == "koog" for col in existing_collections)

            if koog_exists and not force:
                # Collection exists and no force flag - use existing
                self.console.print("\n✓ Koog collection already loaded from cache", style="green bold")
                self.console.print("💡 Use /load-koog --force to reindex from scratch", style="yellow")
                self.console.print("💡 Try: /koog-info to see available documents", style="bright_yellow")
                self.console.print("💡 Just type your questions - RAG is automatic!", style="bright_yellow")
                return
            elif koog_exists and force:
                # Collection exists but force flag - delete and reindex
                self.console.print("⚠️  Force flag detected. Deleting existing collection...", style="yellow")
                self.indexing_pipeline.delete_collection("koog")
                self.console.print("✓ Old collection deleted", style="green")
        except Exception:
            pass  # Collection doesn't exist, continue

        # Load Koog documentation
        self.console.print("\n📚 Loading Koog documentation...", style="bright_cyan bold")
        self.console.print("=" * 70, style="bright_cyan")

        try:
            # Stage 1: Load documentation
            spinner = Spinner("dots", text="[Stage 1] Loading Koog docs...", style="yellow")
            with Live(spinner, console=self.console, transient=True):
                documents = self.koog_loader.load(pattern="**/*.md")

            if not documents:
                self.console.print("✗ No documentation files found", style="red")
                return

            self.console.print(f"[Stage 1] ✓ Loaded {len(documents)} documents", style="green")

            stats = self.koog_loader.get_stats()
            self.console.print(f"[Stage 1] ✓ {stats['total_size_kb']:.1f} KB of documentation", style="green")

            # Initialize Ollama embedding generator
            self.console.print("\n🔧 Initializing Ollama embeddings...", style="yellow")
            ollama_gen = OllamaEmbeddingGenerator(
                base_url="http://localhost:11434",
                model="mxbai-embed-large",
                batch_size=50
            )

            # Test connection
            if not ollama_gen.test_connection():
                self.console.print("\n✗ Ollama connection failed", style="red bold")
                self.console.print("💡 Make sure Ollama is running:", style="yellow")
                self.console.print("   1. Start: ollama serve", style="dim")
                self.console.print("   2. Pull model: ollama pull mxbai-embed-large", style="dim")
                return

            self.console.print("✓ Ollama connected (mxbai-embed-large ready)", style="green")

            # Create temporary Document objects from Koog docs
            from pipeline.document_loader import Document

            temp_documents = []
            for doc in documents:
                temp_doc = Document(
                    content=doc.content,
                    source=doc.relative_path,
                    file_type="md",
                    size=doc.size_bytes,
                    created_at=datetime.now().isoformat()
                )
                temp_documents.append(temp_doc)

            # Stage 2: Chunk
            self.console.print("\n[Stage 2] Chunking documents...", style="yellow")
            chunks = self.indexing_pipeline.chunker.chunk_multiple_documents(temp_documents)
            self.console.print(f"[Stage 2] ✓ {len(chunks)} chunks created", style="green")

            # Stage 3: Generate embeddings with Ollama
            self.console.print("\n[Stage 3] Generating embeddings with Ollama...", style="yellow")
            embeddings = ollama_gen.generate_embeddings_for_chunks(chunks, show_progress=True)

            validation = ollama_gen.validate_embeddings(embeddings)
            self.console.print(f"[Stage 3] ✓ {validation['valid']} embeddings generated ({validation['success_rate']:.1f}% success)", style="green")

            if validation['valid'] == 0:
                self.console.print("✗ All embeddings failed", style="red")
                return

            # Stage 4: Index to ChromaDB
            self.console.print("\n[Stage 4] Indexing to ChromaDB...", style="yellow")
            self.indexing_pipeline.index_manager.add_documents(
                collection_name="koog",
                chunks=chunks,
                embeddings=embeddings,
                collection_metadata={
                    "source": "koog_documentation",
                    "type": "docs",
                    "embedding_model": "mxbai-embed-large"
                }
            )
            self.console.print("[Stage 4] ✓ Collection 'koog' ready", style="green")

            self.console.print("\n" + "=" * 70, style="bright_cyan")
            self.console.print("✓ Koog documentation loaded and indexed!", style="green bold")
            self.console.print(f"  Documents: {len(documents)}", style="dim")
            self.console.print(f"  Chunks: {len(chunks)}", style="dim")
            self.console.print("  Embeddings: 1024d (Ollama)", style="dim")
            self.console.print("\n💡 Try: /koog-info to see documentation details", style="bright_yellow")
            self.console.print("💡 Just type your questions - RAG search is automatic!", style="bright_yellow")

            ollama_gen.close()

        except Exception as e:
            self.console.print(f"\n✗ Error loading Koog: {str(e)}", style="red")
            import traceback
            traceback.print_exc()

    def show_koog_info(self):
        """Show info about loaded Koog documentation."""
        if self.koog_loader is None:
            self.koog_loader = KoogLoader()

        if not self.koog_loader.documents:
            self.console.print("\n✗ No Koog documentation loaded", style="red")
            self.console.print("💡 Use /load-koog to load the documentation first", style="yellow")
            return

        self.console.print("\n📚 Koog Documentation Information", style="bright_cyan bold")
        self.console.print("=" * 70, style="bright_cyan")

        # Summary
        stats = self.koog_loader.get_stats()
        self.console.print(f"\nTotal documents loaded: {stats['total_docs']}", style="green")
        self.console.print(f"Total size: {stats['total_size_kb']:.1f} KB", style="green")
        self.console.print(f"Topics: {', '.join(stats['topics'])}", style="green")

        # Show last 10 documents
        last_10 = self.koog_loader.documents[-10:]
        self.console.print("\n📝 Sample Documents (last 10):", style="yellow bold")
        for idx, doc in enumerate(last_10, 1):
            self.console.print(f"\n  [{idx}] {doc.title}", style="cyan")
            self.console.print(f"      Path: {doc.relative_path}", style="dim")
            self.console.print(f"      Size: {doc.size_bytes} bytes", style="dim")

        # Suggest sample questions
        sample_questions = self.koog_loader.get_sample_questions(5)

        self.console.print("\n\n💡 Suggested questions (just type them - RAG is automatic!):", style="bright_yellow bold")
        for idx, question in enumerate(sample_questions, 1):
            self.console.print(f"  {idx}. {question}", style="bright_green")

        self.console.print("\n" + "=" * 70, style="bright_cyan")

    def init_rag_client(self):
        """Initialize RAG client with reranker lazily."""
        if self.rag_client is None:
            # Use Ollama for embeddings (1024d)
            ollama_gen = OllamaEmbeddingGenerator(
                base_url="http://localhost:11434",
                model="mxbai-embed-large",
                batch_size=50
            )

            # Initialize reranker with Gemini
            reranker = Reranker(
                gemini_client=self.gemini_client,
                distance_threshold=195.0,
                min_rerank_score=5.0
            )

            self.rag_client = RagClient(
                index_manager=self.indexing_pipeline.index_manager,
                embedding_generator=ollama_gen,
                reranker=reranker
            )

    def is_rag_available(self, collection_name: str = "koog") -> bool:
        """Check if RAG collection is available.

        Args:
            collection_name: Collection to check

        Returns:
            True if collection exists and is accessible
        """
        try:
            collections = self.indexing_pipeline.list_collections()
            return any(col.name == collection_name for col in collections)
        except Exception:
            return False

    def search_context(self, question: str, collection_name: str = "koog"):
        """Search RAG for relevant context.

        Args:
            question: User question
            collection_name: Collection to search in

        Returns:
            List of relevant chunks or empty list if no results or error
        """
        try:
            # Initialize RAG components
            self.init_rag_client()

            # Search for relevant chunks
            chunks = self.rag_client.search(
                question=question,
                collection_name=collection_name,
                top_k=5
            )

            return chunks if chunks else []
        except Exception:
            # Silently fail - return empty list if RAG not available
            return []

    def format_context_for_prompt(self, chunks) -> str:
        """Format RAG chunks as context for the prompt with citations.

        Args:
            chunks: List of document chunks

        Returns:
            Formatted context string with citation guidance
        """
        if not chunks:
            return ""

        # Build context from chunks
        context_parts = []
        for chunk in chunks:
            source_name = Path(chunk.source).name
            context_parts.append(f"[Source: {source_name}, Chunk {chunk.chunk_index}]\n{chunk.text}")

        context = "\n\n".join(context_parts)

        # Create prompt with soft citation guidance
        prompt = f"""Use the following documentation to answer the question.
Please cite sources in your response using the format [Source: filename, Chunk X].

Documentation:
---
{context}
---

Question: """

        return prompt
