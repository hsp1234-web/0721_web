# -*- coding: utf-8 -*-
import asyncio
import subprocess
import sys
import json
from pathlib import Path
import os
import time
import shutil
import threading
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.text import Text

# --- 共享狀態管理 ---
STATE_FILE = Path(os.getenv("STATE_FILE", "/tmp/phoenix_state.json"))
_state = {
    "apps": {
        "quant": {"status": "pending"},
        "transcriber": {"status": "pending"},
        "main_dashboard": {"status": "pending"}
    },
    "logs": [],
    "action_url": None
}

def update_state_file():
    with open(STATE_FILE, 'w') as f:
        json.dump(_state, f)

def add_log(message):
    _state["logs"].append(f"[{time.strftime('%H:%M:%S')}] {message}")
    if len(_state["logs"]) > 20:
        _state["logs"].pop(0)
    update_state_file()

def set_app_status(app_name, status):
    _state["apps"][app_name]["status"] = status
    add_log(f"App '{app_name}' status changed to '{status}'")

# --- TUI 渲染 ---
console = Console()
layout = Layout()

layout.split(
    Layout(name="header", size=3),
    Layout(ratio=1, name="main"),
    Layout(size=10, name="footer"),
)
layout["main"].split_row(Layout(name="side"), Layout(name="body", ratio=2))
layout["side"].split(Layout(name="status"), Layout(name="final_link"))
layout["footer"].update(Panel("即時日誌", border_style="green"))

def get_status_table():
    table = Table(title="後端服務狀態", expand=True, border_style="blue")
    table.add_column("服務", justify="right", style="cyan")
    table.add_column("狀態", style="magenta")

    status_map = {
        "pending": "[⚪] 等待中...",
        "preparing": "[🟡] 準備中...",
        "starting": "[🟡] 啟動中...",
        "running": "[🟢] 運行中",
        "failed": "[🔴] 失敗"
    }
    for app, details in _state["apps"].items():
        table.add_row(app.capitalize(), status_map.get(details["status"], details["status"]))
    return table

def get_logs_panel():
    log_text = "\n".join(_state["logs"])
    return Panel(Text(log_text, justify="left"), title="📜 即時啟動日誌", border_style="green")

def get_final_link_panel():
    if _state["action_url"]:
        text = Text(f"👉 點此開啟操作儀表板 👈\n{_state['action_url']}", justify="center", style="bold blue")
        return Panel(text, title="✅ 啟動完成 - 進行操作", border_style="cyan")
    return Panel("等待所有服務就緒...", title="⏳ 操作入口", border_style="yellow")

# --- 核心啟動邏輯 ---
# --- 核心啟動邏輯 ---
async def launch_app(app_name, port):
    """僅負責啟動單個應用。"""
    APPS_DIR = Path("apps")
    app_path = APPS_DIR / app_name
    try:
        set_app_status(app_name, "starting")
        env = os.environ.copy()
        env["PORT"] = str(port)
        # 使用當前環境的 Python 直譯器
        # 在除錯時，可以將 stderr=subprocess.STDOUT，以捕獲啟動錯誤
        subprocess.Popen([sys.executable, "main.py"], cwd=app_path, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        # 等待服務啟動
        await asyncio.sleep(5)
        set_app_status(app_name, "running")

    except Exception as e:
        set_app_status(app_name, "failed")
        add_log(f"啟動 {app_name} 失敗: {e}")
        raise

async def main_logic():
    """核心的循序啟動邏輯，被 TUI 和純腳本模式共享。"""
    add_log("啟動程序開始 (循序模式)...")
    app_configs = [
        {"name": "quant", "port": 8001},
        {"name": "transcriber", "port": 8002},
        {"name": "main_dashboard", "port": 8005}
    ]

    # 平行啟動所有 App
    tasks = [launch_app(config['name'], config['port']) for config in app_configs]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result, config in zip(results, app_configs):
        if isinstance(result, Exception):
            # launch_app 內部已經記錄了日誌
            pass

    # 檢查是否全部成功
    if all(d["status"] == "running" for d in _state["apps"].values()):
        _state["action_url"] = "http://localhost:8000/dashboard"
        add_log("所有服務已成功啟動！操作儀表板已就緒。")
    else:
        add_log("部分服務啟動失敗。")
    update_state_file()

def main_tui():
    """TUI 模式：為人類使用者提供豐富的視覺化介面。"""
    # 在背景執行緒中運行核心異步邏輯
    backend_thread = threading.Thread(target=lambda: asyncio.run(main_logic()), daemon=True)
    backend_thread.start()

    # 主執行緒負責 TUI 渲染
    with Live(layout, screen=True, redirect_stderr=False) as live:
        try:
            while backend_thread.is_alive():
                layout["header"].update(Panel("🚀 鳳凰之心 - 系統啟動監控面板 🚀", style="bold magenta"))
                layout["status"].update(get_status_table())
                layout["final_link"].update(get_final_link_panel())
                layout["footer"].update(get_logs_panel())
                time.sleep(0.5)
        except KeyboardInterrupt:
            add_log("使用者手動中斷。")
        finally:
            backend_thread.join(timeout=5)
            layout["header"].update(Panel("✅ 啟動程序已結束", style="bold green"))
            layout["status"].update(get_status_table())
            layout["final_link"].update(get_final_link_panel())
            layout["footer"].update(get_logs_panel())

# --- 主程序 ---
if __name__ == "__main__":
    # 檢查是否在非互動式環境中
    if os.environ.get("TERM") == "dumb" or not sys.stdout.isatty():
        # 在純腳本模式下，直接、同步地執行核心邏輯
        print("--- 正在以純腳本模式啟動 ---")
        asyncio.run(main_logic())
        print("--- 純腳本模式啟動完成 ---")
    else:
        # 在互動式模式下，啟動 TUI
        main_tui()
