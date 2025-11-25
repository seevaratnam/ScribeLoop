"""Domain models for the document orchestrator."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class AzureSettings:
    """Azure Content Understanding settings."""
    endpoint: str
    api_version: str
    router_analyzer_id: str


@dataclass(slots=True)
class Category:
    """Document category configuration."""
    id: str
    display_name: str
    analyzer_id: str
    classification_prompt: str
    extraction_schema: dict[str, Any]


@dataclass(slots=True)
class PipelineConfig:
    """Complete pipeline configuration."""
    azure: AzureSettings
    categories: list[Category]

    def get_category(self, category_id: str) -> Category | None:
        """Find category by ID."""
        return next((c for c in self.categories if c.id == category_id), None)

    def get_category_by_analyzer(self, analyzer_id: str) -> Category | None:
        """Find category by analyzer ID."""
        return next((c for c in self.categories if c.analyzer_id == analyzer_id), None)


@dataclass(slots=True)
class DocumentRecord:
    """Stored document metadata."""
    document_id: str
    blob_url: str
    filename: str
    content_type: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class AnalysisResult:
    """Document analysis result."""
    document_id: str
    category_id: str | None
    extracted_fields: dict[str, Any]
    confidence: float | None = None
    analyzed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class FeedbackRecord:
    """Feedback for continuous learning."""
    feedback_id: str
    document_id: str
    corrected_fields: dict[str, Any]
    reviewer: str | None = None
    comment: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
