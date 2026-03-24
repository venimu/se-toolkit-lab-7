"""Command handlers - pure functions that take input and return text.

These handlers have no dependency on Telegram. They can be called from:
- --test mode (CLI)
- Unit tests
- The actual Telegram bot

This is called *separation of concerns* - the handler logic is separate
from the transport layer (Telegram).
"""

from handlers.health import handle_health
from handlers.help import handle_help
from handlers.labs import handle_labs
from handlers.scores import handle_scores
from handlers.start import handle_start, get_inline_keyboard, INLINE_KEYBOARD_BUTTONS

__all__ = [
    "handle_help",
    "handle_health",
    "handle_labs",
    "handle_scores",
    "handle_start",
    "get_inline_keyboard",
    "INLINE_KEYBOARD_BUTTONS",
]
