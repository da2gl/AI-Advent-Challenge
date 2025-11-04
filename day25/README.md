# Day 25: Personalized AI Chat with User Profile Management

## Overview

A mini-chat with **user personalization**, **automatic RAG (Retrieval-Augmented Generation)**, and **voice input** that adapts to your preferences and provides context-aware responses.

**New in Day 25**:
- 🎭 **User Profile Management** - Personalize your AI assistant with your name, role, interests, and preferences
- 🎨 **Adaptive System Instructions** - AI automatically adjusts its behavior based on your profile
- 💾 **Persistent Settings** - All personalization saved to `user_config.json` across sessions
- 🌍 **UTF-8 Support** - Full support for non-ASCII characters (Russian, Chinese, etc.)

**From Day 24**: Voice input via Groq Whisper API - record audio from microphone, automatically transcribe to text, and process through the full RAG pipeline.

**From Day 23**: Modular architecture with specialized managers and mandatory reranking for improved relevance.

## Key Features

### 🎭 User Profile & Personalization (NEW in Day 25)
- **Personal Information** - Set your name, role, communication style
- **Preferences** - Configure response length, code style, explanation level
- **Interests & Habits** - Track your interests and habits for contextual responses
- **Persistent Storage** - All settings saved to `data/user_config.json`
- **Automatic Context Injection** - Your profile is automatically added to system instructions
- **UTF-8 Encoding** - Full support for international characters (Russian, Chinese, Arabic, etc.)

**How it works:**
```bash
/profile  # Opens interactive profile manager with 7 options:
  1. Edit name
  2. Edit role (e.g., Developer, Student)
  3. Edit communication style (casual, formal, friendly, professional)
  4. Edit preferences (response length, code style, explanation level)
  5. Manage interests (add/remove topics you care about)
  6. Manage habits (track your working patterns)
  7. Reset to defaults
```

**Example personalized system instruction:**
```
You are a helpful AI assistant.

Personalization:
- You are assisting Alex, who is a Python Developer
- Use a casual communication style
- Provide concise responses, intermediate-level explanations
- User's interests: Machine Learning, Web Development
- User's habits: Prefers code examples, works in VSCode
```

**Three-tier settings structure:**
- `/profile` - Personal data (name, role, interests, habits, preferences)
- `/system` - Base system instruction (augmented with profile context)
- `/settings` - Generation parameters (temperature, top_k, top_p, max_tokens)

### 🎤 Voice Input (from Day 24)
- **Speech-to-Text** - Record audio from microphone and transcribe via Groq Whisper API
- **Simple activation** - Just type `/voice` command to start recording
- **Press Enter to stop** - Intuitive recording control
- **Automatic processing** - Transcribed text flows through full RAG pipeline
- **Free tier** - Uses Groq's free Whisper API for transcription
- **High accuracy** - Powered by OpenAI's Whisper large-v3 model

### 🎯 Automatic RAG Integration
- **No command needed** - RAG automatically activates for every message
- **Automatic context search** - Searches knowledge base before each response
- **Mandatory reranking** - Uses Gemini to score and filter search results
- **Mandatory source citations** - Every response shows which documents were used
- **Conversation history** - Full dialog persistence with SQLite
- **Seamless experience** - Just type your questions naturally

### 🏗️ Modular Architecture
The code has been refactored into specialized managers:
- **IndexManager** - Document indexing and search operations
- **RagManager** - RAG search, context formatting, and Koog loading
- **DialogManager** - Conversation history and dialog management
- **SettingsManager** - System instructions and generation settings
- **UIManager** - Display, welcome screens, and model selection

**Result**: `chat.py` reduced from 1062 to 297 lines (72% reduction)

### 🎯 Mandatory Reranking Pipeline
Every search now goes through a 2-stage retrieval process:

1. **Initial Retrieval**: ChromaDB returns 20 candidates using L2 distance
2. **Reranking**: Gemini scores each candidate (0-10) for relevance
3. **Filtering**: Only top-K results with score ≥ 5.0 are used

