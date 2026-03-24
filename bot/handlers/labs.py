"""Handler for /labs command."""

from services.api_client import LMSAPIClient, format_api_error


async def handle_labs(client: LMSAPIClient) -> str:
    """Handle /labs command - list available labs.

    Args:
        client: The LMS API client.
    """
    try:
        items = await client.get_items()
        labs = [item for item in items if item.get("type") == "lab"]

        if not labs:
            return "📋 No labs available."

        lab_list = "\n".join(f"- {lab['title']}" for lab in labs)
        return f"📋 Available labs:\n{lab_list}"
    except Exception as e:
        return format_api_error(e, "Backend")
