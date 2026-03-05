async function fetchStatus() {
    try {
        let resp = await fetch('/api/status');
        if (!resp.ok) {
            console.error('API Error:', resp.status, resp.statusText);
            throw new Error(`HTTP ${resp.status}`);
        }
        let data = await resp.json();
        console.log('Status data:', data);
        
        // Update API status
        const statusSpan = document.getElementById('api-status');
        statusSpan.textContent = 'Online';
        statusSpan.className = 'online';
        
        // Update last update time
        const now = new Date().toLocaleTimeString();
        document.getElementById('last-update').textContent = now;
        
        if (Array.isArray(data) && data.length > 0) {
            renderStatus(data);
            renderAlerts(data);
        } else {
            document.querySelector('#status-table tbody').innerHTML = '<tr><td colspan="4" style="text-align:center">Waiting for detection data...</td></tr>';
            document.getElementById('alerts-panel').innerHTML = '<p style="color: #666;">No data yet - detection loop may not be running</p>';
        }
    } catch (e) {
        console.error('fetch error:', e);
        const statusSpan = document.getElementById('api-status');
        statusSpan.textContent = 'Offline';
        statusSpan.className = 'offline';
        const errorMsg = `Connection Error: ${e.message}`;
        document.getElementById('alerts-panel').innerHTML = `<p style="color: #e74c3c; font-weight: bold;">${errorMsg}</p>`;
    }
}

function renderStatus(data) {
    const tbody = document.querySelector('#status-table tbody');
    tbody.innerHTML = '';
    data.forEach(item => {
        const tr = document.createElement('tr');
        const level = item.risk_level ? item.risk_level.toLowerCase() : 'green';
        tr.className = level;
        tr.innerHTML = `
            <td>${item.zone || 'N/A'}</td>
            <td>${item.count || 0}</td>
            <td>${item.density_ratio ? item.density_ratio.toFixed(2) : '0.00'}</td>
            <td>${item.risk_level || 'N/A'}</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderAlerts(data) {
    const panel = document.getElementById('alerts-panel');
    const reds = data.filter(i => i.risk_level === 'Red');
    if (reds.length === 0) {
        panel.innerText = 'No alerts';
    } else {
        panel.innerHTML = reds.map(i => `<div style="color: #e74c3c; font-weight: bold;">🚨 ${i.zone}: RED ALERT!</div>`).join('');
    }
}

// Initial fetch and set up auto-refresh
console.log('Dashboard initialized, fetching status...');
fetchStatus();
setInterval(fetchStatus, 5000);

