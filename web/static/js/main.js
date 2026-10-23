// Cavern Wireless - Main JavaScript

// Auto-refresh interval (milliseconds)
const REFRESH_INTERVAL = 5000;

// Update status display
async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        // Update current broadcast
        const currentEl = document.getElementById('current-story');
        if (data.current_story) {
            currentEl.innerHTML = `
                <div class="story-ticket">Ticket ${data.current_story.ticket}</div>
                <div class="story-title">${escapeHtml(data.current_story.title)}</div>
                <div class="story-author">by ${escapeHtml(data.current_story.author)}</div>
                <div class="status-badge status-${data.current_story.status.toLowerCase()}">${data.current_story.status}</div>
            `;
        } else {
            currentEl.innerHTML = '<p class="loading">No story currently playing</p>';
        }
        
        // Update queue count
        document.getElementById('queue-count').textContent = data.queue_count;
        
        // Update playback status
        const playbackEl = document.getElementById('playback-status');
        playbackEl.textContent = data.playback_status;
        playbackEl.className = 'stat-value ' + (data.playback_status === 'ACTIVE' ? 'status-online' : 'status-warning');
        
        // Update system status
        if (data.system) {
            updateSystemIndicator('status-google', data.system.google);
            updateSystemIndicator('status-ollama', data.system.ollama);
            updateSystemIndicator('status-tts', data.system.tts);
            updateSystemIndicator('status-ffmpeg', data.system.ffmpeg);
        }
        
    } catch (error) {
        console.error('Failed to fetch status:', error);
    }
}

function updateSystemIndicator(elementId, status) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = status;
        el.className = 'status-indicator ' + status;
    }
}

// Update queue display
async function updateQueue() {
    try {
        const response = await fetch('/api/queue');
        const queue = await response.json();
        
        const queueEl = document.getElementById('upcoming-queue');
        if (queue.length > 0) {
            queueEl.innerHTML = queue.slice(0, 5).map(s => `
                <div class="queue-item">
                    <span class="ticket">${s.ticket}</span>
                    <span class="title">${escapeHtml(s.title)}</span>
                    <span class="author">by ${escapeHtml(s.author)}</span>
                </div>
            `).join('');
        } else {
            queueEl.innerHTML = '<p class="loading">Queue is empty</p>';
        }
    } catch (error) {
        console.error('Failed to fetch queue:', error);
    }
}

// Update history display
async function updateHistory() {
    try {
        const response = await fetch('/api/history');
        const history = await response.json();
        
        const historyEl = document.getElementById('recent-history');
        if (history.length > 0) {
            historyEl.innerHTML = history.map(s => `
                <div class="history-item">
                    <span class="ticket">${s.ticket}</span>
                    <span class="title">${escapeHtml(s.title)}</span>
                    <span class="time">${new Date(s.completed_at).toLocaleTimeString()}</span>
                </div>
            `).join('');
        } else {
            historyEl.innerHTML = '<p class="loading">No broadcasts yet</p>';
        }
    } catch (error) {
        console.error('Failed to fetch history:', error);
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initial load
updateStatus();
updateQueue();
updateHistory();

// Auto-refresh
setInterval(() => {
    updateStatus();
    updateQueue();
    updateHistory();
}, REFRESH_INTERVAL);
