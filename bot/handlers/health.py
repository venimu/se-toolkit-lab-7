"""Handler for /health command."""


async def handle_health() -> str:
    """Handle /health command - check backend status.

    Task 2: This will call the LMS backend API.
    For now, returns a placeholder.
    """
    return "✅ Backend status: OK (placeholder - will be implemented in Task 2)"
