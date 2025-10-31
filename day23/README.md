# Day 23: Mini-Chat with RAG Memory and Automatic Source Citations

## Overview

A mini-chat with **automatic RAG (Retrieval-Augmented Generation)** that searches the document database for every user message and provides mandatory source citations. Unlike Day 22 which required the `/ask` command, this chat automatically integrates RAG into the regular conversation flow.

## Key Features

### 🎯 Automatic RAG Integration
- **No command needed** - RAG automatically activates for every message
- **Automatic context search** - Searches knowledge base before each response
- **Mandatory source citations** - Every response shows which documents were used
- **Conversation history** - Full dialog persistence with SQLite
- **Seamless experience** - Just type your questions naturally

### 📝 What Changed from Day 22

| Day 22 | Day 23 |
|--------|--------|
| Required `/ask` command | Automatic RAG for all messages |
| Separate RAG mode | Integrated into regular chat |
| Manual citation request | Automatic source display |

### 📚 Citation Format
All responses include inline citations:
```
"The A2A protocol uses JSON-RPC for communication [Source: a2a-client/Module.md, Chunk 2].
It enables standardized communication between AI agents [Source: a2a-core/Module.md, Chunk 3]."
```

### ✅ Benefits
1. **Transparency** - Users can verify every claim
2. **Accuracy** - Eliminates hallucinations by forcing source attribution
3. **Trust** - Clear evidence for all statements
4. **Traceability** - Direct links to source documents
5. **Quality Control** - Easy to identify missing or weak sources

## How It Works

### Automatic RAG Pipeline

```
User types message
    ↓
1. Save message to conversation history
    ↓
2. AUTOMATIC: Search knowledge base
   - Generate embedding (Ollama mxbai-embed-large)
   - Search ChromaDB for top-5 relevant chunks
    ↓
3. AUTOMATIC: Build enhanced prompt
   [RELEVANT DOCUMENTATION CONTEXT]
   [Source 1: file1.md, Chunk 2]
   Content from file1...

   [Source 2: file2.md, Chunk 5]
   Content from file2...
   [END OF CONTEXT]

   User's original question...
    ↓
4. Send to Gemini with conversation history
    ↓
5. Display response
    ↓
6. AUTOMATIC: Display sources used
   📚 Sources (5 documents):
     1. file1.md (Chunk 2, relevance: 0.85)
     2. file2.md (Chunk 5, relevance: 0.82)
     ...
```

### Citation Requirements
The system instructs the model with strict citation rules:

```
IMPORTANT CITATION REQUIREMENTS:
1. You MUST cite the source for EVERY piece of information you provide
2. Use the exact format: [Source: filename, Chunk X] after each fact or claim
3. DO NOT provide any information without citing its source
4. If information is not in the provided context, explicitly state:
   "This information is not available in the provided sources"
5. Multiple citations can be used if information comes from multiple sources
6. Avoiding unsupported claims and hallucinations is critical - only use provided context
```

## Usage

### Start Chat
```bash
cd day23
python chat.py
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
Assistant: The A2A (Agent-to-Agent) protocol is a standardized
communication protocol for AI agents. It enables seamless communication
between different AI agents in distributed systems using a JSON-RPC
based transport layer for message exchange.


📚 Sources (5 documents):
  1. AGENT.md (Chunk 1, relevance: 0.85)
  2. a2a-core/Module.md (Chunk 2, relevance: 0.82)
  3. a2a-transport/README.md (Chunk 4, relevance: 0.79)
  4. a2a-client/Module.md (Chunk 3, relevance: 0.76)
  5. README.md (Chunk 1, relevance: 0.74)

Tokens: 245 prompt + 67 response = 312 total
Context: [████░░░░░░] 1,245 / 30,000 (4.2%)
```

**Key difference**: Sources are automatically displayed after EVERY response, not just when using `/ask`!

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
  /resume    - Load previous dialog
  /clear     - Delete current dialog & create new
  /model     - Change Gemini model
  /help      - Show all commands
  /quit      - Exit

