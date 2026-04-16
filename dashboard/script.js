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
    const grid = document.getElementById('zone-cards-grid');
    if (!grid) return;
    grid.innerHTML = '';

    data.forEach((item, index) => {
        const card = document.createElement('div');
        const clusterClass = item.cluster_detected ? 'cluster-highlight' : '';
        card.className = `zone-card ${clusterClass}`;
        card.style.animationDelay = `${index * 0.1}s`;
        
        const hotspotCoords = item.cluster_detected 
            ? `(${item.hotspot_x}, ${item.hotspot_y})`
            : 'None';

        const clusterWarning = item.cluster_detected 
            ? `<div class="cluster-warning-badge">⚠️ CLUSTER DETECTED</div>`
            : '';

        card.innerHTML = `
            <div class="zone-card-header">
                <span class="zone-name">${item.zone}</span>
                ${clusterWarning}
            </div>
            
            <div class="zone-details">
                <div class="detail-row">
                    <span class="detail-label">Count:</span>
                    <span class="detail-value">${item.count.toLocaleString()}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Density:</span>
                    <span class="detail-value">${item.density_ratio.toFixed(2)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Class:</span>
                    <span class="detail-value">${item.density_class}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Zone Risk:</span>
                    <span class="risk-badge badge-${item.risk_level.toLowerCase()}">${item.risk_level}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Cluster Risk:</span>
                    <span class="risk-badge badge-${item.cluster_risk.toLowerCase()}">${item.cluster_risk}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Hotspot:</span>
                    <span class="detail-value">${hotspotCoords}</span>
                </div>
            </div>
        `;
        grid.appendChild(card);
    });
}


/* ==================== ALERTS ==================== */

