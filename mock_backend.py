# -*- coding: utf-8 -*-
import sqlite3
import time
import random
import argparse
import json
from pathlib import Path
from datetime import datetime

class MockBackend:
    def __init__(self, db_file):
        self.db_file = Path(db_file)
        self.db_file.parent.mkdir(exist_ok=True, parents=True)
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()
        self._setup_database()
        self.apps = ["quant", "transcriber"]

    def _setup_database(self):
        self.cursor.execute("DROP TABLE IF EXISTS phoenix_logs")
        self.cursor.execute("DROP TABLE IF EXISTS status_table")
        self.cursor.execute("""
        CREATE TABLE phoenix_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            cpu_usage REAL,
            ram_usage REAL
        )""")
        self.cursor.execute("""
        CREATE TABLE status_table (
            id INTEGER PRIMARY KEY,
            current_stage TEXT,
            apps_status TEXT,
            action_url TEXT,
            cpu_usage REAL,
            ram_usage REAL
        )""")
        self.cursor.execute("INSERT OR IGNORE INTO status_table (id) VALUES (1)")
        self.conn.commit()

    def log(self, level, message, cpu=None, ram=None):
        ts = datetime.now().isoformat()
        self.cursor.execute(
            "INSERT INTO phoenix_logs (timestamp, level, message, cpu_usage, ram_usage) VALUES (?, ?, ?, ?, ?)",
            (ts, level, message, cpu, ram)
        )
        self.conn.commit()

    def update_status(self, stage=None, apps_status=None, url=None, cpu=None, ram=None):
        if stage: self.cursor.execute("UPDATE status_table SET current_stage = ? WHERE id = 1", (stage,))
        if apps_status: self.cursor.execute("UPDATE status_table SET apps_status = ? WHERE id = 1", (json.dumps(apps_status),))
        if url: self.cursor.execute("UPDATE status_table SET action_url = ? WHERE id = 1", (url,))
        if cpu: self.cursor.execute("UPDATE status_table SET cpu_usage = ? WHERE id = 1", (cpu,))
        if ram: self.cursor.execute("UPDATE status_table SET ram_usage = ? WHERE id = 1", (ram,))
        self.conn.commit()

    def run_simulation(self, duration_seconds=60):
        start_time = time.time()

        self.log("BATTLE", "模擬後端啟動。")
        self.update_status(stage="啟動中", apps_status={app: "pending" for app in self.apps})
        time.sleep(2)

        for app in self.apps:
            self.update_status(stage=f"安裝 {app}", apps_status={**{a: "running" for a in self.apps if a != app}, app: "installing"})
            self.log("INFO", f"開始為 {app} 安裝依賴...")
            for i in range(5):
                self.log("SHELL", f"  - 正在安裝套件 {i+1}/5...")
                time.sleep(random.uniform(0.5, 1.5))
            self.log("SUCCESS", f"{app} 的依賴已安裝。")
            self.update_status(apps_status={**{a: "running" for a in self.apps if a != app}, app: "running"})
            time.sleep(1)

        self.update_status(stage="服務運行中")
        self.log("SUCCESS", "所有模擬服務均已啟動。")

        while time.time() - start_time < duration_seconds:
            cpu = random.uniform(20, 60)
            ram = random.uniform(40, 80)
            self.update_status(cpu=cpu, ram=ram)
            self.log("PERF", "performance_snapshot", cpu=cpu, ram=ram)
            time.sleep(1)

        self.update_status(stage="任務完成", url="http://localhost:8000/dashboard")
        self.log("BATTLE", "模擬後端運行結束。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="模擬後端程式")
    parser.add_argument("--db-file", type=str, required=True, help="SQLite 資料庫檔案路徑")
    parser.add_argument("--duration", type=int, default=60, help="模擬運行的總秒數")
    args = parser.parse_args()

    mock = MockBackend(args.db_file)
    mock.run_simulation(args.duration)
