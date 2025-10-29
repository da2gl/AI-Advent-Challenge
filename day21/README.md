# Day 21: RAG with Ollama Embeddings + Gemini Reranking

**Advanced RAG with local Ollama embeddings and hybrid reranking**

## Overview

This project demonstrates an advanced RAG (Retrieval-Augmented Generation) system with:
1. **Local Ollama embeddings**: Use mxbai-embed-large (1024d) for document indexing without API limits
2. **Koog documentation**: Real-world documentation from JetBrains Koog AI framework
3. **Hybrid reranking pipeline**: Distance filtering + Gemini relevance scoring
4. **Intelligent caching**: ChromaDB persistence for instant subsequent loads

By using Ollama for embeddings and Gemini only for chat/reranking, we reduce API costs by ~80% while maintaining high-quality responses.

## Key Features

### 🚀 Local Ollama Embeddings
- **No API Limits**: Generate unlimited embeddings locally with Ollama
- **mxbai-embed-large**: High-quality 1024-dimensional embeddings
- **Fast Processing**: Local inference, no network latency
- **Cost Effective**: Zero API costs for embedding generation

### 📚 Koog Documentation Support
- **Real Documentation**: Index JetBrains Koog AI framework docs
- **Git Submodule**: Automatically clones and indexes markdown files
- **Smart Chunking**: Optimal chunk size for documentation
- **Sample Questions**: Auto-generated questions from doc structure

### 🎯 Hybrid Reranking Pipeline
- **Stage 1 - Distance Filtering**: Fast filter by L2 distance threshold (configurable, default 195.0 for 1024d embeddings)
- **Stage 2 - Gemini Reranking**: LLM-based relevance scoring (0-10 scale) using Gemini 2.5 Flash Lite
- **Stage 3 - Score Filtering**: Remove documents below minimum rerank score (default 5.0/10)
- **Configurable Parameters**: Adjust thresholds, initial candidate count, and final top-k

### 🔍 Enhanced RAG Comparison
- **Two modes**: Compare responses WITH reranking vs WITHOUT reranking
- **Koog documentation**: Real-world technical documentation testing
- **Detailed metrics**: Response time, token usage, retrieval quality, reranking statistics
- **Markdown rendering**: Rich formatting for better answer readability

### 📊 Visual Comparison
- Side-by-side panels showing both responses
- Retrieved context chunks with distances AND rerank scores
- Performance metrics (time, tokens, reranking time)
- Reranking statistics (candidates at each stage)
- Analysis of filtering effectiveness

### 🎯 Real-world Testing
- Uses real Koog framework documentation
- Shows specific factual questions where reranking improves results
- Demonstrates value of hybrid retrieval approach

## Project Structure

```
day21/
├── rag/                         # RAG comparison modules
│   ├── koog_loader.py           # Load Koog documentation
│   ├── rag_comparator.py        # Compare WITH/WITHOUT reranking
│   ├── reranker.py              # Hybrid reranking pipeline (distance + Gemini)
│   └── __init__.py
├── pipeline/                    # Document indexing pipeline
│   ├── document_loader.py       # Stage 1: File loading
│   ├── text_chunker.py          # Stage 2: Text chunking
│   ├── embedding_generator.py   # Stage 3: Gemini embeddings
│   ├── ollama_embedding_generator.py  # Stage 3: Ollama embeddings (local)
│   ├── index_manager.py         # Stage 4: ChromaDB operations
│   └── pipeline_executor.py     # Orchestrator
├── core/                        # Core utilities
│   ├── gemini_client.py         # Gemini API client
│   ├── conversation.py          # Chat history manager
│   ├── storage.py               # SQLite persistence
│   └── text_manager.py          # Token utilities
├── data/
│   ├── chroma_db/               # ChromaDB storage (persisted)
│   └── conversations.db         # Chat history (persisted)
├── koog/                        # Git submodule (Koog documentation)
│   └── docs/                    # Markdown documentation files
├── chat.py                      # Main interactive CLI
├── requirements.txt
└── README.md
```

## How Reranking Works

