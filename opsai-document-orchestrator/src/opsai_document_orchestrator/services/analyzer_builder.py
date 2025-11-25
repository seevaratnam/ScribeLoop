"""Builder for Azure Content Understanding analyzers."""

import logging
from typing import Any

from ..clients import ContentUnderstandingClient
from ..models import Category, PipelineConfig

logger = logging.getLogger(__name__)


class AnalyzerBuilder:
    """Builds and manages Content Understanding analyzers from configuration."""

    def __init__(self, client: ContentUnderstandingClient):
        self._client = client

    def build_category_analyzer(self, category: Category) -> dict[str, Any]:
        """Build analyzer definition for a category."""
        return {
            "description": f"Extractor for {category.display_name}",
            "baseAnalyzerId": "prebuilt-document",
            "fieldSchema": self._convert_schema(category.extraction_schema),
        }

    def build_router_analyzer(self, config: PipelineConfig) -> dict[str, Any]:
        """Build router analyzer definition with content categories."""
        content_categories = [
            {
                "id": cat.id,
                "description": cat.classification_prompt,
                "analyzerId": cat.analyzer_id,
            }
            for cat in config.categories
        ]

        return {
            "description": "Document classification router",
            "baseAnalyzerId": "prebuilt-document",
            "config": {
                "contentCategories": content_categories,
                "enableSegment": False,
            },
        }

    def setup_all(self, config: PipelineConfig) -> None:
        """Create/update all analyzers from configuration."""
        # Create per-category analyzers
        for category in config.categories:
            body = self.build_category_analyzer(category)
            self._client.create_analyzer(category.analyzer_id, body)
            logger.info(f"Setup analyzer: {category.analyzer_id}")

        # Create router analyzer
        router_body = self.build_router_analyzer(config)
        self._client.create_analyzer(config.azure.router_analyzer_id, router_body)
        logger.info(f"Setup router: {config.azure.router_analyzer_id}")

    def _convert_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        """
        Convert extraction schema to Content Understanding fieldSchema format.
        
        Input format (from YAML):
        {
            "fieldName": {
                "type": "string|number|object|array",
                "description": "...",
                "properties": {...},  # for objects
                "items": {...}        # for arrays
            }
        }
        
        Output format (CU fieldSchema):
        {
            "fieldName": {
                "type": "string|number|object|array",
                "description": "...",
                "properties": {...},  # for objects
                "items": {...}        # for arrays
            }
        }
        """
        result = {}
        for name, field in schema.items():
            result[name] = self._convert_field(field)
        return result

    def _convert_field(self, field: dict[str, Any]) -> dict[str, Any]:
        """Convert a single field definition."""
        converted: dict[str, Any] = {"type": field.get("type", "string")}

        if description := field.get("description"):
            converted["description"] = description

        # Handle nested object properties
        if field.get("type") == "object" and "properties" in field:
            converted["properties"] = {
                k: self._convert_field(v) for k, v in field["properties"].items()
            }

        # Handle array items
        if field.get("type") == "array" and "items" in field:
            converted["items"] = self._convert_field(field["items"])

        return converted
