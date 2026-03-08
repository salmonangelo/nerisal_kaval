let crowdChart, riskChart;
let chartLabels = [];
let chartData = [];

/* ==================== THEME MANAGEMENT ==================== */

function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    updateChartsTheme();
}

function updateChartsTheme() {
    if (crowdChart) crowdChart.destroy();
    if (riskChart) riskChart.destroy();
    
    initCharts();
}

function getChartColors() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
        textColor: isDark ? '#cbd5e1' : '#666666',
        gridColor: isDark ? 'rgba(148, 163, 184, 0.1)' : 'rgba(0, 0, 0, 0.05)',
        primaryLine: isDark ? '#60a5fa' : '#4f46e5',
        primaryFill: isDark ? 'rgba(96, 165, 250, 0.1)' : 'rgba(79, 70, 229, 0.1)',
    };
}

/* ==================== INIT CHARTS ==================== */

function initCharts() {
    const colors = getChartColors();
    
    const crowdCtx = document.getElementById('crowdChart').getContext('2d');
    crowdChart = new Chart(crowdCtx, {
        type: 'line',
        data: {
            labels: chartLabels,
            datasets: [{
                label: 'Total Crowd',
                data: chartData,
                borderColor: colors.primaryLine,
                backgroundColor: colors.primaryFill,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: colors.primaryLine,
                pointBorderColor: 'transparent',
                pointHoverRadius: 5,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    border: { display: false },
                    grid: { color: colors.gridColor },
                    ticks: { color: colors.textColor }
                },
                x: {
                    border: { display: false },
                    grid: { display: false },
                    ticks: { color: colors.textColor }
                }
            }
        }
    });

    const riskCtx = document.getElementById('riskChart').getContext('2d');
    riskChart = new Chart(riskCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: []
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    border: { display: false },
                    grid: { color: colors.gridColor },
                    ticks: { color: colors.textColor }
                },
                y: {
                    border: { display: false },
                    grid: { display: false },
                    ticks: { color: colors.textColor }
                }
            }
        }
    });
}

/* ==================== FETCH STATUS ==================== */

async function fetchStatus() {
    try {
        const response = await fetch('/api/status');
        if (!response.ok) throw new Error("API Error");

        const data = await response.json();

        updateSystemStatus(true);
        updateLastUpdate();

        if (Array.isArray(data) && data.length > 0) {
            renderStatus(data);
            renderAlerts(data);
            updateKPIs(data);
            renderHeatmap(data);
            updateRiskChart(data);
            renderZoneGraph(data);
        }

    } catch (error) {
        updateSystemStatus(false);
    }
}

/* ==================== SYSTEM STATUS ==================== */

function updateSystemStatus(isOnline) {
    const status = document.getElementById('api-status');
    if (isOnline) {
        status.classList.add('online');
        status.querySelector('.status-text').textContent = "System Online";
    } else {
        status.classList.remove('online');
        status.querySelector('.status-text').textContent = "System Offline";
    }
}

function updateLastUpdate() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit' 
    });
    document.getElementById('last-update').textContent = timeStr;
}

/* ==================== KPI UPDATE ==================== */

function updateKPIs(data) {
    const total = data.reduce((sum, z) => sum + z.count, 0);
    const redZones = data.filter(z => z.risk_level === "Red").length;

    document.getElementById('total-count').textContent = total.toLocaleString();
    document.getElementById('high-risk-count').textContent = redZones;

    updateChart(total);
}

/* ==================== LIVE TREND ==================== */

function updateChart(total) {
    const time = new Date().toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    chartLabels.push(time);
    chartData.push(total);

    if (chartLabels.length > 20) {
        chartLabels.shift();
        chartData.shift();
    }

    crowdChart.data.labels = chartLabels;
    crowdChart.data.datasets[0].data = chartData;
    crowdChart.update('none');
}

/* ==================== RISK BAR ==================== */

function updateRiskChart(data) {
    riskChart.data.labels = data.map(z => z.zone);
    riskChart.data.datasets[0].data = data.map(z => 
        z.risk_level === "Red" ? 2 : z.risk_level === "Amber" ? 1 : 0
    );

    riskChart.data.datasets[0].backgroundColor = data.map(z => 
        z.risk_level === "Red" ? '#ef4444' :
        z.risk_level === "Amber" ? '#f59e0b' : '#10b981'
    );

    riskChart.update();
}

