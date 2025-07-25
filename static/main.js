// ==================================================================
// 全域變數與 DOM 元素快取
// ==================================================================
let mainSocket;
let bootstrapSocket;
let appConfig = {};
const progressBars = {}; // 儲存進度條的 DOM 元素

const bootScreen = document.getElementById('boot-screen');
const dashboard = document.getElementById('dashboard');
const topPanel = {
    stats: document.getElementById('ascii-stats'),
    services: document.getElementById('service-status')
};
const mainStreamContainer = document.getElementById('main-stream-container');
const statusBar = document.getElementById('status-bar');

// ==================================================================
// 啟動畫面 (Boot Screen) 渲染函式
// ==================================================================

/**
 * 在啟動畫面中渲染一個文字步驟。
 * @param {object} payload - { text: string, type: string }
 */
function renderBootStep(payload) {
    const line = document.createElement('pre');
    line.innerHTML = `<span class="${payload.type || ''}">${payload.text}</span>`;
    bootScreen.appendChild(line);
    bootScreen.scrollTop = bootScreen.scrollHeight;
}

/**
 * 開始渲染一個進度條。
 * @param {object} payload - { name: string, size: string }
 */
function renderProgressBarStart(payload) {
    const line = document.createElement('div');
    line.className = 'progress-bar-container';

    const text = document.createElement('span');
    text.className = 'label';
    text.textContent = `⏳ 安裝中: ${payload.name.padEnd(12, ' ')}`;

    const progressBar = document.createElement('pre');
    progressBar.className = 'dim';
    progressBar.textContent = `[${'░'.repeat(10)}] 0% (${payload.size})`;

    line.appendChild(text);
    line.appendChild(progressBar);
    bootScreen.appendChild(line);

    // 儲存對 DOM 元素的引用，以便後續更新
    progressBars[payload.name] = { text, progressBar };
    bootScreen.scrollTop = bootScreen.scrollHeight;
}

/**
 * 更新一個已存在的進度條。
 * @param {object} payload - { name: string, progress: number }
 */
function renderProgressBarUpdate(payload) {
    const bar = progressBars[payload.name];
    if (!bar) return;

    const p = payload.progress;
    const filled = '█'.repeat(Math.round(p / 10));
    const empty = '░'.repeat(10 - Math.round(p / 10));
    bar.progressBar.textContent = `[${filled}] ${p}%`;

    if (p >= 100) {
        bar.text.innerHTML = `✅ <span class="ok">已安裝: ${payload.name.padEnd(12, ' ')}</span>`;
    }
}

/**
 * 渲染一個數據表格。
 * @param {object} payload - { title: string, rows: array }
 */
function renderBootTable(payload) {
    const table = document.createElement('div');
    table.className = 'data-stream-table';
    let content = `<div class="ds-row ds-header"><div class="ds-cell">${payload.title}</div></div>`;
    content += `<div class="ds-row ds-separator"><div class="ds-cell"></div></div>`;
    payload.rows.forEach(rowData => {
        content += `<div class="ds-row">`;
        rowData.forEach(cellData => {
            content += `<div class="ds-cell">${cellData}</div>`;
        });
        content += `</div>`;
    });
    table.innerHTML = content;
    bootScreen.appendChild(table);
    bootScreen.scrollTop = bootScreen.scrollHeight;
}

/**
 * 從啟動畫面過渡到主儀表板。
 */
function transitionToMainDashboard() {
    renderBootStep({ text: "正在切換至主駕駛艙...", type: "info" });
    setTimeout(() => {
        bootScreen.classList.add('hidden');
        dashboard.classList.remove('hidden');
        if (bootstrapSocket) bootstrapSocket.close();
        connectMainApp();
    }, 1500); // 延遲 1.5 秒以顯示最後的訊息
}

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
        const blockContentDiv = document.createElement('div');
        blockContentDiv.className = 'stream-block-content';
        blockContentDiv.appendChild(renderBootTable(message.title, message.rows));
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

function connectBootstrap(port) {
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const bootstrapUrl = `${wsProtocol}//${window.location.hostname}:${port}/ws/bootstrap`;

    bootstrapSocket = new WebSocket(bootstrapUrl);

    bootstrapSocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        switch (data.event_type) {
            case 'BOOT_STEP':
                renderBootStep(data.payload);
                break;
            case 'BOOT_PROGRESS_START':
                renderProgressBarStart(data.payload);
                break;
            case 'BOOT_PROGRESS_UPDATE':
                renderProgressBarUpdate(data.payload);
                break;
            case 'BOOT_TABLE':
                renderBootTable(data.payload);
                break;
            case 'BOOT_COMPLETE':
                transitionToMainDashboard();
                break;
        }
    };

    bootstrapSocket.onerror = (error) => {
        console.error("Bootstrap WebSocket Error:", error);
        renderBootStep({ text: "❌ 引導伺服器連線錯誤", type: "error" });
    };
}

function connectMainApp() {
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const mainAppUrl = `${wsProtocol}//${window.location.hostname}:${appConfig.mainPort}/ws`; // 主應用的 port 需要從某處獲取

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
    };
}

// ==================================================================
// 腳本初始執行
// ==================================================================
document.addEventListener("DOMContentLoaded", () => {
    const urlParams = new URLSearchParams(window.location.search);
    const bootstrapPort = urlParams.get('bootstrapPort');

    if (bootstrapPort) {
        connectBootstrap(bootstrapPort);
    } else {
        // Fallback for direct testing or if bootstrap fails
        bootScreen.innerHTML = '<pre class="error">錯誤：未找到引導伺服器埠號。\n無法啟動真實啟動序列。</pre>';
    }
});
