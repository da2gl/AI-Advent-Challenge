# 🚀 Getting Started with God Agent

## Quick Start (5 Minutes)

### 1. Setup Environment

```bash
cd day28

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### 2. Configure API Keys

Edit `.env`:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your key: https://makersuite.google.com/app/apikey

### 3. Run CLI

```bash
python chat.py
```

Try:
- "Hello!"
- "What can you do?"
- "/status"

### 4. Run Web Interface

```bash
cd webapp
python app.py
```

Open: http://localhost:8080

## What Can You Do?

### Chat with RAG
"Explain quantum computing using my knowledge base"

### Create Scheduled Tasks
- Bitcoin price checks every 5 minutes
- Daily code analysis reports
- Weekly system summaries

### Analyze Code
Upload any code file for quality analysis and recommendations

### Deploy Applications
One-click deployment to Railway or Docker

### Voice Input
Record and transcribe voice queries (requires Groq API key)

## Example Workflows

### 1. Research Assistant
1. Index documents in RAG tab
2. Chat with context-aware responses
3. Export conversation summaries

### 2. Code Quality Manager
1. Upload code files
2. Get quality scores and recommendations
3. Schedule daily analysis tasks

### 3. DevOps Automation
1. Configure deployment pipeline
2. Run automated deployments
3. Monitor via status dashboard

## Troubleshooting

**"GEMINI_API_KEY not found"**
- Add key to `.env` file

**"pyaudio failed to install"**
```bash
# macOS:
brew install portaudio
pip install pyaudio

# Linux:
sudo apt-get install portaudio19-dev
pip install pyaudio
```

**"Ollama not found"**
- Install from https://ollama.ai/
- Or set `LLM_PROVIDER=gemini` in `.env`

## Next Steps

1. **Explore Features**: Try each tab in the web interface
2. **Index Knowledge**: Add your documents to RAG
3. **Create Tasks**: Automate your workflows
4. **Customize**: Modify `god_agent.py` for your needs
5. **Deploy**: Use Docker Compose for production

## Need Help?

- Check `README.md` for full documentation
- Visit `/docs` in web interface for API docs
- See `FEATURES.md` for complete feature list

---

**You're ready to use the God Agent!** 🎉
