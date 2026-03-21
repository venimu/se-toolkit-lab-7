"""Command handlers - pure functions that take input and return text.

These handlers have no dependency on Telegram. They can be called from:
- --test mode (CLI)
- Unit tests
- The actual Telegram bot

This is called *separation of concerns* - the handler logic is separate
from the transport layer (Telegram).
"""


async def handle_start() -> str:
    """Handle /start command - welcome message."""
    return (
        "👋 Welcome to the LMS Bot!\n\n"
        "I can help you check system health, browse labs, and view scores.\n\n"
        "Available commands:\n"
        "/start - Welcome message\n"
        "/help - List all commands\n"
        "/health - Check backend status\n"
        "/labs - List available labs\n"
        "/scores <lab> - View scores for a lab"
    )


async def handle_help() -> str:
    """Handle /help command - list available commands."""
    return (
        "📚 Available Commands:\n\n"
        "/start - Welcome message\n"
        "/help - Show this help message\n"
        "/health - Check if the backend is running\n"
        "/labs - List all available labs\n"
        "/scores <lab_name> - View pass rates for a specific lab\n\n"
        "You can also ask questions in plain language!"
    )


async def handle_health() -> str:
    """Handle /health command - check backend status.
    
    Task 2: This will call the LMS backend API.
    For now, returns a placeholder.
    """
    return "✅ Backend status: OK (placeholder - will be implemented in Task 2)"


async def handle_labs() -> str:
    """Handle /labs command - list available labs.
    
    Task 2: This will fetch labs from the LMS backend API.
    For now, returns a placeholder.
    """
    return "📋 Available labs: (placeholder - will be implemented in Task 2)"


async def handle_scores(lab_name: str | None = None) -> str:
    """Handle /scores command - view scores for a lab.
    
    Task 2: This will fetch scores from the LMS backend API.
    For now, returns a placeholder.
    
    Args:
        lab_name: The lab name to get scores for.
    """
    if not lab_name:
        return "Please specify a lab name, e.g., /scores lab-04"
    
    return f"📊 Scores for {lab_name}: (placeholder - will be implemented in Task 2)"
