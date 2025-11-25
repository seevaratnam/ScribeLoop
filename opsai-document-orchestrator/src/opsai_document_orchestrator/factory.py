"""Dependency factory for service instantiation."""

from functools import lru_cache

from .clients import BlobStorageClient, ContentUnderstandingClient
from .config import load_config
from .repositories import DocumentRepository, FeedbackRepository
from .services import DocumentService, AnalyzerBuilder
from .settings import get_settings


@lru_cache(maxsize=1)
def get_blob_client() -> BlobStorageClient:
    """Get cached blob storage client."""
    settings = get_settings()
    return BlobStorageClient(settings.storage_connection_string, settings.storage_container)


@lru_cache(maxsize=1)
def get_cu_client() -> ContentUnderstandingClient:
    """Get cached Content Understanding client."""
    settings = get_settings()
    return ContentUnderstandingClient(
        settings.cu_endpoint, settings.cu_api_key, settings.cu_api_version
    )


@lru_cache(maxsize=1)
def get_doc_repository() -> DocumentRepository:
    """Get cached document repository."""
    settings = get_settings()
    return DocumentRepository(settings.table_connection_string, settings.table_results)


@lru_cache(maxsize=1)
def get_feedback_repository() -> FeedbackRepository:
    """Get cached feedback repository."""
    settings = get_settings()
    return FeedbackRepository(settings.table_connection_string, settings.table_feedback)


def get_document_service() -> DocumentService:
    """Get document service with all dependencies."""
    return DocumentService(
        blob_client=get_blob_client(),
        cu_client=get_cu_client(),
        doc_repo=get_doc_repository(),
        feedback_repo=get_feedback_repository(),
        config=load_config(),
    )


def get_analyzer_builder() -> AnalyzerBuilder:
    """Get analyzer builder."""
    return AnalyzerBuilder(get_cu_client())
