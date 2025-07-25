# -*- coding: utf-8 -*-
# ==============================================================================
# SECTION 0: 環境初始化與核心模組導入
# ==============================================================================
import os
import sys
import subprocess
import time
import io
from pathlib import Path
from datetime import datetime, timezone, timedelta
from IPython.display import display, HTML, Javascript

# ==============================================================================
# SECTION 1: 日誌捕獲與歸檔
# ==============================================================================
log_capture_string = io.StringIO()

class Tee(io.StringIO):
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    def flush(self):
        for f in self.files:
            f.flush()

def get_taipei_time() -> datetime:
    """獲取當前亞洲/台北時間"""
    utc_now = datetime.now(timezone.utc)
    taipei_tz = timezone(timedelta(hours=8))
    return utc_now.astimezone(taipei_tz)

def save_log_file(archive_folder_name: str, status: str):
    """將捕獲的日誌儲存到指定的中文資料夾"""
    try:
        # 在 Colab 環境中，我們總是在 /content/ 下創建歸檔
        base_path = Path("/content")
        archive_path = base_path / archive_folder_name
        archive_path.mkdir(parents=True, exist_ok=True)

        timestamp = get_taipei_time().isoformat()
        filename = f"鳳凰之心-{status}-日誌-{timestamp}.txt"
        filepath = archive_path / filename

        print(f"\n📋 正在歸檔日誌至: {filepath}")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(log_capture_string.getvalue())

        print(f"✅ 日誌歸檔成功。")

    except Exception as e:
        # 如果日誌歸檔失敗，直接打印錯誤到原始的 stderr
        print(f"❌ 日誌歸檔失敗: {e}", file=sys.__stderr__)

# 重定向 stdout 和 stderr 以捕獲所有輸出
original_stdout = sys.stdout
original_stderr = sys.stderr
sys.stdout = Tee(original_stdout, log_capture_string)
sys.stderr = Tee(original_stderr, log_capture_string)


# ==============================================================================
# SECTION 2: 核心啟動流程
# ==============================================================================
server_process = None

# --- 從 Colab 表單獲取參數 (如果不在 Colab 環境中，則使用預設值) ---
LOG_DISPLAY_LINES = 100
STATUS_REFRESH_INTERVAL = 0.5
TARGET_FOLDER_NAME = "WEB"
ARCHIVE_FOLDER_NAME = "作戰日誌歸檔"
FASTAPI_PORT = 8000

