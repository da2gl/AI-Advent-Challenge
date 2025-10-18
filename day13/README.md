# Day 13: Environment - AI Agent with Real Container Control

**Challenge**: Connect an AI agent with a real environment, enable Docker/container management, and run applications in
controlled environments.

**Result**: An AI assistant that can autonomously manage Apple Containers on macOS through natural language
conversation, demonstrating the power of AI agents interacting with real infrastructure.

## Overview

This project implements a sophisticated multi-MCP (Model Context Protocol) integration that connects Google's Gemini AI
with real container environments. The AI agent can understand natural language commands and execute container
operations, fetch web content, and interact with real infrastructure—all through conversational interaction.

**Building on Day 10**: This implementation extends the Day 10 container management system with improved architecture,
better MCP integration, and enhanced user experience.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Console Chat Interface                    │
│                   (chat.py - Rich UI)                        │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
      ┌────────────────┐            ┌─────────────────┐
      │  Gemini Client │            │   MCP Manager   │
      │  (AI Engine)   │            │  (Multi-Client) │
      └────────────────┘            └────────┬────────┘
                                             │
                     ┌───────────────────────┼──────────────────┐
                     ▼                       ▼                  ▼
              ┌──────────────┐      ┌──────────────┐   ┌──────────────┐
              │ Container MCP│      │  Fetch MCP   │   │  Future MCP  │
              │   Client     │      │   Client     │   │   Clients    │
              └──────┬───────┘      └──────┬───────┘   └──────────────┘
                     │                     │
                     ▼                     ▼
              ┌──────────────┐      ┌──────────────┐
              │ Container    │      │  HTTP Fetch  │
              │ MCP Server   │      │  MCP Server  │
              └──────┬───────┘      └──────────────┘
                     │
                     ▼
              ┌───────────────┐
              │Apple Container│
              │    System     │
              └───────────────┘
```

## Key Features

### 🤖 AI-Powered Container Management

- **Natural Language Interface**: Control containers through conversation
- **Autonomous Decision-Making**: AI makes intelligent choices about infrastructure
- **Multi-Turn Conversations**: Context-aware interactions with memory
- **Function Calling**: Automatic tool selection and execution

### 🐳 Comprehensive Container Operations

- **System Control**: Start/stop container system service
- **Container Lifecycle**: Run, stop, start, delete containers
- **Monitoring**: List containers, inspect details, view logs
- **Networking**: Automatic IP address detection and reporting
- **Image Support**: Run containers from any compatible image

### 🌐 HTTP Fetch Capabilities

- **Web Content Fetching**: Retrieve content from any URL
- **Robots.txt Compliance**: Respects website access rules
- **HTML Conversion**: Automatic HTML to text for AI processing
- **Pagination Support**: Handle large content efficiently
- **Metadata Requests**: HTTP HEAD for headers-only

### 💬 Advanced Chat Features

- **Multiple Models**: Gemini 2.5 Flash, Flash Lite, and Pro
- **Conversation Compression**: Automatic context management to stay within limits
- **Token Tracking**: Real-time usage monitoring and statistics
- **Custom System Instructions**: Configure AI behavior and personality
- **Generation Settings**: Fine-tune temperature, Top-K, Top-P, max tokens
- **Rich Terminal UI**: Beautiful formatting with colors and tables

## Project Structure

```
day13/
├── chat.py                      # Main console chat interface
├── requirements.txt             # Python dependencies
├── .flake8                      # Code quality configuration
├── core/                        # Core components from day10
│   ├── __init__.py              # Package exports
│   ├── conversation.py          # Conversation history manager
│   ├── gemini_client.py         # Gemini API client
│   └── text_manager.py          # Text processing utilities
├── mcp_clients/                 # MCP client implementations
│   ├── __init__.py              # Package exports
│   ├── base.py                  # Base MCP client interface
│   ├── container_client.py      # Container MCP client
│   ├── fetch_client.py          # HTTP fetch MCP client
│   └── manager.py               # Multi-MCP manager
└── mcp_servers/                 # MCP server implementations
    ├── __init__.py              # Package exports
    ├── container_server.py      # Apple Container MCP server (10 tools)
    └── fetch_server.py          # HTTP fetch MCP server (2 tools)
```

## Prerequisites

1. **macOS** with Apple Silicon (arm64) or Intel
2. **Apple Container** installed and configured
3. **Python 3.10+**
4. **Gemini API Key** from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Install Apple Container

```bash
# Clone and build from source
git clone https://github.com/apple/container.git
cd container
swift build -c release

