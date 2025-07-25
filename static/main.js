let appConfig = {};
const logPanel = document.getElementById("log-panel");
const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const socket = new WebSocket(`${wsProtocol}//${window.location.host}/ws`);

const addStreamItem = (message, level = 'INFO') => {
    const timestamp = new Date().toLocaleTimeString();
    const newLogEntry = document.createElement('div');
    newLogEntry.innerHTML = `<span class="log-timestamp">${timestamp}</span> <span class="log-level-${level}">[${level}]</span> ${message}`;
    logPanel.appendChild(newLogEntry);

    // 根據 appConfig 中的設定來限制日誌行數
    if (appConfig.LOG_DISPLAY_LINES && logPanel.children.length > appConfig.LOG_DISPLAY_LINES) {
        logPanel.removeChild(logPanel.firstChild);
    }
    logPanel.scrollTop = logPanel.scrollHeight;
};

socket.onopen = () => {
    addStreamItem("成功連接到鳳凰之心後端。正在等待配置指令...", "INFO");
};

socket.onmessage = (event) => {
    const parsedData = JSON.parse(event.data);

    switch (parsedData.event_type) {
        case 'CONFIG_UPDATE':
            appConfig = parsedData.payload;
            addStreamItem("後端配置已接收並應用。", "INFO");
            // 可以在此處根據新配置觸發一些前端行為
            break;
        case 'PERFORMANCE_UPDATE':
            // 這裡可以將性能數據顯示在儀表板的其他部分
            // 為了簡化，我們暫時仍在日誌流中顯示
            const perf = parsedData.payload;
            addStreamItem(`CPU: ${perf.cpu_usage.toFixed(1)}% | RAM: ${(perf.ram_usage / 1024 / 1024).toFixed(0)}MB`, "DEBUG");
            break;
        case 'LOG_MESSAGE':
            const log = parsedData.payload;
            addStreamItem(log.message, log.level);
            break;
        default:
            addStreamItem(`收到未知的事件類型: ${parsedData.event_type}`, "WARNING");
    }
};

socket.onclose = () => {
    addStreamItem("與後端的連線已中斷。", "WARNING");
};

socket.onerror = (error) => {
    console.error("WebSocket Error:", error);
    addStreamItem("WebSocket 連線出現錯誤。", "ERROR");
};
