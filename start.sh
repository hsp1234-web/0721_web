#!/bin/bash

# ==============================================================================
# 高效能 Web 應用程式 - 生產環境啟動腳本
# ==============================================================================
#
# 使用方法:
#   ./start.sh              # 在前台啟動伺服器，日誌會直接輸出到終端。
#   ./start.sh -d           # 以守護進程 (daemon) 模式在後台啟動。
#   ./start.sh stop         # 停止後台運行的伺服器。
#   ./start.sh status       # 檢查後台伺服器的狀態。
#   ./start.sh logs         # 查看後台伺服器的日誌。
#
# ==============================================================================

# --- 設定 ---
# 腳本所在的目錄
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
# Python 虛擬環境路徑 (如果使用)
VENV_PATH="$SCRIPT_DIR/.venv"
# PID 檔案，用於管理後台進程
PID_FILE="$SCRIPT_DIR/app.pid"
# 日誌檔案，用於後台模式
LOG_FILE="$SCRIPT_DIR/app.log"
# 依賴文件
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements/base.txt"

# 確保日誌是即時輸出的
export PYTHONUNBUFFERED=1

# --- 函數定義 ---

# 檢查並安裝依賴
install_deps() {
    echo "⚙️  正在檢查並安裝核心依賴..."
    # 優先使用 uv (如果存在)
    if command -v uv &> /dev/null; then
        uv pip sync "$REQUIREMENTS_FILE"
    else
        # 備用方案：使用 pip
        pip install -r "$REQUIREMENTS_FILE"
    fi
    if [ $? -ne 0 ]; then
        echo "❌ 依賴安裝失敗，請檢查環境。"
        exit 1
    fi
    echo "✅ 依賴已是最新狀態。"
}

# 啟動應用程式
start_app() {
    # 檢查是否已在運行
    if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null; then
        echo "⚠️  應用程式似乎已在運行 (PID: $(cat "$PID_FILE"))。請先停止它。"
        exit 1
    fi

    # 安裝依賴
    install_deps

    # 根據參數決定在前台或後台運行
    if [ "$1" == "-d" ]; then
        echo "🚀 正在以後台模式啟動應用程式..."
        # 在後台運行，並將 PID 寫入檔案
        # nohup 確保即使終端關閉，進程也能繼續運行
        nohup python "$SCRIPT_DIR/core.py" --port 8000 > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        sleep 2
        if ps -p $(cat "$PID_FILE") > /dev/null; then
            echo "✅ 應用程式已在後台啟動 (PID: $(cat "$PID_FILE"))。日誌請查看: $LOG_FILE"
        else
            echo "❌ 應用程式啟動失敗，請檢查日誌: $LOG_FILE"
            rm "$PID_FILE"
            exit 1
        fi
    else
        echo "🚀 正在以前台模式啟動應用程式... (按下 Ctrl+C 停止)"
        # 直接在前台運行
        python "$SCRIPT_DIR/core.py" --port 8000
    fi
}

# 停止應用程式
stop_app() {
    if [ ! -f "$PID_FILE" ]; then
        echo "🤷 找不到 PID 檔案，應用程式可能未在後台運行。"
        return
    fi

    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "🛑 正在停止應用程式 (PID: $PID)..."
        # 發送 SIGTERM 信號，讓 core.py 優雅關閉
        kill $PID
        # 等待進程結束
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null; then
                echo "✅ 應用程式已停止。"
                rm "$PID_FILE"
                return
            fi
            sleep 1
        done
        echo "⚠️  應用程式關閉超時，正在強制終止..."
        kill -9 $PID
        echo "✅ 應用程式已被強制終止。"
    else
        echo "🤷 找不到對應的進程 (PID: $PID)，可能已被手動關閉。"
    fi
    rm "$PID_FILE"
}

# --- 主邏輯 ---
cd "$SCRIPT_DIR"

case "$1" in
    -d|--daemon)
        start_app -d
        ;;
    stop)
        stop_app
        ;;
    restart)
        stop_app
        sleep 1
        start_app -d
        ;;
    status)
        if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null; then
            echo "🟢 應用程式正在運行 (PID: $(cat "$PID_FILE"))。"
        else
            echo "🔴 應用程式未在運行。"
        fi
        ;;
    logs)
        if [ -f "$LOG_FILE" ]; then
            tail -f "$LOG_FILE"
        else
            echo "🤷 找不到日誌檔案: $LOG_FILE"
        fi
        ;;
    ""|start)
        start_app
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs|-d}"
        exit 1
        ;;
esac
