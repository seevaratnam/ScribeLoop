# OpsAI Document Forge (opsai-document-forge)

> An intelligent document processing pipeline powered by Azure Functions and Microsoft Content Understanding

## 🚀 Overview

**OpsAI Document Forge** is a serverless document intelligence platform that leverages Azure Functions to provide seamless document upload, storage, and AI-powered content understanding capabilities. The system orchestrates document workflows from ingestion to intelligent analysis with built-in learning and feedback mechanisms.

## 📋 Features

- **Document Upload API** - RESTful endpoint for secure document uploads
- **Azure Blob Storage Integration** - Automatic document persistence and management
- **Microsoft Content Understanding** - AI-powered document analysis and extraction
- **Learning & Feedback Loop** - Continuous improvement through user feedback
- **Serverless Architecture** - Scalable Azure Functions implementation
- **Real-time Processing** - Asynchronous document processing pipeline

## 🏗️ Architecture

### Text-Based Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        OpsAI Document Forge                         │
│                         Architecture Flow                           │
└─────────────────────────────────────────────────────────────────────┘

[Client Application]
        │
        │ HTTPS
        ▼
┌───────────────────────────────────────────────────────────────────┐
│                    Azure API Management                           │
│                  (Rate Limiting, Auth, CORS)                      │
└───────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│                    Azure Function App                             │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    HTTP Triggers                            │ │
│  ├─────────────────────────────────────────────────────────────┤ │
│  │  • POST   /api/documents/upload                            │ │
│  │  • GET    /api/documents/{id}/status                       │ │
│  │  • POST   /api/documents/{id}/analyze                      │ │
│  │  • POST   /api/feedback/submit                             │ │
│  │  • GET    /api/analytics/insights                          │ │
│  │  • PUT    /api/learning/update-model                       │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                 Background Functions                        │ │
│  ├─────────────────────────────────────────────────────────────┤ │
│  │  • Document Processor (Queue Trigger)                      │ │
│  │  • Content Analyzer (Event Grid Trigger)                   │ │
│  │  • Learning Job (Timer Trigger)                            │ │
│  └─────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
        │                           │                         │
        ▼                           ▼                         ▼
┌──────────────┐          ┌──────────────────┐      ┌──────────────┐
│ Azure Blob   │          │ Azure Service    │      │ Azure Queue  │
│   Storage    │          │      Bus         │      │   Storage    │
│              │          │                  │      │              │
│ • /uploads   │          │ • Processing     │      │ • doc-queue  │
│ • /processed │          │   Events         │      │ • retry-queue│
│ • /archives  │          │ • Notifications  │      │              │
└──────────────┘          └──────────────────┘      └──────────────┘
        │                           │
        ▼                           ▼
┌───────────────────────────────────────────────────────────────────┐
│           Microsoft Content Understanding Service                 │
│                                                                   │
│  • Document Classification                                        │
│  • Entity Extraction                                              │
│  • OCR Processing                                                 │
│  • Form Recognition                                               │
└───────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│                    Data & Analytics Layer                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │  Azure Cosmos DB │  │ Azure Cognitive  │  │ Application    │ │
│  │                  │  │     Search       │  │   Insights     │ │
│  │ • Metadata       │  │                  │  │                │ │
│  │ • Feedback       │  │ • Full-text      │  │ • Telemetry    │ │
│  │ • Results        │  │ • Faceted Search │  │ • Metrics      │ │
│  └──────────────────┘  └──────────────────┘  └────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
```

### Processing Pipeline

```
Document Upload Flow:
═══════════════════

1. Upload Request     ──►  Validation      ──►  Blob Storage
                            │                      │
                            ▼                      ▼
2. Generate SAS URL  ◄──  Store Metadata   ◄──  Queue Message
                            │                      │
                            ▼                      ▼
3. Return Response   ──►  Trigger Analysis ──►  Content Understanding
                                                   │
                                                   ▼
4. Store Results     ◄──  Process Output   ◄──  Extract Insights
                            │                      │
                            ▼                      ▼
5. Update Learning   ──►  Notify Client    ──►  Complete

Feedback Loop:
═════════════

User Feedback ──► Store ──► Aggregate ──► Model Update ──► Improve
     ▲                                                         │
     └─────────────────────────────────────────────────────────┘
```

## 🛠️ Technology Stack

- **Runtime**: Azure Functions v4 (.NET 8 / Node.js 18 / Python 3.11)
- **Storage**: Azure Blob Storage
- **Database**: Azure Cosmos DB
- **Message Queue**: Azure Service Bus / Storage Queues
- **AI/ML**: Microsoft Content Understanding, Azure Cognitive Services
- **Search**: Azure Cognitive Search
- **Monitoring**: Application Insights
- **API Gateway**: Azure API Management

## 📦 Installation

### Prerequisites

- Azure Subscription
- Azure CLI installed
- Azure Functions Core Tools v4
- .NET 8 SDK / Node.js 18+ / Python 3.11+
- Visual Studio Code with Azure Functions extension

### Setup Steps

1. **Clone the repository**
```bash
git clone https://github.com/your-org/opsai-document-forge.git
cd opsai-document-forge
```

2. **Install dependencies**
```bash
# For .NET
dotnet restore

# For Node.js
npm install

# For Python
pip install -r requirements.txt
```

3. **Configure Azure Resources**
```bash
# Login to Azure
az login

# Create resource group
az group create --name rg-opsai-document-forge --location eastus

# Deploy infrastructure (using provided ARM template or Terraform)
az deployment group create \
  --resource-group rg-opsai-document-forge \
  --template-file infrastructure/azuredeploy.json \
  --parameters @infrastructure/parameters.json
