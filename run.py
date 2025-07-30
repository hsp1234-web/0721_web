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
            ram_usage REAL,
            packages TEXT
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
        # 初始化狀態表，並為資源使用率設定預設值
        cursor.execute("INSERT OR IGNORE INTO status_table (id, current_stage, cpu_usage, ram_usage) VALUES (1, 'pending', 0.0, 0.0)")
        # 檢查 packages 欄位是否存在，如果不存在，就新增它
        cursor.execute("PRAGMA table_info(status_table)")
        columns = [column[1] for column in cursor.fetchall()]
        if "packages" not in columns:
            cursor.execute("ALTER TABLE status_table ADD COLUMN packages TEXT")
        conn.commit()

def get_installed_packages():
    """獲取已安裝的套件列表"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format=json'], capture_output=True, text=True)
        packages = json.loads(result.stdout)
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE status_table SET packages = ? WHERE id = 1", (json.dumps(packages),))
            conn.commit()
    except Exception as e:
        add_log("ERROR", f"獲取已安裝套件列表失敗: {e}")

def add_log(level, message):
    """將日誌寫入資料庫和檔案"""
    with open("logs/run.log", "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [{level}] - {message}\n")
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
        if app_name == "quant":
            env["FINMIND_API_TOKEN"] = "fake_token"
        with open(f"logs/{app_name}.log", "wb") as log_file:
            subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=app_path, env=env,
                stdout=log_file, stderr=subprocess.STDOUT
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
        "main_dashboard": "pending",
        "fake_interactive_page": "pending"
    }
    update_status(apps_status=apps_status)

    app_configs = [
        {"name": "main_dashboard", "port": 8005},
        {"name": "fake_interactive_page", "port": 8006}
    ]

    tasks = [launch_app(config['name'], config['port'], apps_status) for config in app_configs]
    await asyncio.gather(*tasks, return_exceptions=True)

    if all(status == "running" for status in apps_status.values()):
        final_url = "http://localhost:8005/" # 預設值
        try:
            from google.colab.output import eval_js
            import google.colab

            if hasattr(google.colab, 'kernel') and google.colab.kernel:
                add_log("INFO", "Colab 環境檢測成功，開始嘗試獲取代理 URL...")
                for i in range(10):  # 最多嘗試 10 次
                    try:
                        url = eval_js(f"google.colab.kernel.proxyPort(8005)")
                        if url and url.startswith('https://'):
                            final_url = url
                            add_log("INFO", f"成功獲取代理 URL (第 {i+1}/10 次嘗試): {final_url}")
                            break  # 成功後跳出迴圈
                        else:
                            add_log("WARNING", f"第 {i+1}/10 次獲取嘗試返回無效的 URL: '{url}'")
                    except Exception as e:
                        add_log("WARNING", f"第 {i+1}/10 次獲取 URL 時發生異常: {e}")

                    if i < 9: # 如果不是最後一次嘗試，則等待
                        add_log("INFO", "等待 5 秒後重試...")
                        await asyncio.sleep(5)

                if final_url == "http://localhost:8005/":
                    add_log("ERROR", "10 次嘗試後仍無法獲取 Colab 代理 URL，將使用預設本地 URL。")
            else:
                add_log("WARNING", "非 Colab kernel 環境，將使用預設本地 URL。")

        except (ImportError, AttributeError):
            add_log("WARNING", f"無法導入 google.colab 模組，將使用本地 URL。")

        update_status(stage="completed", action_url=final_url)
        add_log("INFO", f"所有服務已成功啟動！操作儀表板已就緒。")
    else:
        update_status(stage="failed")
        add_log("ERROR", "部分服務啟動失敗。")

# --- 主程序 ---
import psutil

async def monitor_resources():
    """持續監控並更新系統資源"""
    while True:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        update_status(cpu=cpu, ram=ram)
        await asyncio.sleep(1)

async def run_self_check():
    """執行自檢模式"""
    add_log("INFO", "啟動自檢模式...")
    update_status(stage="self_checking")

    process = await asyncio.create_subprocess_exec(
        sys.executable, "tests/smart_e2e_test.py",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    log_output = stdout.decode() + stderr.decode()
    add_log("INFO", f"自檢腳本輸出:\n{log_output}")

    if process.returncode == 0:
        add_log("INFO", "自檢成功完成。")
        update_status(stage="self_check_passed")
    else:
        add_log("ERROR", f"自檢失敗，返回碼: {process.returncode}")
        update_status(stage="self_check_failed")

async def main():
    """包含休眠邏輯的主異步函數"""
    setup_database()
    get_installed_packages()
    add_log("INFO", "Launch.py main process started.")

    if os.getenv("SELF_CHECK_MODE") == "true":
        await run_self_check()
        add_log("INFO", "Launch.py main process finished after self-check.")
        return

    update_status(stage="initializing")

    monitor_task = asyncio.create_task(monitor_resources())
    main_task = asyncio.create_task(main_logic())

    try:
        await main_task
        if not os.getenv("CI_MODE") and not os.getenv("FAST_TEST_MODE"):
            add_log("INFO", "主邏輯執行完畢，資源監控將持續在背景運行。")
            await monitor_task
        else:
            await asyncio.sleep(3)
            monitor_task.cancel()

    except Exception as e:
        add_log("CRITICAL", f"主程序發生未預期錯誤: {e}")
        update_status(stage="critical_failure")
    finally:
        if not monitor_task.done():
            monitor_task.cancel()
        add_log("INFO", "Launch.py main process finished.")

from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/status', methods=['GET'])
def get_status():
    """提供主狀態表的數據"""
    try:
        conn = sqlite3.connect(f"file:{DB_FILE}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        status = conn.execute('SELECT * FROM status_table WHERE id = 1').fetchone()
        conn.close()
        if status is None:
            return jsonify({"error": "No status data found"}), 404
        return jsonify(dict(status))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """提供一個簡單的健康檢查端點"""
    return jsonify({"status": "ok"})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """提供最新的 10 條日誌"""
    try:
        conn = sqlite3.connect(f"file:{DB_FILE}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        logs = conn.execute('SELECT * FROM log_table ORDER BY id DESC LIMIT 10').fetchall()
        conn.close()
        return jsonify([dict(log) for log in logs])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run_api_server():
    port = int(os.environ.get("API_PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def create_report():
    REPORTS_DIR = Path("reports")
    if not REPORTS_DIR.exists():
        REPORTS_DIR.mkdir()
    with open(REPORTS_DIR / "綜合摘要.md", "w") as f:
        f.write("綜合摘要")
    with open(REPORTS_DIR / "詳細日誌.md", "w") as f:
        f.write("詳細日誌")
    with open(REPORTS_DIR / "詳細效能.md", "w") as f:
        f.write("詳細效能")

if __name__ == "__main__":
    # 在一個獨立的執行緒中，執行 Flask API server
    import threading
    api_thread = threading.Thread(target=run_api_server)
    api_thread.daemon = True
    api_thread.start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        add_log("INFO", "偵測到手動中斷，程序結束。")
        create_report()
