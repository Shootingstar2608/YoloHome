document.addEventListener('DOMContentLoaded', () => {
    // === WebSocket Initialization ===
    const socket = io();

    // DOM Elements
    const statusDot = document.getElementById('connection-status');
    const statusText = document.getElementById('status-text');

    const tempValueDOM = document.getElementById('temp-value');
    const tempProgress = document.getElementById('temp-progress');

    const humidValueDOM = document.getElementById('humid-value');
    const humidProgress = document.getElementById('humid-progress');

    // === Chart.js Setup ===
    const ctx = document.getElementById('realtimeChart').getContext('2d');

    // Gradient configs for chart
    const gradientTemp = ctx.createLinearGradient(0, 0, 0, 400);
    gradientTemp.addColorStop(0, 'rgba(239, 68, 68, 0.5)');
    gradientTemp.addColorStop(1, 'rgba(239, 68, 68, 0.0)');

    const gradientHumid = ctx.createLinearGradient(0, 0, 0, 400);
    gradientHumid.addColorStop(0, 'rgba(6, 182, 212, 0.5)');
    gradientHumid.addColorStop(1, 'rgba(6, 182, 212, 0.0)');

    const MAX_DATA_POINTS = 20;

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [], // Timestamps
            datasets: [
                {
                    label: 'Nhiệt độ (°C)',
                    data: [],
                    borderColor: '#ef4444',
                    backgroundColor: gradientTemp,
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#ef4444',
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    yAxisID: 'y'
                },
                {
                    label: 'Độ ẩm / Ánh sáng (%)',
                    data: [],
                    borderColor: '#06b6d4',
                    backgroundColor: gradientHumid,
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#06b6d4',
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    labels: { color: '#e2e8f0', font: { family: "'Inter', sans-serif" } }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 17, 26, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#e2e8f0',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false },
                    ticks: { color: '#94a3b8', maxTicksLimit: 10 }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false },
                    ticks: { color: '#ef4444' },
                    suggestedMin: 15,
                    suggestedMax: 45
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: { drawOnChartArea: false },
                    ticks: { color: '#06b6d4' },
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            }
        }
    });

    // Helper functions to update UI
    const updateTempUI = (val) => {
        const numVal = parseFloat(val);
        if (isNaN(numVal)) return;
        tempValueDOM.innerText = numVal.toFixed(1);
        // Ngưỡng min 0, max 50C cho progress bar
        let percent = (numVal / 50) * 100;
        if (percent > 100) percent = 100;
        tempProgress.style.width = percent + '%';
    };

    const updateHumidUI = (val) => {
        const numVal = parseFloat(val);
        if (isNaN(numVal)) return;
        humidValueDOM.innerText = Math.round(numVal);
        humidProgress.style.width = Math.min(Math.max(numVal, 0), 100) + '%';
    };

    // Khởi tạo data ban đầu nếu có từ backend render
    let lastTemp = initialData.V2 || 0;
    let lastHumid = initialData.V1 || 0;

    updateTempUI(lastTemp);
    updateHumidUI(lastHumid);

    // Xử lý thêm vào biểu đồ
    const addDataToChart = (timeStr, tempOpt, humidOpt) => {
        if (chart.data.labels.length > MAX_DATA_POINTS) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
            chart.data.datasets[1].data.shift();
        }

        chart.data.labels.push(timeStr);
        chart.data.datasets[0].data.push(tempOpt !== null ? tempOpt : lastTemp);
        chart.data.datasets[1].data.push(humidOpt !== null ? humidOpt : lastHumid);
        chart.update('none'); // Update without full animation for smoother real-time feel
    };

    // Cập nhật biểu đồ mỗi xx giây nếu không có dữ liệu để đồ thị liên tục bò
    setInterval(() => {
        if (lastTemp !== 0 && lastHumid !== 0) {
            const now = new Date();
            const timeStr = now.toLocaleTimeString('vi-VN', { hour12: false });
            addDataToChart(timeStr, lastTemp, lastHumid);
        }
    }, 5000);

    // === Socket.IO Events ===
    socket.on('connect', () => {
        statusDot.classList.add('connected');
        statusText.innerText = 'Đã kết nối Real-time';
    });

    socket.on('disconnect', () => {
        statusDot.classList.remove('connected');
        statusText.innerText = 'Bị ngắt kết nối';
    });

    socket.on('sensor_update', (data) => {
        const { topic, value } = data;

        if (topic === 'V2') { // Nhiệt độ
            lastTemp = value;
            updateTempUI(value);
        } else if (topic === 'V1') { // Độ ẩm
            lastHumid = value;
            updateHumidUI(value);
        }
    });

    // === Motion Detection Notification ===
    const notificationContainer = document.getElementById('notification-container');

    const showMotionNotification = () => {
        const notification = document.createElement('div');
        notification.className = 'motion-alert glass-panel active';
        notification.innerHTML = `
            <div class="alert-content">
                <i class="fa-solid fa-person-running"></i>
                <div class="alert-text">
                    <strong>Phát hiện chuyển động!</strong>
                    <span>Có người di chuyển trong khu vực cảm biến.</span>
                </div>
            </div>
        `;
        notificationContainer.appendChild(notification);

        // Remove after 5 seconds
        setTimeout(() => {
            notification.classList.remove('active');
            setTimeout(() => {
                notification.remove();
            }, 500);
        }, 5000);
    };

    socket.on('motion_detected', (data) => {
        console.log("Motion detected!", data);
        showMotionNotification();
    });

    // === Tab Switching Logic ===
    const navLinks = document.querySelectorAll('.nav-links li[data-tab]');
    const tabContents = document.querySelectorAll('.tab-content');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            document.querySelectorAll('.nav-links li').forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            const targetTabId = link.getAttribute('data-tab');
            tabContents.forEach(tab => {
                if (tab.id === targetTabId) {
                    tab.classList.add('active');
                } else {
                    tab.classList.remove('active');
                }
            });
        });
    });

    // === Module 3: Device Control Logic ===
    const modeToggle = document.getElementById('mode-toggle');
    const labelAuto = document.getElementById('label-auto');
    const labelManual = document.getElementById('label-manual');
    const modeDesc = document.getElementById('mode-desc');
    const dashModeStatus = document.getElementById('dash-mode-status');

    const fanToggle = document.getElementById('fan-toggle');
    const cardFan = document.getElementById('card-fan');
    const stateTextFan = document.getElementById('state-text-fan');
    const dashFanStatus = document.getElementById('dash-fan-status');

    const lightToggle = document.getElementById('light-toggle');
    const cardLight = document.getElementById('card-light');
    const stateTextLight = document.getElementById('state-text-light');
    const dashLightStatus = document.getElementById('dash-light-status');

    const doorControlToggle = document.getElementById('door-control-toggle');
    const cardDoorControl = document.getElementById('card-door-control');
    const stateTextDoorControl = document.getElementById('state-text-door-control');

    let currentMode = '0'; // 0: Auto, 1: Manual

    const updateDeviceUI = (topic, value) => {
        const isOn = (value === '1');

        if (topic === 'V6') { // Mode
            currentMode = value;
            if (modeToggle) modeToggle.checked = isOn;
            
            if (isOn) {
                labelManual.classList.add('active');
                labelAuto.classList.remove('active');
                modeDesc.innerText = 'Hệ thống đang ở chế độ Thủ công. Bạn có thể toàn quyền điều khiển Quạt và Đèn.';
                if (dashModeStatus) {
                    dashModeStatus.className = 'mode-badge manual';
                    dashModeStatus.innerText = 'Chế độ: Manual';
                }
            } else {
                labelAuto.classList.add('active');
                labelManual.classList.remove('active');
                modeDesc.innerText = 'Hệ thống đang tự động điều chỉnh theo Cảm biến Nhiệt độ và Ánh sáng.';
                if (dashModeStatus) {
                    dashModeStatus.className = 'mode-badge auto';
                    dashModeStatus.innerText = 'Chế độ: Auto';
                }
            }
        } else if (topic === 'V4') { // Fan
            if (fanToggle) fanToggle.checked = isOn;
            if (isOn) {
                cardFan.classList.add('active');
                stateTextFan.innerText = 'ĐANG BẬT';
                if (dashFanStatus) {
                    dashFanStatus.className = 'status-badge on';
                    dashFanStatus.innerText = 'BẬT';
                }
            } else {
                cardFan.classList.remove('active');
                stateTextFan.innerText = 'ĐANG TẮT';
                if (dashFanStatus) {
                    dashFanStatus.className = 'status-badge off';
                    dashFanStatus.innerText = 'TẮT';
                }
            }
        } else if (topic === 'V5') { // Light
            if (lightToggle) lightToggle.checked = isOn;
            if (isOn) {
                cardLight.classList.add('active');
                stateTextLight.innerText = 'ĐANG BẬT';
                if (dashLightStatus) {
                    dashLightStatus.className = 'status-badge on';
                    dashLightStatus.innerText = 'BẬT';
                }
            } else {
                cardLight.classList.remove('active');
                stateTextLight.innerText = 'ĐANG TẮT';
                if (dashLightStatus) {
                    dashLightStatus.className = 'status-badge off';
                    dashLightStatus.innerText = 'TẮT';
                }
            }
        } else if (topic === 'V7') { // Smart Door Lock (Servo)
            const isUnlocked = (value === 'unlock' || value === '1');
            const doorCircle = document.getElementById('door-lock-circle');
            const doorIcon = document.getElementById('door-lock-icon');
            const doorStatusText = document.getElementById('door-status-text');
            const servoAngle = document.getElementById('servo-angle');
            const dashDoorStatus = document.getElementById('dash-door-status');

            if (doorControlToggle) doorControlToggle.checked = isUnlocked;

            if (isUnlocked) {
                if (cardDoorControl) cardDoorControl.classList.add('active');
                if (stateTextDoorControl) stateTextDoorControl.innerText = 'ĐÃ MỞ KHÓA';
                if (doorCircle) doorCircle.className = 'door-lock-circle unlocked';
                if (doorIcon) doorIcon.className = 'fa-solid fa-lock-open';
                if (doorStatusText) doorStatusText.innerText = 'CỬA ĐÃ MỞ KHÓA';
                if (servoAngle) servoAngle.innerText = '90°';
                if (dashDoorStatus) {
                    dashDoorStatus.className = 'status-badge on';
                    dashDoorStatus.innerText = 'MỞ';
                }
            } else {
                if (cardDoorControl) cardDoorControl.classList.remove('active');
                if (stateTextDoorControl) stateTextDoorControl.innerText = 'ĐANG KHÓA';
                if (doorCircle) doorCircle.className = 'door-lock-circle locked';
                if (doorIcon) doorIcon.className = 'fa-solid fa-lock';
                if (doorStatusText) doorStatusText.innerText = 'CỬA ĐANG KHÓA';
                if (servoAngle) servoAngle.innerText = '0°';
                if (dashDoorStatus) {
                    dashDoorStatus.className = 'status-badge off';
                    dashDoorStatus.innerText = 'KHÓA';
                }
            }
        }
    };

    // Listen to changes from WebSocket
    socket.on('device_update', (data) => {
        updateDeviceUI(data.topic, data.value);
    });

    // Handle user actions
    if (modeToggle) {
        modeToggle.addEventListener('change', (e) => {
            const val = e.target.checked ? '1' : '0';
            socket.emit('set_device', { topic: 'V6', value: val });
        });
    }

    if (fanToggle) {
        fanToggle.addEventListener('change', (e) => {
            if (currentMode === '0') {
                socket.emit('set_device', { topic: 'V6', value: '1' });
            }
            const val = e.target.checked ? '1' : '0';
            socket.emit('set_device', { topic: 'V4', value: val });
        });
    }

    if (lightToggle) {
        lightToggle.addEventListener('change', (e) => {
            if (currentMode === '0') {
                socket.emit('set_device', { topic: 'V6', value: '1' });
            }
            const val = e.target.checked ? '1' : '0';
            socket.emit('set_device', { topic: 'V5', value: val });
        });
    }

    if (doorControlToggle) {
        doorControlToggle.addEventListener('change', (e) => {
            const val = e.target.checked ? '1' : '0';
            socket.emit('set_device', { topic: 'V7', value: val });
            addUnlockLog(e.target.checked ? 'Mở khóa thủ công (Tab Điều khiển)' : 'Khóa cửa thủ công (Tab Điều khiển)', true);
        });
    }

    // === Module Security: Face Recognition & Door Lock Logic ===
    const camStatusBadge = document.getElementById('cam-status-badge');
    const camStatusMsg = document.getElementById('cam-status-msg');
    const unlockLogList = document.getElementById('unlock-log-list');
    const btnUnlockDoor = document.getElementById('btn-unlock-door');

    if (btnUnlockDoor) {
        btnUnlockDoor.addEventListener('click', () => {
            socket.emit('set_device', { topic: 'V7', value: 'unlock' });
            addUnlockLog('Mở khóa thủ công (Nút bấm Dashboard)', true);
        });
    }

    const addUnlockLog = (userOrAction, success = true) => {
        if (!unlockLogList) return;
        const emptyLog = unlockLogList.querySelector('.empty-log');
        if (emptyLog) emptyLog.remove();

        const li = document.createElement('li');
        li.className = 'log-item';
        li.style.borderLeftColor = success ? 'var(--accent-green)' : 'var(--accent-red)';
        
        const now = new Date();
        const timeStr = now.toLocaleTimeString('vi-VN');
        
        li.innerHTML = `
            <span><i class="fa-solid ${success ? 'fa-user-check' : 'fa-user-xmark'}"></i> ${userOrAction}</span>
            <span style="color: var(--text-muted); font-size: 0.75rem;">${timeStr}</span>
        `;
        unlockLogList.insertBefore(li, unlockLogList.firstChild);

        if (unlockLogList.children.length > 10) {
            unlockLogList.removeChild(unlockLogList.lastChild);
        }
    };

    socket.on('face_status', (data) => {
        console.log("[FaceStatus]", data);
        if (!camStatusBadge || !camStatusMsg) return;

        if (data.status === 'scanning') {
            camStatusBadge.className = 'camera-status-badge scanning';
            camStatusBadge.innerText = 'SCANNING...';
            camStatusMsg.innerHTML = `<i class="fa-solid fa-spinner fa-spin" style="color: #f59e0b;"></i> ${data.message}`;
        } else if (data.status === 'success') {
            camStatusBadge.className = 'camera-status-badge success';
            camStatusBadge.innerText = 'MATCHED';
            camStatusMsg.innerHTML = `<i class="fa-solid fa-circle-check" style="color: var(--accent-green);"></i> ${data.message}`;
            addUnlockLog(`Nhận diện AI: ${data.user}`, true);
        } else if (data.status === 'timeout') {
            camStatusBadge.className = 'camera-status-badge standby';
            camStatusBadge.innerText = 'STANDBY';
            camStatusMsg.innerHTML = `<i class="fa-solid fa-circle-info"></i> ${data.message}`;
        } else if (data.status === 'error') {
            camStatusBadge.className = 'camera-status-badge standby';
            camStatusBadge.innerText = 'ERROR';
            camStatusMsg.innerHTML = `<i class="fa-solid fa-triangle-exclamation" style="color: var(--accent-red);"></i> ${data.message}`;
        }
    });

});
