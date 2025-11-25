"""Azure Blob Storage client for document storage."""

import logging
from datetime import datetime, timedelta

from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

logger = logging.getLogger(__name__)


class BlobStorageClient:
    """Client for Azure Blob Storage operations."""

    def __init__(self, connection_string: str, container_name: str):
        self._connection_string = connection_string
        self._container_name = container_name
        self._service_client = BlobServiceClient.from_connection_string(connection_string)
        self._container_client = self._service_client.get_container_client(container_name)
        self._ensure_container()

    def _ensure_container(self) -> None:
        """Create container if it doesn't exist."""
        try:
            self._container_client.create_container()
            logger.info(f"Created container: {self._container_name}")
        except Exception:
            pass  # Container exists

    def upload(self, blob_name: str, data: bytes, content_type: str) -> str:
        """Upload blob and return URL."""
        blob_client = self._container_client.get_blob_client(blob_name)
        blob_client.upload_blob(data, overwrite=True, content_settings={"content_type": content_type})
        logger.info(f"Uploaded blob: {blob_name}")
        return blob_client.url

    def get_sas_url(self, blob_name: str, expiry_hours: int = 24) -> str:
        """Generate SAS URL for blob access."""
        # Parse account info from connection string
        account_name = None
        account_key = None
        for part in self._connection_string.split(";"):
            if part.startswith("AccountName="):
                account_name = part.split("=", 1)[1]
            elif part.startswith("AccountKey="):
                account_key = part.split("=", 1)[1]

        if not account_name or not account_key:
            # Return direct URL if can't generate SAS
            return self._container_client.get_blob_client(blob_name).url

        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=self._container_name,
            blob_name=blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=expiry_hours),
        )
        blob_url = self._container_client.get_blob_client(blob_name).url
        return f"{blob_url}?{sas_token}"

    def exists(self, blob_name: str) -> bool:
        """Check if blob exists."""
        return self._container_client.get_blob_client(blob_name).exists()

    def delete(self, blob_name: str) -> None:
        """Delete blob."""
        self._container_client.get_blob_client(blob_name).delete_blob()
        logger.info(f"Deleted blob: {blob_name}")
