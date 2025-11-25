"""Azure Functions HTTP endpoints for document orchestrator."""

import json
import logging

import azure.functions as func

from src.opsai_document_orchestrator.config import load_config, save_config, reload_config
from src.opsai_document_orchestrator.factory import get_document_service, get_analyzer_builder
from src.opsai_document_orchestrator.models import AzureSettings, Category, PipelineConfig

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
logger = logging.getLogger(__name__)


# --- Helper Functions ---

def json_response(data: dict, status: int = 200) -> func.HttpResponse:
    """Create JSON HTTP response."""
    return func.HttpResponse(
        json.dumps(data, default=str),
        status_code=status,
        mimetype="application/json",
    )


def error_response(message: str, status: int = 400) -> func.HttpResponse:
    """Create error HTTP response."""
    return json_response({"error": message}, status)


# --- Document Endpoints ---

@app.route(route="documents/upload", methods=["POST"])
def upload_document(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/documents/upload
    
    Upload a document file. Accepts multipart/form-data with 'file' field.
    Returns: { document_id, blob_url }
    """
    try:
        # Get file from request
        file = req.files.get("file")
        if not file:
            return error_response("No file provided", 400)

        filename = file.filename or "document"
        content = file.read()
        content_type = file.content_type or "application/octet-stream"

        service = get_document_service()
        document_id, blob_url = service.upload_document(filename, content, content_type)

        logger.info(f"Document uploaded: {document_id}")
        return json_response({
            "document_id": document_id,
            "blob_url": blob_url,
            "filename": filename,
        }, 201)

    except Exception as e:
        logger.exception("Upload failed")
        return error_response(str(e), 500)


@app.route(route="documents/{document_id}/analyze", methods=["POST"])
def analyze_document(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/documents/{document_id}/analyze
    
    Analyze an uploaded document. Requires blob_url in request body.
    Returns: { document_id, category_id, extracted_fields }
    """
    try:
        document_id = req.route_params.get("document_id")
        if not document_id:
            return error_response("Document ID required", 400)

        body = req.get_json()
        blob_url = body.get("blob_url")
        if not blob_url:
            return error_response("blob_url required in request body", 400)

        service = get_document_service()
        result = service.analyze_document(document_id, blob_url)

        logger.info(f"Document analyzed: {document_id}")
        return json_response({
            "document_id": result.document_id,
            "category_id": result.category_id,
            "extracted_fields": result.extracted_fields,
            "confidence": result.confidence,
            "analyzed_at": result.analyzed_at.isoformat(),
        })

    except Exception as e:
        logger.exception("Analysis failed")
        return error_response(str(e), 500)


@app.route(route="documents/{document_id}/result", methods=["GET"])
def get_result(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/documents/{document_id}/result
    
    Get analysis result for a document.
    """
    try:
        document_id = req.route_params.get("document_id")
        if not document_id:
            return error_response("Document ID required", 400)

        service = get_document_service()
        result = service.get_result(document_id)

        if not result:
            return error_response("Result not found", 404)

        return json_response({
            "document_id": result.document_id,
            "category_id": result.category_id,
            "extracted_fields": result.extracted_fields,
            "confidence": result.confidence,
            "analyzed_at": result.analyzed_at.isoformat(),
        })

    except Exception as e:
        logger.exception("Get result failed")
        return error_response(str(e), 500)


@app.route(route="documents/{document_id}/feedback", methods=["POST"])
def submit_feedback(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/documents/{document_id}/feedback
    
    Submit feedback with corrected fields.
    Body: { corrected_fields: {...}, reviewer?: string, comment?: string }
    """
    try:
        document_id = req.route_params.get("document_id")
        if not document_id:
            return error_response("Document ID required", 400)

        body = req.get_json()
        corrected_fields = body.get("corrected_fields")
        if not corrected_fields:
            return error_response("corrected_fields required", 400)

        service = get_document_service()
        feedback = service.submit_feedback(
            document_id=document_id,
            corrected_fields=corrected_fields,
            reviewer=body.get("reviewer"),
            comment=body.get("comment"),
        )

        logger.info(f"Feedback submitted for: {document_id}")
        return json_response({
            "feedback_id": feedback.feedback_id,
            "document_id": feedback.document_id,
            "created_at": feedback.created_at.isoformat(),
        }, 201)

    except Exception as e:
        logger.exception("Submit feedback failed")
        return error_response(str(e), 500)


# --- Config Endpoints ---

@app.route(route="config", methods=["GET"])
def get_config(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/config
    
    Get current pipeline configuration.
    """
    try:
        config = load_config()
        return json_response({
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
        })

    except Exception as e:
        logger.exception("Get config failed")
        return error_response(str(e), 500)


@app.route(route="config", methods=["PUT"])
def update_config(req: func.HttpRequest) -> func.HttpResponse:
    """
    PUT /api/config
    
    Update pipeline configuration.
    Note: This is an admin endpoint - implement proper auth in production.
    """
    try:
        body = req.get_json()

        # Parse and validate config
        azure_data = body.get("azure", {})
        azure = AzureSettings(
            endpoint=azure_data.get("endpoint", ""),
            api_version=azure_data.get("api_version", "2025-05-01-preview"),
            router_analyzer_id=azure_data.get("router_analyzer_id", "doc-router"),
        )

        categories = [
            Category(
                id=c["id"],
                display_name=c["display_name"],
                analyzer_id=c["analyzer_id"],
                classification_prompt=c.get("classification_prompt", ""),
                extraction_schema=c.get("extraction_schema", {}),
            )
            for c in body.get("categories", [])
        ]

        config = PipelineConfig(azure=azure, categories=categories)
        save_config(config)

        logger.info("Configuration updated")
        return json_response({"message": "Configuration updated"})

    except KeyError as e:
        return error_response(f"Missing required field: {e}", 400)
    except Exception as e:
        logger.exception("Update config failed")
        return error_response(str(e), 500)


@app.route(route="config/setup-analyzers", methods=["POST"])
def setup_analyzers(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/config/setup-analyzers
    
    Create/update all analyzers in Content Understanding based on config.
    """
    try:
        config = load_config()
        builder = get_analyzer_builder()
        builder.setup_all(config)

        logger.info("Analyzers setup complete")
        return json_response({
            "message": "Analyzers created/updated",
            "router_id": config.azure.router_analyzer_id,
            "category_analyzers": [c.analyzer_id for c in config.categories],
        })

    except Exception as e:
        logger.exception("Setup analyzers failed")
        return error_response(str(e), 500)
