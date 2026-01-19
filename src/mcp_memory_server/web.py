"""Web UI placeholder - minimal stub for now."""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="MCP Memory Server")


@app.get("/", response_class=HTMLResponse)
async def root() -> str:
    """Serve a placeholder page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCP Memory Server</title>
        <style>
            body { font-family: system-ui; max-width: 800px; margin: 50px auto; }
            h1 { color: #333; }
            p { color: #666; }
        </style>
    </head>
    <body>
        <h1>MCP Memory Server</h1>
        <p>Web UI coming soon. The MCP server is running.</p>
        <p>Use the MCP tools to interact with the memory system.</p>
    </body>
    </html>
    """


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
