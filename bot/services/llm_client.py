"""LLM client service with tool calling support.

This module handles communication with the LLM API for intent routing.
It supports tool/function calling, allowing the LLM to decide which API
endpoints to call based on the user's natural language query.
"""

import json
import sys
from typing import Any

import httpx


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
            timeout=60.0,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    def _build_system_prompt(self) -> str:
        """Build the system prompt that instructs the LLM how to use tools.

        Returns:
            System prompt string.
        """
        return """You are a helpful assistant for a Learning Management System (LMS).
You have access to various tools (API endpoints) that can fetch data about labs, students, scores, and analytics.

When a user asks a question, you should:
1. Analyze what information they need
2. Call the appropriate tool(s) to get that information
3. Once you have the tool results, synthesize them into a clear, helpful answer

For multi-step questions, you may need to call multiple tools. For example:
- "Which lab has the lowest pass rate?" → First get all labs, then get pass rates for each, then compare
- "Compare group A and B" → Get groups data, then filter and compare

If the user's message is a greeting or doesn't require data, respond naturally without calling tools.
If the message is unclear or seems like gibberish, politely ask for clarification.

Always be specific and cite actual numbers from the data when available."""

    async def chat_with_tools(
        self,
        user_message: str,
        tools: list[dict[str, Any]],
        tool_executor: callable,
        max_iterations: int = 5,
    ) -> str:
        """Chat with the LLM using tool calling.

        This implements the tool calling loop:
        1. Send user message + tool definitions to LLM
        2. LLM responds with tool calls (or final answer)
        3. Execute the tool calls
        4. Feed results back to LLM
        5. Repeat until LLM produces final answer

        Args:
            user_message: The user's natural language query.
            tools: List of tool schemas (function definitions).
            tool_executor: Async function that takes (tool_name, args) and returns result.
            max_iterations: Maximum tool calling iterations.

        Returns:
            The LLM's final response.
        """
        # Build conversation history
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": user_message},
        ]

        for iteration in range(max_iterations):
            # Call LLM
            response_data = await self._call_llm(messages, tools)

            # Check if LLM wants to call tools
            tool_calls = response_data.get("choices", [{}])[0].get("message", {}).get("tool_calls", [])

            if not tool_calls:
                # LLM produced final answer
                return response_data.get("choices", [{}])[0].get("message", {}).get("content", "I couldn't process that request.")

            # Execute tool calls
            tool_results = []
            for tool_call in tool_calls:
                function = tool_call.get("function", {})
                tool_name = function.get("name", "")
                tool_args_str = function.get("arguments", "{}")

                try:
                    tool_args = json.loads(tool_args_str) if tool_args_str else {}
                except json.JSONDecodeError:
                    tool_args = {}

                print(f"[tool] LLM called: {tool_name}({tool_args})", file=sys.stderr)

                # Execute the tool
                try:
                    result = await tool_executor(tool_name, tool_args)
                    print(f"[tool] Result: {self._summarize_result(result)}", file=sys.stderr)
                    tool_results.append({
                        "role": "tool",
                        "content": json.dumps(result, default=str),
                        "tool_call_id": tool_call.get("id", "unknown"),
                    })
                except Exception as e:
                    print(f"[tool] Error executing {tool_name}: {e}", file=sys.stderr)
                    tool_results.append({
                        "role": "tool",
                        "content": json.dumps({"error": str(e)}),
                        "tool_call_id": tool_call.get("id", "unknown"),
                    })

            # Feed tool results back to LLM
            print(f"[summary] Feeding {len(tool_results)} tool result(s) back to LLM", file=sys.stderr)
            messages.append(response_data.get("choices", [{}])[0].get("message", {}))
            messages.extend(tool_results)

        # If we exhausted iterations, return what we have
        return response_data.get("choices", [{}])[0].get("message", {}).get("content", "I'm having trouble processing this request. Please try rephrasing.")

    async def _call_llm(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Make a call to the LLM API.

        Args:
            messages: Conversation history.
            tools: Tool definitions.

        Returns:
            Raw API response.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
        }

        response = await self._client.post("/chat/completions", json=payload)
        response.raise_for_status()
        return response.json()

    def _summarize_result(self, result: Any) -> str:
        """Create a short summary of a tool result for debugging.

        Args:
            result: The tool result.

        Returns:
            A short summary string.
        """
        if isinstance(result, list):
            return f"{len(result)} items"
        elif isinstance(result, dict):
            return f"dict with {len(result)} keys"
        else:
            return str(result)[:50]
