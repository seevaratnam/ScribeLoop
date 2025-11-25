"""Tests for DocumentService."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.opsai_document_orchestrator.models import (
    AnalysisResult,
    FeedbackRecord,
    AzureSettings,
    Category,
    PipelineConfig,
)
from src.opsai_document_orchestrator.services.document_service import DocumentService


@pytest.fixture
def mock_blob_client():
    """Create mock blob client."""
    client = MagicMock()
    client.upload.return_value = "https://storage.blob.core.windows.net/docs/test.pdf"
    client.get_sas_url.return_value = "https://storage.blob.core.windows.net/docs/test.pdf?sas=token"
    return client


@pytest.fixture
def mock_cu_client():
    """Create mock Content Understanding client."""
    client = MagicMock()
    client.analyze.return_value = {
        "contents": [{"category": {"id": "health_claim", "confidence": 0.95}}],
        "fields": {
            "docType": {"value": "HealthClaim"},
            "totalClaimed": {"value": 1500.00},
        },
    }
    return client


@pytest.fixture
def mock_doc_repo():
    """Create mock document repository."""
    repo = MagicMock()
    repo.get.return_value = None
    return repo


@pytest.fixture
def mock_feedback_repo():
    """Create mock feedback repository."""
    return MagicMock()


@pytest.fixture
def config():
    """Create test configuration."""
    return PipelineConfig(
        azure=AzureSettings(
            endpoint="https://test.azure.com",
            api_version="2025-05-01-preview",
            router_analyzer_id="router",
        ),
        categories=[
            Category(
                id="health_claim",
                display_name="Health Claim",
                analyzer_id="health-extractor",
                classification_prompt="Health claims",
                extraction_schema={},
            )
        ],
    )


@pytest.fixture
def service(mock_blob_client, mock_cu_client, mock_doc_repo, mock_feedback_repo, config):
    """Create DocumentService with mocked dependencies."""
    return DocumentService(
        blob_client=mock_blob_client,
        cu_client=mock_cu_client,
        doc_repo=mock_doc_repo,
        feedback_repo=mock_feedback_repo,
        config=config,
    )


class TestUploadDocument:
    """Tests for upload_document method."""

    def test_upload_returns_document_id_and_url(self, service, mock_blob_client):
        """Test that upload returns document ID and blob URL."""
        doc_id, blob_url = service.upload_document(
            filename="test.pdf",
            content=b"PDF content",
            content_type="application/pdf",
        )

        assert doc_id is not None
        assert len(doc_id) == 36  # UUID format
        assert blob_url.startswith("https://")
        mock_blob_client.upload.assert_called_once()

    def test_upload_uses_correct_blob_name(self, service, mock_blob_client):
        """Test that blob name includes document ID and filename."""
        doc_id, _ = service.upload_document(
            filename="invoice.pdf",
            content=b"content",
            content_type="application/pdf",
        )

        call_args = mock_blob_client.upload.call_args
        blob_name = call_args[0][0]
        assert doc_id in blob_name
        assert "invoice.pdf" in blob_name


class TestAnalyzeDocument:
    """Tests for analyze_document method."""

    def test_analyze_returns_result(self, service, mock_cu_client, mock_doc_repo):
        """Test that analyze returns AnalysisResult."""
        result = service.analyze_document(
            document_id="test-123",
            blob_url="https://storage.blob.core.windows.net/docs/test-123/file.pdf",
        )

        assert isinstance(result, AnalysisResult)
        assert result.document_id == "test-123"
        assert result.category_id == "health_claim"
        assert result.confidence == 0.95

    def test_analyze_saves_result(self, service, mock_doc_repo):
        """Test that analysis result is saved to repository."""
        service.analyze_document(
            document_id="test-123",
            blob_url="https://storage.blob.core.windows.net/docs/test-123/file.pdf",
        )

        mock_doc_repo.save.assert_called_once()
        saved_result = mock_doc_repo.save.call_args[0][0]
        assert saved_result.document_id == "test-123"

    def test_analyze_extracts_fields(self, service):
        """Test that fields are extracted from CU response."""
        result = service.analyze_document(
            document_id="test-123",
            blob_url="https://storage.blob.core.windows.net/docs/test-123/file.pdf",
        )

        assert result.extracted_fields["docType"] == "HealthClaim"
        assert result.extracted_fields["totalClaimed"] == 1500.00


class TestSubmitFeedback:
    """Tests for submit_feedback method."""

    def test_feedback_creates_record(self, service, mock_feedback_repo):
        """Test that feedback creates a record."""
        feedback = service.submit_feedback(
            document_id="test-123",
            corrected_fields={"totalClaimed": 1600.00},
            reviewer="test_user",
            comment="Corrected amount",
        )

        assert isinstance(feedback, FeedbackRecord)
        assert feedback.document_id == "test-123"
        assert feedback.corrected_fields["totalClaimed"] == 1600.00
        assert feedback.reviewer == "test_user"

    def test_feedback_is_saved(self, service, mock_feedback_repo):
        """Test that feedback is saved to repository."""
        service.submit_feedback(
            document_id="test-123",
            corrected_fields={"field": "value"},
        )

        mock_feedback_repo.save.assert_called_once()


class TestGetResult:
    """Tests for get_result method."""

    def test_get_returns_stored_result(self, service, mock_doc_repo):
        """Test retrieving stored result."""
        stored_result = AnalysisResult(
            document_id="test-123",
            category_id="health_claim",
            extracted_fields={"field": "value"},
        )
        mock_doc_repo.get.return_value = stored_result

        result = service.get_result("test-123")

        assert result == stored_result
        mock_doc_repo.get.assert_called_once_with("test-123")

    def test_get_returns_none_for_missing(self, service, mock_doc_repo):
        """Test that None is returned for missing document."""
        mock_doc_repo.get.return_value = None

        result = service.get_result("nonexistent")

        assert result is None
