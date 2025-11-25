"""Azure Table Storage repository implementations."""

import json
import logging
from datetime import datetime
from typing import Any

from azure.data.tables import TableServiceClient, TableClient
from azure.core.exceptions import ResourceNotFoundError

from ..models import AnalysisResult, FeedbackRecord

logger = logging.getLogger(__name__)


class TableRepository:
    """Base repository for Azure Table Storage."""

    def __init__(self, connection_string: str, table_name: str):
        self._table_name = table_name
        service_client = TableServiceClient.from_connection_string(connection_string)
        self._table_client: TableClient = service_client.get_table_client(table_name)
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create table if it doesn't exist."""
        try:
            self._table_client.create_table()
            logger.info(f"Created table: {self._table_name}")
        except Exception:
            pass  # Table exists

    def _get_entity(self, partition_key: str, row_key: str) -> dict[str, Any] | None:
        """Get entity from table."""
        try:
            return self._table_client.get_entity(partition_key, row_key)
        except ResourceNotFoundError:
            return None

    def _upsert_entity(self, entity: dict[str, Any]) -> None:
        """Insert or update entity."""
        self._table_client.upsert_entity(entity)

    def _delete_entity(self, partition_key: str, row_key: str) -> None:
        """Delete entity from table."""
        try:
            self._table_client.delete_entity(partition_key, row_key)
        except ResourceNotFoundError:
            pass

    def _query(self, filter_expr: str | None = None) -> list[dict[str, Any]]:
        """Query entities."""
        if filter_expr:
            return list(self._table_client.query_entities(filter_expr))
        return list(self._table_client.list_entities())


class DocumentRepository(TableRepository):
    """Repository for document analysis results."""

    PARTITION_KEY = "documents"

    def get(self, document_id: str) -> AnalysisResult | None:
        """Get analysis result by document ID."""
        entity = self._get_entity(self.PARTITION_KEY, document_id)
        if not entity:
            return None
        return self._to_model(entity)

    def save(self, result: AnalysisResult) -> None:
        """Save analysis result."""
        entity = self._to_entity(result)
        self._upsert_entity(entity)
        logger.info(f"Saved analysis result: {result.document_id}")

    def delete(self, document_id: str) -> None:
        """Delete analysis result."""
        self._delete_entity(self.PARTITION_KEY, document_id)
        logger.info(f"Deleted analysis result: {document_id}")

    def list_all(self) -> list[AnalysisResult]:
        """List all analysis results."""
        entities = self._query(f"PartitionKey eq '{self.PARTITION_KEY}'")
        return [self._to_model(e) for e in entities]

    def list_by_category(self, category_id: str) -> list[AnalysisResult]:
        """List results by category."""
        entities = self._query(
            f"PartitionKey eq '{self.PARTITION_KEY}' and category_id eq '{category_id}'"
        )
        return [self._to_model(e) for e in entities]

    def _to_entity(self, result: AnalysisResult) -> dict[str, Any]:
        """Convert model to table entity."""
        return {
            "PartitionKey": self.PARTITION_KEY,
            "RowKey": result.document_id,
            "category_id": result.category_id or "",
            "extracted_fields": json.dumps(result.extracted_fields),
            "confidence": result.confidence,
            "analyzed_at": result.analyzed_at.isoformat(),
        }

    def _to_model(self, entity: dict[str, Any]) -> AnalysisResult:
        """Convert table entity to model."""
        analyzed_at = entity.get("analyzed_at")
        if isinstance(analyzed_at, str):
            analyzed_at = datetime.fromisoformat(analyzed_at)
        elif analyzed_at is None:
            analyzed_at = datetime.utcnow()

        return AnalysisResult(
            document_id=entity["RowKey"],
            category_id=entity.get("category_id") or None,
            extracted_fields=json.loads(entity.get("extracted_fields", "{}")),
            confidence=entity.get("confidence"),
            analyzed_at=analyzed_at,
        )


class FeedbackRepository(TableRepository):
    """Repository for feedback records."""

    PARTITION_KEY = "feedback"

    def get(self, feedback_id: str) -> FeedbackRecord | None:
        """Get feedback by ID."""
        entity = self._get_entity(self.PARTITION_KEY, feedback_id)
        if not entity:
            return None
        return self._to_model(entity)

    def get_by_document(self, document_id: str) -> list[FeedbackRecord]:
        """Get all feedback for a document."""
        entities = self._query(
            f"PartitionKey eq '{self.PARTITION_KEY}' and document_id eq '{document_id}'"
        )
        return [self._to_model(e) for e in entities]

    def save(self, feedback: FeedbackRecord) -> None:
        """Save feedback record."""
        entity = self._to_entity(feedback)
        self._upsert_entity(entity)
        logger.info(f"Saved feedback: {feedback.feedback_id}")

    def delete(self, feedback_id: str) -> None:
        """Delete feedback record."""
        self._delete_entity(self.PARTITION_KEY, feedback_id)
        logger.info(f"Deleted feedback: {feedback_id}")

    def list_all(self) -> list[FeedbackRecord]:
        """List all feedback records."""
        entities = self._query(f"PartitionKey eq '{self.PARTITION_KEY}'")
        return [self._to_model(e) for e in entities]

    def _to_entity(self, feedback: FeedbackRecord) -> dict[str, Any]:
        """Convert model to table entity."""
        return {
            "PartitionKey": self.PARTITION_KEY,
            "RowKey": feedback.feedback_id,
            "document_id": feedback.document_id,
            "corrected_fields": json.dumps(feedback.corrected_fields),
            "reviewer": feedback.reviewer or "",
            "comment": feedback.comment or "",
            "created_at": feedback.created_at.isoformat(),
        }

    def _to_model(self, entity: dict[str, Any]) -> FeedbackRecord:
        """Convert table entity to model."""
        created_at = entity.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.utcnow()

        return FeedbackRecord(
            feedback_id=entity["RowKey"],
            document_id=entity.get("document_id", ""),
            corrected_fields=json.loads(entity.get("corrected_fields", "{}")),
            reviewer=entity.get("reviewer") or None,
            comment=entity.get("comment") or None,
            created_at=created_at,
        )
