# Day 19: Document Indexing with ChromaDB

**Build a complete document indexing pipeline with semantic search capabilities**

## Overview

This project implements a 4-stage document indexing pipeline that enables semantic search over your documents using embeddings and vector similarity. It's the foundation for building RAG (Retrieval-Augmented Generation) systems.

## Key Features

### 🔄 4-Stage Pipeline
- **Stage 1: Document Loading** - Multi-format support (`.md`, `.rst`, `.txt`, `.py`, `.js`, `.pdf`)
- **Stage 2: Text Chunking** - Smart chunking (500 chars) with sentence boundary detection and overlap
- **Stage 3: Embedding Generation** - Gemini `text-embedding-004` model (768 dimensions)
- **Stage 4: ChromaDB Indexing** - Persistent vector storage with metadata

### 💬 Interactive Chat Interface
- **Multi-collection support** - Organize documents into separate collections
- **Semantic search** - Find relevant chunks by meaning, not just keywords
- **AI integration** - Ask questions about search results using Gemini
- **Conversation history** - Persistent SQLite storage

### 📚 Collection Management
- Create named collections for different document sets
- Search within specific collections or across all
- List collections with statistics
- Delete individual collections or clear all data

## Pipeline Architecture

```
┌─────────────────────────────────┐
│  Input: Files/Directories       │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│  Stage 1: Document Loader       │
│  • Load .md, .rst, .txt, .py    │
│  • Extract metadata             │
│  • Handle encoding              │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│  Stage 2: Text Chunker          │
│  • Split into 500-char chunks   │
│  • 50-char overlap              │
│  • Sentence boundary detection  │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│  Stage 3: Embedding Generator   │
│  • Gemini text-embedding-004    │
│  • Batch processing (100/batch) │
│  • 768-dimensional vectors      │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│  Stage 4: ChromaDB Index        │
│  • Store vectors + metadata     │
│  • Persistent storage           │
│  • Fast similarity search       │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│  Output: Searchable Index       │
└─────────────────────────────────┘
```

## Project Structure

```
day19/
├── pipeline/
│   ├── document_loader.py        # Stage 1: File loading (.md, .rst, .txt, .py, .pdf)
│   ├── text_chunker.py           # Stage 2: Text chunking
│   ├── embedding_generator.py    # Stage 3: Gemini embeddings
│   ├── index_manager.py          # Stage 4: ChromaDB operations
│   ├── pipeline_executor.py      # Orchestrator
│   └── __init__.py
├── core/
│   ├── gemini_client.py          # Gemini API client
│   ├── conversation.py           # Chat history manager
│   ├── storage.py                # SQLite persistence
│   └── __init__.py
├── data/
│   ├── chroma_db/                # ChromaDB storage (generated)
│   └── conversations.db          # Chat history (generated)
├── requests-docs/                # Git submodule: Requests library docs
│   └── docs/                     # 15 .rst files with documentation
├── chat.py                       # Main interactive CLI
├── requirements.txt
└── README.md
```

## Installation

1. **Clone repository with submodules:**
```bash
cd day19
git submodule update --init --recursive
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set Gemini API key:**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Quick Start

```bash
# Start chat interface
python3 chat.py

# Index the Requests documentation (15 .rst files)
You: /index requests-docs/docs --collection requests_docs

# Search for topics
You: /search "how to make HTTP requests"
You: /search "authentication methods"
```

## Usage

### Commands Reference

#### Document Indexing
```bash
/index <path> [--collection <name>]
```

**Examples:**
```
# Index Requests documentation
/index requests-docs/docs --collection requests_docs

# Index with auto-generated collection name
/index requests-docs/docs

# Index single file
/index requests-docs/docs/user/quickstart.rst
```

#### Searching
```bash
/search <query> [--collection <name>]
```

**Examples:**
```
# Search all collections
/search "making HTTP requests"

# Search specific collection
/search "authentication" --collection requests_docs

# Natural language queries
/search "How to handle errors and exceptions?"
/search "What are session objects?"
/search "How to send POST requests with JSON?"
```

#### Collection Management
```bash
/list-collections              # Show all collections
/delete-collection <name>      # Delete specific collection
/clear-index                   # Clear ALL data (requires confirmation)
```

#### Chat Commands
```bash
/resume      # Load previous conversation
/clear       # Start new conversation
/model       # Change AI model
/help        # Show all commands
/quit        # Exit
```

## Example Workflow

```bash
$ python3 chat.py

================================================================
     DOCUMENT INDEXING CHAT - AI Assistant
================================================================

You: /index requests-docs/docs --collection requests_docs

📚 Indexing: requests-docs/docs
Collection: requests_docs
======================================================================
📄 Stage 1: Loading documents...
  ✓ Loaded 15 documents (52840 chars)
✂️  Stage 2: Chunking text...
  ✓ Created 68 chunks (avg: 490 chars)
🧠 Stage 3: Generating embeddings...
  Processing batch 1/1 (68 chunks)...
  ✓ Generated 68 embeddings (100.0% success)
💾 Stage 4: Indexing in ChromaDB...
  ✓ Indexed 68 chunks in collection 'requests_docs'

======================================================================
✓ Indexing complete!
  Documents loaded: 15
  Chunks created: 68
  Embeddings generated: 68
  Documents indexed: 68

💡 Try: /search "your query" --collection requests_docs

You: /search "How to make HTTP requests?"

