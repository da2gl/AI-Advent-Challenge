"""Koog documentation loader for RAG comparison."""

import os
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path


@dataclass
class KoogDocument:
    """Single document from Koog documentation."""
    file_path: str
    title: str
    content: str
    relative_path: str
    size_bytes: int

    def __str__(self):
        return f"{self.title} ({self.size_bytes} bytes)"


class KoogLoader:
    """Loads and manages Koog documentation for RAG experiments."""

    def __init__(self, docs_path: str = "koog"):
        """Initialize Koog loader.

        Args:
            docs_path: Path to Koog documentation directory
        """
        self.docs_path = docs_path
        self.documents: List[KoogDocument] = []

    def load(
        self,
        pattern: str = "**/*.md",
        limit: Optional[int] = None
    ) -> List[KoogDocument]:
        """Load Koog documentation files.

        Args:
            pattern: Glob pattern for files to load (default: **/*.md)
            limit: Maximum number of documents to load

        Returns:
            List of KoogDocument objects
        """
        if not os.path.exists(self.docs_path):
            raise FileNotFoundError(
                f"Koog docs path not found: {self.docs_path}\n"
                f"Make sure the submodule is initialized: "
                f"git submodule update --init"
            )

        docs_dir = Path(self.docs_path)
        md_files = list(docs_dir.glob(pattern))

        if limit:
            md_files = md_files[:limit]

        self.documents = []
        for file_path in md_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Skip empty files
                if not content.strip():
                    continue

                # Extract title from filename or first H1 heading
                title = self._extract_title(file_path, content)

                # Get relative path for display
                relative_path = str(file_path.relative_to(docs_dir))

                doc = KoogDocument(
                    file_path=str(file_path),
                    title=title,
                    content=content,
                    relative_path=relative_path,
                    size_bytes=len(content.encode('utf-8'))
                )
                self.documents.append(doc)

            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {str(e)}")
                continue

        return self.documents

    def _extract_title(self, file_path: Path, content: str) -> str:
        """Extract document title from content or filename.

        Args:
            file_path: Path to the file
            content: File content

        Returns:
            Document title
        """
        # Try to find H1 heading
        lines = content.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            if line.startswith('# '):
                return line[2:].strip()

        # Fallback to filename
        return file_path.stem.replace('-', ' ').replace('_', ' ').title()

    def get_contents(self) -> List[str]:
        """Get all document contents from loaded documents.

        Returns:
            List of document contents (for indexing)
        """
        return [doc.content for doc in self.documents]

    def get_document(self, index: int) -> Optional[KoogDocument]:
        """Get document by index.

        Args:
            index: Document index

        Returns:
            KoogDocument or None if index out of range
        """
        if 0 <= index < len(self.documents):
            return self.documents[index]
        return None

    def get_stats(self) -> dict:
        """Get statistics about loaded documents.

        Returns:
            Dictionary with statistics
        """
        if not self.documents:
            return {
                'total_docs': 0,
                'total_size_bytes': 0,
                'total_size_kb': 0,
                'avg_size_bytes': 0,
                'topics': []
            }

        total_size = sum(doc.size_bytes for doc in self.documents)

        # Extract topics from directory structure
        topics = set()
        for doc in self.documents:
            parts = Path(doc.relative_path).parts
            if len(parts) > 1:
                topics.add(parts[0])

        return {
            'total_docs': len(self.documents),
            'total_size_bytes': total_size,
            'total_size_kb': total_size / 1024,
            'avg_size_bytes': total_size / len(self.documents),
            'topics': sorted(list(topics)) if topics else ['docs']
        }

    def get_sample_questions(self, count: int = 5) -> List[str]:
        """Generate sample questions based on document titles.

        Args:
            count: Number of questions to generate

        Returns:
            List of suggested questions
        """
        if not self.documents:
            return []

        questions = []
        for doc in self.documents[:count]:
            # Generate question from title
            title = doc.title.lower()

            # Common patterns for generating questions
            if 'how' in title or 'guide' in title:
                questions.append(f"How does {title} work?")
            elif 'what' in title:
                questions.append(title + "?")
            else:
                questions.append(f"What is {title}?")

        return questions

    def search_by_keyword(self, keyword: str) -> List[KoogDocument]:
        """Search documents by keyword in title or content.

        Args:
            keyword: Keyword to search for

        Returns:
            List of matching documents
        """
        keyword_lower = keyword.lower()
        matches = []

        for doc in self.documents:
            if (keyword_lower in doc.title.lower()
                    or keyword_lower in doc.content.lower()):
                matches.append(doc)

        return matches

    def __len__(self) -> int:
        """Return number of loaded documents."""
        return len(self.documents)
