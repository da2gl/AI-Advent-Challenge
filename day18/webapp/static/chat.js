// Chat functionality
class TerminalChat {
    constructor() {
        this.messagesContainer = document.getElementById('chat-messages');
        this.userInput = document.getElementById('user-input');
        this.conversationHistory = [];

        this.userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        // Auto-scroll to bottom
        this.scrollToBottom();
    }

    scrollToBottom() {
        const terminal = document.getElementById('terminal');
        terminal.scrollTop = terminal.scrollHeight;
    }

    addMessage(content, type = 'user') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${type}`;

        let formattedContent = '';

        switch(type) {
            case 'user':
                formattedContent = `<span class="label">you@gemini:~$</span> ${this.escapeHtml(content)}`;
                break;
            case 'assistant':
                formattedContent = `<span class="label">assistant@gemini:</span>\n${this.formatMarkdown(content)}`;
                break;
            case 'system':
                formattedContent = `<span class="label">[SYSTEM]</span> ${this.escapeHtml(content)}`;
                break;
            case 'error':
                formattedContent = `<span class="label">[ERROR]</span> ${this.escapeHtml(content)}`;
                break;
            case 'success':
                formattedContent = `<span class="label">[SUCCESS]</span> ${this.escapeHtml(content)}`;
                break;
        }

        messageDiv.innerHTML = formattedContent;
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addLoadingMessage() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message loading';
        messageDiv.id = 'loading-message';
        messageDiv.innerHTML = '<span class="label">assistant@gemini:</span> Thinking<span class="cursor"></span>';
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
        return messageDiv;
    }

    removeLoadingMessage() {
        const loading = document.getElementById('loading-message');
        if (loading) {
            loading.remove();
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatMarkdown(text) {
        // Simple markdown formatting for terminal
        let formatted = this.escapeHtml(text);

        // Code blocks
        formatted = formatted.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            return `<div class="code-block">${code.trim()}</div>`;
        });

        // Inline code
        formatted = formatted.replace(/`([^`]+)`/g, '<span style="color: #aaffaa;">$1</span>');

        // Bold
        formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

        // Italic
        formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');

        // Line breaks
        formatted = formatted.replace(/\n/g, '<br>');

        return formatted;
    }

    async sendMessage() {
        const message = this.userInput.value.trim();
        if (!message) return;

        // Clear input
        this.userInput.value = '';

        // Add user message
        this.addMessage(message, 'user');

        // Handle commands
        if (message.startsWith('/')) {
            this.handleCommand(message);
            return;
        }

        // Send to API
        await this.sendToAPI(message);
    }

    async handleCommand(command) {
        const cmd = command.toLowerCase().trim();

        if (cmd === '/clear') {
            this.messagesContainer.innerHTML = '';
            this.conversationHistory = [];
            this.addMessage('Chat history cleared', 'success');
        } else if (cmd === '/model') {
            this.addMessage('Model selection coming soon...', 'system');
        } else if (cmd.startsWith('/deploy')) {
            const parts = command.split(/\s+/);
            const platform = parts[1] || 'railway';
            await this.triggerDeployment(platform);
        } else if (cmd === '/status') {
            await this.checkDeploymentStatus();
        } else {
            this.addMessage(`Unknown command: ${command}`, 'error');
        }
    }

    async sendToAPI(message) {
        const loading = this.addLoadingMessage();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    history: this.conversationHistory
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            this.removeLoadingMessage();

            if (data.error) {
                this.addMessage(data.error, 'error');
            } else {
                this.addMessage(data.response, 'assistant');
                this.conversationHistory = data.history;
            }
        } catch (error) {
            this.removeLoadingMessage();
            this.addMessage(`Error: ${error.message}`, 'error');
        }
    }

    async triggerDeployment(platform = 'railway') {
        this.addMessage(`Triggering deployment to ${platform}...`, 'system');

        try {
            const response = await fetch('/api/deploy', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    platform: platform
                })
            });

            const data = await response.json();

            if (data.error) {
                this.addMessage(data.error, 'error');
            } else {
                this.displayDeploymentStatus(data);
            }
        } catch (error) {
            this.addMessage(`Deployment error: ${error.message}`, 'error');
        }
    }

    async checkDeploymentStatus() {
        try {
            const response = await fetch('/api/deploy/status');
            const data = await response.json();

            this.displayDeploymentStatus(data);
        } catch (error) {
            this.addMessage(`Error fetching status: ${error.message}`, 'error');
        }
    }

    displayDeploymentStatus(data) {
        let statusHtml = '<div class="deployment-status">';
        statusHtml += '<div style="color: #00ddff; font-weight: bold;">═══ Deployment Pipeline Status ═══</div><br>';

        if (data.stages) {
            data.stages.forEach(stage => {
                const statusIcon = stage.status === 'success' ? '✓' :
                                 stage.status === 'error' ? '✗' :
                                 stage.status === 'running' ? '▶' : '○';
                statusHtml += `<div class="deployment-stage ${stage.status}">${statusIcon} ${stage.name}: ${stage.message}</div>`;
            });
        }

        // Add deployment logs if available
        if (data.deployment_logs && data.deployment_logs.length > 0) {
            statusHtml += '<br><div style="color: #888;">─────────────────────────────────</div>';
            statusHtml += '<div style="color: #ffaa00; font-weight: bold;">📋 Deployment Logs</div><br>';
            statusHtml += '<div style="color: #999; font-size: 0.9em;">';
            data.deployment_logs.forEach(log => {
                statusHtml += `${this.escapeHtml(log)}<br>`;
            });
            statusHtml += '</div>';
        }

        // Add AI recommendations if available
        if (data.ai_recommendations && !data.ai_recommendations.startsWith('AI')) {
            statusHtml += '<br><div style="color: #888;">─────────────────────────────────</div>';
            statusHtml += '<div style="color: #00ff88; font-weight: bold;">🤖 AI Recommendations</div><br>';
            statusHtml += `<div style="color: #bbb; white-space: pre-wrap;">${this.escapeHtml(data.ai_recommendations)}</div>`;
        }

        statusHtml += '<br><div style="color: #888;">─────────────────────────────────</div>';
        statusHtml += `<div style="color: #aaa;">Overall Status: ${data.status || 'Unknown'}</div>`;
        statusHtml += '</div>';

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message message-system';
        messageDiv.innerHTML = statusHtml;
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }
}

// Initialize chat when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.chat = new TerminalChat();
});
