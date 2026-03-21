"""Handler for /scores command."""


async def handle_scores(lab_name: str | None = None) -> str:
    """Handle /scores command - view scores for a lab.

    Task 2: This will fetch scores from the LMS backend API.
    For now, returns a placeholder.

    Args:
        lab_name: The lab name to get scores for.
    """
    if not lab_name:
        return "Please specify a lab name, e.g., /scores lab-04"

    return f"📊 Scores for {lab_name}: (placeholder - will be implemented in Task 2)"
