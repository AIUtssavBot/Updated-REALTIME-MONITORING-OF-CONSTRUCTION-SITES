// Connect to Socket.IO server
const socket = io();
const alertSound = document.getElementById('alert-sound');
let safetyAlerts = [];
let proximityAlerts = [];
let audioEnabled = true;
let safetyDetectionEnabled = true;
let proximityDetectionEnabled = true;
let totalWorkers = 0;
let activeViolations = 0;

// Global violation storage for synchronization
window.violationData = {
    safety_gear: [],
    proximity: [],
    all: []
};

// DOM elements
const safetyAlertsList = document.getElementById('safety-alerts');
const proximityAlertsList = document.getElementById('proximity-alerts');
const toggleAudio = document.getElementById('toggle-audio');
const toggleSafety = document.getElementById('toggle-safety');
const toggleProximity = document.getElementById('toggle-proximity');
const refreshCamerasBtn = document.getElementById('refresh-cameras');
const testAlertBtn = document.getElementById('test-alert');
const clearAlertsBtn = document.getElementById('clear-alerts');
const connectionStatus = document.getElementById('status-indicator');
const safetyRateEl = document.getElementById('safety-rate');
const proximityRateEl = document.getElementById('proximity-rate');
const totalWorkersEl = document.getElementById('total-workers');
const activeViolationsEl = document.getElementById('active-violations');
const lastUpdatedEl = document.getElementById('last-updated');

// Socket.IO connections
socket.on('connect', () => {
    connectionStatus.classList.remove('status-error');
    connectionStatus.classList.add('status-ok');
    document.getElementById('connection-status').textContent = 'Connected';
});

socket.on('disconnect', () => {
    connectionStatus.classList.remove('status-ok');
    connectionStatus.classList.add('status-error');
    document.getElementById('connection-status').textContent = 'Disconnected';
});

// Handle safety alert events
socket.on('safety_alert', (data) => {
    if (!safetyDetectionEnabled) return;
    
    const alert = JSON.parse(data);
    safetyAlerts.unshift(alert); // Add to beginning of array
    
            // Store in global violation data for synchronization
            if (alert.violations && alert.violations.length > 0) {
                alert.violations.forEach(violation => {
                    const violationRecord = {
                        id: Date.now() + Math.random(), // Simple ID generation
                        timestamp: new Date().toISOString(),
                        camera_id: parseInt(alert.camera_id),
                        type: 'safety_gear',
                        details: `Worker ${violation.worker_id.split('_').pop()}: Missing ${violation.missing_gear.join(', ')}`,
                        duration: violation.duration,
                        screenshot: violation.screenshot || '',
                        status: 'ongoing',
                        analysis: `Safety gear violation detected. Worker missing ${violation.missing_gear.join(', ')} for ${violation.duration} seconds.`
                    };
                    
                    window.violationData.safety_gear.unshift(violationRecord);
                    window.violationData.all.unshift(violationRecord);
                    
                    // Store in database via API
                    storeViolationInDatabase(violationRecord);
                });
            }
    
    updateSafetyAlertsList();
    updateStatistics();
    
    // Play alert sound if enabled
    if (audioEnabled) {
        alertSound.play().catch(e => console.log('Error playing sound:', e));
    }
    
    // Flash the camera border
    const cameraCard = document.querySelector(`.col-md-6:nth-child(${parseInt(alert.camera_id) + 1}) .card`);
    if (cameraCard) {
        cameraCard.classList.add('alert-active');
        setTimeout(() => {
            cameraCard.classList.remove('alert-active');
        }, 3000);
    }
});

// Handle proximity alert events
socket.on('proximity_alert', (data) => {
    if (!proximityDetectionEnabled) return;
    
    const alert = JSON.parse(data);
    proximityAlerts.unshift(alert); // Add to beginning of array
    
            // Store in global violation data for synchronization
            if (alert.alerts && alert.alerts.length > 0) {
                alert.alerts.forEach(proximityAlert => {
                    const violationRecord = {
                        id: Date.now() + Math.random(), // Simple ID generation
                        timestamp: new Date().toISOString(),
                        camera_id: parseInt(alert.camera_id),
                        type: 'proximity',
                        details: `Worker ${proximityAlert.worker_id.split('_').pop()} too close to ${proximityAlert.machine_id} (${proximityAlert.distance}px)`,
                        duration: 0,
                        screenshot: proximityAlert.screenshot || '',
                        status: 'ongoing',
                        analysis: `Proximity violation detected. Worker is ${proximityAlert.distance} pixels away from machinery, below the safety threshold of 80 pixels.`
                    };
                    
                    window.violationData.proximity.unshift(violationRecord);
                    window.violationData.all.unshift(violationRecord);
                    
                    // Store in database via API
                    storeViolationInDatabase(violationRecord);
                });
            }
    
    updateProximityAlertsList();
    updateStatistics();
    
    // Play alert sound if enabled
    if (audioEnabled) {
        alertSound.play().catch(e => console.log('Error playing sound:', e));
    }
    
    // Flash the camera border
    const cameraCard = document.querySelector(`.col-md-6:nth-child(${parseInt(alert.camera_id) + 1}) .card`);
    if (cameraCard) {
        cameraCard.classList.add('alert-active');
        setTimeout(() => {
            cameraCard.classList.remove('alert-active');
        }, 3000);
    }
});

