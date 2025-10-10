# Day 8: Token Counting and Context Management

AI Advent Challenge - Day 8 implementation demonstrating token counting and intelligent context compression using Google
Gemini API.

## Overview

This project demonstrates advanced token management techniques for AI chat applications:

1. **Token Counting** - Real-time tracking of token usage
2. **AI-based Summarization** - Using Gemini to compress long texts
3. **Hierarchical Summarization** - Managing conversation history with multi-level compression

## Features

### 1. Token Tracking

- Real-time token counting for every request/response
- Visual progress bar showing context usage
- Automatic warnings when approaching token limits

### 2. Context Compression

Two compression methods are implemented:

#### AI-based Summarization

- Uses Gemini API to create intelligent summaries
- Preserves key information while reducing token count
- High quality but requires additional API call

#### Hierarchical Summarization

- Keeps recent messages (last 5) in full
- Summarizes older messages into a single summary
- Automatically triggered when approaching context limit

### 3. Visual Interface

- Color-coded token usage display
- Progress bars for context consumption
- Warnings when context is filling up (⚠️ at 80%, 🔴 at 90%)

## Installation

```bash
cd day8
pip install -r requirements.txt
```

## Configuration

Set your Gemini API key:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Or enter it when prompted by the application.

## Usage

Run the chat application:

```bash
python chat.py
```

### Available Commands

| Command     | Description                              |
|-------------|------------------------------------------|
| `/tokens`   | Show detailed token statistics           |
| `/compress` | Manually compress conversation history   |
| `/demo`     | Run compression demo with reduced limits |
| `/model`    | Change AI model                          |
| `/system`   | Set system instruction                   |
| `/settings` | Adjust generation parameters             |
| `/clear`    | Clear conversation history               |
| `/help`     | Show help message                        |
| `/quit`     | Exit application                         |

## How It Works

### Token Estimation

Token counting uses a rough estimation formula:

- **Russian text**: ~3 characters per token
- **English text**: ~4 characters per token
- **Mixed content**: ~3.5 characters per token

For accurate counts, the API returns exact token usage in `usageMetadata`.

### Compression Strategies

#### 1. AI Summarization (text_manager.py:35-88)

When you send a long text, it can be summarized:

```python
summary_result = TextManager.summarize_text(
    text=long_text,
    client=gemini_client,
    max_tokens=500
)
```

**Example:**

- Original: 2000 tokens
- Summary: 500 tokens
- **Saved: 1500 tokens (75% compression)**

#### 2. Hierarchical Summarization (conversation.py:111-186)

When conversation history grows too large:

```
Before compression (15 messages, 8000 tokens):
[Msg 1] User: ...
[Msg 2] Assistant: ...
...
[Msg 13] User: ...
[Msg 14] Assistant: ...
[Msg 15] User: ...

After compression (6 messages, 3000 tokens):
[Summary] Previous conversation: [AI-generated summary of messages 1-10]
[Msg 11] User: ...
[Msg 12] Assistant: ...
[Msg 13] User: ...
[Msg 14] Assistant: ...
[Msg 15] User: ...

Saved: 5000 tokens (62% reduction)
```

### Context Limits

- **Model limit**: 30,000 tokens
- **Warning threshold**: 25,000 tokens (83%)
- **Auto-suggest compress**: When over 80%

## Code Structure

```
day8/
├── chat.py              # Main chat interface
├── gemini_client.py     # Gemini API client
├── conversation.py      # Conversation history manager
├── text_manager.py      # Token estimation & compression utilities
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

### Key Classes

**ConversationHistory** (conversation.py)

- Tracks all messages and token counts
- Implements hierarchical compression
- Monitors context usage

**TextManager** (text_manager.py)

- Estimates token counts
- Performs AI-based summarization
- Formats progress bars

**ConsoleChat** (chat.py)

- User interface
- Command handling
- Token display and warnings

## Demo Scenarios

### Scenario 1: Short Prompt

```
You: What is Python?
Assistant: Python is a high-level programming language...

Tokens: 15 prompt + 45 response = 60 total
Context: [60/30,000] █░░░░░░░░░░░░░░░░░░░ 0.2% ✓
```

### Scenario 2: Long Conversation

After many messages:

```
Tokens: 850 prompt + 1200 response = 2050 total
Context: [26,500/30,000] ████████████████░░░░ 88.3% ⚠️