def run_colab_flow(
    log_display_lines: int,
    status_refresh_interval: float,
    target_folder_name: str,
    archive_folder_name: str,
    fastapi_port: int,
):
    """
    執行完整的 Colab 啟動流程。
    """
    global server_process
    try:
        # --- 啟動時立即歸檔一次日誌 ---
        save_log_file(archive_folder_name, "啟動")

        # --- 步驟 1: 清理並準備顯示區域 ---
        display(Javascript("document.querySelectorAll('.phoenix-launcher-output').forEach(el => el.remove());"))
        time.sleep(0.2)

        container_id = f"phoenix-container-{int(time.time())}"
        display(HTML(f"""
            <div id="{container_id}" class="phoenix-launcher-output" style="height: 95vh; border: 1px solid #444; border-radius: 8px; overflow: hidden;">
                <p style="color: #e8eaed; font-family: 'Noto Sans TC', sans-serif; padding: 20px;">
                    ⚙️ 指揮官，正在初始化鳳凰之心駕駛艙...
                </p>
            </div>
        """))

        # --- 步驟 2: 將參數設定為環境變數 ---
        print("✅ 正在設定環境變數...")
        os.environ['LOG_DISPLAY_LINES'] = str(log_display_lines)
        os.environ['STATUS_REFRESH_INTERVAL'] = str(status_refresh_interval)
        os.environ['ARCHIVE_FOLDER_NAME'] = str(archive_folder_name)
        os.environ['FASTAPI_PORT'] = str(fastapi_port)
        print(f"   - 日誌行數: {log_display_lines}")
        print(f"   - 刷新頻率: {status_refresh_interval}s")
        print(f"   - 歸檔目錄: {archive_folder_name}")
        print(f"   - 服務埠號: {fastapi_port}")

        # --- 步驟 3: 驗證並進入專案目錄 ---
        project_path = Path("/content") / target_folder_name
        if not project_path.is_dir() or not (project_path / "main.py").exists():
            raise FileNotFoundError(f"指定的專案資料夾 '{project_path}' 不存在或缺少 'main.py' 核心檔案。")

        print(f"📂 已成功定位專案目錄: {project_path}")
        os.chdir(project_path)

        # --- 步驟 4: 安裝/驗證專案依賴 (阻塞式) ---
        print("\n🚀 正在配置專案環境，請稍候...")
        install_result = subprocess.run(
            [sys.executable, "uv_manager.py"],
            capture_output=True, text=True, encoding='utf-8'
        )
        if install_result.returncode != 0:
            print("❌ 依賴配置失敗，終止作戰。")
            print("--- STDOUT ---")
            print(install_result.stdout)
            print("--- STDERR ---")
            print(install_result.stderr)
            raise RuntimeError("依賴安裝失敗。")

        print("✅ 專案環境配置成功。")
        print(install_result.stdout)

        # --- 步驟 5: 在背景啟動 FastAPI 伺服器 ---
        print("\n🔥 正在點燃後端引擎...")
        server_process = subprocess.Popen(
            [sys.executable, "run.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True, encoding='utf-8'
        )
        print(f"   - 後端伺服器程序已啟動 (PID: {server_process.pid})。")

        # --- 步驟 6: 等待伺服器就緒並嵌入駕駛艙 ---
        print("📡 正在等待伺服器響應...")
        time.sleep(10)

        print(f"🌍 正在將駕駛艙嵌入至容器 (ID: {container_id})...")
        js_code = f"""
            const container = document.getElementById('{container_id}');
            if (container) {{
                container.innerHTML = '';
                const iframe = document.createElement('iframe');
                const url = new URL(window.location.href);
                const hostname = url.hostname.endsWith('googleusercontent.com')
                    ? `{fastapi_port}-${{url.hostname}}`
                    : `localhost:{fastapi_port}`;
                iframe.src = `https://${{hostname}}`;
                iframe.style.width = '100%';
                iframe.style.height = '100%';
                iframe.style.border = 'none';
                container.appendChild(iframe);
            }}
        """
        display(Javascript(js_code))
        print("\n✅ 鳳凰之心駕駛艙已上線！")
        print("ℹ️ 要停止所有服務，請點擊 Colab 執行單元格左側的「中斷執行」(■) 按鈕。")

        # --- 步驟 7: 監控後端日誌並保持 Colab 活躍 ---
        if server_process.stdout:
            for line in iter(server_process.stdout.readline, ''):
                if line:
                    print(f"[後端引擎]: {line.strip()}")

        server_process.wait()

    except KeyboardInterrupt:
        print("\n\n🛑 [偵測到使用者手動中斷請求...]")
    except Exception as e:
        print(f"\n\n💥 作戰流程發生未預期的嚴重錯誤: {e}", file=sys.__stderr__)
    finally:
        if server_process and server_process.poll() is None:
            print("...正在關閉後端伺服器...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
                print("✅ 後端伺服器已成功終止。")
            except subprocess.TimeoutExpired:
                print("⚠️ 伺服器未能溫和終止，將強制結束。")
                server_process.kill()

        # --- 結束時再次歸檔日誌 ---
        save_log_file(archive_folder_name, "關閉")

        # 恢復 stdout 和 stderr
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        print("\n--- 系統已安全關閉 ---")

if __name__ == '__main__':
    run_colab_flow(
        log_display_lines=LOG_DISPLAY_LINES,
        status_refresh_interval=STATUS_REFRESH_INTERVAL,
        target_folder_name=TARGET_FOLDER_NAME,
        archive_folder_name=ARCHIVE_FOLDER_NAME,
        fastapi_port=FASTAPI_PORT,
    )