// Function to update the safety alerts list
function updateSafetyAlertsList() {
    // Keep only the most recent 20 alerts
    safetyAlerts = safetyAlerts.slice(0, 20);
    
    if (safetyAlerts.length === 0) {
        safetyAlertsList.innerHTML = '<div class="alert alert-info">No safety gear violations detected.</div>';
        return;
    }
    
    let html = '';
    safetyAlerts.forEach((alert, index) => {
        const timestamp = new Date().toLocaleTimeString();
        const cameraId = parseInt(alert.camera_id) + 1;
        const violations = alert.violations.map(v => 
            `<strong>${v.worker_id.replace(/worker_\d+_(\d+)/, 'Worker $1')}</strong>: Missing ${v.missing_gear.join(', ')} (${v.duration}s)`
        ).join('<br>');
        
        html += `
            <div class="alert alert-danger">
                <strong>Camera ${cameraId}</strong>: Safety Violation
                <span class="alert-timestamp">${timestamp}</span>
                <div>${violations}</div>
            </div>
        `;
    });
    
    safetyAlertsList.innerHTML = html;
}

// Function to update the proximity alerts list
function updateProximityAlertsList() {
    // Keep only the most recent 20 alerts
    proximityAlerts = proximityAlerts.slice(0, 20);
    
    if (proximityAlerts.length === 0) {
        proximityAlertsList.innerHTML = '<div class="alert alert-info">No proximity alerts detected.</div>';
        return;
    }
    
    let html = '';
    proximityAlerts.forEach((alert, index) => {
        const timestamp = new Date().toLocaleTimeString();
        const cameraId = parseInt(alert.camera_id) + 1;
        const alerts = alert.alerts.map(a => 
            `<strong>${a.worker_id.replace(/worker_\d+_(\d+)/, 'Worker $1')}</strong> too close to ${a.machine_id.replace(/machine_\d+_(\d+)/, 'Machine $1')} (${a.distance}px)`
        ).join('<br>');
        
        html += `
            <div class="alert alert-warning">
                <strong>Camera ${cameraId}</strong>: Proximity Alert
                <span class="alert-timestamp">${timestamp}</span>
                <div>${alerts}</div>
            </div>
        `;
    });
    
    proximityAlertsList.innerHTML = html;
}

// Update statistics
function updateStatistics() {
    // Simulate some statistics
    const now = new Date();
    
    // Randomly update total workers (between 8-15 for demonstration)
    totalWorkers = Math.floor(Math.random() * 8) + 8;
    
    // Calculate active violations
    activeViolations = safetyAlerts.length + proximityAlerts.length;
    
    // Calculate compliance rate (between 70-100%)
    const safetyRate = Math.floor(Math.random() * 30) + 70;
    
    // Calculate proximity alert frequency (between 10-40%)
    const proximityRate = Math.floor(Math.random() * 30) + 10;
    
    // Update DOM
    totalWorkersEl.textContent = totalWorkers;
    activeViolationsEl.textContent = activeViolations;
    lastUpdatedEl.textContent = now.toLocaleTimeString();
    
    safetyRateEl.style.width = `${safetyRate}%`;
    safetyRateEl.textContent = `${safetyRate}%`;
    safetyRateEl.setAttribute('aria-valuenow', safetyRate);
    
    proximityRateEl.style.width = `${proximityRate}%`;
    proximityRateEl.textContent = `${proximityRate}%`;
    proximityRateEl.setAttribute('aria-valuenow', proximityRate);
    
    // Update color based on rate
    if (safetyRate < 80) {
        safetyRateEl.classList.remove('bg-success');
        safetyRateEl.classList.add('bg-warning');
    } else {
        safetyRateEl.classList.remove('bg-warning');
        safetyRateEl.classList.add('bg-success');
    }
    
    if (proximityRate > 30) {
        proximityRateEl.classList.remove('bg-warning');
        proximityRateEl.classList.add('bg-danger');
    } else {
        proximityRateEl.classList.remove('bg-danger');
        proximityRateEl.classList.add('bg-warning');
    }
}

