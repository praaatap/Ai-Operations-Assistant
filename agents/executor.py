"""
Executor Agent - Executes plan steps by calling tools
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Any

from .base_agent import BaseAgent
from models import ExecutionPlan, ExecutionResult, StepExecution, PlanStep
from tools import GitHubTool, WeatherTool, NewsTool


class ExecutorAgent(BaseAgent):
    """
    Executor Agent takes an execution plan and runs each step,
    calling the appropriate tools and collecting results.
    """
    
    def __init__(self, llm_client):
        super().__init__(llm_client)
        self.tools = {
            "github": GitHubTool(),
            "weather": WeatherTool(),
            "news": NewsTool()
        }
    
    @property
    def name(self) -> str:
        return "Executor"
    
    @property
    def system_prompt(self) -> str:
        return """You are an Executor Agent. Your role is to execute tool calls and collect results.
You don't generate plans - you only execute steps given to you."""

    async def process(self, plan: ExecutionPlan) -> ExecutionResult:
        """
        Execute steps in the plan, processing independent steps in parallel.
        
        Args:
            plan: ExecutionPlan with steps to execute
            
        Returns:
            ExecutionResult with all step outcomes
        """
        import asyncio
        
        results: List[StepExecution] = []
        step_results: Dict[int, Any] = {}  # Store results by step number
        
        # Sort steps by step number to ensure correct processing order
        sorted_steps = sorted(plan.steps, key=lambda x: x.step_number)
        
        # Track completed steps
        completed_step_ids = set()
        pending_steps = list(sorted_steps)
        
        while pending_steps:
            # excessive safeguard: break if no progress to avoid infinite loops
            progress_made = False
            
            # Find steps that are ready to run (dependencies satisfied)
            batch = []
            remaining = []
            
            for step in pending_steps:
                dependencies = set(step.depends_on)
                if dependencies.issubset(completed_step_ids):
                    batch.append(step)
                else:
                    remaining.append(step)
            
            if not batch:
                # This handles cases where dependencies might be circular or missing
                # We'll just run the next available step to unblock
                if pending_steps:
                    batch.append(pending_steps[0])
                    remaining = pending_steps[1:]
            
            # Execute batch in parallel
            batch_coroutines = [self._execute_step(step, step_results) for step in batch]
            if batch_coroutines:
                batch_results = await asyncio.gather(*batch_coroutines)
                
                for execution in batch_results:
                    results.append(execution)
                    completed_step_ids.add(execution.step_number)
                    
                    if execution.status == "success":
                        step_results[execution.step_number] = execution.result
                
                progress_made = True
            
            pending_steps = remaining
            
            if not progress_made and pending_steps:
                # Should not happen with proper dependency graph, but just in case
                break
        
        # Re-sort results by step number for consistent output
        results.sort(key=lambda x: x.step_number)
        
        # Calculate summary
        successful = sum(1 for r in results if r.status == "success")
        failed = sum(1 for r in results if r.status == "failed")
        
        return ExecutionResult(
            success=failed == 0,
            steps_executed=len(results),
            steps_failed=failed,
            results=results
        )
    
    async def _execute_step(self, step: PlanStep, previous_results: Dict[int, Any]) -> StepExecution:
        """Execute a single step"""
        tool_name = step.tool.lower()
        
        # Check if tool exists
        if tool_name not in self.tools:
            return StepExecution(
                step_number=step.step_number,
                status="failed",
                tool=step.tool,
                action=step.action,
                error=f"Unknown tool: {step.tool}"
            )
        
        tool = self.tools[tool_name]
        
        try:
            # Prepare parameters
            params = self._prepare_parameters(step, previous_results)
            params["action"] = step.action
            
            # Execute the tool
            result = await tool.execute(**params)
            
            # Check for errors in result
            if "error" in result:
                return StepExecution(
                    step_number=step.step_number,
                    status="failed",
                    tool=step.tool,
                    action=step.action,
                    error=result["error"]
                )
            
            return StepExecution(
                step_number=step.step_number,
                status="success",
                tool=step.tool,
                action=step.action,
                result=result
            )
            
        except Exception as e:
            return StepExecution(
                step_number=step.step_number,
                status="failed",
                tool=step.tool,
                action=step.action,
                error=str(e)
            )
    
    def _prepare_parameters(self, step: PlanStep, previous_results: Dict[int, Any]) -> Dict[str, Any]:
        """Prepare parameters, resolving any dependencies"""
        params = dict(step.parameters)
        
        # Here we could resolve references to previous step results
        # For now, just return the parameters as-is
        return params
    
    async def execute_single_step(self, step: PlanStep) -> StepExecution:
        """Execute a single step (for retries)"""
        return await self._execute_step(step, {})
    
    async def close(self):
        """Clean up tool resources"""
        for tool in self.tools.values():
            if hasattr(tool, 'close'):
                await tool.close()
