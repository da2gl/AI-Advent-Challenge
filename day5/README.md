# Day 5: AI Model Comparison

Compare three different AI models (worst, medium, best) using free APIs.

## Selected Models

### 1. Worst (Smallest) - 1.5B parameters
**Model:** `katanemo/Arch-Router-1.5B`
**Provider:** HuggingFace Inference API (Free)
**Link:** https://huggingface.co/katanemo/Arch-Router-1.5B

### 2. Medium - 3B parameters
**Model:** `HuggingFaceTB/SmolLM3-3B`
**Provider:** HuggingFace Inference API (Free)
**Link:** https://huggingface.co/HuggingFaceTB/SmolLM3-3B

### 3. Best (Largest) - 8B parameters
**Model:** `llama-3.1-8b-instant`
**Provider:** Groq API (Free)
**Link:** https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Get API keys:
   - **HuggingFace Token:** https://huggingface.co/settings/tokens (create "Read" token)
   - **Groq API Key:** https://console.groq.com/keys

3. Set environment variables:
```bash
export HUGGINGFACE_API_KEY="hf_your_token_here"
export GROQ_API_KEY="gsk_your_key_here"
```

## Usage

Run the comparison:
```bash
python model_comparison.py
```

This will:
- Send the same prompt to all 3 models
- Measure response time and token usage
- Generate a comparison report in markdown format

## Files

- `huggingface_client.py` - HuggingFace Inference API client (with retry logic)
- `groq_client.py` - Groq API client
- `model_comparison.py` - Main comparison script
- `model_comparison_YYYYMMDD_HHMMSS.md` - Generated comparison report
- `.env.example` - API key template

## What Gets Measured

- **Response Time:** Time taken to generate response (seconds)
- **Token Count:** Prompt tokens, completion tokens, total tokens
- **Cost:** All models use free tier ($0.00)
- **Quality:** Compare actual responses side-by-side

## Results Summary

Based on the test with prompt "Explain what is artificial intelligence in simple terms":

| Model | Size | Time | Quality |
|-------|------|------|---------|
| Arch-Router-1.5B | 1.5B | 3.05s | ⭐⭐⭐ Good, structured |
| SmolLM3-3B | 3B | 2.86s | ⭐⭐ Strange format with `<think>` |
| Llama-3.1-8B (Groq) | 8B | 0.57s | ⭐⭐⭐⭐ Best quality + fastest! |

**Winner:** Groq's Llama-3.1-8B is both the fastest AND highest quality! 🏆
