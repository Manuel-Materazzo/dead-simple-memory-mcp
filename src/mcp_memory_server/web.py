"""Web UI for MCP Memory Server."""

from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.requests import Request

from mcp_memory_server.database import (
    create_memory,
    delete_memory,
    get_statistics,
    list_memories,
    search_memories,
    update_memory,
)

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(title="MCP Memory Server")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


class MemoryCreate(BaseModel):
    content: str
    metadata: Optional[dict[str, Any]] = None
    force: bool = False


class MemoryUpdate(BaseModel):
    content: str
    metadata: Optional[dict[str, Any]] = None


@app.get("/api/memories")
async def api_list_memories(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
) -> dict[str, Any]:
    """List memories with pagination."""
    return list_memories(page=page, limit=limit)


@app.get("/api/memories/search")
async def api_search_memories(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    threshold: float = Query(0.5, ge=0, le=1),
) -> dict[str, Any]:
    """Search memories using vector similarity."""
    results = search_memories(q, limit=limit, similarity_threshold=threshold)
    return {"results": results, "count": len(results)}


@app.post("/api/memories")
async def api_create_memory(memory: MemoryCreate) -> dict[str, Any]:
    """Create a new memory."""
    result = create_memory(
        content=memory.content,
        metadata=memory.metadata,
        force=memory.force,
    )
    return result


@app.put("/api/memories/{memory_id}")
async def api_update_memory(memory_id: int, memory: MemoryUpdate) -> dict[str, Any]:
    """Update an existing memory."""
    result = update_memory(
        memory_id=memory_id,
        content=memory.content,
        metadata=memory.metadata,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@app.delete("/api/memories/{memory_id}")
async def api_delete_memory(memory_id: int) -> dict[str, Any]:
    """Delete a memory."""
    result = delete_memory(memory_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/stats")
async def api_stats() -> dict[str, Any]:
    """Get memory database statistics."""
    return get_statistics()


@app.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    """Serve the main UI."""
    return templates.TemplateResponse(request, "index.html")
