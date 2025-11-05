# Day 26: AI Autotest Agent with MCP Integration

An intelligent chat-based assistant powered by Google Gemini AI that can automatically generate and execute Python tests using the Model Context Protocol (MCP).

## 🌟 Features

### Core Capabilities
- **AI-Powered Chat Interface** - Natural conversation with Google Gemini 2.5 models
- **Automatic Test Generation** - AI analyzes your code and generates comprehensive pytest tests
- **MCP Tool Integration** - File operations and shell command execution via MCP servers
- **@ File Mentions** - Fuzzy file path autocomplete with inline context injection
- **RAG Document Search** - ChromaDB-powered semantic search across indexed documents
- **User Personalization** - Persistent user profiles with preferences and context
- **Voice Input** - Speech-to-text via Groq Whisper API
- **Conversation History** - SQLite-based persistent chat storage

### MCP-Powered Features
- **File Operations** - Read, write, search files through MCP filesystem server
- **Test Execution** - Run pytest and capture results via MCP shell server
- **Multi-turn Function Calling** - AI decides which tools to use autonomously
- **Safe Sandboxing** - All file and shell operations go through MCP protocol

## 🏗 Architecture

```
day26/
├── chat.py                      # Main entry point with chat loop
├── requirements.txt             # Python dependencies
├── core/                        # Core functionality
│   ├── gemini_client.py        # Gemini API with function calling
│   ├── storage.py              # SQLite conversation storage
│   ├── user_profile.py         # User personalization
│   ├── conversation.py         # Conversation history
│   ├── text_manager.py         # Token counting utilities
│   ├── file_mentions.py        # @ file mention parsing
│   └── autocomplete.py         # Fuzzy file path autocomplete
├── managers/                    # Feature managers
│   ├── index_manager.py        # Document indexing
│   ├── rag_manager.py          # RAG search & reranking
│   ├── dialog_manager.py       # Conversation management
│   ├── settings_manager.py     # AI parameters
│   ├── ui_manager.py           # Rich console UI
│   └── speech_manager.py       # Voice input
├── mcp_integration/             # MCP integration
│   ├── manager.py              # MCP client & tool router
│   ├── shell_server.py         # Custom MCP shell server
│   └── config.json             # MCP server configuration
├── pipeline/                    # Document processing
├── rag/                         # RAG-specific modules
└── data/                        # Persistent data
    ├── conversations.db        # SQLite chat history
    └── user_config.json        # User profile
```

## 📋 Prerequisites

### Required Software
- **Python 3.8+**
- **Node.js 14+** (for MCP servers via npx)

### API Keys
1. **Google AI (Gemini) API Key** - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Groq API Key** (optional, for voice input) - Get from [Groq Console](https://console.groq.com)

### MCP Servers
The following MCP servers are automatically launched:
- `@modelcontextprotocol/server-filesystem` - File operations (via npx)
- Custom `shell_server.py` - Shell command execution (local Python server)

## 🚀 Installation

### 1. Navigate to Directory
```bash
cd day26
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables
```bash
# Required
export GEMINI_API_KEY="your-gemini-api-key"

# Optional (for voice input)
export GROQ_API_KEY="your-groq-api-key"
```

### 5. Verify Node.js (for MCP servers)
```bash
node --version  # Should be 14+
```

## 💡 Usage

### Start the Chat
```bash
python chat.py
```

### File Mentions with @ Symbol

Type `@` to trigger fuzzy file path autocomplete. Use arrow keys to navigate and Tab/Enter to select:

```
You: @calc<Tab>
     → autocompletes to @calculator.py

You: @calculator.py write comprehensive tests
```

The AI automatically reads the mentioned file and includes it in context.

### Autotest Workflow Example

```
You: @calculator.py create tests for this file

AI: 🔧 Calling tool: filesystem_read_file
    Reading calculator.py...

    I'll generate comprehensive pytest tests.

    🔧 Calling tool: filesystem_write_file
    Writing tests/test_calculator.py...

    🔧 Calling tool: shell_execute_command
    Running pytest tests/test_calculator.py -v...

    Results: ✓ 5 passed, ✗ 1 failed

🔧 Tools used (3):
  1. filesystem_read_file
  2. filesystem_write_file
  3. shell_execute_command
```

## 📝 Available Commands

- `/help` - Show all commands
- `/quit` - Exit
- `/model` - Change AI model
- `/profile` - Manage user profile
- `/index <path>` - Index documents for RAG
- `/voice` - Voice input

## 🤖 How It Works

1. **User Request**: "test my code.py"
2. **AI Analysis**: Gemini decides to use MCP tools
3. **File Read**: MCP filesystem reads code.py  
4. **Test Generation**: AI creates pytest tests
5. **File Write**: MCP filesystem saves test file
6. **Execution**: MCP shell runs pytest
7. **Results**: AI formats and presents output

## 🔧 MCP Tools

### Filesystem
- read_file, write_file, list_directory, search_files

### Shell  
- execute_command (for running pytest)

## 📚 Documentation

Full documentation from day25 applies:
- User profiles and personalization
- RAG document indexing
- Voice input
- Conversation management

**New in Day 26:**
- MCP integration for autonomous file operations and test execution
- @ file mentions with fuzzy autocomplete for quick context injection

## References

- [Google Gemini API](https://ai.google.dev/) - Gemini models and function calling
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) - Protocol for AI-tool integration
- [MCP Filesystem Server](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) - File operations via MCP
- [Groq Console](https://console.groq.com/) - Get free Groq API key for Whisper
- [Groq Documentation](https://console.groq.com/docs/speech-text) - Whisper API docs
- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition model
- [ChromaDB Documentation](https://docs.trychroma.com/) - Vector database for embeddings
- [pytest](https://docs.pytest.org/) - Python testing framework
- [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/) - Interactive command line interface library
- [fuzzywuzzy](https://github.com/seatgeek/fuzzywuzzy) - Fuzzy string matching for autocomplete
- [RAG Paper](https://arxiv.org/abs/2005.11401) - Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
- [Reranking in RAG](https://arxiv.org/abs/2407.21439) - Survey on reranking techniques for RAG

---

## License

Educational project for AI Advent Challenge
