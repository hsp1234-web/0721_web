import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import sys

# 建立 FastAPI 應用程式實例
app = FastAPI(
    title="鳳凰之心-後端引擎",
    description="提供儀表板介面與核心 API 服務",
    version="1.3.0"
)

# --- 關鍵修正 v1.3 ---
# 採用「環境變數優先」策略，以接收來自啟動腳本的精準路徑
print("="*50, file=sys.stderr)
print("🚀 伺服器路徑解析偵錯資訊 (v1.3)", file=sys.stderr)

BASE_DIR = None
# 優先從環境變數讀取由指揮中心注入的根目錄路徑
injected_path = os.environ.get('PHOENIX_HEART_ROOT')

if injected_path:
    print("   - ✅ 偵測到指揮中心注入的路徑。", file=sys.stderr)
    BASE_DIR = Path(injected_path)
else:
    print("   - ⚠️ 未偵測到指揮中心注入的路徑，嘗試備用方案...", file=sys.stderr)
    try:
        # 備用方案 1: 使用 __file__
        BASE_DIR = Path(__file__).resolve().parent
        print("   - ✅ 備用方案 1: 使用 __file__ 成功。", file=sys.stderr)
    except NameError:
        # 備用方案 2: 使用當前工作目錄
        BASE_DIR = Path.cwd()
        print("   - ✅ 備用方案 2: 使用 cwd() 成功。", file=sys.stderr)

print(f"   - 當前工作目錄 (os.getcwd): {os.getcwd()}", file=sys.stderr)
print(f"   - 計算出的基準目錄 (BASE_DIR): {BASE_DIR}", file=sys.stderr)

templates_dir = BASE_DIR / "templates"
print(f"   - 目標模板目錄: {templates_dir}", file=sys.stderr)

if not templates_dir.is_dir():
    print(f"   - ❌ 錯誤：在上述路徑找不到 'templates' 資料夾！", file=sys.stderr)
    print(f"   - 檔案列表 @ {BASE_DIR}: {[p.name for p in BASE_DIR.iterdir()]}", file=sys.stderr)
else:
    print(f"   - ✅ 成功找到 'templates' 資料夾。", file=sys.stderr)
print("="*50, file=sys.stderr)
# --- 偵錯日誌結束 ---


# 1. 設定模板引擎
templates = Jinja2Templates(directory=str(templates_dir))

# 2. 掛載靜態檔案目錄 (可選，但為良好實踐)
static_path = BASE_DIR / "static"
if static_path.is_dir():
    app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    根路徑端點。
    當使用者訪問網站首頁時，這個函式會被觸發。
    它會回傳渲染後的 dashboard.html 頁面。
    """
    return templates.TemplateResponse(
        "dashboard.html", {"request": request}
    )

# --- WebSocket 和其他 API 端點可以加在這裡 ---
# 例如: @app.websocket("/ws/logs") ...

if __name__ == "__main__":
    port = int(os.environ.get("FASTAPI_PORT", 8000))
    uvicorn.run("server_main:app", host="0.0.0.0", port=port, reload=True)
