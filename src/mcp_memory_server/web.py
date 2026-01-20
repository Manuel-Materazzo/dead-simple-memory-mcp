"""Web UI for MCP Memory Server."""

from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from mcp_memory_server.database import (
    create_memory,
    delete_memory,
    list_memories,
    search_memories,
    update_memory,
)

app = FastAPI(title="MCP Memory Server")


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


@app.get("/", response_class=HTMLResponse)
async def root() -> str:  # noqa: E501
    """Serve the main UI."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Memory Server</title>
    <style>
        :root {
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --border-color: #30363d;
            --text-primary: #e6edf3;
            --text-secondary: #8b949e;
            --accent-blue: #58a6ff;
            --accent-green: #3fb950;
            --accent-red: #f85149;
            --accent-yellow: #d29922;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.5;
            min-height: 100vh;
        }
        .container { max-width: 900px; margin: 0 auto; padding: 24px; }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border-color);
        }
        h1 { font-size: 24px; font-weight: 600; }
        .stats { color: var(--text-secondary); font-size: 14px; }

        .search-bar {
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
        }
        .search-bar input {
            flex: 1;
            padding: 10px 12px;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            color: var(--text-primary);
            font-size: 14px;
        }
        .search-bar input:focus { outline: none; border-color: var(--accent-blue); }
        .search-bar input::placeholder { color: var(--text-secondary); }

        .btn {
            padding: 10px 16px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            background: var(--bg-tertiary);
            color: var(--text-primary);
            font-size: 14px;
            cursor: pointer;
            transition: background 0.15s, border-color 0.15s;
        }
        .btn:hover { background: var(--bg-secondary); border-color: var(--text-secondary); }
        .btn-primary { background: var(--accent-blue); border-color: var(--accent-blue); color: #fff; }
        .btn-primary:hover { background: #4d94e6; }
        .btn-danger { color: var(--accent-red); }
        .btn-danger:hover { background: rgba(248, 81, 73, 0.1); border-color: var(--accent-red); }
        .btn-small { padding: 6px 12px; font-size: 12px; }

        .memory-list { display: flex; flex-direction: column; gap: 12px; }
        .memory-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
        }
        .memory-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 8px;
        }
        .memory-id {
            font-size: 12px;
            color: var(--text-secondary);
            font-family: monospace;
        }
        .memory-similarity {
            font-size: 12px;
            padding: 2px 8px;
            background: rgba(88, 166, 255, 0.15);
            color: var(--accent-blue);
            border-radius: 12px;
        }
        .memory-content {
            font-size: 14px;
            white-space: pre-wrap;
            word-break: break-word;
            margin-bottom: 12px;
        }
        .memory-content.editing {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 8px;
            min-height: 60px;
            outline: none;
        }
        .memory-content.editing:focus { border-color: var(--accent-blue); }
        .memory-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .memory-date { font-size: 12px; color: var(--text-secondary); }
        .memory-actions { display: flex; gap: 8px; }

        .modal-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.6);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 100;
        }
        .modal-overlay.hidden { display: none; }
        .modal {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            width: 90%;
            max-width: 500px;
            padding: 24px;
        }
        .modal h2 { margin-bottom: 16px; font-size: 18px; }
        .modal textarea {
            width: 100%;
            min-height: 120px;
            padding: 12px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            color: var(--text-primary);
            font-size: 14px;
            font-family: inherit;
            resize: vertical;
            margin-bottom: 16px;
        }
        .modal textarea:focus { outline: none; border-color: var(--accent-blue); }
        .modal-actions { display: flex; justify-content: flex-end; gap: 8px; }

        .conflict-warning {
            background: rgba(210, 153, 34, 0.1);
            border: 1px solid var(--accent-yellow);
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 16px;
        }
        .conflict-warning h3 { color: var(--accent-yellow); font-size: 14px; margin-bottom: 8px; }
        .conflict-item {
            font-size: 13px;
            padding: 8px;
            background: var(--bg-tertiary);
            border-radius: 4px;
            margin-top: 8px;
        }
        .conflict-similarity { color: var(--accent-yellow); }

        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 16px;
            margin-top: 24px;
            padding-top: 16px;
            border-top: 1px solid var(--border-color);
        }
        .pagination span { color: var(--text-secondary); font-size: 14px; }

        .empty-state {
            text-align: center;
            padding: 48px;
            color: var(--text-secondary);
        }
        .empty-state h3 { margin-bottom: 8px; color: var(--text-primary); }

        .loading { opacity: 0.6; pointer-events: none; }
        .toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            padding: 12px 20px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-size: 14px;
            z-index: 200;
            animation: slideIn 0.3s ease;
        }
        .toast.success { border-color: var(--accent-green); color: var(--accent-green); }
        .toast.error { border-color: var(--accent-red); color: var(--accent-red); }
        @keyframes slideIn { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>MCP Memory Server</h1>
            <span class="stats" id="stats">Loading...</span>
        </header>

        <div class="search-bar">
            <input type="text" id="searchInput" placeholder="Search memories..." />
            <button class="btn" id="clearSearch" style="display: none;">Clear</button>
            <button class="btn btn-primary" id="addBtn">+ Add Memory</button>
        </div>

        <div id="memoryList" class="memory-list"></div>

        <div id="pagination" class="pagination" style="display: none;">
            <button class="btn btn-small" id="prevPage">Previous</button>
            <span id="pageInfo"></span>
            <button class="btn btn-small" id="nextPage">Next</button>
        </div>
    </div>

    <div class="modal-overlay hidden" id="addModal">
        <div class="modal">
            <h2>Add New Memory</h2>
            <div id="conflictWarning" class="conflict-warning" style="display: none;"></div>
            <textarea id="newMemoryContent" placeholder="Enter memory content..."></textarea>
            <div class="modal-actions">
                <button class="btn" id="cancelAdd">Cancel</button>
                <button class="btn btn-primary" id="saveMemory">Save</button>
                <button class="btn btn-primary" id="forceSave" style="display: none;">Save Anyway</button>
            </div>
        </div>
    </div>

    <script>
        const API = '/api/memories';
        let currentPage = 1;
        let totalPages = 1;
        let isSearchMode = false;
        let editingId = null;

        async function fetchMemories(page = 1) {
            const res = await fetch(`${API}?page=${page}&limit=50`);
            const data = await res.json();
            currentPage = data.page;
            totalPages = data.total_pages;
            renderMemories(data.memories);
            updateStats(data.total);
            updatePagination();
        }

        async function searchMemories(query) {
            if (!query.trim()) {
                isSearchMode = false;
                document.getElementById('clearSearch').style.display = 'none';
                fetchMemories(1);
                return;
            }
            isSearchMode = true;
            document.getElementById('clearSearch').style.display = '';
            const res = await fetch(`${API}/search?q=${encodeURIComponent(query)}&limit=50`);
            const data = await res.json();
            renderMemories(data.results, true);
            updateStats(data.count, true);
            document.getElementById('pagination').style.display = 'none';
        }

        function renderMemories(memories, showSimilarity = false) {
            const list = document.getElementById('memoryList');
            if (!memories.length) {
                list.innerHTML = `<div class="empty-state"><h3>No memories found</h3><p>${isSearchMode ? 'Try a different search query' : 'Add your first memory to get started'}</p></div>`;
                return;
            }
            list.innerHTML = memories.map(m => `
                <div class="memory-card" data-id="${m.id}">
                    <div class="memory-header">
                        <span class="memory-id">#${m.id}</span>
                        ${showSimilarity ? `<span class="memory-similarity">${(m.similarity * 100).toFixed(1)}% match</span>` : ''}
                    </div>
                    <div class="memory-content" id="content-${m.id}">${escapeHtml(m.content)}</div>
                    <div class="memory-footer">
                        <span class="memory-date">Created: ${formatDate(m.created_at)}${m.updated_at !== m.created_at ? ` · Updated: ${formatDate(m.updated_at)}` : ''}</span>
                        <div class="memory-actions">
                            <button class="btn btn-small" onclick="startEdit(${m.id})">Edit</button>
                            <button class="btn btn-small btn-danger" onclick="deleteMemory(${m.id})">Delete</button>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        function startEdit(id) {
            if (editingId) cancelEdit();
            editingId = id;
            const el = document.getElementById(`content-${id}`);
            const text = el.textContent;
            el.innerHTML = '';
            el.contentEditable = true;
            el.classList.add('editing');
            el.textContent = text;
            el.focus();

            const actions = el.closest('.memory-card').querySelector('.memory-actions');
            actions.innerHTML = `
                <button class="btn btn-small" onclick="saveEdit(${id})">Save</button>
                <button class="btn btn-small" onclick="cancelEdit()">Cancel</button>
            `;
        }

        async function saveEdit(id) {
            const el = document.getElementById(`content-${id}`);
            const content = el.textContent.trim();
            if (!content) { showToast('Content cannot be empty', 'error'); return; }

            try {
                const res = await fetch(`${API}/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content })
                });
                if (!res.ok) throw new Error('Failed to update');
                showToast('Memory updated', 'success');
                editingId = null;
                isSearchMode ? searchMemories(document.getElementById('searchInput').value) : fetchMemories(currentPage);
            } catch (e) {
                showToast('Failed to update memory', 'error');
            }
        }

        function cancelEdit() {
            if (!editingId) return;
            isSearchMode ? searchMemories(document.getElementById('searchInput').value) : fetchMemories(currentPage);
            editingId = null;
        }

        async function deleteMemory(id) {
            if (!confirm('Delete this memory?')) return;
            try {
                const res = await fetch(`${API}/${id}`, { method: 'DELETE' });
                if (!res.ok) throw new Error('Failed to delete');
                showToast('Memory deleted', 'success');
                isSearchMode ? searchMemories(document.getElementById('searchInput').value) : fetchMemories(currentPage);
            } catch (e) {
                showToast('Failed to delete memory', 'error');
            }
        }

        async function createMemory(force = false) {
            const content = document.getElementById('newMemoryContent').value.trim();
            if (!content) { showToast('Content cannot be empty', 'error'); return; }

            try {
                const res = await fetch(API, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content, force })
                });
                const data = await res.json();

                if (data.status === 'conflict_detected') {
                    showConflict(data.similar_memories);
                    return;
                }

                closeModal();
                showToast('Memory created', 'success');
                fetchMemories(1);
            } catch (e) {
                showToast('Failed to create memory', 'error');
            }
        }

        function showConflict(memories) {
            const warning = document.getElementById('conflictWarning');
            warning.style.display = '';
            warning.innerHTML = `
                <h3>Similar memories found</h3>
                <p>These existing memories are similar:</p>
                ${memories.map(m => `
                    <div class="conflict-item">
                        <span class="conflict-similarity">${(m.similarity * 100).toFixed(1)}% match</span>
                        ${escapeHtml(m.content)}
                    </div>
                `).join('')}
            `;
            document.getElementById('saveMemory').style.display = 'none';
            document.getElementById('forceSave').style.display = '';
        }

        function openModal() {
            document.getElementById('addModal').classList.remove('hidden');
            document.getElementById('newMemoryContent').value = '';
            document.getElementById('conflictWarning').style.display = 'none';
            document.getElementById('saveMemory').style.display = '';
            document.getElementById('forceSave').style.display = 'none';
            document.getElementById('newMemoryContent').focus();
        }

        function closeModal() {
            document.getElementById('addModal').classList.add('hidden');
        }

        function updateStats(total, isSearch = false) {
            document.getElementById('stats').textContent = isSearch ? `${total} result${total !== 1 ? 's' : ''} found` : `${total} memor${total !== 1 ? 'ies' : 'y'}`;
        }

        function updatePagination() {
            const pagination = document.getElementById('pagination');
            if (totalPages <= 1) { pagination.style.display = 'none'; return; }
            pagination.style.display = '';
            document.getElementById('pageInfo').textContent = `Page ${currentPage} of ${totalPages}`;
            document.getElementById('prevPage').disabled = currentPage <= 1;
            document.getElementById('nextPage').disabled = currentPage >= totalPages;
        }

        function formatDate(dateStr) {
            if (!dateStr) return '';
            const d = new Date(dateStr);
            return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function showToast(message, type = 'info') {
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.textContent = message;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        }

        let searchTimeout;
        document.getElementById('searchInput').addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => searchMemories(e.target.value), 300);
        });

        document.getElementById('clearSearch').addEventListener('click', () => {
            document.getElementById('searchInput').value = '';
            isSearchMode = false;
            document.getElementById('clearSearch').style.display = 'none';
            fetchMemories(1);
        });

        document.getElementById('addBtn').addEventListener('click', openModal);
        document.getElementById('cancelAdd').addEventListener('click', closeModal);
        document.getElementById('saveMemory').addEventListener('click', () => createMemory(false));
        document.getElementById('forceSave').addEventListener('click', () => createMemory(true));

        document.getElementById('prevPage').addEventListener('click', () => fetchMemories(currentPage - 1));
        document.getElementById('nextPage').addEventListener('click', () => fetchMemories(currentPage + 1));

        document.getElementById('addModal').addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) closeModal();
        });

        fetchMemories(1);
    </script>
</body>
</html>"""
