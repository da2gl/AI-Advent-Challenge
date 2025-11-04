"""Document loader for various file formats."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from datetime import datetime


@dataclass
class Document:
    """Represents a loaded document."""
    content: str
    source: str
    file_type: str
    size: int
    created_at: str


class DocumentLoader:
    """Load documents from various file formats."""

    SUPPORTED_EXTENSIONS = {'.txt', '.md', '.rst', '.py', '.js', '.java', '.go', '.rs', '.cpp', '.pdf'}

    def __init__(self):
        """Initialize document loader."""
        self.pdf_available = self._check_pdf_support()

    def _check_pdf_support(self) -> bool:
        """Check if PDF support is available."""
        try:
            import PyPDF2  # noqa: F401
            return True
        except ImportError:
            return False

    def load_file(self, file_path: str) -> Optional[Document]:
        """Load a single file.

        Args:
            file_path: Path to the file

        Returns:
            Document object or None if failed
        """
        path = Path(file_path)

        if not path.exists():
            print(f"Error: File not found: {file_path}")
            return None

        if not path.is_file():
            print(f"Error: Not a file: {file_path}")
            return None

        extension = path.suffix.lower()
        if extension not in self.SUPPORTED_EXTENSIONS:
            print(f"Warning: Unsupported file type: {extension}")
            return None

        # Load content based on file type
        try:
            if extension == '.pdf':
                content = self._load_pdf(path)
            else:
                content = self._load_text(path)

            if content is None:
                return None

            # Get file metadata
            stat = path.stat()

            return Document(
                content=content,
                source=str(path),
                file_type=extension[1:],  # Remove leading dot
                size=stat.st_size,
                created_at=datetime.fromtimestamp(stat.st_mtime).isoformat()
            )

        except Exception as e:
            print(f"Error loading {file_path}: {str(e)}")
            return None

    def _load_text(self, path: Path) -> Optional[str]:
        """Load text-based file.

        Args:
            path: Path object

        Returns:
            File content as string
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading {path}: {str(e)}")
                return None
        except Exception as e:
            print(f"Error reading {path}: {str(e)}")
            return None

    def _load_pdf(self, path: Path) -> Optional[str]:
        """Load PDF file.

        Args:
            path: Path object

        Returns:
            Extracted text from PDF
        """
        if not self.pdf_available:
            print(f"Warning: PyPDF2 not available, skipping {path}")
            return None

        try:
            import PyPDF2

            with open(path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text_parts = []

                for page_num, page in enumerate(reader.pages):
                    try:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                    except Exception as e:
                        print(f"Warning: Error extracting page {page_num} from {path}: {str(e)}")

                return '\n\n'.join(text_parts)

        except Exception as e:
            print(f"Error loading PDF {path}: {str(e)}")
            return None

    def load_directory(self, directory_path: str, recursive: bool = True) -> List[Document]:
        """Load all supported files from a directory.

        Args:
            directory_path: Path to directory
            recursive: Whether to search subdirectories

        Returns:
            List of Document objects
        """
        path = Path(directory_path)

        if not path.exists():
            print(f"Error: Directory not found: {directory_path}")
            return []

        if not path.is_dir():
            print(f"Error: Not a directory: {directory_path}")
            return []

        documents = []

        # Get all files
        if recursive:
            files = [f for f in path.rglob('*') if f.is_file()]
        else:
            files = [f for f in path.iterdir() if f.is_file()]

        # Filter and load supported files
        for file_path in files:
            if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                doc = self.load_file(str(file_path))
                if doc:
                    documents.append(doc)

        return documents

    def get_stats(self, documents: List[Document]) -> dict:
        """Get statistics about loaded documents.

        Args:
            documents: List of Document objects

        Returns:
            Dictionary with statistics
        """
        if not documents:
            return {
                'total_files': 0,
                'total_size': 0,
                'total_chars': 0,
                'file_types': {}
            }

        file_types = {}
        total_size = 0
        total_chars = 0

        for doc in documents:
            # Count by file type
            file_types[doc.file_type] = file_types.get(doc.file_type, 0) + 1
            total_size += doc.size
            total_chars += len(doc.content)

        return {
            'total_files': len(documents),
            'total_size': total_size,
            'total_chars': total_chars,
            'file_types': file_types
        }
