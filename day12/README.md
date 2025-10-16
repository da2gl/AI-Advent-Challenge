# Day 12: MCP Tool Chaining Agent

Interactive chat with Gemini AI that can automatically chain MCP tools together via `/pipeline` command.

## Overview

This project combines **interactive chat** with **automatic tool chaining**:

- **Regular Chat**: Talk with Gemini, use individual MCP tools
- **Pipeline Mode** (`/pipeline`): Agent automatically chains tools to complete complex tasks

```
/pipeline Analyze Bitcoin and save report
    ↓
Get Crypto Data → AI Analysis → Save File → Notification ✅
```

The agent intelligently decides which tools to call, in what order, and how to combine their results.

## Features

- **Automatic Tool Chaining**: Gemini AI decides which tools to call and when
- **Cryptocurrency Analysis**: Analyze Bitcoin, Ethereum, and other cryptocurrencies
- **File Management**: Automatically save analysis results to files
- **macOS Notifications**: Get notified when pipeline tasks complete
- **Multi-MCP Integration**: Combines crypto data tools with pipeline tools

## Architecture

```
┌─────────────────┐
│  Pipeline Agent │  ← Gemini AI orchestrates everything
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼────┐
│Crypto│  │Pipeline│  ← MCP Servers
│Server│  │Server │
└───┬──┘  └──┬────┘
    │        │
    ▼        ▼
 [Tools]  [Tools]
```

### MCP Servers

#### 1. Crypto Server (from day11)

- `get_crypto_by_symbol(symbol)` - Get detailed crypto data
- `get_crypto_prices(limit)` - Get top cryptocurrencies
- `get_trending_crypto()` - Get trending coins
- `get_market_summary()` - Get global market data

#### 2. Pipeline Server (new)

- `summarize(text, max_length)` - Summarize text
- `saveToFile(content, filename)` - Save content to file
- `readFile(filename)` - Read file content

## Installation

```bash
cd day12

# Install dependencies
pip install -r requirements.txt

# Set your Gemini API key
export GEMINI_API_KEY='your-api-key-here'
```

## Usage

### Interactive Chat (Main)

Start the interactive chat interface:

```bash
python chat.py
```

**Regular chat**:

```
You: What is Bitcoin's current price?
Assistant: [Uses crypto MCP tool to get price]
```

**Pipeline mode** (automatic tool chaining):

```
You: /pipeline Analyze Bitcoin and save detailed report to btc_analysis.md
🚀 Running pipeline...
→ Calling tool: get_crypto_by_symbol
  ✓ Tool executed successfully
→ Calling tool: saveToFile
  ✓ Tool executed successfully
✓ Pipeline completed!
✓ Report saved as markdown with formatting!
```

### Demo Mode (Optional)

Run pre-configured demonstration scenarios:

```bash
python main.py demo
```

This will execute 4 example pipelines without interaction.

### Programmatic Usage

```python
from agent import PipelineAgent
import asyncio


async def main():
    agent = PipelineAgent(api_key="your-key", enable_notifications=True)

    await agent.connect_servers()

    result = await agent.execute_task(
        "Analyze Bitcoin price and save report to btc_analysis.txt"
    )

    await agent.disconnect_servers()
    agent.close()


asyncio.run(main())
```

## How It Works

### Tool Chaining Process

1. **User provides high-level task**
   ```
   "Analyze Bitcoin and save report"
   ```

2. **Gemini AI breaks it down**
    - Call `get_crypto_by_symbol("btc")` to get data
    - Analyze the data using AI reasoning
    - Call `saveToFile(analysis, "bitcoin_analysis.txt")`

3. **Agent executes the chain**
   ```
   Crypto Data → AI Analysis → File Save → Notification
   ```

4. **User gets notified**
    - macOS notification when task completes
    - Report saved in `output/` directory

### Example Pipeline Execution

```
Task: "Analyze Bitcoin and save to report.txt"

→ Calling tool: get_crypto_by_symbol
  Arguments: {"symbol": "btc", "currency": "usd"}
  ✓ Tool executed successfully

→ Agent analyzes the data using Gemini AI

→ Calling tool: saveToFile
  Arguments: {
    "content": "Bitcoin Analysis Report...",
    "filename": "bitcoin_analysis.txt"
  }
  ✓ Tool executed successfully

✓ Task completed!
✓ Notification sent
```

## Output

Results are saved in the `output/` directory:

```
output/
├── bitcoin_analysis.md      # Formatted markdown report
├── top_crypto_comparison.md # With tables and lists
├── trending_crypto.md        # Structured analysis
└── market_overview.md        # Market stats formatted
```

All reports are formatted markdown with:

- `## Headers` for sections
- **Bold** for emphasis
- Lists for data points
- Proper structure and readability

## Project Structure

