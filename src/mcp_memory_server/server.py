"""MCP Server implementation with stdio transport."""

import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from mcp_memory_server.config import get_search_threshold, get_ui_port, is_ui_enabled
from mcp_memory_server.database import (
    create_memory,
    delete_memory,
    init_database,
    list_memories,
    search_memories,
    update_memory,
)
from mcp_memory_server.embeddings import start_model_loading

server = Server("mcp-memory-server")


@server.list_tools()  # type: ignore[no-untyped-call, untyped-decorator]
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="search_memory",
            description="Search memories using vector similarity",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query text",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)",
                        "default": 5,
                    },
                    "similarity_threshold": {
                        "type": "number",
                        "description": "Minimum cosine similarity 0-1 (default: 0.5)",
                        "default": 0.5,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="write_memory",
            description="Store a new memory with automatic duplicate detection",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Memory content to store",
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Skip duplicate check and force creation (default: false)",
                        "default": False,
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional context as JSON",
                    },
                },
                "required": ["content"],
            },
        ),
        Tool(
            name="update_memory",
            description="Update an existing memory by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "Memory ID to update",
                    },
                    "content": {
                        "type": "string",
                        "description": "New content",
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Updated metadata",
                    },
                },
                "required": ["id", "content"],
            },
        ),
        Tool(
            name="delete_memory",
            description="Delete a memory by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "Memory ID to delete",
                    },
                },
                "required": ["id"],
            },
        ),
        Tool(
            name="list_memories",
            description="List all memories you saved so far with pagination",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "Page number, 1-indexed (default: 1)",
                        "default": 1,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results per page (default: 50)",
                        "default": 50,
                    },
                },
            },
        ),
    ]


@server.call_tool()  # type: ignore[untyped-decorator]
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    result: dict[str, Any]

    if name == "search_memory":
        query = arguments["query"]
        limit = arguments.get("limit", 5)
        threshold = arguments.get("similarity_threshold", get_search_threshold())
        results = search_memories(query, limit=limit, similarity_threshold=threshold)
        result = {"results": results, "count": len(results)}

    elif name == "write_memory":
        content = arguments["content"]
        force = arguments.get("force", False)
        metadata = arguments.get("metadata")
        result = create_memory(content, metadata=metadata, force=force)

    elif name == "update_memory":
        memory_id = arguments["id"]
        content = arguments["content"]
        metadata = arguments.get("metadata")
        result = update_memory(memory_id, content, metadata=metadata)

    elif name == "delete_memory":
        memory_id = arguments["id"]
        result = delete_memory(memory_id)

    elif name == "list_memories":
        page = arguments.get("page", 1)
        limit = arguments.get("limit", 50)
        result = list_memories(page=page, limit=limit)

    else:
        result = {"status": "error", "message": f"Unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


def start_ui_server() -> None:
    """Start the web UI server in a background thread."""
    import threading

    import uvicorn

    from mcp_memory_server.web import app

    port = get_ui_port()

    def run_server() -> None:
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()


def main() -> None:
    """Main entry point for the MCP server."""
    import asyncio

    start_model_loading()

    init_database()

    if is_ui_enabled():
        start_ui_server()

    async def run_server() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
