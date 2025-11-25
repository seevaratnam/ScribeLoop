"""Configuration loading and management."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from .models import AzureSettings, Category, PipelineConfig


class ConfigError(Exception):
    """Configuration loading error."""
    pass


def _get_config_path() -> Path:
    """Get config file path from environment or default."""
    env_path = os.getenv("CONFIG_FILE_PATH", "config/pipeline.yaml")
    path = Path(env_path)
    if not path.is_absolute():
        path = Path(__file__).parent.parent.parent / path
    return path


def _parse_config(data: dict[str, Any]) -> PipelineConfig:
    """Parse raw YAML data into PipelineConfig."""
    azure_data = data.get("azure", {})
    azure = AzureSettings(
        endpoint=azure_data.get("endpoint", ""),
        api_version=azure_data.get("api_version", "2025-05-01-preview"),
        router_analyzer_id=azure_data.get("router_analyzer_id", "doc-router"),
    )

    categories = [
        Category(
            id=cat["id"],
            display_name=cat["display_name"],
            analyzer_id=cat["analyzer_id"],
            classification_prompt=cat.get("classification_prompt", "").strip(),
            extraction_schema=cat.get("extraction_schema", {}),
        )
        for cat in data.get("categories", [])
    ]

    return PipelineConfig(azure=azure, categories=categories)


@lru_cache(maxsize=1)
def load_config() -> PipelineConfig:
    """Load and cache pipeline configuration."""
    path = _get_config_path()
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return _parse_config(data)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML: {e}") from e


def reload_config() -> PipelineConfig:
    """Clear cache and reload configuration."""
    load_config.cache_clear()
    return load_config()


def save_config(config: PipelineConfig) -> None:
    """Save configuration to YAML file."""
    path = _get_config_path()
    data = {
        "azure": {
            "endpoint": config.azure.endpoint,
            "api_version": config.azure.api_version,
            "router_analyzer_id": config.azure.router_analyzer_id,
        },
        "categories": [
            {
                "id": c.id,
                "display_name": c.display_name,
                "analyzer_id": c.analyzer_id,
                "classification_prompt": c.classification_prompt,
                "extraction_schema": c.extraction_schema,
            }
            for c in config.categories
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    load_config.cache_clear()
