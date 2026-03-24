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

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

# Add bot directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import load_config
from handlers import (
    get_inline_keyboard,
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
    """Run the bot in production mode, connecting to Telegram."""
    config = load_config()
    api_client = LMSAPIClient(config.lms_api_base_url, config.lms_api_key)
    llm_client = LLMClient(
        config.llm_api_base_url,
        config.llm_api_key,
        config.llm_api_model,
    )

    bot = Bot(token=config.bot_token)
    dp = Dispatcher()

    callback_queries = {
        "query:list_labs": "/labs",
        "query:health": "/health",
        "query:scores": "show me scores for lab 4",
        "query:top_learners": "who are the top 5 students in lab 4",
        "query:pass_rates": "which lab has the lowest pass rate?",
        "query:groups": "which group is doing best in lab 3?",
        "query:sync": "refresh the data",
        "query:help": "/help",
    }

    async def resolve_message(text: str) -> tuple[str, bool]:
        cmd_name, arg = parse_command(text)

        if cmd_name == "/start":
            return await handle_start(), True
        if cmd_name == "/help":
            return await handle_help(), True
        if cmd_name == "/health":
            return await handle_health(api_client), False
        if cmd_name == "/labs":
            return await handle_labs(api_client), False
        if cmd_name == "/scores":
            return await handle_scores(api_client, arg), False

        return await handle_intent(text, api_client, llm_client), False

    @dp.message(Command("start"))
    async def on_start(message: Message) -> None:
        text, _ = await resolve_message("/start")
        await message.answer(text, reply_markup=get_inline_keyboard())

    @dp.message(Command("help"))
    async def on_help(message: Message) -> None:
        text, _ = await resolve_message("/help")
        await message.answer(text, reply_markup=get_inline_keyboard())

    @dp.message(Command("health"))
    async def on_health(message: Message) -> None:
        text, _ = await resolve_message("/health")
        await message.answer(text)

    @dp.message(Command("labs"))
    async def on_labs(message: Message) -> None:
        text, _ = await resolve_message("/labs")
        await message.answer(text)

    @dp.message(Command("scores"))
    async def on_scores(message: Message) -> None:
        text, _ = await resolve_message(message.text or "/scores")
        await message.answer(text)

    @dp.callback_query(F.data.startswith("query:"))
    async def on_callback(callback: CallbackQuery) -> None:
        query_text = callback_queries.get(callback.data or "", "/help")
        text, show_keyboard = await resolve_message(query_text)
        await callback.answer()
        if callback.message:
            if show_keyboard:
                await callback.message.answer(text, reply_markup=get_inline_keyboard())
            else:
                await callback.message.answer(text)

    @dp.message()
    async def on_text(message: Message) -> None:
        text, show_keyboard = await resolve_message(message.text or "")
        if show_keyboard:
            await message.answer(text, reply_markup=get_inline_keyboard())
        else:
            await message.answer(text)

    try:
        await dp.start_polling(bot)
    finally:
        await api_client.close()
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
