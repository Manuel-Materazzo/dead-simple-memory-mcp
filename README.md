# MCP Memory Server

A minimal, self-contained MCP (Model Context Protocol) server for AI agent memory management with vector search capabilities.

## Features

- **Vector Search**: Find memories using semantic similarity
- **Duplicate Detection**: Automatically detects similar memories before storing
- **Zero External Dependencies**: Uses embedded SQLite with sqlite-vec
- **stdio Transport**: Compatible with LM Studio and other MCP clients

## Installation

```bash
# Using uvx (recommended)
uvx mcp-memory-server

# Or install with pip
pip install mcp-memory-server
```

## MCP Tools

### `search_memory`
Search memories using vector similarity.

**Parameters:**
- `query` (string, required): Search query text
- `limit` (integer, optional, default=5): Number of results
- `similarity_threshold` (float, optional, default=0.5): Minimum cosine similarity (0-1)

### `write_memory`
Store a new memory with automatic duplicate detection.

**Parameters:**
- `content` (string, required): Memory content to store
- `force` (boolean, optional, default=false): Skip duplicate check
- `metadata` (object, optional): Additional context as JSON

### `update_memory`
Update an existing memory by ID.

**Parameters:**
- `id` (integer, required): Memory ID to update
- `content` (string, required): New content
- `metadata` (object, optional): Updated metadata

### `delete_memory`
Delete a memory by ID.

**Parameters:**
- `id` (integer, required): Memory ID to delete

### `list_memories`
List all memories with pagination.

**Parameters:**
- `page` (integer, optional, default=1): Page number (1-indexed)
- `limit` (integer, optional, default=50): Results per page

## Configuration

### Environment Variables

| Variable | Default                     | Description |
|----------|-----------------------------|-------------|
| `MEMORY_DB_PATH` | `~/.mcp-memory/memories.db` | SQLite database location |
| `MEMORY_UI_PORT` | `6277`                      | Web UI port |
| `MEMORY_UI_ENABLED` | `true`                      | Enable/disable web UI |
| `MEMORY_EMBEDDING_MODEL` | `all-MiniLM-L6-v2`          | Embedding model name |
| `MEMORY_DUPLICATE_THRESHOLD` | `0.7`                       | Similarity threshold for duplicate detection |
| `MEMORY_SEARCH_THRESHOLD` | `0.5`                       | Default similarity threshold for search queries |

### LM Studio Configuration (mcp.json)

```json
{
  "mcpServers": {
    "dead-simple-memory": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Manuel-Materazzo/dead-simple-memory-mcp.git",
        "mcp-memory-server"
      ],
      "env": {
        "MEMORY_DB_PATH": "/Users/username/.mcp-memory/memories.db"
      }
    }
  }
}
```

## Development

```bash
# Install dependencies
uv sync

# Run the server
uv run python -m mcp_memory_server

# Run tests
uv run pytest

# Type check
uv run mypy src/

# Lint
uv run ruff check src/
```

## License

MIT
