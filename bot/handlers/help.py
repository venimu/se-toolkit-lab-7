"""Handler for /help command."""


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
