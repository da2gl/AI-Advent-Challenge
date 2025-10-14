# Day 10: Apple Container MCP Server + Multi-MCP Management

Complete Apple Container management through MCP (Model Context Protocol) with Gemini AI integration. Built with **
FastMCP** framework for cleaner, more maintainable code. Features improved multi-server MCP command interface for better
scalability.

## Architecture

```
Apple Container CLI ←→ Container MCP Server ←→ MCP Manager ←→ Gemini AI Agent
                              ↓
                      Multiple MCP Servers
                      (Container, Fetch)
```

## Features

### Container Management via MCP

- 🐳 **Container Operations**: List, run, stop, start, inspect, logs, delete
- ⚙️ **System Management**: Start, stop, and check status of container system service
- 🔧 **Native Integration**: Uses Apple Container CLI directly
- 📊 **Structured Responses**: JSON-formatted results from all operations
- 🛡️ **Error Handling**: Comprehensive error messages and timeout protection

### Improved MCP Interface

- 📡 **Multi-Server Support**: Seamlessly manage multiple MCP servers
- 🎨 **Enhanced `/mcp` Command**:
    - `/mcp` - Show connected servers summary
    - `/mcp <server>` - Show specific server's tools
    - `/mcp all` - Show all tools from all servers
- 📋 **Better UX**: Table views, color coding, organized output
- 🔍 **Detailed Tool Info**: Parameters, types, descriptions for each tool

### AI Integration

- 🤖 **Gemini 2.5 Models**: Flash, Flash Lite, and Pro variants
- 💬 **Natural Language**: Control containers through conversational interface
- 🔄 **Function Calling**: Automatic tool selection and execution
- 📈 **Token Management**: History compression and tracking

## Prerequisites

