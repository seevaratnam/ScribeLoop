"""Tests for extraction schema to CU fieldSchema conversion."""

import pytest

from src.opsai_document_orchestrator.services.analyzer_builder import AnalyzerBuilder
from src.opsai_document_orchestrator.models import Category


class MockCUClient:
    """Mock Content Understanding client for testing."""

    def __init__(self):
        self.created_analyzers = {}

    def create_analyzer(self, analyzer_id: str, body: dict):
        self.created_analyzers[analyzer_id] = body


@pytest.fixture
def builder():
    """Create AnalyzerBuilder with mock client."""
    return AnalyzerBuilder(MockCUClient())


def test_convert_simple_string_field(builder):
    """Test conversion of simple string field."""
    schema = {"name": {"type": "string", "description": "A name field"}}
    result = builder._convert_schema(schema)

    assert result["name"]["type"] == "string"
    assert result["name"]["description"] == "A name field"


def test_convert_number_field(builder):
    """Test conversion of number field."""
    schema = {"amount": {"type": "number", "description": "An amount"}}
    result = builder._convert_schema(schema)

    assert result["amount"]["type"] == "number"


def test_convert_nested_object(builder):
    """Test conversion of nested object field."""
    schema = {
        "address": {
            "type": "object",
            "description": "Address details",
            "properties": {
                "street": {"type": "string"},
                "city": {"type": "string"},
                "zip": {"type": "string"},
            },
        }
    }
    result = builder._convert_schema(schema)

    assert result["address"]["type"] == "object"
    assert "properties" in result["address"]
    assert result["address"]["properties"]["street"]["type"] == "string"
    assert result["address"]["properties"]["city"]["type"] == "string"


def test_convert_array_field(builder):
    """Test conversion of array field."""
    schema = {
        "items": {
            "type": "array",
            "description": "List of items",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "quantity": {"type": "number"},
                },
            },
        }
    }
    result = builder._convert_schema(schema)

    assert result["items"]["type"] == "array"
    assert "items" in result["items"]
    assert result["items"]["items"]["type"] == "object"
    assert "properties" in result["items"]["items"]


def test_convert_complex_nested_schema(builder):
    """Test conversion of deeply nested schema."""
    schema = {
        "claim": {
            "type": "object",
            "properties": {
                "member": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                    },
                },
                "lines": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string"},
                            "amount": {"type": "number"},
                        },
                    },
                },
            },
        }
    }
    result = builder._convert_schema(schema)

    # Verify structure preserved
    claim = result["claim"]
    assert claim["type"] == "object"

    member = claim["properties"]["member"]
    assert member["type"] == "object"
    assert member["properties"]["id"]["type"] == "string"

    lines = claim["properties"]["lines"]
    assert lines["type"] == "array"
    assert lines["items"]["properties"]["code"]["type"] == "string"


def test_build_category_analyzer(builder):
    """Test building analyzer definition for a category."""
    category = Category(
        id="test_cat",
        display_name="Test Category",
        analyzer_id="test-analyzer",
        classification_prompt="Test prompt",
        extraction_schema={
            "field1": {"type": "string"},
            "field2": {"type": "number"},
        },
    )

    result = builder.build_category_analyzer(category)

    assert result["baseAnalyzerId"] == "prebuilt-document"
    assert "Extractor for Test Category" in result["description"]
    assert "fieldSchema" in result
    assert "field1" in result["fieldSchema"]


def test_build_router_analyzer(builder):
    """Test building router analyzer definition."""
    from src.opsai_document_orchestrator.models import AzureSettings, PipelineConfig

    config = PipelineConfig(
        azure=AzureSettings(
            endpoint="https://test.azure.com",
            api_version="2025-05-01-preview",
            router_analyzer_id="router",
        ),
        categories=[
            Category(
                id="cat1",
                display_name="Category 1",
                analyzer_id="analyzer1",
                classification_prompt="Category 1 documents",
                extraction_schema={},
            ),
            Category(
                id="cat2",
                display_name="Category 2",
                analyzer_id="analyzer2",
                classification_prompt="Category 2 documents",
                extraction_schema={},
            ),
        ],
    )

    result = builder.build_router_analyzer(config)

    assert result["baseAnalyzerId"] == "prebuilt-document"
    assert "config" in result

    categories = result["config"]["contentCategories"]
    assert len(categories) == 2
    assert categories[0]["id"] == "cat1"
    assert categories[0]["analyzerId"] == "analyzer1"
    assert categories[1]["id"] == "cat2"
