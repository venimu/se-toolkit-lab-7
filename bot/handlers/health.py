"""Handler for /health command."""

from services.api_client import LMSAPIClient, format_api_error


async def handle_health(client: LMSAPIClient) -> str:
    """Handle /health command - check backend status.

    Args:
        client: The LMS API client.
    """
    try:
        health = await client.check_health()
        return f"✅ Backend is healthy. {health['item_count']} items available."
    except Exception as e:
        return format_api_error(e, "Backend")
