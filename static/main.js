// ==================================================================
// 全域變數與 DOM 元素快取
// ==================================================================
let mainSocket;
let appConfig = {};

const bootScreen = document.getElementById('boot-screen');
const dashboard = document.getElementById('dashboard');
const topPanel = {
    stats: document.getElementById('ascii-stats'),
    services: document.getElementById('service-status')
};
const mainStreamContainer = document.getElementById('main-stream-container');
const statusBar = document.getElementById('status-bar');

// ==================================================================
// 主儀表板 (Dashboard) 渲染函式
// ==================================================================

function updateDashboard(data) {
    const { cpu, ram, services } = data;

    // 更新資源監控
    const cpuFill = Math.round(cpu / 10);
    const ramFill = Math.round(ram / 10);
    const cpuBar = '█'.repeat(cpuFill) + '░'.repeat(10 - cpuFill);
    const ramBar = '█'.repeat(ramFill) + '░'.repeat(10 - ramFill);
    topPanel.stats.innerHTML =
        `CPU: [${cpuBar}] ${cpu.toFixed(1).padStart(4)}%\n` +
        `RAM: [${ramBar}] ${ram.toFixed(1).padStart(4)}%`;

    // 更新服務狀態
    const statusIcons = { ok: '✅', warn: '⚠️', error: '❌' };
    let servicesHtml = '';
    services.forEach(s => {
        servicesHtml += `<div class="service-item"><span class="service-icon">${statusIcons[s.status]}</span><span class="${s.status}">${s.name}</span></div>`;
    });
    topPanel.services.innerHTML = servicesHtml;

    // 更新狀態欄
    const isOk = services.every(s => s.status === 'ok');
    const systemStatus = isOk ? '<span class="ok">🟢 系統狀態正常</span>' : '<span class="error">🔴 系統偵測到異常</span>';
    const currentTime = new Date().toLocaleTimeString('zh-TW', { hour12: false });
    statusBar.innerHTML = `
        <div class="status-group"><span>CPU: ${cpu.toFixed(1)}%</span><span>RAM: ${ram.toFixed(1)}%</span></div>
        <div>${systemStatus}</div>
        <div class="dim">${currentTime}</div>
    `;
}

function addMainStreamLog(log) {
    const { icon, level, levelClass, message, timestamp } = log;
    const ts = new Date(timestamp * 1000).toLocaleTimeString('en-GB');

    const streamItem = document.createElement('div');
    streamItem.className = 'stream-item';

    const metaHTML = `
        <div class="stream-meta">
            <span class="stream-icon">${icon}</span>
            <span class="stream-ts">[${ts}]</span>
            <span class="stream-level ${levelClass}">[${level.toUpperCase()}]</span>
        </div>`;
    streamItem.innerHTML = metaHTML;

    if (typeof message === 'string') {
        const textContentDiv = document.createElement('div');
        textContentDiv.className = 'stream-text-content';
        textContentDiv.innerHTML = `<span>${message}</span>`;
        streamItem.appendChild(textContentDiv);
    } else { // 假設是表格
        // 為了簡化，我們可以在這裡添加一個渲染表格的邏輯
        // 或者確保後端只發送字串格式的日誌
        const blockContentDiv = document.createElement('div');
        blockContentDiv.className = 'stream-block-content';
        const pre = document.createElement('pre');
        pre.textContent = JSON.stringify(message, null, 2);
        blockContentDiv.appendChild(pre);
        streamItem.appendChild(blockContentDiv);
    }

    mainStreamContainer.prepend(streamItem);
    while (mainStreamContainer.children.length > (appConfig.maxStreamLines || 50)) {
        mainStreamContainer.lastChild.remove();
    }
}


// ==================================================================
// WebSocket 連線管理
// ==================================================================

function connectMainApp() {
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    // 在 Colab/iframe 環境中，主機和埠號與頁面相同
    const mainAppUrl = `${wsProtocol}//${window.location.host}/ws/logs`;

    mainSocket = new WebSocket(mainAppUrl);

    mainSocket.onopen = () => {
        addMainStreamLog({
            icon: '✅', level: 'SYSTEM', levelClass: 'ok',
            message: '成功連接到鳳凰之心主引擎。', timestamp: Date.now()/1000
        });
    };

    mainSocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        switch (data.event_type) {
            case 'CONFIG_UPDATE':
                appConfig = data.payload;
                break;
            case 'DASHBOARD_UPDATE':
                updateDashboard(data.payload);
                break;
            case 'STREAM_LOG':
                addMainStreamLog(data.payload);
                break;
        }
    };

    mainSocket.onerror = (error) => {
        console.error("Main WebSocket Error:", error);
        addMainStreamLog({
            icon: '❌', level: 'ERROR', levelClass: 'error',
            message: '與主引擎的 WebSocket 連線中斷。請檢查後端日誌。', timestamp: Date.now()/1000
        });
    };

    mainSocket.onclose = () => {
        addMainStreamLog({
            icon: '⚠️', level: 'WARN', levelClass: 'warn',
            message: '與主引擎的連線已關閉。', timestamp: Date.now()/1000
        });
    };
}

// ==================================================================
// 腳本初始執行
// ==================================================================
function initializeDashboard() {
    // 直接顯示儀表板，隱藏啟動畫面
    bootScreen.classList.add('hidden');
    dashboard.classList.remove('hidden');
    // 連接到主應用 WebSocket
    connectMainApp();
}

document.addEventListener("DOMContentLoaded", initializeDashboard);
