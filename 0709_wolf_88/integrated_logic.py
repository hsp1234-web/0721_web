# -*- coding: utf-8 -*-
"""
================================================================================
整合後的業務邏輯
================================================================================

本檔案整合了【普羅米修斯之火】金融數據框架與【鳳凰專案】錄音轉寫服務的核心業務邏輯。

--------------------------------------------------------------------------------
第一部分：【普羅米修斯之火】核心邏輯
--------------------------------------------------------------------------------
這部分包含了金融數據的獲取、處理、因子計算與模擬。
"""

# ... (從 0709_wolf_88/src/prometheus/ 下的相關檔案複製核心邏輯) ...

"""
--------------------------------------------------------------------------------
第二部分：【鳳凰專案】核心邏輯
--------------------------------------------------------------------------------
這部分包含了錄音轉寫服務的 API、工人進程和任務管理。
"""

# ... (從 0709_wolf_88/src/prometheus/transcriber/ 下的相關檔案複製核心邏輯) ...
import typer
from prometheus.entrypoints.ai_analyst_app import ai_analyst_job
from prometheus.entrypoints.query_gateway import run_dashboard_service
from prometheus.core.logging.log_manager import LogManager

app = typer.Typer()
# 由於 LogManager 不再是單例，我們為 CLI 的主進程創建一個常規的 logger
log_manager = LogManager(log_file="prometheus_cli.log")
logger = log_manager.get_logger("Conductor")

@app.command(name="analyze")
def cli_analyze():
    """
    啟動 AI 分析師報告生成器。
    """
    logger.info("正在啟動 AI 分析師...")
    ai_analyst_job()
    logger.info("AI 分析師工作完成。")


import subprocess
import sys
import os

@app.command(name="dashboard")
def cli_dashboard(
    host: str = typer.Option("127.0.0.1", help="綁定主機"),
    port: int = typer.Option(8000, help="綁定埠號"),
):
    """啟動網頁儀表板。"""
    logger.info(f"準備在 http://{host}:{port} 啟動儀表板...")
    run_dashboard_service(None, host, port)

data_app = typer.Typer()
app.add_typer(data_app, name="data")

@data_app.command("create-dummy")
def create_dummy():
    """
    建立一個用於測試的虛構 OHLCV CSV 檔案。
    """
    from pathlib import Path
    import numpy as np
    import pandas as pd

    DATA_DIR = Path("data")
    DATA_DIR.mkdir(exist_ok=True)
    file_path = DATA_DIR / "ohlcv_data.csv"

    date_range = pd.to_datetime(
        pd.date_range(start="2022-01-01", periods=1000, freq="D")
    )

    open_prices = np.random.uniform(90, 110, size=1000)

    data = {
        "Date": date_range,
        "Open": open_prices,
        "High": open_prices + np.random.uniform(0, 5, size=1000),
        "Low": open_prices - np.random.uniform(0, 5, size=1000),
        "Close": open_prices + np.random.uniform(-2, 2, size=1000),
        "Volume": np.random.randint(100000, 500000, size=1000),
    }

    df = pd.DataFrame(data)

    df.to_csv(file_path, index=False)
    logger.info(f"已成功建立虛構數據檔案於: {file_path}")


results_app = typer.Typer()
app.add_typer(results_app, name="results")

@results_app.command("clear")
def clear_results():
    """
    清除所有生成的結果、佇列、日誌和檢查點。
    """
    import os
    import shutil

    logger.info("開始清除所有執行數據...")

    RESULTS_DB_PATH = "output/results.sqlite"
    QUEUE_DIR = "data/queues"
    LOG_DIR = "data/logs"
    CHECKPOINT_DIR = "data/checkpoints"
    REPORTS_DIR = "data/reports"

    def remove_path(path_str, is_dir=False):
        if is_dir:
            if os.path.isdir(path_str):
                shutil.rmtree(path_str)
                logger.info(f"已刪除並清空目錄: {path_str}")
        else:
            if os.path.exists(path_str):
                os.remove(path_str)
                logger.info(f"已刪除檔案: {path_str}")

    try:
        remove_path(RESULTS_DB_PATH, is_dir=False)
        remove_path(QUEUE_DIR, is_dir=True)
        remove_path(LOG_DIR, is_dir=True)
        remove_path(CHECKPOINT_DIR, is_dir=True)
        remove_path(REPORTS_DIR, is_dir=True)

        # 重建空目錄
        os.makedirs(QUEUE_DIR, exist_ok=True)
        os.makedirs(LOG_DIR, exist_ok=True)
        os.makedirs(CHECKPOINT_DIR, exist_ok=True)
        os.makedirs(REPORTS_DIR, exist_ok=True)

        logger.info("清除程序完成。")
    except Exception as e:
        logger.error(f"清除過程中發生錯誤: {e}", exc_info=True)


@results_app.command("show")
def show_results():
    """
    從 SQLite 資料庫查詢並顯示回測結果。
    """
    import sqlite3
    import pandas as pd

    logger.info("正在從 SQLite 資料庫查詢結果...")
    DB_PATH = "output/results.sqlite"
    TABLE_NAME = "backtest_results"
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)
        conn.close()

        if df.empty:
            logger.warning("資料庫中尚無任何結果。")
        else:
            logger.info("查詢完成。")
            # 使用一個 logger 呼叫來顯示整個 DataFrame
            logger.info(f"\n--- 回測結果 ---\n{df.to_string()}\n----------------")

    except Exception as e:
        logger.error(f"查詢結果時發生錯誤: {e}", exc_info=True)


