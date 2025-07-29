# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import os
import json
from pathlib import Path

app = FastAPI()

STATE_FILE = Path(os.getenv("STATE_FILE", "/tmp/phoenix_state.json"))

@app.get("/api/get-action-url")
async def get_action_url():
    """
    讀取共享狀態檔案，並返回其中的 action_url (如果存在)。
    """
    action_url = None
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                action_url = state.get("action_url")
        except (json.JSONDecodeError, IOError):
            pass # 檔案可能正在寫入，忽略錯誤

    if action_url:
        return JSONResponse(content={"status": "success", "url": action_url})
    else:
        return JSONResponse(content={"status": "pending"}, status_code=404)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
