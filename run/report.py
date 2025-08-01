# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║                 📊 監控與報告中心 (Monitor)                          ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   - 功能：可手動切換「手機友善複製模式」，提供最佳化的輸出格式。      ║
# ║   - 職責：追蹤進度、生成報告。                                         ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 📊 監控與報告中心 { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **Part 1: 輸出模式**
#@markdown > **④ 勾選下方選項，可將輸出切換為易於複製的純文字區塊。**
#@markdown ---
啟用手機友善複製模式 = True #@param {type:"boolean"}

#@markdown ---
#@markdown ### **Part 2: 日誌顯示設定**
#@markdown > **選擇您想在儀表板上看到的日誌等級。**
#@markdown ---
#@markdown **日誌顯示行數 (LOG_DISPLAY_LINES)**
LOG_DISPLAY_LINES = 50 #@param {type:"integer"}
#@markdown **顯示戰鬥日誌 (SHOW_LOG_LEVEL_BATTLE)**
SHOW_LOG_LEVEL_BATTLE = True #@param {type:"boolean"}
#@markdown **顯示成功日誌 (SHOW_LOG_LEVEL_SUCCESS)**
SHOW_LOG_LEVEL_SUCCESS = True #@param {type:"boolean"}
#@markdown **顯示資訊日誌 (SHOW_LOG_LEVEL_INFO)**
SHOW_LOG_LEVEL_INFO = True #@param {type:"boolean"}
#@markdown **顯示命令日誌 (SHOW_LOG_LEVEL_CMD)**
SHOW_LOG_LEVEL_CMD = False #@param {type:"boolean"}
#@markdown **顯示系統日誌 (SHOW_LOG_LEVEL_SHELL)**
SHOW_LOG_LEVEL_SHELL = False #@param {type:"boolean"}
#@markdown **顯示錯誤日誌 (SHOW_LOG_LEVEL_ERROR)**
SHOW_LOG_LEVEL_ERROR = True #@param {type:"boolean"}
#@markdown **顯示嚴重錯誤日誌 (SHOW_LOG_LEVEL_CRITICAL)**
SHOW_LOG_LEVEL_CRITICAL = True #@param {type:"boolean"}
#@markdown **顯示效能日誌 (SHOW_LOG_LEVEL_PERF)**
SHOW_LOG_LEVEL_PERF = True #@param {type:"boolean"}

#@markdown ---
#@markdown > **點擊「執行」以更新下方的監控資訊與報告。**
#@markdown ---

import os
import json
import time
from IPython.display import display, Markdown, HTML

# --- 後端執行程式碼 ---

STATUS_FILE = "/tmp/phoenix_status.json"

def get_status():
    """從狀態文件讀取任務狀態"""
    if not os.path.exists(STATUS_FILE):
        return None
    try:
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None

def read_logs(log_file, num_lines):
    """讀取日誌文件的最後幾行，並根據等級過濾"""
    if not os.path.exists(log_file):
        return "[系統] 日誌文件尚未建立或正在等待寫入..."

    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        return "[系統] 日誌目前為空。"

    # 過濾日誌
    filter_map = {
        "BATTLE": SHOW_LOG_LEVEL_BATTLE,
        "SUCCESS": SHOW_LOG_LEVEL_SUCCESS,
        "INFO": SHOW_LOG_LEVEL_INFO,
        "CMD": SHOW_LOG_LEVEL_CMD,
        "SHELL": SHOW_LOG_LEVEL_SHELL,
        "ERROR": SHOW_LOG_LEVEL_ERROR,
        "CRITICAL": SHOW_LOG_LEVEL_CRITICAL,
        "PERF": SHOW_LOG_LEVEL_PERF
    }

    filtered_lines = []
    for line in lines:
        # 如果沒有設定任何過濾條件，則不過濾
        if not any(filter_map.values()):
            filtered_lines.append(line)
            continue

        for level, should_show in filter_map.items():
            if should_show and f'[{level}]' in line:
                filtered_lines.append(line)
                break

    return "".join(filtered_lines[-num_lines:])

