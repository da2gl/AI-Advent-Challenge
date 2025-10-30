# Day 22: RAG with Mandatory Citations and Sources

## Overview

RAG system that **requires mandatory citations and source references** in all model responses to reduce hallucinations and improve answer reliability. Every fact in the answer must be attributed to a specific source document and chunk.

## Key Features

### 🎯 Mandatory Citations
- **Every fact must be cited** - Model cannot provide information without source attribution
- **Structured format** - `[Source: filename, Chunk X]` after each claim
- **No hallucinations** - Model explicitly restricted to provided context only
- **Explicit unavailability** - States "This information is not available in the provided sources" if data missing

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

### RAG Pipeline with Citations

```
Question
    ↓
1. Generate embedding (Ollama mxbai-embed-large)
    ↓
2. Search ChromaDB for relevant chunks (top-5)
    ↓
3. Build context with source markers:
   [Source: file1.md, Chunk 2]
   Content from file1...

   [Source: file2.md, Chunk 5]
   Content from file2...
    ↓
4. Enhanced prompt with MANDATORY CITATION RULES:
   - MUST cite source for EVERY fact
   - Use format: [Source: filename, Chunk X]
   - DO NOT provide unsourced information
   - Stay within provided context only
    ↓
5. Gemini generates answer WITH citations
    ↓
6. Display answer + source list
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
cd day22
python chat.py
```

### Load Documentation
```bash
/load-koog
```
Loads JetBrains Koog documentation (165 markdown files) using Ollama embeddings.

### Ask Questions with RAG
```bash
/ask What is the A2A protocol and what is it used for?
```

**Output:**
```
╭────────────────────────────── Question ──────────────────────────────╮
│  What is the A2A protocol and what is it used for?                   │
╰──────────────────────────────────────────────────────────────────────╯

╭────────────── Answer (with mandatory citations) ─────────────────────╮
│                                                                       │
│  The A2A (Agent-to-Agent) protocol is a standardized communication   │
│  protocol for AI agents [Source: AGENT.md, Chunk 1].                 │
│                                                                       │
│  It is used for enabling seamless communication between different    │
│  AI agents in distributed systems [Source: a2a-core/Module.md,       │
│  Chunk 2]. The protocol provides a JSON-RPC based transport layer    │
│  for message exchange [Source: a2a-transport/README.md, Chunk 4].    │
│                                                                       │
╰──────────────────────────────────────────────────────────────────────╯

📚 Sources used (5 chunks):
  1. AGENT.md (Chunk 1, distance: 165.43)
  2. a2a-core/Module.md (Chunk 2, distance: 172.18)
  3. a2a-transport/README.md (Chunk 4, distance: 178.92)
  4. a2a-client/Module.md (Chunk 3, distance: 181.47)
  5. README.md (Chunk 1, distance: 189.23)
```

### View Documentation Info
```bash
/koog-info
```
Shows loaded documents and suggests sample questions.

### Available Commands
```
RAG with Citations & Sources:
  /load-koog [--force]  - Load Koog docs (cached, use --force to reindex)
  /koog-info            - Show loaded docs & suggest questions
  /ask <question>       - Ask question using RAG with mandatory citations

Document Indexing:
  /index <path>         - Index documents
  /search <query>       - Search index
  /list-collections     - Show all collections

Chat Commands:
  /resume    - Load previous dialog
  /clear     - Delete current dialog
  /model     - Change Gemini model
  /help      - Show all commands
  /quit      - Exit
```

## Technical Details

### Architecture
```
day22/
├── chat.py                      # Main chat interface with /ask command
├── rag/
│   └── rag_comparator.py        # RAG with mandatory citations prompt
├── pipeline/
│   ├── ollama_embedding_generator.py  # Ollama embeddings (1024d)
│   └── index_manager.py         # ChromaDB operations
└── data/
    └── chroma_db/               # Persisted vector database
```

### Citation Pattern (Regex)
```python
pattern = r'\[Source:\s*([^,]+),\s*Chunk\s+(\d+)\]'
```

Matches:
- `[Source: AGENT.md, Chunk 1]`
- `[Source: a2a-core/Module.md, Chunk 3]`
- `[Source: README.md, Chunk 5]`

### Prompt Location
- **File**: `rag/rag_comparator.py`
- **Method**: `_ask_with_rag()`
- **Lines**: ~216-236

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
