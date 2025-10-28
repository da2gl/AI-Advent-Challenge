# Day 20: RAG Comparison - With vs Without Retrieval

**Compare model responses with and without Retrieval-Augmented Generation (RAG)**

## Overview

This project demonstrates the difference between asking an LLM questions with and without retrieval-augmented generation. It uses the SQuAD dataset to show where RAG provides clear benefits and where the model can answer without additional context.

## Key Features

### 🔍 RAG Comparison
- **Two modes**: Compare responses with RAG vs without RAG side-by-side
- **SQuAD integration**: Load Stanford Question Answering Dataset for testing
- **Batch testing**: Test multiple questions automatically
- **Detailed metrics**: Response time, token usage, retrieval quality

### 📊 Visual Comparison
- Side-by-side panels showing both responses
- Retrieved context chunks with distances
- Performance metrics (time, tokens)
- Analysis of when RAG helps

### 🎯 Real-world Testing
- Uses actual questions from SQuAD validation set
- Shows specific factual questions where RAG excels
- Demonstrates limitations of non-RAG approaches

## Project Structure

```
day20/
├── rag/                         # RAG comparison modules
│   ├── squad_loader.py          # Load SQuAD dataset
│   ├── rag_comparator.py        # Compare with/without RAG
│   └── __init__.py
├── pipeline/                    # From day19: Document indexing
│   ├── document_loader.py       # Stage 1: File loading
│   ├── text_chunker.py          # Stage 2: Text chunking
│   ├── embedding_generator.py   # Stage 3: Gemini embeddings
│   ├── index_manager.py         # Stage 4: ChromaDB operations
│   └── pipeline_executor.py     # Orchestrator
├── core/                        # From day19: Core utilities
│   ├── gemini_client.py         # Gemini API client
│   ├── conversation.py          # Chat history manager
│   ├── storage.py               # SQLite persistence
│   └── text_manager.py          # Token utilities
├── data/
│   ├── chroma_db/               # ChromaDB storage (generated)
│   ├── squad_cache/             # SQuAD dataset cache (generated)
│   └── conversations.db         # Chat history (generated)
├── chat.py                      # Main interactive CLI
├── requirements.txt
└── README.md
```

## Installation

**Install dependencies:**
```bash
cd day20
pip install -r requirements.txt
```

**Set up API key:**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Usage

### Start Chat Interface

```bash
python chat.py
```

### RAG Comparison Commands

#### 1. Load SQuAD Dataset
```bash
/load-squad [--limit <n>]
```
- Downloads and indexes SQuAD validation dataset
- Dataset cached locally in `data/squad_cache/` (~35MB)
- Default limit: 500 examples
- Automatically deletes old collection if exists
- Shows all 4 pipeline stages:
  - Stage 1: Loading dataset (downloads on first run)
  - Stage 2: Chunking contexts
  - Stage 3: Generating embeddings
  - Stage 4: Indexing to ChromaDB

**Example:**
```bash
/load-squad --limit 100
```

**Note:** First run downloads the dataset (~35MB), subsequent runs use cached version.

#### 2. Show Dataset Info
```bash
/squad-info
```
- Shows statistics about loaded SQuAD dataset
- Displays last 10 questions with topics and answers
- Suggests 5 random questions to try
- Helps you find interesting questions to test

**Example Output:**
```
📚 SQuAD Dataset Information
══════════════════════════════════════════════════════════

Total examples loaded: 500
Unique contexts: 93

📝 Sample Questions (last 10):

  [1] To whom did the Virgin Mary allegedly appear in 1858?
      Topic: University_of_Notre_Dame
      Answer: Saint Bernadette Soubirous
  ...

💡 Suggested questions to try:
  1. When did the Methodists break away from the Anglican Church?
  2. What was the average family size in 2000?
  3. In which country is Normandy located?
  ...
```

#### 3. Compare Single Question
```bash
/compare <question>
```
- Compares response with and without RAG
- Shows retrieved context chunks
- Displays performance metrics

**Example:**
```bash
/compare What year did the first Super Bowl take place?
```

