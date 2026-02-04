"""
Pydantic Models - Structured data models for agents and tools
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


# ============== Tool Models ==============

class ToolAction(str, Enum):
    """Supported tool actions"""
    GITHUB_SEARCH = "github_search"
    GITHUB_GET_REPO = "github_get_repo"
    WEATHER_GET = "weather_get"
    NEWS_HEADLINES = "news_headlines"
    NEWS_SEARCH = "news_search"


class ToolParameter(BaseModel):
    """Single tool parameter"""
    name: str
    value: Any


class ToolCall(BaseModel):
    """A single tool call specification"""
    tool: str = Field(..., description="Tool name: github, weather, or news")
    action: str = Field(..., description="Action to perform with the tool")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the tool")


class ToolResult(BaseModel):
    """Result from a tool execution"""
    tool: str
    action: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ============== Planner Models ==============

class PlanStep(BaseModel):
    """A single step in the execution plan"""
    step_number: int = Field(..., description="Step number in sequence")
    description: str = Field(..., description="What this step does")
    tool: str = Field(..., description="Tool to use: github, weather, or news")
    action: str = Field(..., description="Action to perform")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the tool")
    depends_on: List[int] = Field(default_factory=list, description="Step numbers this depends on")


class ExecutionPlan(BaseModel):
    """Complete execution plan from Planner Agent"""
    task_summary: str = Field(..., description="Summary of user's request")
    steps: List[PlanStep] = Field(..., description="Ordered list of steps to execute")
    expected_output: str = Field(..., description="What the final output should contain")

    model_config = {
        "json_schema_extra": {
            "example": {
                "task_summary": "Get weather for London",
                "steps": [
                    {
                        "step_number": 1,
                        "description": "Fetch weather data for London",
                        "tool": "weather",
                        "action": "get",
                        "parameters": {"city": "London"},
                        "depends_on": []
                    }
                ],
                "expected_output": "Current weather conditions in London"
            }
        }
    }


# ============== Executor Models ==============

class StepExecution(BaseModel):
    """Result of executing a single step"""
    step_number: int
    status: str = Field(..., description="'success', 'failed', or 'skipped'")
    tool: str
    action: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ExecutionResult(BaseModel):
    """Complete result from Executor Agent"""
    success: bool
    steps_executed: int
    steps_failed: int
    results: List[StepExecution]


# ============== Verifier Models ==============

class VerificationIssue(BaseModel):
    """An issue found during verification"""
    step_number: int
    issue_type: str = Field(..., description="'missing_data', 'incomplete', 'error'")
    description: str
    can_retry: bool = False


class VerificationResult(BaseModel):
    """Result from Verifier Agent"""
    is_complete: bool
    issues: List[VerificationIssue] = Field(default_factory=list)
    retry_steps: List[int] = Field(default_factory=list, description="Step numbers to retry")


# ============== Final Output Models ==============

class FinalResponse(BaseModel):
    """Final structured response to user"""
    success: bool
    summary: str = Field(..., description="Human-readable summary of results")
    data: Dict[str, Any] = Field(default_factory=dict, description="Structured data results")
    sources: List[str] = Field(default_factory=list, description="APIs/sources used")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "summary": "The current weather in London is 15°C with clear skies.",
                "data": {
                    "weather_get": {
                        "temperature": 15,
                        "condition": "Clear sky",
                        "location": "London"
                    }
                },
                "sources": ["Weather API"],
                "errors": []
            }
        }
    }


# ============== API Request/Response Models ==============

class TaskRequest(BaseModel):
    """API request model"""
    task: str = Field(..., description="Natural language task/query from user", min_length=1, max_length=500)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "task": "What is the weather in Tokyo and finding trending AI repos on GitHub?"
            }
        }
    }


class TaskResponse(BaseModel):
    """API response model"""
    success: bool
    plan: Optional[ExecutionPlan] = None
    execution: Optional[ExecutionResult] = None
    response: Optional[FinalResponse] = None
    cost: float = Field(default=0.0, description="Estimated cost in USD")
    error: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "response": {
                    "success": True,
                    "summary": "I found the weather and repositories.",
                    "data": {},
                    "sources": [],
                    "errors": []
                }
            }
        }
    }