@results_app.command("generate-report")
def generate_report(
    xml_path: str = typer.Option("output/reports/report.xml", help="JUnit XML 報告的路徑"),
    md_path: str = typer.Option("TEST_REPORT.md", help="要生成的 Markdown 報告的路徑"),
):
    """
    從 JUnit XML 檔案產生 Markdown 報告。
    """
    import xml.etree.ElementTree as ET
    from datetime import datetime

    logger.info(f"AI 報告生成器啟動，正在讀取原始數據: {xml_path}")
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        suite = root.find("testsuite")

        # 提取核心數據
        total = int(suite.get("tests", 0))
        failures = int(suite.get("failures", 0))
        errors = int(suite.get("errors", 0))
        skipped = int(suite.get("skipped", 0))
        exec_time = float(suite.get("time", 0))
        passed = total - failures - errors - skipped

        # 開始構建 Markdown 報告
        report_content = []
        report_content.append("# **【普羅米修斯之火】系統測試作戰報告**")
        report_content.append(
            f"> 報告生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

        # 總結區塊
        report_content.append("## **一、 戰況總覽**")
        if failures == 0 and errors == 0:
            report_content.append(
                "> **結論：<font color='green'>任務成功 (SUCCESS)</font>** - 所有品質閘門均已通過。系統戰備狀態良好。"
            )
        else:
            report_content.append(
                "> **結論：<font color='red'>任務失敗 (FAILURE)</font>** - 發現關鍵性錯誤。系統存在風險，需立即審查。"
            )

        summary_table = [
            "| 指標 (Metric) | 數量 (Count) |",
            "|:---|:---:|",
            f"| ✅ **測試通過 (Passed)** | {passed} |",
            f"| ❌ **測試失敗 (Failed)** | {failures} |",
            f"| 🔥 **執行錯誤 (Errors)** | {errors} |",
            f"| 🚧 **測試跳過 (Skipped)** | {skipped} |",
            f"| ⏱️ **總執行時間 (Time)** | {exec_time:.2f} 秒 |",
            f"| 🧮 **總執行數量 (Total)** | {total} |",
        ]
        report_content.append("\n".join(summary_table))

        # 失敗與錯誤詳情
        if failures > 0 or errors > 0:
            report_content.append("\n## **二、 失敗與錯誤詳情**")
            count = 1
            for testcase in suite.findall("testcase"):
                failure = testcase.find("failure")
                error = testcase.find("error")

                detail = failure if failure is not None else error

                if detail is not None:
                    test_name = testcase.get("name", "未知測試")
                    class_name = testcase.get("classname", "未知類別")
                    error_type = detail.tag.capitalize()  # "failure" -> "Failure"
                    message = detail.get("message", "無訊息").splitlines()[0]

                    report_content.append(f"\n### {count}. {error_type}: {message}")
                    report_content.append(
                        f"- **測試位置:** `{class_name}.{test_name}`"
                    )
                    report_content.append("- **詳細堆疊追蹤:**")
                    # 檢查 detail.text 是否為 None
                    stack_trace = (
                        detail.text.strip() if detail.text else "無堆疊追蹤資訊。"
                    )
                    report_content.append(f"```\n{stack_trace}\n```")
                    count += 1

        # 寫入檔案
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_content))

        logger.info(f"作戰報告已成功生成至: {md_path}")

    except FileNotFoundError:
        logger.error(f"找不到原始數據檔案: {xml_path}")
    except ET.ParseError:
        logger.error(f"原始數據檔案格式錯誤: {xml_path}")
    except Exception as e:
        logger.error(f"生成報告時發生未知錯誤: {e}")


@results_app.command("add-tasks")
def add_tasks(
    num_tasks: int = typer.Option(10, help="要添加的任務數量"),
):
    """
    向任務佇列中添加指定數量的隨機回測任務。
    """
    import random
    import uuid
    from prometheus.core.context import AppContext

    with AppContext() as ctx:
        logger.info(f"正在生成 {num_tasks} 個回測任務...")
        batch_id = str(uuid.uuid4())
        for i in range(num_tasks):
            # 任務現在是一個字典
            task = {
                "task_id": str(uuid.uuid4()),
                "type": "backtest",
                "strategy": "SMA_Crossover",
                "symbol": random.choice(["BTC/USDT", "ETH/USDT", "XRP/USDT"]),
                "params": {"fast": random.randint(5, 15), "slow": random.randint(20, 40)},
                "batch_id": batch_id,
            }
            ctx.queue.put(task)
            logger.debug(f"已將任務 {i+1}/{num_tasks} ({task['strategy']}) 添加到佇列。")
        logger.info(f"成功將 {num_tasks} 個任務添加到佇列。")


pipelines_app = typer.Typer()
app.add_typer(pipelines_app, name="pipelines")

@pipelines_app.command("run-downloader")
def run_downloader(
    start_date: str = typer.Option(..., help="下載開始日期 (YYYY-MM-DD)"),
    end_date: str = typer.Option(..., help="下載結束日期 (YYYY-MM-DD)"),
    output_dir: str = typer.Option("data/downloads", help="檔案儲存目錄"),
    max_workers: int = typer.Option(16, help="最大同時下載任務數"),
):
    """
    TAIFEX 自動化數據採集器 v1.0
    """
    import os
    import random
    import time
    from collections import Counter
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from datetime import datetime, timedelta
    import requests
    from prometheus.core.config import config

    logger.info("--- 啟動數據採集任務 ---")
    logger.info(f"時間範圍: {start_date} 到 {end_date}")
    logger.info(f"輸出目錄: {output_dir}")

    tasks = []
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    date_range = [
        start_dt + timedelta(days=x) for x in range((end_dt - start_dt).days + 1)
    ]

    base_url = config.get("data_acquisition.taifex.base_url")
    for current_date in date_range:
        date_str = current_date.strftime("%Y_%m_%d")
        # 範例：僅下載期貨逐筆資料
        tasks.append(
            {
                "url": f"{base_url}/file/taifex/Dailydownload/DailydownloadCSV/Daily_{date_str}.zip",
                "file_name": f"Daily_{date_str}.zip",
                "min_delay": 0.2,
                "max_delay": 1.0,
            }
        )

    results_counter = Counter()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        with requests.Session() as session:
            future_to_task = {
                executor.submit(execute_download, session, task, output_dir): task
                for task in tasks
            }
            for future in as_completed(future_to_task):
                try:
                    status, message = future.result()
                    results_counter[status] += 1
                    logger.info(f"[{status.upper()}] {message}")
                except Exception as exc:
                    logger.info(f"[CRITICAL] 任務執行異常: {exc}")

    logger.info("\n--- 採集任務總結 ---")
    for status, count in results_counter.items():
        logger.info(f"  {status}: {count} 個")


