"""
Verifier Agent - Validates execution results and formats final output
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any

from .base_agent import BaseAgent
from models import (
    ExecutionPlan, 
    ExecutionResult, 
    VerificationResult,
    VerificationIssue,
    FinalResponse,
    StepExecution
)


class VerifierAgent(BaseAgent):
    """
    Verifier Agent validates execution results, identifies issues,
    and formats the final response for the user.
    """
    
    @property
    def name(self) -> str:
        return "Verifier"
    
    @property
    def system_prompt(self) -> str:
        return """You are a Verifier Agent for an AI Operations Assistant.

Your role is to:
1. Analyze execution results for completeness and correctness
2. Identify missing or failed data
3. Format a clear, helpful response for the user

When creating the final response:
- Summarize the key findings in plain language
- Organize data in a structured way
- Note any errors or limitations
- Be concise but comprehensive

OUTPUT FORMAT (JSON only):
{
    "success": true/false,
    "summary": "Human-readable summary of results",
    "data": {
        "category1": [...],
        "category2": [...]
    },
    "sources": ["API names used"],
    "errors": ["any errors encountered"]
}"""

    async def process(self, 
                      plan: ExecutionPlan, 
                      execution: ExecutionResult) -> FinalResponse:
        """
        Verify execution results and generate final response.
        
        Args:
            plan: Original execution plan
            execution: Results from executor
            
        Returns:
            FinalResponse with formatted results
        """
        # First verify the results
        verification = self._verify_results(plan, execution)
        
        # Generate the final response using LLM
        final_response = await self._generate_response(plan, execution, verification)
        
        return final_response
    
    def _verify_results(self, 
                        plan: ExecutionPlan, 
                        execution: ExecutionResult) -> VerificationResult:
        """Check execution results for issues"""
        issues: List[VerificationIssue] = []
        retry_steps: List[int] = []
        
        for step_result in execution.results:
            if step_result.status == "failed":
                issues.append(VerificationIssue(
                    step_number=step_result.step_number,
                    issue_type="error",
                    description=step_result.error or "Unknown error",
                    can_retry=True
                ))
                retry_steps.append(step_result.step_number)
            
            elif step_result.status == "success" and step_result.result:
                # Check for empty results
                if self._is_empty_result(step_result.result):
                    issues.append(VerificationIssue(
                        step_number=step_result.step_number,
                        issue_type="missing_data",
                        description="Tool returned empty results",
                        can_retry=False
                    ))
        
        return VerificationResult(
            is_complete=len(issues) == 0,
            issues=issues,
            retry_steps=retry_steps
        )
    
    def _is_empty_result(self, result: Dict[str, Any]) -> bool:
        """Check if result is essentially empty"""
        if not result:
            return True
        
        # Check common result patterns
        if "repositories" in result and len(result["repositories"]) == 0:
            return True
        if "articles" in result and len(result["articles"]) == 0:
            return True
        
        return False
    
    async def _generate_response(self,
                                  plan: ExecutionPlan,
                                  execution: ExecutionResult,
                                  verification: VerificationResult) -> FinalResponse:
        """Use LLM to generate a formatted response"""
        
        # Collect all successful results
        results_data = {}
        sources = set()
        errors = []
        
        for step_result in execution.results:
            if step_result.status == "success" and step_result.result:
                tool_key = f"{step_result.tool}_{step_result.action}"
                results_data[tool_key] = step_result.result
                sources.add(f"{step_result.tool.title()} API")
            elif step_result.status == "failed":
                errors.append(f"Step {step_result.step_number}: {step_result.error}")
        
        # Create prompt for LLM to format response
        prompt = f"""Format these execution results into a user-friendly response.

ORIGINAL REQUEST: {plan.task_summary}

EXECUTION RESULTS:
{self._format_results_for_prompt(execution.results)}

Create a response with:
1. A natural language summary answering the user's question
2. Organized data from the results
3. Note any errors or limitations

Respond with JSON only."""

        try:
            response = self._generate_json(prompt)
            
            return FinalResponse(
                success=execution.success,
                summary=response.get("summary", plan.task_summary),
                data=response.get("data", results_data),
                sources=list(sources),
                errors=errors
            )
        except Exception as e:
            # Fallback response
            return FinalResponse(
                success=execution.success,
                summary=f"Completed {execution.steps_executed} steps with {execution.steps_failed} failures.",
                data=results_data,
                sources=list(sources),
                errors=errors + [str(e)]
            )
    
    def _format_results_for_prompt(self, results: List[StepExecution]) -> str:
        """Format step results for LLM prompt"""
        formatted = []
        for step in results:
            if step.status == "success":
                formatted.append(f"Step {step.step_number} ({step.tool}/{step.action}): SUCCESS")
                if step.result:
                    # Truncate large results
                    result_str = str(step.result)
                    if len(result_str) > 500:
                        result_str = result_str[:500] + "..."
                    formatted.append(f"  Result: {result_str}")
            else:
                formatted.append(f"Step {step.step_number} ({step.tool}/{step.action}): FAILED - {step.error}")
        
        return "\n".join(formatted)
    
    def get_retry_steps(self, 
                        plan: ExecutionPlan, 
                        verification: VerificationResult) -> List:
        """Get steps that should be retried"""
        return [
            step for step in plan.steps 
            if step.step_number in verification.retry_steps
        ]