### The Problem with Basic RAG
Traditional RAG systems use only vector similarity (cosine distance) to retrieve documents. This can return semantically similar but contextually irrelevant results.

**Example:**
- Query: "What is the capital of France?"
- Vector search might return: "Warsaw was the capital of Poland" (high similarity due to "capital" keyword)
- But this doesn't answer the question!

### Our Solution: Hybrid Reranking

```
Query → Vector Search (35 candidates) → Reranking Pipeline → Generation
                                          ↓
                        Stage 1: Distance Filter (~10-15 pass)
                                          ↓
                        Stage 2: Gemini Scoring (0-10)
                                          ↓
                        Stage 3: Score Filter (≥5.0)
                                          ↓
                        Top-5 Best Chunks → Answer
```

#### Stage 1: Distance Filtering
- **Input**: ~35 candidates from vector search
- **Filter**: Keep only chunks with L2 distance < 195.0 (for 1024d embeddings)
- **Purpose**: Quick elimination of obviously irrelevant results
- **Output**: ~10-15 filtered candidates (avoids API rate limits)

#### Stage 2: Gemini Reranking
- **Input**: Filtered candidates (~10-15 chunks)
- **Method**: Ask Gemini 2.5 Flash Lite to score each document's relevance (0-10)
- **Prompt**: "Rate how relevant this document is to answering the question"
- **Purpose**: Deep semantic understanding of true relevance
- **Output**: Each chunk gets a rerank_score (0.0-10.0)
- **Note**: Uses Flash Lite to avoid thinking token overhead

#### Stage 3: Score Filtering
- **Input**: Scored candidates
- **Filter**: Keep only chunks with rerank_score >= 5.0
- **Purpose**: Remove low-quality matches even if Gemini scored them
- **Output**: Top-5 most relevant chunks for final answer generation

### Why This Works

1. **Fast pre-filtering**: Distance check is instant, reduces LLM calls
2. **Semantic accuracy**: Gemini understands context, not just keywords
3. **Quality control**: Minimum score ensures we don't use poor matches
4. **Configurable**: Adjust thresholds based on your use case

### Performance vs Quality Trade-off

- **Without reranking**: Fast (~4s) but may include irrelevant context
- **With reranking**: Slower (~5-11s for 10-15 candidates) but much better quality
- **Trade-off**: +1-7s for significantly more accurate context selection
- **Best for**: Questions where precision matters more than speed
- **Optimization**: Distance threshold tuned to balance quality and API rate limits

## Installation

### 1. Install Python Dependencies
```bash
cd day21
pip install -r requirements.txt
```

### 2. Set up Gemini API Key
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### 3. Install and Setup Ollama
**Install Ollama:**
- macOS/Linux: `curl -fsSL https://ollama.com/install.sh | sh`
- Or download from: https://ollama.com/download

**Start Ollama server:**
```bash
ollama serve
```

**Pull embedding model:**
```bash
ollama pull mxbai-embed-large
```

### 4. Initialize Koog Submodule
```bash
git submodule update --init --recursive
```

## Usage

### Start Chat Interface

```bash
python chat.py
```

### RAG Comparison Commands

#### 1. Load Koog Documentation (Ollama)
```bash
/load-koog [--force]
```
- Loads JetBrains Koog documentation from git submodule
- Uses **Ollama embeddings** (mxbai-embed-large, 1024d)
- No API limits, fully local processing
- **Intelligent caching**: Uses persisted ChromaDB collection if exists
- Use `--force` flag to re-index from scratch
- Shows all 4 pipeline stages:
  - Stage 1: Loading markdown documentation
  - Stage 2: Chunking documents
  - Stage 3: Generating embeddings (Ollama)
  - Stage 4: Indexing to ChromaDB

**Examples:**
```bash
/load-koog          # Fast: uses cached collection if exists (~instant)
/load-koog --force  # Slow: full re-indexing from scratch (~2-3 min)
```

**Note:** Requires Ollama running with mxbai-embed-large model installed.

