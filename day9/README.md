# Day 9: MCP Integration with Gemini AI

Complete integration between MCP (Model Context Protocol) servers and Gemini AI, enabling Gemini to use various tools
through natural language commands. Supports multiple MCP servers simultaneously.

## Architecture

```
Multiple MCP Servers ←→ MCP Manager ←→ Python Client + Gemini AI
(fetch, browser, etc.)                      (chat.py)
```

## Features

- 🔌 **Multiple MCP Servers**: Connect to fetch (HTTP requests) and browser automation servers
- 🤖 **AI-Powered**: Uses Google Gemini 2.5 models for intelligent decision-making
- 🔧 **MCP Integration**: Full Model Context Protocol implementation with Python SDK
- 💬 **Interactive Chat**: Natural language interface for tool usage
- 📊 **Token Management**: Track and compress conversation history (from Day 8)
- ⚙️ **Customizable**: Adjustable model parameters and system instructions
- 🏗️ **Extensible**: Easy to add new MCP clients through modular architecture

## Prerequisites

1. **Python 3.10+** - For the application and MCP server
2. **Gemini API Key** - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)

## Installation

### 1. Install Python Dependencies

```bash
cd day9
pip install -r requirements.txt
```

This will install:

- `mcp-server-fetch` - HTTP fetch MCP server (no API key required)
- `mcp-server-browser-use` - Browser automation MCP server (requires ANTHROPIC_API_KEY)
- `mcp[cli]` - MCP Python SDK
- `requests` - HTTP library
- `rich` - Terminal UI

### 2. (Optional) Install Playwright Browsers

Only required if you want to use browser automation (requires ANTHROPIC_API_KEY):

```bash
python -m playwright install
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

The fetch server works without any additional setup!

### 3. Set up Environment

Create a `.env` file or set environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Usage

### Run the Chat Application

The MCP server starts automatically when you run the chat application:

```bash
cd day9
python chat.py
```

### Start Chatting!

**With Fetch MCP (HTTP requests):**

```
You: Fetch https://python.org and tell me what it's about
Assistant: [fetches page] Python.org is the official website for Python...

You: Get the latest news from https://news.ycombinator.com
Assistant: [fetches and parses] Here are the top stories...
```

**With Browser MCP (requires ANTHROPIC_API_KEY):**

```
You: Open google.com and search for "Python MCP"
Assistant: [executes browser commands] Done! I've navigated to Google and performed the search.
```

## Commands

| Command     | Description                                  |
|-------------|----------------------------------------------|
| `/mcp`      | Show MCP servers status and available tools  |
| `/model`    | Change Gemini model (Flash, Flash Lite, Pro) |
| `/system`   | View/change system instruction               |
| `/settings` | Adjust temperature, top-k, top-p, max tokens |
| `/tokens`   | Show detailed token usage statistics         |
| `/compress` | Manually compress conversation history       |
| `/clear`    | Clear conversation history                   |
| `/quit`     | Exit the application                         |
| `/help`     | Show help message                            |

## Available MCP Tools

Use `/mcp` command to see all connected servers and their tools.

### Fetch MCP Server (Always Available)

- **fetch** - Fetch web content and convert to markdown
    - Parameters: url, max_length, start_index, raw

### Browser MCP Server (Requires ANTHROPIC_API_KEY)

- **run_browser_agent** - Full browser automation with AI agent
    - **navigate** - Navigate to URLs
    - **click** - Click elements
    - **fill** - Fill forms
    - **extract** - Extract content
    - **screenshot** - Take screenshots
    - And more...

## Example Use Cases

### Fetch Web Content

```
You: Fetch https://github.com/modelcontextprotocol/servers and summarize what you find
You: Get me the content from https://python.org
```

### Extract Information

```
You: Fetch https://news.ycombinator.com and tell me the top 5 stories
```

### Browser Automation (Requires ANTHROPIC_API_KEY)

```
You: Search Google for "AI agent frameworks"
You: Go to example.com and fill out the contact form
You: Navigate to github.com and search for "fastmcp"
```

## Token Management

The application tracks token usage and can automatically compress conversation history when approaching context limits:

- **Max Context**: 30,000 tokens
- **Auto-compress**: Triggers at 80% usage (24,000 tokens)
- **Compression**: Uses Gemini to summarize older messages while keeping recent ones

## Configuration

### Generation Settings

Adjust AI behavior through `/settings`:

- **Temperature** (0.0-2.0): Controls randomness (default: 0.7)
- **Top K** (1-100): Limits vocabulary selection (default: 40)
- **Top P** (0.0-1.0): Nucleus sampling threshold (default: 0.95)
- **Max Output Tokens**: Maximum response length (default: 2048)

### Models

Three Gemini models available:

1. **Gemini 2.5 Flash** (Default) - Fast and balanced
2. **Gemini 2.5 Flash Lite** - Ultra-fast responses
3. **Gemini 2.5 Pro** - Most capable, slower

## Troubleshooting

### Fetch Server Not Connected

- Ensure `mcp-server-fetch` is installed: `pip install mcp-server-fetch`
- Verify Python 3.10+ is installed
- Check internet connection

### Browser Server Not Connected

- Install `mcp-server-browser-use`: `pip install mcp-server-browser-use`
- Set ANTHROPIC_API_KEY environment variable
- Install Playwright browsers: `python -m playwright install`

### API Errors

- Check your Gemini API key is valid
- Ensure you have API quota available
- Check internet connection

### Tools Not Working

- Use `/mcp` to verify which servers are connected
- Check that required API keys are set (ANTHROPIC_API_KEY for browser)
- Restart the chat application

## Project Structure

```
day9/
├── chat.py              # Main application with UI and orchestration
├── mcp_clients/         # MCP client implementations
│   ├── __init__.py      # Package exports
│   ├── base.py          # Base MCP client class
│   ├── browser_client.py # Browser automation client
│   ├── fetch_client.py  # HTTP fetch client
│   └── manager.py       # MCP manager for multiple servers
├── gemini_client.py     # Gemini API client with function calling
├── conversation.py      # Conversation history management
├── text_manager.py      # Token counting and text compression
├── requirements.txt     # Python dependencies
├── .flake8              # Code style configuration
└── README.md            # This file
```

## Implementation Details

### Function Calling Flow

1. User sends message to Gemini
2. Gemini decides if MCP tools are needed
3. If yes, Gemini returns function calls
4. Client executes tools via appropriate MCP server
5. Results sent back to Gemini
6. Gemini processes results and responds to user

### MCP Protocol

The application uses the Model Context Protocol (MCP) to communicate with multiple servers:

- **Transport**: stdio (standard input/output)
- **Servers**:
    - `mcp-server-fetch` - Python-based HTTP client
    - `mcp-server-browser-use` - Python-based browser automation
- **Client**: Python MCP SDK with custom manager for multiple servers

## References

- [MCP Protocol](https://modelcontextprotocol.io) - Official Model Context Protocol documentation
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) - Python SDK for MCP
- [mcp-server-fetch](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch) - HTTP fetch MCP server
- [mcp-server-browser-use](https://github.com/browser-use/mcp-server-browser-use) - Browser automation MCP server
- [Gemini API](https://ai.google.dev/docs) - Google Gemini AI documentation
- [Playwright](https://playwright.dev/python/) - Browser automation library

## License

Educational project for AI Advent Challenge
