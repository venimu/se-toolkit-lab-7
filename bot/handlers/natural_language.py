"""Natural language query handler with fallback for greetings and gibberish.

This handler processes plain text messages that aren't slash commands.
It uses the LLM-powered intent router to understand what the user wants.
"""

import re

from services.api_client import LMSAPIClient
from services.llm_client import LLMClient
from handlers.intent_router import IntentRouter


# Simple patterns for fallback detection (not for routing, just for graceful handling)
GREETING_PATTERNS = [
    r"\b(hi|hello|hey|greetings|good\s+(morning|afternoon|evening))\b",
    r"\b(how\s+are\s+you|how\s+is\s+it\s+going)\b",
]


def _is_greeting(message: str) -> bool:
    """Check if a message is a greeting.

    This is NOT for routing - the LLM handles routing. This is just for
    providing a quick, friendly response to simple greetings without
    burning API calls.

    Args:
        message: The user's message.

    Returns:
        True if the message appears to be a greeting.
    """
    message_lower = message.lower().strip()
    for pattern in GREETING_PATTERNS:
        if re.search(pattern, message_lower):
            return True
    return False


def _get_greeting_response() -> str:
    """Return a friendly greeting response with capabilities hint.

    Returns:
        A greeting message that also hints at what the bot can do.
    """
    return """Hello! 👋 I'm your LMS assistant. I can help you with:

• Checking system health
• Browsing available labs and tasks
• Viewing scores and pass rates
• Comparing group performance
• Finding top learners
• Tracking completion rates

Just ask me anything like:
- "What labs are available?"
- "Show me scores for lab 4"
- "Which lab has the lowest pass rate?"
- "Who are the top 5 students in lab 3?"

You can also use commands like /start, /help, /health, /labs, /scores"""


def _is_gibberish(message: str) -> bool:
    """Check if a message appears to be gibberish or too short to process.

    This is a simple heuristic - very short messages or random character
    sequences. The LLM will still try to handle these gracefully.

    Args:
        message: The user's message.

    Returns:
        True if the message appears to be gibberish.
    """
    message_clean = message.strip()

    # Too short (1-2 chars of random letters)
    if len(message_clean) <= 2 and message_clean.isalpha():
        return True

    # Repeated characters (e.g., "aaaa", "asdfgh")
    if len(message_clean) >= 4:
        unique_ratio = len(set(message_clean.lower())) / len(message_clean)
        if unique_ratio < 0.4:
            return True

    # No vowels at all (likely random consonants)
    vowels = set("aeiouаеёиоуыэюя")
    if not any(c in vowels for c in message_clean.lower()):
        if len(message_clean) >= 4:
            return True

    return False


def _get_gibberish_response() -> str:
    """Return a helpful response for unclear messages.

    Returns:
        A message asking for clarification with examples.
    """
    return """I'm not sure I understood that. 😅 Could you rephrase your question?

Here are some things I can help you with:
• "What labs are available?"
• "Show me scores for lab 4"
• "Which lab has the lowest pass rate?"
• "Who are the top students?"
• "Compare groups in lab 3"

Or just use /help to see all available commands!"""


async def handle_natural_language(
    message: str,
    api_client: LMSAPIClient,
    llm_client: LLMClient,
) -> str:
    """Handle a natural language message from the user.

    This function:
    1. Checks for simple greetings (quick response without LLM)
    2. Checks for gibberish (helpful fallback)
    3. Otherwise, routes through the LLM intent router

    Args:
        message: The user's natural language message.
        api_client: The LMS API client.
        llm_client: The LLM client for tool calling.

    Returns:
        The bot's response.
    """
    # Quick greeting check (saves API calls)
    if _is_greeting(message):
        return _get_greeting_response()

    # Gibberish check
    if _is_gibberish(message):
        return _get_gibberish_response()

    # Route through LLM
    router = IntentRouter(api_client)
    return await router.route(message, llm_client)
