# Day 7: Two-Agent AI System with Koog Framework

## Overview

This project demonstrates interaction between two AI agents using the **Koog framework** and **Google Gemini AI**:

- **Agent 1 (Meteorologist)**: Creates catastrophic weather disaster scenarios
- **Agent 2 (Disaster Screenwriter)**: Reviews the weather report and transforms it into a Hollywood movie concept

Both agents are unified in a single `Agents.kt` file for simplicity.

## Architecture

```
┌─────────────────┐       Weather Report       ┌─────────────────┐
│                 │  ──────────────────────────> │                 │
│  Meteorologist  │        (Text Output)        │  Screenwriter   │
│     Agent       │                             │     Agent       │
│   (Gemini AI)   │                             │   (Gemini AI)   │
└─────────────────┘                             └─────────────────┘
                                                          │
                                                          ▼
                                                   results/*.md
                                                   (Saved Output)
```

## Features

- **Unified Agent Architecture**: Both agents in single `Agents.kt` file
- Two independent AI agents with different personalities and models
- Agent 1 generates structured disaster scenarios
- Agent 2 receives Agent 1's output and creates creative movie scripts
- Text-based communication between agents
- **Automatic MD Export**: Results saved to `results/result_YYYYMMDD_HHMMSS.md`
- Beautiful console output with formatting

## Technologies

- **Kotlin** 2.2.20
- **Koog Framework** 0.5.0 - AI agent framework (includes all LLM providers)
- **Google Gemini 2.0 Flash** - AI model for both agents

## Setup

### 1. Get Google AI API Key

Visit [Google AI Studio](https://ai.google.dev/) and get your API key.

### 2. Configure API Key

Option A: Environment variable (recommended)
```bash
export GEMINI_API_KEY=your_api_key_here
```

Option B: Configuration file
```bash
cp config.properties.example config.properties
# Edit config.properties and add your API key
```

### 3. Build Project

```bash
./gradlew build
```

### 4. Run

```bash
./gradlew run
```

Or in IntelliJ IDEA: Run `Main.kt`

## How It Works

1. **Meteorologist Agent** receives a location (e.g., "Tokyo, Japan")
2. Generates a dramatic weather disaster report with:
   - Disaster type (hurricane, tornado, tsunami, etc.)
   - Scientific details (wind speed, pressure, etc.)
   - Timeline and affected areas
   - Dramatic descriptions

3. **Screenwriter Agent** receives the weather report
4. Transforms it into a movie concept with:
   - Movie title and tagline
   - Main character description
   - Plot summary
   - Climax scene
   - Spectacle rating (1-10)
   - Recommendations for more drama

## Example Output

```
╔════════════════════════════════════════════════════════════╗
║  DISASTER MOVIE GENERATOR: Two-Agent AI System            ║
║  Agent 1: Meteorologist → Agent 2: Screenwriter           ║
╚════════════════════════════════════════════════════════════╝

┌────────────────────────────────────────────────────────┐
│ 🌪️  AGENT 1: METEOROLOGIST                            │
└────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════
  METEOROLOGICAL DISASTER REPORT
═══════════════════════════════════════════════════════════
[Weather disaster scenario...]

┌────────────────────────────────────────────────────────┐
│ 🎬 AGENT 2: DISASTER MOVIE SCREENWRITER                │
└────────────────────────────────────────────────────────┘

███████████████████████████████████████████████████████████
  DISASTER MOVIE SCRIPT CONCEPT
███████████████████████████████████████████████████████████
[Movie script concept...]
```

## Project Structure

```
day7/
├── build.gradle.kts              # Build configuration (minimal dependencies)
├── src/main/kotlin/org/example/
│   ├── Main.kt                   # Main application + MD export
│   ├── Agents.kt                 # Both agents in one file
│   └── models/                   # Optional data models (not used)
├── results/                      # Auto-generated MD results
│   └── result_*.md               # Timestamped results
├── config.properties.example     # API key example
└── README.md                     # This file
```

## Key Implementation Details

### Agent 1: Meteorologist
- Model: `Gemini 2.0 Flash`
- Temperature: 0.8 (balanced creativity)
- Task: Generate scientific disaster scenarios

### Agent 2: Screenwriter
- Model: `Gemini 2.0 Flash`
- Temperature: 0.9 (high creativity)
- Task: Transform data into entertainment

## Requirements

- JDK 17 or higher
- Internet connection (for API calls)
- Google AI API key

## Output

After running, you'll get:
1. **Console output** with formatted agent responses
2. **MD file** in `results/` folder with complete interaction log

Example: `results/result_20251009_143022.md`

## Notes

- Both agents return text output (not structured data)
- Agents unified in single file for simplicity
- Agent interaction is sequential: Agent 1 → Agent 2
- Agent 2 validates and enhances Agent 1's work
- Results automatically saved to markdown files
- Demonstrates clean separation of concerns with different AI personas

## License

Educational project for AI Advent Challenge