# Or use Homebrew if available
brew install apple-container
```

Verify installation:

```bash
container --version
# Should show: container CLI version 0.5.0 or later
```

### Start Container System Service

**IMPORTANT**: Before running the chat application:

```bash
container system start
```

This starts the background service required for all container operations.

## Installation

### 1. Install Dependencies

```bash
cd day13
pip install -r requirements.txt
```

Dependencies installed:

- `fastmcp` - FastMCP framework for MCP servers and clients
- `requests==2.31.0` - HTTP library for Gemini API
- `rich==13.7.0` - Terminal UI formatting and colors

### 2. Configure Environment

```bash
export GEMINI_API_KEY="your-gemini-api-key-here"
```

Or the application will prompt you to enter it at startup.

## Usage

### Start the Application

```bash
python chat.py
```

The application will:

1. Connect to Container MCP server (manages Apple Containers)
2. Connect to Fetch MCP server (handles HTTP requests)
3. Display welcome screen with available commands
4. Start interactive chat interface

### Available Commands

| Command         | Description                                             |
|-----------------|---------------------------------------------------------|
| `/help`         | Show help and available commands                        |
| `/mcp`          | Show connected MCP servers summary                      |
| `/mcp <server>` | Show tools for specific server (e.g., `/mcp container`) |
| `/mcp all`      | Show all tools from all servers with full details       |
| `/model`        | Change AI model (Flash, Flash Lite, Pro)                |
| `/system`       | View/change system instruction                          |
| `/settings`     | Adjust temperature, top-k, top-p, max tokens            |
| `/tokens`       | Show detailed token usage statistics                    |
| `/compress`     | Manually compress conversation history                  |
| `/clear`        | Clear conversation history                              |
| `/quit`         | Exit the application                                    |

### Example Conversations

#### Starting Container System

```
You: Start the container system
Assistant: 🔧 Calling tool: start_system
✓ Tool executed successfully
Container system service started successfully
```

#### Running a Container

```
You: Run an nginx container named web-server on port 8080
Assistant: 🔧 Calling tool: run_container
Arguments: {
  "image": "nginx:latest",
  "name": "web-server",
  "detach": true,
  "ports": "8080:80"
}
✓ Tool executed successfully
Successfully started container from image 'nginx:latest' at 192.168.127.2
Container ID: abc123def456
```

#### Listing Containers

```
You: Show me all my containers
Assistant: 🔧 Calling tool: list_containers
✓ Tool executed successfully

CONTAINER ID    IMAGE           STATUS    NAME
abc123def456    nginx:latest    running   web-server
def789abc123    postgres:15     stopped   my-database
```

#### Inspecting Container

```
You: What's the IP address of my web-server container?
Assistant: 🔧 Calling tool: inspect_container
Arguments: {
  "container": "web-server"
}
✓ Tool executed successfully

Your web-server container is running at IP address 192.168.127.2
Status: running
Image: nginx:latest
```

#### Fetching Web Content

```
You: Fetch the latest documentation from https://nginx.org
Assistant: 🔧 Calling tool: fetch
Arguments: {
  "url": "https://nginx.org",
  "max_length": 5000
}
✓ Tool executed successfully

I've fetched the nginx documentation. Here's a summary:
[... content displayed ...]
```

#### Multi-Step Operations

```
You: Set up a PostgreSQL database and show me how to connect to it
Assistant: 🔧 Calling tool: run_container
Arguments: {
  "image": "postgres:15",
  "name": "dev-db",
  "detach": true,
  "env": ["POSTGRES_PASSWORD=secretpass"]
}
✓ Successfully started PostgreSQL container

🔧 Calling tool: inspect_container
Arguments: {
  "container": "dev-db"
}
✓ Retrieved container information

I've set up a PostgreSQL database for you. Here's how to connect:

Container: dev-db
IP Address: 192.168.127.5
Port: 5432
Username: postgres
Password: secretpass

Connection string: postgresql://postgres:secretpass@192.168.127.5:5432/postgres
```

## MCP Servers & Tools

### Container MCP Server (10 tools)

#### Container Lifecycle

1. **list_containers** - List all containers (running and stopped)
2. **run_container** - Run new container from image
    - Supports: name, ports, environment variables, detach mode
3. **stop_container** - Stop running container
4. **start_container** - Start stopped container
5. **delete_container** - Remove container (with force option)

#### Monitoring & Inspection

6. **inspect_container** - Get detailed container information
    - Returns: IP address, status, image, configuration
7. **get_logs** - Fetch container logs
    - Options: tail count, follow mode

#### System Management

8. **start_system** - Start container system service
9. **stop_system** - Stop container system service
10. **system_status** - Check system service status

### Fetch MCP Server (2 tools)

1. **fetch** - HTTP GET request with content processing
    - robots.txt compliance
    - HTML to text conversion
    - Content pagination
    - Configurable timeout
2. **fetch_head** - HTTP HEAD request for metadata
    - Returns headers and status code

## Technical Details

### Gemini AI Models

The application supports three Gemini 2.5 models:

- **Gemini 2.5 Flash** (default): Fast and balanced for most tasks
- **Gemini 2.5 Flash Lite**: Ultra-fast responses, lighter processing
- **Gemini 2.5 Pro**: Most advanced, highest quality outputs

Change models anytime with `/model` command.

### Conversation Management

**Token Limits**:

- Max Context: 30,000 tokens
- Safe Threshold: 25,000 tokens (80%)
- Auto-compression triggers at threshold

**Compression Strategy**:

- Keeps 5 most recent messages intact
- Summarizes older messages using Gemini
- Maintains conversation coherence
- Can save 50-80% of tokens

### Generation Settings

Configurable via `/settings`:

- **Temperature**: 0.7 (0.0-2.0) - Controls randomness
- **Top K**: 40 (1-100) - Limits token selection pool
- **Top P**: 0.95 (0.0-1.0) - Nucleus sampling threshold
- **Max Output Tokens**: 2048 - Maximum response length

### MCP Integration with FastMCP

This project uses **FastMCP** framework for clean, maintainable MCP implementation:

#### Server Example

```python
from fastmcp import FastMCP

