"""Intent router for natural language queries.

This module defines all backend endpoints as LLM tools and provides
the routing logic that lets the LLM decide which API calls to make.
"""

import json
from typing import Any

from services.api_client import LMSAPIClient


def get_tool_schemas() -> list[dict[str, Any]]:
    """Return all 9 backend endpoints as LLM tool schemas.

    Each tool schema describes:
    - name: The function name the LLM will call
    - description: What the tool does and when to use it
    - parameters: JSON Schema for the tool's arguments

    Returns:
        List of tool schema dictionaries.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "get_items",
                "description": "Get the list of all labs and tasks available in the LMS. Use this when the user asks about available labs, what labs exist, or needs to see the full catalog.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_learners",
                "description": "Get the list of all enrolled learners and their group assignments. Use this when the user asks about students, enrollment, or who is in the course.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_scores",
                "description": "Get score distribution (4 buckets) for a specific lab. Use this when the user asks about score distribution, how students scored, or wants to see the spread of scores for a lab.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g., 'lab-01', 'lab-04'",
                        },
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_pass_rates",
                "description": "Get per-task average scores and attempt counts for a specific lab. Use this when the user asks about pass rates, average scores, task difficulty, or how well students are doing on a lab.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g., 'lab-01', 'lab-04'",
                        },
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_timeline",
                "description": "Get submission timeline showing submissions per day for a lab. Use this when the user asks about when submissions happened, activity over time, or submission patterns.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g., 'lab-01', 'lab-04'",
                        },
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_groups",
                "description": "Get per-group scores and student counts for a lab. Use this when the user asks about group performance, which group is best, or wants to compare groups.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g., 'lab-01', 'lab-04'",
                        },
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_top_learners",
                "description": "Get top N learners by score for a lab. Use this when the user asks about top students, leaderboard, who is doing best, or wants to see high performers.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g., 'lab-01', 'lab-04'",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of top learners to return, e.g., 5, 10",
                            "default": 10,
                        },
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_completion_rate",
                "description": "Get completion rate percentage for a lab. Use this when the user asks about completion rate, how many students finished, or what percentage completed a lab.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g., 'lab-01', 'lab-04'",
                        },
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "trigger_sync",
                "description": "Trigger a data sync from the autochecker to refresh the database. Use this when the user asks to refresh data, sync, or update the latest scores.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
    ]


class IntentRouter:
    """Routes natural language queries to backend API via LLM.

    The router:
    1. Receives a natural language query from the user
    2. Sends it to the LLM along with tool definitions
    3. The LLM decides which tools to call
    4. Executes the tool calls against the backend API
    5. Feeds results back to the LLM
    6. Returns the LLM's final synthesized answer
    """

    def __init__(self, api_client: LMSAPIClient):
        """Initialize the intent router.

        Args:
            api_client: The LMS API client for executing tool calls.
        """
        self.api_client = api_client
        self.tool_schemas = get_tool_schemas()
        self.tool_executors = self._build_tool_executors()

    def _build_tool_executors(self) -> dict[str, callable]:
        """Build a mapping of tool names to executor functions.

        Returns:
            Dictionary mapping tool names to async functions.
        """
        return {
            "get_items": self.api_client.get_items,
            "get_learners": self.api_client.get_learners,
            "get_scores": lambda lab="": self.api_client.get_scores(lab.get("lab", "")),
            "get_pass_rates": lambda lab="": self.api_client.get_pass_rates(lab.get("lab", "")),
            "get_timeline": lambda lab="": self.api_client.get_timeline(lab.get("lab", "")),
            "get_groups": lambda lab="": self.api_client.get_groups(lab.get("lab", "")),
            "get_top_learners": lambda lab="", limit=10: self.api_client.get_top_learners(
                lab.get("lab", ""), lab.get("limit", 10)
            ),
            "get_completion_rate": lambda lab="": self.api_client.get_completion_rate(lab.get("lab", "")),
            "trigger_sync": self.api_client.trigger_sync,
        }

    async def route(self, user_message: str, llm_client: "LLMClient") -> str:
        """Route a user message through the LLM to get a response.

        Args:
            user_message: The user's natural language query.
            llm_client: The LLM client for making tool-calling requests.

        Returns:
            The LLM's final response.
        """
        # Create a tool executor closure that captures self.api_client
        async def execute_tool(tool_name: str, args: dict[str, Any]) -> Any:
            """Execute a tool by name with given arguments.

            Args:
                tool_name: The name of the tool to execute.
                args: The arguments for the tool.

            Returns:
                The tool result.
            """
            if tool_name not in self.tool_executors:
                return {"error": f"Unknown tool: {tool_name}"}

            executor = self.tool_executors[tool_name]
            return await executor(**args) if args else await executor()

        # Use the LLM client's chat_with_tools method
        return await llm_client.chat_with_tools(
            user_message=user_message,
            tools=self.tool_schemas,
            tool_executor=execute_tool,
        )
