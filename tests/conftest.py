"""Shared pytest configuration and fixtures."""

import os
import tempfile
from collections.abc import Generator

import pytest

os.environ["MEMORY_DB_PATH"] = os.path.join(tempfile.gettempdir(), "test_memories.db")


@pytest.fixture(scope="session", autouse=True)
def init_embedding_model() -> Generator[None, None, None]:
    """Initialize the embedding model once for the entire test session."""
    from mcp_memory_server.embeddings import _model_ready, start_model_loading

    if not _model_ready.is_set():
        start_model_loading()
        _model_ready.wait()

    yield
