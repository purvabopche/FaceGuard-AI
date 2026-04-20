document.addEventListener('DOMContentLoaded', () => {
    // --- Navigation Logic ---
    const navItems = document.querySelectorAll('.nav-links li');
    const sections = document.querySelectorAll('main section');
    
    let cameraCheckInterval;
    let isRegistering = false;
    
    function stopCameraFeed() {
        // Ping backend to release hardware camera
        fetch('/stop_camera', { method: 'POST' });
        
        // Hide image streams in UI
        document.getElementById('reg-stream').style.display = 'none';
        document.getElementById('att-stream').style.display = 'none';
        
        document.getElementById('reg-camera-box').style.display = 'flex';
        document.getElementById('att-camera-box').style.display = 'flex';
        
        // Clear reg progress checking
        if (cameraCheckInterval) clearInterval(cameraCheckInterval);
        isRegistering = false;
    }

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            // Update active nav
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            // Hide all sections, show target
            const targetId = item.getAttribute('data-target');
            sections.forEach(sec => {
                sec.style.display = 'none';
                sec.classList.remove('active-section');
            });
            const targetSec = document.getElementById(targetId);
            targetSec.style.display = 'flex';
            targetSec.classList.add('active-section');
            
            // Reset state when navigating
            stopCameraFeed();
            
            // Fetch records auto if view section
            if(targetId === 'view-section') {
                document.getElementById('record-date').valueAsDate = new Date();
                fetchRecords();
            }
        });
    });

    // --- Helper Functions ---
    function showStatus(elementId, message, type) {
        const el = document.getElementById(elementId);
        el.className = 'status-msg show';
        el.classList.add(`status-${type}`);
        el.textContent = message;
        
        // auto hide
        setTimeout(() => {
            el.classList.remove('show');
        }, 5000);
    }
    
    function startVideoFeed(imgElementId, placeholderId) {
        document.getElementById(placeholderId).style.display = 'none';
        const imgEl = document.getElementById(imgElementId);
        imgEl.style.display = 'block';
        // append timestamp to bypass cache
        imgEl.src = `/video_feed?t=${new Date().getTime()}`;
    }

    // --- Register Logic ---
    const regBtn = document.getElementById('start-capture-btn');
    
    regBtn.addEventListener('click', async () => {
        if(isRegistering) return;
        
        const id = document.getElementById('reg-id').value.trim();
        const name = document.getElementById('reg-name').value.trim();
        
        if (!id || !name) {
            showStatus('reg-status', 'Please enter ID and Name', 'error');
            return;
        }
        
        try {
            const res = await fetch('/start_register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id, name })
            });
            const data = await res.json();
            
            if (res.ok) {
                isRegistering = true;
                showStatus('reg-status', data.message, 'info');
                startVideoFeed('reg-stream', 'reg-camera-box');
                
                document.getElementById('reg-progress-container').style.display = 'block';
                
                // Poll for progress
                cameraCheckInterval = setInterval(async () => {
                    const statusRes = await fetch('/registration_status');
                    const statusData = await statusRes.json();
                    
                    if (statusData.complete) {
                        clearInterval(cameraCheckInterval);
                        isRegistering = false;
                        showStatus('reg-status', statusData.message, 'success');
                        document.getElementById('reg-progress').style.width = '100%';
                        
                        setTimeout(() => {
                            document.getElementById('reg-progress-container').style.display = 'none';
                            stopCameraFeed();
                        }, 2000);
                    } else {
                        const pct = (statusData.progress / statusData.total) * 100;
                        document.getElementById('reg-progress').style.width = `${pct}%`;
                    }
                }, 500);
                
            } else {
                showStatus('reg-status', data.error, 'error');
            }
        } catch (err) {
            showStatus('reg-status', 'Server error. Is the backend running?', 'error');
        }
    });

    // --- Train Logic ---
    document.getElementById('train-btn').addEventListener('click', async () => {
        showStatus('train-status', 'Training model... Please wait.', 'info');
        try {
            const res = await fetch('/train_model', { method: 'POST' });
            const data = await res.json();
            
            if (res.ok) {
                showStatus('train-status', data.message, 'success');
            } else {
                showStatus('train-status', data.error, 'error');
            }
        } catch (err) {
            showStatus('train-status', 'Server error during training', 'error');
        }
    });

    // --- Attendance Logic ---
    const startAttBtn = document.getElementById('start-attendance-btn');
    const stopAttBtn = document.getElementById('stop-attendance-btn');

    startAttBtn.addEventListener('click', async () => {
        try {
            const res = await fetch('/start_attendance', { method: 'POST' });
            const data = await res.json();
            
            if(res.ok) {
                startVideoFeed('att-stream', 'att-camera-box');
                startAttBtn.disabled = true;
                stopAttBtn.disabled = false;
                showStatus('att-status', data.message, 'success');
            } else {
                showStatus('att-status', data.error, 'error');
            }
        } catch(err) {
            showStatus('att-status', 'Server error.', 'error');
        }
    });
    
    stopAttBtn.addEventListener('click', () => {
        stopCameraFeed();
        startAttBtn.disabled = false;
        stopAttBtn.disabled = true;
        showStatus('att-status', 'Attendance tracking stopped.', 'info');
    });

    // --- View Records Logic ---
    const fetchRecordsBtn = document.getElementById('fetch-records-btn');
    const dateInput = document.getElementById('record-date');
    const tbody = document.getElementById('records-body');

    fetchRecordsBtn.addEventListener('click', fetchRecords);

    async function fetchRecords() {
        const date = dateInput.value;
        if (!date) return;
        
        try {
            const res = await fetch(`/get_attendance?date=${date}`);
            const data = await res.json();
            
            tbody.innerHTML = '';
            
            if (data.records && data.records.length > 0) {
                data.records.forEach(rec => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${rec.Id}</td>
                        <td><strong>${rec.Name}</strong></td>
                        <td>${rec.Time}</td>
                        <td><span class="status-badge">Present</span></td>
                    `;
                    tbody.appendChild(tr);
                });
            } else {
                tbody.innerHTML = '<tr><td colspan="4" class="empty-state">No attendance records found for this date.</td></tr>';
            }
        } catch (err) {
            console.error(err);
            tbody.innerHTML = '<tr><td colspan="4" class="empty-state">Error fetching records.</td></tr>';
        }
    }
});
