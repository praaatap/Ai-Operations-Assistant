# AI Operations Assistant

A multi-agent AI system that accepts natural language tasks, plans execution steps, calls external APIs, and returns structured results.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Request (Natural Language)             │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                        PLANNER AGENT                             │
│  • Analyzes user intent                                          │
│  • Creates step-by-step execution plan                           │
│  • Selects appropriate tools for each step                       │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                       EXECUTOR AGENT                             │
│  • Iterates through plan steps                                   │
│  • Calls tools with appropriate parameters                       │
│  • Handles errors with retry logic                               │
└─────────────────────────────────────────────────────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
        ┌──────────┐      ┌──────────┐      ┌──────────┐
        │  GitHub  │      │ Weather  │      │   News   │
        │   Tool   │      │   Tool   │      │   Tool   │
        └──────────┘      └──────────┘      └──────────┘
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                       VERIFIER AGENT                             │
│  • Validates execution results                                   │
│  • Identifies missing or failed data                             │
│  • Formats final structured response                             │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Structured Response (JSON)                   │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Clone and Navigate

```bash
cd ai_ops_assistant
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
copy .env.example .env
# Edit .env with your API keys
```

Required API keys:
- `GEMINI_API_KEY` - Get from [Google AI Studio](https://aistudio.google.com/app/apikey)
- `NEWS_API_KEY` - Get from [NewsAPI.org](https://newsapi.org/register)

### 5. Run the Server

```bash
uvicorn main:app --reload
```

Server starts at: `http://localhost:8000`

### Optional: Run with Docker

If you prefer to run with Docker:

1. Build and run using Docker Compose:
```bash
docker-compose up --build -d
```

2. View logs:
```bash
docker-compose logs -f
```

3. Stop the container:
```bash
docker-compose down
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/process` | POST | Process a natural language task |
| `/plan` | POST | Get execution plan only (no execution) |

## 🔧 Integrated APIs

| API | Purpose | Authentication |
|-----|---------|----------------|
| **GitHub API** | Search repositories, get repo details | None (public access) |
| **Open-Meteo API** | Get weather data for any city | None (free) |
| **NewsAPI** | Fetch news headlines and search articles | API Key (free tier) |

## 🧪 Example Prompts

### 1. GitHub Search
```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"task": "Find the top 5 most starred Python machine learning libraries on GitHub"}'
```

### 2. Weather Query
```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"task": "What is the current weather in Tokyo, London, and New York?"}'
```

### 3. News Search
```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"task": "Get me the latest technology news headlines"}'
```

### 4. Combined Query
```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"task": "Find trending AI repositories on GitHub and get the latest AI news"}'
```

### 5. Complex Multi-Step Task
```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"task": "Get the weather in San Francisco and find popular weather app repositories on GitHub"}'
```

## 📁 Project Structure

```
ai_ops_assistant/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py      # Abstract base class
│   ├── planner.py         # Planner Agent
│   ├── executor.py        # Executor Agent
│   └── verifier.py        # Verifier Agent
├── tools/
│   ├── __init__.py
│   ├── base_tool.py       # Tool interface
│   ├── github_tool.py     # GitHub API
│   ├── weather_tool.py    # Weather API
│   └── news_tool.py       # News API
├── llm/
│   ├── __init__.py
│   └── client.py          # Multi-LLM client (Gemini/OpenAI)
├── main.py                # FastAPI application
├── models.py              # Pydantic models
├── requirements.txt       # Dependencies
├── .env.example           # Environment template
└── README.md              # This file
```

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes* | Google Gemini API key |
| `OPENAI_API_KEY` | Yes* | OpenAI API key |
| `NEWS_API_KEY` | Yes | NewsAPI.org API key |
| `LLM_PROVIDER` | No | `gemini` or `openai` (default: gemini) |

*At least one LLM API key is required

## ⚠️ Known Limitations & Tradeoffs

1. **Rate Limits**: GitHub API has 60 requests/hour for unauthenticated requests. NewsAPI free tier has limits.

2. **No Caching**: API responses are not cached. Each request makes fresh API calls.

3. **Sequential Execution**: Steps are executed sequentially, not in parallel.

4. **No Persistent State**: No conversation memory between requests.

5. **LLM Dependency**: Quality of plans depends on LLM understanding of the task.

## 🛠️ Development

### Logging

The application uses structured logging. Logs are output to:
- Console (standard output)
- `ai_ops.log` file

### Running Tests

Run the test suite using pytest:

```bash
pytest tests/
```

### OpenAPI Specification

The project follows OpenAPI standards.
- Interactive Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- JSON Spec: `http://localhost:8000/openapi.json`

To generate the `openapi.json` file statically:
```bash
python scripts/generate_schema.py
```

## 📝 License

MIT License