Note: No /ask command needed - RAG is automatic for all messages!
```

## Technical Details

### Architecture
```
day23/
├── chat.py                      # Main chat with AUTOMATIC RAG
│   ├── _search_rag_context()    # Auto-search on every message
│   ├── _format_context_for_prompt()  # Context injection
│   └── chat_loop()              # Integrated RAG flow
├── core/
│   ├── conversation.py          # Dialog history with SQLite
│   └── gemini_client.py         # Gemini API client
├── rag/
│   └── koog_loader.py           # Koog documentation loader
├── pipeline/
│   ├── ollama_embedding_generator.py  # Ollama embeddings (1024d)
│   └── index_manager.py         # ChromaDB operations
├── koog/                        # Git submodule with docs
└── data/
    ├── conversations.db         # SQLite dialog storage
    └── chroma_db/               # Persisted vector database
```

### Key Implementation Changes

#### chat.py Lines 764-816: New RAG Helper Methods
```python
def _search_rag_context(self, question: str, collection_name: str = "koog"):
    """Search RAG for relevant context - called automatically"""
    # Generate embedding and search ChromaDB
    # Returns chunks or empty list if RAG not available

def _format_context_for_prompt(self, chunks) -> str:
    """Format chunks as context for the prompt"""
    # Builds structured context with source markers
```

#### chat.py Lines 1002-1038: Automatic RAG Integration
```python
# Before generating response:
1. Search RAG: rag_chunks = self._search_rag_context(prompt_to_send)
2. Format context: rag_context = self._format_context_for_prompt(rag_chunks)
3. Inject context: final_prompt = rag_context + prompt_to_send
4. Generate with Gemini
5. Display sources automatically
```

### Technologies
- **LLM**: Google Gemini 2.5 Flash
- **Embeddings**: Ollama mxbai-embed-large (1024d, local)
- **Vector DB**: ChromaDB (L2 distance)
- **Dataset**: Koog documentation (165 markdown files)
- **UI**: Rich (terminal with markdown rendering)

## Success Metrics

### Citation Coverage
- ✅ **Target**: 100% of answers contain citations
- ✅ **Format**: All citations match `[Source: filename, Chunk X]`
- ✅ **Minimum**: ≥2 citations per answer
- ✅ **Quality**: No uncertainty indicators ("I think", "probably", etc.)

### Hallucination Reduction
**Without Citations:**
- Model can make unsupported claims
- No source verification possible
- Hallucinations difficult to detect

**With Mandatory Citations:**
- ✅ Every fact requires source attribution
- ✅ Model restricted to provided context
- ✅ Users can verify each claim
- ✅ Missing information explicitly stated
- ✅ Hallucinations eliminated by design

## Example Interaction

```
You: /load-koog
✓ Koog collection already loaded from cache

You: /ask What is the A2A protocol?

🔍 Asking with RAG (collection: koog)...
======================================================================

╭────────────────────────────── Question ──────────────────────────────╮
│  What is the A2A protocol?                                           │
╰──────────────────────────────────────────────────────────────────────╯

╭────────────── Answer (with mandatory citations) ─────────────────────╮
│                                                                       │
│  The A2A (Agent-to-Agent) protocol is a standardized protocol for    │
│  communication between AI agents [Source: AGENT.md, Chunk 1].        │
│                                                                       │
│  It defines how agents discover each other, exchange messages, and   │
│  coordinate tasks [Source: a2a-core/Module.md, Chunk 2]. The         │
│  protocol uses JSON-RPC as its transport mechanism [Source:          │
│  a2a-transport/README.md, Chunk 3].                                  │
│                                                                       │
╰──────────────────────────────────────────────────────────────────────╯

📚 Sources used (5 chunks):
  1. AGENT.md (Chunk 1, distance: 165.43)
  2. a2a-core/Module.md (Chunk 2, distance: 172.18)
  3. a2a-transport/README.md (Chunk 3, distance: 178.92)
  4. README.md (Chunk 1, distance: 183.15)
  5. a2a-client/Module.md (Chunk 5, distance: 189.76)

======================================================================
```

## References

- [Ollama](https://ollama.com/) - Local LLM runtime
- [mxbai-embed-large](https://ollama.com/library/mxbai-embed-large) - Embedding model on Ollama
- [Koog](https://github.com/JetBrains/koog) - JetBrains AI framework
- [RAG Paper](https://arxiv.org/abs/2005.11401) - Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
- [ChromaDB Documentation](https://docs.trychroma.com/) - Vector database for embeddings
- [Google Gemini API](https://ai.google.dev/) - Gemini models and embeddings
- [RAG Survey](https://arxiv.org/abs/2312.10997) - Recent survey on RAG techniques

---

## License

Educational project for AI Advent Challenge
