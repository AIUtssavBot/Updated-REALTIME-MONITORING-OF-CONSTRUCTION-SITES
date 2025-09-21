// Violations Analysis Page JavaScript
let violationsData = [];
let filteredViolations = [];
let charts = {};

// DOM elements
const totalViolationsEl = document.getElementById('total-violations');
const safetyViolationsEl = document.getElementById('safety-violations');
const proximityViolationsEl = document.getElementById('proximity-violations');
const resolvedViolationsEl = document.getElementById('resolved-violations');
const violationsTableBody = document.getElementById('violations-table-body');
const dateFilter = document.getElementById('date-filter');
const cameraFilter = document.getElementById('camera-filter');
const violationTypeFilter = document.getElementById('violation-type');
const applyFiltersBtn = document.getElementById('apply-filters');
const exportDataBtn = document.getElementById('export-data');
const refreshViolationsBtn = document.getElementById('refresh-violations');
const clearViolationsBtn = document.getElementById('clear-violations');

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    loadViolationsData();
    setupEventListeners();
    updateSummaryCards();
    setupRealTimeSync();
    highlightActiveNavLink();
});

// Highlight active navigation link
function highlightActiveNavLink() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

// Setup real-time synchronization
function setupRealTimeSync() {
    // Check for new violations every 3 seconds
    setInterval(async () => {
        // First try to load from global storage (real-time data from dashboard)
        const hasGlobalData = loadViolationsFromGlobal();
        
        if (!hasGlobalData) {
            // If no global data, refresh from database
            await loadViolationsData();
        }
        
        // Update UI components
        updateSummaryCards();
        updateCharts();
    }, 3000);
}

// Setup event listeners
function setupEventListeners() {
    applyFiltersBtn.addEventListener('click', applyFilters);
    exportDataBtn.addEventListener('click', exportData);
    refreshViolationsBtn.addEventListener('click', loadViolationsData);
    clearViolationsBtn.addEventListener('click', clearAllViolations);
    
    // Auto-refresh every 30 seconds
    setInterval(loadViolationsData, 30000);
}

// Load violations data from server
async function loadViolationsData() {
    try {
        // Build query parameters
        const params = new URLSearchParams();
        const dateFilter = document.getElementById('date-filter').value;
        const cameraFilter = document.getElementById('camera-filter').value;
        const violationType = document.getElementById('violation-type').value;
        
        if (cameraFilter !== 'all') {
            params.append('camera_id', cameraFilter);
        }
        if (violationType !== 'all') {
            params.append('type', violationType);
        }
        
        const response = await fetch(`/api/violations?${params.toString()}`);
        if (response.ok) {
            violationsData = await response.json();
            applyFilters();
        } else {
            console.error('Failed to load violations data');
            violationsData = [];
            applyFilters();
        }
    } catch (error) {
        console.error('Error loading violations:', error);
        violationsData = [];
        applyFilters();
    }
}

// Load violations from global storage (real-time data from dashboard)
function loadViolationsFromGlobal() {
    if (window.violationData && window.violationData.all.length > 0) {
        violationsData = [...window.violationData.all];
        applyFilters();
        return true;
    }
    return false;
}

// Apply filters to violations data
function applyFilters() {
    let filtered = [...violationsData];
    
    // Date filter
    const dateFilterValue = dateFilter.value;
    const now = new Date();
    let startDate;
    
    switch (dateFilterValue) {
        case 'today':
            startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
            break;
        case 'week':
            startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
            break;
        case 'month':
            startDate = new Date(now.getFullYear(), now.getMonth(), 1);
            break;
        case 'all':
        default:
            startDate = null;
    }
    
    if (startDate) {
        filtered = filtered.filter(v => new Date(v.timestamp) >= startDate);
    }
    
    // Camera filter
    const cameraFilterValue = cameraFilter.value;
    if (cameraFilterValue !== 'all') {
        filtered = filtered.filter(v => v.camera_id == cameraFilterValue);
    }
    
    // Violation type filter
    const violationTypeValue = violationTypeFilter.value;
    if (violationTypeValue !== 'all') {
        filtered = filtered.filter(v => v.type === violationTypeValue);
    }
    
    filteredViolations = filtered;
    updateViolationsTable();
    updateCharts();
    updateSummaryCards();
}

