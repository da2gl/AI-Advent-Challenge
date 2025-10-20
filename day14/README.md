# Day 14: AI Code Analysis with Filesystem MCP

**Challenge**: Instead of loading entire codebases at once (which exceeds context limits), implement a smart exploration
system where the AI decides which files to read based on project structure and analysis goals—similar to how Cursor and
Claude Code work.

**Result**: An AI code analysis assistant that can find bugs, review architecture, and understand codebases through
natural language conversation.

## What You'll Learn

- 🤖 **AI-driven exploration**: Multi-pass analysis strategy
- 📁 **MCP filesystem integration**: 6 tools for file operations
- 🔄 **Iterative code analysis**: Smart file selection and reading
- 💬 **Conversational interface**: Natural language code review

---

## Quick Start

```bash
# 1. Install dependencies
cd day14
pip install -r requirements.txt

# 2. Set API key
export GEMINI_API_KEY="your-key-here"

# 3. Run the assistant
python chat.py

# 4. Analyze a project (example with Flask submodule)
You: Analyze flask_test_project and show project tree
```

---

## Architecture

```
Chat Interface (chat.py)
    ↓
Gemini AI Client ←→ MCP Manager
                        ↓
                 Filesystem MCP
                 (6 tools)
                        ↓
                  Local Files
```

**Key Components:**

- **Gemini Client**: AI engine with function calling
- **MCP Manager**: Handles filesystem tool orchestration
- **Filesystem Server**: 6 tools for file exploration
- **Conversation Manager**: Context and token management

---

## The 6 Filesystem Tools

### 1. `get_project_tree(path, max_depth=3)`

Get directory structure as a tree view.

**Use case**: First step in any analysis—understand project organization.

**Example**:

```python
{
    "tree": "project/\n├── src/\n│   └── main.py\n└── tests/",
    "stats": {"files": 15, "directories": 4}
}
```

### 2. `get_file_list(path, extensions=None)`

List all files with metadata (size, type, readability).

**Use case**: See what files are available before reading.

**Example**:

```python
{
    "files": [
        {"path": "src/app.py", "size": 2048, "extension": ".py", "readable": true},
        {"path": "tests/test_app.py", "size": 1024, "extension": ".py", "readable": true}
    ]
}
```

### 3. `read_file(file_path)`

Read a single file's content.

**Use case**: Read key files identified during exploration.

**Limits**: 100KB per file, UTF-8/latin-1 encoding.

### 4. `read_multiple_files(file_paths, max_total_size=500000)`

Batch read multiple files.

**Use case**: Read related files together (e.g., module + tests).

**Limits**: 50 files max, 500KB total.

### 5. `search_in_files(path, pattern, extensions=None)`

Regex search across files.

**Use case**: Find TODO comments, security patterns, specific function calls.

**Example**:

```python
search_in_files("src", "TODO|FIXME", [".py"])
# Returns: matches with file path and line number
```

### 6. `get_file_info(file_path)`

Get file metadata and language detection.

**Use case**: Check if file is readable before attempting to read.

---

## How It Works: Iterative Analysis Strategy

The AI uses a **4-pass exploration strategy** instead of loading all files at once:

### Pass 1: Structure Discovery 🔍

```
You: "Analyze flask_test_project and show project tree"

AI → get_project_tree("flask_test_project", max_depth=2)
Sees: Project structure, identifies entry points
```

### Pass 2: Strategic File Selection 🎯

```
AI decides: "This is a Flask app, read the main application file first"

AI → read_file("flask_test_project/src/flask/app.py")
Analyzes: Core application logic
```

### Pass 3: Deep Dive 🔬

```
You: "Check flask_test_project/src/flask/sansio/ for logic errors
      and linting issues"

AI → get_file_list("flask_test_project/src/flask/sansio/")
AI → read_multiple_files([list of Python files])
AI → search_in_files("flask_test_project/src/flask/sansio/",
                      "TODO|FIXME|XXX", [".py"])
```

### Pass 4: Report 📋

```
AI reports:
  ✓ Code quality: Well-structured module with type hints
  ✓ Linting: Follows PEP 8 conventions
  ⚠ Found 2 potential issues:
    1. Missing docstrings in some functions
    2. Complex conditional logic in request parsing
```

**Why this works**: Only reads necessary files, respects token limits, makes intelligent decisions.

---

## Practical Example: Analyzing Flask

### 1. Add Flask as submodule

```bash
cd day14
git submodule add https://github.com/pallets/flask.git flask_test_project
git submodule update --init
```

### 2. Start analysis

```bash
python chat.py
```

### 3. Example prompts

**Explore structure:**

```
You: Analyze flask_test_project and show project tree
AI: [Shows Flask project tree with src/, tests/, docs/]
```

**Find bugs:**

```
You: Check flask_test_project/src/flask/sansio/ for logic errors
     and linting issues
AI: [Analyzes sansio module for logic errors and linting issues]
```