def execute_download(session, task_info, output_dir):
    """執行單一檔案下載任務，包含重試與錯誤處理。"""
    import os
    import random
    import time
    import requests
    from prometheus.core.config import config

    file_path = os.path.join(output_dir, task_info["file_name"])
    if os.path.exists(file_path):
        return "exists", f"檔案已存在: {task_info['file_name']}"

    time.sleep(random.uniform(task_info["min_delay"], task_info["max_delay"]))

    user_agents = config.get("data_acquisition.taifex.user_agents")
    base_url = config.get("data_acquisition.taifex.base_url")

    for attempt in range(3):  # 重試3次
        try:
            headers = {
                "User-Agent": random.choice(user_agents),
                "Referer": task_info.get("referer", base_url),
            }
            response = (
                session.post(
                    task_info["url"],
                    data=task_info.get("payload", {}),
                    headers=headers,
                    timeout=120,
                )
                if task_info.get("payload")
                else session.get(task_info["url"], headers=headers, timeout=120)
            )

            if (
                response.status_code == 200
                and len(response.content) > 100
                and "查無資料" not in response.text
            ):
                os.makedirs(output_dir, exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(response.content)
                return "success", f"成功下載: {task_info['file_name']}"
            elif response.status_code == 404:
                return "not_found", f"404 Not Found: {task_info['file_name']}"
            else:
                return (
                    "error",
                    f"伺服器錯誤 {response.status_code}: {task_info['file_name']}",
                )

        except requests.exceptions.RequestException as e:
            if attempt == 2:
                return "error", f"網路請求失敗: {e}"
            time.sleep(5 * (attempt + 1))

    return "error", f"達到最大重試次數: {task_info['file_name']}"


@pipelines_app.command("run-explorer")
def run_explorer(
    input_dir: str = typer.Option("data/downloads", help="掃描的原始檔案目錄"),
    db_path: str = typer.Option("data/metadata/schema_registry.db", help="格式註冊表資料庫路徑"),
):
    """
    TAIFEX 格式探勘與註冊器 v1.0
    """
    import hashlib
    import os
    from prometheus.core.db.schema_registry import SchemaRegistry
    from prometheus.core.utils.helpers import (
        prospect_file_content,
        read_file_content,
    )

    registry = SchemaRegistry(db_path)
    logger.info(f"開始掃描目錄: {input_dir}")
    new_formats = 0
    updated_formats = 0

    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)
        if not os.path.isfile(file_path):
            continue

        try:
            file_bytes_content = read_file_content(file_path)
            if file_bytes_content is None:
                continue

            result = prospect_file_content(file_bytes_content)

            if result["status"] == "success":
                fingerprint = get_header_fingerprint(result["header"])
                status = registry.add_or_update_schema(fingerprint, result["header"], result["encoding"], filename)
                if status == "new":
                    new_formats += 1
                else:
                    updated_formats += 1

        except Exception as e:
            logger.error(f"處理檔案 {filename} 失敗: {e}", exc_info=True)

    registry.close()
    logger.info("--- 格式探勘總結 ---")
    logger.info(f"發現新格式: {new_formats} 種")
    logger.info(f"更新現有格式計數: {updated_formats} 次")


def get_header_fingerprint(header_line: str) -> str:
    """對標準化後的標頭計算指紋。"""
    import hashlib
    normalized_header = "".join(header_line.lower().split()).replace('"', "")
    return hashlib.sha256(normalized_header.encode("utf-8")).hexdigest()


@pipelines_app.command("run-elt")
def run_elt(
    input_dir: str = typer.Option("data/downloads", help="下載檔案的來源目錄 (供 Loader 使用)"),
    raw_db_path: str = typer.Option("data/raw_warehouse/raw_taifex.duckdb", help="原始數據艙資料庫路徑"),
    schema_db_path: str = typer.Option("data/metadata/schema_registry.db", help="格式註冊表資料庫路徑"),
    analytics_db_path: str = typer.Option("data/analytics_warehouse/analytics_taifex.duckdb", help="分析數據庫路徑"),
):
    """
    TAIFEX ELT 加工管線 v1.0
    """
    import os
    from prometheus.core.db.data_warehouse import AnalyticsDataWarehouse, RawDataWarehouse
    from prometheus.core.db.schema_registry import SchemaRegistry

    # Ensure parent directories for database files exist
    os.makedirs(os.path.dirname(raw_db_path), exist_ok=True)
    os.makedirs(os.path.dirname(schema_db_path), exist_ok=True)
    os.makedirs(os.path.dirname(analytics_db_path), exist_ok=True)

    run_loader(input_dir, raw_db_path, schema_db_path)
    run_transformer(raw_db_path, schema_db_path, analytics_db_path)


