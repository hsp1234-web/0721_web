// ==============================================================================
// 全域變數與狀態管理
// ==============================================================================
let socket;
let appConfig = {}; // 儲存從主伺服器收到的設定
let bootstrapPort;

// DOM 元素快取
const dashboard = document.getElementById('dashboard');
const installLogPanel = document.getElementById('install-log-panel');
const mainLogPanel = document.getElementById('main-log-panel');
const systemStatus = document.getElementById('system-status');

// ==============================================================================
// UI 控制函式
// ==============================================================================

/**
 * 顯示安裝日誌介面，隱藏主駕駛艙。
 */
function showInstallationUI() {
    dashboard.style.display = 'none';
    installLogPanel.style.display = 'block';
    addInstallLog("正在連接到引導伺服器以獲取安裝日誌...", "info");
}

/**
 * 顯示主駕駛艙介面，隱藏安裝日誌。
 */
function showFullDashboardUI() {
    installLogPanel.style.display = 'none';
    dashboard.style.display = 'flex';
    addMainLog("主駕駛艙介面已啟動。", "INFO");
}

/**
 * 在安裝日誌面板中新增一條日誌。
 * @param {string} message - 日誌訊息。
 * @param {string} level - 日誌級別 (e.g., 'info', 'error')。
 */
function addInstallLog(message, level = 'log') {
    const entry = document.createElement('div');
    entry.className = `log-entry log-level-${level.toUpperCase()}`;
    entry.textContent = message;
    installLogPanel.appendChild(entry);
    installLogPanel.scrollTop = installLogPanel.scrollHeight;
}

/**
 * 在主駕駛艙的日誌面板中新增一條日誌。
 * @param {string} message - 日誌訊息。
 * @param {string} level - 日誌級別。
 */
function addMainLog(message, level = 'INFO') {
    const timestamp = new Date().toLocaleTimeString();
    const newLogEntry = document.createElement('div');
    newLogEntry.className = 'log-entry';
    newLogEntry.innerHTML = `<span class="log-timestamp">${timestamp}</span> <span class="log-level-${level}">[${level}]</span> ${message}`;

    mainLogPanel.appendChild(newLogEntry);
    if (appConfig.LOG_DISPLAY_LINES && mainLogPanel.children.length > appConfig.LOG_DISPLAY_LINES) {
        mainLogPanel.removeChild(mainLogPanel.firstChild);
    }
    mainLogPanel.scrollTop = mainLogPanel.scrollHeight;
}

/**
 * 更新系統狀態顯示。
 * @param {object} perf - 性能數據。
 */
function updateStatus(perf) {
    const cpu = perf.cpu_usage.toFixed(1);
    const ram = (perf.ram_usage / 1024 / 1024).toFixed(0);
    systemStatus.textContent = `CPU: ${cpu}% | RAM: ${ram} MB`;
}


// ==============================================================================
// WebSocket 連線邏輯
// ==============================================================================

/**
 * 連接到引導伺服器。
 */
function connectBootstrap() {
    showInstallationUI();
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const bootstrapUrl = `${wsProtocol}//${window.location.hostname}:${bootstrapPort}/ws/bootstrap`;

    socket = new WebSocket(bootstrapUrl);

    socket.onopen = () => addInstallLog("✅ 成功連接到引導伺服器。", "info");

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        switch (data.event_type) {
            case 'INSTALL_LOG':
                addInstallLog(data.payload, 'log');
                break;
            case 'INSTALL_ERROR':
                addInstallLog(`❌ ${data.payload}`, 'error');
                break;
            case 'INSTALL_COMPLETE':
                addInstallLog("✅ 所有依賴已成功安裝。", "info");
                addInstallLog("正在準備切換至主應用伺服器...", "info");
                socket.close();
                // 延遲切換，給主伺服器啟動時間
                setTimeout(connectMainApp, 3000);
                break;
        }
    };

    socket.onclose = () => addInstallLog("與引導伺服器的連線已關閉。", "info");
    socket.onerror = (error) => {
        console.error("Bootstrap WebSocket Error:", error);
        addInstallLog("引導伺服器連線發生錯誤。", "error");
    };
}

/**
 * 連接到主應用伺服器。
 */
function connectMainApp() {
    showFullDashboardUI();
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const mainAppUrl = `${wsProtocol}//${window.location.host}/ws`;

    socket = new WebSocket(mainAppUrl);

    socket.onopen = () => addMainLog("成功連接到鳳凰之心主引擎。", "INFO");

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        switch (data.event_type) {
            case 'CONFIG_UPDATE':
                appConfig = data.payload;
                addMainLog("後端配置已接收並應用。", "INFO");
                break;
            case 'PERFORMANCE_UPDATE':
                updateStatus(data.payload);
                break;
            case 'LOG_MESSAGE':
                const log = data.payload;
                addMainLog(log.message, log.level);
                break;
            default:
                addMainLog(`收到未知的事件類型: ${data.event_type}`, "WARNING");
        }
    };

    socket.onclose = () => addMainLog("與主引擎的連線已中斷。", "WARNING");
    socket.onerror = (error) => {
        console.error("Main App WebSocket Error:", error);
        addMainLog("與主引擎的連線發生錯誤。", "ERROR");
    };
}

// ==============================================================================
// 初始啟動
// ==============================================================================
document.addEventListener("DOMContentLoaded", () => {
    // 從 URL 查詢參數中獲取引導伺服器的埠號
    const urlParams = new URLSearchParams(window.location.search);
    bootstrapPort = urlParams.get('bootstrapPort');

    if (bootstrapPort) {
        connectBootstrap();
    } else {
        // 如果沒有提供 bootstrapPort，則直接嘗試連接主應用
        // 這保持了舊的、非分段加載模式的相容性
        console.warn("未在 URL 中找到 bootstrapPort，將直接嘗試連接主應用。");
        connectMainApp();
    }
});
