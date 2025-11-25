# OpsAI Document Orchestrator

Production-ready Azure Functions app for document classification and extraction using Azure AI Content Understanding.

## Features

- **Document Upload**: Upload PDFs, images, and other documents to Azure Blob Storage
- **Classification**: Automatically classify documents using configurable categories
- **Extraction**: Extract structured data based on per-category schemas
- **Feedback**: Capture corrections for continuous learning
- **Config-Driven**: YAML-based configuration for categories and schemas

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Azure Functions (HTTP)                       │
├─────────────────────────────────────────────────────────────────┤
│  /documents/upload    → Upload to Blob Storage                   │
│  /documents/{id}/analyze → Classify & Extract via CU            │
│  /documents/{id}/result  → Get analysis results                 │
│  /documents/{id}/feedback → Submit corrections                  │
│  /config              → Get/Update pipeline configuration       │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────┐    ┌──────────────────┐    ┌─────────────┐
│ Blob Storage│    │ Content          │    │ Table       │
│ (Documents) │    │ Understanding    │    │ Storage     │
└─────────────┘    └──────────────────┘    └─────────────┘
```

## Project Structure

```
opsai-document-orchestrator/
├── function_app.py          # Azure Functions entry point
├── host.json                # Functions host configuration
├── requirements.txt         # Python dependencies
├── config/
│   └── pipeline.yaml        # Pipeline configuration
├── src/opsai_document_orchestrator/
│   ├── models/              # Domain models (dataclasses)
│   ├── clients/             # External service clients
│   ├── repositories/        # Data access layer
│   ├── services/            # Business logic
│   ├── config.py            # Configuration loading
│   ├── settings.py          # Environment settings
│   └── factory.py           # Dependency injection
└── tests/                   # Unit tests
```

## Setup

### Prerequisites

- Python 3.10+
- Azure subscription with:
  - Storage Account (Blob + Table)
  - Content Understanding resource
- Azure Functions Core Tools (for local development)

### Installation

```bash
# Clone the repository
cd opsai-document-orchestrator

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. Copy the example settings file:
```bash
cp local.settings.json.example local.settings.json
```

2. Update `local.settings.json` with your Azure credentials:
```json
{
  "Values": {
    "AZURE_STORAGE_CONNECTION_STRING": "<your-connection-string>",
    "AZURE_CU_ENDPOINT": "https://<resource>.cognitiveservices.azure.com",
    "AZURE_CU_API_KEY": "<your-api-key>",
    "AZURE_TABLE_CONNECTION_STRING": "<your-connection-string>"
  }
}
```

3. Configure document categories in `config/pipeline.yaml`:
```yaml
azure:
  endpoint: "https://<resource>.cognitiveservices.azure.com"
  router_analyzer_id: "doc-router"

categories:
  - id: "health_claim"
    display_name: "Health Claim"
    analyzer_id: "health-claim-extractor"
    classification_prompt: |
      Health insurance claim forms...
    extraction_schema:
      totalClaimed:
        type: number
        description: "Total claimed amount"
```

### Setup Analyzers

Before processing documents, create the analyzers in Content Understanding:

```bash
# Using the CLI
python -m src.opsai_document_orchestrator.cli setup-analyzers

# Or via HTTP endpoint (after starting the function app)
curl -X POST http://localhost:7071/api/config/setup-analyzers
```

### Running Locally

```bash
func start
```

## API Reference

### Upload Document
```http
POST /api/documents/upload
Content-Type: multipart/form-data

file: <binary>
```

Response:
```json
{
  "document_id": "uuid",
  "blob_url": "https://...",
  "filename": "document.pdf"
}
```

### Analyze Document
```http
POST /api/documents/{document_id}/analyze
Content-Type: application/json

{
  "blob_url": "https://..."
}
```

Response:
```json
{
  "document_id": "uuid",
  "category_id": "health_claim",
  "extracted_fields": {...},
  "confidence": 0.95,
  "analyzed_at": "2024-01-01T00:00:00Z"
}
```

### Get Result
```http
GET /api/documents/{document_id}/result
```

### Submit Feedback
```http
POST /api/documents/{document_id}/feedback
Content-Type: application/json

{
  "corrected_fields": {...},
  "reviewer": "user@example.com",
  "comment": "Fixed amount"
}
```

### Get Configuration
```http
GET /api/config
```

### Update Configuration
```http
PUT /api/config
Content-Type: application/json

{
  "azure": {...},
  "categories": [...]
}
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_config_loading.py -v
```

## Deployment

### Deploy to Azure

```bash
# Login to Azure
az login

# Create Function App (if not exists)
az functionapp create \
  --resource-group <rg-name> \
  --consumption-plan-location <location> \
  --runtime python \
  --runtime-version 3.10 \
  --functions-version 4 \
  --name <app-name> \
  --storage-account <storage-name>

# Deploy
func azure functionapp publish <app-name>

# Configure settings
az functionapp config appsettings set \
  --name <app-name> \
  --resource-group <rg-name> \
  --settings \
    AZURE_STORAGE_CONNECTION_STRING="..." \
    AZURE_CU_ENDPOINT="..." \
    AZURE_CU_API_KEY="..."
```

## Design Principles

This project follows:

- **KISS**: Simple, focused components
- **DRY**: Shared abstractions in repositories and services
- **Clean Architecture**: Clear separation of concerns
  - Models: Pure data structures
  - Repositories: Data access abstraction
  - Services: Business logic
  - Functions: Thin HTTP layer
- **Azure Well-Architected Framework**:
  - **Reliability**: Error handling, retries in clients
  - **Security**: Secrets via environment variables, SAS tokens
  - **Cost Optimization**: Serverless, consumption-based
  - **Operational Excellence**: Structured logging, health checks
  - **Performance**: Connection caching, async where beneficial

## License

MIT
