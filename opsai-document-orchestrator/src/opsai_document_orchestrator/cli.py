"""CLI for managing document orchestrator."""

import argparse
import sys

from .config import load_config
from .factory import get_analyzer_builder
from .settings import get_settings


def validate_config_cmd() -> int:
    """Validate the pipeline configuration."""
    try:
        config = load_config()
        issues = validate_config(config)
        
        if issues:
            print("Configuration issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return 1
        
        print(f"Configuration valid: {len(config.categories)} categories configured")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def validate_config(config) -> list[str]:
    """Validate pipeline configuration."""
    issues = []
    if not config.azure.endpoint:
        issues.append("Azure endpoint not configured")
    if not config.categories:
        issues.append("No categories configured")
    return issues


def setup_analyzers_cmd() -> int:
    """Create/update analyzers in Content Understanding."""
    try:
        settings = get_settings()
        if not settings.cu_endpoint or not settings.cu_api_key:
            print("Error: AZURE_CU_ENDPOINT and AZURE_CU_API_KEY must be set")
            return 1

        config = load_config()
        builder = get_analyzer_builder()

        print(f"Setting up analyzers for {len(config.categories)} categories...")
        builder.setup_all(config)

        print("Analyzers created/updated:")
        print(f"  Router: {config.azure.router_analyzer_id}")
        for cat in config.categories:
            print(f"  Category '{cat.id}': {cat.analyzer_id}")

        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def list_analyzers_cmd() -> int:
    """List configured analyzers."""
    try:
        config = load_config()
        
        print("Configured Analyzers:")
        print(f"  Router: {config.azure.router_analyzer_id}")
        print("\nCategory Analyzers:")
        for cat in config.categories:
            print(f"  {cat.id}:")
            print(f"    Analyzer ID: {cat.analyzer_id}")
            print(f"    Display Name: {cat.display_name}")
            fields = list(cat.extraction_schema.keys())
            print(f"    Fields: {', '.join(fields[:5])}{'...' if len(fields) > 5 else ''}")
        
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="OpsAI Document Orchestrator CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("validate", help="Validate pipeline configuration")
    subparsers.add_parser("setup-analyzers", help="Create/update CU analyzers")
    subparsers.add_parser("list-analyzers", help="List configured analyzers")

    args = parser.parse_args()

    match args.command:
        case "validate":
            return validate_config_cmd()
        case "setup-analyzers":
            return setup_analyzers_cmd()
        case "list-analyzers":
            return list_analyzers_cmd()
        case _:
            parser.print_help()
            return 0


if __name__ == "__main__":
    sys.exit(main())
