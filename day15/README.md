# Day 15: Enhanced Dialog History Compression

**Challenge**: Implement an intelligent dialog history compression mechanism that automatically summarizes older conversations to reduce token usage while maintaining conversation quality.

**Result**: An AI assistant that compresses conversation history when token usage reaches a threshold, replacing old messages with detailed summaries that preserve context and enable natural conversation continuation.

## What You'll Learn

- 🗜️ **Automatic compression**: Token-based compression triggers
- 📝 **Smart summarization**: Context-preserving AI summaries with enhanced prompts
- 💾 **Memory management**: Keep recent messages, summarize old ones
- 📊 **Efficiency tracking**: Detailed compression statistics

---

## Quick Start

```bash
# 1. Install dependencies
cd day15
pip install -r requirements.txt

# 2. Set API key
export GEMINI_API_KEY="your-key-here"

# 3. Run the assistant
python chat.py

# 4. Have a long conversation and watch automatic compression
You: Let's talk about Python programming
Assistant: Sure! What would you like to know?
# ... continue chatting ...
# When tokens reach 25,000, history auto-compresses
```

---

## Architecture

```
Chat Interface (chat.py)
    ↓
Gemini AI Client ←→ Conversation History Manager
                        ↓
                  Text Manager
                  (Enhanced Compression & Summarization)
                        ↓
                  Gemini API
                  (Summary Generation)
```

**Key Components:**

- **Chat Interface**: Rich console-based chat with commands
- **Gemini Client**: AI engine for chat and summarization
- **Conversation Manager**: Tracks history and triggers compression
- **Text Manager**: **Enhanced prompts** for context-preserving summaries

---

## How Compression Works

### Compression Strategy

The system uses **token-based automatic compression** to manage conversation history efficiently:

1. **Monitor token usage** in real-time after each message
2. **Trigger compression** when tokens exceed 25,000 (83% of 30K limit)
3. **Keep recent context** - last 5 messages stay uncompressed
4. **Summarize old messages** - compress older messages into a structured summary
5. **Continue naturally** - AI maintains conversation flow using the summary

### Configuration

```python
# In core/conversation.py
MAX_CONTEXT_TOKENS = 30000   # Gemini model limit
SAFE_THRESHOLD = 25000       # Trigger compression at 83%
KEEP_RECENT_MESSAGES = 5     # Keep last 5 messages uncompressed
```

### Compression Process

#### Before Compression:
```
[Message 1: User asks about Python]
[Message 2: Assistant explains basics]
[Message 3: User asks about classes]
[Message 4: Assistant explains OOP]
[Message 5: User asks about decorators]
[Message 6: Assistant explains decorators]
[Message 7: User asks about generators]  ← Recent (kept)
[Message 8: Assistant explains generators] ← Recent (kept)
[Message 9: User asks about async]        ← Recent (kept)
[Message 10: Assistant explains async]    ← Recent (kept)
[Message 11: User's current question]     ← Current (kept)

Total: 11 messages, ~15,000 tokens
```

#### After Compression:
```
[CONVERSATION HISTORY COMPRESSED]
This is a summary of the previous conversation to preserve context
while reducing token usage.

Summary: Previous conversation covered Python basics including syntax
and data types, OOP concepts with classes and inheritance, decorators
for metaprogramming and function modification. User showed interest in
advanced topics and asked detailed questions about implementation.

[Compression stats: 6 messages compressed, 11,713 tokens saved]
----
[Message 7: User asks about generators]  ← Recent (kept)
[Message 8: Assistant explains generators] ← Recent (kept)
[Message 9: User asks about async]        ← Recent (kept)
[Message 10: Assistant explains async]    ← Recent (kept)
[Message 11: User's current question]     ← Current (kept)

Total: 6 items (1 summary + 5 messages), ~3,500 tokens
```

**Result**: 6 messages compressed into 1 summary, saving ~11,700 tokens (77% reduction) while preserving context.

---

## Enhanced Summarization Prompt

The **key improvement** in day15 is the enhanced summarization prompt in `core/text_manager.py`:

### New Enhanced Prompt:

```python
prompt = """You are summarizing a conversation history to preserve context for an AI assistant.

TASK: Create a comprehensive summary that captures all essential information needed to continue the conversation naturally.

REQUIREMENTS:
- Maximum length: {max_tokens} tokens
- Preserve ALL key facts, names, numbers, dates, and specific details
- Maintain the chronological flow of the conversation
- Keep important questions asked and answers given
- Preserve any decisions made, problems identified, or solutions proposed
- Include technical details, code snippets, or file names if mentioned
- Maintain the context and relationship between topics discussed

CONVERSATION TO SUMMARIZE:
{text}

SUMMARY (preserve all critical details):"""
```

### Why This Works Better

**Old prompt** (basic):
```
Create a concise summary of the following text.
Maximum summary length: 500 tokens.
Preserve all key points and important information.
```

