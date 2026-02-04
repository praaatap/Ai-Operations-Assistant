"""
AI Operations Assistant - Main FastAPI Application

A multi-agent AI system that processes natural language tasks,
plans execution steps, calls APIs, and returns structured results.

Enhanced with LangGraph workflow orchestration and Redis caching.
"""
import os
import time
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse

# Initialize Logging
from utils.logging_config import setup_logging
logger = setup_logging()

# Load environment variables
load_dotenv()

from models import TaskRequest, TaskResponse, FinalResponse
from llm import LLMClient
from agents import PlannerAgent, ExecutorAgent, VerifierAgent
from agents.langgraph_workflow import LangGraphWorkflow
from utils.cache import cache_client


# Global instances
llm_client = None
planner = None
executor = None
verifier = None
workflow = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources"""
    global llm_client, planner, executor, verifier, workflow
    
    logger.info("Initializing AI Operations Assistant...")
    
    # Initialize Redis cache
    redis_connected = await cache_client.connect()
    if redis_connected:
        logger.info("Redis cache connected successfully")
    else:
        logger.warning("Using in-memory cache (Redis not available)")
    
    # Check for required API keys
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not gemini_key and not openai_key:
        logger.warning("No LLM API key configured! Please set GEMINI_API_KEY or OPENAI_API_KEY.")
        llm_client = None
    else:
        # Startup with available LLM
        try:
            llm_client = LLMClient()
            logger.info(f"LLM client initialized with provider: {llm_client.provider}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            llm_client = None
    
    if llm_client:
        planner = PlannerAgent(llm_client)
        executor = ExecutorAgent(llm_client)
        verifier = VerifierAgent(llm_client)
        
        # Initialize LangGraph workflow
        workflow = LangGraphWorkflow(planner, executor, verifier)
        logger.info("Agents and LangGraph workflow initialized successfully")
    
    yield
    
    # Shutdown
    if executor:
        await executor.close()
        logger.info("Executor resources closed")
    
    # Close Redis connection
    await cache_client.close()
    
    logger.info("Shutdown complete")


# Metadata for OpenAPI
tags_metadata = [
    {
        "name": "Operations",
        "description": "Core operations for processing tasks",
    },
    {
        "name": "System",
        "description": "Health checks and system information",
    },
    {
        "name": "Debug",
        "description": "Debugging and monitoring endpoints",
    },
]

app = FastAPI(
    title="AI Operations Assistant",
    description="""
    # AI Operations Assistant API
    
    A multi-agent system powered by **LangGraph** capable of:
    * **Planning**: Analyzing complex natural language requests
    * **Execution**: Calling external APIs (GitHub, Weather, News)
    * **Verification**: Ensuring results are correct and formatted
    * **Caching**: Redis-backed response caching for improved performance
    
    ## Usage
    Post your natural language query to `/process`.
    
    ## Architecture
    Uses LangGraph state machine for orchestrating Planner → Executor → Verifier agents.
    """,
    version="2.0.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    contact={
        "name": "AI Operations Team",
        "email": "ai-ops@example.com",
    },
    license_info={
        "name": "MIT",
    }
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error. Please try again later."},
    )


@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "AI Operations Assistant",
        "version": "2.0.0",
        "features": [
            "Multi-agent architecture (Planner, Executor, Verifier)",
            "LangGraph workflow orchestration",
            "Redis caching for API responses",
            "GitHub, Weather, and News API integrations"
        ],
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    status = "healthy"
    if not llm_client:
        status = "degraded (no LLM)"
    
    cache_stats = cache_client.get_stats()
        
    return {
        "status": status,
        "version": "2.0.0",
        "agents": {
            "planner": planner is not None,
            "executor": executor is not None,
            "verifier": verifier is not None
        },
        "workflow": workflow is not None,
        "cache": cache_stats
    }


@app.post("/process", response_model=TaskResponse, tags=["Operations"])
async def process_task(request: TaskRequest):
    """
    Process a natural language task through the multi-agent pipeline.
    
    Flow:
    1. **Planner Agent** creates an execution plan
    2. **Executor Agent** runs the plan steps
    3. **Verifier Agent** validates and formats the response
    
    Uses LangGraph for orchestration with automatic retry logic.
    """
    logger.info(f"Received task request: {request.task}")
    
    if not planner or not executor or not verifier:
        logger.error("Agents not initialized due to missing LLM configuration")
        raise HTTPException(
            status_code=503, 
            detail="LLM not configured. Please set GEMINI_API_KEY or OPENAI_API_KEY."
        )
    
    try:
        start_time = time.time()
        
        if workflow:
            # Use LangGraph workflow
            logger.info("Processing with LangGraph workflow")
            result = await workflow.run(request.task)
            
            # Extract response from workflow result
            final_response = result.get("final_response", {})
            
            duration = time.time() - start_time
            logger.info(f"Task processing completed in {duration:.2f}s")
            
            # Get token usage
            usage = llm_client.get_token_usage() if llm_client else {}
            
            return TaskResponse(
                success=result.get("success", False),
                plan=result.get("plan"),
                execution=result.get("execution_results", [{}])[-1] if result.get("execution_results") else None,
                response=FinalResponse(
                    success=final_response.get("success", False),
                    summary=final_response.get("summary", "Task completed"),
                    data=final_response.get("data", {}),
                    sources=final_response.get("sources", []),
                    errors=final_response.get("errors", [])
                ),
                cost=usage.get("estimated_cost_usd", 0.0)
            )
        else:
            # Fallback to direct agent calls
            logger.info("Processing with direct agent calls (LangGraph not available)")
            
            # Step 1: Planning
            logger.info("Starting Phase 1: Planning")
            try:
                plan = await planner.process(request.task)
                logger.info(f"Plan generated: {len(plan.steps)} steps")
            except Exception as e:
                logger.error(f"Planning failed with error: {e}")
                raise HTTPException(status_code=500, detail=f"Planning Agent failed: {e}")
            
            if not plan.steps:
                logger.warning("Planning completed but returned 0 steps. Raw plan: " + str(plan))
                return TaskResponse(
                    success=False,
                    plan=plan,
                    error="Could not create a valid execution plan for this task. The LLM might have failed to understand the request."
                )
            
            # Step 2: Execution
            logger.info(f"Starting Phase 2: Execution ({len(plan.steps)} steps)")
            execution = await executor.process(plan)
            
            # Step 3: Verification & Response Generation
            logger.info("Starting Phase 3: Verification")
            response = await verifier.process(plan, execution)
            
            duration = time.time() - start_time
            logger.info(f"Task processing completed in {duration:.2f}s with success={response.success}")
            
            return TaskResponse(
                success=response.success,
                plan=plan,
                execution=execution,
                response=response
            )
        
    except Exception as e:
        logger.error(f"Error processing task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/plan", tags=["Operations"])
async def plan_only(request: TaskRequest):
    """Get just the execution plan without running it (Dry Run)"""
    logger.info(f"Generating plan for: {request.task}")
    
    if not planner:
        raise HTTPException(
            status_code=503, 
            detail="LLM not configured."
        )
    try:
        plan = await planner.process(request.task)
        return {"success": True, "plan": plan}
    except Exception as e:
        logger.error(f"Planning error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph", tags=["Debug"], response_class=HTMLResponse)
async def view_workflow_graph():
    """View the LangGraph workflow as a Mermaid diagram"""
    if not workflow:
        raise HTTPException(status_code=503, detail="Workflow not initialized")
    
    mermaid_diagram = workflow.get_graph_visualization()
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Ops Workflow Graph</title>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                display: flex; 
                justify-content: center; 
                padding: 20px;
                background: #f5f5f5;
            }}
            .container {{
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{ color: #333; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔄 LangGraph Workflow</h1>
            <div class="mermaid">
            {mermaid_diagram}
            </div>
        </div>
        <script>mermaid.initialize({{startOnLoad:true}});</script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/cache/stats", tags=["Debug"])
async def cache_stats():
    """Get cache statistics"""
    return cache_client.get_stats()


@app.post("/cache/clear", tags=["Debug"])
async def clear_cache():
    """Clear all cached data"""
    success = await cache_client.clear()
    return {"success": success, "message": "Cache cleared" if success else "Failed to clear cache"}


if __name__ == "__main__":
    import uvicorn
    # Use standard logging config for uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)