"""Configuration management via environment variables."""

import os
from pathlib import Path


def get_db_path() -> Path:
    """Get the database path from environment or use default."""
    default_path = Path.home() / ".mcp-memory" / "memories.db"
    path_str = os.getenv("MEMORY_DB_PATH")
    if path_str:
        return Path(path_str)
    return default_path


def get_ui_port() -> int:
    """Get the UI port from environment or use default."""
    return int(os.getenv("MEMORY_UI_PORT", "6277"))


def is_ui_enabled() -> bool:
    """Check if the UI is enabled."""
    return os.getenv("MEMORY_UI_ENABLED", "true").lower() == "true"


def get_embedding_model() -> str:
    """Get the embedding model name from environment or use default."""
    return os.getenv("MEMORY_EMBEDDING_MODEL", "all-MiniLM-L6-v2")


def get_duplicate_threshold() -> float:
    """Get the duplicate detection threshold from environment or use default."""
    return float(os.getenv("MEMORY_DUPLICATE_THRESHOLD", "0.7"))


def get_search_threshold() -> float:
    """Get the search similarity threshold from environment or use default."""
    return float(os.getenv("MEMORY_SEARCH_THRESHOLD", "0.5"))