def run_loader(input_dir, raw_db_path, schema_db_path):
    import os
    from prometheus.core.db.data_warehouse import RawDataWarehouse
    from prometheus.core.db.schema_registry import SchemaRegistry
    from prometheus.core.utils.helpers import (
        prospect_file_content,
        read_file_content,
    )

    logger.info("--- [階段 2] 執行 Loader ---")
    raw_wh = RawDataWarehouse(raw_db_path)
    schema_registry = SchemaRegistry(schema_db_path)

    known_fingerprints = schema_registry.get_known_fingerprints()
    if not known_fingerprints:
        logger.info("Loader: No known fingerprints loaded from schema registry. Only files matching these will be processed.")

    files_loaded = 0
    if not os.path.exists(input_dir):
        logger.warning(f"Loader input directory {input_dir} does not exist. Skipping loading.")
        raw_wh.close()
        schema_registry.close()
        return

    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)

        if not os.path.isfile(file_path):
            continue

        if raw_wh.is_file_processed(file_path):
            logger.debug(f"Loader: File {filename} already in raw_import_log. Skipping.")
            continue

        try:
            file_bytes_content = read_file_content(file_path)
            if file_bytes_content is None:
                continue

            result = prospect_file_content(file_bytes_content)
            if result["status"] == "success":
                fingerprint = get_header_fingerprint(result["header"])
                if fingerprint in known_fingerprints:
                    raw_wh.log_processed_file(file_path, file_bytes_content, fingerprint)
                    files_loaded += 1
                    logger.info(f"Loader: Loaded {filename} (fingerprint: {fingerprint[:8]}...) as it's a known schema.")
                else:
                    logger.info(f"Loader: Skipped {filename} (fingerprint: {fingerprint[:8]}...) as its schema is not in the registry.")
            else:
                logger.warning(f"Loader: Skipped file {filename} due to content prospecting failure: {result.get('error', 'Unknown error')}")

        except Exception as e:
            logger.error(f"Loader 處理 {filename} 失敗: {e}", exc_info=True)

    raw_wh.close()
    schema_registry.close()
    logger.info(f"Loader 完成，新載入 {files_loaded} 個檔案。")


def run_transformer(raw_db_path, schema_db_path, analytics_db_path):
    import io
    import pandas as pd
    from prometheus.core.db.data_warehouse import AnalyticsDataWarehouse, RawDataWarehouse
    from prometheus.core.db.schema_registry import SchemaRegistry

    logger.info("--- [階段 3] 執行 Transformer ---")
    schema_registry = SchemaRegistry(schema_db_path)
    raw_wh = RawDataWarehouse(raw_db_path)
    analytics_wh = AnalyticsDataWarehouse(analytics_db_path)

    schema_map = schema_registry.get_all_schemas()
    if not schema_map:
        logger.warning("Transformer: 格式註冊表為空或讀取失敗，Transformer 無法執行有效轉換。")
        schema_registry.close()
        raw_wh.close()
        analytics_wh.close()
        return

    daily_futures_header_str = "交易日期,契約代碼,到期月份(週別),開盤價,最高價,最低價,收盤價,成交量"
    target_daily_futures_fingerprint = get_header_fingerprint(daily_futures_header_str)

    if target_daily_futures_fingerprint not in schema_map:
        logger.warning(f"Transformer: Did not find fingerprint for daily_futures_header '{daily_futures_header_str}' in schema_map. Cannot process daily_futures.")
    else:
        logger.info(f"Transformer: Target fingerprint for daily_futures is {target_daily_futures_fingerprint[:8]}...")

    analytics_wh.create_daily_futures_table()

    records = raw_wh.execute_query("SELECT content_blob, format_fingerprint FROM raw_import_log").fetchall()
    transformed_count = 0
    for blob, fingerprint in records:
        if fingerprint != target_daily_futures_fingerprint:
            continue

        if fingerprint not in schema_map:
            continue

        header_str_from_registry, encoding = schema_map[fingerprint]
        try:
            df = pd.read_csv(io.BytesIO(blob), encoding=encoding, thousands=",", header=0, on_bad_lines="skip")
            df.columns = [str(col).strip().replace('"', "") for col in df.columns]

            target_columns_canonical = [
                "交易日期", "契約代碼", "到期月份(週別)", "開盤價",
                "最高價", "最低價", "收盤價", "成交量",
            ]

            df_to_load = pd.DataFrame()
            for canonical_col_name in target_columns_canonical:
                if canonical_col_name in df.columns:
                    df_to_load[canonical_col_name] = df[canonical_col_name]
                else:
                    df_to_load[canonical_col_name] = None

            if not df_to_load.empty:
                analytics_wh.insert_daily_futures(df_to_load)
                transformed_count += 1

        except pd.errors.EmptyDataError:
            logger.warning(f"Transformer: No data or columns found in CSV for fingerprint {fingerprint[:8]}...")
        except Exception as e:
            logger.error(f"Transformer 處理指紋 {fingerprint[:8]}... 的資料時失敗: {e}", exc_info=True)

    raw_wh.close()
    analytics_wh.close()
    schema_registry.close()
    logger.info(f"Transformer 完成，成功轉換 {transformed_count} 筆記錄。")


@pipelines_app.command("run-stock-factors")
def run_stock_factors():
    """
    執行第四號生產線：股票因子生成。
    """
    from prometheus.pipelines.p4_stock_factor_generation import main as p4_main
    logger.info("--- 啟動 P4：股票因子生成管線 ---")
    p4_main()
    logger.info("--- P4：股票因子生成管線執行完畢 ---")


@pipelines_app.command("run-crypto-factors")
def run_crypto_factors():
    """
    執行第五號生產線：加密貨幣因子生成。
    """
    from prometheus.pipelines.p5_crypto_factor_generation import main as p5_main
    logger.info("--- 啟動 P5：加密貨幣因子生成管線 ---")
    p5_main()
    logger.info("--- P5：加密貨幣因子生成管線執行完畢 ---")


