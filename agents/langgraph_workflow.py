"""
LangGraph Workflow - Multi-agent orchestration using LangGraph state machine
"""
import logging
from typing import TypedDict, Annotated, List, Any, Literal
from operator import add

logger = logging.getLogger(__name__)

# Type definitions for state
class AgentState(TypedDict):
    """State shared across all agents in the workflow"""
    # Input
    task: str
    
    # Planning
    plan: dict | None
    plan_steps: List[dict]
    
    # Execution
    execution_results: Annotated[List[dict], add]
    current_step: int
    
    # Verification
    verification: dict | None
    retry_count: int
    max_retries: int
    
    # Output
    final_response: dict | None
    success: bool
    errors: List[str]


def create_initial_state(task: str) -> AgentState:
    """Create initial state for a new task"""
    return AgentState(
        task=task,
        plan=None,
        plan_steps=[],
        execution_results=[],
        current_step=0,
        verification=None,
        retry_count=0,
        max_retries=2,
        final_response=None,
        success=False,
        errors=[]
    )


class LangGraphWorkflow:
    """
    LangGraph-based workflow orchestrator for multi-agent system.
    
    Flow:
    1. Planner creates execution plan
    2. Executor runs each step
    3. Verifier validates results
    4. Retry if needed, otherwise finalize
    """
    
    def __init__(self, planner, executor, verifier):
        self.planner = planner
        self.executor = executor
        self.verifier = verifier
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph state machine"""
        try:
            from langgraph.graph import StateGraph, END
            
            # Create graph with state schema
            workflow = StateGraph(AgentState)
            
            # Add nodes
            workflow.add_node("plan", self._plan_node)
            workflow.add_node("execute", self._execute_node)
            workflow.add_node("verify", self._verify_node)
            workflow.add_node("finalize", self._finalize_node)
            
            # Set entry point
            workflow.set_entry_point("plan")
            
            # Add edges
            workflow.add_edge("plan", "execute")
            workflow.add_edge("execute", "verify")
            
            # Conditional edge: retry or finalize
            workflow.add_conditional_edges(
                "verify",
                self._should_retry,
                {
                    "retry": "execute",
                    "finalize": "finalize"
                }
            )
            
            workflow.add_edge("finalize", END)
            
            # Compile the graph
            return workflow.compile()
            
        except ImportError as e:
            logger.warning(f"LangGraph not available: {e}. Using simple orchestration.")
            return None
    
    async def _plan_node(self, state: AgentState) -> dict:
        """Planning node - creates execution plan"""
        logger.info(f"[PLAN] Creating plan for: {state['task']}")
        
        try:
            plan = await self.planner.process(state["task"])
            
            return {
                "plan": plan.model_dump() if hasattr(plan, 'model_dump') else plan,
                "plan_steps": [step.model_dump() if hasattr(step, 'model_dump') else step 
                              for step in plan.steps] if hasattr(plan, 'steps') else []
            }
        except Exception as e:
            logger.error(f"[PLAN] Error: {e}")
            return {
                "errors": [f"Planning failed: {str(e)}"],
                "success": False
            }
    
    async def _execute_node(self, state: AgentState) -> dict:
        """Execution node - runs plan steps"""
        logger.info(f"[EXECUTE] Running {len(state.get('plan_steps', []))} steps")
        
        try:
            # Reconstruct plan object for executor
            from models import ExecutionPlan, PlanStep
            
            plan_data = state.get("plan", {})
            steps = [PlanStep(**s) for s in state.get("plan_steps", [])]
            
            plan = ExecutionPlan(
                task_summary=plan_data.get("task_summary", state["task"]),
                steps=steps,
                expected_output=plan_data.get("expected_output", "")
            )
            
            execution = await self.executor.process(plan)
            
            return {
                "execution_results": [execution.model_dump() if hasattr(execution, 'model_dump') else execution]
            }
        except Exception as e:
            logger.error(f"[EXECUTE] Error: {e}")
            return {
                "errors": [f"Execution failed: {str(e)}"]
            }
    
    async def _verify_node(self, state: AgentState) -> dict:
        """Verification node - validates results"""
        logger.info("[VERIFY] Validating execution results")
        
        try:
            from models import ExecutionPlan, ExecutionResult, PlanStep
            
            # Reconstruct objects
            plan_data = state.get("plan", {})
            steps = [PlanStep(**s) for s in state.get("plan_steps", [])]
            
            plan = ExecutionPlan(
                task_summary=plan_data.get("task_summary", state["task"]),
                steps=steps,
                expected_output=plan_data.get("expected_output", "")
            )
            
            # Get latest execution result
            exec_results = state.get("execution_results", [])
            if exec_results:
                latest = exec_results[-1]
                if isinstance(latest, dict):
                    execution = ExecutionResult(**latest)
                else:
                    execution = latest
            else:
                from models import ExecutionResult
                execution = ExecutionResult(
                    success=False,
                    steps_executed=0,
                    steps_failed=0,
                    results=[]
                )
            
            response = await self.verifier.process(plan, execution)
            
            return {
                "verification": response.model_dump() if hasattr(response, 'model_dump') else response,
                "retry_count": state.get("retry_count", 0) + 1
            }
        except Exception as e:
            logger.error(f"[VERIFY] Error: {e}")
            return {
                "errors": [f"Verification failed: {str(e)}"],
                "retry_count": state.get("retry_count", 0) + 1
            }
    
    def _should_retry(self, state: AgentState) -> Literal["retry", "finalize"]:
        """Determine if we should retry or finalize"""
        verification = state.get("verification", {})
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 2)
        
        # Check if verification indicates issues that can be retried
        if isinstance(verification, dict):
            success = verification.get("success", True)
            has_errors = bool(verification.get("errors", []))
        else:
            success = True
            has_errors = False
        
        should_retry = not success and has_errors and retry_count < max_retries
        
        if should_retry:
            logger.info(f"[WORKFLOW] Retrying (attempt {retry_count + 1}/{max_retries})")
            return "retry"
        
        return "finalize"
    
    async def _finalize_node(self, state: AgentState) -> dict:
        """Finalize node - prepare final response"""
        logger.info("[FINALIZE] Preparing final response")
        
        verification = state.get("verification", {})
        errors = state.get("errors", [])
        
        success = not errors and verification.get("success", False)
        
        return {
            "final_response": verification,
            "success": success
        }
    
    async def run(self, task: str) -> dict:
        """Run the complete workflow"""
        initial_state = create_initial_state(task)
        
        if self.graph:
            # Use LangGraph
            logger.info("[WORKFLOW] Running with LangGraph")
            try:
                final_state = await self.graph.ainvoke(initial_state)
                return final_state
            except Exception as e:
                logger.error(f"[WORKFLOW] LangGraph error: {e}")
                # Fall back to simple orchestration
                return await self._simple_orchestration(task)
        else:
            # Simple orchestration fallback
            return await self._simple_orchestration(task)
    
    async def _simple_orchestration(self, task: str) -> dict:
        """Fallback simple orchestration without LangGraph"""
        logger.info("[WORKFLOW] Running simple orchestration")
        
        state = create_initial_state(task)
        
        # Plan
        state = {**state, **await self._plan_node(state)}
        
        # Execute
        state = {**state, **await self._execute_node(state)}
        
        # Verify
        state = {**state, **await self._verify_node(state)}
        
        # Finalize
        state = {**state, **await self._finalize_node(state)}
        
        return state
    
    def get_graph_visualization(self) -> str | None:
        """Get Mermaid diagram of the workflow"""
        if not self.graph:
            return None
        
        try:
            return self.graph.get_graph().draw_mermaid()
        except Exception as e:
            logger.warning(f"Could not generate graph visualization: {e}")
            return """
graph TD
    A[Start] --> B[Planner Agent]
    B --> C[Executor Agent]
    C --> D[Verifier Agent]
    D --> E{Success?}
    E -->|Yes| F[Finalize]
    E -->|No & Retries Left| C
    E -->|No & No Retries| F
    F --> G[End]
"""
