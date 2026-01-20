"""Database management for memory storage."""

import json
import sqlite3
from datetime import datetime
from typing import Any, Optional

import sqlite_vec

from mcp_memory_server.config import get_db_path, get_duplicate_threshold
from mcp_memory_server.embeddings import embedding_to_blob, get_embedding

EMBEDDING_DIM = 384


def get_connection() -> sqlite3.Connection:
    """Get a database connection with sqlite-vec loaded."""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    conn.row_factory = sqlite3.Row
    return conn


def init_database() -> None:
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            embedding BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
    """)

    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS vec_memories USING vec0(
            embedding float[384]
        )
    """)

    conn.commit()
    conn.close()


def search_memories(
    query: str, limit: int = 5, similarity_threshold: float = 0.7
) -> list[dict[str, Any]]:
    """Search memories using vector similarity."""
    query_embedding = get_embedding(query)
    query_blob = embedding_to_blob(query_embedding)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            v.rowid,
            v.distance
        FROM vec_memories v
        WHERE v.embedding MATCH ?
        ORDER BY v.distance ASC
        LIMIT ?
        """,
        (query_blob, limit * 2),
    )

    vec_results = cursor.fetchall()

    results = []
    for row in vec_results:
        distance = row["distance"]
        # For normalized embeddings, L2 distance relates to cosine similarity by:
        # cosine_similarity = 1 - (L2_distance² / 2)
        similarity = 1 - (distance * distance / 2)
        if similarity < similarity_threshold:
            continue

        cursor.execute(
            "SELECT id, content, created_at, updated_at, metadata FROM memories WHERE id = ?",
            (row["rowid"],),
        )
        memory_row = cursor.fetchone()
        if memory_row:
            results.append({
                "id": memory_row["id"],
                "content": memory_row["content"],
                "similarity": round(similarity, 4),
                "created_at": memory_row["created_at"],
                "updated_at": memory_row["updated_at"],
                "metadata": json.loads(memory_row["metadata"])
                if memory_row["metadata"]
                else None,
            })

        if len(results) >= limit:
            break

    conn.close()
    return results


def find_similar_memories(
    content: str, threshold: Optional[float] = None
) -> list[dict[str, Any]]:
    """Find memories similar to the given content for duplicate detection."""
    if threshold is None:
        threshold = get_duplicate_threshold()
    return search_memories(content, limit=5, similarity_threshold=threshold)


def create_memory(
    content: str, metadata: Optional[dict[str, Any]] = None, force: bool = False
) -> dict[str, Any]:
    """Create a new memory with duplicate detection."""
    if not force:
        similar = find_similar_memories(content)
        if similar:
            return {
                "status": "conflict_detected",
                "message": "Found similar existing memories. "
                "Use force=true to create anyway, or call update_memory to merge.",
                "similar_memories": [
                    {"id": m["id"], "content": m["content"], "similarity": m["similarity"]}
                    for m in similar
                ],
            }

    embedding = get_embedding(content)
    embedding_blob = embedding_to_blob(embedding)
    metadata_json = json.dumps(metadata) if metadata else None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO memories (content, embedding, metadata) VALUES (?, ?, ?)",
        (content, embedding_blob, metadata_json),
    )
    memory_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO vec_memories (rowid, embedding) VALUES (?, ?)",
        (memory_id, embedding_blob),
    )

    conn.commit()

    cursor.execute("SELECT created_at FROM memories WHERE id = ?", (memory_id,))
    row = cursor.fetchone()
    created_at = row["created_at"] if row else datetime.now().isoformat()

    conn.close()

    return {
        "status": "stored",
        "id": memory_id,
        "content": content,
        "created_at": created_at,
    }


def update_memory(
    memory_id: int, content: str, metadata: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """Update an existing memory by ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM memories WHERE id = ?", (memory_id,))
    if not cursor.fetchone():
        conn.close()
        return {"status": "error", "message": f"Memory with id {memory_id} not found"}

    embedding = get_embedding(content)
    embedding_blob = embedding_to_blob(embedding)
    metadata_json = json.dumps(metadata) if metadata else None
    updated_at = datetime.now().isoformat()

    cursor.execute(
        "UPDATE memories SET content = ?, embedding = ?, metadata = ?, updated_at = ? WHERE id = ?",
        (content, embedding_blob, metadata_json, updated_at, memory_id),
    )

    cursor.execute(
        "UPDATE vec_memories SET embedding = ? WHERE rowid = ?",
        (embedding_blob, memory_id),
    )

    conn.commit()
    conn.close()

    return {
        "status": "updated",
        "id": memory_id,
        "content": content,
        "updated_at": updated_at,
    }


def delete_memory(memory_id: int) -> dict[str, Any]:
    """Delete a memory by ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM memories WHERE id = ?", (memory_id,))
    if not cursor.fetchone():
        conn.close()
        return {"status": "error", "message": f"Memory with id {memory_id} not found"}

    cursor.execute("DELETE FROM vec_memories WHERE rowid = ?", (memory_id,))
    cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))

    conn.commit()
    conn.close()

    return {"status": "deleted", "id": memory_id}


def list_memories(page: int = 1, limit: int = 50) -> dict[str, Any]:
    """List all memories with pagination."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM memories")
    total = cursor.fetchone()["total"]

    offset = (page - 1) * limit
    cursor.execute(
        """
        SELECT id, content, created_at, updated_at, metadata
        FROM memories
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    )

    memories = []
    for row in cursor.fetchall():
        memories.append({
            "id": row["id"],
            "content": row["content"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
        })

    conn.close()

    total_pages = (total + limit - 1) // limit if total > 0 else 1

    return {
        "memories": memories,
        "total": total,
        "page": page,
        "total_pages": total_pages,
    }
