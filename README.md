# AI Operations Assistant

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-orange?style=for-the-badge)
![Gemini](https://img.shields.io/badge/Google%20Gemini-Integrated-8E75B2?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

## Project Overview

The AI Operations Assistant is an enterprise-grade, multi-agent system designed to autonomously plan, execute, and verify complex operational tasks. Built on a microservices architecture, it leverages Large Language Models (LLMs) to orchestrate a suite of integrated tools, providing real-time intelligence and automation.

This system demonstrates advanced agentic workflows, separating reasoning (Planner), action (Executor), and validation (Verifier) into distinct, connected components.

## Architecture

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
5.  **Caching Layer**: Redis-based caching strategy to optimize API usage and reduce latency.
6.  **Premium User Interface**: A data-centric dashboard built with Streamlit, featuring real-time workflow visualization and cost analytics.

## Installation & Setup

Follow these steps to set up the project locally.

### 1. Prerequisites
*   Python 3.10 or higher
*   Git

### 2. Clone the Repository
```bash
git clone https://github.com/praaatap/Ai-Operations-Assistant.git
cd Ai-Operations-Assistant
```

### 3. Create a Virtual Environment (Recommended)
It is highly recommended to use a virtual environment to manage dependencies.

**Windows:**
```powershell
# Create the virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\activate
```

**macOS / Linux:**
```bash
# Create the virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

*Note: When activated, your terminal prompt should show `(venv)`.*

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configuration
Copy the example environment file and configure your API keys.

```bash
cp .env.example .env
# On Windows use: copy .env.example .env
```

Open `.env` in a text editor and add your API keys:
*   `GEMINI_API_KEY`: Required for Gemini LLM.
*   `GROQ_API_KEY`: Required if using Groq.
*   `NEWS_API_KEY`: Required for News tool.

## Usage

### Running the Application

To launch both the backend API and the frontend dashboard (with auto-start enabled):

```bash
# Ensure your venv is activated
streamlit run streamlit_app.py
```

The application opens in your browser at `http://localhost:8501`.

### Troubleshooting

*   **API Connection Error**: If you see connection errors, ensure `uvicorn` is installed and the backend started. The Streamlit app tries to auto-start it, but you can also run it manually:
    ```bash
    uvicorn main:app --reload --host 127.0.0.1 --port 8000
    ```
*   **Module Not Found**: Ensure you have activated your virtual environment (`venv`) before running commands.

## Technology Stack

*   **Backend**: FastAPI, Uvicorn
*   **Frontend**: Streamlit
*   **AI Orchestration**: LangChain, LangGraph
*   **LLM Providers**: Google GenAI (Gemini), Groq
*   **Caching**: Redis (with in-memory fallback)
*   **Deployment**: Docker-ready, Streamlit Cloud compatible

## Contact

For inquiries regarding this project, please open an issue in the repository.
