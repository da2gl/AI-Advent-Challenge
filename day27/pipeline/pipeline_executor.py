"""Pipeline executor for document indexing."""

from dataclasses import dataclass
from typing import Optional, Union
from pathlib import Path

from .document_loader import DocumentLoader
from .text_chunker import TextChunker
from .embedding_generator import EmbeddingGenerator
from .ollama_embedding_generator import OllamaEmbeddingGenerator
from .index_manager import ChromaIndexManager


@dataclass
class PipelineResult:
    """Result of pipeline execution."""
    success: bool
    collection_name: str
    documents_loaded: int
    chunks_created: int
    embeddings_generated: int
    documents_indexed: int
    error_message: Optional[str] = None


class IndexingPipeline:
    """4-stage document indexing pipeline."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        persist_directory: str = "data/chroma_db",
        embedding_generator: Optional[Union[EmbeddingGenerator, OllamaEmbeddingGenerator]] = None
    ):
        """Initialize pipeline.

        Args:
            api_key: Gemini API key (required if embedding_generator not provided)
            persist_directory: ChromaDB persistence directory
            embedding_generator: Custom embedding generator (Gemini or Ollama).
                               If None, creates Gemini generator with api_key.
        """
        self.api_key = api_key
        self.persist_directory = persist_directory

        # Initialize pipeline stages
        self.loader = DocumentLoader()
        self.chunker = TextChunker(chunk_size=500, overlap=50)

        # Use provided embedding generator or create Gemini one
        if embedding_generator:
            self.embedding_gen = embedding_generator
        elif api_key:
            self.embedding_gen = EmbeddingGenerator(api_key=api_key, batch_size=100)
        else:
            raise ValueError(
                "Either api_key or embedding_generator must be provided"
            )

        self.index_manager = ChromaIndexManager(persist_directory=persist_directory)

    def index_path(
        self,
        path: str,
        collection_name: str,
        show_progress: bool = True
    ) -> PipelineResult:
        """Index a file or directory.

        Args:
            path: Path to file or directory
            collection_name: Name for the collection
            show_progress: Whether to show progress messages

        Returns:
            PipelineResult with execution details
        """
        try:
            # Stage 1: Load documents
            if show_progress:
                print("📄 Stage 1: Loading documents...")

            path_obj = Path(path)
            if path_obj.is_file():
                documents = [self.loader.load_file(path)]
                documents = [d for d in documents if d is not None]
            elif path_obj.is_dir():
                documents = self.loader.load_directory(path, recursive=True)
            else:
                return PipelineResult(
                    success=False,
                    collection_name=collection_name,
                    documents_loaded=0,
                    chunks_created=0,
                    embeddings_generated=0,
                    documents_indexed=0,
                    error_message=f"Path not found: {path}"
                )

            if not documents:
                return PipelineResult(
                    success=False,
                    collection_name=collection_name,
                    documents_loaded=0,
                    chunks_created=0,
                    embeddings_generated=0,
                    documents_indexed=0,
                    error_message="No documents loaded"
                )

            if show_progress:
                doc_stats = self.loader.get_stats(documents)
                print(f"  ✓ Loaded {len(documents)} documents ({doc_stats['total_chars']} chars)")

            # Stage 2: Chunk documents
            if show_progress:
                print("✂️  Stage 2: Chunking text...")

            chunks = self.chunker.chunk_multiple_documents(documents)

            if not chunks:
                return PipelineResult(
                    success=False,
                    collection_name=collection_name,
                    documents_loaded=len(documents),
                    chunks_created=0,
                    embeddings_generated=0,
                    documents_indexed=0,
                    error_message="No chunks created"
                )

            if show_progress:
                chunk_stats = self.chunker.get_stats(chunks)
                print(f"  ✓ Created {len(chunks)} chunks (avg: {chunk_stats['avg_chunk_size']} chars)")

            # Stage 3: Generate embeddings
            if show_progress:
                print("🧠 Stage 3: Generating embeddings...")

            embeddings = self.embedding_gen.generate_embeddings_for_chunks(
                chunks,
                show_progress=show_progress
            )

            if not embeddings:
                return PipelineResult(
                    success=False,
                    collection_name=collection_name,
                    documents_loaded=len(documents),
                    chunks_created=len(chunks),
                    embeddings_generated=0,
                    documents_indexed=0,
                    error_message="No embeddings generated"
                )

            # Validate embeddings
            validation = self.embedding_gen.validate_embeddings(embeddings)

            if show_progress:
                print(f"  ✓ Generated {validation['valid']} embeddings "
                      f"({validation['success_rate']:.1f}% success)")

            if validation['valid'] == 0:
                return PipelineResult(
                    success=False,
                    collection_name=collection_name,
                    documents_loaded=len(documents),
                    chunks_created=len(chunks),
                    embeddings_generated=0,
                    documents_indexed=0,
                    error_message="All embeddings failed validation"
                )

            # Stage 4: Index in ChromaDB
            if show_progress:
                print("💾 Stage 4: Indexing in ChromaDB...")

            indexed_count = self.index_manager.add_documents(
                collection_name=collection_name,
                chunks=chunks,
                embeddings=embeddings,
                collection_metadata={
                    'source_path': path,
                    'total_documents': len(documents)
                }
            )

            if show_progress:
                print(f"  ✓ Indexed {indexed_count} chunks in collection '{collection_name}'")

            return PipelineResult(
                success=True,
                collection_name=collection_name,
                documents_loaded=len(documents),
                chunks_created=len(chunks),
                embeddings_generated=validation['valid'],
                documents_indexed=indexed_count
            )

        except Exception as e:
            return PipelineResult(
                success=False,
                collection_name=collection_name,
                documents_loaded=0,
                chunks_created=0,
                embeddings_generated=0,
                documents_indexed=0,
                error_message=f"Pipeline error: {str(e)}"
            )

    def search(
        self,
        query: str,
        collection_name: Optional[str] = None,
        top_k: int = 5
    ):
        """Search for documents.

        Args:
            query: Search query
            collection_name: Specific collection (None for all)
            top_k: Number of results

        Returns:
            List of SearchResult objects
        """
        # Generate query embedding
        query_embedding = self.embedding_gen.generate_embedding(query)

        if not query_embedding:
            print("Error: Failed to generate query embedding")
            return []

        # Search in index
        results = self.index_manager.search(
            query_embedding=query_embedding,
            collection_name=collection_name,
            top_k=top_k
        )

        return results

    def list_collections(self):
        """List all collections.

        Returns:
            List of CollectionInfo objects
        """
        return self.index_manager.list_collections()

    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection.

        Args:
            collection_name: Name of collection to delete

        Returns:
            True if successful
        """
        return self.index_manager.delete_collection(collection_name)

    def clear_all(self) -> bool:
        """Clear all collections.

        Returns:
            True if successful
        """
        return self.index_manager.clear_all()

    def get_stats(self):
        """Get overall statistics.

        Returns:
            Dictionary with statistics
        """
        return self.index_manager.get_stats()

    def close(self):
        """Close pipeline resources."""
        self.embedding_gen.close()
