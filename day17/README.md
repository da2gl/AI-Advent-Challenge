# Day 17: Code Analysis Pipeline with AI Chat

**AI-powered code analysis pipeline integrated into interactive chat interface**

## Overview

This project implements a multi-stage data processing pipeline for analyzing source code. The pipeline combines static analysis with AI-powered insights, all accessible through an interactive chat interface.

## Key Features

### 🔍 Code Analysis Pipeline
- **4-stage processing**: Metadata extraction → Static analysis → AI documentation → Quality assessment
- **Multi-language support**: Python, JavaScript, TypeScript, Java, Go, Rust, C++
- **Intelligent metrics**: Complexity, code smells, security issues, quality scoring
- **AI-powered insights**: Gemini AI generates documentation and improvement suggestions

### 💬 Interactive Chat Integration
- **Integrated analysis**: Run `/analyze <file>` directly in chat
- **AI conversation**: Ask questions about analyzed code
- **Context-aware responses**: AI remembers analysis results
- **Report export**: Save analysis reports to files

### 📊 Analysis Metrics
- Code/comment/blank line counts
- Function and class extraction
- Cyclomatic complexity
- Code smell detection
- Security vulnerability scanning
- Quality score (0-100)

## Pipeline Architecture

```
┌─────────────────────────────────────┐
│  Input: Source Code File            │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Stage 1: Metadata Extraction       │
│  • Language detection               │
│  • Line counting                    │
│  • Function/class extraction        │
│  • Import analysis                  │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Stage 2: Static Analysis           │
│  • Complexity calculation           │
│  • Code smell detection             │
│  • Issue identification             │
│  • Security checks                  │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Stage 3: AI Documentation          │
│  • Gemini AI analysis               │
│  • Code summary generation          │
│  • Pattern detection                │
│  • Improvement suggestions          │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Stage 4: Quality Assessment        │
│  • Score calculation (0-100)        │
│  • Recommendations                  │
│  • Priority ranking                 │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Output: Comprehensive Report       │
└─────────────────────────────────────┘
```

## Project Structure

```
day17/
├── pipeline/
│   ├── code_analyzer.py           # Core analysis stages
│   ├── pipeline_executor.py       # Pipeline orchestrator
│   └── __init__.py
├── core/
│   ├── gemini_client.py           # Gemini API client
│   ├── conversation.py            # Conversation management
│   ├── storage.py                 # SQLite persistence
│   └── text_manager.py            # Text processing utilities
├── test_samples/
│   ├── sample1_good.py            # Well-written code example
│   ├── sample2_bad.py             # Code with issues example
│   └── sample3_javascript.js      # JavaScript example
├── results/                        # Analysis reports (generated)
├── data/
│   └── conversations.db           # Chat history database
├── chat.py                        # Main interactive chat
├── analyze_code.py                # Standalone CLI tool
├── demo.sh                        # Demo script
├── README.md             # Detailed pipeline docs
└── requirements.txt
```

## Installation

1. **Clone and navigate:**
```bash
cd day17
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up API key:**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Usage

### Interactive Chat Mode (Recommended)

```bash
python3 chat.py
```

**Available commands:**
```
/analyze <file>        - Analyze a code file
/save-report <file>    - Save last analysis report
/resume                - Load previous conversation
/clear                 - Start new conversation
/model                 - Change AI model
/help                  - Show all commands
/quit                  - Exit
```

**Example workflow:**
```
You: /analyze test_samples/sample1_good.py

[Pipeline runs and shows beautiful formatted results]

📊 Code Metadata
├─ Language: python
├─ Code lines: 88
├─ Functions: 11
└─ Classes: 1

🎯 Quality Score: 99/100 ⭐ Excellent

You: Why is the quality score so high?

AI: Your code scored 99/100 because it demonstrates excellent
    practices: well-modularized functions averaging 8 lines each,
    good complexity score of 1, and clear naming conventions...

You: How can I make it even better?

AI: To reach 100/100, consider:
    1. Adding docstrings to all functions
    2. Replacing magic numbers with named constants...

You: /save-report results/analysis.txt
✓ Report saved to: results/analysis.txt
```

### Standalone CLI Mode

```bash
# Basic analysis
python3 analyze_code.py my_code.py

# With AI documentation
python3 analyze_code.py my_code.py

# Save to file
python3 analyze_code.py my_code.py -o report.txt

# JSON format
python3 analyze_code.py my_code.py -o report.json -f json