1. **macOS** with Apple Silicon (arm64)
2. **Apple Container** - From [github.com/apple/container](https://github.com/apple/container) - Installed and system
   service started
3. **Python 3.10+**
4. **Gemini API Key** - From [Google AI Studio](https://makersuite.google.com/app/apikey)

### Install Apple Container

If not already installed:

```bash
# Clone and build from source
git clone https://github.com/apple/container.git
cd container
swift build -c release

# Or use Homebrew (if available)
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

This starts the background service required for container operations.

## Installation

### 1. Install Python Dependencies

```bash
cd day10
pip install -r requirements.txt
```

This installs:

- `fastmcp` - FastMCP framework for MCP servers and clients
- `requests` - HTTP library for Gemini API
- `rich` - Terminal UI formatting

### 2. Set up Environment

```bash
export GEMINI_API_KEY="your-gemini-api-key-here"
```

Or create a `.env` file (not included in repo).

## Usage

### Start the Chat Application

```bash
cd day10
python chat.py
```

The application will:

1. Connect to Container MCP server (local `mcp_servers/container_server.py`)
2. Connect to Fetch MCP server (local `mcp_servers/fetch_server.py`)
3. Start the interactive chat

### Commands

| Command         | Description                                             |
|-----------------|---------------------------------------------------------|
| `/mcp`          | Show connected MCP servers summary                      |
| `/mcp <server>` | Show tools for specific server (e.g., `/mcp container`) |
| `/mcp all`      | Show all tools from all servers with full details       |
| `/model`        | Change Gemini model (Flash, Flash Lite, Pro)            |
| `/system`       | View/change system instruction                          |
| `/settings`     | Adjust temperature, top-k, top-p, max tokens            |
| `/tokens`       | Show detailed token usage statistics                    |
| `/compress`     | Manually compress conversation history                  |
| `/clear`        | Clear conversation history                              |
| `/quit`         | Exit the application                                    |
| `/help`         | Show help message                                       |

### Example Interactions

#### Container Management

```
You: List all my containers
Assistant: [calls list_containers tool]
          You have 3 containers: nginx-web (running), postgres-db (stopped), redis-cache (running)

You: Run nginx container on port 8080
Assistant: [calls run_container tool]
          Started nginx container successfully! Running on port 8080
          Container ID: abc123def456

You: Show me the logs from nginx container
Assistant: [calls get_logs tool]
          [Displays last 100 lines of logs]

You: How many containers are currently running?
Assistant: [calls list_containers, analyzes results]
          You have 2 containers currently running: nginx-web and redis-cache
```

#### MCP Server Management

```
You: /mcp
📡 Connected MCP Servers (2):
  ✓ container - 10 tools | Container management
  ✓ fetch     - 2 tools  | HTTP fetch server

Use '/mcp <name>' for details

You: /mcp container
🔧 Container MCP Server
   Container management
   Available tools: 10
─────────────────────────
  • list_containers
    List all containers (running and stopped)
    Parameters:
      all (boolean): Show all containers

  • run_container
    Run a new container from an image
    Parameters:
    * image (string): Container image to run
      name (string): Optional name
      ports (string): Port mapping
      ...
```

#### Web Fetch + Containers

```
You: Fetch the nginx documentation and then run an nginx container
Assistant: [calls fetch tool, then run_container tool]
          I've fetched the nginx docs. Based on the documentation,
          I'm running an nginx container with recommended settings...
          Container started successfully on port 8080!
```

## Available Container Tools

The Container MCP server provides 10 tools:

### Container Operations

#### `list_containers`

List all containers (running and stopped)

- **Parameters**:
    - `all` (boolean) - Show all containers (default: true)

#### `run_container`

Run a new container from an image

- **Parameters**:
    - `image` (string, required) - Image to run (e.g., "nginx:latest")
    - `name` (string) - Optional container name
    - `detach` (boolean) - Run in background (default: true)
    - `ports` (string) - Port mapping (e.g., "8080:80")
    - `env` (array) - Environment variables (e.g., ["KEY=VALUE"])

#### `stop_container`

Stop a running container

- **Parameters**:
    - `container` (string, required) - Container ID or name

#### `start_container`

Start a stopped container

- **Parameters**:
    - `container` (string, required) - Container ID or name

#### `inspect_container`

Get detailed information about a container

- **Parameters**:
    - `container` (string, required) - Container ID or name

#### `get_logs`

Fetch logs from a container

- **Parameters**:
    - `container` (string, required) - Container ID or name
    - `tail` (integer) - Number of lines (default: 100)
    - `follow` (boolean) - Stream logs (default: false)

#### `delete_container`

Remove a container

- **Parameters**:
    - `container` (string, required) - Container ID or name
    - `force` (boolean) - Force delete running container (default: false)

### System Management

#### `start_system`

Start the Apple Container system service

This must be run before any container operations can be performed. The system service runs in the background and manages
container lifecycle.

- **Parameters**: None

#### `stop_system`

Stop the Apple Container system service

This will stop all running containers and shut down the system service.

- **Parameters**: None

#### `system_status`

Check the status of the Apple Container system service

- **Parameters**: None

## Use Cases

### 1. Development Environment Setup

```
You: Set up a postgres database for development
Assistant: → Runs postgres:15 container
          → Sets up with random secure password
          → Returns connection string
```

### 2. Quick Testing

```
You: I need nginx to serve my static files
Assistant: → Runs nginx container
          → Mounts local directory
          → Provides access URL
```

### 3. Container Debugging

```
You: Why is my redis container not responding?
Assistant: → Inspects container
          → Checks logs
          → Identifies issue (port conflict)
          → Suggests solution
```

### 4. Resource Monitoring

```
You: Which containers are using the most resources?
Assistant: → Lists all containers
          → Inspects each
          → Reports resource usage
```

## Project Structure

```
day10/
├── chat.py                      # Main application with improved MCP UI
├── mcp_servers/                 # MCP server implementations
│   ├── container_server.py      # Apple Container MCP server (FastMCP) - 10 tools
│   └── fetch_server.py          # HTTP fetch MCP server (FastMCP) - 2 tools
├── mcp_clients/                 # MCP client implementations
│   ├── __init__.py              # Package exports
│   ├── base.py                  # Base MCP client class (~180 lines)
│   ├── fetch_client.py          # HTTP fetch client (~50 lines)
│   ├── container_client.py      # Container management client (~50 lines)
│   └── manager.py               # MCP manager for multiple servers
├── gemini_client.py             # Gemini API client
├── conversation.py              # Conversation history management
├── text_manager.py              # Token counting and compression
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Implementation Details

### Built with FastMCP

This project uses **FastMCP** for both MCP servers and clients, eliminating the need for the vanilla MCP Python SDK.

#### MCP Server (Container Management)

The server uses the FastMCP framework for clean, maintainable code:

```python
from fastmcp import FastMCP

mcp = FastMCP("Apple Container Manager")


@mcp.tool()
def list_containers(all: bool = True) -> dict:
    """List all containers (running and stopped)."""
    result = run_container_command(["list", "--all" if all else ""])
    return {"success": True, "containers": result["output"]}


@mcp.tool()
def run_container(image: str, name: str = None, ports: str = None) -> dict:
    """Run a new container from an image."""
    # Automatically generates MCP Tool schema from type hints!
    ...


if __name__ == "__main__":
    mcp.run(show_banner=False)  # Disable ASCII art banner
```

**Benefits of FastMCP Server:**

- Automatic schema generation from Python type hints
- ~440 lines for 10 tools (container_server.py) with comprehensive functionality
- Cleaner, more Pythonic API
- Each tool is a simple decorated function
- Optional banner display (`show_banner=False` for cleaner output)

#### MCP Clients (Container, Fetch)

All MCP clients use FastMCP's Client API:

```python
from fastmcp import Client

# Connect to a local MCP server via stdio
self.client_context = Client({
    "mcpServers": {
        "container": {
            "command": "python",
            "args": ["mcp_servers/container_server.py"]
        }
    }
})
self.client = await self.client_context.__aenter__()

# List available tools
tools = await self.client.list_tools()

# Call a tool
result = await self.client.call_tool("list_containers", {"all": True})
```

**Benefits of FastMCP Client:**

- ~50 lines vs ~74 with vanilla MCP SDK (32% less code per client)
- Simple context manager pattern
- Automatic connection management
- Support for stdio, SSE, and in-memory transports
- Configuration-based server definitions

All commands are executed via Python `subprocess` with:

- 30-second timeout
- Proper error handling
- JSON-formatted responses

### Improved `/mcp` Command

Three display modes:

1. **Summary** (`/mcp`): Table view of all connected servers
2. **Specific** (`/mcp <server>`): Detailed tools for one server
3. **All** (`/mcp all`): Complete details for all servers

### MCP Manager Enhancement

The manager now automatically routes tool calls to the correct server:

```python
# No need to specify server - manager finds the right one
result = await mcp_manager.call_tool("list_containers", {})
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

### Container MCP Server Not Connecting

- Verify `mcp_servers/container_server.py` exists
- Check Python path: `which python`
- Try running server directly: `python mcp_servers/container_server.py`

### Permission Errors

Container operations may require proper permissions. Ensure:

- Your user has access to container operations
- Container system service is running
- macOS security settings allow container operations

### API Errors

- Verify GEMINI_API_KEY is set and valid
- Check API quota at [Google AI Studio](https://makersuite.google.com/)
- Ensure internet connection is stable

## Advanced Features

### Multiple Container Operations

The AI can chain multiple container operations:

```
You: Set up a complete web stack
Assistant:
  1. Running postgres container...
  2. Running redis container...
  3. Running nginx container...
  4. Configuring network between containers...
  All services are up! Here are the details...
```

### Smart Container Management

The AI understands container relationships:

```
You: My web app isn't connecting to the database
Assistant:
  Let me check:
  1. Inspecting web container... [running]
  2. Inspecting postgres container... [stopped]

  The issue is that your database container is stopped.
  Would you like me to start it?
```

## References

- [Apple Container](https://github.com/apple/container) - Official repository
- [FastMCP](https://gofastmcp.com) - FastMCP framework for MCP servers and clients
- [Gemini API](https://ai.google.dev/docs) - Google Gemini AI documentation

## License

Educational project for AI Advent Challenge
