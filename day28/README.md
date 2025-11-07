# 🤖 God Agent - Ultimate AI Personal Assistant

**Day 28: AI Advent Challenge**

The God Agent is the culmination of 28 days of AI development - a comprehensive personal assistant that combines ALL the best features from previous days into one powerful, production-ready system.

## 🌟 Features

### Core Capabilities

- **🧠 Multi-Provider LLM Support**: Gemini (Google AI) + Ollama (Local LLM) with runtime switching
- **📚 RAG**: ChromaDB vector database with semantic search and Gemini reranking
- **🛠️ MCP Integration**: File operations, shell execution, autonomous tool use
- **⏰ Background Task Scheduling**: APScheduler with AI summaries and notifications
- **🔍 Code Analysis**: Multi-language support (Python, JS, Java, Go, Rust, C++) with quality scoring
- **🚀 Deployment Automation**: 4-stage pipeline for Railway/Docker with AI recommendations
- **🎤 Voice Input**: Groq Whisper API for speech-to-text
- **👤 User Personalization**: Adaptive system with persistent preferences

### Interfaces

- **💻 CLI**: Rich terminal UI with file autocomplete
- **🌐 Web**: FastAPI + Modern responsive UI with dark/light theme

## 📁 Project Structure

```
day28/
├── god_agent.py          # Main orchestration class
├── chat.py               # CLI interface
├── requirements.txt      # Dependencies
├── webapp/               # Web interface
│   ├── app.py            # FastAPI backend
│   └── static/           # Frontend (HTML/CSS/JS)
├── core/                 # Core LLM & storage
├── rag/                  # RAG components
├── mcp_integration/      # MCP tools
├── tasks/                # Task scheduling
├── pipeline/             # Code analysis & deployment
└── managers/             # Feature managers
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Google AI API key: https://makersuite.google.com/app/apikey
- (Optional) Ollama: https://ollama.ai/
- (Optional) Groq API key for voice

### Installation

```bash
cd day28
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add GEMINI_API_KEY
```

### Running

**CLI (Local):**
```bash
python chat.py
```

**Web Interface (Local):**
```bash
python webapp/app.py
# Open http://localhost:8080
```

**Docker (Recommended for Production):**
```bash
# Start all services
docker-compose up -d

# View logs
docker logs -f god-agent

# Stop services
docker-compose down
```

Access the web interface at http://localhost:8080

## 💡 Usage Examples

### CLI Commands

**Basic Chat:**
```bash
You: Hello!
AI: Hello! I'm your ultimate AI assistant...

You: /help
# Shows all available commands
```

**Voice Input:**
```bash
You: /voice
# Records 5 seconds of audio and transcribes
```

**Task Management:**
```bash
You: /tasks
# View and manage scheduled tasks

You: Create a task to check Bitcoin price every 5 minutes
# AI will help create the task
```

**Code Analysis:**
```bash
You: /analyze path/to/file.py
# Analyzes code quality, complexity, and issues
```

**Deployment:**
```bash
You: /deploy
Platform [railway/docker]: docker
# Validates, builds, and deploys application
```

**Model Switching:**
```bash
You: /model
# Switch between Gemini and Ollama at runtime
```

### Python API Examples

**Chat with RAG:**
```python
from god_agent import GodAgent

agent = GodAgent(gemini_api_key="your_key", llm_provider="gemini")
await agent.start()

response = await agent.chat("Explain quantum computing", use_rag=True)
```

**Create Scheduled Task:**
```python
task_id = agent.create_task({
    'name': 'Bitcoin Price Check',
    'mcp_tool': 'crypto_get_price',
    'tool_args': {'symbol': 'bitcoin'},
    'schedule_type': 'interval',
    'schedule_value': '5 minutes',
    'use_ai_summary': True
})
```

**Analyze Code:**
```python
analysis = await agent.analyze_code(code, 'file.py')
print(f"Quality Score: {analysis['quality_score']}/100")
```

**Runtime Provider Switching:**
```python
# Switch from Gemini to Ollama
success = agent.switch_llm_provider('ollama')

# Continue chatting with new provider
response = await agent.chat("Hello with Ollama!")
```

## 🌐 Web Interface Features

The web interface provides a full-featured UI with:

### Chat Tab
- Real-time chat via WebSocket
- Markdown rendering for AI responses
- RAG toggle for knowledge-enhanced answers
- Temperature control for response creativity
- Conversation history

### Tasks Tab
- View all scheduled tasks
- Create new tasks with cron/interval schedules
- Pause/resume tasks
- Delete tasks
- View task execution logs
- AI-powered task summaries

### RAG Tab
- Upload documents (TXT, PDF, MD)
- Index content for semantic search
- Search knowledge base
- View indexed documents
- Delete documents

### Code Analysis Tab
- Upload code files for analysis
- Quality scoring (0-100)
- Complexity metrics
- Security issue detection
- Best practice recommendations
- Multi-language support

### Deploy Tab
- Select platform (Railway/Docker)
- Automated deployment pipeline
- Real-time deployment logs
- AI recommendations for optimization

### Status Tab
- System uptime and metrics
- Active services status
- API key configuration
- Capability status
- Resource usage

## 🔌 Web API Endpoints

**Chat:**
- `POST /api/chat` - Chat (HTTP)
- `WS /ws/chat` - Real-time chat (WebSocket)

**Tasks:**
- `GET /api/tasks` - List all tasks
- `POST /api/tasks` - Create new task
- `PUT /api/tasks/{id}/pause` - Pause task
- `PUT /api/tasks/{id}/resume` - Resume task
- `DELETE /api/tasks/{id}` - Delete task

**Code Analysis:**
- `POST /api/code/analyze` - Analyze code

**Deployment:**
- `POST /api/deploy` - Deploy application

**RAG:**
- `POST /api/rag/index` - Index document
- `POST /api/rag/search` - Search knowledge base
- `POST /api/rag/index/file` - Upload and index file

**System:**
- `GET /api/status` - System status
- `GET /api/tools` - List available MCP tools

**Interactive API Documentation:**
- OpenAPI/Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## 🔧 Configuration

**.env:**
```bash
GEMINI_API_KEY=your_key
GROQ_API_KEY=your_key  # Optional
LLM_PROVIDER=gemini  # or 'ollama'
```

**Enable/Disable Features:**
```python
capabilities = AgentCapabilities(
    llm_enabled=True,
    rag_enabled=True,
    tasks_enabled=True,
    code_analysis_enabled=True,
    deployment_enabled=True,
    voice_enabled=False
)
agent = GodAgent(gemini_api_key="key", capabilities=capabilities)
```

## 🐳 Docker Deployment

### Quick Start

```bash
# Build and start all services
docker-compose up -d

