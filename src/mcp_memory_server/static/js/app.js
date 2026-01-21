const API = '/api/memories';
let currentPage = 1;
let totalPages = 1;
let isSearchMode = false;
let editingId = null;
let pendingDeleteId = null;

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
        list.innerHTML = `
            <div class="empty-state">
                <h3>No memories found</h3>
                <p>${isSearchMode ? 'Try a different search query' : 'Add your first memory to get started'}</p>
            </div>`;
        return;
    }
    list.innerHTML = memories.map(m => `
        <div class="memory-card" data-id="${m.id}">
            <div class="memory-header">
                <span class="memory-id">#${m.id}</span>
                ${showSimilarity ? `<span class="memory-similarity">${(m.similarity * 100).toFixed(1)}% match</span>` : ''}
            </div>
            <div class="memory-content" id="content-${m.id}">${escapeHtml(m.content)}</div>
            ${m.metadata ? `
            <div class="memory-metadata" id="metadata-display-${m.id}">
                <span class="metadata-label">Metadata:</span>
                <code class="metadata-value">${escapeHtml(JSON.stringify(m.metadata, null, 2))}</code>
            </div>` : ''}
            <div class="memory-metadata-edit hidden" id="metadata-edit-${m.id}">
                <label class="metadata-edit-label">Metadata (JSON):</label>
                <textarea class="metadata-textarea" id="metadata-input-${m.id}" placeholder='{"key": "value"}'>${m.metadata ? JSON.stringify(m.metadata, null, 2) : ''}</textarea>
            </div>
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
    if (editingId === id) return;
    if (editingId) resetEditingState();
    editingId = id;
    const el = document.getElementById(`content-${id}`);
    const text = el.textContent;
    el.innerHTML = '';
    el.contentEditable = true;
    el.classList.add('editing');
    el.textContent = text;
    el.focus();

    const metadataDisplay = document.getElementById(`metadata-display-${id}`);
    if (metadataDisplay) metadataDisplay.classList.add('hidden');
    const metadataEdit = document.getElementById(`metadata-edit-${id}`);
    if (metadataEdit) metadataEdit.classList.remove('hidden');

    const actions = el.closest('.memory-card').querySelector('.memory-actions');
    actions.innerHTML = `
        <button class="btn btn-small" onclick="saveEdit(${id})">Save</button>
        <button class="btn btn-small" onclick="cancelEdit()">Cancel</button>
    `;
}

function resetEditingState() {
    if (!editingId) return;
    const el = document.getElementById(`content-${editingId}`);
    if (el) {
        el.contentEditable = false;
        el.classList.remove('editing');

        const metadataDisplay = document.getElementById(`metadata-display-${editingId}`);
        if (metadataDisplay) metadataDisplay.classList.remove('hidden');
        const metadataEdit = document.getElementById(`metadata-edit-${editingId}`);
        if (metadataEdit) metadataEdit.classList.add('hidden');

        const card = el.closest('.memory-card');
        if (card) {
            const actions = card.querySelector('.memory-actions');
            actions.innerHTML = `
                <button class="btn btn-small" onclick="startEdit(${editingId})">Edit</button>
                <button class="btn btn-small btn-danger" onclick="deleteMemory(${editingId})">Delete</button>
            `;
        }
    }
    editingId = null;
}

async function saveEdit(id) {
    const el = document.getElementById(`content-${id}`);
    const content = el.textContent.trim();
    if (!content) {
        showToast('Content cannot be empty', 'error');
        return;
    }

    const metadataInput = document.getElementById(`metadata-input-${id}`);
    let metadata = null;
    if (metadataInput && metadataInput.value.trim()) {
        try {
            metadata = JSON.parse(metadataInput.value.trim());
        } catch (e) {
            showToast('Invalid JSON in metadata field', 'error');
            return;
        }
    }

    try {
        const res = await fetch(`${API}/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content, metadata })
        });
        if (!res.ok) throw new Error('Failed to update');
        showToast('Memory updated', 'success');
        editingId = null;
        isSearchMode ? searchMemories(document.getElementById('searchInput').value) : fetchMemories(currentPage);
        fetchStats();
    } catch (e) {
        showToast('Failed to update memory', 'error');
    }
}