mcp = FastMCP("Apple Container Manager")


@mcp.tool()
def list_containers(all: bool = True) -> dict:
    """List all containers (running and stopped)."""
    result = run_container_command(["list", "--all" if all else ""])
    return {"success": True, "containers": result["output"]}


if __name__ == "__main__":
    mcp.run(show_banner=False)
```

#### Client Example

```python
from fastmcp import Client

self.client_context = Client({
    "mcpServers": {
        "container": {
            "command": "python",
            "args": ["mcp_servers/container_server.py"]
        }
    }
})
self.client = await self.client_context.__aenter__()
result = await self.client.call_tool("list_containers", {"all": True})
```

**Benefits**:

- Automatic schema generation from type hints
- ~50 lines per client vs ~74 with vanilla MCP SDK (32% reduction)
- Simple decorator-based tool definitions
- Clean context manager pattern

## Use Cases

### 1. Development Environment Setup

```
You: Set up a complete development environment with postgres and redis
Assistant: → Runs postgres:15 container with secure password
          → Runs redis:latest container
          → Configures networking
          → Returns connection details for both
```

### 2. Quick Testing

```
You: I need to test my static website, can you help?
Assistant: → Runs nginx container
          → Provides URL to access
          → Shows logs for debugging
```

### 3. Container Debugging

```
You: My application container keeps crashing, help me debug it
Assistant: → Inspects container status
          → Checks recent logs
          → Identifies error pattern
          → Suggests fix (port conflict, missing env var, etc.)
```

### 4. Resource Monitoring

```
You: Show me all running containers and their status
Assistant: → Lists all containers
          → Filters for running ones
          → Displays status table
          → Reports IP addresses
```

### 5. Multi-Service Orchestration

```
You: Deploy a web stack with nginx, postgres, and redis
Assistant: → Runs postgres container
          → Runs redis container
          → Runs nginx container
          → Verifies all are running
          → Provides connection info for each
```

## Code Quality

This project maintains high code quality standards:

- ✅ **Linting**: flake8 compliant (no warnings)
- ✅ **Type Hints**: Comprehensive type annotations
- ✅ **Docstrings**: Full documentation for all functions
- ✅ **Error Handling**: Robust exception management
- ✅ **Async/Await**: Proper async patterns throughout
- ✅ **Modularity**: Clean separation of concerns

Run quality checks:

```bash
python -m flake8 .
python -m py_compile chat.py core/*.py mcp_clients/*.py
```

## Troubleshooting

### Container System Not Started

```
Error: XPC connection error: Connection invalid
```

**Solution**: Start the container system service:

```bash
container system start
```

### MCP Server Connection Failed

- Verify `mcp_servers/container_server.py` exists
- Check Python path: `which python`
- Run server directly to test: `python mcp_servers/container_server.py`

### Permission Errors

Ensure:

- Your user has container operation permissions
- Container system service is running
- macOS security settings allow container operations

### API Key Issues

```bash
# Verify API key is set
echo $GEMINI_API_KEY

# Test API key validity
curl -H "Content-Type: application/json" \
     -d '{"contents":[{"parts":[{"text":"test"}]}]}' \
     "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$GEMINI_API_KEY"
```

### Import Errors

If you see `ModuleNotFoundError`:

```bash
# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
python -c "from fastmcp import FastMCP; print('FastMCP OK')"
python -c "from rich import Console; print('Rich OK')"
```

## Advanced Features

### Smart Context Management

The AI automatically compresses conversation history when approaching token limits, preserving recent context while
summarizing older messages.

### Multi-Tool Coordination

The AI can chain multiple tool calls to accomplish complex tasks:

```
You: Check if any containers are running, stop them, and clean up
Assistant: → Lists containers (finds 3 running)
          → Stops all 3 containers
          → Deletes stopped containers
          → Confirms cleanup complete
```

### Error Recovery

The AI handles errors gracefully:

```
You: Run a container named web that already exists
Assistant: → Attempts to run container
          → Receives error (name conflict)
          → Suggests using different name or deleting existing
```

## References

- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP specification
- [FastMCP Framework](https://github.com/jlowin/fastmcp) - FastMCP documentation
- [Google Gemini API](https://ai.google.dev/) - Gemini API docs
- [Apple Container](https://github.com/apple/container) - Container system
- [Rich Library](https://rich.readthedocs.io/) - Terminal formatting

## License

Educational project for AI Advent Challenge
