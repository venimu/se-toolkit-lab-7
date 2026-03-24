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
            "description": "List all labs and tasks available in the LMS. Use this first when you need to discover lab identifiers such as 'lab-01' before calling analytics tools.",
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
            "description": "List enrolled learners and their student groups. Use this for questions about enrollment counts, student rosters, or groups.",
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
            "description": "Get the 4-bucket score distribution for one lab. Use this when the user asks for scores, score histogram, or grade spread for a specific lab.",
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
            "description": "Get per-task average scores and attempt counts for one lab. Use this for pass-rate questions and for comparing labs after you discover the lab IDs.",
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
            "description": "Get submissions per day for one lab. Use this for time trends, activity over time, or submission spikes.",
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
            "description": "Get per-group average scores and student counts for one lab. Use this to compare groups or find the best or worst group in a lab.",
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
            "description": "Get the top learners for one lab. This tool requires a lab identifier and optionally a limit. If the user asks for top students without naming a lab, ask a clarifying question instead of guessing.",
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
            "description": "Get the completion rate percentage for one lab, including how many learners passed out of the total.",
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
            "description": "Refresh LMS data from the autochecker. Use this only when the user explicitly asks to sync, refresh, reload, or update the data.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]

# System prompt that encourages tool use
SYSTEM_PROMPT = """You are an LMS analytics assistant with access to backend tools.

Your job is to answer the user's question by choosing tools, reading their results, and then writing a grounded answer.

Rules:
1. If the question is about labs, learners, scores, pass rates, groups, completion, timeline, or sync, use tools instead of answering from memory.
2. Do not invent lab IDs, percentages, counts, or names. If you need data, call a tool.
3. If the request is ambiguous but still data-oriented, ask one short clarifying question.
4. If the message is a greeting, respond briefly and mention that the user can ask about labs, scores, pass rates, learners, groups, or sync.
5. If the message is gibberish or not understandable, say that you did not understand and give a few concrete examples of what the user can ask.
6. If the user explicitly asks to sync or refresh data, call trigger_sync.

Tool usage guidance:
- Use get_items first whenever you need to discover valid lab identifiers.
- All analytics tools except get_items, get_learners, and trigger_sync require a specific lab ID.
- If the user says "lab 4", treat that as ambiguous and ask what they want to know about lab 4.
- If the user asks for top learners without naming a lab, ask which lab they mean.
- For comparisons across labs, first call get_items, then call the needed analytics tool for each relevant lab, then compare the returned numbers.

Answer style:
- Be concise but specific.
- Prefer actual numbers, counts, and lab names from tool results.
- After tool calls finish, synthesize the data instead of dumping raw JSON.
"""


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
