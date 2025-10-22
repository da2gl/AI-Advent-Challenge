# Day 16: AI Agent with Long-term Memory (SQLite)

Gemini chat agent with persistent conversation storage using SQLite database.

## Features

- **SQLite Persistence**: All conversations automatically saved to database
- **Multiple Dialogs**: Work with multiple conversation threads
- **Auto-save**: Every message is automatically saved
- **Auto-cleanup**: Empty dialogs automatically deleted on startup
- **Resume Dialogs**: Load and continue any previous conversation
- **Dialog Management**: Create, delete, and switch between dialogs
- **Token Management**: Track and compress conversation history
- **Model Selection**: Choose between Gemini 2.5 Flash, Lite, or Pro
- **Rich Interface**: Beautiful console UI with tables and formatting

## Architecture

```
day16/
├── data/
│   └── conversations.db          # SQLite database (auto-created)
├── core/
│   ├── storage.py                # SQLite storage manager
│   ├── conversation.py           # Conversation history with persistence
│   ├── gemini_client.py          # Gemini API client
│   └── text_manager.py           # Token management utilities
├── chat.py                       # Main chat interface
└── requirements.txt
```

## Database Schema

### dialogs table
- `id` - Primary key
- `title` - Dialog title (auto-generated from first message)
- `created_at` - Creation timestamp
- `last_updated` - Last activity timestamp
- `model` - Gemini model used
- `message_count` - Number of messages

### messages table
- `id` - Primary key
- `dialog_id` - Foreign key to dialogs
- `timestamp` - Message timestamp
- `role` - 'user' or 'model'
- `content` - Message text
- `tokens` - Token count

## Installation

```bash
cd day16
pip install -r requirements.txt
```

Set your Gemini API key:
```bash
export GEMINI_API_KEY='your-api-key-here'
```

## Usage

```bash
python chat.py
```

## Commands

### Dialog Management
- `/resume` - Show list of all dialogs and load selected one
- `/clear` - Delete current dialog and create a new one (no confirmation)

### Model & Settings
- `/model` - Change Gemini model
- `/system` - Set system instruction
- `/settings` - Adjust generation parameters (temperature, top_k, etc.)

### History Management
- `/compress` - Compress conversation history to save tokens
- `/tokens` - View token usage statistics

### Utility
- `/help` - Show help message
- `/quit` - Exit application

## Workflow

1. **Start**: Always creates a new dialog automatically
2. **Chat**: All messages are auto-saved to SQLite
3. **Resume**: Use `/resume` to load any previous dialog
4. **Clear**: Use `/clear` to delete current and start fresh
5. **Exit**: All data persists in database

## Example Session

### First Run - New Dialog Created Silently
```bash
$ python chat.py

═══════════════════════════════════════════════════
     GEMINI CHAT - AI Assistant
═══════════════════════════════════════════════════
Commands:
  /resume   - Load previous dialog
  /clear    - Delete current dialog & create new
  /model    - Change model
  /compress - Compress conversation history
  /quit     - Exit chat
═══════════════════════════════════════════════════
Dialog #1: Untitled
Messages: 0
Model: Gemini 2.5 Flash (Fast & Balanced)
═══════════════════════════════════════════════════

You: Write a Python function for authentication
Assistant: [AI response here]

You: /quit
Goodbye!
```

### Second Run - Loading Previous Dialog
```bash
$ python chat.py

You: /resume

═══════════════════════════════════════════════════════════════════════
              AVAILABLE DIALOGS
═══════════════════════════════════════════════════════════════════════
  #    Title                                    Messages   Updated
─────────────────────────────────────────────────────────────────────────
  1    Write a Python function for authen...       2      just now
  2    [✓] Untitled                                0      just now
═══════════════════════════════════════════════════════════════════════

Select dialog number (or press Enter to cancel): 1

✓ Loaded dialog #1: Write a Python function for authen...
📝 History restored: 2 messages

You: Let's continue working on this
```