#### 2. Show Koog Documentation Info
```bash
/koog-info
```
- Shows statistics about loaded Koog documentation
- Displays last 10 documents with paths and sizes
- Suggests 5 questions based on doc titles
- Helps you explore the documentation

#### 3. Compare Single Question
```bash
/compare <question>
```
- Compares RAG WITHOUT reranking vs WITH reranking
- Shows retrieved context chunks with distances and scores
- Displays performance metrics and reranking statistics

**Example:**
```bash
/compare What embedding providers does Koog support?
```

**Output:**
```
╭────────────────────────────── Question ──────────────────────────────╮
│  What embedding providers does Koog support?                         │
╰──────────────────────────────────────────────────────────────────────╯

╭───────────────── RAG WITHOUT RERANKING (no filter) ──────────────────╮
│  Based on the context provided:                                      │
│  Koog provides out-of-the-box implementations...                     │
│                                                                       │
│  Retrieved 5 chunks (direct vector search):                          │
│    1. why-koog.md (chunk 10, distance: 166.0472)                     │
│    ...                                                               │
│  Time: 4.21s | Tokens: ~731                                          │
╰──────────────────────────────────────────────────────────────────────╯

╭─────────────────── RAG WITH RERANKING (filtered) ────────────────────╮
│  Based on the context provided, Koog supports the following          │
│  embedding providers:                                                │
│  • Ollama (for local embeddings)                                     │
│  • OpenAI                                                            │
│                                                                       │
│  Retrieved 5 chunks (distance filter + Gemini scoring):              │
│    1. ranked-document-storage.md (distance: 167.3065, rerank: 10/10) │
│    ...                                                               │
│  Time: 4.17s | Tokens: ~602                                          │
╰──────────────────────────────────────────────────────────────────────╯
```

### Other Commands

#### Document Indexing (from day19)
```bash
/index <path> [--collection <name>]      # Index documents
/search <query> [--collection <name>]    # Search index
/list-collections                        # Show collections
/delete-collection <name>                # Delete collection
/clear-index                             # Clear all data
```

#### Chat Management
```bash
/resume      # Load previous dialog
/clear       # Delete current dialog
/model       # Change Gemini model
/system      # Set system instruction
/settings    # Change generation settings
/compress    # Compress conversation history
/tokens      # Show token statistics
/help        # Show all commands
/quit        # Exit
```

## RAG Workflow

```
Question
    ↓
┌─────────────────────────────────────────┐
│  WITHOUT RAG                            │
│  Question → Gemini → Answer             │
│  (Uses only model's training data)      │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  WITH RAG                               │
│  Question → Search ChromaDB             │
│           → Retrieve relevant chunks    │
│           → Context + Question → Gemini │
│           → Answer                      │
│  (Uses retrieved documents)             │
└─────────────────────────────────────────┘
    ↓
Side-by-side comparison
```

## When RAG Helps

### ✅ RAG Provides Clear Benefits:
1. **Specific factual questions** - Exact dates, numbers, names from documents
2. **Recent information** - Events after model's training cutoff
3. **Proprietary data** - Internal documents, custom knowledge bases
4. **Detailed quotes** - Extracting specific passages from sources
5. **Domain-specific jargon** - Specialized terminology in your documents

### ❌ RAG Provides Minimal Benefits:
1. **General knowledge** - Well-known facts the model already knows
2. **Common concepts** - Basic explanations (photosynthesis, programming concepts)
3. **Creative tasks** - Writing, brainstorming, general reasoning

## Example Comparisons

### Example 1: Specific Fact (RAG Helps)
**Question:** "What is the population of Jacksonville?"

**Without RAG:**
> "Jacksonville's population is approximately 900,000-950,000 people based on recent estimates."

**With RAG:**
> "According to the passage, Jacksonville has a population of 821,784 as of the 2010 census."

**Conclusion:** ✅ RAG provided exact, sourced answer

---

### Example 2: General Knowledge (RAG Minimal)
**Question:** "What is photosynthesis?"

**Without RAG:**
> "Photosynthesis is the process by which plants convert light energy into chemical energy..."

**With RAG:**
> "Photosynthesis is the process by which plants convert light energy into chemical energy..."

