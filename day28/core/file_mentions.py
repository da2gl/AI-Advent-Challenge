"""File mention parser for @file.py and @folder/ patterns."""

import os
import re
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class FileMention:
    """Represents a mentioned file."""
    path: str
    exists: bool
    is_dir: bool
    size: Optional[int] = None
    file_count: Optional[int] = None  # For directories


class FileMentionParser:
    """Parses and processes @ file mentions from user input."""

    def __init__(self, base_dir: str = "."):
        """
        Initialize parser.

        Args:
            base_dir: Base directory for relative paths
        """
        self.base_dir = Path(base_dir).resolve()

    def parse_mentions(self, text: str) -> List[FileMention]:
        """
        Parse all @ mentions from text.

        Args:
            text: User input text

        Returns:
            List of FileMention objects
        """
        # Pattern: @path/to/file or @folder/
        # Allows alphanumeric, dots, slashes, underscores, hyphens
        pattern = r'@([\w\-./]+/?)'
        matches = re.findall(pattern, text)

        mentions = []
        seen = set()  # Avoid duplicates

        for match in matches:
            if match in seen:
                continue
            seen.add(match)

            mention = self._create_mention(match)
            mentions.append(mention)

        return mentions

    def _create_mention(self, path_str: str) -> FileMention:
        """
        Create FileMention object with validation.

        Args:
            path_str: Path string from mention

        Returns:
            FileMention object
        """
        # Resolve relative to base_dir
        if path_str.startswith('/'):
            full_path = Path(path_str)
        else:
            full_path = (self.base_dir / path_str).resolve()

        exists = full_path.exists()
        is_dir = full_path.is_dir() if exists else path_str.endswith('/')

        size = None
        file_count = None

        if exists:
            if is_dir:
                # Count files in directory
                file_count = self._count_files(full_path)
            else:
                # Get file size
                try:
                    size = full_path.stat().st_size
                except Exception:
                    size = None

        return FileMention(
            path=str(full_path.relative_to(self.base_dir)) if exists else path_str,
            exists=exists,
            is_dir=is_dir,
            size=size,
            file_count=file_count
        )

    def _count_files(self, directory: Path, recursive: bool = True) -> int:
        """
        Count files in directory.

        Args:
            directory: Directory path
            recursive: Count recursively

        Returns:
            Number of files
        """
        try:
            if recursive:
                return sum(1 for _ in directory.rglob('*') if _.is_file())
            else:
                return sum(1 for _ in directory.iterdir() if _.is_file())
        except Exception:
            return 0

    def format_context(self, mentions: List[FileMention]) -> str:
        """
        Format mentions as context for AI.

        Args:
            mentions: List of FileMention objects

        Returns:
            Formatted context string
        """
        if not mentions:
            return ""

        context_parts = ["User mentioned the following files:\n"]

        for mention in mentions:
            if not mention.exists:
                context_parts.append(f"- @{mention.path} ⚠️ (not found)\n")
                continue

            if mention.is_dir:
                context_parts.append(
                    f"- @{mention.path}/ (directory with {mention.file_count} files)\n"
                )
            else:
                size_kb = mention.size / 1024 if mention.size else 0
                if size_kb < 1:
                    size_str = f"{mention.size} bytes"
                else:
                    size_str = f"{size_kb:.1f} KB"
                context_parts.append(f"- @{mention.path} ({size_str})\n")

        context_parts.append("\nYou can use MCP tools to read these files:\n")
        context_parts.append("- filesystem_read_file(path) to read file content\n")
        context_parts.append("- filesystem_list_directory(path) to list directory\n")
        context_parts.append("\n")

        return "".join(context_parts)

    def get_project_files(
        self,
        extensions: Optional[List[str]] = None,
        exclude_dirs: Optional[List[str]] = None
    ) -> List[str]:
        """
        Get all files in project for autocomplete.

        Args:
            extensions: Filter by extensions (e.g., ['.py', '.js'])
            exclude_dirs: Directories to exclude

        Returns:
            List of relative file paths
        """
        if exclude_dirs is None:
            exclude_dirs = [
                '__pycache__', '.git', '.venv', 'venv',
                'node_modules', '.idea', 'dist', 'build'
            ]

        files = []

        try:
            for root, dirs, filenames in os.walk(self.base_dir):
                # Remove excluded directories
                dirs[:] = [d for d in dirs if d not in exclude_dirs]

                root_path = Path(root)
                for filename in filenames:
                    file_path = root_path / filename

                    # Filter by extension
                    if extensions and file_path.suffix not in extensions:
                        continue

                    # Get relative path
                    try:
                        rel_path = file_path.relative_to(self.base_dir)
                        files.append(str(rel_path))
                    except ValueError:
                        continue

        except Exception:
            pass

        return sorted(files)

    def get_project_dirs(
        self,
        exclude_dirs: Optional[List[str]] = None
    ) -> List[str]:
        """
        Get all directories in project for autocomplete.

        Args:
            exclude_dirs: Directories to exclude

        Returns:
            List of relative directory paths
        """
        if exclude_dirs is None:
            exclude_dirs = [
                '__pycache__', '.git', '.venv', 'venv',
                'node_modules', '.idea', 'dist', 'build'
            ]

        dirs = []

        try:
            for root, dirnames, _ in os.walk(self.base_dir):
                # Remove excluded directories
                dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

                root_path = Path(root)
                for dirname in dirnames:
                    dir_path = root_path / dirname

                    # Get relative path
                    try:
                        rel_path = dir_path.relative_to(self.base_dir)
                        dirs.append(str(rel_path) + '/')
                    except ValueError:
                        continue

        except Exception:
            pass

        return sorted(dirs)

    def remove_mentions_from_text(self, text: str) -> str:
        """
        Remove @ mentions from text (keep them in context only).

        Args:
            text: Original text with mentions

        Returns:
            Text without @ mentions
        """
        # Replace @path with just path in quotes
        pattern = r'@([\w\-./]+/?)'

        def replace_mention(match):
            return f'"{match.group(1)}"'

        return re.sub(pattern, replace_mention, text)
