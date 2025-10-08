# Day 6: Step-by-Step Reasoning Comparison

This project demonstrates the difference between direct answers and step-by-step reasoning when using Gemini AI. It automatically compares both approaches and uses AI to analyze which method works better.

## Task

Compare how Gemini 2.5 Flash responds to the same problem with two different approaches:
1. **Direct answer** - No special instructions
2. **Step-by-step reasoning** - With "solve step by step" instruction

The comparison is automated and includes AI-generated analysis of which approach works better.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your Gemini API key:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Usage

Run the automatic comparison script:
```bash
python auto_comparison.py
```

Or provide a custom problem:
```bash
python auto_comparison.py "A farmer has 20 chickens and rabbits with 56 legs total. How many of each?"
```

## How It Works

The script performs three steps:

1. **Direct Answer**: Sends the problem to Gemini without special instructions
2. **Step-by-Step**: Sends the same problem with "Please solve this step by step" instruction
3. **AI Analysis**: Asks Gemini to compare both approaches and analyze:
   - Which answer is more correct/complete
   - Key differences in reasoning
   - Pros and cons of each approach
   - When to use each method
   - Conclusion for this specific problem

Results are displayed in the console and saved to a markdown file with timestamp.

## Example Results

Default problem: `Solve the equation: 3x + 7 = 2x + 15`

**Findings:**
- Both approaches produced correct answers (x = 8)
- Direct answer: 852 tokens, concise solution
- Step-by-step: 948 tokens, more verbose with explanations
- Step-by-step approach better for educational purposes
- Direct approach better for quick answers to those familiar with algebra

See `reasoning_comparison_20251008_141801.md` for detailed example output.

## Key Findings

**Step-by-step reasoning provides:**
- Explicit rationale for each operation
- Better for learning and teaching
- More accessible to beginners
- Thorough understanding of the process

**Direct answers are better for:**
- Concise, efficient solutions
- Users already familiar with the concept
- Quick reference needs
- Token efficiency

## Files

- `gemini_client.py` - Gemini API client implementation (from day4)
- `auto_comparison.py` - Automated comparison script with AI analysis
- `requirements.txt` - Python dependencies (requests, rich)
- `reasoning_comparison_*.md` - Generated comparison reports with timestamps

## Dependencies

- `requests==2.31.0` - HTTP library for API calls
- `rich==13.7.0` - Terminal formatting (optional, for enhanced display)