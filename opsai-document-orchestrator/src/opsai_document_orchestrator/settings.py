"""Environment-based settings following 12-factor app principles."""

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True, slots=True)
class Settings:
    """Application settings from environment variables."""
    # Azure Storage
    storage_connection_string: str
    storage_container: str

    # Azure Content Understanding
    cu_endpoint: str
    cu_api_key: str
    cu_api_version: str

    # Azure Table Storage
    table_connection_string: str
    table_results: str
    table_feedback: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings from environment variables."""
    return Settings(
        storage_connection_string=os.getenv("AZURE_STORAGE_CONNECTION_STRING", ""),
        storage_container=os.getenv("AZURE_STORAGE_CONTAINER", "documents"),
        cu_endpoint=os.getenv("AZURE_CU_ENDPOINT", ""),
        cu_api_key=os.getenv("AZURE_CU_API_KEY", ""),
        cu_api_version=os.getenv("AZURE_CU_API_VERSION", "2025-05-01-preview"),
        table_connection_string=os.getenv("AZURE_TABLE_CONNECTION_STRING", ""),
        table_results=os.getenv("AZURE_TABLE_RESULTS", "AnalysisResults"),
        table_feedback=os.getenv("AZURE_TABLE_FEEDBACK", "FeedbackRecords"),
    )
