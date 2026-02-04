"""
Planner Agent - Converts natural language tasks into structured execution plans
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List

from .base_agent import BaseAgent
from models import ExecutionPlan, PlanStep


class PlannerAgent(BaseAgent):
    """
    Planner Agent converts user's natural language request into a structured
    step-by-step execution plan with tool calls.
    """
    
    @property
    def name(self) -> str:
        return "Planner"
    
    @property
    def system_prompt(self) -> str:
        return """You are a Planning Agent for an AI Operations Assistant.

Your role is to analyze user requests and create structured execution plans.

AVAILABLE TOOLS:
1. github - Search GitHub repositories and get repo details
   - Actions: "search" (search repos by query), "get_repo" (get specific repo details)
   - Parameters for search: query (string), sort (stars/forks/updated), limit (int)
   - Parameters for get_repo: owner (string), repo (string)

2. weather - Get current weather for any city
   - Actions: "get" (get weather for a city)
   - Parameters: city (string), units (celsius/fahrenheit)

3. news - Fetch news articles and headlines
   - Actions: "headlines" (top headlines), "search" (search articles)
   - Parameters for headlines: category (business/tech/sports/etc), country (us/gb/in), limit
   - Parameters for search: query (string), limit (int)

4. wikipedia - Search Wikipedia and get article summaries
   - Actions: "search" (find articles), "summary" (get article summary)
   - Parameters: query (string), limit (int, for search only)

5. jokes - Get random jokes for entertainment
   - Actions: "random" (any joke), "programming" (coding jokes), "dad" (dad jokes), "pun" (puns)
   - Parameters: count (int, default 1)

6. quotes - Get inspirational and famous quotes
   - Actions: "random" (random quotes), "today" (quote of the day), "search" (search quotes), "author" (by author)
   - Parameters: query (string, for search/author), count (int)

RULES:
1. Break down complex tasks into sequential steps
2. Each step should use exactly ONE tool
3. Identify dependencies between steps
4. Be specific with parameters - extract values from user's request
5. Always respond with valid JSON matching the required schema

OUTPUT FORMAT (JSON only):
{
    "task_summary": "Brief summary of what user wants",
    "steps": [
        {
            "step_number": 1,
            "description": "What this step does",
            "tool": "tool_name",
            "action": "action_name",
            "parameters": {"param": "value"},
            "depends_on": []
        }
    ],
    "expected_output": "What the final result should contain"
}"""

    async def process(self, task: str) -> ExecutionPlan:
        """
        Convert a natural language task into an execution plan.
        
        Args:
            task: User's natural language task/request
            
        Returns:
            ExecutionPlan with steps to execute
        """
        prompt = f"""Create an execution plan for this user request:

USER REQUEST: {task}

Analyze the request and create a step-by-step plan using the available tools.
Respond with JSON only."""

        try:
            response = self._generate_json(prompt)
            
            # Parse steps
            steps = []
            for step_data in response.get("steps", []):
                step = PlanStep(
                    step_number=step_data.get("step_number", len(steps) + 1),
                    description=step_data.get("description", ""),
                    tool=step_data.get("tool", ""),
                    action=step_data.get("action", ""),
                    parameters=step_data.get("parameters", {}),
                    depends_on=step_data.get("depends_on", [])
                )
                steps.append(step)
            
            plan = ExecutionPlan(
                task_summary=response.get("task_summary", task),
                steps=steps,
                expected_output=response.get("expected_output", "Results from the executed tools")
            )
            
            return plan
            
        except Exception as e:
            # Return a minimal plan on error
            return ExecutionPlan(
                task_summary=task,
                steps=[],
                expected_output=f"Error creating plan: {str(e)}"
            )