function renderAlerts(data) {
    const panel = document.getElementById('alerts-panel');
    const reds = data.filter(z => z.risk_level === "Red");
    const ambers = data.filter(z => z.risk_level === "Amber");

    // Update sidebar alert badge
    const badge = document.getElementById('alert-badge');
    const totalAlerts = reds.length + ambers.length;
    if (badge) {
        if (totalAlerts > 0) {
            badge.textContent = totalAlerts;
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    }

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

/* ==================== CV ANALYSIS FEEDS ==================== */

let lastFramesUpdate = 0;
const FRAMES_POLL_INTERVAL = 1000; // 1 second

async function fetchFrames() {
    try {
        const response = await fetch('/api/frames');
        if (!response.ok) throw new Error("Frames API Error");

        const framesData = await response.json();
        renderCVFrames(framesData);
    } catch (error) {
        console.warn("CV frames fetch failed:", error);
    }
}

function renderCVFrames(framesData) {
    const container = document.getElementById('cv-feeds-grid');
    if (!container) return; // Section not yet mounted

    // Define the frame cards to display
    const frameConfigs = [
        { key: 'tracking_A', label: 'Tracking Zone A' },
        { key: 'tracking_B', label: 'Tracking Zone B' },
        { key: 'heatmap_A', label: 'Heatmap Zone A' },
        { key: 'heatmap_B', label: 'Heatmap Zone B' },
        { key: 'risk_zones', label: 'Risk Zones (Full Frame)' }
    ];

    // Clear and rebuild grid
    container.innerHTML = '';

    frameConfigs.forEach((config, index) => {
        const base64Data = framesData[config.key];
        const card = document.createElement('div');
        card.className = 'cv-feed-card';
        card.style.animationDelay = `${index * 0.05}s`;

        if (base64Data && base64Data.trim().length > 0) {
            card.innerHTML = `
                <div class="cv-feed-label">${config.label}</div>
                <img src="data:image/jpeg;base64,${base64Data}" alt="${config.label}" class="cv-feed-image">
            `;
        } else {
            card.innerHTML = `
                <div class="cv-feed-label">${config.label}</div>
                <div class="cv-feed-placeholder">No data</div>
            `;
        }

        container.appendChild(card);
    });
}

/* ==================== ZONE FLOW TRACKING ==================== */

async function fetchFlows() {
    try {
        const response = await fetch('/api/flows');
        if (!response.ok) throw new Error("Flows API Error");

        const flowsData = await response.json();
        renderFlows(flowsData);
    } catch (error) {
        console.warn("Flows fetch failed:", error);
    }
}

function renderFlows(flowsData) {
    const container = document.getElementById('flows-table');
    if (!container) return; // Section not yet mounted

    if (!flowsData || flowsData.length === 0) {
        container.innerHTML = '<p style="padding: 20px; color: #999;">No zone flows detected yet</p>';
        return;
    }

    let html = '<div class="flows-list">';
    flowsData.forEach((flow, idx) => {
        html += `
            <div class="flow-item" style="animation-delay: ${idx * 0.05}s">
                <div class="flow-from">${flow.from}</div>
                <div class="flow-arrow">→</div>
                <div class="flow-to">${flow.to}</div>
                <div class="flow-count">${flow.count} people</div>
            </div>
        `;
    });
    html += '</div>';

    container.innerHTML = html;
}

/* ==================== HEATMAP ==================== */

function renderHeatmap(data) {
    const img = document.getElementById('heatmap-img');
    if (!img) return;
    
    // Force refresh by adding timestamp to URL
    img.src = '/api/heatmap?t=' + Date.now();
}

/* ==================== ZONE GRAPH ==================== */

function renderZoneGraph(data) {
    const canvas = document.getElementById('zoneGraph');
    if (!canvas) return; // Safety check
    
    // Set explicit canvas dimensions (not CSS-based)
    // Get container width from parent
    const containerWidth = canvas.parentElement?.offsetWidth || 600;
    canvas.width = containerWidth;
    canvas.height = 320; // Default height matching CSS
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return; // Safety check

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

/* ==================== ZONE FEED CROPPING ==================== */

// Zone coordinates from run.py (frame dimensions: 640x480)
const ZONE_COORDINATES = {
    "Zone_A": { x1: 0, y1: 0, x2: 320, y2: 480 },
    "Zone_B": { x1: 320, y1: 0, x2: 640, y2: 480 }
};
const FRAME_WIDTH = 640;
const FRAME_HEIGHT = 480;

function setupZoneFeedCropping() {
    // Apply clip-path to each zone feed to show only its region
    Object.entries(ZONE_COORDINATES).forEach(([zoneName, coords]) => {
        // Map zone name to image element ID (Zone_A -> stream-zone-a)
        const imgId = `stream-${zoneName.toLowerCase().replace('_', '-')}`;
        const img = document.getElementById(imgId);
        
        if (img) {
            // Convert pixel coordinates to percentages for clip-path
            const x1Percent = (coords.x1 / FRAME_WIDTH) * 100;
            const y1Percent = (coords.y1 / FRAME_HEIGHT) * 100;
            const x2Percent = (coords.x2 / FRAME_WIDTH) * 100;
            const y2Percent = (coords.y2 / FRAME_HEIGHT) * 100;
            
            // Apply CSS clip-path to mask image to zone region
            img.style.clipPath = `polygon(${x1Percent}% ${y1Percent}%, ${x2Percent}% ${y1Percent}%, ${x2Percent}% ${y2Percent}%, ${x1Percent}% ${y2Percent}%)`;
            
            // Ensure the image container allows clipping
            if (img.parentElement) {
                img.parentElement.style.overflow = 'hidden';
            }
        }
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

    // Setup sidebar toggle
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    const mainPanel = document.querySelector('.main-panel');
    if (sidebarToggle && sidebar && mainPanel) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            mainPanel.classList.toggle('expanded');
        });
    }

    // Live clock in topbar
    function updateClock() {
        const el = document.getElementById('topbar-clock');
        if (el) {
            el.textContent = new Date().toLocaleTimeString('en-US', {
                hour: '2-digit', minute: '2-digit', second: '2-digit'
            });
        }
    }
    updateClock();
    setInterval(updateClock, 1000);

    // Active nav highlight on scroll
    const sections = document.querySelectorAll('.page-section');
    const navItems = document.querySelectorAll('.nav-item[data-section]');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const id = entry.target.id;
                navItems.forEach(item => {
                    item.classList.toggle('active', item.dataset.section === id);
                });
            }
        });
    }, { threshold: 0.3 });
    sections.forEach(s => observer.observe(s));

    // Setup zone feed cropping to show only each zone's region
    setupZoneFeedCropping();

    // Initialize charts and data
    initCharts();
    fetchStatus();
    fetchFrames(); // Initial CV frames fetch
    fetchFlows();  // Initial zone flows fetch
    
    // Poll status every 2.5 seconds
    setInterval(fetchStatus, 2500);
    
    // Poll CV analysis frames every 1 second
    setInterval(fetchFrames, 1000);
    
    // Poll zone flows every 2.5 seconds
    setInterval(fetchFlows, 2500);
});