# Check status
docker ps

# View logs
docker logs -f god-agent

# Restart after code changes
docker-compose up -d --build

# Stop all services
docker-compose down
```

### Services

The docker-compose setup includes:
- **god-agent**: Main application (port 8080)
- **ollama**: Local LLM server (port 11434) - optional
- **redis**: Caching layer (port 6379) - optional
- **prometheus**: Monitoring (port 9090) - optional

### Environment Variables

Create `.env` file with required variables:
```bash
GEMINI_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here  # Optional for voice
LLM_PROVIDER=gemini  # or 'ollama'
```

### Docker Notes

- MCP tools are limited in Docker (file system access restricted)
- For full MCP functionality, run locally with `python chat.py`
- Ollama service requires ~8GB RAM and GPU for optimal performance
- Redis and Prometheus are optional - comment out in docker-compose.yml if not needed

## 🧪 Testing

```bash
pytest
pytest --cov=.
```

## 🔧 Troubleshooting

### Common Issues

**"GEMINI_API_KEY not found"**
- Ensure `.env` file exists in project root
- Verify API key is set: `GEMINI_API_KEY=your_key_here`
- Get API key from: https://makersuite.google.com/app/apikey

**"pyaudio failed to install"**
```bash
# macOS:
brew install portaudio
pip install pyaudio

# Linux (Ubuntu/Debian):
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio

# Windows:
pip install pipwin
pipwin install pyaudio
```

**"Ollama not found"**
- Install Ollama: https://ollama.ai/
- Pull required model: `ollama pull qwen2.5-coder:7b-instruct`
- Or use Gemini: set `LLM_PROVIDER=gemini` in `.env`

**"Port 8080 already in use"**
```bash
# Find and kill process using port 8080
lsof -ti:8080 | xargs kill -9

# Or change port in .env
PORT=8081
```

**"God Agent not initialized" (Web Interface)**
- Check Docker logs: `docker logs god-agent`
- Verify `.env` file is mounted correctly
- Restart container: `docker-compose restart god-agent`

**"MCP connection failed" (Warning in logs)**
- This is normal in Docker environment
- MCP tools require direct file system access
- For full MCP functionality, run locally: `python chat.py`

**UTF-8 encoding errors**
```bash
# Set UTF-8 locale (Linux/macOS)
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
```

### Getting Help

- Check full documentation: `GETTING_STARTED.md`
- API documentation: http://localhost:8080/docs (when server running)
- GitHub Issues: Report bugs or request features

## 📊 Key Technologies

- **LLMs**: Google Gemini, Ollama
- **Vector DB**: ChromaDB
- **Web**: FastAPI, WebSocket
- **Scheduler**: APScheduler
- **MCP**: Model Context Protocol
- **UI**: Rich (CLI), Modern HTML/CSS/JS (Web)

## 🚧 Roadmap

- Multi-user auth (JWT)
- Voice output (TTS)
- Plugin system
- Mobile app
- Kubernetes deployment
- More cloud platforms

## 📚 References

- [Google Gemini API](https://ai.google.dev/) - Gemini models and function calling
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) - Protocol for AI-tool integration
- [MCP Filesystem Server](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) - File operations via MCP
- [Ollama](https://ollama.com/) - Run large language models locally
- [Groq Console](https://console.groq.com/) - Get free Groq API key for Whisper
- [Groq Documentation](https://console.groq.com/docs/speech-text) - Whisper API docs
- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition model
- [ChromaDB Documentation](https://docs.trychroma.com/) - Vector database for embeddings
- [FastAPI Documentation](https://fastapi.tiangolo.com/) - Modern web framework for APIs
- [APScheduler Documentation](https://apscheduler.readthedocs.io/) - Advanced Python task scheduler
- [Docker Documentation](https://docs.docker.com/) - Containerization platform
- [Railway](https://railway.app/) - Cloud deployment platform
- [pytest](https://docs.pytest.org/) - Python testing framework
- [Rich](https://rich.readthedocs.io/) - Rich text and beautiful formatting in terminal
- [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/) - Interactive command line interface library
- [fuzzywuzzy](https://github.com/seatgeek/fuzzywuzzy) - Fuzzy string matching for autocomplete
- [RAG Paper](https://arxiv.org/abs/2005.11401) - Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
- [Reranking in RAG](https://arxiv.org/abs/2407.21439) - Survey on reranking techniques for RAG

**Note:** Most base Ollama models have weaker tool calling capabilities compared to Gemini. The `qwen2.5-coder:7b-instruct` variant is specifically fine-tuned for tool calling and code generation.

---

## 📄 License

Educational project for AI Advent Challenge