**New prompt** (comprehensive):
- ✅ Explicitly instructs to preserve names, numbers, dates
- ✅ Maintains chronological flow of conversation
- ✅ Preserves both questions AND answers
- ✅ Includes technical details and code snippets
- ✅ Maintains topic relationships and context

**Result**: Summaries preserve enough context for the AI to continue conversations naturally, even after multiple compressions.

---

## Improved Summary Formatting

### New Format in `core/conversation.py`:

```
[CONVERSATION HISTORY COMPRESSED]
This is a summary of the previous conversation to preserve context while reducing token usage.

{detailed_summary}

[Compression stats: X messages compressed, Y tokens saved]
```

**Benefits**:
- Clear visual indicator that compression occurred
- Context explanation for the AI
- Embedded statistics for tracking
- Better separation from regular messages

---

## Compression Statistics

The system tracks detailed compression metrics:

```python
{
    "messages_compressed": 6,        # Number of messages compressed
    "tokens_before": 15234,          # Token count before compression
    "tokens_after": 3521,            # Token count after compression
    "tokens_saved": 11713,           # Tokens saved (15234 - 3521)
    "compression_ratio": 0.769,      # 76.9% reduction
    "summary_tokens": 487,           # Tokens used for summary
    "messages_kept": 5,              # Recent messages kept
    "efficiency_percent": 76.9       # Compression efficiency %
}
```

### Viewing Statistics

```bash
# In chat interface
/tokens                # Show current token usage with progress bar
/compress              # Manually trigger compression
```

---

## Practical Example: Long Conversation

### Session Start
```
You: Tell me about Python decorators
Assistant: [Detailed explanation about decorators]
Tokens: 1,234 / 30,000 (4.1%) ✓
```

### After 10 exchanges
```
You: Can you show me an example with class decorators?
Assistant: [Example with explanation]
Tokens: 12,456 / 30,000 (41.5%) ✓
```

### After 20 exchanges (approaching limit)
```
You: How do decorators work with async functions?
Assistant: [Detailed async decorator explanation]
Tokens: 26,789 / 30,000 (89.3%) ⚠️

⚠️  Context limit reached! Auto-compressing...

Compression Results
====================================================================
Messages compressed: 15
Tokens before: 26,789
Tokens after: 8,555
Tokens saved: 18,234
Compression ratio: 68.1%
====================================================================

✓ Conversation compressed successfully!
```

### Continuing After Compression
```
You: Can you remind me what we discussed about class decorators?
Assistant: Based on our earlier conversation, we covered class decorators which...

# The AI can still access the summarized context!
Tokens: 9,823 / 30,000 (32.7%) ✓
```

---

## Commands

| Command      | Description                          |
|--------------|--------------------------------------|
| `/help`      | Show available commands              |
| `/model`     | Change AI model (Flash/Pro/Lite)     |
| `/system`    | View/change system instruction       |
| `/settings`  | Adjust temperature, top-k, top-p     |
| `/tokens`    | Show token usage statistics          |
| `/compress`  | Manually compress history            |
| `/clear`     | Clear conversation history           |
| `/quit`      | Exit                                 |

---

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

**Dependencies:**
- `requests==2.31.0` - HTTP client for Gemini API
- `rich==13.7.0` - Terminal UI with progress bars and markdown

---

## Benefits of Compression

### 1. Extended Conversations
- **Without compression**: ~20-30 exchanges before hitting limit
- **With compression**: Unlimited conversation length

### 2. Cost Efficiency
- Reduced token usage = lower API costs
- Typical savings: **60-80%** on long conversations

### 3. Performance
- Faster API responses with smaller context
- Better focus on recent, relevant information

### 4. Quality Maintenance
- Enhanced summaries preserve key context
- Recent messages stay intact for immediate context
- AI can reference both summary and recent messages
- Chronological flow maintained

---

## Comparison: Day 8 vs Day 15

### Day 8 (Basic Compression)
```python
# Simple prompt
"Create a concise summary of the following text.
Maximum summary length: 500 tokens.
Preserve all key points and important information."

# Basic summary format
"[Previous conversation summary: {summary}]"

# Basic statistics
messages_compressed, tokens_before, tokens_after, tokens_saved
```

### Day 15 (Enhanced Compression)
```python
# Comprehensive prompt with detailed instructions
"You are summarizing a conversation history to preserve context...
- Preserve ALL key facts, names, numbers, dates
- Maintain chronological flow
- Keep questions AND answers
- Include technical details..."

# Structured summary format
"[CONVERSATION HISTORY COMPRESSED]
This is a summary of the previous conversation to preserve context...
{detailed_summary}
[Compression stats: X messages compressed, Y tokens saved]"

# Extended statistics
messages_compressed, tokens_before, tokens_after, tokens_saved,
compression_ratio, summary_tokens, messages_kept, efficiency_percent
```

**Result**: Better context preservation, clearer formatting, more detailed tracking.

---

## Project Structure