@app.command(name="build-feature-store")
def build_feature_store():
    """
    【作戰指令】統一數據倉儲重構：建造特徵倉儲。
    """
    import asyncio
    from prometheus.core.db.db_manager import DBManager
    # from prometheus.pipelines.p1_factor_generation import p1_factor_generation_pipeline
    # from prometheus.pipelines.p2_index_factor_generation import p2_index_factor_pipeline
    # from prometheus.pipelines.p3_bond_factor_generation import p3_bond_factor_pipeline
    from prometheus.pipelines.p4_stock_factor_generation import main as p4_main
    from prometheus.pipelines.p5_crypto_factor_generation import main as p5_main

    logger.info("--- 啟動統一數據倉儲建構流程 ---")
    db_manager = DBManager()

    # --- P1, P2, P3 (已停用) ---
    # 根據目前的檔案結構，這些管線不存在，暫時註解以確保命令可執行
    # logger.info("執行 P1 通用因子生成...")
    # p1_df = asyncio.run(p1_factor_generation_pipeline.run())
    # db_manager.save_data(p1_df, 'factors')
    # logger.info("P1 通用因子數據已合併。")

    # logger.info("執行 P2 指數因子生成...")
    # p2_df = asyncio.run(p2_index_factor_pipeline.run())
    # db_manager.save_data(p2_df, 'factors')
    # logger.info("P2 指數因子數據已合併。")

    # logger.info("執行 P3 債券因子生成...")
    # p3_df = asyncio.run(p3_bond_factor_pipeline.run())
    # db_manager.save_data(p3_df, 'factors')
    # logger.info("P3 債券因子數據已合併。")

    # --- P4, P5 ---
    # 這些管線的 main 函數內部直接調用 DBManager，我們暫時保持這種方式
    # 未來可以進一步重構，但目前足以滿足作戰目標
    logger.info("執行 P4 股票因子生成...")
    p4_main()
    logger.info("P4 股票因子數據已合併。")

    logger.info("執行 P5 加密貨幣因子生成...")
    p5_main()
    logger.info("P5 加密貨幣因子數據已合併。")

    logger.info("--- 統一數據倉儲建構流程完畢 ---")


@pipelines_app.command("run-simulation-training")
def run_simulation_training(
    target_factor: str = typer.Option(..., help="要模擬的目標因子名稱"),
):
    """
    執行第六號生產線：因子代理模擬模型訓練。
    """
    from prometheus.pipelines.p6_simulation_training import run_main as p6_run_main
    logger.info(f"--- 啟動 P6：因子代理模擬模型訓練管線，目標為 {target_factor} ---")
    p6_run_main(target_factor=target_factor)
    logger.info(f"--- P6：因子代理模擬模型訓練管線執行完畢 ---")


@pipelines_app.command("run")
def run_pipeline(
    name: str = typer.Option(..., help="要執行的管線名稱"),
    ticker: str = typer.Option(None, "--ticker", "-t", help="要處理的資產代號")
):
    """
    執行指定的數據管線。
    """
    import asyncio
    pipeline_context = {"ticker": ticker} if ticker else {}
    logger.info(f"--- 啟動 {name} 管線，上下文: {pipeline_context} ---")

    if name == "p1_factor_generation":
        from prometheus.pipelines.p1_factor_generation import p1_factor_generation_pipeline
        asyncio.run(p1_factor_generation_pipeline.run(context=pipeline_context))
    elif name == "p2_index_factor_generation":
        from prometheus.pipelines.p2_index_factor_generation import p2_index_factor_pipeline
        asyncio.run(p2_index_factor_pipeline.run(context=pipeline_context))
    elif name == "p3_bond_factor_generation":
        from prometheus.pipelines.p3_bond_factor_generation import p3_bond_factor_pipeline
        asyncio.run(p3_bond_factor_pipeline.run(context=pipeline_context))
    else:
        logger.error(f"錯誤：找不到名為 '{name}' 的管線。")
        raise typer.Exit(code=1)

    logger.info(f"--- {name} 管線執行完畢 ---")


@pipelines_app.command("run-backfill")
def run_backfill_cli(
    start_date: str = typer.Option(..., help="回填開始日期 (YYYY-MM-DD)"),
    end_date: str = typer.Option(..., help="回填結束日期 (YYYY-MM-DD)"),
):
    """
    執行歷史數據回填管線。
    """
    import pandas as pd
    from prometheus.core.analysis.data_engine import DataEngine
    from prometheus.core.clients.client_factory import ClientFactory

    logger.info(f"--- 開始執行數據回填作業：從 {start_date} 到 {end_date} ---")

    data_engine = DataEngine()
    hourly_timestamps = pd.date_range(start=start_date, end=end_date, freq="H")
    total_tasks = len(hourly_timestamps)

    for i, ts in enumerate(hourly_timestamps):
        logger.debug(f"--- 正在處理 ({i + 1}/{total_tasks}): {ts} ---")
        try:
            data_engine.generate_snapshot(ts)
        except Exception as e:
            logger.error(f"❌ 處理 {ts} 時發生錯誤: {e}", exc_info=True)

    data_engine.close()
    ClientFactory.close_all()
    logger.info("--- 數據回填作業完成 ---")


from prometheus.models.strategy_models import Strategy
from prometheus.services.backtesting_service import BacktestingService
from prometheus.services.evolution_chamber import EvolutionChamber
from prometheus.services.strategy_reporter import StrategyReporter
from prometheus.core.db.db_manager import DBManager

