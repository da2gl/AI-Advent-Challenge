"""MCP server for pipeline operations: summarize and saveToFile."""

import os
from pathlib import Path
from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("Pipeline Server")


@mcp.tool()
def summarize(
    text: str,
    max_length: int = 200,
    style: str = "concise"
) -> str:
    """Summarize text content.

    This tool takes text and returns a summary. In a real implementation,
    this would use an AI model for summarization. For demo purposes,
    it returns instructions for the agent to use Gemini for summarization.

    Args:
        text: Text content to summarize
        max_length: Maximum length of summary in words (default: 200)
        style: Summary style - 'concise', 'detailed', or 'bullet' (default: concise)

    Returns:
        Summary instructions or result
    """
    # This is a placeholder that instructs the agent to use Gemini
    # The actual summarization will be done by the agent using Gemini API
    word_count = len(text.split())

    result = {
        "status": "ready_for_summarization",
        "original_length": word_count,
        "target_length": max_length,
        "style": style,
        "text": text[:500] + "..." if len(text) > 500 else text,
        "message": f"Text ready for summarization ({word_count} words → {max_length} words)"
    }

    import json
    return json.dumps(result, indent=2)


@mcp.tool()
def saveToFile(
    content: str,
    filename: str,
    directory: str = "output"
) -> str:
    """Save content to a file.

    Args:
        content: Content to save
        filename: Name of the file (e.g., 'report.txt', 'analysis.md')
        directory: Directory to save file in (default: 'output')

    Returns:
        JSON string with success status and file path
    """
    import json

    try:
        # Create directory if it doesn't exist
        output_dir = Path(directory)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Full file path
        file_path = output_dir / filename

        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Get absolute path
        abs_path = file_path.absolute()
        file_size = os.path.getsize(abs_path)

        result = {
            "success": True,
            "filename": filename,
            "path": str(abs_path),
            "size_bytes": file_size,
            "message": f"Successfully saved {file_size} bytes to {abs_path}"
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        result = {
            "success": False,
            "error": str(e),
            "message": f"Failed to save file: {str(e)}"
        }
        return json.dumps(result, indent=2)


@mcp.tool()
def readFile(
    filename: str,
    directory: str = "output"
) -> str:
    """Read content from a file.

    Args:
        filename: Name of the file to read
        directory: Directory containing the file (default: 'output')

    Returns:
        JSON string with file content or error
    """
    import json

    try:
        file_path = Path(directory) / filename

        if not file_path.exists():
            return json.dumps({
                "success": False,
                "error": "File not found",
                "message": f"File {file_path} does not exist"
            }, indent=2)

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        result = {
            "success": True,
            "filename": filename,
            "path": str(file_path.absolute()),
            "size_bytes": len(content),
            "content": content,
            "message": f"Successfully read {len(content)} bytes from {filename}"
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        result = {
            "success": False,
            "error": str(e),
            "message": f"Failed to read file: {str(e)}"
        }
        return json.dumps(result, indent=2)


if __name__ == "__main__":
    # Run the MCP server
    mcp.run(show_banner=False)
