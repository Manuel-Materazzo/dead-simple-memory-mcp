"""Tests for database operations."""

import os
import tempfile
from pathlib import Path

import pytest

os.environ["MEMORY_DB_PATH"] = str(Path(tempfile.gettempdir()) / "test_memories.db")

from mcp_memory_server.database import (
    create_memory,
    delete_memory,
    init_database,
    list_memories,
    search_memories,
    update_memory,
)
from mcp_memory_server.embeddings import start_model_loading


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Initialize the database and embedding model before tests."""
    start_model_loading()
    init_database()
    yield
    db_path = Path(os.environ["MEMORY_DB_PATH"])
    if db_path.exists():
        db_path.unlink()


class TestMemoryOperations:
    def test_create_memory(self):
        """Test creating a new memory."""
        result = create_memory("I love programming in Python", force=True)
        assert result["status"] == "stored"
        assert result["id"] is not None
        assert result["content"] == "I love programming in Python"

    def test_create_memory_duplicate_detection(self):
        """Test duplicate detection when creating memories."""
        create_memory("I enjoy writing tests", force=True)
        result = create_memory("I enjoy writing tests")
        assert result["status"] == "conflict_detected"
        assert "similar_memories" in result

    def test_search_memories(self):
        """Test searching memories with vector similarity."""
        create_memory("The weather is sunny today", force=True)
        results = search_memories("sunny weather", limit=5, similarity_threshold=0.5)
        assert len(results) >= 1
        assert any("sunny" in r["content"].lower() for r in results)

    def test_update_memory(self):
        """Test updating an existing memory."""
        created = create_memory("Original content here", force=True)
        memory_id = created["id"]
        
        result = update_memory(memory_id, "Updated content here")
        assert result["status"] == "updated"
        assert result["content"] == "Updated content here"

    def test_update_nonexistent_memory(self):
        """Test updating a memory that doesn't exist."""
        result = update_memory(99999, "This should fail")
        assert result["status"] == "error"
        assert "not found" in result["message"]

    def test_delete_memory(self):
        """Test deleting a memory."""
        created = create_memory("Memory to delete", force=True)
        memory_id = created["id"]
        
        result = delete_memory(memory_id)
        assert result["status"] == "deleted"
        assert result["id"] == memory_id

    def test_delete_nonexistent_memory(self):
        """Test deleting a memory that doesn't exist."""
        result = delete_memory(99999)
        assert result["status"] == "error"
        assert "not found" in result["message"]

    def test_list_memories(self):
        """Test listing memories with pagination."""
        for i in range(3):
            create_memory(f"List test memory {i}", force=True)
        
        result = list_memories(page=1, limit=10)
        assert "memories" in result
        assert "total" in result
        assert "page" in result
        assert "total_pages" in result
        assert len(result["memories"]) > 0