```
day15/
├── chat.py                      # Main chat interface with compression
├── requirements.txt             # Dependencies (requests, rich)
├── README.md                    # This file
└── core/
    ├── __init__.py
    ├── conversation.py          # Enhanced compression logic & stats
    ├── gemini_client.py         # Gemini API integration
    └── text_manager.py          # Improved summarization prompts
```

---

## Key Improvements Over Day 8

### 1. Enhanced Summarization Prompt ⭐
- **More detailed instructions** for context preservation
- **Explicit requirements** for key information (names, numbers, dates)
- **Better structure** for AI understanding
- Maintains **chronological flow** and **topic relationships**

### 2. Improved Summary Formatting
- Clear header: `[CONVERSATION HISTORY COMPRESSED]`
- Context explanation for the AI
- Embedded compression statistics
- Better visual separation from regular messages

### 3. Extended Compression Statistics
- `summary_tokens`: Tokens used for the summary
- `messages_kept`: Number of recent messages preserved
- `efficiency_percent`: Overall compression efficiency
- `compression_ratio`: Actual reduction achieved

### 4. Better User Visibility
- Clear notifications when compression occurs
- Before/after token counts displayed
- Compression effectiveness shown (e.g., "saved 18,234 tokens")
- Progress bars for token usage

---

## Advanced Usage

### Custom Compression Settings

Modify `core/conversation.py` to adjust compression behavior:

```python
# More aggressive compression (compress earlier)
SAFE_THRESHOLD = 15000  # Compress at 50% instead of 83%

# Keep more recent context
KEEP_RECENT_MESSAGES = 10  # Keep last 10 instead of 5

# Larger summaries (in compress_history method)
max_tokens=1000  # Use 1000 tokens for summary instead of 500
```

### Monitor Compression Effectiveness

```python
# After compression
result = conversation.compress_history(client)

print(f"Compressed {result['messages_compressed']} messages")
print(f"Saved {result['tokens_saved']:,} tokens")
print(f"Efficiency: {result['efficiency_percent']:.1f}%")
print(f"Summary uses: {result['summary_tokens']} tokens")
```

### Model Selection for Better Summaries

```bash
# In chat
/model

# Select model:
# 1. Gemini 2.5 Flash (default) - Good balance
# 2. Gemini 2.5 Flash Lite - Fast but less detailed
# 3. Gemini 2.5 Pro - Best summaries, most context preservation
```

For critical conversations where context is important, use **Gemini Pro** for better quality summaries.

---

## Troubleshooting

### Compression Not Triggering

Check token threshold:
```python
stats = conversation.get_compression_stats()
print(f"Tokens: {stats['total_tokens']} / {stats['max_tokens']}")
print(f"Should compress: {stats['should_compress']}")  # True if > 25,000
```

### Summary Quality Issues

1. **Use better model**: `/model` → Select Gemini Pro
2. **Increase summary size**: Change `max_tokens=500` to `max_tokens=1000` in `compress_history()`
3. **Check API key**: Ensure `GEMINI_API_KEY` is valid

### Memory Issues

- Lower `KEEP_RECENT_MESSAGES` to compress more aggressively
- Manually compress with `/compress` before hitting limit
- Use `/clear` to start fresh if needed

### API Timeout

If compression times out:
- Check internet connection
- Increase timeout in `compress_history()`: `timeout=30` instead of 15
- Reduce `max_tokens` for faster summarization

---

## Example Session

```bash
$ cd day15
$ export GEMINI_API_KEY="your-key-here"
$ python chat.py

==================================================
     GEMINI CHAT - AI Assistant
==================================================
Commands:
  /model    - Change model
  /system   - View/change system instruction
  /settings - View/change generation settings
  /compress - Compress conversation history
  /tokens   - Show token statistics
  /clear    - Clear conversation history
  /quit     - Exit chat
  /help     - Show this help
==================================================
Current model: Gemini 2.5 Flash (Fast & Balanced)
==================================================

You: Let's discuss Python decorators in detail
Assistant: [Detailed explanation of decorators]
Tokens: 1,500 / 30,000 (5.0%) ✓

You: Show me practical examples
Assistant: [Multiple examples with explanations]
Tokens: 14,200 / 30,000 (47.3%) 🟡
...
[After many exchanges]

⚠️  Context limit reached! Auto-compressing...
✓ Compressed 12 messages, saved 15,432 tokens
```

---

## Testing

Quick verification that everything works:

```bash
# 1. Run flake8 linting
flake8 . --exclude=__pycache__,venv,.venv --max-line-length=120

# 2. Test import structure
python -c "from core.conversation import ConversationHistory; print('✓ Imports OK')"

# 3. Test chat interface
python chat.py
# Type: /help to verify commands
# Type: /tokens to verify stats
# Type: /quit to exit
```

---

## References

- [Google Gemini API](https://ai.google.dev/) - Gemini API documentation
- [Rich Library](https://rich.readthedocs.io/) - Terminal formatting
- [Requests](https://docs.python-requests.org/) - HTTP library

---

## License

Educational project for AI Advent Challenge