**Architecture review:**

```
You: Explain the routing architecture in flask_test_project
AI: [Reads routing.py, app.py, explains decorator pattern]
```

**Search patterns:**

```
You: Find all deprecated API usage in flask_test_project
AI: [Uses search_in_files with deprecation patterns]
```

### 4. Choose the right model

- **Gemini 2.5 Flash** (default): General analysis, good balance
- **Gemini 2.5 Pro**: Deep analysis, complex codebases, security audits
- **Gemini 2.5 Flash Lite**: Quick structure checks

Change model: `/model` → select Pro for thorough analysis

---

## Smart Filtering

**Automatically ignores:**

- Build: `__pycache__`, `build/`, `dist/`, `*.pyc`
- Dependencies: `node_modules/`, `.venv/`, `venv/`
- IDE: `.idea/`, `.vscode/`, `.git/`
- Binary: `.jar`, `.class`, images, PDFs

**Supports:**

- Languages: Python, Kotlin, Java, JS/TS, Go, Rust, C/C++, C#, Ruby, PHP
- Config: YAML, JSON, XML, TOML, properties

**Size limits:**

- 100KB per file
- 500KB per multi-file request
- 100 max search results

---

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

Dependencies:

- `fastmcp` - MCP server/client framework
- `requests==2.31.0` - HTTP client for Gemini API
- `rich==13.7.0` - Terminal UI

---

## Commands

| Command     | Description                      |
|-------------|----------------------------------|
| `/help`     | Show available commands          |
| `/mcp`      | List filesystem tools            |
| `/model`    | Change AI model (Flash/Pro/Lite) |
| `/system`   | Customize AI behavior            |
| `/settings` | Adjust temperature, top-k, top-p |
| `/tokens`   | Show token usage stats           |
| `/clear`    | Clear conversation history       |
| `/quit`     | Exit                             |

---

## Use Cases

### 1. Project Structure Analysis

```
You: Analyze flask_test_project and show project tree
AI: Shows complete project tree with directory structure
    and file organization
```

### 2. Code Quality & Linting

```
You: Check flask_test_project/src/flask/sansio/ for logic errors
     and linting issues
AI: Analyzes Python code for logic errors, PEP 8 violations,
    code quality issues, and potential bugs
```

### 3. Security Audit

```
You: Check for SQL injection vulnerabilities in flask_test_project
AI: Scans for unsafe query construction and security issues
```

### 4. Architecture Review

```
You: Explain the design patterns used in flask_test_project
AI: Identifies factory, decorator, singleton patterns
```

### 5. Dependency Analysis

```
You: Show import structure of flask_test_project
AI: Maps module dependencies, finds circular imports
```

---

## MCP Integration

### Server (filesystem_server.py)

```python
from fastmcp import FastMCP

mcp = FastMCP("Filesystem Manager")


@mcp.tool()
def read_file(file_path: str) -> dict:
    """Read single file content."""
    # Implementation
    return {"success": True, "content": content}
```

### Client (filesystem_client.py)

```python
from mcp_clients import FilesystemClient

client = FilesystemClient()
await client.connect()
result = await client.read_file("path/to/file.py")
```

**Benefits:**

- Automatic schema generation
- Decorator-based tools
- Clean async patterns
- Minimal boilerplate

---

## Troubleshooting

### MCP Connection Failed

```bash
# Check server exists
ls mcp_servers/filesystem_server.py

# Test directly
python mcp_servers/filesystem_server.py

# Verify fastmcp installed
pip install fastmcp
```

### API Key Issues

```bash
# Set key
export GEMINI_API_KEY="your-key"

# Verify
echo $GEMINI_API_KEY
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt
```

---

## Advanced Features

### Custom System Instructions

```bash
/system
> 3. Enter new instruction

You are a security expert. Focus on:
- SQL injection
- XSS vulnerabilities
- Authentication issues
```

### Model Selection for Tasks

- **Flash Lite**: Quick structure checks
- **Flash**: General bug detection
- **Pro**: Security audits, deep analysis

### Conversation Management

- Auto-compression at 25K tokens (80% of 30K limit)
- Keeps 5 recent messages intact
- Summarizes older messages

---

## Project Structure

```
day14/
├── chat.py                  # Main interface
├── requirements.txt         # Dependencies
├── core/                    # Gemini client, conversation manager
├── mcp_clients/             # MCP client layer
├── mcp_servers/             # Filesystem MCP server (6 tools)
└── flask_test_project/      # Example: Flask submodule for analysis
```

---

## References

- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP specification
- [FastMCP Framework](https://github.com/jlowin/fastmcp) - FastMCP documentation
- [Google Gemini API](https://ai.google.dev/) - Gemini API docs
- [Flask](https://github.com/pallets/flask) - Example project for analysis

---

## License

Educational project for AI Advent Challenge
