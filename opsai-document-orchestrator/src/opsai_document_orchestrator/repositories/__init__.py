"""Data repositories for persistence."""

from .base import Repository
from .table_storage import TableRepository, DocumentRepository, FeedbackRepository

__all__ = ["Repository", "TableRepository", "DocumentRepository", "FeedbackRepository"]