⚠️  Context usage is high! Consider using /compress
```

### Scenario 3: Compression

```
You: /compress

🔄 Compressing conversation history...

============================================================
Compression Results
============================================================
Messages compressed: 12
Tokens before: 26,500
Tokens after: 8,750
Tokens saved: 17,750
Compression ratio: 66.9%
============================================================

✓ Conversation compressed successfully!
```

### Scenario 4: Demo Mode

Run `/demo` for quick demonstration with reduced token limits:

```
You: /demo

============================================================
🎬 DEMO MODE - Token Compression Demonstration
============================================================

This demo shows how compression works with reduced limits:
  • Context limit: 2,000 tokens (instead of 30,000)
  • Warning threshold: 1,500 tokens (75%)
  • Keep recent: 3 messages (instead of 5)
  • Responses: Forced to be short (500-700 tokens)

Available demo prompts:
  • short: Short prompt (~16 tokens) → 2048 tokens response
  • long: Long prompt (~100 tokens) → 2048 tokens response
  • very_long: Very long prompt (~1600 tokens) → 2048 tokens response

Commands:
  /short      - Send short demo prompt
  /long       - Send long demo prompt
  /very_long  - Send very long demo prompt
  /exit_demo  - Exit demo mode

You: /long
→ Loading long prompt (100 tokens, max_output: 2,048)

[Spinner shows: "Thinking..."]
Assistant: [Short, structured response about machine learning basics]

Tokens: 100 prompt + 650 response = 750 total
Context [DEMO]: [750/2,000] ███████░░░░░░░░░░░░░ 37.5% ✓

[After 2-3 messages context fills quickly...]

Context [DEMO]: [1,650/2,000] ████████████████░░░░ 82.5% ⚠️

⚠️  Context limit reached! Auto-compressing...
[Spinner shows: "Compressing conversation history..."]
✓ Compressed 2 messages, saved 800 tokens

You: /exit_demo
✓ Exited demo mode - Normal limits restored
```

**Demo mode features:**
- Token-based compression (not message-count based)
- Auto-compression with visual spinners
- Short responses enforced by system instruction
- Instant feedback on compression performance
- Safe testing environment

## Technical Details

### Token Counting Methods

1. **Estimation** (Fast, offline)
    - Character-based approximation
    - No API calls required
    - ~90% accurate

2. **API Metadata** (Exact, from response)
   ```json
   {
     "usageMetadata": {
       "promptTokenCount": 850,
       "candidatesTokenCount": 1200,
       "totalTokenCount": 2050
     }
   }
   ```

### Compression Algorithms

**Summarization Prompt:**

```
Create a concise summary of the following text.
Maximum summary length: 500 tokens.
Preserve all key points and important information.

Text: [original text]

Summary:
```

**Hierarchical Strategy:**

- Keep last 5 messages → Full detail
- Older messages → Single summary
- Recalculate total tokens
- **Token-based triggering** (not message count)

## Performance

| Operation        | Time  | API Calls         |
|------------------|-------|-------------------|
| Token estimation | <1ms  | 0                 |
| Regular message  | ~2s   | 1                 |
| Compression      | ~15s  | 1 (with timeout)  |

## Limitations

1. Token estimation is approximate (actual count from API is precise)
2. Compression requires extra API call (costs tokens/money)
3. Very old context may lose fine details after summarization
4. Summary quality depends on AI model performance

## Recent Improvements

✅ **Fixed hanging issue during compression**
- Added visual spinners for all compression operations
- Reduced timeout from 30s to 15s for faster failure
- Improved error handling with specific messages

✅ **Enhanced demo mode**
- Special system instruction for short responses
- Token-based compression (not message-count based)
- Predefined prompts (`/short`, `/long`, `/very_long`)
- Real-time compression demonstration

## References

- [Google Gemini API Documentation](https://ai.google.dev/docs)
- [Token Management Best Practices](https://ai.google.dev/docs/concepts#tokens)
- Context Compression Techniques:
    - Summarization (AI-based)
    - Hierarchical Summarization (this implementation)
    - Sliding Window
    - Semantic Compression

## License

Educational project for AI Advent Challenge
