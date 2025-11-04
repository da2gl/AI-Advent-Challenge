"""Document indexing manager."""

from pathlib import Path
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from pipeline.pipeline_executor import IndexingPipeline


class IndexManager:
    """Manages document indexing and search operations."""

    def __init__(self, console: Console, api_key: str, persist_directory: str = "data/chroma_db"):
        """
        Initialize index manager.

        Args:
            console: Rich console for output
            api_key: Gemini API key
            persist_directory: ChromaDB persistence directory
        """
        self.console = console
        self.api_key = api_key
        self.persist_directory = persist_directory
        self.indexing_pipeline = None
        self.last_search_results = None

    def _init_pipeline(self):
        """Initialize indexing pipeline lazily."""
        if self.indexing_pipeline is None:
            self.indexing_pipeline = IndexingPipeline(
                api_key=self.api_key,
                persist_directory=self.persist_directory
            )

    def index_documents(self, command_args: str):
        """Index documents from path."""
        # Parse arguments
        parts = command_args.split()
        if not parts:
            self.console.print("✗ Usage: /index <path> [--collection <name>]", style="red")
            return

        path = parts[0]
        collection_name = None

        # Look for --collection flag
        if "--collection" in parts:
            try:
                coll_idx = parts.index("--collection")
                if coll_idx + 1 < len(parts):
                    collection_name = parts[coll_idx + 1]
            except (ValueError, IndexError):
                pass

        # Default collection name from path
        if not collection_name:
            path_obj = Path(path)
            collection_name = path_obj.stem if path_obj.is_file() else path_obj.name
            # Sanitize collection name
            collection_name = collection_name.replace(" ", "_").replace("-", "_").lower()

        # Validate path
        path_obj = Path(path)
        if not path_obj.exists():
            self.console.print(f"✗ Path not found: {path}", style="red")
            return

        # Initialize pipeline
        self._init_pipeline()

        # Run indexing
        self.console.print(f"\n📚 Indexing: {path}", style="bright_cyan bold")
        self.console.print(f"Collection: {collection_name}", style="cyan")
        self.console.print("=" * 70, style="bright_cyan")

        try:
            result = self.indexing_pipeline.index_path(
                path=path,
                collection_name=collection_name,
                show_progress=True
            )

            if result.success:
                self.console.print("\n" + "=" * 70, style="bright_cyan")
                self.console.print("✓ Indexing complete!", style="green bold")
                self.console.print(f"  Documents loaded: {result.documents_loaded}", style="dim")
                self.console.print(f"  Chunks created: {result.chunks_created}", style="dim")
                self.console.print(f"  Embeddings generated: {result.embeddings_generated}", style="dim")
                self.console.print(f"  Documents indexed: {result.documents_indexed}", style="dim")
                self.console.print(f"\n💡 Try: /search \"your query\" --collection {collection_name}", style="bright_yellow")
            else:
                self.console.print(f"\n✗ Indexing failed: {result.error_message}", style="red")

        except Exception as e:
            self.console.print(f"\n✗ Indexing error: {str(e)}", style="red")

    def search_index(self, command_args: str):
        """Search in indexed documents."""
        # Parse arguments
        parts = command_args.split("--collection")

        if not parts or not parts[0].strip():
            self.console.print("✗ Usage: /search <query> [--collection <name>]", style="red")
            return

        query = parts[0].strip().strip('"').strip("'")
        collection_name = None

        if len(parts) > 1:
            collection_name = parts[1].strip()

        # Initialize pipeline
        self._init_pipeline()

        # Search
        self.console.print(f"\n🔍 Searching for: \"{query}\"", style="bright_cyan bold")
        if collection_name:
            self.console.print(f"Collection: {collection_name}", style="cyan")
        else:
            self.console.print("Collection: All collections", style="cyan")
        self.console.print("=" * 70, style="bright_cyan")

        try:
            spinner = Spinner("dots", text="Searching...", style="yellow")
            with Live(spinner, console=self.console, transient=True):
                results = self.indexing_pipeline.search(
                    query=query,
                    collection_name=collection_name,
                    top_k=5
                )

            if not results:
                self.console.print("\n✗ No results found", style="yellow")
                return

            # Store results
            self.last_search_results = results

            # Display results
            self.console.print(f"\n📋 Found {len(results)} results:\n", style="green bold")

            for idx, result in enumerate(results, 1):
                # Create result panel
                source_name = Path(result.source).name
                panel_content = f"[dim]{result.text[:300]}{'...' if len(result.text) > 300 else ''}[/dim]\n\n"
                panel_content += f"[cyan]Source:[/cyan] {source_name}\n"
                panel_content += f"[cyan]Chunk:[/cyan] {result.chunk_index} | [cyan]Distance:[/cyan] {result.distance:.4f}"

                panel = Panel(
                    panel_content,
                    title=f"Result {idx}",
                    border_style="bright_green" if idx == 1 else "green"
                )
                self.console.print(panel)

            self.console.print("\n💡 You can now ask AI questions about these results!", style="bright_yellow")

        except Exception as e:
            self.console.print(f"\n✗ Search error: {str(e)}", style="red")

    def list_collections(self):
        """List all collections."""
        self._init_pipeline()

        try:
            collections = self.indexing_pipeline.list_collections()

            if not collections:
                self.console.print("\n📚 No collections found", style="yellow")
                self.console.print("💡 Use /index <path> to create a collection", style="dim")
                return

            # Create table
            table = Table(title="📚 Collections", show_header=True, header_style="bold magenta")
            table.add_column("Name", style="cyan", width=30)
            table.add_column("Documents", justify="right", style="white", width=12)
            table.add_column("Metadata", style="dim", width=30)

            total_docs = 0
            for col in collections:
                total_docs += col.count
                metadata_str = ", ".join(f"{k}: {v}" for k, v in col.metadata.items() if k != "hnsw:space")
                table.add_row(col.name, str(col.count), metadata_str[:30])

            self.console.print("\n")
            self.console.print(table)
            self.console.print(f"\nTotal: {len(collections)} collections, {total_docs} documents", style="dim")

        except Exception as e:
            self.console.print(f"\n✗ Error listing collections: {str(e)}", style="red")

    def delete_collection(self, collection_name: str):
        """Delete a specific collection."""
        if not collection_name.strip():
            self.console.print("✗ Usage: /delete-collection <name>", style="red")
            return

        self._init_pipeline()

        try:
            success = self.indexing_pipeline.delete_collection(collection_name.strip())
            if success:
                self.console.print(f"✓ Collection '{collection_name}' deleted", style="green")
            else:
                self.console.print(f"✗ Failed to delete collection '{collection_name}'", style="red")
        except Exception as e:
            self.console.print(f"✗ Error: {str(e)}", style="red")

    def clear_all(self):
        """Clear all indexed data."""
        self._init_pipeline()

        # Confirm
        self.console.print("\n⚠️  Warning: This will delete ALL collections and indexed data!", style="yellow bold")
        confirm = input("Type 'yes' to confirm: ").strip().lower()

        if confirm != "yes":
            self.console.print("Cancelled", style="dim")
            return

        try:
            success = self.indexing_pipeline.clear_all()
            if success:
                self.console.print("✓ All indexed data cleared", style="green")
            else:
                self.console.print("✗ Failed to clear index", style="red")
        except Exception as e:
            self.console.print(f"✗ Error: {str(e)}", style="red")