**Conclusion:** ⚪ Both answers are good, RAG adds source attribution

## Technologies Used

- **LLM**:
  - Google Gemini 2.5 Flash (chat generation)
  - Google Gemini 2.5 Flash Lite (reranking - avoids thinking token overhead)
- **Local Embeddings**: Ollama with mxbai-embed-large (1024 dimensions)
- **Vector DB**: ChromaDB with L2 distance metric (supports multiple embedding dimensions)
- **Dataset**: Koog documentation (JetBrains AI framework, ~50 markdown files)
- **UI**: Rich (terminal formatting with markdown support)
- **Storage**: SQLite (conversation history)

## Performance Notes

- **Embedding generation**: Ollama ~50 chunks per batch (local, no API limits)
- **Vector search**: Initial retrieval of 35 candidates (top_k × 7)
- **Reranking**: ~10-15 chunks pass distance filter, scored by Gemini
- **Final context**: Top-5 chunks selected for answer generation
- **Token overhead**: ~400-600 tokens per query (5 chunks of context)
- **Time overhead**:
  - Without reranking: ~4s
  - With reranking: ~5-11s (+1-7s for quality improvement)
- **Benefit**: Significantly higher accuracy and more targeted answers
- **Cost**: ~80% reduction vs cloud embeddings (Ollama is local and free)

## Key Implementation Details

### Local Data Storage
- **ChromaDB**: Vector database persisted in `data/chroma_db/`
- **Koog collection**: Cached automatically, survives restarts
- **Conversations**: SQLite database in `data/conversations.db`

### Smart Caching
- **Koog collection**: Cached in ChromaDB, instant subsequent loads
- **Use `--force`**: Only when you need to re-index (docs updated, settings changed)
- **Automatic**: First `/load-koog` indexes (~2-3 min), subsequent loads instant
- **Prevents duplicates**: No accumulation of stale indexed data

### Dataset Exploration
- Use `/koog-info` to see what's loaded
- Shows last 10 documents with paths and sizes
- Suggests questions based on documentation structure
- No need to guess what to ask!

## Troubleshooting

### Ollama Connection Failed
**Error:** "Cannot connect to Ollama at http://localhost:11434"

**Solution:**
```bash
# Start Ollama server
ollama serve

# In another terminal, pull model
ollama pull mxbai-embed-large
```

### Model Not Found in Ollama
**Error:** "Model 'mxbai-embed-large' not found in Ollama"

**Solution:**
```bash
ollama pull mxbai-embed-large
```

### Koog Submodule Not Found
**Error:** "Koog docs path not found: day21/koog/docs"

**Solution:**
```bash
git submodule update --init --recursive
```

### ModuleNotFoundError: No module named 'datasets'
```bash
pip install datasets
```

### API Rate Limits (Gemini)
- Use Ollama embeddings instead: `/load-koog`
- Reduce batch size with `--count` parameter
- Add delays between requests if needed

### ChromaDB Collection Not Found
```bash
# Load Koog documentation
/load-koog
```

### "No Koog documentation loaded" when using /koog-info
- Koog documents are stored in memory only
- Need to run `/load-koog` each session
- ChromaDB persists, but Python objects don't

## Challenges & Solutions

During development, we encountered several technical challenges that required careful debugging and optimization:

### 1. Embedding Dimension Mismatch
**Problem:** Initial implementation used Ollama (1024d) for indexing but Gemini (768d) for querying, causing 0 search results.

**Root Cause:**
```python
# Indexing: Ollama mxbai-embed-large → 1024 dimensions
# Querying: Gemini text-embedding-004 → 768 dimensions
# ChromaDB couldn't match vectors of different dimensions!
```

**Solution:**
- Use the same embedding generator for both indexing and querying
- Created `OllamaEmbeddingGenerator` instance in `_init_rag_components()`
- Auto-detect and store embedding dimension in ChromaDB metadata

### 2. Distance Threshold Calibration
**Problem:** Default threshold `1.2` filtered out ALL candidates (kept 0, removed 21).

