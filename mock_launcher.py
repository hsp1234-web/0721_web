# -*- coding: utf-8 -*-
import asyncio
import sqlite3
from pathlib import Path
import os
import time
import json
import random

# --- 資料庫設定 ---
DB_FILE = Path(os.getenv("DB_FILE", "/tmp/state.db"))

def setup_database():
    """初始化資料庫和資料表"""
    if DB_FILE.exists():
        os.remove(DB_FILE)
        print(f"舊的資料庫檔案 {DB_FILE} 已刪除。")

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS status_table (
            id INTEGER PRIMARY KEY,
            current_stage TEXT,
            total_tasks INTEGER,
            completed_tasks INTEGER,
            current_task_name TEXT,
            apps_status TEXT,
            action_url TEXT,
            cpu_usage REAL,
            ram_usage REAL
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            level TEXT,
            summary TEXT,
            type TEXT DEFAULT 'text',
            payload TEXT
        )
        """)
        cursor.execute("INSERT OR IGNORE INTO status_table (id, current_stage, total_tasks, completed_tasks, cpu_usage, ram_usage) VALUES (1, 'pending', 0, 0, 0.0, 0.0)")
        conn.commit()
    print(f"資料庫 {DB_FILE} 已成功初始化。")

def add_log(level, summary, type='text', payload=None):
    """將日誌寫入資料庫"""
    with sqlite3.connect(DB_FILE) as conn:
        payload_str = json.dumps(payload) if payload is not None else None
        conn.execute(
            "INSERT INTO log_table (level, summary, type, payload) VALUES (?, ?, ?, ?)",
            (level, summary, type, payload_str)
        )
        conn.commit()

def update_status(**kwargs):
    """更新狀態表"""
    with sqlite3.connect(DB_FILE) as conn:
        updates = [f"{key} = ?" for key in kwargs]
        params = list(kwargs.values())
        query = f"UPDATE status_table SET {', '.join(updates)} WHERE id = 1"
        conn.execute(query, params)
        conn.commit()

async def mock_main_logic():
    """模擬核心啟動邏輯"""
    add_log("INFO", "模擬啟動程序開始...")
    update_status(current_stage="initializing")

    # --- 模擬安裝 ---
    mock_packages = [
        "fastapi", "uvicorn", "pydantic", "rich", "psutil", "sqlalchemy",
        "alembic", "pytest", "requests", "jinja2", "websockets", "numpy",
        "pandas", "scikit-learn", "torch"
    ]
    total_tasks = len(mock_packages)
    update_status(current_stage="installing", total_tasks=total_tasks, completed_tasks=0, current_task_name="正在準備...")
    add_log("INFO", f"開始模擬安裝 {total_tasks} 個依賴套件...")

    for i, package in enumerate(mock_packages):
        update_status(completed_tasks=i + 1, current_task_name=package)
        add_log("INFO", f"正在安裝 {package}...")
        if random.random() < 0.1: # 10% 的機率產生一個警告日誌
             add_log("WARNING", f"套件 {package} 的一個非關鍵依賴無法解析，但不影響主功能。")
        await asyncio.sleep(0.8)

    add_log("SUCCESS", "所有依賴已成功安裝！")
    update_status(current_stage="launching", current_task_name="正在啟動服務...")

    # --- 模擬服務啟動 ---
    apps = {"main_dashboard": "pending", "quant": "pending", "transcriber": "pending"}
    update_status(apps_status=json.dumps(apps))

    for app_name in apps:
        apps[app_name] = "starting"
        update_status(apps_status=json.dumps(apps), current_task_name=f"啟動 {app_name}")
        add_log("INFO", f"App '{app_name}' 正在啟動...")
        await asyncio.sleep(1)
        apps[app_name] = "running"
        update_status(apps_status=json.dumps(apps))
        add_log("SUCCESS", f"App '{app_name}' 已成功運行！")

    # --- 模擬安全性掃描 ---
    add_log("INFO", "執行安全性掃描...")
    await asyncio.sleep(1)
    security_data = {
        "title": "🛡️ 安全性掃描數據流",
        "rows": [
            {"key": "防火牆規則", "value": "[✅ 通過] | 35 條規則已載入"},
            {"key": "對外開放埠號", "value": "[⚠️ 警告] | 發現非標準埠號 8080"},
            {"key": "依賴套件漏洞", "value": "[✅ 通過] | 未發現已知漏洞"},
        ]
    }
    add_log("INFO", "安全性掃描完成", type="data_block", payload=security_data)


    # --- 完成 ---
    final_url = "http://localhost:8005/"
    update_status(current_stage="completed", action_url=final_url, current_task_name="完成")
    add_log("SUCCESS", "所有服務已成功啟動！操作儀表板已就緒。", payload={"url": final_url})
    print("\n模擬程序執行完畢！")
    print(f"現在可以啟動 API 伺服器 (`python apps/dashboard_api/main.py`) 和主儀表板 (`python apps/main_dashboard/main.py`) 來查看結果了。")
    print("儀表板將會持續接收資源監控數據。")


async def monitor_resources():
    """持續監控並更新系統資源"""
    while True:
        cpu = round(random.uniform(20.0, 70.0), 2)
        ram = round(random.uniform(30.0, 60.0), 2)
        update_status(cpu_usage=cpu, ram_usage=ram)
        await asyncio.sleep(1)

async def main():
    setup_database()
    # 使用 gather 讓主邏輯和資源監控並行執行
    # 主邏輯執行完畢後，資源監控會繼續在背景執行
    main_task = asyncio.create_task(mock_main_logic())
    monitor_task = asyncio.create_task(monitor_resources())
    await main_task


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n偵測到手動中斷，程序結束。")
