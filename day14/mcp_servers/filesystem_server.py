"""Filesystem MCP Server for code analysis.

Provides tools for AI agents to explore project structure and read source code files.
"""

import re
from pathlib import Path
from typing import List, Optional

from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("Filesystem Manager")

# Configuration
IGNORE_PATTERNS = [
    '__pycache__', '.venv', 'venv', 'node_modules', 'env',
    'build', 'dist', 'target', '.git', '.idea', '.vscode',
    '.gradle', '.mvn', 'out', 'bin', '.pytest_cache',
    '.mypy_cache', '.tox', '.eggs', '*.egg-info'
]

IGNORE_EXTENSIONS = [
    '.pyc', '.pyo', '.class', '.o', '.obj', '.exe', '.dll',
    '.so', '.dylib', '.jar', '.war', '.ear', '.zip', '.tar',
    '.gz', '.rar', '.7z', '.png', '.jpg', '.jpeg', '.gif',
    '.ico', '.svg', '.pdf', '.doc', '.docx', '.xls', '.xlsx'
]

SUPPORTED_EXTENSIONS = [
    '.py', '.kt', '.kts', '.java', '.js', '.ts', '.jsx', '.tsx',
    '.go', '.rs', '.cpp', '.c', '.h', '.hpp', '.cs', '.rb',
    '.php', '.swift', '.scala', '.r', '.sql', '.sh', '.bash',
    '.yaml', '.yml', '.json', '.xml', '.html', '.css', '.md',
    '.txt', '.gradle', '.properties', '.toml', '.ini', '.cfg'
]

MAX_FILE_SIZE = 100_000  # 100KB per file
MAX_TOTAL_SIZE = 500_000  # 500KB total per request
MAX_SEARCH_RESULTS = 100  # Maximum search results


def should_ignore(path: Path) -> bool:
    """Check if path should be ignored.

    Args:
        path: Path to check

    Returns:
        True if path should be ignored
    """
    path_str = str(path)
    name = path.name

    # Check ignore patterns
    for pattern in IGNORE_PATTERNS:
        if pattern in path_str or name == pattern:
            return True

    # Check ignore extensions
    if path.is_file():
        ext = path.suffix.lower()
        if ext in IGNORE_EXTENSIONS:
            return True

    return False


def is_supported_file(path: Path, extensions: Optional[List[str]] = None) -> bool:
    """Check if file is supported for reading.

    Args:
        path: Path to check
        extensions: Optional list of extensions to filter (e.g., ['.py', '.kt'])

    Returns:
        True if file is supported
    """
    if not path.is_file():
        return False

    if should_ignore(path):
        return False

    ext = path.suffix.lower()

    # Check custom extensions if provided
    if extensions:
        return ext in [e.lower() for e in extensions]

    # Check default supported extensions
    return ext in SUPPORTED_EXTENSIONS


def get_relative_path(path: Path, base_path: Path) -> str:
    """Get relative path from base.

    Args:
        path: Target path
        base_path: Base path

    Returns:
        Relative path string
    """
    try:
        return str(path.relative_to(base_path))
    except ValueError:
        return str(path)


