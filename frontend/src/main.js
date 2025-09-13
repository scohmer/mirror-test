// Main JavaScript file for the dashboard
console.log('Dashboard initialized');

// DOM elements
const statusGrid = document.getElementById('status-grid');
const triggerTestBtn = document.getElementById('trigger-test-btn');
const lastUpdatedSpan = document.getElementById('last-updated');

// WebSocket connection to backend (will be established after initial load)
let ws = null;

// Fetch and display repository list from backend
async function loadRepositoryList() {
    try {
        const response = await fetch('/api/v1/test/test'); // This endpoint should return the list of repositories to test
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Repository list:', data);
        updateDashboard(data); // Display the repository list on the dashboard
    } catch (error) {
        console.error('Error loading repository list:', error);
        // Fallback to a mock implementation for demonstration
        updateDashboard([
            { distribution: 'Debian', version: '7', status: 'running', repository: 'http://deb.debian.org/debian' },
            { distribution: 'Debian', version: '8', status: 'success', repository: 'http://deb.debian.org/debian' },
            { distribution: 'Ubuntu', version: '20.04', status: 'failure', repository: 'http://archive.ubuntu.com/ubuntu' }
        ]);
    }
}

// Simulate getting test results from WebSocket (since we're not running full backend)
function simulateWebSocketData() {
    // This would normally come from the actual WebSocket connection
    const mockResults = [
        { distribution: 'Debian', version: '7', status: 'running', repository: 'http://deb.debian.org/debian' },
        { distribution: 'Debian', version: '8', status: 'success', repository: 'http://deb.debian.org/debian' },
        { distribution: 'Ubuntu', version: '20.04', status: 'failure', repository: 'http://archive.ubuntu.com/ubuntu' },
        { distribution: 'Ubuntu', version: '22.04', status: 'success', repository: 'http://archive.ubuntu.com/ubuntu' },
        { distribution: 'Kali', version: 'kali-rolling', status: 'running', repository: 'http://kali.download/kali' }
    ];
    updateDashboard(mockResults);
}


// Update the dashboard with new data
function updateDashboard(data) {
    // Clear existing grid
    statusGrid.innerHTML = '';
    
    // Update last updated time
    const now = new Date();
    lastUpdatedSpan.textContent = now.toLocaleString();
    
    // Create grid items for each repository
    data.forEach(repo => {
        const repoElement = document.createElement('div');
        repoElement.className = 'status-card';
        
        // Determine status class (functional, warning, error)
        let statusClass = '';
        let statusIcon = '';
        switch(repo.status) {
            case 'success':
                statusClass = 'success';
                statusIcon = '✓';
                break;
            case 'failure':
                statusClass = 'failure';
                statusIcon = '✗';
                break;
            case 'partial':
                statusClass = 'warning';
                statusIcon = '⚠';
                break;
            case 'running':
                statusClass = 'running';
                statusIcon = '↻';
                break;
            default:
                statusClass = 'running';
                statusIcon = '?';
        }
        
        // Build detailed test results if available
        let testDetailsHtml = '';
        if (repo.test_details) {
            testDetailsHtml = `
                <div class="test-details">
                    <div class="test-item">
                        <span class="test-name">Connectivity:</span>
                        <span class="test-status ${repo.test_details.connectivity.status}">${repo.test_details.connectivity.status}</span>
                        <span class="test-duration">(${repo.test_details.connectivity.duration}s)</span>
                    </div>
                    <div class="test-item">
                        <span class="test-name">Update:</span>
                        <span class="test-status ${repo.test_details.update.status}">${repo.test_details.update.status}</span>
                        <span class="test-duration">(${repo.test_details.update.duration}s)</span>
                    </div>
                    <div class="test-item">
                        <span class="test-name">Install:</span>
                        <span class="test-status ${repo.test_details.install.status}">${repo.test_details.install.status}</span>
                        <span class="test-duration">(${repo.test_details.install.duration}s)</span>
                    </div>
                </div>
            `;
        }

        repoElement.innerHTML = `
            <h3>${repo.distribution} ${repo.version}</h3>
            <div class="status-icon ${statusClass}">${statusIcon}</div>
            <p>Repository: ${repo.repository}</p>
            <p>Overall Status: <span class="status-indicator ${statusClass}"></span> ${repo.status}</p>
            <p>Total Duration: ${repo.duration_seconds ? repo.duration_seconds + 's' : '-'}</p>
            ${testDetailsHtml}
            ${repo.error_message ? `<p class="error-message">Error: ${repo.error_message}</p>` : ''}
        `;
        
        statusGrid.appendChild(repoElement);
    });
}

// Establish WebSocket connection when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // Load repository list first
    loadRepositoryList();
    
    // Connect to the test-specific WebSocket endpoint through nginx proxy
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host; // This includes hostname and port
    ws = new WebSocket(`${wsProtocol}//${wsHost}/test/ws`);
    ws.onopen = () => {
        console.log('Connected to backend test WebSocket');
    };

    ws.onmessage = (event) => {
        console.log('Received data:', event.data);
        // Try to parse as JSON, fallback to treating as plain text
        try {
            const data = JSON.parse(event.data);
            console.log('Parsed JSON data:', data);
            // Only update dashboard if the message contains repository status data
            if (data && Array.isArray(data)) {
                updateDashboard(data);
            } else {
                console.log('Received non-repository data:', data);
            }
        } catch (e) {
            console.log('Received plain text data:', event.data);
            // If it's not JSON, we might still want to process it or ignore it
            // For now, just log and continue
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        // Fallback to polling approach if WebSocket fails
        console.log('Falling back to polling for updates...');
        setInterval(loadRepositoryList, 5000); // Poll every 5 seconds
    };

    ws.onclose = () => {
        console.log('Disconnected from backend WebSocket');
    };
});

// Trigger manual test
triggerTestBtn.addEventListener('click', () => {
    fetch('/api/v1/test/test', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('Manual test triggered:', data);
        // Update the dashboard with the new result
        updateDashboard([data]);
    })
    .catch(error => {
        console.error('Error triggering manual test:', error);
    });
});