// Event listeners
toggleAudio.addEventListener('change', function() {
    audioEnabled = this.checked;
});

toggleSafety.addEventListener('change', function() {
    safetyDetectionEnabled = this.checked;
});

toggleProximity.addEventListener('change', function() {
    proximityDetectionEnabled = this.checked;
});

refreshCamerasBtn.addEventListener('click', function() {
    // Refresh all camera feeds
    document.querySelectorAll('.camera-feed').forEach(feed => {
        const src = feed.src;
        feed.src = '';
        feed.src = src + '?' + new Date().getTime();
    });
    
    // Update camera status randomly for demonstration
    document.querySelectorAll('[id^="camera-"]').forEach(statusBadge => {
        if (Math.random() > 0.9) { // 10% chance of offline status
            statusBadge.classList.remove('bg-success');
            statusBadge.classList.add('bg-danger');
            statusBadge.textContent = 'Offline';
            
            // Add grayscale to the camera
            const cameraCard = statusBadge.closest('.card');
            const cameraFeed = cameraCard.querySelector('.camera-feed');
            cameraFeed.classList.add('camera-offline');
        } else {
            statusBadge.classList.remove('bg-danger');
            statusBadge.classList.add('bg-success');
            statusBadge.textContent = 'Online';
            
            // Remove grayscale
            const cameraCard = statusBadge.closest('.card');
            const cameraFeed = cameraCard.querySelector('.camera-feed');
            cameraFeed.classList.remove('camera-offline');
        }
    });
});

testAlertBtn.addEventListener('click', function() {
    // Generate a test safety alert
    const testSafetyAlert = {
        camera_id: Math.floor(Math.random() * 4).toString(),
        violations: [
            {
                worker_id: `worker_${Math.floor(Math.random() * 4)}_${Math.floor(Math.random() * 5)}`,
                missing_gear: ['helmet', 'vest'],
                duration: 6.5
            }
        ]
    };
    
    // Generate a test proximity alert
    const testProximityAlert = {
        camera_id: Math.floor(Math.random() * 4).toString(),
        alerts: [
            {
                worker_id: `worker_${Math.floor(Math.random() * 4)}_${Math.floor(Math.random() * 5)}`,
                machine_id: `machine_${Math.floor(Math.random() * 4)}_${Math.floor(Math.random() * 2)}`,
                distance: 45.2
            }
        ]
    };
    
    // Simulate socket events
    socket.emit('safety_alert', JSON.stringify(testSafetyAlert));
    socket.emit('proximity_alert', JSON.stringify(testProximityAlert));
    
    // Also handle them locally
    if (safetyDetectionEnabled) {
        safetyAlerts.unshift(testSafetyAlert);
        updateSafetyAlertsList();
    }
    
    if (proximityDetectionEnabled) {
        proximityAlerts.unshift(testProximityAlert);
        updateProximityAlertsList();
    }
    
    updateStatistics();
    
    // Play alert sound if enabled
    if (audioEnabled) {
        alertSound.play().catch(e => console.log('Error playing sound:', e));
    }
});

clearAlertsBtn.addEventListener('click', function() {
    safetyAlerts = [];
    proximityAlerts = [];
    
    // Also clear global violation data for synchronization
    if (window.violationData) {
        window.violationData.safety_gear = [];
        window.violationData.proximity = [];
        window.violationData.all = [];
    }
    
    updateSafetyAlertsList();
    updateProximityAlertsList();
    updateStatistics();
});

// Initial update
updateStatistics();

// Periodic statistics update
setInterval(updateStatistics, 30000);

// Highlight active navigation link
document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});

// Check for camera errors
document.querySelectorAll('.camera-feed').forEach(feed => {
    feed.addEventListener('error', function() {
        const cameraCard = this.closest('.card');
        const cameraHeader = cameraCard.querySelector('.card-header');
        const statusBadge = cameraHeader.querySelector('[id^="camera-"]');
        
        statusBadge.classList.remove('bg-success');
        statusBadge.classList.add('bg-danger');
        statusBadge.textContent = 'Error';
        
        this.classList.add('camera-offline');
    });
});

// Store violation in database
async function storeViolationInDatabase(violationRecord) {
    try {
        const response = await fetch('/api/violations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(violationRecord)
        });
        
        if (!response.ok) {
            console.error('Failed to store violation in database');
        }
    } catch (error) {
        console.error('Error storing violation in database:', error);
    }
} 