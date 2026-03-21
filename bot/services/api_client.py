"""LMS API client service.

This module handles all HTTP requests to the LMS backend API.
It uses Bearer token authentication and provides user-friendly error messages.
"""

import httpx
from typing import Any


class LMSAPIClient:
    """Client for the LMS backend API."""

    def __init__(self, base_url: str, api_key: str):
        """Initialize the API client.
        
        Args:
            base_url: The base URL of the LMS API (e.g., http://localhost:42002).
            api_key: The API key for authentication.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=10.0,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def _request(self, method: str, endpoint: str, **kwargs: Any) -> httpx.Response:
        """Make an HTTP request with error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint (e.g., "/items/").
            **kwargs: Additional arguments passed to httpx.
            
        Returns:
            The HTTP response.
            
        Raises:
            httpx.RequestError: On connection or request errors.
            httpx.HTTPStatusError: On HTTP error status codes.
        """
        return await self._client.request(method, endpoint, **kwargs)

    async def get_items(self) -> list[dict[str, Any]]:
        """Fetch all items (labs and tasks) from the API.
        
        Returns:
            List of items.
        """
        response = await self._request("GET", "/items/")
        response.raise_for_status()
        return response.json()

    async def get_pass_rates(self, lab: str) -> list[dict[str, Any]]:
        """Fetch pass rates for a specific lab.
        
        Args:
            lab: The lab identifier (e.g., "lab-04").
            
        Returns:
            List of pass rate data.
        """
        response = await self._request("GET", "/analytics/pass-rates", params={"lab": lab})
        response.raise_for_status()
        return response.json()

    async def check_health(self) -> dict[str, Any]:
        """Check if the backend is healthy.

        Returns:
            Health status dictionary with 'status' and 'item_count' keys.
        """
        items = await self.get_items()
        return {"status": "healthy", "item_count": len(items)}

    async def get_learners(self) -> list[dict[str, Any]]:
        """Fetch all enrolled learners.

        Returns:
            List of learners.
        """
        response = await self._request("GET", "/learners/")
        response.raise_for_status()
        return response.json()

    async def get_scores(self, lab: str) -> list[dict[str, Any]]:
        """Fetch score distribution for a lab.

        Args:
            lab: The lab identifier.

        Returns:
            List of score distribution data.
        """
        response = await self._request("GET", "/analytics/scores", params={"lab": lab})
        response.raise_for_status()
        return response.json()

    async def get_timeline(self, lab: str) -> list[dict[str, Any]]:
        """Fetch timeline data for a lab.

        Args:
            lab: The lab identifier.

        Returns:
            List of timeline data.
        """
        response = await self._request("GET", "/analytics/timeline", params={"lab": lab})
        response.raise_for_status()
        return response.json()

    async def get_groups(self, lab: str) -> list[dict[str, Any]]:
        """Fetch per-group data for a lab.

        Args:
            lab: The lab identifier.

        Returns:
            List of group data.
        """
        response = await self._request("GET", "/analytics/groups", params={"lab": lab})
        response.raise_for_status()
        return response.json()

    async def get_top_learners(
        self,
        lab: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Fetch top learners for a lab.

        Args:
            lab: The lab identifier.
            limit: Number of top learners to return.

        Returns:
            List of top learner data.
        """
        response = await self._request(
            "GET",
            "/analytics/top-learners",
            params={"lab": lab, "limit": limit},
        )
        response.raise_for_status()
        return response.json()

    async def get_completion_rate(self, lab: str) -> dict[str, Any]:
        """Fetch completion rate for a lab.

        Args:
            lab: The lab identifier.

        Returns:
            Completion rate data.
        """
        response = await self._request("GET", "/analytics/completion-rate", params={"lab": lab})
        response.raise_for_status()
        return response.json()

    async def trigger_sync(self) -> dict[str, Any]:
        """Trigger ETL sync.

        Returns:
            Sync result data.
        """
        response = await self._request("POST", "/pipeline/sync", json={})
        response.raise_for_status()
        return response.json()


def format_api_error(error: Exception, context: str = "Backend") -> str:
    """Format an API error into a user-friendly message.
    
    This function converts raw exceptions into messages that:
    - Include the actual error (for debugging)
    - Don't show raw tracebacks
    - Aren't vague ("something went wrong")
    
    Args:
        error: The exception that was raised.
        context: The context of the error (e.g., "Backend", "API").
        
    Returns:
        A user-friendly error message string.
    """
    if isinstance(error, httpx.HTTPStatusError):
        return f"{context} error: HTTP {error.response.status_code} {error.response.reason_phrase}. The backend service may be down."
    elif isinstance(error, httpx.ConnectError):
        # Extract the core error message
        error_msg = str(error)
        if "Connection refused" in error_msg:
            return f"{context} error: connection refused. Check that the services are running."
        elif "ConnectError" in error_msg:
            # Try to get the underlying error
            return f"{context} error: {error_msg.split(':')[-1].strip()}"
        return f"{context} error: {error_msg}"
    elif isinstance(error, httpx.TimeoutException):
        return f"{context} error: request timed out. The service may be overloaded."
    elif isinstance(error, httpx.RequestError):
        return f"{context} error: {error.args[0] if error.args else 'unknown request error'}."
    else:
        return f"{context} error: {str(error)}"
