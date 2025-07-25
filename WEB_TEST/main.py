# -*- coding: utf-8 -*-
import sys
from fastapi import FastAPI

try:
    # 這是我們測試的核心：嘗試導入 pydantic_settings
    # 如果 uv_manager.py 成功安裝了 requirements.txt 中的所有內容
    # 這裡就不會拋出 ModuleNotFoundError
    from pydantic_settings import BaseSettings
    print("SUCCESS: pydantic_settings 導入成功。")

    class Settings(BaseSettings):
        app_name: str = "鳳凰之心測試應用"

    settings = Settings()
    app = FastAPI()

    @app.get("/")
    def read_root():
        return {"message": f"歡迎來到 {settings.app_name}"}

except ImportError as e:
    print(f"FATAL: 依賴導入失敗: {e}", file=sys.stderr)
    # 拋出異常以確保測試能捕捉到失敗
    raise