@mcp.tool()
def get_project_tree(path: str, max_depth: int = 3) -> dict:
    """Get directory tree structure.

    Args:
        path: Root directory path to scan
        max_depth: Maximum depth to traverse (default: 3)

    Returns:
        Dictionary with tree structure and statistics
    """
    try:
        root_path = Path(path).resolve()

        if not root_path.exists():
            return {
                "success": False,
                "error": f"Path does not exist: {path}"
            }

        if not root_path.is_dir():
            return {
                "success": False,
                "error": f"Path is not a directory: {path}"
            }

        tree_lines = []
        file_count = 0
        dir_count = 0
        total_size = 0

        def build_tree(current_path: Path, prefix: str = "", depth: int = 0):
            nonlocal file_count, dir_count, total_size

            if depth > max_depth:
                return

            if should_ignore(current_path):
                return

            try:
                items = sorted(current_path.iterdir(),
                               key=lambda x: (not x.is_dir(), x.name))
            except PermissionError:
                return

            for i, item in enumerate(items):
                if should_ignore(item):
                    continue

                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                next_prefix = "    " if is_last else "│   "

                if item.is_dir():
                    tree_lines.append(f"{prefix}{current_prefix}{item.name}/")
                    dir_count += 1
                    build_tree(item, prefix + next_prefix, depth + 1)
                else:
                    size = item.stat().st_size
                    size_str = f" ({size:,} bytes)" if size > 1024 else ""
                    tree_lines.append(f"{prefix}{current_prefix}{item.name}{size_str}")
                    file_count += 1
                    total_size += size

        tree_lines.append(f"{root_path.name}/")
        build_tree(root_path)

        return {
            "success": True,
            "path": str(root_path),
            "tree": "\n".join(tree_lines),
            "stats": {
                "files": file_count,
                "directories": dir_count,
                "total_size": total_size,
                "max_depth": max_depth
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to build tree: {str(e)}"
        }


@mcp.tool()
def get_file_list(path: str, extensions: Optional[List[str]] = None) -> dict:
    """Get list of files with metadata.

    Args:
        path: Directory path to scan
        extensions: Optional list of file extensions to filter (e.g., ['.py', '.kt'])

    Returns:
        Dictionary with file list and metadata
    """
    try:
        root_path = Path(path).resolve()

        if not root_path.exists():
            return {
                "success": False,
                "error": f"Path does not exist: {path}"
            }

        if not root_path.is_dir():
            return {
                "success": False,
                "error": f"Path is not a directory: {path}"
            }

        files = []
        total_size = 0

        for file_path in root_path.rglob('*'):
            if is_supported_file(file_path, extensions):
                try:
                    size = file_path.stat().st_size
                    rel_path = get_relative_path(file_path, root_path)

                    files.append({
                        "path": str(file_path),
                        "relative_path": rel_path,
                        "name": file_path.name,
                        "extension": file_path.suffix,
                        "size": size,
                        "readable": size <= MAX_FILE_SIZE
                    })
                    total_size += size
                except (PermissionError, OSError):
                    continue

        # Sort by path
        files.sort(key=lambda x: x['relative_path'])

        return {
            "success": True,
            "path": str(root_path),
            "files": files,
            "count": len(files),
            "total_size": total_size,
            "filters": {
                "extensions": extensions or "all supported",
                "max_file_size": MAX_FILE_SIZE
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list files: {str(e)}"
        }


@mcp.tool()
def read_file(file_path: str) -> dict:
    """Read single file content.

    Args:
        file_path: Path to file to read

    Returns:
        Dictionary with file content and metadata
    """
    try:
        path = Path(file_path).resolve()

        if not path.exists():
            return {
                "success": False,
                "error": f"File does not exist: {file_path}"
            }

        if not path.is_file():
            return {
                "success": False,
                "error": f"Path is not a file: {file_path}"
            }

        if should_ignore(path):
            return {
                "success": False,
                "error": f"File type is not supported or ignored: {file_path}"
            }

        size = path.stat().st_size

        if size > MAX_FILE_SIZE:
            return {
                "success": False,
                "error": f"File too large: {size:,} bytes (max: {MAX_FILE_SIZE:,})"
            }

        # Try to read as text
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try other encodings
            try:
                with open(path, 'r', encoding='latin-1') as f:
                    content = f.read()
            except Exception:
                return {
                    "success": False,
                    "error": f"Failed to decode file (not a text file): {file_path}"
                }

        # Count lines
        lines = content.split('\n')
        line_count = len(lines)

        return {
            "success": True,
            "path": str(path),
            "name": path.name,
            "extension": path.suffix,
            "size": size,
            "lines": line_count,
            "content": content
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to read file: {str(e)}"
        }


@mcp.tool()
def read_multiple_files(file_paths: List[str], max_total_size: int = MAX_TOTAL_SIZE) -> dict:
    """Read multiple files at once.

    Args:
        file_paths: List of file paths to read
        max_total_size: Maximum total size in bytes (default: 500KB)

    Returns:
        Dictionary with all files content and metadata
    """
    try:
        if not file_paths:
            return {
                "success": False,
                "error": "No file paths provided"
            }

        if len(file_paths) > 50:
            return {
                "success": False,
                "error": f"Too many files requested: {len(file_paths)} (max: 50)"
            }

        results = []
        total_size = 0
        success_count = 0
        error_count = 0

        for file_path in file_paths:
            result = read_file(file_path)

            if result["success"]:
                file_size = result["size"]

                # Check if adding this file exceeds limit
                if total_size + file_size > max_total_size:
                    results.append({
                        "path": file_path,
                        "success": False,
                        "error": f"Skipped: would exceed total size limit ({max_total_size:,} bytes)"
                    })
                    error_count += 1
                else:
                    results.append(result)
                    total_size += file_size
                    success_count += 1
            else:
                results.append(result)
                error_count += 1

        return {
            "success": True,
            "files": results,
            "stats": {
                "requested": len(file_paths),
                "successful": success_count,
                "failed": error_count,
                "total_size": total_size,
                "max_total_size": max_total_size
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to read files: {str(e)}"
        }


@mcp.tool()
def search_in_files(path: str, pattern: str, extensions: Optional[List[str]] = None) -> dict:
    """Search for pattern in files.

    Args:
        path: Directory path to search in
        pattern: Regular expression pattern to search for
        extensions: Optional list of file extensions to search (e.g., ['.py', '.kt'])

    Returns:
        Dictionary with search results
    """
    try:
        root_path = Path(path).resolve()

        if not root_path.exists():
            return {
                "success": False,
                "error": f"Path does not exist: {path}"
            }

        if not root_path.is_dir():
            return {
                "success": False,
                "error": f"Path is not a directory: {path}"
            }

        # Compile regex pattern
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return {
                "success": False,
                "error": f"Invalid regex pattern: {str(e)}"
            }

        matches = []
        files_searched = 0
        match_count = 0

        for file_path in root_path.rglob('*'):
            if not is_supported_file(file_path, extensions):
                continue

            if file_path.stat().st_size > MAX_FILE_SIZE:
                continue

            files_searched += 1

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            rel_path = get_relative_path(file_path, root_path)

                            matches.append({
                                "file": str(file_path),
                                "relative_path": rel_path,
                                "line": line_num,
                                "content": line.rstrip()
                            })

                            match_count += 1

                            if match_count >= MAX_SEARCH_RESULTS:
                                break

                if match_count >= MAX_SEARCH_RESULTS:
                    break

            except (UnicodeDecodeError, PermissionError, OSError):
                continue

        return {
            "success": True,
            "path": str(root_path),
            "pattern": pattern,
            "matches": matches,
            "stats": {
                "files_searched": files_searched,
                "matches_found": match_count,
                "max_results": MAX_SEARCH_RESULTS,
                "extensions": extensions or "all supported"
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Search failed: {str(e)}"
        }


@mcp.tool()
def get_file_info(file_path: str) -> dict:
    """Get detailed file information.

    Args:
        file_path: Path to file

    Returns:
        Dictionary with file metadata
    """
    try:
        path = Path(file_path).resolve()

        if not path.exists():
            return {
                "success": False,
                "error": f"File does not exist: {file_path}"
            }

        if not path.is_file():
            return {
                "success": False,
                "error": f"Path is not a file: {file_path}"
            }

        stat = path.stat()
        size = stat.st_size

        # Determine language from extension
        ext = path.suffix.lower()
        language_map = {
            '.py': 'Python',
            '.kt': 'Kotlin',
            '.kts': 'Kotlin Script',
            '.java': 'Java',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'React JSX',
            '.tsx': 'React TSX',
            '.go': 'Go',
            '.rs': 'Rust',
            '.cpp': 'C++',
            '.c': 'C',
            '.h': 'C/C++ Header',
            '.cs': 'C#',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.swift': 'Swift'
        }

        return {
            "success": True,
            "path": str(path),
            "name": path.name,
            "extension": ext,
            "language": language_map.get(ext, "Unknown"),
            "size": size,
            "size_readable": f"{size:,} bytes" if size < 1024 else f"{size / 1024:.1f} KB",
            "readable": size <= MAX_FILE_SIZE,
            "ignored": should_ignore(path),
            "supported": is_supported_file(path)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get file info: {str(e)}"
        }


if __name__ == "__main__":
    # Run MCP server
    mcp.run(show_banner=False)
