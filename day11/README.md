# Day 11: Background Task Manager with MCP Integration

A 24/7 AI agent with background task management capabilities, cryptocurrency data integration, and Gemini AI-powered
summaries.

## Features

- **Background Task Management**: Create, schedule, and manage tasks that run automatically
- **Multiple MCP Servers**:
    - Crypto Data (CoinGecko API - no key required)
    - Background Task Management
- **AI-Powered Summaries**: Gemini AI generates intelligent summaries from raw data
- **Flexible Scheduling** (APScheduler-powered):
    - Interval-based (every N minutes/hours/days)
    - Daily at specific time
    - Weekly on specific day/time
    - Pause/resume tasks without losing schedule
    - Parallel task execution with thread pool
- **Persistent Storage**: SQLite database stores tasks and execution history
- **Rich Console UI**: Beautiful terminal interface with tables and colors
- **Smart Notifications**:
    - macOS native notifications with action buttons
    - Configurable levels: all, errors only, significant changes, or silent
    - AI-generated summaries (2-3 sentence insights)

## Architecture

```
day11/
├── core/                       # Base components from day10
│   ├── gemini_client.py       # Gemini API client
│   ├── conversation.py        # Conversation history management
│   └── text_manager.py        # Text utilities
├── mcp_servers/               # MCP server implementations
│   ├── crypto_server.py       # CoinGecko cryptocurrency data
│   └── background_server.py   # Task management interface
├── mcp_clients/               # MCP client implementations
│   ├── base.py                # Base FastMCP client
│   ├── crypto_client.py       # Crypto MCP client
│   ├── background_client.py   # Background MCP client
│   └── manager.py             # MCP connection manager
├── tasks/                     # Task management subsystem
│   ├── storage.py             # SQLite database (tasks + history)
│   ├── scheduler.py           # Legacy scheduler (schedule library)
│   └── scheduler_apscheduler.py # Production scheduler (APScheduler)
├── notifications/             # Notification system
│   └── macos_notifier.py      # macOS native notifications
└── chat.py                    # Main chat interface
```

### Key Components

**APScheduler-Based Task Execution**

- Uses `BackgroundScheduler` with `ThreadPoolExecutor` for parallel task execution
- Each task runs in a separate thread with its own event loop
- Thread-safe architecture with proper event loop isolation
- Automatic task recovery on restart

**MCP Architecture**

- FastMCP-based servers running as subprocesses
- Client manager handles multiple MCP server connections
- Thread-safe: each task execution creates temporary MCP connections in its thread context
- Supports crypto data and background task management tools

**Storage Layer**

- SQLite database for persistent task configuration
- Complete execution history with AI summaries
- Tracks success/failure rates, duration metrics, and timestamps

**AI Integration**

- Gemini 2.5 Flash for fast AI summaries (150 token limit)
- Prompt engineered for concise 2-3 sentence insights
- Temperature 0.7 for balanced creativity and accuracy
- Async execution for non-blocking task processing

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set your Gemini API key:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Usage

### Start the Agent

```bash
cd day11
python chat.py
```

### Task Management Commands

- `/tasks` - Show task management menu
- `/tasks list` - List all tasks
- `/tasks add` - Create a new task (interactive)
- `/tasks remove <id>` - Delete a task
- `/tasks start <id>` - Enable a task
- `/tasks stop <id>` - Disable a task
- `/tasks pause <id>` - Pause task (keeps it scheduled)
- `/tasks resume <id>` - Resume a paused task
- `/tasks run <id>` - Execute a task immediately
- `/tasks history <id>` - View execution history (last 20 runs)
- `/tasks result <id>` - Show latest result with AI summary
- `/tasks status` - View scheduler statistics and uptime

### Other Commands

- `/mcp [server]` - Show MCP servers and tools
- `/model` - Change Gemini model (Flash, Flash Lite, Pro)
- `/system` - Update system instruction
- `/settings` - Adjust generation settings (temperature, tokens, etc.)
- `/tokens` - Show token usage statistics
- `/compress` - Compress conversation history
- `/clear` - Clear conversation history
- `/help` - Show all available commands
- `/quit` - Exit

### Available MCP Tools

**Crypto Data Tools:**

- `get_crypto_prices` - Get top N cryptocurrency prices
- `get_crypto_by_symbol` - Get specific crypto by symbol (btc, eth, sol, etc.)
- `get_trending_crypto` - Get currently trending cryptocurrencies
- `get_market_summary` - Get global market summary and statistics

**Background Task Management Tools:**

- `create_background_task` - Create a new scheduled task
- `list_background_tasks` - List all tasks with their status
- `start_background_task` - Enable a task
- `stop_background_task` - Disable a task
- `remove_background_task` - Delete a task permanently
- `run_task_immediately` - Execute a task right now
- `get_latest_task_result` - Get most recent execution result
- `get_task_execution_history` - View task execution history
- `update_task_schedule` - Modify task schedule
- `get_scheduler_status` - Get scheduler statistics

## Examples

### Example 1: Create a Crypto Price Tracker

1. Run `/tasks add`
2. Follow the interactive prompts:
   ```
   Task name: Crypto Price Tracker
   Description: Track top 10 cryptocurrency prices
   Schedule type: [1] Interval
   Interval: 30 minutes
   MCP Tool: get_crypto_prices
   Tool arguments: {"limit": 10}
   AI Summary: Y
   Notification: [1] All
   ```

The task will now run every 30 minutes, fetch crypto prices, generate an AI summary, and display notifications!

### Example 2: Daily Market Summary

Create a task that runs every day at 9 AM:

```bash
/tasks add
# Enter:
Task name: Daily Crypto Summary
Description: Morning market overview
Schedule type: [2] Daily
Time: 09:00
MCP Tool: get_market_summary
Tool arguments: {}
AI Summary: Y
Notification: [1] All
```

### Example 3: Natural Language Task Creation

You can also create tasks using natural language with the AI:

```
You: Create a background task that checks Bitcoin price every hour
     and gives me an AI summary

AI: I'll create that task for you.
    [Creates task using create_background_task MCP tool]
    ✓ Task created successfully!
```

### Example 4: Monitor Trending Cryptos

Track what's trending in crypto every 2 hours with silent mode:

```
You: Monitor trending cryptocurrencies every 2 hours,
     save to history but don't notify me

AI: [Uses create_background_task with notification_level='silent']
    Task created and running in the background!
```

### Database Schema

**tasks table:**

```sql
- id (INTEGER PRIMARY KEY)
- name (TEXT)
- description (TEXT)
- schedule_type (TEXT): 'interval', 'daily', or 'weekly'
- schedule_value (TEXT): e.g., '30 minutes', '09:00', 'Monday 09:00'
- mcp_tool (TEXT): MCP tool name to execute
- tool_args (TEXT): JSON-encoded arguments
- use_ai_summary (INTEGER): 0 or 1
- notification_level (TEXT): 'all', 'errors', 'significant', 'silent'
- enabled (INTEGER): 0 or 1
- created_at (TEXT): ISO timestamp
- last_run (TEXT): ISO timestamp
- next_run (TEXT): ISO timestamp
```

**task_history table:**

```sql
- id (INTEGER PRIMARY KEY)
- task_id (INTEGER): Foreign key to tasks
- run_time (TEXT): ISO timestamp
- status (TEXT): 'success' or 'error'
- duration_ms (INTEGER): Execution time
- raw_data (TEXT): MCP tool output
- ai_summary (TEXT): AI-generated summary
- error_message (TEXT): Error details if failed
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
