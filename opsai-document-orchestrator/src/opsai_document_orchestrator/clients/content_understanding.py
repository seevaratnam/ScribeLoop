"""Azure AI Content Understanding client."""

import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ContentUnderstandingError(Exception):
    """Content Understanding API error."""
    pass


class ContentUnderstandingClient:
    """Client for Azure AI Content Understanding API."""

    def __init__(self, endpoint: str, api_key: str, api_version: str = "2025-05-01-preview"):
        self._endpoint = endpoint.rstrip("/")
        self._api_key = api_key
        self._api_version = api_version
        self._client = httpx.Client(timeout=120.0)

    def _headers(self) -> dict[str, str]:
        return {
            "Ocp-Apim-Subscription-Key": self._api_key,
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        return f"{self._endpoint}/contentunderstanding{path}?api-version={self._api_version}"

    def create_analyzer(self, analyzer_id: str, body: dict[str, Any]) -> None:
        """Create or update an analyzer."""
        url = f"{self._endpoint}/contentunderstanding/analyzers/{analyzer_id}?api-version={self._api_version}"
        response = self._client.put(url, headers=self._headers(), json=body)
        if response.status_code not in (200, 201):
            raise ContentUnderstandingError(f"Failed to create analyzer: {response.text}")
        logger.info(f"Created/updated analyzer: {analyzer_id}")

    def get_analyzer(self, analyzer_id: str) -> dict[str, Any] | None:
        """Get analyzer by ID."""
        url = f"{self._endpoint}/contentunderstanding/analyzers/{analyzer_id}?api-version={self._api_version}"
        response = self._client.get(url, headers=self._headers())
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise ContentUnderstandingError(f"Failed to get analyzer: {response.text}")
        return response.json()

    def delete_analyzer(self, analyzer_id: str) -> None:
        """Delete an analyzer."""
        url = f"{self._endpoint}/contentunderstanding/analyzers/{analyzer_id}?api-version={self._api_version}"
        response = self._client.delete(url, headers=self._headers())
        if response.status_code not in (200, 204, 404):
            raise ContentUnderstandingError(f"Failed to delete analyzer: {response.text}")
        logger.info(f"Deleted analyzer: {analyzer_id}")

    def analyze(self, analyzer_id: str, document_url: str, poll_interval: float = 2.0) -> dict[str, Any]:
        """
        Submit document for analysis and poll until complete.
        
        Returns the analysis result with classification and extracted fields.
        """
        # Submit analysis request
        url = f"{self._endpoint}/contentunderstanding/analyzers/{analyzer_id}:analyze?api-version={self._api_version}"
        body = {"url": document_url}
        
        response = self._client.post(url, headers=self._headers(), json=body)
        if response.status_code not in (200, 202):
            raise ContentUnderstandingError(f"Failed to start analysis: {response.text}")

        # If synchronous response, return directly
        if response.status_code == 200:
            return response.json()

        # Poll for async result
        operation_url = response.headers.get("Operation-Location")
        if not operation_url:
            raise ContentUnderstandingError("No operation location in response")

        logger.info(f"Polling analysis operation: {operation_url}")
        while True:
            time.sleep(poll_interval)
            result_response = self._client.get(operation_url, headers=self._headers())
            if result_response.status_code != 200:
                raise ContentUnderstandingError(f"Failed to get operation status: {result_response.text}")

            result = result_response.json()
            status = result.get("status", "").lower()

            match status:
                case "succeeded":
                    logger.info("Analysis completed successfully")
                    return result.get("result", result)
                case "failed":
                    error = result.get("error", {}).get("message", "Unknown error")
                    raise ContentUnderstandingError(f"Analysis failed: {error}")
                case "running" | "notstarted":
                    continue
                case _:
                    raise ContentUnderstandingError(f"Unknown status: {status}")

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()
