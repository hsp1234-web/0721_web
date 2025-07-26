# 繁體中文: main.py - 統一指揮中心
# 繁體中文: main.py - 統一指揮中心 (最終版)
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI

# --- 業務邏輯與路由導入 ---
# 放棄動態加載，回歸到最穩定、最明確的靜態導入
from apps.transcriber import logic as transcriber_logic
from apps.quant.main import router as quant_router
from apps.transcriber.main import router as transcriber_router

# --- FastAPI 生命週期管理 ---
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    處理應用程式啟動與關閉事件。
    """
    print("--- 指揮中心啟動程序開始 ---")
    transcriber_logic.start_worker()
    yield
    print("--- 指揮中心關閉程序開始 ---")
    transcriber_logic.stop_worker()
    print("指揮中心已成功關閉。")

# --- FastAPI 應用實例 ---
app = FastAPI(
    title="統一指揮中心",
    description="整合量化分析與語音轉錄服務的 API (靜態路由加載)",
    version="2.0.0", # 重大版本更新
    lifespan=lifespan,
)

# --- 手動掛載路由 ---
print("正在手動掛載 API 路由器...")
app.include_router(quant_router)
print(f"成功掛載來自 'quant' 的路由器。")
app.include_router(transcriber_router)
print(f"成功掛載來自 'transcriber' 的路由器。")

# --- 主程式入口 ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
