"""Document processing service - core business logic."""

import logging
import uuid
from datetime import datetime
from typing import Any

from ..clients import BlobStorageClient, ContentUnderstandingClient
from ..config import load_config
from ..models import AnalysisResult, FeedbackRecord, PipelineConfig
from ..repositories import DocumentRepository, FeedbackRepository

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Orchestrates document upload, analysis, and feedback operations.
    
    Single responsibility: coordinate between storage, analysis, and persistence.
    """

    def __init__(
        self,
        blob_client: BlobStorageClient,
        cu_client: ContentUnderstandingClient,
        doc_repo: DocumentRepository,
        feedback_repo: FeedbackRepository,
        config: PipelineConfig | None = None,
    ):
        self._blob = blob_client
        self._cu = cu_client
        self._docs = doc_repo
        self._feedback = feedback_repo
        self._config = config or load_config()

    def upload_document(
        self, filename: str, content: bytes, content_type: str
    ) -> tuple[str, str]:
        """
        Upload document to blob storage.
        
        Returns: (document_id, blob_url)
        """
        document_id = str(uuid.uuid4())
        blob_name = f"{document_id}/{filename}"
        
        blob_url = self._blob.upload(blob_name, content, content_type)
        logger.info(f"Uploaded document: {document_id}")
        
        return document_id, blob_url

    def analyze_document(self, document_id: str, blob_url: str) -> AnalysisResult:
        """
        Analyze document using Content Understanding router.
        
        1. Generate SAS URL for CU access
        2. Call router analyzer
        3. Parse and store results
        """
        # Extract blob name from URL for SAS generation
        blob_name = self._extract_blob_name(blob_url)
        sas_url = self._blob.get_sas_url(blob_name)

        # Call Content Understanding
        raw_result = self._cu.analyze(
            self._config.azure.router_analyzer_id, sas_url
        )

        # Parse response
        category_id, fields, confidence = self._parse_cu_response(raw_result)

        # Create and save result
        result = AnalysisResult(
            document_id=document_id,
            category_id=category_id,
            extracted_fields=fields,
            confidence=confidence,
            analyzed_at=datetime.utcnow(),
        )
        self._docs.save(result)

        logger.info(f"Analyzed document {document_id}: category={category_id}")
        return result

    def get_result(self, document_id: str) -> AnalysisResult | None:
        """Get analysis result for document."""
        return self._docs.get(document_id)

    def submit_feedback(
        self,
        document_id: str,
        corrected_fields: dict[str, Any],
        reviewer: str | None = None,
        comment: str | None = None,
    ) -> FeedbackRecord:
        """
        Submit feedback for a document analysis.
        
        Stores corrections for future model improvements.
        """
        feedback_id = str(uuid.uuid4())
        feedback = FeedbackRecord(
            feedback_id=feedback_id,
            document_id=document_id,
            corrected_fields=corrected_fields,
            reviewer=reviewer,
            comment=comment,
            created_at=datetime.utcnow(),
        )
        self._feedback.save(feedback)

        logger.info(f"Recorded feedback {feedback_id} for document {document_id}")
        return feedback

    def get_feedback(self, document_id: str) -> list[FeedbackRecord]:
        """Get all feedback for a document."""
        return self._feedback.get_by_document(document_id)

    def _extract_blob_name(self, blob_url: str) -> str:
        """Extract blob name from full URL."""
        # URL format: https://account.blob.core.windows.net/container/blob_name
        parts = blob_url.split("/")
        # Find container index and return everything after
        for i, part in enumerate(parts):
            if ".blob.core.windows.net" in part:
                return "/".join(parts[i + 2:])  # Skip container name
        return blob_url  # Fallback

    def _parse_cu_response(
        self, response: dict[str, Any]
    ) -> tuple[str | None, dict[str, Any], float | None]:
        """
        Parse Content Understanding response.
        
        Returns: (category_id, extracted_fields, confidence)
        """
        # Extract category from classification result
        category_id = None
        confidence = None
        
        # Handle classification from router
        if contents := response.get("contents"):
            for content in contents:
                if category := content.get("category"):
                    category_id = category.get("id")
                    confidence = category.get("confidence")
                    break

        # Extract fields
        fields: dict[str, Any] = {}
        if field_results := response.get("fields"):
            fields = self._flatten_fields(field_results)

        return category_id, fields, confidence

    def _flatten_fields(self, field_results: dict[str, Any]) -> dict[str, Any]:
        """Flatten CU field results to simple key-value pairs."""
        result = {}
        for name, field in field_results.items():
            if isinstance(field, dict):
                if "value" in field:
                    result[name] = field["value"]
                elif "values" in field:
                    # Array field
                    result[name] = [
                        self._flatten_fields(item) if isinstance(item, dict) else item
                        for item in field["values"]
                    ]
                else:
                    # Nested object
                    result[name] = self._flatten_fields(field)
            else:
                result[name] = field
        return result
