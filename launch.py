# -*- coding: utf-8 -*-
import asyncio
import subprocess
import sys
import sqlite3
from pathlib import Path
import os
import time
import json

# --- 資料庫設定 ---
DB_FILE = Path(os.getenv("DB_FILE", "/tmp/state.db"))

def setup_database():
    """初始化資料庫和資料表"""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # 狀態表：只有一筆紀錄，不斷更新
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS status_table (
            id INTEGER PRIMARY KEY,
            current_stage TEXT,
            apps_status TEXT,
            action_url TEXT,
            cpu_usage REAL,
            ram_usage REAL
        )
        """)
        # 日誌表：持續插入新紀錄
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            level TEXT,
            message TEXT
        )
        """)
        # 初始化狀態表
        cursor.execute("INSERT OR IGNORE INTO status_table (id, current_stage) VALUES (1, 'pending')")
        conn.commit()

def add_log(level, message):
    """將日誌寫入資料庫"""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO log_table (level, message) VALUES (?, ?)", (level, message))
        conn.commit()

def update_status(stage=None, apps_status=None, action_url=None, cpu=None, ram=None):
    """更新狀態表中的紀錄"""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        updates = []
        params = []
        if stage:
            updates.append("current_stage = ?")
            params.append(stage)
        if apps_status:
            updates.append("apps_status = ?")
            params.append(json.dumps(apps_status))
        if action_url:
            updates.append("action_url = ?")
            params.append(action_url)
        if cpu is not None:
            updates.append("cpu_usage = ?")
            params.append(cpu)
        if ram is not None:
            updates.append("ram_usage = ?")
            params.append(ram)

        if updates:
            query = f"UPDATE status_table SET {', '.join(updates)} WHERE id = 1"
            cursor.execute(query, params)
            conn.commit()

# --- 核心啟動邏輯 ---
async def launch_app(app_name, port, apps_status):
    """啟動單個應用，並支援快速測試模式。"""
    apps_status[app_name] = "starting"
    update_status(apps_status=apps_status)
    add_log("INFO", f"App '{app_name}' status changed to 'starting'")

    if os.getenv("FAST_TEST_MODE") == "true":
        await asyncio.sleep(2)
        apps_status[app_name] = "running"
        update_status(apps_status=apps_status)
        add_log("INFO", f"App '{app_name}' in fast test mode, skipping actual launch.")
        return

    APPS_DIR = Path("apps")
    app_path = APPS_DIR / app_name
    try:
        env = os.environ.copy()
        env["PORT"] = str(port)
        subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=app_path, env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        )
        await asyncio.sleep(10)
        apps_status[app_name] = "running"
        update_status(apps_status=apps_status)
        add_log("INFO", f"App '{app_name}' status changed to 'running'")
    except Exception as e:
        apps_status[app_name] = "failed"
        update_status(apps_status=apps_status)
        add_log("ERROR", f"啟動 {app_name} 失敗: {e}")
        raise

async def main_logic():
    """核心的循序啟動邏輯"""
    add_log("INFO", "啟動程序開始...")
    update_status(stage="initializing")

    apps_status = {
        "quant": "pending",
        "transcriber": "pending",
        "main_dashboard": "pending"
    }
    update_status(apps_status=apps_status)

    app_configs = [
        {"name": "quant", "port": 8001},
        {"name": "transcriber", "port": 8002},
        {"name": "main_dashboard", "port": 8005}
    ]

    tasks = [launch_app(config['name'], config['port'], apps_status) for config in app_configs]
    await asyncio.gather(*tasks, return_exceptions=True)

    if all(status == "running" for status in apps_status.values()):
        final_url = "http://localhost:8000/dashboard"
        update_status(stage="completed", action_url=final_url)
        add_log("INFO", "所有服務已成功啟動！操作儀表板已就緒。")
    else:
        update_status(stage="failed")
        add_log("ERROR", "部分服務啟動失敗。")

# --- 主程序 ---
if __name__ == "__main__":
    setup_database()
    try:
        asyncio.run(main_logic())
    except Exception as e:
        add_log("CRITICAL", f"主程序發生未預期錯誤: {e}")
        update_status(stage="critical_failure")
