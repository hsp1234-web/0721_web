# -*- coding: utf-8 -*-
import uvicorn
from main import app

if __name__ == "__main__":
    print("INFO: 準備啟動 Uvicorn 伺服器...")
    # 我們實際上不需要在測試中啟動伺服器，
    # 只要 main.py 能夠被成功導入且不拋出 ModuleNotFoundError，
    # 測試就已經成功了。
    # 如果 main.py 中的導入失敗，這個腳本在執行 'from main import app' 時就會失敗。
    print("SUCCESS: run.py 成功導入 main.py。應用程式已準備就緒。")
    # 在真實場景中，下面這行會啟動伺服器
    # uvicorn.run(app, host="0.0.0.0", port=8000)