```

4. **Configure Application Settings**
```json
{
  "AzureWebJobsStorage": "DefaultEndpointsProtocol=https;AccountName=...",
  "FUNCTIONS_WORKER_RUNTIME": "dotnet",
  "BlobStorageConnectionString": "...",
  "ContentUnderstandingEndpoint": "https://...",
  "ContentUnderstandingApiKey": "...",
  "CosmosDbConnectionString": "...",
  "ServiceBusConnectionString": "..."
}
```

5. **Deploy Function App**
```bash
func azure functionapp publish opsai-document-forge-app
```

## 📡 API Endpoints

### Document Upload
```http
POST /api/documents/upload
Content-Type: multipart/form-data

{
  "file": <binary>,
  "metadata": {
    "name": "document.pdf",
    "type": "invoice",
    "tags": ["finance", "2024"]
  }
}

Response:
{
  "documentId": "doc-12345",
  "uploadUrl": "https://storage.blob.core.windows.net/...",
  "status": "uploaded",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Analyze Document
```http
POST /api/documents/{documentId}/analyze
Content-Type: application/json

{
  "analysisType": "full",
  "extractFields": ["invoice_number", "date", "total"],
  "options": {
    "language": "en",
    "ocr": true
  }
}

Response:
{
  "analysisId": "analysis-67890",
  "status": "processing",
  "estimatedCompletion": "2024-01-15T10:35:00Z"
}
```

### Submit Feedback
```http
POST /api/feedback/submit
Content-Type: application/json

{
  "documentId": "doc-12345",
  "analysisId": "analysis-67890",
  "feedback": {
    "accuracy": 0.95,
    "corrections": {
      "invoice_number": "INV-2024-001"
    },
    "comments": "Date extraction was accurate"
  }
}
```

### Get Analytics Insights
```http
GET /api/analytics/insights?timeframe=30d&type=processing

Response:
{
  "totalDocuments": 1250,
  "averageProcessingTime": 3.5,
  "accuracyScore": 0.92,
  "topDocumentTypes": ["invoice", "contract", "receipt"],
  "feedbackScore": 4.5
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_STORAGE_CONNECTION` | Azure Blob Storage connection string | Yes |
| `CONTENT_UNDERSTANDING_ENDPOINT` | Microsoft Content Understanding API endpoint | Yes |
| `CONTENT_UNDERSTANDING_KEY` | API key for Content Understanding | Yes |
| `COSMOS_DB_CONNECTION` | Cosmos DB connection string | Yes |
| `SERVICE_BUS_CONNECTION` | Service Bus connection string | Yes |
| `APP_INSIGHTS_KEY` | Application Insights instrumentation key | Yes |
| `MAX_FILE_SIZE_MB` | Maximum upload file size in MB | No (default: 50) |
| `PROCESSING_TIMEOUT_SECONDS` | Document processing timeout | No (default: 300) |

### Function App Settings

```json
{
  "extensions": {
    "http": {
      "routePrefix": "api",
      "maxConcurrentRequests": 100
    },
    "queues": {
      "batchSize": 16,
      "maxPollingInterval": "00:00:02"
    }
  },
  "logging": {
    "logLevel": {
      "default": "Information",
      "Function": "Debug"
    }
  }
}
```

## 📊 Monitoring & Logging

- **Application Insights** - Real-time monitoring and diagnostics
- **Azure Monitor** - Infrastructure metrics and alerts
- **Custom Dashboards** - Business metrics and KPIs
- **Log Analytics** - Centralized log management

## 🧪 Testing

```bash
# Run unit tests
dotnet test

# Run integration tests
npm run test:integration

# Run end-to-end tests
python -m pytest tests/e2e
```

## 🚀 Deployment

### CI/CD Pipeline (Azure DevOps/GitHub Actions)

```yaml
name: Deploy OpsAI Document Forge

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup .NET
        uses: actions/setup-dotnet@v1
        with:
          dotnet-version: '8.0.x'
      - name: Build
        run: dotnet build --configuration Release
      - name: Test
        run: dotnet test
      - name: Deploy to Azure
        uses: Azure/functions-action@v1
        with:
          app-name: 'opsai-document-forge-app'
          package: './output'
          publish-profile: ${{ secrets.AZURE_FUNCTIONAPP_PUBLISH_PROFILE }}
```

## 📈 Performance Optimization

- **Blob Storage Tiering** - Automatic archival of processed documents
- **Caching Strategy** - Redis Cache for frequently accessed data
- **Async Processing** - Queue-based document processing
- **Auto-scaling** - Dynamic scaling based on load
- **CDN Integration** - Fast document retrieval globally

## 🔒 Security

- **Azure AD Authentication** - OAuth 2.0 / OpenID Connect
- **API Key Management** - Azure Key Vault integration
- **Data Encryption** - At rest and in transit
- **RBAC** - Role-based access control
- **Network Security** - VNet integration and Private Endpoints
- **Compliance** - GDPR, HIPAA ready

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 🤝 Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📧 Support

- **Documentation**: [https://docs.opsai-document-forge.com](https://docs.opsai-document-forge.com)
- **Issues**: [GitHub Issues](https://github.com/your-org/opsai-document-forge/issues)
- **Email**: support@opsai-document-forge.com

## 🏆 Roadmap

- [ ] Multi-language support (Q1 2025)
- [ ] Advanced ML model customization (Q2 2025)
- [ ] Batch processing optimization (Q2 2025)
- [ ] Mobile SDK (Q3 2025)
- [ ] On-premises deployment option (Q4 2025)

---

**Built with ❤️ by the OpsAI Team**