# Quick check without AI
python3 analyze_code.py my_code.py --brief --no-ai
```

### Demo Script

```bash
./demo.sh
```

Shows analysis of all three sample files with explanations.

## Example Analysis Results

### Sample 1: Good Code
```
📊 Metadata: 88 lines, 11 functions, 1 class
🎯 Score: 99/100 ⭐ Excellent
🔬 Complexity: 1
💡 Recommendations: Add more comments
```

### Sample 2: Problematic Code
```
📊 Metadata: 82 lines, 9 functions, 1 class
🎯 Score: 89/100 ✅ Good
🔬 Complexity: 4
⚠️  Issues: 3 (1 high-severity)
💡 Recommendations:
    • Fix eval() usage (security risk)
    • Refactor repetitive if/elif chains
    • Add docstrings
```

### Sample 3: JavaScript
```
📊 Metadata: 77 lines, 2 functions, 1 class
🎯 Score: 97/100 ⭐ Excellent
🔬 Complexity: 2
💡 Recommendations: Extract magic numbers
```

## Quality Scoring System

**Score components:**
- ✅ **+5**: Good comment ratio (>20%)
- ✅ **+5**: Well-modularized (<30 lines/function avg)
- ⚠️ **-5**: Moderate complexity (10-20)
- ⚠️ **-15**: High complexity (>20)
- ⚠️ **-3 per code smell**
- ⚠️ **-5 per medium issue**
- ⚠️ **-10 per high-severity issue**

**Ratings:**
- 90-100: ⭐ Excellent
- 75-89: ✅ Good
- 60-74: ⚠️ Fair
- <60: ❌ Needs Improvement

## Pipeline Design Pattern

This implementation demonstrates the **Pipeline Pattern** for data processing:

1. **Sequential stages**: Data flows through distinct processing steps
2. **Modular components**: Each stage is independent and reusable
3. **Composable**: Easy to add/remove/reorder stages
4. **Testable**: Each stage can be tested independently
5. **Hybrid approach**: Combines classical algorithms + AI

### Why This Architecture?

- **Classical stages (1,2,4)**: Fast, deterministic, no API costs
- **AI stage (3)**: Provides insights humans would give
- **Best of both worlds**: Speed + intelligence

## Technical Details

### Dependencies
- `requests` - HTTP client for Gemini API
- `rich` - Terminal formatting and tables
- Standard library: `re`, `pathlib`, `dataclasses`

### Performance
- Metadata extraction: ~50ms
- Static analysis: ~100ms
- AI documentation: 2-5 seconds
- **Total: ~3-6 seconds per file**

### Limitations
- Requires valid syntax (won't analyze broken code)
- Large files (>10k lines) may be slower
- AI analysis requires internet connection
- Some language features may not be detected

## Advanced Usage

### Custom Analysis Pipeline

```python
from pipeline import CodeAnalysisPipeline, MetadataExtractor

# Create custom pipeline
pipeline = CodeAnalysisPipeline()

# Analyze code
result = pipeline.analyze_file('my_code.py')

# Access results
print(f"Quality: {result.quality_score}")
print(f"Complexity: {result.static_analysis.complexity_score}")
for smell in result.static_analysis.code_smells:
    print(f"  - {smell}")
```

### Batch Analysis

```python
import glob
from pipeline import CodeAnalysisPipeline

pipeline = CodeAnalysisPipeline()

for file in glob.glob('src/**/*.py', recursive=True):
    result = pipeline.analyze_file(file)
    if result.quality_score < 70:
        print(f"⚠️ {file}: {result.quality_score:.1f}")
```

## Chat Features

### Persistent Storage
- All conversations saved to SQLite
- Resume any previous analysis session
- Full history of all analyses

### AI Context Awareness
After `/analyze`, AI knows:
- Code structure and metrics
- Detected issues and smells
- Quality score breakdown
- Can answer specific questions about YOUR code

### Example Interaction
```
You: /analyze my_api.py
[Analysis runs...]

You: Why did I get penalized for complexity?
AI: Your complexity score is 18, which is in the "moderate"
    range (10-20). The main contributors are:
    - handle_request() function has 8 decision points
    - Nested if/elif chains in validate_input()
    ...

You: How should I refactor handle_request?
AI: Consider using a strategy pattern or command pattern...
```

## Learning Outcomes

This project demonstrates:

1. **Pipeline Pattern**: Multi-stage data processing
2. **Hybrid AI**: Combining classical algorithms + LLM
3. **Modular Design**: Reusable, testable components
4. **Rich UI**: Professional terminal interfaces
5. **Context Management**: AI remembers analysis state
6. **Error Handling**: Graceful degradation
7. **File I/O**: Reading/writing reports

## References

- [Google Gemini API](https://ai.google.dev/) - Gemini API documentation
- [Rich Library](https://rich.readthedocs.io/) - Terminal formatting
- [Requests](https://docs.python-requests.org/) - HTTP library
- [SQLite3](https://docs.python.org/3/library/sqlite3.html) - Python SQLite documentation

---

## License

Educational project for AI Advent Challenge
