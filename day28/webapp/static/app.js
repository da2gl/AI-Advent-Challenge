// God Agent - Frontend Application Logic

// Configuration
const API_BASE = window.location.origin;
const WS_BASE = `ws://${window.location.host}`;

// State
let conversationHistory = [];
let ws = null;
let wsReconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    setupTabs();
    setupChat();
    setupTasks();
    setupCodeAnalysis();
    setupDeployment();
    setupRAG();
    setupStatus();
    setupTheme();
    initWebSocket();
}

// ═══════════════════════════════════════════════════════════
// TAB NAVIGATION
// ═══════════════════════════════════════════════════════════

function setupTabs() {
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;

            // Update active states
            navButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            tabContents.forEach(tab => {
                tab.classList.remove('active');
                if (tab.id === `${tabName}-tab`) {
                    tab.classList.add('active');
                }
            });

            // Load data for specific tabs
            if (tabName === 'tasks') {
                loadTasks();
            } else if (tabName === 'status') {
                loadStatus();
            }
        });
    });
}

// ═══════════════════════════════════════════════════════════
// THEME TOGGLE
// ═══════════════════════════════════════════════════════════

function setupTheme() {
    const themeBtn = document.getElementById('theme-btn');
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    themeBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
    });
}

function updateThemeIcon(theme) {
    const icon = document.querySelector('#theme-btn i');
    icon.className = theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
}

// ═══════════════════════════════════════════════════════════
// WEBSOCKET CHAT
// ═══════════════════════════════════════════════════════════

function initWebSocket() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        return;
    }

    ws = new WebSocket(`${WS_BASE}/ws/chat`);

    ws.onopen = () => {
        console.log('WebSocket connected');
        wsReconnectAttempts = 0;
        showNotification('Connected to God Agent', 'success');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.error) {
            addMessageToChat('system', `Error: ${data.error}`);
        } else {
            addMessageToChat('assistant', data.response);
            conversationHistory.push({
                role: 'model',
                parts: [{ text: data.response }]
            });
        }
        hideLoading();
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        showNotification('WebSocket connection error', 'error');
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected');
        if (wsReconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            wsReconnectAttempts++;
            setTimeout(() => {
                console.log(`Reconnecting... (attempt ${wsReconnectAttempts})`);
                initWebSocket();
            }, 2000 * wsReconnectAttempts);
        } else {
            showNotification('WebSocket connection lost. Using HTTP fallback.', 'warning');
        }
    };
}

// ═══════════════════════════════════════════════════════════
// CHAT FUNCTIONALITY
// ═══════════════════════════════════════════════════════════

