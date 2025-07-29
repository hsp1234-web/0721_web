# -*- coding: utf-8 -*-
import asyncio
import subprocess
import sys
import json
from pathlib import Path
import os
import time
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
def run_backend_tasks():
    APPS_DIR = Path("apps")

    async def prepare_and_launch(app_name, port):
        try:
            app_path = APPS_DIR / app_name
            # 準備
            set_app_status(app_name, "preparing")
            venv_python = app_path / ".venv/bin/python"
            if not venv_python.exists():
                subprocess.run(f"uv venv --quiet -p {sys.executable}", cwd=app_path, shell=True, check=True)
                subprocess.run(f"{venv_python} -m pip install -q -r requirements.txt", cwd=app_path, shell=True, check=True)

            # 啟動
            set_app_status(app_name, "starting")
            env = os.environ.copy()
            env["PORT"] = str(port)
            subprocess.Popen([str(venv_python), "main.py"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # 健康檢查
            await asyncio.sleep(5)
            async with httpx.AsyncClient() as client:
                await client.get(f"http://localhost:{port}/", timeout=5)

            set_app_status(app_name, "running")
        except Exception as e:
            set_app_status(app_name, "failed")
            add_log(f"啟動 {app_name} 失敗: {e}")

    async def main_async():
        add_log("啟動程序開始...")
        tasks = [
            prepare_and_launch("quant", 8001),
            prepare_and_launch("transcriber", 8002),
            prepare_and_launch("main_dashboard", 8005)
        ]
        await asyncio.gather(*tasks)

        # 檢查是否全部成功
        if all(d["status"] == "running" for d in _state["apps"].values()):
            _state["action_url"] = "http://localhost:8000/dashboard" # 這是代理的地址
            add_log("所有服務已成功啟動！操作儀表板已就緒。")
        else:
            add_log("部分服務啟動失敗。")
        update_state_file()

    asyncio.run(main_async())

# --- 主程序 ---
if __name__ == "__main__":
    # 啟動背景任務
    backend_thread = threading.Thread(target=run_backend_tasks, daemon=True)
    backend_thread.start()

    # 啟動 TUI 渲染
    with Live(layout, screen=True, redirect_stderr=False) as live:
        try:
            while backend_thread.is_alive():
                layout["header"].update(Panel("🚀 鳳凰之心 - 系統啟動監控面板 🚀", style="bold magenta"))
                layout["status"].update(get_status_table())
                layout["final_link"].update(get_final_link_panel())
                layout["footer"].update(get_logs_panel())
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        finally:
            # 最終渲染
            layout["header"].update(Panel("✅ 啟動程序已結束", style="bold green"))
            layout["status"].update(get_status_table())
            layout["final_link"].update(get_final_link_panel())
            layout["footer"].update(get_logs_panel())