**Output:**
```
┌─ Question ─────────────────────────────────────┐
│ What year did the first Super Bowl take place? │
├─ WITHOUT RAG ──────────────────────────────────┤
│ I believe it was in 1967...                    │
│ Time: 1.2s | Tokens: ~50                       │
├─ WITH RAG ──────────────────────────────────────┤
│ According to the passage, the first Super Bowl │
│ took place in 1967.                            │
│ Time: 2.3s | Tokens: ~280                      │
│ Retrieved: 3 chunks from squad collection      │
├─ ANALYSIS ──────────────────────────────────────┤
│ • RAG added 3 context chunks                   │
│ • Response time: +1.1s                         │
│ • Token usage: +230 tokens                     │
└─────────────────────────────────────────────────┘
```

#### 4. Batch Compare
```bash
/batch-compare [--count <n>]
```
- Tests multiple questions from SQuAD dataset
- Default count: 10 questions
- Shows summary statistics

**Example:**
```bash
/batch-compare --count 20
```

**Output:**
```
📊 Batch Comparison Summary
══════════════════════════════════════════════════
Questions tested: 20
Average time without RAG: 1.15s
Average time with RAG: 2.34s
Average tokens without RAG: 65
Average tokens with RAG: 285

RAG overhead: +1.19s per query
RAG token cost: +220 tokens per query
══════════════════════════════════════════════════
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

- **LLM**: Google Gemini 2.5 Flash/Pro
- **Embeddings**: Gemini text-embedding-004 (768 dimensions)
- **Vector DB**: ChromaDB
- **Dataset**: SQuAD (Stanford Question Answering Dataset)
- **UI**: Rich (terminal formatting)
- **Storage**: SQLite (conversation history)

## Performance Notes

- **Embedding generation**: ~100 chunks per batch
- **Vector search**: Top-k retrieval (default k=3)
- **Token overhead**: RAG adds ~200-300 tokens per query
- **Time overhead**: RAG adds ~1-2 seconds per query
- **Benefit**: Significantly higher accuracy for specific facts

## Key Implementation Details

### Local Data Storage
- **SQuAD cache**: Downloaded dataset stored in `data/squad_cache/` (not in `~/.cache/`)
- **ChromaDB**: Vector database in `data/chroma_db/`
- **Session data**: SQuAD examples loaded in memory each session
- **Tip**: Use `/load-squad` at start of each session to reload data

### Auto-cleanup
- Loading SQuAD automatically deletes old "squad" collection
- Prevents duplicate data accumulation
- Ensures fresh indexing on each load

### Dataset Exploration
- Use `/squad-info` to see what's loaded
- Shows last 10 questions (most diverse)
- Suggests random questions from loaded set
- No need to guess what to ask!

## Troubleshooting

### ModuleNotFoundError: No module named 'datasets'
```bash
pip install datasets
```

### API Rate Limits
- Reduce batch size with `--count` parameter
- Add delays between requests if needed

### ChromaDB Collection Not Found
```bash
# Load SQuAD first
/load-squad
```

### "No SQuAD dataset loaded" when using /squad-info
- SQuAD examples are stored in memory only
- Need to run `/load-squad` each session
- ChromaDB persists, but Python objects don't

## Conclusion

This project demonstrates that RAG is not always necessary but provides significant benefits when:
- Questions require specific factual information
- Answers need to be sourced from documents
- Information is not in the model's training data

The trade-off is increased token usage and response time, which is worthwhile for accuracy-critical applications.

## References

- [SQuAD Dataset](https://rajpurkar.github.io/SQuAD-explorer/) - Stanford Question Answering Dataset
- [RAG Paper](https://arxiv.org/abs/2005.11401) - Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
- [ChromaDB Documentation](https://docs.trychroma.com/) - Vector database for embeddings
- [Google Gemini API](https://ai.google.dev/) - Gemini models and embeddings
- [HuggingFace Datasets](https://huggingface.co/docs/datasets/) - Dataset library
- [RAG Survey](https://arxiv.org/abs/2312.10997) - Recent survey on RAG techniques

---

## License

Educational project for AI Advent Challenge
