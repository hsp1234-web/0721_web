document.addEventListener("DOMContentLoaded", () => {
    const logPanel = document.getElementById("log-panel");
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const socket = new WebSocket(`${wsProtocol}//${window.location.host}/ws/logs`);

    const createLogEntry = (log) => {
        const entry = document.createElement("div");
        entry.className = "log-entry";

        const timestampSpan = document.createElement("span");
        timestampSpan.className = "log-timestamp";
        timestampSpan.textContent = new Date(log.timestamp * 1000).toLocaleTimeString();

        const levelSpan = document.createElement("span");
        levelSpan.className = `log-level-${log.level}`;
        levelSpan.textContent = `[${log.level}]`;

        const messageSpan = document.createElement("span");
        messageSpan.className = "log-message";
        messageSpan.textContent = log.message;

        entry.appendChild(timestampSpan);
        entry.appendChild(levelSpan);
        entry.appendChild(document.createTextNode(" ")); // for spacing
        entry.appendChild(messageSpan);

        return entry;
    };

    socket.onopen = () => {
        const entry = createLogEntry({
            timestamp: Date.now() / 1000,
            level: "INFO",
            message: "成功連接到引擎遙測數據通道。"
        });
        logPanel.appendChild(entry);
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.event_type === "LOG_MESSAGE") {
                const log = data.payload;
                const entry = createLogEntry(log);
                logPanel.appendChild(entry);
                // 自動滾動到底部
                logPanel.scrollTop = logPanel.scrollHeight;
            }
        } catch (e) {
            console.error("無法解析收到的日誌訊息:", e);
            const entry = createLogEntry({
                timestamp: Date.now() / 1000,
                level: "ERROR",
                message: "收到一個無效的日誌格式。"
            });
            logPanel.appendChild(entry);
        }
    };

    socket.onclose = () => {
        const entry = createLogEntry({
            timestamp: Date.now() / 1000,
            level: "WARNING",
            message: "與引擎的遙測數據通道已斷開。"
        });
        logPanel.appendChild(entry);
    };

    socket.onerror = (error) => {
        console.error("WebSocket 錯誤:", error);
        const entry = createLogEntry({
            timestamp: Date.now() / 1000,
            level: "ERROR",
            message: "與遙測通道的連線發生錯誤。"
        });
        logPanel.appendChild(entry);
    };
});