### Clearing Dialog
```bash
You: /clear

You: Starting fresh conversation
# Dialog deleted and new one created silently
```

## Key Features Explained

### Automatic Persistence
Every message is automatically saved to SQLite database:
- No manual save required
- Data survives program restarts
- Multiple dialogs stored independently

### Dialog Lifecycle
1. **Auto-cleanup**: Empty dialogs from previous sessions deleted on startup
2. **Creation**: New dialog created silently on every start
3. **Auto-naming**: First user message becomes dialog title (truncated to 50 chars)
4. **Resume**: Only shows dialogs with messages (empty dialogs hidden)
5. **Delete**: `/clear` removes dialog instantly and creates new one (no confirmation)

### Smart Token Management
- Automatic token counting per message
- Context usage tracking with progress bar
- Auto-compression when approaching token limits
- Manual compression with `/compress` command

### Database Benefits
- **ACID transactions**: Data integrity guaranteed
- **Indexed queries**: Fast dialog and message retrieval
- **Foreign keys**: Automatic cascade delete
- **Timestamps**: Track dialog activity

## Implementation Details

### SQLite Schema
```sql
CREATE TABLE dialogs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    model TEXT,
    message_count INTEGER DEFAULT 0
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dialog_id INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    tokens INTEGER DEFAULT 0,
    FOREIGN KEY (dialog_id) REFERENCES dialogs(id) ON DELETE CASCADE
);

CREATE INDEX idx_messages_dialog ON messages(dialog_id, timestamp);
```

### Storage Manager API
```python
from core.storage import SQLiteStorage

storage = SQLiteStorage("data/conversations.db")

# Create dialog
dialog_id = storage.create_dialog(model="gemini-2.5-flash")

# Save message
storage.save_message(dialog_id, role="user", content="Hello", tokens=5)

# Load dialog
messages = storage.load_dialog(dialog_id)

# List all dialogs
dialogs = storage.list_dialogs()

# Delete dialog
storage.delete_dialog(dialog_id)
```

### Conversation History Integration
```python
from core.conversation import ConversationHistory
from core.storage import SQLiteStorage

storage = SQLiteStorage()
conversation = ConversationHistory(storage, dialog_id=1)

# Messages auto-save to SQLite
conversation.add_user_message("Hello")
conversation.add_assistant_message("Hi there!")

# Load from storage
conversation.load_from_storage(dialog_id=1)
```

## Comparison with Claude Code

| Feature | Day 16 Implementation | Claude Code |
|---------|----------------------|-------------|
| **Startup** | Always creates new dialog | Offers to resume last |
| **Persistence** | SQLite database | Unknown (not documented) |
| **Dialog Management** | `/resume` command | `/resume` command |
| **Clear Behavior** | Delete + create new | Clear history |
| **Memory Format** | SQLite structured data | CLAUDE.md files (instructions only) |
| **History** | Full conversation in DB | Session-based (unclear) |

## Technical Notes

- **Thread-safe**: SQLite handles concurrent access
- **Portable**: Single `.db` file contains all data
- **Scalable**: Indexed queries for performance
- **Minimal dependencies**: Only requires `sqlite3` (built-in Python)

## Troubleshooting

### Database locked error
If you see "database is locked", ensure only one instance of the program is running.

### Missing API key
Set the environment variable:
```bash
export GEMINI_API_KEY='your-key-here'
# Or add to ~/.bashrc or ~/.zshrc
```

### Dialog not appearing in `/resume`
Check that messages were added before quitting. Empty dialogs (no messages) will still appear but with 0 message count.

---

## References

- [Google Gemini API](https://ai.google.dev/) - Gemini API documentation
- [Rich Library](https://rich.readthedocs.io/) - Terminal formatting
- [Requests](https://docs.python-requests.org/) - HTTP library
- [SQLite3](https://docs.python.org/3/library/sqlite3.html) - Python SQLite documentation

---

## License

Educational project for AI Advent Challenge