import importlib
import os
import sys
from typing import Dict

from fastapi import APIRouter, FastAPI
from fastapi.routing import APIRoute

# 將專案根目錄加入 sys.path，確保無論從哪裡啟動都能正確找到模組
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


# --- 應用程式實例 ---
app = FastAPI(
    title="高效能 Web 應用程式",
    description="一個現代化、可維護的後端架構，遵循模組化、依賴注入與懶啟動原則。",
    version="1.0.0",
)


# --- 根路由 ---
@app.get("/", tags=["系統"])
def read_root() -> Dict[str, str]:
    """根路由，提供一個簡單的歡迎訊息。"""
    return {"message": "歡迎來到高效能 Web 應用程式架構！"}


# --- 動態路由掃描與聚合 ---
APPS_DIR = "apps"

print("[應用主入口] 開始掃描業務邏輯單元 (apps)...")

for app_name in os.listdir(APPS_DIR):
    app_path = os.path.join(APPS_DIR, app_name)

    if os.path.isdir(app_path) and not app_name.startswith("__"):
        router_module_path = f"{APPS_DIR}.{app_name}.main"

        try:
            router_module = importlib.import_module(router_module_path)

            if hasattr(router_module, "router"):
                print(f"  -> 發現並註冊路由: {app_name}")
                router_instance = getattr(router_module, "router")
                if isinstance(router_instance, APIRouter):
                    app.include_router(
                        router_instance,
                        prefix=f"/{app_name}",
                        tags=[app_name.capitalize()],
                    )
            else:
                print(f"  -! 在 {router_module_path} 中找不到 'router' 物件。")

        except ImportError as e:
            print(f"  -! 無法從 {app_name} 匯入路由: {e}")
        except Exception as e:
            print(f"  -! 處理 {app_name} 時發生未知錯誤: {e}")

print("[應用主入口] 所有路由掃描完畢。")

# --- 診斷資訊：打印所有已註冊的路由 ---
print("[應用主入口] --- 已註冊的 API 路由 ---")
for route in app.routes:
    if isinstance(route, APIRoute):
        methods = ", ".join(route.methods)
        print(f"  - 路徑: {route.path}, 方法: {{{methods}}}, 名稱: {route.name}")
    else:
        # For mounted sub-applications, etc.
        print(f"  - 掛載點/路由: {route}")
print("[應用主入口] --- 路由列表結束 ---")