function cancelEdit() {
    if (!editingId) return;
    isSearchMode ? searchMemories(document.getElementById('searchInput').value) : fetchMemories(currentPage);
    editingId = null;
}

function deleteMemory(id) {
    pendingDeleteId = id;
    document.getElementById('deleteModal').classList.remove('hidden');
}

function closeDeleteModal() {
    document.getElementById('deleteModal').classList.add('hidden');
    pendingDeleteId = null;
}

async function confirmDelete() {
    if (!pendingDeleteId) return;
    const id = pendingDeleteId;
    closeDeleteModal();
    try {
        const res = await fetch(`${API}/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Failed to delete');
        showToast('Memory deleted', 'success');
        isSearchMode ? searchMemories(document.getElementById('searchInput').value) : fetchMemories(currentPage);
        fetchStats();
    } catch (e) {
        showToast('Failed to delete memory', 'error');
    }
}

async function createMemory(force = false) {
    const content = document.getElementById('newMemoryContent').value.trim();
    if (!content) {
        showToast('Content cannot be empty', 'error');
        return;
    }

    const metadataInput = document.getElementById('newMemoryMetadata');
    let metadata = null;
    if (metadataInput && metadataInput.value.trim()) {
        try {
            metadata = JSON.parse(metadataInput.value.trim());
        } catch (e) {
            showToast('Invalid JSON in metadata field', 'error');
            return;
        }
    }

    try {
        const res = await fetch(API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content, metadata, force })
        });
        const data = await res.json();

        if (data.status === 'conflict_detected') {
            showConflict(data.similar_memories);
            return;
        }

        closeModal();
        showToast('Memory created', 'success');
        fetchMemories(1);
        fetchStats();
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
    if (editingId) resetEditingState();
    document.getElementById('addModal').classList.remove('hidden');
    document.getElementById('newMemoryContent').value = '';
    document.getElementById('newMemoryMetadata').value = '';
    document.getElementById('conflictWarning').style.display = 'none';
    document.getElementById('saveMemory').style.display = '';
    document.getElementById('forceSave').style.display = 'none';
    document.getElementById('newMemoryContent').focus();
}

function closeModal() {
    document.getElementById('addModal').classList.add('hidden');
}

function updateStats(total, isSearch = false) {
    document.getElementById('stats').textContent = isSearch
        ? `${total} result${total !== 1 ? 's' : ''} found`
        : `${total} memor${total !== 1 ? 'ies' : 'y'}`;
}

async function fetchStats() {
    try {
        const res = await fetch('/api/stats');
        const stats = await res.json();
        document.getElementById('statMemories').textContent = stats.total_memories;
        document.getElementById('statStorage').textContent = stats.storage_human;
        document.getElementById('statActivity').textContent = stats.latest_activity 
            ? formatRelativeTime(stats.latest_activity) 
            : 'Never';
        document.getElementById('statModel').textContent = stats.embedding_model;
    } catch (e) {
        console.error('Failed to fetch stats:', e);
    }
}

function formatRelativeTime(dateStr) {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    if (diffSec < 60) return 'Just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHour < 24) return `${diffHour}h ago`;
    if (diffDay < 7) return `${diffDay}d ago`;
    return date.toLocaleDateString();
}

function updatePagination() {
    const pagination = document.getElementById('pagination');
    if (totalPages <= 1) {
        pagination.style.display = 'none';
        return;
    }
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

// Event listeners
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

document.getElementById('cancelDelete').addEventListener('click', closeDeleteModal);
document.getElementById('confirmDelete').addEventListener('click', confirmDelete);
document.getElementById('deleteModal').addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) closeDeleteModal();
});

// Initialize
fetchMemories(1);
fetchStats();
