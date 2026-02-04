# AI Operations Assistant

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-orange?style=for-the-badge)
![Gemini](https://img.shields.io/badge/Google%20Gemini-Integrated-8E75B2?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

## Demo Images
<img width="2532" height="1347" alt="image" src="https://github.com/user-attachments/assets/cb1e1297-a106-4a53-ab36-ea90711fe227" />
<img width="2551" height="1357" alt="image" src="https://github.com/user-attachments/assets/dafdca62-c876-495d-b419-1d2d52e17659" />


## Project Overview

The AI Operations Assistant is an enterprise-grade, multi-agent system designed to autonomously plan, execute, and verify complex operational tasks. Built on a microservices architecture, it leverages Large Language Models (LLMs) to orchestrate a suite of integrated tools, providing real-time intelligence and automation.

This system demonstrates advanced agentic workflows, separating reasoning (Planner), action (Executor), and validation (Verifier) into distinct, coordinate components.

## Architecture

The system follows a strict multi-agent orchestration pattern powered by LangGraph:

```mermaid
graph TD
    User[User Request] --> Planner
    Planner[Planner Agent] -->|Execution Plan| Executor
    
    subgraph Execution Loop
        Executor[Executor Agent] -->|Tool Calls| Tools
        Tools -->|Results| Executor
    end
    
    Executor -->|Raw Results| Verifier
    Verifier[Verifier Agent] -->|Validation| Response
    
    subgraph Integrated Tools
        Tools --> GitHub[GitHub API]
        Tools --> Weather[Weather API]
        Tools --> News[News API]
        Tools --> Wikipedia[Wikipedia API]
        Tools --> Jokes[Jokes API]
        Tools --> Quotes[Quotes API]
    end
    
    Response[Structured JSON Response] --> UI[Streamlit Dashboard]
```

## Key Features

1.  **Multi-Agent Orchestration**: Implements a chain-of-thought workflow where agents specialize in planning, execution, and verification.
2.  **Tool Integration**: Seamlessly connects to 6 external APIs including GitHub, Open-Meteo, NewsAPI, and Wikipedia.
3.  **Dual LLM Support**: Configurable to run on Google Gemini (default) or Groq (Llama 3) for high-performance inference.
4.  **Resilient Architecture**: Includes automatic backend recovery, health monitoring, and graceful error handling.
5.  **caching Layer**: Redis-based caching strategy to optimize API usage and reduce latency.
6.  **Premium User Interface**: A data-centric dashboard built with Streamlit, featuring real-time workflow visualization and cost analytics.

## Technology Stack

*   **Backend**: FastAPI, Uvicorn
*   **Frontend**: Streamlit
*   **AI Orchestration**: LangChain, LangGraph
*   **LLM Providers**: Google GenAI (Gemini), Groq
*   **Caching**: Redis (with in-memory fallback)
*   **Deployment**: Docker-ready, Streamlit Cloud compatible

## Installation

### Prerequisites

*   Python 3.10 or higher
*   Git

### Setup Steps

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/praaatap/Ai-Operations-Assistant.git
    cd Ai-Operations-Assistant
    ```

2.  **Create Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuration**
    Copy the example environment file and configure your API keys:
    ```bash
    cp .env.example .env
    ```
    Edit `.env` to include your `GEMINI_API_KEY` or `GROQ_API_KEY`.

## Usage

### Running the Application

To launch both the backend API and the frontend dashboard:

```bash
streamlit run streamlit_app.py
```

The application will automatically start the backend server and open the web interface in your default browser at `http://localhost:8501`.

### API Endpoints

The system exposes a RESTful API for direct integration:

*   `POST /process`: Submit a natural language task.
*   `GET /health`: Check system status and agent availability.

## Project Structure

```text
├── agents/             # Agent implementations (Planner, Executor, Verifier)
├── llm/                # LLM client abstraction and cost tracking
├── tools/              # Tool integrations (GitHub, Weather, etc.)
├── utils/              # Helper utilities (Caching, Logging)
├── main.py             # FastAPI backend entry point
├── streamlit_app.py    # Streamlit frontend dashboard
└── requirements.txt    # Project dependencies
```

## Contact

For inquiries regarding this project, please open an issue in the repository.