function setupChat() {
    const sendBtn = document.getElementById('send-btn');
    const chatInput = document.getElementById('chat-input');
    const voiceBtn = document.getElementById('voice-btn');
    const clearBtn = document.getElementById('clear-chat');
    const tempSlider = document.getElementById('temperature');
    const tempValue = document.getElementById('temp-value');

    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    voiceBtn.addEventListener('click', () => {
        showNotification('Voice input not yet implemented in web interface', 'info');
    });

    clearBtn.addEventListener('click', () => {
        conversationHistory = [];
        document.getElementById('chat-messages').innerHTML = `
            <div class="message system">
                <div class="message-content">
                    <strong>God Agent:</strong> Chat cleared. How can I help you?
                </div>
            </div>
        `;
    });

    tempSlider.addEventListener('input', (e) => {
        tempValue.textContent = e.target.value;
    });
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();

    if (!message) return;

    const useRag = document.getElementById('use-rag').checked;
    const temperature = parseFloat(document.getElementById('temperature').value);

    // Add user message to chat
    addMessageToChat('user', message);
    conversationHistory.push({
        role: 'user',
        parts: [{ text: message }]
    });

    input.value = '';

    // Show loading
    showLoading();

    // Send via WebSocket if available, otherwise use HTTP
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            message,
            use_rag: useRag,
            temperature,
            history: conversationHistory.slice(0, -1) // Don't include current message
        }));
    } else {
        // Fallback to HTTP
        try {
            const response = await fetch(`${API_BASE}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message,
                    use_rag: useRag,
                    temperature,
                    history: conversationHistory.slice(0, -1)
                })
            });

            const data = await response.json();

            if (response.ok) {
                addMessageToChat('assistant', data.response);
                conversationHistory.push({
                    role: 'model',
                    content: data.response
                });
            } else {
                addMessageToChat('system', `Error: ${data.detail || 'Unknown error'}`);
            }
        } catch (error) {
            addMessageToChat('system', `Error: ${error.message}`);
        } finally {
            hideLoading();
        }
    }
}

function addMessageToChat(role, content) {
    const messagesDiv = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    if (role === 'user') {
        contentDiv.innerHTML = `<strong>You:</strong> ${escapeHtml(content)}`;
    } else if (role === 'assistant') {
        contentDiv.innerHTML = `<strong>God Agent:</strong> ${formatMarkdown(content)}`;
    } else {
        contentDiv.innerHTML = content;
    }

    messageDiv.appendChild(contentDiv);
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// ═══════════════════════════════════════════════════════════
// TASK MANAGEMENT
// ═══════════════════════════════════════════════════════════

function setupTasks() {
    const newTaskBtn = document.getElementById('new-task-btn');
    const refreshBtn = document.getElementById('refresh-tasks-btn');
    const modal = document.getElementById('task-modal');
    const closeBtn = modal.querySelector('.close');
    const form = document.getElementById('task-form');

    newTaskBtn.addEventListener('click', () => {
        modal.style.display = 'block';
    });

    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    refreshBtn.addEventListener('click', loadTasks);

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const taskData = {
            name: document.getElementById('task-name').value,
            mcp_tool: document.getElementById('task-tool').value,
            tool_args: JSON.parse(document.getElementById('task-args').value || '{}'),
            schedule_type: document.getElementById('task-schedule-type').value,
            schedule_value: document.getElementById('task-schedule-value').value,
            use_ai_summary: document.getElementById('task-ai-summary').checked,
            notification_level: document.getElementById('task-notification').value
        };

        try {
            showLoading();
            const response = await fetch(`${API_BASE}/api/tasks`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(taskData)
            });

            const data = await response.json();

            if (response.ok) {
                showNotification('Task created successfully!', 'success');
                modal.style.display = 'none';
                form.reset();
                loadTasks();
            } else {
                showNotification(`Error: ${data.detail}`, 'error');
            }
        } catch (error) {
            showNotification(`Error: ${error.message}`, 'error');
        } finally {
            hideLoading();
        }
    });
}

async function loadTasks() {
    try {
        showLoading();
        const response = await fetch(`${API_BASE}/api/tasks`);
        const data = await response.json();

        const tasksList = document.getElementById('tasks-list');
        tasksList.innerHTML = '';

        if (data.tasks.length === 0) {
            tasksList.innerHTML = '<p>No tasks found. Create your first task!</p>';
            return;
        }

        data.tasks.forEach(task => {
            const taskDiv = document.createElement('div');
            taskDiv.className = 'task-item';
            taskDiv.innerHTML = `
                <div class="task-info">
                    <h4>${task.name}</h4>
                    <div class="task-details">
                        <p><strong>Tool:</strong> ${task.mcp_tool}</p>
                        <p><strong>Schedule:</strong> ${task.schedule_type} - ${task.schedule_value}</p>
                        <p><strong>Last Run:</strong> ${task.last_run || 'Never'}</p>
                        <p><strong>Status:</strong> ${task.enabled ? 'Enabled' : 'Disabled'}</p>
                    </div>
                </div>
                <div class="task-actions">
                    <button class="btn btn-primary" onclick="runTask(${task.id})">
                        <i class="fas fa-play"></i> Run
                    </button>
                    <button class="btn btn-secondary" onclick="deleteTask(${task.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            tasksList.appendChild(taskDiv);
        });
    } catch (error) {
        showNotification(`Error loading tasks: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

async function runTask(taskId) {
    try {
        showLoading();
        const response = await fetch(`${API_BASE}/api/tasks/${taskId}/run`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            showNotification('Task triggered successfully!', 'success');
        } else {
            showNotification(`Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) return;

    try {
        showLoading();
        const response = await fetch(`${API_BASE}/api/tasks/${taskId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (response.ok) {
            showNotification('Task deleted successfully!', 'success');
            loadTasks();
        } else {
            showNotification(`Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

// ═══════════════════════════════════════════════════════════
// CODE ANALYSIS
// ═══════════════════════════════════════════════════════════

function setupCodeAnalysis() {
    const analyzeBtn = document.getElementById('analyze-code-btn');
    const fileInput = document.getElementById('code-file-input');

    analyzeBtn.addEventListener('click', analyzeCode);

    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const text = await file.text();
        document.getElementById('code-input').value = text;
        document.getElementById('code-filepath').value = file.name;
    });
}

async function analyzeCode() {
    const code = document.getElementById('code-input').value.trim();
    const filePath = document.getElementById('code-filepath').value;

    if (!code) {
        showNotification('Please enter code to analyze', 'warning');
        return;
    }

    try {
        showLoading();
        const response = await fetch(`${API_BASE}/api/code/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, file_path: filePath })
        });

        const data = await response.json();

        if (response.ok) {
            displayCodeAnalysis(data.analysis);
        } else {
            showNotification(`Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

function displayCodeAnalysis(analysis) {
    const resultsDiv = document.getElementById('code-results');

    const qualityClass = analysis.quality_score >= 80 ? 'good' :
                        analysis.quality_score >= 60 ? 'medium' : 'bad';

    resultsDiv.innerHTML = `
        <h3>Analysis Results</h3>
        <div class="quality-score ${qualityClass}">
            Quality Score: ${analysis.quality_score.toFixed(1)}/100
        </div>

        <h4>Metadata</h4>
        <p><strong>Language:</strong> ${analysis.metadata.language}</p>
        <p><strong>Total Lines:</strong> ${analysis.metadata.total_lines}</p>
        <p><strong>Code Lines:</strong> ${analysis.metadata.code_lines}</p>
        <p><strong>Functions:</strong> ${analysis.metadata.functions}</p>
        <p><strong>Classes:</strong> ${analysis.metadata.classes}</p>

        <h4>Static Analysis</h4>
        <p><strong>Complexity Score:</strong> ${analysis.static_analysis.complexity_score}</p>
        <p><strong>Issues Found:</strong> ${analysis.static_analysis.issues.length}</p>
        <p><strong>Code Smells:</strong> ${analysis.static_analysis.code_smells.length}</p>

        ${analysis.recommendations.length > 0 ? `
            <h4>Recommendations</h4>
            <ul class="recommendations">
                ${analysis.recommendations.map(r => `<li>${r}</li>`).join('')}
            </ul>
        ` : ''}

        ${analysis.ai_documentation ? `
            <h4>AI Analysis</h4>
            <p>${analysis.ai_documentation}</p>
        ` : ''}
    `;
}

// ═══════════════════════════════════════════════════════════
// DEPLOYMENT
// ═══════════════════════════════════════════════════════════

function setupDeployment() {
    const deployBtn = document.getElementById('deploy-btn');
    deployBtn.addEventListener('click', runDeployment);
}

async function runDeployment() {
    const platform = document.getElementById('deploy-platform').value;

    try {
        showLoading();
        const response = await fetch(`${API_BASE}/api/deploy`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform })
        });

        const data = await response.json();

        if (response.ok) {
            displayDeploymentResults(data.deployment);
            showNotification('Deployment completed!', 'success');
        } else {
            showNotification(`Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

function displayDeploymentResults(deployment) {
    const stagesDiv = document.getElementById('deploy-stages');
    const resultsDiv = document.getElementById('deploy-results');

    // Display stages
    stagesDiv.innerHTML = '<h3>Pipeline Stages</h3>';
    deployment.stages.forEach(stage => {
        const statusMap = {
            pending: { icon: 'fas fa-circle', class: 'pending' },
            running: { icon: 'fas fa-spinner fa-spin', class: 'running' },
            success: { icon: 'fas fa-check-circle', class: 'success' },
            error: { icon: 'fas fa-times-circle', class: 'error' }
        };
        const status = statusMap[stage.status] || statusMap.pending;

        stagesDiv.innerHTML += `
            <div class="stage-item">
                <i class="${status.icon} stage-icon ${status.class}"></i>
                <div>
                    <strong>${stage.name}</strong>
                    <p>${stage.message}</p>
                </div>
            </div>
        `;
    });

    // Display AI recommendations
    if (deployment.results.ai_recommendations) {
        resultsDiv.innerHTML = `
            <h3>AI Recommendations</h3>
            <p>${deployment.results.ai_recommendations}</p>
        `;
    }
}

// ═══════════════════════════════════════════════════════════
// RAG KNOWLEDGE BASE
// ═══════════════════════════════════════════════════════════

function setupRAG() {
    const indexBtn = document.getElementById('index-btn');
    const searchBtn = document.getElementById('search-btn');
    const fileInput = document.getElementById('rag-file-input');

    indexBtn.addEventListener('click', indexDocument);
    searchBtn.addEventListener('click', searchKnowledge);

    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const text = await file.text();
        document.getElementById('rag-content').value = text;
    });
}

async function indexDocument() {
    const content = document.getElementById('rag-content').value.trim();

    if (!content) {
        showNotification('Please enter content to index', 'warning');
        return;
    }

    try {
        showLoading();
        const response = await fetch(`${API_BASE}/api/rag/index`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content, metadata: {} })
        });

        const data = await response.json();

        if (response.ok) {
            showNotification('Document indexed successfully!', 'success');
            document.getElementById('rag-content').value = '';
        } else {
            showNotification(`Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

async function searchKnowledge() {
    const query = document.getElementById('rag-query').value.trim();

    if (!query) {
        showNotification('Please enter a search query', 'warning');
        return;
    }

    try {
        showLoading();
        const response = await fetch(`${API_BASE}/api/rag/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, top_k: 5 })
        });

        const data = await response.json();

        if (response.ok) {
            displayRAGResults(data.results);
        } else {
            showNotification(`Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

function displayRAGResults(results) {
    const resultsDiv = document.getElementById('rag-results');

    if (results.length === 0) {
        resultsDiv.innerHTML = '<p>No results found.</p>';
        return;
    }

    resultsDiv.innerHTML = '<h4>Search Results</h4>';
    results.forEach((result, i) => {
        resultsDiv.innerHTML += `
            <div class="rag-result-item">
                <strong>Result ${i + 1}</strong>
                <p>${escapeHtml(result.content.substring(0, 200))}...</p>
                ${result.score ? `<small>Score: ${result.score.toFixed(3)}</small>` : ''}
            </div>
        `;
    });
}

// ═══════════════════════════════════════════════════════════
// STATUS MONITORING
// ═══════════════════════════════════════════════════════════

function setupStatus() {
    const refreshBtn = document.getElementById('refresh-status-btn');
    refreshBtn.addEventListener('click', loadStatus);
}

async function loadStatus() {
    try {
        showLoading();
        const response = await fetch(`${API_BASE}/api/status`);
        const data = await response.json();

        if (response.ok) {
            displayStatus(data.status);
        } else {
            showNotification(`Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

function displayStatus(status) {
    const statusDiv = document.getElementById('status-display');

    statusDiv.innerHTML = `
        <div class="status-card">
            <h3>System Overview</h3>
            <div class="status-grid">
                <div class="status-item">
                    <div class="status-value">${Math.floor(status.uptime_seconds)}s</div>
                    <div class="status-label">Uptime</div>
                </div>
                <div class="status-item">
                    <div class="status-value">${status.llm_provider}</div>
                    <div class="status-label">LLM Provider</div>
                </div>
                <div class="status-item">
                    <div class="status-value">${status.conversation_count}</div>
                    <div class="status-label">Conversations</div>
                </div>
                <div class="status-item">
                    <div class="status-value">${status.active_modules.length}</div>
                    <div class="status-label">Active Modules</div>
                </div>
            </div>
        </div>

        <div class="status-card">
            <h3>Active Modules</h3>
            <ul>
                ${status.active_modules.map(m => `<li>${m}</li>`).join('')}
            </ul>
        </div>

        ${status.task_scheduler ? `
            <div class="status-card">
                <h3>Task Scheduler</h3>
                <div class="status-grid">
                    <div class="status-item">
                        <div class="status-value">${status.task_scheduler.active_jobs}</div>
                        <div class="status-label">Active Jobs</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value">${status.task_scheduler.tasks_executed}</div>
                        <div class="status-label">Tasks Executed</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value">${status.task_scheduler.tasks_failed}</div>
                        <div class="status-label">Tasks Failed</div>
                    </div>
                </div>
            </div>
        ` : ''}
    `;
}

// ═══════════════════════════════════════════════════════════
// UTILITY FUNCTIONS
// ═══════════════════════════════════════════════════════════

function showLoading() {
    document.getElementById('loading-overlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
}

function showNotification(message, type = 'info') {
    // Simple notification - could be enhanced with a toast library
    const colors = {
        success: '#10b981',
        error: '#ef4444',
        warning: '#f59e0b',
        info: '#6366f1'
    };

    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background: ${colors[type]};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        z-index: 1000;
        animation: slideIn 0.3s;
    `;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatMarkdown(text) {
    // Simple markdown formatting
    return escapeHtml(text)
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);