**Benefits:**
- ✅ Higher precision - irrelevant results filtered out
- ✅ Better ranking - semantic relevance vs. just embedding distance
- ✅ Quality control - low-quality matches automatically removed

### 📚 Citation Format
All responses include inline citations:
```
"The A2A protocol uses JSON-RPC for communication [Source: a2a-client/Module.md, Chunk 2].
It enables standardized communication between AI agents [Source: a2a-core/Module.md, Chunk 3]."
```

After each response, sources are displayed with rerank scores:
```
📚 Sources (3 documents):
  1. a2a-client/Module.md (Chunk 2, relevance: 0.85, rerank: 8.5/10)
  2. a2a-core/Module.md (Chunk 3, relevance: 0.82, rerank: 7.8/10)
  3. README.md (Chunk 1, relevance: 0.79, rerank: 7.2/10)
```

### ✅ Benefits
1. **Transparency** - Users can verify every claim
2. **Accuracy** - Reranking + citations eliminate hallucinations
3. **Trust** - Clear evidence with quality scores for all statements
4. **Traceability** - Direct links to source documents
5. **Quality Control** - Easy to identify missing or weak sources
6. **Maintainability** - Modular code is easier to extend and test

## Setup & Requirements

### Prerequisites
1. **Python 3.8+**
2. **Ollama** - For local embeddings
   ```bash
   # Install from https://ollama.com/
   ollama serve
   ollama pull mxbai-embed-large
   ```
