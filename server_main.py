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
    version="1.4.0"
)

# --- 路徑解析與偵錯日誌 (維持不變) ---
print("="*50, file=sys.stderr)
print("🚀 伺服器路徑解析偵錯資訊 (v1.4)", file=sys.stderr)

BASE_DIR = None
injected_path = os.environ.get('PHOENIX_HEART_ROOT')

if injected_path:
    print("   - ✅ 偵測到指揮中心注入的路徑。", file=sys.stderr)
    BASE_DIR = Path(injected_path)
else:
    print("   - ⚠️ 未偵測到指揮中心注入的路徑，嘗試備用方案...", file=sys.stderr)
    try:
        BASE_DIR = Path(__file__).resolve().parent
        print("   - ✅ 備用方案 1: 使用 __file__ 成功。", file=sys.stderr)
    except NameError:
        BASE_DIR = Path.cwd()
        print("   - ✅ 備用方案 2: 使用 cwd() 成功。", file=sys.stderr)

print(f"   - 計算出的基準目錄 (BASE_DIR): {BASE_DIR}", file=sys.stderr)
templates_dir = BASE_DIR / "templates"
print(f"   - 目標模板目錄: {templates_dir}", file=sys.stderr)

if not templates_dir.is_dir():
    print(f"   - ❌ 錯誤：在上述路徑找不到 'templates' 資料夾！", file=sys.stderr)
else:
    print(f"   - ✅ 成功找到 'templates' 資料夾。", file=sys.stderr)
print("="*50, file=sys.stderr)
# --- 偵錯日誌結束 ---


# 設定模板引擎
templates = Jinja2Templates(directory=str(templates_dir))

# 掛載靜態檔案目錄
static_path = BASE_DIR / "static"
if static_path.is_dir():
    app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    根路徑端點，回傳儀表板 HTML。
    """
    return templates.TemplateResponse(
        "dashboard.html", {"request": request}
    )

if __name__ == "__main__":
    port = int(os.environ.get("FASTAPI_PORT", 8000))
    
    # --- 關鍵修正 v1.4 ---
    # 將 reload=True 移除 (或設為 False)。
    # reload 功能是開發模式專用，在 Colab 的生產/部署環境中會引起衝突。
    # 移除後，Uvicorn 會以穩定、單一程序的方式啟動。
    uvicorn.run("server_main:app", host="0.0.0.0", port=port)
