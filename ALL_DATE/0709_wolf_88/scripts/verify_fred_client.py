import sys
from pathlib import Path

# --- 路徑修正 ---
# 為了讓此腳本可以獨立執行，需要手動將專案根目錄加到 sys.path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "src"))

from prometheus.core.config import ConfigManager
from prometheus.core.clients.fred import FredClient
from rich.console import Console

console = Console()

def verify_fred_client():
    """
    驗證 FredClient 的功能是否正常。
    1. 檢查 API 金鑰是否存在。
    2. 嘗試獲取一個已知的數據系列 (T10Y2Y)。
    3. 打印結果或錯誤訊息。
    """
    console.print("\n[bold cyan]--- 驗證 FRED 客戶端 ---[/bold cyan]")
    config = ConfigManager.get_instance()
    fred_api_key = config.get("api_keys.fred")

    if not fred_api_key:
        console.print(
            "[bold red]錯誤：找不到 FRED API 金鑰 (api_keys.fred)。請在設定中配置。[/bold red]"
        )
        return

    console.print("✅ FRED API 金鑰已找到。")

    try:
        client = FredClient(api_key=fred_api_key)
        console.print("正在獲取 10年-2年期美國國債利差 (T10Y2Y)...")
        df = client.fetch_data("T10Y2Y")

        if not df.empty:
            console.print("✅ 成功獲取數據：")
            console.print(df.head())
        else:
            console.print("[bold red]錯誤：無法獲取 T10Y2Y 數據，但未引發例外。[/bold red]")

    except Exception as e:
        console.print(f"[bold red]獲取數據時發生錯誤：{e}[/bold red]")

if __name__ == "__main__":
    verify_fred_client()