@app.command()
def run_evolution_cycle():
    """
    🚀 [端到端] 執行一次完整的演化週期：演化 -> 回測 -> 報告。
    """
    print("--- 啟動【演化室行動】完整作戰週期 ---")

    # 1. 初始化核心服務
    db_manager = DBManager()
    backtester = BacktestingService(db_manager)

    # 2. 準備演化所需數據
    # 假設因子數據已存在
    all_factors_df = db_manager.fetch_table('factors')
    # 排除非因子欄位
    available_factors = [col for col in all_factors_df.columns if col not in ['date', 'symbol', 'close']]

    if not available_factors:
        print("錯誤：數據庫中找不到可用的因子。請先執行 build-feature-store。")
        return

    target_asset_for_evolution = 'AAPL' # 選擇一個數據庫中存在的資產
    print(f"INFO: 將使用 '{target_asset_for_evolution}' 作為本次演化的目標資產。")
    chamber = EvolutionChamber(backtester, available_factors, target_asset=target_asset_for_evolution)

    # 3. 執行演化
    # 為了快速演示，使用較小的參數
    hof = chamber.run_evolution(n_pop=20, n_gen=5)

    if not hof:
        print("錯誤：演化未能產生有效結果。")
        return

    # 4. 對最優策略進行最終回測以獲得完整報告
    best_individual = hof[0]
    best_factors = [available_factors[i] for i in best_individual]
    final_strategy = Strategy(
        factors=best_factors,
        weights={factor: 1.0 / len(best_factors) for factor in best_factors},
        target_asset='AAPL' # 修正：明確指定一個存在的資產
    )
    final_report = backtester.run(final_strategy)

    # 5. 生成報告
    reporter = StrategyReporter()
    reporter.generate_report(hof, final_report, available_factors)

    print("--- 【演化室行動】作戰週期結束 ---")

# --- Transcriber CLI ---
transcriber_cli = typer.Typer()
app.add_typer(transcriber_cli, name="transcriber")

@transcriber_cli.command(name="run-server")
def run_transcriber_server(
    host: str = typer.Option("127.0.0.1", help="綁定主機"),
    port: int = typer.Option(8001, help="綁定埠號"),
    num_workers: int = typer.Option(1, help="要啟動的轉寫工人數量"),
):
    """
    啟動轉寫服務 API 伺服器。
    """
    import multiprocessing as mp
    import sys
    import time
    from prometheus.transcriber.main import app as transcriber_app
    from prometheus.transcriber.transcriber_worker import transcriber_worker_process
    from prometheus.transcriber.mock_worker import mock_worker_process
    import uvicorn

    logger.info("--- 啟動【鳳凰專案】轉寫服務 ---")

    # 根據平台設定多進程啟動方法
    if sys.platform == "darwin":
        mp.set_start_method("spawn", force=True)
    else:
        mp.set_start_method("spawn")

    # We need to get the queue from the app state, but the app is not running yet.
    # For now, we will create a new queue and pass it to both the app and the workers.
    # This is not ideal, but it's a temporary solution.

    task_queue = mp.Queue()
    transcriber_app.state.task_queue = task_queue # Inject the queue into the app state

    processes = []

    # 1. 啟動 API 伺服器
    api_process = mp.Process(
        target=uvicorn.run,
        kwargs={"app": transcriber_app, "host": host, "port": port, "log_level": "info"},
        name="TranscriberAPIServer"
    )
    processes.append(api_process)

    # 2. 選擇並啟動工人
    # 這裡我們暫時硬編碼使用模擬工人，以便測試
    worker_target = mock_worker_process
    worker_name = "MockWorkerProcess"
    logger.info(f"將啟動 {num_workers} 個模擬轉寫工人。")

    for i in range(num_workers):
        worker_process_instance = mp.Process(
            target=worker_target,
            # 簡化參數，暫時不傳入 config 和 result_queue
            args=(None, task_queue, None, None),
            name=f"{worker_name}-{i+1}"
        )
        processes.append(worker_process_instance)

    try:
        for p in processes:
            p.start()
            logger.info(f"已啟動行程: {p.name} (PID: {p.pid})")

        # 主行程等待所有子行程結束
        for p in processes:
            p.join()

    except KeyboardInterrupt:
        logger.info("收到中斷信號，正在關閉所有轉寫服務行程...")
    finally:
        for p in processes:
            if p.is_alive():
                p.terminate()
                p.join(timeout=5)
        logger.info("所有轉寫服務已關閉。")


if __name__ == "__main__":
    app()
\n\n# ==================== Transcriber Logic ====================\n\n
"""轉寫服務 API 主應用程式"""
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator
import logging

import aiofiles
import aiosqlite
from fastapi import FastAPI, File, HTTPException, UploadFile, Request
from fastapi.staticfiles import StaticFiles

from prometheus.core.logging.log_manager import LogManager
from prometheus.transcriber.core import DATABASE_FILE, UPLOAD_DIR, initialize_database

# --- 靜態檔案目錄設定 ---
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)

# --- 日誌記錄器設定 ---
log_manager = LogManager(log_file="transcriber_api.log")
logger = log_manager.get_logger(__name__)


# --- 應用程式生命週期管理 ---
import multiprocessing as mp

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """處理應用程式啟動與關閉事件"""
    logger.info("轉寫服務 API 啟動中...")
    await initialize_database()
    # 如果沒有從 CLI 注入佇列，則建立一個新的
    if not hasattr(app.state, 'task_queue'):
        logger.warning("未在 app.state 中找到任務佇列，正在建立新的佇列。")
        app.state.task_queue = mp.Queue()
    yield
    logger.info("轉寫服務 API 已關閉。")
    # 佇列的生命週期由 CLI 管理，此處不關閉


