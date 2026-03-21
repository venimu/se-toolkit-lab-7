"""Handler for /start command."""


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
        "/scores <lab> - View pass rates for a specific lab"
    )
