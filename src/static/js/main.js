// Theme management

console.log('JavaScript loaded');
function toggleTheme() {
    const themeBtn = document.getElementById('theme-toggle');
    document.body.classList.toggle('theme-dark');
    const isDark = document.body.classList.contains('theme-dark');
    themeBtn.textContent = isDark ? '☀️' : '🌙';
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

// Format content
function formatContent(content, format = 'text') {
    if (format === 'markdown') {
        // Configure marked with syntax highlighting
        marked.setOptions({
            highlight: function(code, lang) {
                if (Prism.languages[lang]) {
                    return Prism.highlight(code, Prism.languages[lang], lang);
                }
                return code;
            },
            breaks: true,
            gfm: true
        });
        
        try {
            return marked.parse(content);
        } catch (error) {
            console.error('Markdown parsing error:', error);
            return content;
        }
    } else {
        // Simple example: escape HTML to prevent XSS attacks
        const div = document.createElement('div');
        div.textContent = content;
        return div.innerHTML;
    }
}

// Message handling
function addMessage(content, type = 'user', format = 'text') {
    const messages = document.getElementById('messages') || document.getElementById('api-messages');
    if (!messages) {
        console.error('No element to append messages to');
        return;
    }
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    if (type === 'assistant' && content.includes('Error')) {
        messageDiv.classList.add('error');
    }
    
    try {
        messageDiv.innerHTML = formatContent(content, format);
        
        // Apply syntax highlighting to code blocks
        if (format === 'markdown') {
            messageDiv.querySelectorAll('pre code').forEach((block) => {
                Prism.highlightElement(block);
            });
        }
        
        messages.appendChild(messageDiv);
        messages.scrollTop = messages.scrollHeight;
    } catch (error) {
        console.error('Message rendering error:', error);
        messageDiv.textContent = content;
        messages.appendChild(messageDiv);
    }
}

// Enhanced formatting controls
function setupFormatControls() {
    const formatSelect = document.getElementById('format');
    const prompt = document.getElementById('prompt');
    
    if (formatSelect && prompt) {
        formatSelect.addEventListener('change', () => {
            prompt.dataset.format = formatSelect.value;
            prompt.placeholder = `Type your ${formatSelect.value} here...`;
        });
    }
}

// Send message
async function sendMessage() {
    const promptInput = document.getElementById('prompt');
    const message = promptInput.value.trim();
    const format = promptInput.dataset.format || 'text';
    
    if (!message) {
        addMessage('Please enter a message', 'error');
        return;
    }

    addMessage(message, 'user', format);
    promptInput.value = '';

    try {
        const response = await fetch('/api/v1/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt: message })
        });

        const data = await response.json();
        if (response.ok) {
            addMessage(data.response, 'assistant', 'markdown');
            // Update statistics after successful request
            await updateStatistics();
        } else {
            addMessage(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        addMessage(`Error: ${error.message}`, 'error');
    }
}

// Initialize UI
document.addEventListener('DOMContentLoaded', () => {
    setupFormatControls();
    const themeBtn = document.getElementById('theme-toggle');
    if (themeBtn) {
        themeBtn.addEventListener('click', toggleTheme);
    }

    const theme = localStorage.getItem('theme') || 'light';
    if (theme === 'dark') {
        document.body.classList.add('theme-dark');
        themeBtn.textContent = '☀️';
    } else {
        themeBtn.textContent = '🌙';
    }
    
    // Verify CSS loading
    const styles = getComputedStyle(document.body);
    if (!styles.getPropertyValue('--primary')) {
        console.error('CSS variables not loaded');
    }

    const updateKeyBtn = document.getElementById('update-key');
    if (updateKeyBtn) {
        updateKeyBtn.addEventListener('click', updateApiKey);
    }

    const sendBtn = document.getElementById('send-btn');
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }

    // Initial statistics update
    updateStatistics();
    setInterval(updateStatistics, 30000);
});

async function updateApiKey() {
    const apiKeyInput = document.getElementById('api-key');
    const updateBtn = document.getElementById('update-key');
    const apiKey = apiKeyInput.value.trim();

    if (!apiKey) {
        addMessage('Please enter an API key', 'error');
        return;
    }

    try {
        updateBtn.disabled = true;
        const response = await fetch('/api/v1/settings/api-key', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ api_key: apiKey })
        });

        const data = await response.json();
        if (response.ok) {
            addMessage('API key updated successfully', 'success');
            apiKeyInput.value = '';
        } else {
            addMessage(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        addMessage(`Error: ${error.message}`, 'error');
    } finally {
        updateBtn.disabled = false;
    }
}

async function updateStatistics() {
    try {
        const response = await fetch('/api/v1/statistics');
        const data = await response.json();
        
        // Update number displays only
        const requestsToday = document.getElementById('requests-today');
        const rateLimit = document.getElementById('rate-limit');
        
        if (requestsToday) {
            requestsToday.textContent = data.requests_today;
        }
        if (rateLimit) {
            rateLimit.textContent = data.current_rate;
        }
    } catch (error) {
        console.error('Error updating statistics:', error);
    }
}