/* ==================== TABLE ==================== */

function renderStatus(data) {
    const tbody = document.querySelector('#status-table tbody');
    tbody.innerHTML = '';

    data.forEach((item, index) => {
        const tr = document.createElement('tr');
        tr.style.animationDelay = `${index * 0.05}s`;
        
        tr.innerHTML = `
            <td><strong>${item.zone}</strong></td>
            <td>${item.count.toLocaleString()}</td>
            <td>${item.density_ratio.toFixed(2)}</td>
            <td>
                <span class="badge ${item.risk_level.toLowerCase()}">
                    ${item.risk_level}
                </span>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

/* ==================== ALERTS ==================== */

function renderAlerts(data) {
    const panel = document.getElementById('alerts-panel');
    const reds = data.filter(z => z.risk_level === "Red");
    const ambers = data.filter(z => z.risk_level === "Amber");

    if (reds.length === 0 && ambers.length === 0) {
        panel.innerHTML = '<p class="nominal-state">✓ System nominal</p>';
    } else {
        let alertsHtml = '';
        
        reds.forEach((z, idx) => {
            alertsHtml += `
                <div class="alert-item" style="animation-delay: ${idx * 0.1}s">
                    🚨 Zone ${z.zone} is CRITICAL
                </div>
            `;
        });
        
        ambers.forEach((z, idx) => {
            alertsHtml += `
                <div class="alert-item" style="animation-delay: ${(reds.length + idx) * 0.1}s">
                    ⚠️ Zone ${z.zone} is elevated
                </div>
            `;
        });
        
        panel.innerHTML = alertsHtml;
    }
}

/* ==================== HEATMAP ==================== */

function renderHeatmap(data) {
    const grid = document.getElementById('heatmap-grid');
    grid.innerHTML = '';

    data.forEach((zone, index) => {
        const cell = document.createElement('div');
        cell.className = 'heat-cell';
        cell.style.animationDelay = `${index * 0.02}s`;

        const intensity = Math.min(zone.density_ratio, 1);
        const red = Math.floor(255 * intensity);
        const green = Math.floor(255 * (1 - intensity));
        const blue = 50;

        cell.style.backgroundColor = `rgb(${red},${green},${blue})`;
        cell.title = `${zone.zone}: ${(intensity * 100).toFixed(1)}%`;
        
        grid.appendChild(cell);
    });
}

/* ==================== ZONE GRAPH ==================== */

function renderZoneGraph(data) {
    const canvas = document.getElementById('zoneGraph');
    const ctx = canvas.getContext('2d');
    
    // Set canvas size
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    const zones = data.map(z => ({ 
        name: z.zone, 
        risk: z.risk_level 
    }));

    // Calculate positions in circle
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(canvas.width, canvas.height) / 3;

    const positions = zones.map((zone, i) => {
        const angle = (i / zones.length) * Math.PI * 2;
        return {
            ...zone,
            x: centerX + radius * Math.cos(angle),
            y: centerY + radius * Math.sin(angle)
        };
    });

    // Draw connections between all zones
    ctx.strokeStyle = '#cbd5e1';
    ctx.lineWidth = 2;
    ctx.globalAlpha = 0.5;

    for (let i = 0; i < positions.length; i++) {
        for (let j = i + 1; j < positions.length; j++) {
            ctx.beginPath();
            ctx.moveTo(positions[i].x, positions[i].y);
            ctx.lineTo(positions[j].x, positions[j].y);
            ctx.stroke();
        }
    }

    ctx.globalAlpha = 1;

    // Draw zone nodes
    positions.forEach(zone => {
        const color = zone.risk === 'Red' ? '#ef4444' : 
                     zone.risk === 'Amber' ? '#f59e0b' : '#10b981';

        // Node circle
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(zone.x, zone.y, 25, 0, Math.PI * 2);
        ctx.fill();

        // Node border
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 3;
        ctx.stroke();

        // Zone label
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 12px Poppins';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(zone.name, zone.x, zone.y);
    });
}

/* ==================== INITIALIZATION ==================== */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme
    initializeTheme();

    // Setup theme toggle
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }

    // Initialize charts and data
    initCharts();
    fetchStatus();
    setInterval(fetchStatus, 2500);
});