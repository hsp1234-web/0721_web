# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║                 📊 離線報告生成器 V23.1 (多選項版)                    ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   - 職責：從 state.db 讀取數據，生成對行動裝置友善的 Markdown 報告。 ║
# ║   - 時機：請在「指揮中心」儲存格完全停止後再執行此腳本。             ║
# ║   - 特點：可選擇性生成不同報告，所有輸出都在可一鍵複製的區塊中。     ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 📊 最終任務報告生成器 v23.1 { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **Part 1: 報告設定**
#@markdown > **指定專案資料夾以找到 state.db 檔案。**
#@markdown ---
#@markdown **專案資料夾名稱 (PROJECT_FOLDER_NAME)**
PROJECT_FOLDER_NAME = "WEB1" #@param {type:"string"}

#@markdown ---
#@markdown ### **Part 2: 報告內容**
#@markdown > **選擇您想要包含在報告中的內容。**
#@markdown ---
#@markdown **產生任務總結報告 (GENERATE_SUMMARY_REPORT)**
GENERATE_SUMMARY_REPORT = True #@param {type:"boolean"}
#@markdown **產生效能分析報告 (GENERATE_PERFORMANCE_REPORT)**
GENERATE_PERFORMANCE_REPORT = True #@param {type:"boolean"}
#@markdown **產生詳細日誌報告 (GENERATE_DETAILED_LOG_REPORT)**
GENERATE_DETAILED_LOG_REPORT = True #@param {type:"boolean"}


#@markdown ---
#@markdown > **點擊「執行」以生成報告。**
#@markdown ---
import os
import sys
import subprocess
from pathlib import Path
from IPython.display import display, Markdown, Code

# --- 設定路徑 ---
# Colab 的內容根目錄
content_root = Path("/content")
# 專案資料夾的路徑，這也是 repo 的根目錄
project_path = content_root / PROJECT_FOLDER_NAME

# 修正路徑邏輯：報告腳本位於專案資料夾內部
report_script = project_path / "scripts" / "generate_report.py"

db_file = project_path / "state.db"
config_file = project_path / "config.json"
# generate_report.py 預設會輸出到其工作目錄下的 logs/，所以我們將 CWD 設為 project_path
report_output_dir = project_path / "logs"

# --- 檢查必要檔案 ---
if not project_path.is_dir():
    print(f"❌ 錯誤：找不到專案資料夾 '{project_path}'。請確認「指揮中心」已成功執行，且資料夾名稱正確。")
elif not db_file.exists():
    print(f"❌ 錯誤：在 '{project_path}' 中找不到 state.db。")
    print("   請確認「指揮中心」已正常運行並被手動中斷，以確保狀態已寫入資料庫。")
elif not config_file.exists():
    print(f"❌ 錯誤：在 '{project_path}' 中找不到 config.json。")
    print("   請確認「指揮中心」已成功執行。")
elif not report_script.is_file():
    print(f"❌ 嚴重錯誤：找不到報告生成腳本 '{report_script}'。")
else:
    print("✅ 所有必要檔案均已找到，準備生成報告...")

    # --- 執行報告生成腳本 ---
    command = [
        sys.executable, str(report_script),
        "--db-file", str(db_file),
        "--config-file", str(config_file)
    ]

    # 在專案資料夾的上下文中執行
    process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding='utf-8',
        cwd=project_path
    )

    if process.returncode != 0:
        print("❌ 報告生成失敗。腳本輸出：")
        print(process.stdout)
        if process.stderr:
            print("--- 錯誤訊息 ---")
            print(process.stderr)
    else:
        print("✅ 報告生成腳本執行成功。")
        print(process.stdout)

        # --- 顯示報告 ---
        report_files_map = {
            "GENERATE_SUMMARY_REPORT": ("綜合戰情簡報", "summary_report.md"),
            "GENERATE_PERFORMANCE_REPORT": ("效能分析報告", "performance_report.md"),
            "GENERATE_DETAILED_LOG_REPORT": ("詳細日誌報告", "detailed_log_report.md"),
        }

        # 根據用戶勾選的變數來決定顯示哪些報告
        reports_to_show_keys = [key for key, value in locals().items() if key.startswith("GENERATE_") and value]

        if not reports_to_show_keys:
             print("\nℹ️ 您沒有選擇任何要顯示的報告。")
        else:
            all_reports_found = True
            for key in reports_to_show_keys:
                if key in report_files_map:
                    report_name, report_filename = report_files_map[key]
                    report_path = report_output_dir / report_filename
                    if report_path.exists():
                        print("\n" + "="*80)
                        display(Markdown(f"## 📊 {report_name}"))
                        print("="*80)
                        display(Code(data=report_path.read_text(encoding='utf-8'), language='markdown'))
                    else:
                        print(f"⚠️ 警告：找不到報告檔案 '{report_path}'。")
                        all_reports_found = False

            if all_reports_found:
                print("\n🎉 所有已選報告已顯示完畢。")
            else:
                print("\n⚠️ 部分所選報告未能顯示。")