3. **Google Gemini API Key** - Get from [Google AI Studio](https://ai.google.dev/)
4. **Groq API Key** (for voice input) - Get free key from [Groq Console](https://console.groq.com/)

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install PyAudio** (for voice input):

   **macOS:**
   ```bash
   brew install portaudio
   pip install pyaudio
   ```

   **Linux:**
   ```bash
   sudo apt-get install portaudio19-dev python3-pyaudio
   pip install pyaudio
   ```

   **Windows:**
   ```bash
   pip install pipwin
   pipwin install pyaudio
   ```

3. **Set API keys:**
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key"
   export GROQ_API_KEY="your-groq-api-key"
   ```

   Or the program will prompt you for keys on first run.

4. **Run the chat:**
   ```bash
   python chat.py
   ```

### Voice Input Setup

To use the `/voice` command:
1. Get a free Groq API key from [console.groq.com](https://console.groq.com/)
2. Set `GROQ_API_KEY` environment variable or enter when prompted
3. Ensure microphone permissions are granted
4. Type `/voice` in chat, speak your question, press Enter to stop recording

## How It Works

### Automatic RAG Pipeline with Reranking

```
User types message
    ↓
1. Save message to conversation history
    ↓
2. AUTOMATIC: Search knowledge base
   - Generate embedding (Ollama mxbai-embed-large, 1024d)
   - Search ChromaDB for top-20 candidates (L2 distance)
    ↓
3. AUTOMATIC: Rerank with Gemini
   - Score each candidate 0-10 for relevance
   - Filter by distance threshold (< 195.0)
   - Keep only scores ≥ 5.0
   - Return top-5 best matches
    ↓
4. AUTOMATIC: Build enhanced prompt
   [RELEVANT DOCUMENTATION CONTEXT]
   [Source 1: file1.md, Chunk 2]
   Content from file1...

   [Source 2: file2.md, Chunk 5]
   Content from file2...

   Please cite sources in your response using the format [Source: filename, Chunk X].

   Question: User's original question...
    ↓
5. Send to Gemini with conversation history
    ↓
6. Display response
    ↓
7. AUTOMATIC: Display sources with rerank scores
   📚 Sources (5 documents):
     1. file1.md (Chunk 2, relevance: 0.85, rerank: 8.5/10)
     2. file2.md (Chunk 5, relevance: 0.82, rerank: 7.8/10)
     ...
```

### Citation Guidelines
The system uses soft citation guidance:

```
Use the following documentation to answer the question.
Please cite sources in your response using the format [Source: filename, Chunk X].

Documentation:
---
[CONTEXT CHUNKS]
---

Question: [USER QUESTION]
```

## Usage

### Prerequisites
```bash
# Install Ollama
brew install ollama  # macOS
# or download from https://ollama.com

# Start Ollama server
ollama serve

# Pull embedding model
ollama pull mxbai-embed-large
```

### Start Chat
```bash
cd day25
python chat.py
```

**First Run:**
- `data/user_config.json` is automatically created with default settings
- Welcome message shows your name if configured (otherwise "User")
- Terminal encoding is checked and fixed if needed

### Setup Your Profile (Optional)
```bash
/profile
# Edit your name, role, interests, etc.
```

### First Time: Load Documentation
```bash
/load-koog
```
Loads Koog documentation using Ollama embeddings. This is cached - only needs to run once.

### Just Type Your Questions!
No special command needed - RAG is automatic:
```bash
You: What is the A2A protocol and what is it used for?
```

**Output:**
```
AI: The A2A (Agent-to-Agent) protocol is a standardized
communication protocol for AI agents [Source: AGENT.md, Chunk 1].
It enables seamless communication between different AI agents in
distributed systems using a JSON-RPC based transport layer
[Source: a2a-core/Module.md, Chunk 2].


📚 Sources (3 documents):
  1. AGENT.md (Chunk 1, relevance: 0.85, rerank: 8.5/10)
  2. a2a-core/Module.md (Chunk 2, relevance: 0.82, rerank: 7.8/10)
  3. a2a-client/Module.md (Chunk 3, relevance: 0.76, rerank: 7.1/10)
```

**Key difference**: Sources with rerank scores are automatically displayed after EVERY response!

### View Documentation Info
```bash
/koog-info
```
Shows loaded documents and suggests sample questions.

### Available Commands
```
Document Management:
  /load-koog [--force]  - Load Koog docs (cached, use --force to reindex)
  /koog-info            - Show loaded docs & suggest questions
  /index <path>         - Index custom documents
  /search <query>       - Search index manually
  /list-collections     - Show all collections

Chat Commands:
  /voice     - Record voice input and transcribe (press Enter to stop)
  /profile   - Manage user info (name, role, preferences, interests)
  /system    - View/change base system instruction
  /settings  - View/change generation settings (temperature, top_k, etc.)
  /resume    - Load previous dialog
  /clear     - Delete current dialog & create new
  /model     - Change Gemini model
  /compress  - Compress conversation history
  /tokens    - Show token statistics
  /help      - Show all commands
  /quit      - Exit

Note: No /ask command needed - RAG is automatic for all messages!

Three-tier personalization:
  /profile   - Personal data only (name, role, interests, habits)
  /system    - Base AI instruction (auto-enhanced with profile)
  /settings  - Technical generation parameters
```

## Technical Details

### Architecture
```
day25/
├── chat.py                      # Main orchestrator with personalization
│   ├── handle_command()         # Command routing (including /profile)
│   ├── chat_loop()              # Main loop with automatic RAG
│   ├── _manage_profile()        # Profile management submenu
│   ├── _edit_preferences()      # Preferences editor
│   ├── _manage_interests()      # Interests management
│   ├── _manage_habits()         # Habits management
│   └── _init_rag_manager()      # Lazy initialization
├── managers/                    # Modular architecture
│   ├── __init__.py              # Manager exports
│   ├── index_manager.py         # Document indexing (258 lines)
│   ├── rag_manager.py           # RAG operations (319 lines)
│   ├── dialog_manager.py        # Conversation mgmt (208 lines)
│   ├── settings_manager.py      # Settings with profile support (110 lines)
│   ├── ui_manager.py            # UI/Display with personalization (144 lines)
│   └── speech_manager.py        # Voice input via Groq Whisper
├── core/
│   ├── conversation.py          # Dialog history with SQLite
│   ├── gemini_client.py         # Gemini API client
│   ├── storage.py               # SQLite operations
│   ├── text_manager.py          # Token counting
│   └── user_profile.py          # NEW: User profile management
├── rag/
│   ├── rag_client.py            # NEW: Simple RAG client with reranking
│   ├── reranker.py              # Gemini-based reranker
│   └── koog_loader.py           # Koog documentation loader
├── pipeline/
│   ├── ollama_embedding_generator.py  # Ollama embeddings (1024d)
│   ├── index_manager.py         # ChromaDB operations
│   ├── document_loader.py       # Document loading
│   ├── text_chunker.py          # Text chunking
│   └── pipeline_executor.py     # Indexing pipeline
├── koog/                        # Git submodule with docs
└── data/
    ├── conversations.db         # SQLite dialog storage
    ├── user_config.json         # NEW: User profile and settings
    └── chroma_db/               # Persisted vector database
```

### Key Components

#### UserProfile (core/user_profile.py)
Manages persistent user profile and personalization:
```python
class UserProfile:
    def __init__(self, config_path: str = "data/user_config.json"):
        # Load or create user config from JSON
        self.profile_data = self._load_or_create_default()

    def get_system_instruction(self) -> str:
        # Build personalized system instruction
        # Base instruction + user context injection
        return personalized_instruction

    def update_profile_field(self, field: str, value: Any) -> bool:
        # Update field and auto-save to JSON
        return self.save()

    def update_preference(self, pref_name: str, value: str) -> bool:
        # Update preference and auto-save

    def add_interest(self, interest: str) -> bool:
        # Add interest to profile

    def add_habit(self, habit: str) -> bool:
        # Add habit to profile
```

**Configuration Structure:**
```json
{
  "user_profile": {
    "name": "Alex",
    "role": "Python Developer",
    "communication_style": "casual",
    "preferences": {
      "response_length": "concise",
      "code_style": "clean",
      "explanation_level": "intermediate"
    },
    "interests": ["Machine Learning", "Web Development"],
    "habits": ["Prefers code examples"]
  },
  "generation_settings": {
    "temperature": 0.7,
    "top_k": 40,
    "top_p": 0.95,
    "max_output_tokens": 2048
  },
  "system_instruction": "You are a helpful AI assistant."
}
```

#### RagClient (rag/rag_client.py)
Simple client that coordinates search and reranking:
```python
class RagClient:
    def search(self, question: str, top_k: int = 5, initial_k: int = 20):
        # 1. Generate embedding
        question_embedding = self.embedding_generator.generate_embedding(question)

        # 2. Get initial candidates from ChromaDB
        initial_chunks = self.index_manager.search(
            query_embedding=question_embedding,
            top_k=initial_k  # Get 20 candidates
        )

        # 3. Rerank with Gemini
        reranked_chunks, stats = self.reranker.rerank(
            query=question,
            chunks=initial_chunks,
            top_k=top_k  # Return top 5
        )

        return reranked_chunks
```

#### Reranker (rag/reranker.py)
Three-stage filtering pipeline:
```python
class Reranker:
    def rerank(self, query: str, chunks: list, top_k: int = 3):
        # Stage 1: Filter by distance threshold
        filtered = [c for c in chunks if c.distance < 195.0]

        # Stage 2: Score with Gemini (0-10)
        for chunk in filtered:
            chunk.rerank_score = self._score_relevance(query, chunk.text)

        # Stage 3: Filter by min score and sort
        final = [c for c in filtered if c.rerank_score >= 5.0]
        final.sort(key=lambda x: x.rerank_score, reverse=True)

        return final[:top_k]
```

#### RagManager (managers/rag_manager.py)
Handles all RAG operations:
- `load_koog()` - Load and index Koog documentation
- `show_koog_info()` - Display documentation statistics
- `init_rag_client()` - Initialize RAG client with reranker
- `is_rag_available()` - Check if RAG collection exists
- `search_context()` - Search with automatic reranking
- `format_context_for_prompt()` - Format chunks for LLM

### Technologies
- **LLM**: Google Gemini 2.5 Flash
- **Speech-to-Text**: Groq Whisper API (whisper-large-v3, free tier)
- **Reranking**: Google Gemini 2.5 Flash Lite (for speed)
- **Embeddings**: Ollama mxbai-embed-large (1024d, local)
- **Vector DB**: ChromaDB (L2 distance)
- **Dataset**: Koog documentation (165 markdown files)
- **UI**: Rich (terminal with markdown rendering)
- **Storage**: SQLite (conversation persistence)
- **Audio**: PyAudio (microphone recording)

### Reranking Configuration
```python
Reranker(
    gemini_client=gemini_client,
    distance_threshold=195.0,    # L2 distance for 1024d vectors
    min_rerank_score=5.0,        # Minimum relevance score (0-10)
    max_score=10.0               # Maximum score
)
```

## Success Metrics

### Personalization (NEW in Day 25)
- ✅ **User Context**: Profile data automatically injected into system instructions
- ✅ **Persistence**: All settings saved to JSON across sessions
- ✅ **Separation**: Clear three-tier structure (/profile, /system, /settings)
- ✅ **UTF-8 Support**: Full international character support with automatic encoding fix
- ✅ **User Experience**: Interactive profile management with 7 options
- ✅ **Flexibility**: Easy to customize AI behavior per user

### Code Quality
- ✅ **Modularity**: 6 specialized managers (added SpeechManager)
- ✅ **Maintainability**: New UserProfile class with clean API
- ✅ **Persistence**: JSON-based configuration (human-readable)
- ✅ **Separation**: UI, RAG, Dialog, Settings, Profile, and Index concerns separated
- ✅ **Error Handling**: Proper UTF-8 and UnicodeDecodeError handling

### RAG Quality
- ✅ **Precision**: Reranking improves top-K accuracy
- ✅ **Relevance**: Gemini scoring catches semantic mismatches
- ✅ **Coverage**: 100% of answers contain citations
- ✅ **Format**: All citations match `[Source: filename, Chunk X]`

### Hallucination Reduction
**Without Reranking:**
- May include marginally relevant chunks
- Distance-based ranking sometimes misleading
- Lower quality results reduce answer accuracy

**With Mandatory Reranking:**
- ✅ Semantic relevance verified by LLM
- ✅ Low-quality matches filtered out
- ✅ Better context quality → fewer hallucinations
- ✅ Transparent quality scores shown to user

## Example Interaction

### Setting Up Your Profile (NEW in Day 25)
```
You: /profile

============================================================
User Profile Management
============================================================

Current Profile:
  Name:                 User
  Role:                 Developer
  Communication Style:  casual
  Response Length:      concise
  Code Style:           clean
  Explanation Level:    intermediate

Actions:
  1. Edit name
  2. Edit role
  3. Edit communication style
  4. Edit preferences
  5. Manage interests
  6. Manage habits
  7. Reset to defaults
  0. Back to chat
============================================================

Select action (0-7): 1
Enter your name: Alex
✓ Name updated and saved

Select action (0-7): 5
Current interests: (none)
Actions: [a]dd, [r]emove, [b]ack
Choose action: a
Enter new interest: Machine Learning
✓ Interest added and saved

Select action (0-7): 0
```

### Text Input (with Personalized Welcome)
```
============================================================
     AI Assistant - Welcome, Alex!
============================================================

Model: Gemini 2.5 Flash (Fast & Balanced)
Temperature: 0.7 | TopK: 40 | TopP: 0.95 | MaxTokens: 2048
System instruction: You are a helpful AI assistant...
============================================================

You: /load-koog
✓ Koog collection already loaded from cache
💡 Just type your questions - RAG is automatic!

You: What is the A2A protocol?

AI: The A2A (Agent-to-Agent) protocol is a standardized protocol for
communication between AI agents [Source: AGENT.md, Chunk 1]. It defines
how agents discover each other, exchange messages, and coordinate tasks
[Source: a2a-core/Module.md, Chunk 2]. The protocol uses JSON-RPC as
its transport mechanism [Source: a2a-transport/README.md, Chunk 3].


📚 Sources (3 documents):
  1. AGENT.md (Chunk 1, relevance: 0.85, rerank: 8.5/10)
  2. a2a-core/Module.md (Chunk 2, relevance: 0.82, rerank: 7.8/10)
  3. a2a-transport/README.md (Chunk 3, relevance: 0.79, rerank: 7.2/10)

You: /quit
Goodbye!
```

### Voice Input (from Day 24)
```
You: /voice
🔴 Recording... Press Enter to stop
[User speaks: "What is two plus two?"]
[User presses Enter]
✓ Recording stopped
Transcribing audio...
📝 Recognized: What is two plus two?

AI: Two plus two equals four (2 + 2 = 4).

ℹ️  RAG not loaded. Answer based on general knowledge.

You: /voice
🔴 Recording... Press Enter to stop
[User speaks: "Tell me a joke"]
[User presses Enter]
✓ Recording stopped
Transcribing audio...
📝 Recognized: Tell me a joke

AI: Why don't scientists trust atoms? Because they make up everything!

ℹ️  RAG not loaded. Answer based on general knowledge.
```

## Troubleshooting

### UTF-8 Encoding Issues (NEW in Day 25)
```
UnicodeDecodeError: 'utf-8' codec can't decode byte...
```
**Problem**: Terminal doesn't support UTF-8 encoding for non-ASCII characters (Russian, Chinese, etc.)

**Solution**: The app automatically fixes stdin encoding. If issues persist:

**macOS/Linux:**
```bash
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
python chat.py
```

**Windows:**
```bash
chcp 65001  # Set console to UTF-8
python chat.py
```

**IntelliJ IDEA / PyCharm:**
- File → Settings → Editor → File Encodings
- Set "Global Encoding" and "Project Encoding" to UTF-8
- Restart IDE

The app now includes:
- ✅ Automatic stdin UTF-8 wrapping
- ✅ UnicodeDecodeError exception handling
- ✅ Encoding warning on startup
- ✅ Full support for international characters

### Ollama Connection Error
```
Connection error: Is Ollama running at http://localhost:11434?
```
**Solution**: Start Ollama server
```bash
ollama serve
ollama pull mxbai-embed-large
```

### Gemini API Overloaded (503)
```
API error (status 503): The model is overloaded. Please try again later.
```
**Solution**: Wait a few moments or try a different model
```bash
/model
# Select option 2 (Flash Lite - usually less loaded)
```

### No Documents Found
```
ℹ️  RAG not loaded. Answer based on general knowledge.
💡 Use /load-koog to enable document search
```
**Solution**: Load documentation
```bash
/load-koog
```

### Voice Input Issues

**Microphone not working:**
```
Error during recording: [Errno -9996] Invalid input device
```
**Solution**: Check microphone permissions and device availability
- macOS: System Preferences → Security & Privacy → Microphone
- Linux: Check `arecord -l` for available devices
- Windows: Check Windows Sound settings

**PyAudio installation error:**
```
error: portaudio.h: No such file or directory
```
**Solution**: Install PortAudio first (see Installation section above)

**Groq API error:**
```
Error: Groq API key is required for voice input
```
**Solution**: Set GROQ_API_KEY environment variable or enter when prompted
```bash
export GROQ_API_KEY="your-groq-api-key"
```
Get free key from [console.groq.com](https://console.groq.com/)

## References

- [Groq Console](https://console.groq.com/) - Get free Groq API key for Whisper
- [Groq Documentation](https://console.groq.com/docs/speech-text) - Whisper API docs
- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition model
- [Ollama](https://ollama.com/) - Local LLM runtime
- [mxbai-embed-large](https://ollama.com/library/mxbai-embed-large) - Embedding model on Ollama
- [Koog](https://github.com/JetBrains/koog) - JetBrains AI framework
- [RAG Paper](https://arxiv.org/abs/2005.11401) - Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
- [ChromaDB Documentation](https://docs.trychroma.com/) - Vector database for embeddings
- [Google Gemini API](https://ai.google.dev/) - Gemini models and embeddings
- [Reranking in RAG](https://arxiv.org/abs/2407.21439) - Survey on reranking techniques for RAG
- [RAG Survey](https://arxiv.org/abs/2312.10997) - Recent survey on RAG techniques

---

## License

Educational project for AI Advent Challenge