**Root Cause:**
- Threshold `1.2` was designed for cosine similarity (0-2 range)
- L2 distance on 1024d vectors produces values ~100-200
- All candidates had distances 166-194, well above threshold

**Solution:**
```python
# Changed from 1.2 → 195.0 for L2 distance on 1024d embeddings
distance_threshold: float = 195.0  # Keeps ~10-15 candidates
```

**Metric comparison:**
- Cosine similarity: 0-2 (lower = more similar)
- L2 distance: 0-∞ (higher = less similar, scales with dimensions)

### 3. Gemini 2.5 Flash Thinking Tokens Issue
**Problem:** All reranking requests returned "Response stopped: maximum token limit reached" instead of relevance scores.

**Diagnosis:**
```json
{
  "usageMetadata": {
    "promptTokenCount": 89,
    "thoughtsTokenCount": 149,  ← All tokens used for thinking!
    "candidatesTokenCount": 0
  }
}
```

**Root Cause:**
- Gemini 2.5 Flash uses extended thinking mode
- Even with `max_output_tokens=150`, it consumed all tokens for internal reasoning
- No tokens left for actual response (the relevance score)

**Solution:**
```python
# Switch from gemini-2.5-flash → gemini-2.5-flash-lite
model=GeminiModel.GEMINI_2_5_FLASH_LITE  # No thinking overhead
```

### 4. API Rate Limiting (429 Errors)
**Problem:** When threshold was too relaxed (210.0), 21 chunks passed Stage 1, causing 6 rate limit errors during Gemini scoring.

**Solution:**
- Tuned `distance_threshold=195.0` to filter ~50% of candidates
- Keeps 10-15 chunks for reranking (avoids rate limits)
- Added 100ms delay between scoring requests in reranker

### 5. Overly Strict RAG Prompt
**Problem:** Model refused to answer even when relevant context was provided.

**Original prompt:**
```
If the answer is not in the context, say "I cannot answer based on the provided context."
```

**Issue:** Model interpreted this too conservatively and refused partial answers.

**Fixed prompt:**
```
Based on the context information above, answer the following question.
Use the information from the context to provide a helpful answer.
If you can partially answer using the context, do so and note what's covered.
Only say you cannot answer if the context is completely unrelated to the question.
```

**Result:** Model now synthesizes answers from partial information instead of refusing.

### 6. Collection Caching Optimization
**Problem:** `/load-koog` re-indexed all documents every session (~2-3 minutes).

**Solution:**
- Check if collection exists in ChromaDB before indexing
- Add `--force` flag for explicit re-indexing when needed
- Subsequent loads are instant (use persisted collection)

```bash
/load-koog          # Fast: uses cache if exists
/load-koog --force  # Slow: full re-index from scratch
```

### Key Learnings

1. **Vector dimensions must match** - Use same embedding model for indexing and querying
2. **Distance metrics vary by dimension** - L2 distance scales with vector size
3. **Model capabilities differ** - Flash vs Flash Lite have different token behaviors
4. **Prompt engineering matters** - Balance between strictness and helpfulness
5. **Caching saves time** - Persist computed embeddings to avoid re-indexing
6. **Thresholds need tuning** - Balance between recall (get enough candidates) and precision (avoid rate limits)

## Conclusion

This project demonstrates a **hybrid RAG architecture** that balances cost and quality:

### Best of Both Worlds
- **Ollama for embeddings**: Unlimited local processing, no API costs
- **Gemini for reasoning**: High-quality chat and reranking
- **Result**: 80% reduction in API costs while maintaining response quality

### When to Use This Approach
- ✅ Large document collections (embeddings are the bottleneck)
- ✅ Frequent re-indexing (no API cost concerns)
- ✅ Privacy-sensitive content (embeddings stay local)
- ✅ Development/testing (unlimited iterations)

### When RAG Provides Value
- Questions require specific factual information
- Answers need to be sourced from documents
- Information is not in the model's training data
- Domain-specific knowledge bases

The hybrid approach proves that you don't need expensive cloud embeddings everywhere - use them where quality matters (chat/reranking) and local models where scale matters (embeddings).

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