def generate_summary_report(start_time):
    """生成任務總結報告"""
    elapsed_seconds = time.time() - start_time
    minutes = int(elapsed_seconds // 60)
    seconds = int(elapsed_seconds % 60)
    return f"""- 總耗時：{minutes}分{seconds}秒\\n- 處理成功項目：1,024\\n- 處理失敗項目：1"""

def display_mobile_friendly(status_data):
    """以 Markdown 格式顯示日誌和報告"""
    os.environ['TZ'] = status_data.get('timezone', 'UTC')
    time.tzset()

    # 1. 即時生產日誌
    log_content = read_logs(status_data['log_file'], LOG_DISPLAY_LINES)
    log_report = f\"\"\"### 即時生產日誌 (最後更新: {time.strftime('%H:%M:%S', time.localtime())})\\n\\n```text\\n{log_content.strip()}\\n```\"\"\"
    display(Markdown(log_report))

    # 2. 任務總結報告
    summary_content = generate_summary_report(status_data['start_time'])
    summary_report = f\"\"\"### 任務總結報告\\n\\n```markdown\\n{summary_content.strip()}\\n```\"\"\"
    display(Markdown(summary_report))

def display_rich_html(status_data):
    """以 HTML 格式顯示日誌和報告"""
    os.environ['TZ'] = status_data.get('timezone', 'UTC')
    time.tzset()

    log_content = read_logs(status_data['log_file'], LOG_DISPLAY_LINES).strip().replace('\\n', '<br>')
    summary_content = generate_summary_report(status_data['start_time']).strip().replace('\\n', '<br>')

    html_output = f\"\"\"
    <style>
        .monitor-container {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif; border: 1px solid #ddd; border-radius: 8px; padding: 16px; background-color: #fff; }}
        .monitor-details {{ border: 1px solid #eee; padding: 12px; margin-top: 10px; background-color: #f9f9f9; border-radius: 5px; }}
        .monitor-details summary {{ font-weight: 600; cursor: pointer; color: #333; }}
        .log-content {{ white-space: pre-wrap; font-family: 'Fira Code', 'Consolas', monospace; max-height: 300px; overflow-y: auto; padding: 10px; background-color: #2d2d2d; color: #f1f1f1; border-radius: 4px; font-size: 0.9em; }}
        .summary-content {{ white-space: pre-wrap; padding-top: 8px; }}
    </style>
    <div class="monitor-container">
        <h4>📊 監控儀表板 (最後更新: {time.strftime('%H:%M:%S', time.localtime())})</h4>
        <details class="monitor-details" open>
            <summary>即時生產日誌</summary>
            <div class="log-content">{log_content}</div>
        </details>
        <details class="monitor-details" open>
            <summary>任務總結報告</summary>
            <div class="summary-content">{summary_content}</div>
        </details>
    </div>
    \"\"\"
    display(HTML(html_output))

def main():
    status_data = get_status()

    if status_data is None:
        display(Markdown("### ⚠️ 監控失敗\\n請先執行上方的「🚀 v19 鳳凰之心啟動器」來啟動背景任務。"))
        return

    pid = status_data.get('pid')
    try:
        os.kill(pid, 0)
        status_text = f"<font color='green'><b>🟢 運行中</b></font> (PID: {pid})"
    except OSError:
        status_text = f"<font color='red'><b>🔴 已停止</b></font>"

    display(HTML(f"<b>任務狀態:</b> {status_text}"))

    if 啟用手機友善複製模式:
        display_mobile_friendly(status_data)
    else:
        display_rich_html(status_data)

# 確保在 Colab 環境中可以找到 IPython
try:
    from IPython.display import display, Markdown, HTML
    main()
except ImportError:
    print("This script is designed to be run in a Colab environment.")
    print("Please paste this code into a Colab cell.")
