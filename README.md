# AI Operations Assistant

A multi-agent AI system powered by **LangGraph** that accepts natural language tasks, plans execution steps, calls external APIs, and returns structured results with **Redis caching** for improved performance.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Request (Natural Language)             │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH WORKFLOW                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    PLANNER AGENT                        │   │
│  │  • Analyzes user intent using LLM                       │   │
│  │  • Creates step-by-step execution plan                  │   │
│  │  • Selects appropriate tools for each step              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   EXECUTOR AGENT                        │   │
│  │  • Iterates through plan steps                          │   │
│  │  • Calls tools with appropriate parameters              │   │
│  │  • Handles errors with retry logic                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│               ┌──────────────┼──────────────┐                   │
│               ▼              ▼              ▼                   │
│         ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│         │  GitHub  │  │ Weather  │  │   News   │               │
│         │   Tool   │  │   Tool   │  │   Tool   │               │
│         └──────────┘  └──────────┘  └──────────┘               │
│               │              │              │                   │
│               └──────────────┼──────────────┘                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   VERIFIER AGENT                        │   │
│  │  • Validates execution results                          │   │
│  │  • Identifies missing or failed data                    │   │
│  │  • Formats final structured response                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                   ┌──────────┴──────────┐                       │
│                   ▼                     ▼                       │
│              [Success]             [Retry?]──► Back to Executor │
│                   │                                              │
└───────────────────┼──────────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Structured Response (JSON)                   │
└─────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │   Redis Cache   │
                    │  (API Responses)│
                    └─────────────────┘
```

## ✨ Features

- **Multi-Agent Architecture**: Planner, Executor, and Verifier agents working together
- **LangGraph Orchestration**: State machine-based workflow with automatic retry logic
- **Parallel Execution**: Independent steps run concurrently for faster performance
- **Cost Tracking**: Real-time token usage and cost estimation
- **Redis Caching**: API response caching with configurable TTL
- **Multiple LLM Support**: Gemini and OpenAI integration
- **Real API Integration**: GitHub, Weather (Open-Meteo), and News APIs

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
cd ai_ops_assistant

# Copy environment file and add your API keys
copy .env.example .env
# Edit .env with your API keys

# Start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 2: Local Development

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment file and add your API keys
copy .env.example .env

# Start Redis (optional, falls back to in-memory cache)
docker run -d -p 6379:6379 redis:7-alpine

# Run the server
uvicorn main:app --reload
```

Server starts at: `http://localhost:8000`

### Running the Streamlit UI

```bash
# After starting the API server, run Streamlit in a new terminal
streamlit run streamlit_app.py
```

Streamlit UI starts at: `http://localhost:8501`

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information and features |
| `/health` | GET | Health check with cache stats |
| `/process` | POST | Process a natural language task |
| `/plan` | POST | Get execution plan only (dry run) |
| `/graph` | GET | View LangGraph workflow diagram |
| `/cache/stats` | GET | Cache hit/miss statistics |
| `/cache/clear` | POST | Clear cached data |

## 🔧 Integrated APIs

| API | Purpose | Cache TTL |
|-----|---------|-----------|
| **GitHub API** | Search repos, get details | 10 minutes |
| **Open-Meteo API** | Current weather data | 5 minutes |
| **NewsAPI** | Headlines and articles | 15 minutes |

## 🧪 Example Prompts

### GitHub Search
```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"task": "Find the top 5 most starred Python machine learning libraries on GitHub"}'
```

### Weather Query
```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"task": "What is the current weather in Tokyo, London, and New York?"}'
```

### News Search
```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"task": "Get me the latest technology news headlines"}'
```

### Combined Query
```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"task": "Find trending AI repositories on GitHub and get the latest AI news"}'
```

## 📁 Project Structure

```
ai_ops_assistant/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py           # Abstract base class
│   ├── planner.py              # Planner Agent
│   ├── executor.py             # Executor Agent
│   ├── verifier.py             # Verifier Agent
│   └── langgraph_workflow.py   # LangGraph orchestration
├── tools/
│   ├── __init__.py
│   ├── base_tool.py            # Tool interface
│   ├── github_tool.py          # GitHub API (cached)
│   ├── weather_tool.py         # Weather API (cached)
│   └── news_tool.py            # News API (cached)
├── llm/
│   ├── __init__.py
│   └── client.py               # Multi-LLM client
├── utils/
│   ├── __init__.py
│   ├── logging_config.py       # Logging setup
│   └── cache.py                # Redis cache utility
├── tests/
│   └── test_api.py             # API tests
├── main.py                     # FastAPI application
├── models.py                   # Pydantic models
├── docker-compose.yml          # Docker services
├── Dockerfile                  # Container definition
├── requirements.txt            # Dependencies
├── .env.example                # Environment template
└── README.md                   # Documentation
```

## 🔑 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes* | - | Google Gemini API key |
| `OPENAI_API_KEY` | Yes* | - | OpenAI API key |
| `NEWS_API_KEY` | Yes | - | NewsAPI.org API key |
| `LLM_PROVIDER` | No | gemini | `gemini` or `openai` |
| `REDIS_URL` | No | redis://localhost:6379 | Redis connection URL |
| `CACHE_TTL_WEATHER` | No | 300 | Weather cache TTL (seconds) |
| `CACHE_TTL_NEWS` | No | 900 | News cache TTL (seconds) |
| `CACHE_TTL_GITHUB` | No | 600 | GitHub cache TTL (seconds) |

*At least one LLM API key is required

## 🛠️ Development

### View Workflow Graph
Navigate to `http://localhost:8000/graph` to see the LangGraph workflow as a Mermaid diagram.

### Cache Statistics
```bash
curl http://localhost:8000/cache/stats
```

### Running Tests
```bash
pytest tests/ -v
```

### OpenAPI Documentation
- Interactive Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 📝 License

MIT License
