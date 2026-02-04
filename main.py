"""
AI Operations Assistant - Main FastAPI Application

A multi-agent AI system that processes natural language tasks,
plans execution steps, calls APIs, and returns structured results.
"""
import os
import time
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Initialize Logging
from utils.logging_config import setup_logging
logger = setup_logging()

# Load environment variables
load_dotenv()

from models import TaskRequest, TaskResponse, FinalResponse
from llm import LLMClient
from agents import PlannerAgent, ExecutorAgent, VerifierAgent


# Global instances
llm_client = None
planner = None
executor = None
verifier = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources"""
    global llm_client, planner, executor, verifier
    
    logger.info("Initializing AI Operations Assistant...")
    
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
        logger.info("Agents initialized successfully")
    
    yield
    
    # Shutdown
    if executor:
        await executor.close()
        logger.info("Executor, executor resources closed")
    
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
]

app = FastAPI(
    title="AI Operations Assistant",
    description="""
    # AI Operations Assistant API
    
    A multi-agent system capable of:
    * **Planning**: Analyzing complex natural language requests
    * **Execution**: Calling external APIs (GitHub, Weather, News)
    * **Verification**: Ensuring results are correct and formatted
    
    ## usage
    Post your natural language query to `/process`.
    """,
    version="1.0.1",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    contact={
        "name": "GenAI Intern Candidate",
        "email": "candidate@example.com",
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
        "version": "1.0.1",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    status = "healthy"
    if not llm_client:
        status = "degraded (no LLM)"
        
    return {
        "status": status,
        "agents": {
            "planner": planner is not None,
            "executor": executor is not None,
            "verifier": verifier is not None
        }
    }


@app.post("/process", response_model=TaskResponse, tags=["Operations"])
async def process_task(request: TaskRequest):
    """
    Process a natural language task through the multi-agent pipeline.
    
    Flow:
    1. **Planner Agent** creates an execution plan
    2. **Executor Agent** runs the plan steps
    3. **Verifier Agent** validates and formats the response
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
        
        # Step 1: Planning
        logger.info("Starting Phase 1: Planning")
        plan = await planner.process(request.task)
        
        if not plan.steps:
            logger.warning("Planning failed to generate steps")
            return TaskResponse(
                success=False,
                plan=plan,
                error="Could not create a valid execution plan for this task"
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


if __name__ == "__main__":
    import uvicorn
    # Use standard logging config for uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)