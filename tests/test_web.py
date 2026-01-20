"""Tests for the Web UI API endpoints."""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from mcp_memory_server.database import init_database
from mcp_memory_server.web import app


@pytest.fixture(autouse=True)
def setup_database() -> Generator[None, None, None]:
    """Set up a fresh database for each test."""
    db_path = os.environ["MEMORY_DB_PATH"]
    if os.path.exists(db_path):
        os.remove(db_path)

    init_database()
    yield

    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


class TestWebAPI:
    """Tests for the Web API endpoints."""

    def test_health_check(self, client: TestClient) -> None:
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_root_returns_html(self, client: TestClient) -> None:
        """Test that root returns HTML UI."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "MCP Memory Server" in response.text

    def test_list_memories_empty(self, client: TestClient) -> None:
        """Test listing memories when empty."""
        response = client.get("/api/memories")
        assert response.status_code == 200
        data = response.json()
        assert data["memories"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["total_pages"] == 1

    def test_create_memory(self, client: TestClient) -> None:
        """Test creating a new memory."""
        response = client.post(
            "/api/memories",
            json={"content": "Test memory content", "force": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "stored"
        assert data["content"] == "Test memory content"
        assert "id" in data

    def test_create_memory_conflict_detection(self, client: TestClient) -> None:
        """Test that duplicate detection works."""
        client.post(
            "/api/memories",
            json={"content": "I love pizza", "force": True},
        )

        response = client.post(
            "/api/memories",
            json={"content": "I love pizza very much"},
        )
        data = response.json()
        assert data["status"] == "conflict_detected"
        assert "similar_memories" in data

    def test_list_memories_with_data(self, client: TestClient) -> None:
        """Test listing memories with data."""
        client.post("/api/memories", json={"content": "Memory 1", "force": True})
        client.post("/api/memories", json={"content": "Memory 2", "force": True})

        response = client.get("/api/memories")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["memories"]) == 2

    def test_search_memories(self, client: TestClient) -> None:
        """Test searching memories."""
        client.post("/api/memories", json={"content": "Python programming", "force": True})
        client.post("/api/memories", json={"content": "JavaScript coding", "force": True})

        response = client.get("/api/memories/search?q=Python")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any("Python" in r["content"] for r in data["results"])

    def test_update_memory(self, client: TestClient) -> None:
        """Test updating a memory."""
        create_response = client.post(
            "/api/memories",
            json={"content": "Original content", "force": True},
        )
        memory_id = create_response.json()["id"]

        response = client.put(
            f"/api/memories/{memory_id}",
            json={"content": "Updated content"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        assert data["content"] == "Updated content"

    def test_update_nonexistent_memory(self, client: TestClient) -> None:
        """Test updating a non-existent memory."""
        response = client.put(
            "/api/memories/99999",
            json={"content": "New content"},
        )
        assert response.status_code == 404

    def test_delete_memory(self, client: TestClient) -> None:
        """Test deleting a memory."""
        create_response = client.post(
            "/api/memories",
            json={"content": "To be deleted", "force": True},
        )
        memory_id = create_response.json()["id"]

        response = client.delete(f"/api/memories/{memory_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"

        list_response = client.get("/api/memories")
        assert list_response.json()["total"] == 0

    def test_delete_nonexistent_memory(self, client: TestClient) -> None:
        """Test deleting a non-existent memory."""
        response = client.delete("/api/memories/99999")
        assert response.status_code == 404

    def test_pagination(self, client: TestClient) -> None:
        """Test pagination of memories."""
        for i in range(5):
            client.post(
                "/api/memories",
                json={"content": f"Memory number {i}", "force": True},
            )

        response = client.get("/api/memories?page=1&limit=2")
        data = response.json()
        assert len(data["memories"]) == 2
        assert data["total"] == 5
        assert data["total_pages"] == 3

        response2 = client.get("/api/memories?page=2&limit=2")
        data2 = response2.json()
        assert len(data2["memories"]) == 2
        assert data2["page"] == 2
