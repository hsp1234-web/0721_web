from fastapi import FastAPI
import os
import importlib

# --- 應用程式實例 ---
app = FastAPI(
    title="高效能 Web 應用程式",
    description="一個現代化、可維護的後端架構，遵循模組化、依賴注入與懶啟動原則。",
    version="1.0.0",
)

# --- 根路由 ---
@app.get("/", tags=["系統"])
def read_root():
    """
    根路由，提供一個簡單的歡迎訊息。
    """
    return {"message": "歡迎來到高效能 Web 應用程式架構！"}

# --- 動態路由掃描與聚合 ---
APPS_DIR = "apps"

print("[應用主入口] 開始掃描業務邏輯單元 (apps)...")

for app_name in os.listdir(APPS_DIR):
    app_path = os.path.join(APPS_DIR, app_name)

    # 確保它是一個目錄，並且不是 __pycache__ 之類的特殊目錄
    if os.path.isdir(app_path) and not app_name.startswith('__'):
        router_module_path = f"{APPS_DIR}.{app_name}.main"

        try:
            # 動態匯入模組
            router_module = importlib.import_module(router_module_path)

            # 檢查模組中是否有 'router' 物件，並且它是 APIRouter 的實例
            if hasattr(router_module, 'router'):
                print(f"  -> 發現並註冊路由: {app_name}")
                # 引入子應用的路由
                app.include_router(
                    router_module.router,
                    prefix=f"/{app_name}", # 給子應用的所有 API 加上前綴，例如 /transcriber
                    tags=[app_name.capitalize()], # 在 OpenAPI 文件中為其建立分類
                )
            else:
                 print(f"  -! 在 {router_module_path} 中找不到 'router' 物件。")

        except ImportError as e:
            # 如果 'main.py' 不存在或有匯入錯誤，則忽略
            print(f"  -! 無法從 {app_name} 匯入路由: {e}")
        except Exception as e:
            print(f"  -! 處理 {app_name} 時發生未知錯誤: {e}")

print("[應用主入口] 所有路由掃描完畢。")
