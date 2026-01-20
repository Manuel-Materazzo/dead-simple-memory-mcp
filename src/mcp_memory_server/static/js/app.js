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
    if (!content) {
        showToast('Content cannot be empty', 'error');
        return;
    }

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
    if (editingId) resetEditingState();
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
    document.getElementById('stats').textContent = isSearch
        ? `${total} result${total !== 1 ? 's' : ''} found`
        : `${total} memor${total !== 1 ? 'ies' : 'y'}`;
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

// Initialize
fetchMemories(1);
