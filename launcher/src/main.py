# launcher/src/main.py

import os
import sys
import time
import toml
from pathlib import Path

# 將專案根目錄加入 sys.path
# 這樣我們就可以 `from src.core import ...`
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.display.dashboard import Dashboard
from src.core.environment import EnvironmentManager
from src.core.installer import Installer
from src.core.process_manager import ProcessManager
from src.core.log_database import LogDatabase

def get_colab_url(port: int, dashboard: Dashboard) -> str:
    """使用 google.colab.output 來獲取公開 URL。"""
    try:
        from google.colab import output
        url = output.eval_js(f'google.colab.kernel.proxyPort({port})')
        dashboard.add_log(f"✅ 成功獲取 Colab URL: {url}")
        return url
    except ImportError:
        dashboard.add_log("⚠️ 未在 Colab 環境中，無法獲取公開 URL。將使用本地地址。")
        return f"http://localhost:{port}"
    except Exception as e:
        dashboard.add_log(f"❌ 獲取 Colab URL 失敗: {e}")
        return "獲取 URL 失敗"

def main():
    """
    鳳凰之心啟動器主函式。
    """
    # 1. 載入設定
    config_path = project_root / "config" / "settings.toml"
    try:
        config = toml.load(config_path)
    except FileNotFoundError:
        print(f"錯誤：找不到設定檔 {config_path}")
        sys.exit(1)

    # 2. 初始化日誌資料庫 (如果啟用)
    log_db = None
    if config["log_archive"]["enabled"]:
        archive_path = Path("/content") / config["log_archive"]["folder_name"]
        db_path = archive_path / "launcher_logs.db"
        log_db = LogDatabase(db_path, max_size_kb=config["log_archive"]["max_db_size_kb"])

    # 3. 初始化儀表板
    dashboard = Dashboard(
        log_display_lines=config["launcher"]["log_display_lines"],
        timezone=config["launcher"]["timezone"],
        log_db=log_db
    )
    dashboard.start()
    dashboard.add_log("✅ 指揮中心介面已啟動。")

    try:
        # 3. 設定路徑
        if config.get("mode", {}).get("test_mode", False):
            base_path = Path("/tmp/mock_content")
        else:
            base_path = Path("/content")  # Colab-specific

        project_path = base_path / config["project"]["project_folder_name"]
        dashboard.add_log(f"專案路徑設定為: {project_path}")

        # 4. 執行第一階段：同步核心任務
        dashboard.update_status("階段", "環境準備")

        # 4a. 環境檢查
        env_manager = EnvironmentManager(project_path)
        if not env_manager.run_all_checks():
            dashboard.add_log("❌ 環境檢查失敗，程序中止。")
            time.sleep(5)
            return #
        dashboard.add_log("✅ 環境檢查通過。")

        # 4b. 安裝核心依賴
        installer = Installer(project_path)
        if not installer.install_core_dependencies():
             dashboard.add_log("❌ 核心依賴安裝失敗，程序中止。")
             time.sleep(5)
             return
        dashboard.add_log("✅ 核心依賴安裝成功。")

        # 4c. 下載或更新程式碼
        if not project_path.exists():
            if not installer.download_code(config["project"]["repository_url"], config["project"]["target_branch_or_tag"]):
                dashboard.add_log("❌ 程式碼下載失敗，程序中止。")
                time.sleep(5)
                return
            dashboard.add_log("✅ 程式碼下載成功。")
        else:
            dashboard.add_log("ℹ️ 專案目錄已存在，跳過下載。")

        # 4d. 安裝專案依賴
        os.chdir(project_path) # 切換工作目錄以正確執行 pip
        dashboard.add_log(f"工作目錄切換至: {os.getcwd()}")
        if installer.install_dependencies():
            dashboard.add_log("✅ 專案依賴安裝成功。")
        else:
            dashboard.add_log("⚠️ 專案依賴安裝被跳過（可能由於空間不足）。應用程式可能功能不全。")


        dashboard.update_status("階段", "核心服務啟動")
        dashboard.add_log("🚀 所有前置任務完成！準備啟動主應用程式...")

        # 5. 執行第二階段：非同步任務 (啟動伺服器)
        dashboard.update_status("階段", "啟動主應用")
        process_manager = ProcessManager(dashboard, project_path)
        process_manager.start_server()

        # 嘗試獲取 Colab URL
        # 這裡需要一個更好的方法來檢測 uvicorn 何時準備就緒
        dashboard.add_log("⏳ 等待伺服器啟動 (約 5 秒)...")
        time.sleep(5)
        app_url = get_colab_url(8000, dashboard)
        dashboard.update_status("應用 URL", app_url)


        # 在測試模式下，成功啟動伺服器後短暫等待即退出
        if config.get("mode", {}).get("test_mode", False):
            dashboard.add_log("✅ 測試模式：任務完成，3秒後自動退出。")
            time.sleep(3)
        else:
            # 保持儀表板運行
            while True:
                dashboard.update()
                time.sleep(config["launcher"]["refresh_rate_seconds"])

    except KeyboardInterrupt:
        dashboard.add_log("🟡 手動中斷程序...")
    except Exception as e:
        dashboard.add_log(f"🔴 發生未預期的錯誤: {e}")
        import traceback
        dashboard.add_log(traceback.format_exc())
    finally:
        dashboard.add_log("🛑 指揮中心正在關閉。")
        if 'process_manager' in locals():
            process_manager.stop_server()
        dashboard.stop()
        print("鳳凰之心指揮中心已關閉。")


if __name__ == "__main__":
    main()
