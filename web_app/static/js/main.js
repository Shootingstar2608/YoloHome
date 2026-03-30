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

});
