"""Tests for configuration loading."""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.opsai_document_orchestrator.config import (
    load_config,
    _parse_config,
    ConfigError,
)
from src.opsai_document_orchestrator.models import PipelineConfig


SAMPLE_CONFIG = {
    "azure": {
        "endpoint": "https://test.cognitiveservices.azure.com",
        "api_version": "2025-05-01-preview",
        "router_analyzer_id": "test-router",
    },
    "categories": [
        {
            "id": "test_category",
            "display_name": "Test Category",
            "analyzer_id": "test-analyzer",
            "classification_prompt": "Test documents for testing.",
            "extraction_schema": {
                "field1": {"type": "string", "description": "A test field"},
                "field2": {"type": "number"},
            },
        }
    ],
}


def test_parse_config_creates_pipeline_config():
    """Test that _parse_config creates valid PipelineConfig."""
    config = _parse_config(SAMPLE_CONFIG)

    assert isinstance(config, PipelineConfig)
    assert config.azure.endpoint == "https://test.cognitiveservices.azure.com"
    assert config.azure.api_version == "2025-05-01-preview"
    assert config.azure.router_analyzer_id == "test-router"


def test_parse_config_creates_categories():
    """Test that categories are parsed correctly."""
    config = _parse_config(SAMPLE_CONFIG)

    assert len(config.categories) == 1
    category = config.categories[0]
    assert category.id == "test_category"
    assert category.display_name == "Test Category"
    assert category.analyzer_id == "test-analyzer"
    assert "Test documents" in category.classification_prompt


def test_parse_config_extracts_schema():
    """Test that extraction schema is preserved."""
    config = _parse_config(SAMPLE_CONFIG)
    schema = config.categories[0].extraction_schema

    assert "field1" in schema
    assert schema["field1"]["type"] == "string"
    assert schema["field1"]["description"] == "A test field"
    assert schema["field2"]["type"] == "number"


def test_get_category_by_id():
    """Test finding category by ID."""
    config = _parse_config(SAMPLE_CONFIG)

    found = config.get_category("test_category")
    assert found is not None
    assert found.id == "test_category"

    not_found = config.get_category("nonexistent")
    assert not_found is None


def test_get_category_by_analyzer():
    """Test finding category by analyzer ID."""
    config = _parse_config(SAMPLE_CONFIG)

    found = config.get_category_by_analyzer("test-analyzer")
    assert found is not None
    assert found.analyzer_id == "test-analyzer"


def test_parse_config_handles_empty_categories():
    """Test handling of empty categories list."""
    config_data = {
        "azure": {
            "endpoint": "https://test.azure.com",
            "router_analyzer_id": "router",
        },
        "categories": [],
    }
    config = _parse_config(config_data)
    assert config.categories == []


def test_parse_config_uses_defaults():
    """Test that defaults are used for missing optional fields."""
    config_data = {
        "azure": {
            "endpoint": "https://test.azure.com",
            "router_analyzer_id": "router",
        },
    }
    config = _parse_config(config_data)
    assert config.azure.api_version == "2025-05-01-preview"
    assert config.categories == []
