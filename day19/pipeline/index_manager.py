"""ChromaDB index manager for storing and retrieving document embeddings."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path
import chromadb
from chromadb.config import Settings


@dataclass
class CollectionInfo:
    """Information about a ChromaDB collection."""
    name: str
    count: int
    metadata: Dict[str, Any]


@dataclass
class SearchResult:
    """Search result from ChromaDB."""
    text: str
    source: str
    distance: float
    metadata: Dict[str, Any]
    chunk_index: int


class ChromaIndexManager:
    """Manage ChromaDB collections for document indexing."""

    def __init__(self, persist_directory: str = "data/chroma_db"):
        """Initialize ChromaDB manager.

        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = persist_directory

        # Create directory if it doesn't exist
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

    def create_or_get_collection(self, collection_name: str, metadata: Dict[str, Any] = None) -> Any:
        """Create a new collection or get existing one.

        Args:
            collection_name: Name of the collection
            metadata: Optional metadata for the collection

        Returns:
            ChromaDB collection object
        """
        try:
            # Try to get existing collection
            collection = self.client.get_collection(name=collection_name)
            return collection
        except Exception:
            # Create new collection if it doesn't exist
            collection = self.client.create_collection(
                name=collection_name,
                metadata=metadata or {}
            )
            return collection

    def add_documents(
        self,
        collection_name: str,
        chunks: List,
        embeddings: List[List[float]],
        collection_metadata: Dict[str, Any] = None
    ) -> int:
        """Add documents to a collection.

        Args:
            collection_name: Name of the collection
            chunks: List of TextChunk objects
            embeddings: List of embedding vectors
            collection_metadata: Optional metadata for the collection

        Returns:
            Number of documents successfully added
        """
        if not chunks or not embeddings:
            return 0

        if len(chunks) != len(embeddings):
            raise ValueError(f"Chunks count ({len(chunks)}) doesn't match embeddings count ({len(embeddings)})")

        # Get or create collection
        collection = self.create_or_get_collection(collection_name, collection_metadata)

        # Filter out chunks with invalid embeddings
        valid_data = []
        for chunk, embedding in zip(chunks, embeddings):
            if embedding and len(embedding) > 0:
                valid_data.append((chunk, embedding))

        if not valid_data:
            print("Warning: No valid embeddings to add")
            return 0

        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        embeddings_list = []

        for idx, (chunk, embedding) in enumerate(valid_data):
            # Create unique ID
            chunk_id = f"{collection_name}_{chunk.source}_{chunk.chunk_index}_{idx}"

            ids.append(chunk_id)
            documents.append(chunk.text)
            metadatas.append(chunk.metadata)
            embeddings_list.append(embedding)

        # Add to collection
        try:
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings_list
            )
            return len(ids)
        except Exception as e:
            print(f"Error adding documents to collection: {str(e)}")
            return 0

    def search(
        self,
        query_embedding: List[float],
        collection_name: Optional[str] = None,
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar documents.

        Args:
            query_embedding: Query embedding vector
            collection_name: Specific collection to search (None for all)
            top_k: Number of results to return
            where: Optional metadata filter

        Returns:
            List of SearchResult objects
        """
        if collection_name:
            # Search in specific collection
            collections = [self.get_collection(collection_name)]
            if not collections[0]:
                return []
        else:
            # Search in all collections
            collections = self.list_collections()
            collections = [self.get_collection(col.name) for col in collections]

        all_results = []

        for collection in collections:
            if not collection:
                continue

            try:
                # Query the collection
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=where
                )

                # Parse results
                if results and results['documents'] and results['documents'][0]:
                    for idx, doc in enumerate(results['documents'][0]):
                        metadata = results['metadatas'][0][idx] if results['metadatas'] else {}
                        distance = results['distances'][0][idx] if results['distances'] else 0.0

                        all_results.append(SearchResult(
                            text=doc,
                            source=metadata.get('source', 'unknown'),
                            distance=distance,
                            metadata=metadata,
                            chunk_index=metadata.get('chunk_index', 0)
                        ))

            except Exception as e:
                print(f"Error searching collection {collection.name}: {str(e)}")
                continue

        # Sort by distance and return top_k
        all_results.sort(key=lambda x: x.distance)
        return all_results[:top_k]

    def list_collections(self) -> List[CollectionInfo]:
        """List all collections.

        Returns:
            List of CollectionInfo objects
        """
        collections = []

        try:
            for collection in self.client.list_collections():
                count = collection.count()
                metadata = collection.metadata or {}

                collections.append(CollectionInfo(
                    name=collection.name,
                    count=count,
                    metadata=metadata
                ))
        except Exception as e:
            print(f"Error listing collections: {str(e)}")

        return collections

    def get_collection(self, collection_name: str) -> Optional[Any]:
        """Get a specific collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Collection object or None if not found
        """
        try:
            return self.client.get_collection(name=collection_name)
        except Exception:
            return None

    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection.

        Args:
            collection_name: Name of the collection to delete

        Returns:
            True if deleted successfully
        """
        try:
            self.client.delete_collection(name=collection_name)
            return True
        except Exception as e:
            print(f"Error deleting collection {collection_name}: {str(e)}")
            return False

    def clear_all(self) -> bool:
        """Delete all collections.

        Returns:
            True if all collections deleted successfully
        """
        try:
            collections = self.list_collections()
            for col in collections:
                self.delete_collection(col.name)
            return True
        except Exception as e:
            print(f"Error clearing all collections: {str(e)}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get overall statistics.

        Returns:
            Dictionary with statistics
        """
        collections = self.list_collections()
        total_documents = sum(col.count for col in collections)

        return {
            'total_collections': len(collections),
            'total_documents': total_documents,
            'collections': [
                {'name': col.name, 'count': col.count, 'metadata': col.metadata}
                for col in collections
            ]
        }
