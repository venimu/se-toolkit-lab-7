"""LLM client service with tool calling support.

This module handles communication with the LLM API, including:
- Tool definitions (schemas for backend endpoints)
- Tool calling loop (LLM decides, we execute, feed back results)
- Response summarization
"""

import json
import httpx
from typing import Any


# Tool definitions for all 9 backend endpoints
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_items",
            "description": "Get list of all labs and tasks from the LMS",
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
            "description": "Get list of enrolled students and their groups",
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
            "description": "Get score distribution (4 buckets) for a specific lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g., 'lab-01'",
                    }
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pass_rates",
            "description": "Get per-task average pass rates and attempt counts for a lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g., 'lab-01'",
                    }
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_timeline",
            "description": "Get submissions per day timeline for a lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g., 'lab-01'",
                    }
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_groups",
            "description": "Get per-group scores and student counts for a lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g., 'lab-01'",
                    }
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_learners",
            "description": "Get top N learners by score for a lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g., 'lab-01'",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of top learners to return, e.g., 5",
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
            "description": "Get completion rate percentage for a lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g., 'lab-01'",
                    }
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_sync",
            "description": "Trigger ETL sync to refresh data from autochecker",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]

# System prompt that encourages tool use
SYSTEM_PROMPT = """You are an assistant for a Learning Management System (LMS). You have access to tools that let you query data about labs, students, scores, and analytics.

When a user asks a question:
1. Think about what data you need to answer
2. Call the appropriate tool(s) to get that data
3. Once you have the data, summarize it clearly for the user with specific numbers and names

If the user's message is a greeting (hello, hi, hey), respond naturally and mention what you can help with - list available commands like /labs, /scores, /health.

If the user types gibberish or something you don't understand (like "asdfgh"), say you didn't understand and suggest what commands they can try - mention available commands and that they can ask about labs, scores, or pass rates.

If the user asks to sync, refresh, load, or update data, call the trigger_sync tool and report that the sync was successful and data has been loaded/refreshed.

Available tools:
- get_items: List all labs and tasks - use this to discover what labs exist
- get_learners: List enrolled students and groups
- get_scores: Score distribution for a lab (4 buckets)
- get_pass_rates: Per-task average pass rates and attempt counts for a lab
- get_timeline: Submissions per day timeline for a lab
- get_groups: Per-group scores and student counts for a lab
- get_top_learners: Top N learners by score for a lab
- get_completion_rate: Completion rate percentage for a lab
- trigger_sync: Trigger ETL sync to refresh data from autochecker - call this when user asks to sync, refresh, load, or update data

Always use tools when the user asks about labs, scores, students, or analytics. Be specific - include actual lab names, numbers, and percentages from the data. When comparing labs, always fetch the data first using get_items to get lab IDs, then call the appropriate analytics tools.

For "which lab has the lowest/highest pass rate" type questions:
1. First call get_items to get all lab identifiers
2. Then call get_pass_rates for each lab
3. Compare the results and report the specific lab name with its percentage

Be helpful and specific. Always ground your answers in the actual data returned by the tools."""


class LLMClient:
    """Client for LLM API with tool calling support."""

    def __init__(self, base_url: str, api_key: str, model: str):
        """Initialize the LLM client.

        Args:
            base_url: The base URL of the LLM API.
            api_key: The API key for authentication.
            model: The model name to use.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=180.0,  # Extended timeout for multi-step LLM queries
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Send a chat request to the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            tools: Optional list of tool definitions.

        Returns:
            The LLM response as a dict.
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        response = await self._client.post("/chat/completions", json=payload)
        response.raise_for_status()
        return response.json()

    async def route(
        self,
        user_message: str,
        api_client: Any,
        debug: bool = True,
    ) -> str:
        """Route a user message through the LLM tool calling loop.

        This implements the core loop:
        1. Send user message + tool definitions to LLM
        2. If LLM calls tools, execute them
        3. Feed tool results back to LLM
        4. LLM produces final answer

        Args:
            user_message: The user's input message.
            api_client: The LMS API client for executing tool calls.
            debug: Whether to print debug output to stderr.

        Returns:
            The final response string.
        """
        import sys

        def log(msg: str) -> None:
            if debug:
                print(msg, file=sys.stderr)

        # Initialize conversation with system prompt
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        max_iterations = 5  # Prevent infinite loops
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Call LLM with current conversation
            response = await self.chat(messages, tools=TOOL_DEFINITIONS)
            choice = response["choices"][0]
            message = choice["message"]

            # Check if LLM wants to call tools
            tool_calls = message.get("tool_calls", [])

            if not tool_calls:
                # No tool calls - LLM has final answer
                return message.get(
                    "content", "I don't have enough information to answer that."
                )

            # Add LLM's message with tool calls to conversation
            messages.append(message)

            # Execute each tool call
            for tool_call in tool_calls:
                function = tool_call["function"]
                tool_name = function["name"]
                tool_args = (
                    json.loads(function["arguments"]) if function["arguments"] else {}
                )

                log(f"[tool] LLM called: {tool_name}({tool_args})")

                # Execute the tool
                result = await self._execute_tool(tool_name, tool_args, api_client)
                log(f"[tool] Result: {str(result)[:200]}")

                # Add tool result to conversation
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": tool_name,
                        "content": json.dumps(result)
                        if not isinstance(result, str)
                        else result,
                    }
                )

            log(f"[summary] Feeding {len(tool_calls)} tool result(s) back to LLM")

        # Max iterations reached - return what we have
        return "I'm having trouble processing this request. Please try rephrasing."

    async def _execute_tool(
        self,
        name: str,
        args: dict[str, Any],
        api_client: Any,
    ) -> Any:
        """Execute a tool call using the API client.

        Args:
            name: The tool name.
            args: The tool arguments.
            api_client: The LMS API client.

        Returns:
            The tool result.
        """
        tool_methods = {
            "get_items": api_client.get_items,
            "get_learners": api_client.get_learners,
            "get_scores": api_client.get_scores,
            "get_pass_rates": api_client.get_pass_rates,
            "get_timeline": api_client.get_timeline,
            "get_groups": api_client.get_groups,
            "get_top_learners": api_client.get_top_learners,
            "get_completion_rate": api_client.get_completion_rate,
            "trigger_sync": api_client.trigger_sync,
        }

        method = tool_methods.get(name)
        if not method:
            return {"error": f"Unknown tool: {name}"}

        try:
            # Call the method with args
            if args:
                result = await method(**args)
            else:
                result = await method()
            return result
        except Exception as e:
            return {"error": str(e)}
