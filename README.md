# 🚀 Sales Outreach Agent

**An intelligent multi-agent system that generates, evaluates, and ranks sales outreach emails using AI.**

[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://python.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-Agents%20SDK-green)](https://github.com/openai/openai-agents)
[![License](https://img.shields.io/badge/license-MIT-purple)](LICENSE)

---

## 📋 Portfolio Summary

### Problem

Cold outreach emails suffer from low response rates (typically 1-3%) because:
- Generic templates feel impersonal and get ignored
- Single-prompt AI generates inconsistent quality
- No objective way to measure email effectiveness before sending
- SDRs spend hours writing emails manually without knowing which approach works best

### Approach

Built a **multi-agent orchestration system** that:
1. **Generates 3 parallel drafts** using specialized AI personas (Professional, Engaging, Concise)
2. **Evaluates each draft** using a hybrid scoring system (40% rule-based + 60% LLM judge)
3. **Automatically selects the winner** based on objective metrics
4. **Provides actionable feedback** for continuous improvement

**Key Design Decisions:**
- Externalized prompts in markdown files for easy iteration without code changes
- Pydantic settings for type-safe configuration management
- Async parallel execution to minimize latency
- Modular architecture separating agents, scoring, and pipeline orchestration

### Key Challenges

| Challenge | Solution |
|-----------|----------|
| Inconsistent LLM outputs | Designed 100+ line prompts with personas, examples, and constraints |
| Prompt injection in templates | Used `{{` escaping and separated user input from system prompts |
| Scoring subjectivity | Combined objective rules (length, structure, spam triggers) with calibrated LLM evaluation |
| API cost management | Built cost tracking with per-call logging and budget alerts |
| Gradio 6.x breaking changes | Adapted UI code to new API with simplified component initialization |

### Key Learnings

- **Prompt engineering is the product**: Moving from 3-line prompts to 100+ line prompts with personas, chain-of-thought, and examples dramatically improved output quality
- **Multi-agent > single agent**: Parallel generation with evaluation outperforms iterative refinement
- **Hybrid scoring adds objectivity**: Pure LLM evaluation is inconsistent; combining rules creates reproducible baselines
- **Configuration as code**: Pydantic settings caught 5+ configuration errors during development that would have been silent runtime failures

### Outcomes

- **3x draft generation** with automatic winner selection
- **< 2 seconds** end-to-end pipeline execution
- **$0.01 per run** average API cost (GPT-4o-mini)
- **Production-ready** with tests, logging, and REST API
- **Extensible** - easy to add new agent personas or scoring criteria

### Tech Stack

| Layer | Technology |
|-------|------------|
| **AI/LLM** | OpenAI GPT-4o-mini, OpenAI Agents SDK |
| **Backend** | Python 3.10+, FastAPI, Pydantic |
| **Frontend** | Gradio |
| **Testing** | Pytest |
| **Infrastructure** | dotenv, structured logging |

---

## ✨ Features

### 🤖 Multi-Persona Generation
Three specialized SDR agents generate drafts in parallel:

| Agent | Style | Best For |
|-------|-------|----------|
| **👔 Professional** | Value-focused, ROI-driven | C-suite, Enterprise |
| **💡 Engaging** | Pattern-interrupts, conversational | Startups, Marketing |
| **⚡ Concise** | Ultra-brief, bullet-points | Busy executives |

### 📊 Hybrid Scoring Engine
- **Rule-Based (40%)**: Length, structure, keywords, spam triggers, CTA quality
- **LLM Judge (60%)**: Persuasiveness, tone, clarity, personalization
- **Improvement Suggestions**: Actionable feedback for each draft

### 🎯 World-Class Prompt Engineering
- Rich personas with names, backstories, and motivations
- Chain-of-thought reasoning frameworks
- Few-shot examples (good and bad)
- Explicit negative constraints
- Dynamic context injection

---

## 📁 Architecture

```
Sales-Outreach-Agent/
├── config/                    # Configuration & prompts
│   ├── settings.py           # Pydantic settings with validation
│   └── prompts/              # Externalized prompt templates
│       ├── professional_sdr.md
│       ├── engaging_sdr.md
│       ├── concise_sdr.md
│       └── email_judge.md
│
├── src/                       # Core source code
│   ├── agents/               # Agent definitions
│   ├── scoring/              # Rule + LLM + Hybrid scorers
│   ├── pipeline/             # Orchestration logic
│   └── utils/                # Cost tracking, caching, logging
│
├── app/                       # Application layer
│   ├── gradio_app.py         # Web UI
│   └── api.py                # REST API
│
└── tests/                     # Test suite
```

---

## 🛠️ Quick Start

```bash
# Clone
git clone https://github.com/Terry-Mathew/Sales-Outreach-Agent.git
cd Sales-Outreach-Agent

# Setup
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt

# Configure
copy .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run
python main.py              # Gradio UI
python main.py --api        # REST API
```

---

## 📡 API Usage

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prospect_description": "CTO of a 75-person e-commerce company..."}'
```

API docs: http://localhost:8000/docs

---

## 🧠 How It Works

```
┌─────────────────┐
│ Prospect Input  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│           Parallel Draft Generation          │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐  │
│  │Professional│ │ Engaging  │ │  Concise  │  │
│  │   Agent   │ │   Agent   │ │   Agent   │  │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘  │
└────────┼─────────────┼─────────────┼────────┘
         │             │             │
         ▼             ▼             ▼
┌─────────────────────────────────────────────┐
│              Hybrid Scoring                  │
│   ┌────────────────┐  ┌────────────────┐    │
│   │  Rule Scorer   │  │   LLM Judge    │    │
│   │     (40%)      │  │     (60%)      │    │
│   └────────────────┘  └────────────────┘    │
└────────────────────┬────────────────────────┘
                     │
                     ▼
              🏆 Best Draft Selected
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
