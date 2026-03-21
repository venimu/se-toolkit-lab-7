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

from handlers import (
    handle_help,
    handle_health,
    handle_labs,
    handle_scores,
    handle_start,
)


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
    cmd_name, arg = parse_command(command)
    
    # Map commands to handlers
    handlers = {
        "/start": lambda: handle_start(),
        "/help": lambda: handle_help(),
        "/health": lambda: handle_health(),
        "/labs": lambda: handle_labs(),
        "/scores": lambda: handle_scores(arg),
    }
    
    handler = handlers.get(cmd_name)
    if handler is None:
        print(f"Unknown command: {cmd_name}")
        print("Available commands: /start, /help, /health, /labs, /scores")
        sys.exit(1)
    
    result = await handler()
    print(result)


async def run_telegram_mode() -> None:
    """Run the bot in production mode, connecting to Telegram.
    
    Task 2: This will initialize aiogram and start polling for updates.
    For now, this is a placeholder.
    """
    print("Telegram mode not yet implemented - will be added in Task 2")
    print("For now, use --test mode to test handlers:")
    print("  uv run bot.py --test \"/start\"")


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
