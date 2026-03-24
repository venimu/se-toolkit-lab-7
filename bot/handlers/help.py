"""Handler for /help command with inline keyboard reference."""

from handlers.start import get_inline_keyboard


async def handle_help() -> str:
    """Handle /help command - list available commands with button reference."""
    keyboard = get_inline_keyboard()
    button_count = sum(len(row) for row in keyboard)

    return (
        "📚 Available Commands:\n\n"
        "/start - Welcome message\n"
        "/help - Show this help message\n"
        "/health - Check if the backend is running\n"
        "/labs - List all available labs\n"
        "/scores <lab_name> - View pass rates for a specific lab\n\n"
        f"Quick actions: Use the {button_count} inline buttons below for common queries,\n"
        "or ask questions in plain language like:\n"
        "• 'which lab has the lowest pass rate?'\n"
        "• 'show me scores for lab 4'\n"
        "• 'who are the top 5 students?'"
    )
