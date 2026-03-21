"""Handler for /scores command."""

from services.api_client import LMSAPIClient, format_api_error


async def handle_scores(client: LMSAPIClient, lab_name: str | None = None) -> str:
    """Handle /scores command - view scores for a lab.

    Args:
        client: The LMS API client.
        lab_name: The lab name to get scores for.
    """
    if not lab_name:
        return "Please specify a lab name, e.g., /scores lab-04"
    
    try:
        pass_rates = await client.get_pass_rates(lab_name)
        
        if not pass_rates:
            return f"📊 No scores found for {lab_name}."
        
        lines = [f"📊 Pass rates for {lab_name}:"]
        for rate in pass_rates:
            task_name = rate.get("task_title", rate.get("task", "Unknown"))
            pass_rate = rate.get("pass_rate", 0)
            attempts = rate.get("attempts", 0)
            lines.append(f"- {task_name}: {pass_rate:.1f}% ({attempts} attempts)")
        
        return "\n".join(lines)
    except Exception as e:
        return format_api_error(e, "Backend")
