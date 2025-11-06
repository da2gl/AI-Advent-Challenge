# Day 27: Local LLM with Ollama vs Cloud LLM Comparison

This project extends Day 26 by adding support for local LLMs via Ollama, enabling comparison between local and cloud-based AI models.

## Features

- **Dual-mode LLM support**: Switch between Ollama (local) and Gemini (cloud) via `/model` command
- **Unified interface**: Both providers use the same API interface for compatibility
- **Runtime configuration**: Switch providers and models without restarting
- **All Day 26 features preserved**: MCP integration, RAG, voice input, etc.

## Setup

### 1. Install Ollama

Download and install Ollama from [ollama.com](https://ollama.com/)

```bash
# For macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

### 2. Pull Qwen 2.5 Coder Tools Model

```bash
# Pull Qwen 2.5 Coder Tools 7B model (best for tool calling and coding)
ollama pull hhao/qwen2.5-coder-tools:7b

# Verify the model is available
ollama list
```

### 3. Start Ollama Server

```bash
# Start Ollama server (runs on http://localhost:11434 by default)
ollama serve
```

### 4. Install Python Dependencies

```bash
cd day27
pip install -r requirements.txt
```

### 5. Set API Key (for Gemini)

If you want to use Gemini (cloud), set your API key:

```bash
export GEMINI_API_KEY=your_api_key_here
```

For Ollama usage, no API key is required.

## Usage

### Basic Chat

```bash
# Run chat (starts with Gemini by default)
python chat.py

# Use /model command to switch between Gemini and Ollama
# Select Ollama → Qwen 2.5 Coder Tools for local usage
```

### Key Differences from Day 26

1. **Multi-Provider Support**: Can switch between Gemini (cloud) and Ollama (local) via `/model` command
2. **No Env Configuration**: Model selection happens in runtime, not via environment variables
3. **Local LLM Option**: Ollama allows privacy-focused, offline usage
4. **Directive Prompts for Ollama**: Qwen requires more explicit instructions for tool calling compared to Gemini

### Working with Qwen and MCP Tools

Qwen requires more **directive prompts** for tool calling compared to Gemini:

**❌ Vague (may not work):**
```
@rag/reranker.py write tests and run
```

**✓ Directive (works well):**
```
Read rag/reranker.py using filesystem_read_file, then create tests
```

**✓ Step-by-step (best):**
```
Step 1: Call filesystem_read_file with path="rag/reranker.py"
Step 2: Create tests using filesystem_write_file
Step 3: Run pytest using shell_execute_command
```

## Architecture

### Core Components

1. **ollama_client.py**: Ollama API client with Gemini-compatible interface
2. **llm_provider.py**: Provider abstraction and factory pattern
3. **chat.py**: Updated to use provider abstraction

### Provider Switching

Use the `/model` command in chat to switch between providers:

1. Start chat: `python chat.py`
2. Type `/model` to open provider/model selection
3. Choose provider (Gemini or Ollama)
4. Choose model for that provider
5. Continue chatting with new provider

## Testing

### Test Code Generation

```
You: Write a Python function to calculate factorial

AI: [Response from local LLM]
```

### Test General Conversation

```
You: Explain what LLMs are

AI: [Response from local LLM]
```

### Test with MCP Tools

```
You: @calculator.py create unit tests for this file

AI: [Uses MCP tools to read file, generate tests, and save them]
```

## Comparison: Ollama vs Gemini

### Ollama (Local) - Qwen 2.5 Coder Tools

**Pros:**
- Privacy: Data never leaves your machine
- No API costs
- No rate limits
- Works offline
- Fast response times (depends on hardware)
- Good code generation capabilities

**Cons:**
- Requires local compute resources (~8GB RAM for 7B model)
- Weaker tool calling compared to Gemini (needs directive prompts)
- May not follow complex multi-step instructions reliably
- Limited to models you can run locally

**Best for:**
- Privacy-sensitive applications
- Cost-conscious usage
- Offline environments
- Simple coding tasks
- Single-step tool operations

### Gemini (Cloud)

**Pros:**
- More powerful models (gemini-2.5-pro)
- No local compute requirements
- Always up-to-date
- Superior reasoning capabilities
- **Excellent tool calling** - understands complex instructions naturally
- Reliable multi-step workflows with MCP tools

**Cons:**
- Requires API key and costs money
- Rate limits apply
- Requires internet connection
- Data sent to Google

**Best for:**
- Complex reasoning tasks
- Production applications
- Multi-step automated workflows
- When you need reliable tool calling with MCP
- Complex coding tasks requiring multiple operations

## Performance Notes

### Qwen 2.5 Coder Tools (7B)

- **Speed**: Fast on modern CPUs (slower on GPU)
- **Quality**: Good for code generation, weaker at tool calling
- **Memory**: ~8GB RAM required
- **Tool Calling**: Requires explicit, directive prompts
- **Use Case**: Best for single-file code generation or direct commands

### Gemini 2.5 Flash

- **Speed**: Very fast (cloud API, ~1-3 seconds)
- **Quality**: Excellent reasoning, code generation, and tool calling
- **Cost**: Pay per token (free tier available)
- **Tool Calling**: Natural understanding, handles complex multi-step tasks
- **Use Case**: Best for complex workflows, autonomous agents

## Troubleshooting

### Ollama Connection Error

```
Connection error - is Ollama running? Try: ollama serve
```

**Solution**: Make sure Ollama server is running:
```bash
ollama serve
```

### Model Not Found

```
Error: model 'hhao/qwen2.5-coder-tools:7b' not found
```

**Solution**: Pull the model first:
```bash
ollama pull hhao/qwen2.5-coder-tools:7b
```

### Qwen Not Calling MCP Tools

If Qwen responds with text instead of calling tools:

**Solution**: Use more directive prompts:
```
Instead of: "@file.py write tests"
Try: "Call filesystem_read_file with path='file.py'"
```

### Port Already in Use

If port 11434 is already in use, specify a different port:

```bash
OLLAMA_HOST=0.0.0.0:11435 ollama serve
export OLLAMA_BASE_URL=http://localhost:11435
```

## Available Ollama Models

Common models you can pull:

```bash
# Recommended for MCP Tool Calling
ollama pull hhao/qwen2.5-coder-tools:7b  # Best for tool calling + coding

# Code-focused (no tool calling)
ollama pull qwen2.5-coder                # 7B, good at coding but weak tool calling
ollama pull codellama                     # 7B parameters

# General Purpose
ollama pull llama3.2        # 3B parameters, weak tool calling
ollama pull llama3.1        # 8B parameters
ollama pull mistral         # 7B parameters

# Large & Powerful (no tool calling optimization)
ollama pull llama3.1:70b    # 70B parameters (requires ~40GB RAM)
```

**Note:** Most base Ollama models have weaker tool calling capabilities compared to Gemini. The `hhao/qwen2.5-coder-tools:7b` variant is specifically fine-tuned for tool calling.

## References

- [Google Gemini API](https://ai.google.dev/) - Gemini models and function calling
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) - Protocol for AI-tool integration
- [MCP Filesystem Server](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) - File operations via MCP
- [Ollama](https://ollama.com/) - Run large language models locally
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