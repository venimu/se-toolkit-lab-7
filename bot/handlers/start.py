"""Handler for /start command with inline keyboard buttons."""

from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


# Inline keyboard button definitions for common queries
# These buttons are shown to users after /start to help them discover actions
INLINE_KEYBOARD_BUTTONS: list[list[dict[str, Any]]] = [
    [
        {"text": "📋 List Labs", "callback_data": "query:list_labs"},
        {"text": "💚 Health Check", "callback_data": "query:health"},
    ],
    [
        {"text": "📊 View Scores", "callback_data": "query:scores"},
        {"text": "🏆 Top Learners", "callback_data": "query:top_learners"},
    ],
    [
        {"text": "📈 Pass Rates", "callback_data": "query:pass_rates"},
        {"text": "👥 Group Stats", "callback_data": "query:groups"},
    ],
    [
        {"text": "🔄 Sync Data", "callback_data": "query:sync"},
        {"text": "❓ Help", "callback_data": "query:help"},
    ],
]


def get_inline_keyboard() -> InlineKeyboardMarkup:
    """Return the inline keyboard markup for the /start command.

    Returns:
        InlineKeyboardMarkup with buttons for common queries.
    """
    keyboard = [
        [
            InlineKeyboardButton(text="📋 List Labs", callback_data="query:list_labs"),
            InlineKeyboardButton(text="💚 Health Check", callback_data="query:health"),
        ],
        [
            InlineKeyboardButton(text="📊 View Scores", callback_data="query:scores"),
            InlineKeyboardButton(
                text="🏆 Top Learners", callback_data="query:top_learners"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📈 Pass Rates", callback_data="query:pass_rates"
            ),
            InlineKeyboardButton(text="👥 Group Stats", callback_data="query:groups"),
        ],
        [
            InlineKeyboardButton(text="🔄 Sync Data", callback_data="query:sync"),
            InlineKeyboardButton(text="❓ Help", callback_data="query:help"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def handle_start() -> str:
    """Handle /start command - welcome message with inline keyboard hint."""
    return (
        "👋 Welcome to the LMS Bot!\n\n"
        "I can help you check system health, browse labs, and view scores.\n\n"
        "Use the buttons below or type your question in plain language!\n\n"
        "Available commands:\n"
        "/start - Welcome message\n"
        "/help - List all commands\n"
        "/health - Check backend status\n"
        "/labs - List available labs\n"
        "/scores <lab> - View pass rates for a specific lab"
    )