// Update violations table
function updateViolationsTable() {
    if (filteredViolations.length === 0) {
        violationsTableBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-muted py-4">
                    No violations found matching the current filters.
                </td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    filteredViolations.forEach(violation => {
        const timestamp = new Date(violation.timestamp).toLocaleString();
        const statusClass = violation.status === 'resolved' ? 'status-resolved' : 
                           violation.status === 'ongoing' ? 'status-ongoing' : 'status-pending';
        const typeClass = violation.type === 'safety_gear' ? 'violation-type-safety' : 'violation-type-proximity';
        
        html += `
            <tr class="violation-row" data-violation-id="${violation.id}">
                <td>${timestamp}</td>
                <td>Camera ${violation.camera_id + 1}</td>
                <td><span class="${typeClass}">${violation.type.replace('_', ' ').toUpperCase()}</span></td>
                <td>${violation.details}</td>
                <td>${violation.duration}s</td>
                <td>
                    <img src="${violation.screenshot}" class="violation-image" alt="Violation Screenshot" 
                         onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjYwIiB2aWV3Qm94PSIwIDAgMTAwIDYwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHdpZHRoPSIxMDAiIGhlaWdodD0iNjAiIGZpbGw9IiNmOGY5ZmEiLz48dGV4dCB4PSI1MCIgeT0iMzUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxMiIgZmlsbD0iIzZjNzU3ZCIgdGV4dC1hbmNob3I9Im1pZGRsZSI+SW1hZ2UgTm90IEZvdW5kPC90ZXh0Pjwvc3ZnPg=='">
                </td>
                <td><span class="badge ${statusClass}">${violation.status.toUpperCase()}</span></td>
                <td>
                    <button class="btn btn-sm btn-outline-primary btn-action" onclick="viewViolationDetails(${violation.id})">
                        View
                    </button>
                    ${violation.status !== 'resolved' ? 
                        `<button class="btn btn-sm btn-outline-success btn-action" onclick="resolveViolation(${violation.id})">
                            Resolve
                        </button>` : ''
                    }
                </td>
            </tr>
        `;
    });
    
    violationsTableBody.innerHTML = html;
}

// View violation details in modal
function viewViolationDetails(violationId) {
    const violation = violationsData.find(v => v.id === violationId);
    if (!violation) return;
    
    document.getElementById('violation-image').src = violation.screenshot;
    document.getElementById('modal-timestamp').textContent = new Date(violation.timestamp).toLocaleString();
    document.getElementById('modal-camera').textContent = `Camera ${violation.camera_id + 1}`;
    document.getElementById('modal-type').textContent = violation.type.replace('_', ' ').toUpperCase();
    document.getElementById('modal-duration').textContent = `${violation.duration}s`;
    document.getElementById('modal-status').textContent = violation.status.toUpperCase();
    document.getElementById('modal-analysis').textContent = violation.analysis;
    
    const modal = new bootstrap.Modal(document.getElementById('violationModal'));
    modal.show();
}

// Resolve violation
async function resolveViolation(violationId) {
    try {
        const response = await fetch(`/api/violations/${violationId}/resolve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                // Update local data
                const violation = violationsData.find(v => v.id === violationId);
                if (violation) {
                    violation.status = 'resolved';
                }
                
                // Update global violation data for synchronization
                if (window.violationData) {
                    const globalViolation = window.violationData.all.find(v => v.id === violationId);
                    if (globalViolation) {
                        globalViolation.status = 'resolved';
                    }
                }
                
                applyFilters();
                updateSummaryCards();
                updateCharts();
                showNotification('Violation resolved successfully', 'success');
            } else {
                showNotification(result.message, 'error');
            }
        } else {
            showNotification('Failed to resolve violation', 'error');
        }
    } catch (error) {
        console.error('Error resolving violation:', error);
        showNotification('Error resolving violation', 'error');
    }
}

// Clear all violations
async function clearAllViolations() {
    if (confirm('Are you sure you want to clear all violations? This action cannot be undone.')) {
        try {
            // Clear from database
            const response = await fetch('/api/violations/clear', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                // Clear local data
                violationsData = [];
                
                // Also clear global violation data for synchronization
                if (window.violationData) {
                    window.violationData.safety_gear = [];
                    window.violationData.proximity = [];
                    window.violationData.all = [];
                }
                
                applyFilters();
                updateSummaryCards();
                updateCharts();
                showNotification('All violations cleared', 'success');
            } else {
                showNotification('Failed to clear violations from database', 'error');
            }
        } catch (error) {
            console.error('Error clearing violations:', error);
            showNotification('Error clearing violations', 'error');
        }
    }
}

// Export data
function exportData() {
    const csvContent = generateCSV(filteredViolations);
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `violations_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Generate CSV content
function generateCSV(data) {
    const headers = ['Timestamp', 'Camera', 'Type', 'Details', 'Duration', 'Status'];
    const rows = data.map(v => [
        new Date(v.timestamp).toLocaleString(),
        `Camera ${v.camera_id + 1}`,
        v.type.replace('_', ' ').toUpperCase(),
        v.details,
        `${v.duration}s`,
        v.status.toUpperCase()
    ]);
    
    return [headers, ...rows].map(row => row.join(',')).join('\n');
}

// Update summary cards
function updateSummaryCards() {
    const total = filteredViolations.length;
    const safety = filteredViolations.filter(v => v.type === 'safety_gear').length;
    const proximity = filteredViolations.filter(v => v.type === 'proximity').length;
    const resolved = filteredViolations.filter(v => v.status === 'resolved').length;
    
    totalViolationsEl.textContent = total;
    safetyViolationsEl.textContent = safety;
    proximityViolationsEl.textContent = proximity;
    resolvedViolationsEl.textContent = resolved;
}

// Initialize charts
function initializeCharts() {
    // Violations over time chart
    const violationsCtx = document.getElementById('violationsChart').getContext('2d');
    charts.violations = new Chart(violationsCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Safety Gear Violations',
                data: [],
                borderColor: '#ffc107',
                backgroundColor: 'rgba(255, 193, 7, 0.1)',
                tension: 0.4
            }, {
                label: 'Proximity Violations',
                data: [],
                borderColor: '#17a2b8',
                backgroundColor: 'rgba(23, 162, 184, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
    
    // Violations by camera chart
    const cameraCtx = document.getElementById('cameraChart').getContext('2d');
    charts.camera = new Chart(cameraCtx, {
        type: 'doughnut',
        data: {
            labels: ['Camera 1', 'Camera 2', 'Camera 3', 'Camera 4'],
            datasets: [{
                data: [0, 0, 0, 0],
                backgroundColor: ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0'],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Update charts
function updateCharts() {
    updateViolationsOverTimeChart();
    updateCameraChart();
}

// Update violations over time chart
function updateViolationsOverTimeChart() {
    const last24Hours = [];
    const now = new Date();
    
    // Generate hourly labels for last 24 hours
    for (let i = 23; i >= 0; i--) {
        const hour = new Date(now.getTime() - i * 60 * 60 * 1000);
        last24Hours.push(hour.getHours() + ':00');
    }
    
    // Count violations by hour
    const safetyData = new Array(24).fill(0);
    const proximityData = new Array(24).fill(0);
    
    filteredViolations.forEach(violation => {
        const violationTime = new Date(violation.timestamp);
        const hoursAgo = Math.floor((now - violationTime) / (1000 * 60 * 60));
        
        if (hoursAgo >= 0 && hoursAgo < 24) {
            if (violation.type === 'safety_gear') {
                safetyData[23 - hoursAgo]++;
            } else if (violation.type === 'proximity') {
                proximityData[23 - hoursAgo]++;
            }
        }
    });
    
    charts.violations.data.labels = last24Hours;
    charts.violations.data.datasets[0].data = safetyData;
    charts.violations.data.datasets[1].data = proximityData;
    charts.violations.update();
}

// Update camera chart
function updateCameraChart() {
    const cameraData = [0, 0, 0, 0];
    
    filteredViolations.forEach(violation => {
        if (violation.camera_id >= 0 && violation.camera_id < 4) {
            cameraData[violation.camera_id]++;
        }
    });
    
    charts.camera.data.datasets[0].data = cameraData;
    charts.camera.update();
}

// Show notification
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}