```
day12/
├── chat.py                    # Main: Interactive chat interface ⭐
├── agent.py                   # Pipeline orchestrator (used by /pipeline)
├── main.py                    # Demo mode (optional)
├── core/                      # Core utilities
│   ├── gemini_client.py      # Gemini API client
│   ├── conversation.py       # Conversation management
│   └── text_manager.py       # Text utilities
├── mcp_servers/              # MCP servers
│   ├── crypto_server.py      # Cryptocurrency data
│   └── pipeline_server.py    # File operations
├── mcp_clients/              # MCP clients
│   ├── manager.py            # Client manager
│   ├── crypto_client.py      # Crypto client
│   └── pipeline_client.py    # Pipeline client
├── notifications/            # Notification system
│   └── macos.py             # macOS notifications (improved!)
├── .flake8                   # Linter config
├── requirements.txt
└── README.md
```

### Architecture

```
chat.py (Main Interface)
  ├─> Regular chat: Direct Gemini + MCP tools
  └─> /pipeline command → agent.py
                           └─> Automatic tool chaining
                           └─> macOS notifications
```

## Key Concepts

### Model Context Protocol (MCP)

MCP allows AI systems to securely connect to external tools and data sources. Each server exposes tools that the AI can
call.

### Tool Chaining

Instead of manually calling tools in sequence, the agent uses Gemini's function calling to automatically:

1. Decide which tools to call
2. Determine the order of calls
3. Pass data between tools
4. Create final result

### Benefits

- **Automation**: No manual orchestration needed
- **Intelligence**: AI decides the best tool chain
- **Flexibility**: Same agent handles different tasks
- **Reliability**: Built-in error handling and retries

## Advanced Usage

### Custom Tool Chains

Create custom pipelines by adding new tools to either server:

```python
# In pipeline_server.py
@mcp.tool()
def custom_analysis(data: str) -> str:
    """Your custom analysis logic."""
    # Implement your tool
    return result
```

### Multi-Step Pipelines

The agent can handle complex multi-step workflows:

```python
await agent.execute_task(
    "Get Bitcoin and Ethereum data, compare them, "
    "create a comparative analysis, and save to comparison.txt"
)
```

## Troubleshooting

### API Key Issues

```bash
# Check if API key is set
echo $GEMINI_API_KEY

# Set it if not
export GEMINI_API_KEY='your-key-here'
```

### MCP Connection Errors

- Ensure all Python dependencies are installed
- Check that server files are in `mcp_servers/` directory
- Verify Python executable path is correct

### Notification Issues

- Notifications only work on macOS
- Check System Preferences → Notifications settings
- Ensure Terminal/Python has notification permissions

## Chat Commands

Available commands in `chat.py`:

| Command            | Description             | Example                                 |
|--------------------|-------------------------|-----------------------------------------|
| `/pipeline <task>` | Run pipeline agent      | `/pipeline Analyze BTC and save report` |
| `/mcp`             | Show MCP servers status | `/mcp`                                  |
| `/model`           | Change AI model         | `/model`                                |
| `/tokens`          | Show token usage        | `/tokens`                               |
| `/clear`           | Clear conversation      | `/clear`                                |
| `/help`            | Show help               | `/help`                                 |
| `/quit`            | Exit chat               | `/quit`                                 |

## Examples

### Example 1: Regular Chat

```
You: What is Bitcoin's current price?
Assistant: [Uses get_crypto_by_symbol tool]
The current Bitcoin price is $111,507 USD...
```

### Example 2: Pipeline - Bitcoin Analysis

```
You: /pipeline Get current Bitcoin data and create detailed analysis. Save to bitcoin_report.md

🚀 Running pipeline: Get current Bitcoin data...
→ Calling tool: get_crypto_by_symbol
→ Calling tool: saveToFile
✓ Pipeline completed in 3 iterations!
✓ macOS Notification sent!
✓ Report saved as formatted markdown!
```

### Example 3: Pipeline - Market Comparison

```
You: /pipeline Compare top 5 cryptocurrencies and save comparison to top_5.md

→ Calling tool: get_crypto_prices
→ Calling tool: saveToFile
✓ Pipeline completed!
✓ Markdown report with tables and formatting!
```

### Example 4: Direct Tool Usage

```
You: Show me trending cryptocurrencies
Assistant: [Calls get_trending_crypto automatically]
Here are the currently trending coins...
```

## References

### Core Technologies

- [FastMCP](https://gofastmcp.com) - FastMCP framework for MCP servers and clients
- [Gemini API](https://ai.google.dev/docs) - Google Gemini AI documentation
- [APScheduler](https://apscheduler.readthedocs.io/) - Advanced Python Scheduler library
- [Rich](https://rich.readthedocs.io/) - Rich text and beautiful formatting in terminal

### APIs

- [CoinGecko API](https://www.coingecko.com/en/api) - Free cryptocurrency data API (no key required)

## License

Educational project for AI Advent Challenge