🔍 Searching for: "How to make HTTP requests?"
Collection: All collections
======================================================================

📋 Found 5 results:

╭─ Result 1 ───────────────────────────────────╮
│ Making Requests                               │
│ ===============                               │
│                                               │
│ Making a request with Requests is very        │
│ simple. Begin by importing the Requests       │
│ module::                                      │
│                                               │
│     >>> import requests                       │
│                                               │
│ Now, let's try to get a webpage...           │
│                                               │
│ Source: quickstart.rst                        │
│ Chunk: 3 | Distance: 0.2156                  │
╰───────────────────────────────────────────────╯

[More results...]

💡 You can now ask AI questions about these results!

You: Show me examples of POST requests

AI: Based on the documentation, here are examples
    of making POST requests with the Requests library:

    1. Simple POST request:
    >>> r = requests.post('https://httpbin.org/post',
                          data={'key':'value'})

    2. Sending JSON data:
    >>> r = requests.post('https://httpbin.org/post',
                          json={'key': 'value'})

    [AI continues with detailed explanation...]

You: /list-collections

📚 Collections
┌────────────────┬───────────┬─────────────────────┐
│ Name           │ Documents │ Metadata            │
├────────────────┼───────────┼─────────────────────┤
│ requests_docs  │ 68        │ source_path: requ.. │
└────────────────┴───────────┴─────────────────────┘

Total: 1 collections, 68 documents
```

## Technical Details

### Pipeline Configuration
- **Chunk Size**: 500 characters
- **Overlap**: 50 characters  
- **Embedding Model**: `text-embedding-004`
- **Embedding Dimensions**: 768
- **Batch Size**: 100 chunks per API call
- **Vector DB**: ChromaDB with persistence

### Supported File Types
- Markdown (`.md`)
- reStructuredText (`.rst`) - **Sphinx/Python docs**
- Text files (`.txt`)
- Python (`.py`)
- JavaScript (`.js`)
- Java (`.java`)
- Go (`.go`)
- Rust (`.rs`)
- C++ (`.cpp`)
- PDF (`.pdf`) - requires PyPDF2

### API Rate Limits
- Gemini Free Tier: 1,500 embedding requests/day
- 1 request = 1 batch (up to 100 texts)
- **Requests docs**: 15 files → ~68 chunks (well within limits!)

### Performance
- **Loading**: ~50ms per file
- **Chunking**: ~100ms for 10k chars
- **Embeddings**: 1-2s per batch (100 chunks)
- **Indexing**: ~50ms per batch
- **Search**: <100ms for 1M vectors

## Advanced Usage

### Batch Indexing Multiple Directories

```bash
# Index Requests documentation
/index requests-docs/docs --collection requests_docs

# Index your own project documentation
/index my-project/docs --collection my_docs

# Search across all collections
/search "authentication examples"

# Search specific collection
/search "authentication" --collection requests_docs
```

### Custom Chunking Strategy

Modify `pipeline/text_chunker.py`:

```python
# Larger chunks for technical docs
chunker = TextChunker(chunk_size=1000, overlap=100)

# Smaller chunks for Q&A
chunker = TextChunker(chunk_size=300, overlap=30)
```

### Metadata Filtering

Search with metadata filters (modify `index_manager.py`):

```python
results = index_manager.search(
    query_embedding=embedding,
    where={"file_type": "py"},  # Only Python files
    top_k=5
)
```

## Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### "API key not set"
```bash
export GEMINI_API_KEY="your-key"
# Or set in ~/.bashrc or ~/.zshrc
```

### "Rate limit exceeded"
- Wait 24 hours for quota reset
- Reduce chunk count (index fewer documents)
- Use smaller chunk sizes

### "No search results"
- Check collection name spelling
- Try broader search queries
- Verify documents were indexed: `/list-collections`

### ChromaDB errors
```bash
# Clear and restart
rm -rf data/chroma_db
python3 chat.py
```

## Learning Outcomes

This project demonstrates:

1. **Document Processing Pipeline**: Multi-stage data transformation
2. **Text Chunking Strategies**: Overlap and boundary detection
3. **Embedding Generation**: Converting text to vectors
4. **Vector Databases**: ChromaDB for similarity search
5. **Semantic Search**: Meaning-based retrieval vs keywords
6. **Collection Management**: Organizing vector spaces
7. **RAG Foundation**: Building blocks for retrieval systems

## What is RAG?

**RAG (Retrieval-Augmented Generation)** combines:
- **Retrieval**: Find relevant documents (what we built!)
- **Augmentation**: Add documents to LLM context
- **Generation**: LLM answers using retrieved info

This project completes the **Retrieval** component. Add LLM context injection for full RAG!

## Next Steps

To build full RAG:
1. ✅ **Indexing** (this project)
2. Search for relevant chunks
3. Inject chunks into LLM prompt
4. Generate answer with context

Example RAG flow:
```python
# 1. Search (already implemented)
results = pipeline.search("How to use async in Python?")

# 2. Build context
context = "\n\n".join([r.text for r in results])

# 3. Create prompt with context
prompt = f"""Based on these documents:
{context}

Answer: How to use async in Python?"""

# 4. Generate answer
response = gemini.generate_content(prompt)
```

## References

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Google Gemini API](https://ai.google.dev/)
- [Sentence Transformers](https://www.sbert.net/)
- [RAG Paper](https://arxiv.org/abs/2005.11401)

---

## License

Educational project for AI Advent Challenge
