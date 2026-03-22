"""Intent router handler - uses LLM to route natural language to tools."""

from services.api_client import LMSAPIClient, format_api_error
from services.llm_client import LLMClient


async def handle_intent(
    message: str,
    api_client: LMSAPIClient,
    llm_client: LLMClient,
) -> str:
    """Handle a natural language message using LLM intent routing.

    This function sends the user's message to the LLM along with tool definitions.
    The LLM decides which tools to call, we execute them, feed results back,
    and the LLM produces the final answer.

    Args:
        message: The user's input message.
        api_client: The LMS API client for executing tool calls.
        llm_client: The LLM client for chatting.

    Returns:
        The LLM's response string.
    """
    try:
        response = await llm_client.route(message, api_client, debug=True)
        return response
    except Exception as e:
        return format_api_error(e, "LLM")
