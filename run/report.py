# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║                 📊 離線報告生成器 V23.2 (自動依賴安裝)                ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   - 職責：從 state.db 讀取數據，生成對行動裝置友善的 Markdown 報告。 ║
# ║   - 時機：請在「指揮中心」儲存格完全停止後再執行此腳本。             ║
# ║   - 特點：可選擇性生成不同報告，所有輸出都在可一鍵複製的區塊中。     ║
# ║   - 新功能：自動使用 uv 安裝報告所需的依賴套件。                     ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 📊 最終任務報告生成器 v23.2 { vertical-output: true, display-mode: "form" }
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
content_root = Path("/content")
project_path = content_root / PROJECT_FOLDER_NAME
report_script = project_path / "scripts" / "generate_report.py"
requirements_file = project_path / "scripts" / "requirements-report.txt"
db_file = project_path / "state.db"
config_file = project_path / "config.json"
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
elif not requirements_file.exists():
    print(f"❌ 嚴重錯誤：找不到報告依賴檔案 '{requirements_file}'。")
else:
    print("✅ 所有必要檔案均已找到。")

    # --- 步驟 1: 自動安裝依賴 ---
    print("\n--- 正在檢查並安裝報告所需依賴 ---")
    try:
        # 確保 uv 已安裝
        subprocess.run(["uv", "--version"], check=True, capture_output=True, text=True)

        install_command = [
            "uv", "pip", "install", "-r", str(requirements_file)
        ]
        install_process = subprocess.run(
            install_command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=True # 如果安裝失敗則拋出例外
        )
        print("✅ 依賴已就緒。")
        # print(install_process.stdout) # 可選：顯示詳細安裝日誌

        # --- 步驟 2: 執行報告生成腳本 ---
        print("\n--- 正在生成報告 ---")
        report_command = [
            sys.executable, str(report_script),
            "--db-file", str(db_file),
            "--config-file", str(config_file)
        ]

        report_process = subprocess.run(
            report_command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd=project_path
        )

        if report_process.returncode != 0:
            print("❌ 報告生成失敗。腳本輸出：")
            print(report_process.stdout)
            if report_process.stderr:
                print("--- 錯誤訊息 ---")
                print(report_process.stderr)
        else:
            print("✅ 報告生成腳本執行成功。")
            print(report_process.stdout)

            # --- 步驟 3: 顯示報告 ---
            report_files_map = {
                "GENERATE_SUMMARY_REPORT": ("綜合戰情簡報", "summary_report.md"),
                "GENERATE_PERFORMANCE_REPORT": ("效能分析報告", "performance_report.md"),
                "GENERATE_DETAILED_LOG_REPORT": ("詳細日誌報告", "detailed_log_report.md"),
            }

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

    except subprocess.CalledProcessError as e:
        print("❌ 依賴安裝失敗。")
        print(e.stdout)
        if e.stderr:
            print("--- 錯誤訊息 ---")
            print(e.stderr)
    except FileNotFoundError:
        print("❌ 錯誤：找不到 'uv' 命令。請確保 uv 已安裝在您的環境中。")
        print("   您可以嘗試執行 `pip install uv` 來安裝。")
    except Exception as e:
        print(f"❌ 執行時發生未預期的錯誤: {e}")