# --- FastAPI 應用程式實例 ---
app = FastAPI(lifespan=lifespan)


# --- API 端點 ---
@app.get("/health", status_code=200, summary="健康檢查")
async def health_check() -> dict[str, str]:
    """提供一個簡單的健康檢查端點，確認服務是否正常運行。"""
    return {"status": "ok"}


@app.post("/upload", status_code=202, summary="上傳音檔並建立轉寫任務")
async def upload_file(
    request: Request,
    file: UploadFile = File(..., description="要上傳的音訊檔案"),
) -> dict[str, str]:
    """
    接收客戶端上傳的音訊檔案，將其儲存至伺服器，並為其建立一個新的轉寫任務。

    - **儲存檔案**: 檔案會以 UUID 重新命名，以避免檔名衝突。
    - **建立任務**: 在資料庫中新增一筆任務記錄。
    - **加入佇列**: 將任務 ID 加入背景處理佇列，交由工人進程處理。
    """
    task_id = str(uuid.uuid4())
    # 確保上傳目錄存在
    UPLOAD_DIR.mkdir(exist_ok=True)
    filepath = UPLOAD_DIR / f"{task_id}_{file.filename}"

    try:
        # 以 1MB 的區塊讀寫檔案，避免一次性載入過大檔案佔用記憶體
        async with aiofiles.open(filepath, "wb") as out_file:
            while content := await file.read(1024 * 1024):
                await out_file.write(content)
        logger.info("檔案 '%s' 已成功上傳至 '%s'", file.filename, filepath)

        # 在資料庫中記錄此任務
        async with aiosqlite.connect(DATABASE_FILE) as db:
            await db.execute(
                "INSERT INTO transcription_tasks (id, original_filepath) VALUES (?, ?)",
                (task_id, str(filepath)),
            )
            await db.commit()

        # 將任務 ID 推入佇列
        task_queue = request.app.state.task_queue
        task_queue.put(task_id)
        logger.info("任務 %s 已成功加入轉寫佇列。", task_id)

    except IOError as e:
        logger.exception("檔案操作時發生錯誤: %s", e)
        raise HTTPException(status_code=500, detail="檔案儲存失敗，請檢查伺服器權限或磁碟空間。") from e
    except aiosqlite.Error as e:
        logger.exception("資料庫操作時發生錯誤: %s", e)
        raise HTTPException(status_code=500, detail="無法建立轉寫任務，請檢查資料庫狀態。") from e

    return {"task_id": task_id}


@app.get("/status/{task_id}", summary="查詢轉寫任務狀態")
async def get_task_status(
    task_id: str,
) -> dict[str, Any]:
    """根據任務 ID，查詢並返回該任務的當前狀態、進度及轉寫結果。"""
    try:
        async with aiosqlite.connect(DATABASE_FILE) as db:
            db.row_factory = aiosqlite.Row  # 讓查詢結果可以像字典一樣取值
            async with db.execute(
                "SELECT * FROM transcription_tasks WHERE id = ?", (task_id,)
            ) as cursor:
                task = await cursor.fetchone()

        if task is None:
            raise HTTPException(status_code=404, detail=f"找不到任務 ID: {task_id}")

        return dict(task)

    except aiosqlite.Error as e:
        logger.exception("查詢任務 %s 狀態時發生資料庫錯誤: %s", task_id, e)
        raise HTTPException(status_code=500, detail="查詢任務狀態時發生錯誤。") from e


# --- 掛載靜態檔案 ---
# 將 static 目錄下的檔案作為根路徑 (/) 的靜態資源，並提供 index.html 作為預設頁面
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

