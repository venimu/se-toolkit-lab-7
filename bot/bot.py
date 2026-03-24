#!/usr/bin/env python3
"""LMS Telegram Bot entry point.

Usage:
    # Test mode (no Telegram connection needed)
    uv run bot.py --test "/start"
    uv run bot.py --test "/help"
    uv run bot.py --test "/health"
    uv run bot.py --test "/labs"
    uv run bot.py --test "/scores lab-04"

    # Production mode (connects to Telegram)
    uv run bot.py
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add bot directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import load_config
from handlers import (
    handle_help,
    handle_health,
    handle_labs,
    handle_scores,
    handle_start,
)
from handlers.intent_router import handle_intent
from services.api_client import LMSAPIClient
from services.llm_client import LLMClient


def parse_command(test_input: str) -> tuple[str, str | None]:
    """Parse a command string into command name and argument.

    Args:
        test_input: The command string, e.g., "/scores lab-04"

    Returns:
        Tuple of (command_name, argument) where argument may be None.
    """
    parts = test_input.strip().split(maxsplit=1)
    command = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else None
    return command, arg


async def run_test_mode(command: str) -> None:
    """Run a command in test mode and print result to stdout.

    Args:
        command: The command string to execute.
    """
    # Load config and create API client
    config = load_config()
    client = LMSAPIClient(config.lms_api_base_url, config.lms_api_key)
    llm_client = LLMClient(
        config.llm_api_base_url,
        config.llm_api_key,
        config.llm_api_model,
    )

    try:
        cmd_name, arg = parse_command(command)

        # Check if this is a slash command or plain text
        if cmd_name.startswith("/"):
            # Slash command - use direct handlers
            if cmd_name == "/start":
                result = await handle_start()
            elif cmd_name == "/help":
                result = await handle_help()
            elif cmd_name == "/health":
                result = await handle_health(client)
            elif cmd_name == "/labs":
                result = await handle_labs(client)
            elif cmd_name == "/scores":
                result = await handle_scores(client, arg)
            else:
                print(f"Unknown command: {cmd_name}")
                print("Available commands: /start, /help, /health, /labs, /scores")
                sys.exit(0)
        else:
            # Plain text - use LLM intent routing
            # The entire input is the message (not just the first word)
            result = await handle_intent(command, client, llm_client)

        print(result)
    finally:
        await client.close()
        await llm_client.close()


async def run_telegram_mode() -> None:
    """Run the bot in production mode, connecting to Telegram.

    This initializes aiogram, registers handlers for slash commands and
    plain text messages, and starts polling for updates.
    """
    from aiogram import Bot, Dispatcher, types
    from aiogram.filters import Command
    from config import load_config
    from handlers import get_inline_keyboard

    config = load_config()
    bot = Bot(token=config.bot_token)
    dp = Dispatcher()

    # Create API and LLM clients
    client = LMSAPIClient(config.lms_api_base_url, config.lms_api_key)
    llm_client = LLMClient(
        config.llm_api_base_url,
        config.llm_api_key,
        config.llm_api_model,
    )

    # Register slash command handlers
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message) -> None:
        response = await handle_start()
        keyboard = get_inline_keyboard()
        await message.answer(response, reply_markup=keyboard)

    @dp.message(Command("help"))
    async def cmd_help(message: types.Message) -> None:
        response = await handle_help()
        await message.answer(response)

    @dp.message(Command("health"))
    async def cmd_health(message: types.Message) -> None:
        response = await handle_health(client)
        await message.answer(response)

    @dp.message(Command("labs"))
    async def cmd_labs(message: types.Message) -> None:
        response = await handle_labs(client)
        await message.answer(response)

    @dp.message(Command("scores"))
    async def cmd_scores(message: types.Message) -> None:
        # Extract lab argument from command
        lab = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
        response = await handle_scores(client, lab)
        await message.answer(response)

    @dp.message(Command("sync"))
    async def cmd_sync(message: types.Message) -> None:
        response = await handle_intent("sync the data", client, llm_client)
        await message.answer(response)

    # Handle plain text messages with LLM intent routing
    @dp.message()
    async def handle_text(message: types.Message) -> None:
        user_text = message.text or ""
        if user_text.strip():
            response = await handle_intent(user_text, client, llm_client)
            await message.answer(response)

    # Start polling with extended timeout for LLM queries
    print("Bot started in Telegram mode. Polling for messages...")
    await dp.start_polling(bot, poll_timeout=60.0)  # Extended polling timeout

    # Cleanup
    await client.close()
    await llm_client.close()
    await bot.session.close()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="LMS Telegram Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run bot.py --test "/start"     # Test /start command
  uv run bot.py --test "/help"      # Test /help command
  uv run bot.py                     # Run in Telegram mode
""",
    )
    parser.add_argument(
        "--test",
        metavar="COMMAND",
        help="Run a command in test mode (no Telegram connection)",
    )

    args = parser.parse_args()

    if args.test:
        # Test mode: call handlers directly
        asyncio.run(run_test_mode(args.test))
    else:
        # Production mode: connect to Telegram
        asyncio.run(run_telegram_mode())


if __name__ == "__main__":
    main()