# --- 直接執行時的備用啟動方式 ---
if __name__ == "__main__":
    import uvicorn
    logger.info("使用 uvicorn 直接啟動 API 伺服器 (僅供開發測試)...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
"""真實轉寫工人模組"""
import asyncio
import multiprocessing as mp
import time
from typing import Any, Optional

from faster_whisper import WhisperModel
import aiosqlite

from prometheus.core.logging.log_manager import LogManager
from prometheus.transcriber.core import DATABASE_FILE
from prometheus.transcriber.core.hardware import get_best_hardware_config

# --- 日誌記錄器設定 ---
log_manager = LogManager(log_file="transcriber_worker.log")
logger = log_manager.get_logger(__name__)


async def process_single_task(task_id: str) -> None:
    """
    處理一個指定的轉寫任務。

    Args:
        task_id (str): 要處理的任務 ID。
    """
    logger.info("開始處理任務: %s", task_id)
    audio_path = None

    try:
        # 1. 更新任務狀態為 'processing'
        await update_task_status_in_db(task_id, "processing")

        # 2. 從資料庫獲取音檔路徑
        async with aiosqlite.connect(DATABASE_FILE) as db:
            async with db.execute(
                "SELECT original_filepath FROM transcription_tasks WHERE id = ?",
                (task_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    logger.error("在資料庫中找不到任務 %s 的檔案路徑。", task_id)
                    await update_task_status_in_db(task_id, "failed", error_message="找不到檔案路徑")
                    return
                audio_path = row[0]

        # 3. 執行轉寫
        hardware_config = get_best_hardware_config()
        logger.info("使用硬體設定: %s", hardware_config)
        model = WhisperModel(
            "tiny",  # 暫時使用 tiny 模型以利測試
            device=hardware_config["device"],
            compute_type=hardware_config["compute_type"],
        )
        segments, _info = model.transcribe(audio_path, beam_size=5)
        full_transcript = "".join(segment.text for segment in segments)
        logger.info("任務 %s: 轉寫完成。", task_id)

        # 4. 更新最終結果
        await update_task_status_in_db(
            task_id, "completed", result_text=full_transcript.strip()
        )
        logger.info("任務 %s 狀態更新為: completed", task_id)

    except Exception as e:
        logger.exception("處理任務 %s 過程中發生錯誤", task_id)
        await update_task_status_in_db(task_id, "failed", error_message=str(e))
        logger.info("任務 %s 狀態更新為: failed", task_id)


async def update_task_status_in_db(
    task_id: str,
    status: str,
    result_text: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    """在資料庫中更新任務的狀態、結果或錯誤訊息。"""
    try:
        async with aiosqlite.connect(DATABASE_FILE) as db:
            await db.execute(
                """
                UPDATE transcription_tasks
                SET status = ?, result_text = ?, error_message = ?
                WHERE id = ?
                """,
                (status, result_text, error_message, task_id),
            )
            await db.commit()
    except aiosqlite.Error as e:
        logger.exception("更新任務 %s 狀態時發生資料庫錯誤", task_id)


def transcriber_worker_process(
    log_queue: Optional[mp.Queue],
    task_queue: mp.Queue,
    result_queue: Optional[mp.Queue],
    config: Optional[dict[str, Any]],
) -> None:
    """
    轉寫工人行程的主函數。

    它會持續從任務佇列中獲取任務 ID，並呼叫 `process_single_task` 進行處理。
    """
    # 此處的 log_queue, result_queue, config 暫未使用，但保留簽名以符合架構
    logger.info("真實轉寫工人行程已啟動 (PID: %s)", mp.current_process().pid)

    async def main_loop() -> None:
        while True:
            try:
                # 從佇列中獲取任務，如果佇列為空，會阻塞等待
                task_id = task_queue.get()
                if task_id is None:
                    logger.info("收到結束信號，工人行程即將關閉。")
                    break
                await process_single_task(task_id)
            except (KeyboardInterrupt, SystemExit):
                logger.info("工人行程收到中斷信號，正在關閉。")
                break
            except Exception:
                logger.exception("工人在主循環中發生嚴重錯誤，將在10秒後重試。")
                await asyncio.sleep(10)

    # 為了能在同步函數中運行異步循環
    asyncio.run(main_loop())


if __name__ == "__main__":
    # 這部分保留用於獨立測試
    # 為了直接運行, 需要一個模擬的佇列
    class MockQueue:
        """模擬佇列."""

        def put(self, *args: Any, **kwargs: Any) -> None:
            """模擬 put."""
            pass

    transcriber_worker_process(MockQueue(), mp.Queue(), mp.Queue(), {})
"""模擬轉寫工人模組"""
import asyncio
import multiprocessing as mp
import time
from typing import Any, Optional

import aiosqlite

from prometheus.core.logging.log_manager import LogManager
from prometheus.transcriber.core import DATABASE_FILE

# --- 日誌記錄器設定 ---
log_manager = LogManager(log_file="transcriber_mock_worker.log")
logger = log_manager.get_logger(__name__)


async def simulate_task_processing(task_id: str) -> None:
    """
    模擬處理一個指定的轉寫任務。

    Args:
        task_id (str): 要模擬處理的任務 ID。
    """
    logger.info("模擬處理任務: %s", task_id)

    try:
        # 1. 模擬更新任務狀態為 'processing'
        await update_task_status_in_db(task_id, "processing")
        logger.info("任務 %s: 狀態更新為 -> processing", task_id)
        await asyncio.sleep(0.5)  # 模擬處理延遲

        # 2. 模擬轉寫完成
        mock_transcript = f"這是任務 {task_id} 的模擬轉寫結果。"
        logger.info("任務 %s: 模擬轉寫完成。", task_id)
        await asyncio.sleep(0.5)

        # 3. 更新最終結果
        await update_task_status_in_db(
            task_id, "completed", result_text=mock_transcript
        )
        logger.info("任務 %s: 狀態更新為 -> completed", task_id)

    except Exception as e:
        logger.exception("模擬處理任務 %s 過程中發生錯誤", task_id)
        await update_task_status_in_db(task_id, "failed", error_message=str(e))
        logger.info("任務 %s: 狀態更新為 -> failed", task_id)


async def update_task_status_in_db(
    task_id: str,
    status: str,
    result_text: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    """在資料庫中更新任務的狀態、結果或錯誤訊息。"""
    try:
        async with aiosqlite.connect(DATABASE_FILE) as db:
            await db.execute(
                """
                UPDATE transcription_tasks
                SET status = ?, result_text = ?, error_message = ?
                WHERE id = ?
                """,
                (status, result_text, error_message, task_id),
            )
            await db.commit()
    except aiosqlite.Error as e:
        logger.exception("更新任務 %s 狀態時發生資料庫錯誤", task_id)


def mock_worker_process(
    log_queue: Optional[mp.Queue],
    task_queue: mp.Queue,
    result_queue: Optional[mp.Queue],
    config: Optional[dict[str, Any]],
) -> None:
    """
    模擬轉寫工人行程的主函數。

    它會持續從任務佇列中獲取任務 ID，並呼叫 `simulate_task_processing` 進行模擬處理。
    """
    logger.info("模擬轉寫工人行程已啟動 (PID: %s)", mp.current_process().pid)

    async def main_loop() -> None:
        while True:
            try:
                task_id = task_queue.get()
                if task_id is None:
                    logger.info("收到結束信號，模擬工人行程即將關閉。")
                    break
                await simulate_task_processing(task_id)
            except (KeyboardInterrupt, SystemExit):
                logger.info("模擬工人行程收到中斷信號，正在關閉。")
                break
            except Exception:
                logger.exception("模擬工人在主循環中發生嚴重錯誤，將在10秒後重試。")
                await asyncio.sleep(10)

    asyncio.run(main_loop())
