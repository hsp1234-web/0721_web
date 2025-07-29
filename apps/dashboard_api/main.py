# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import os
import json
from pathlib import Path

app = FastAPI()

# 共享狀態將透過一個臨時 json 檔案來傳遞，這是跨程序通訊最簡單可靠的方式之一
STATE_FILE = Path(os.getenv("STATE_FILE", "/tmp/phoenix_state.json"))

@app.get("/api/status")
async def get_status():
    """
    讀取共享狀態檔案並返回其內容。
    """
    if not STATE_FILE.exists():
        return JSONResponse(content={"error": "State file not found"}, status_code=404)

    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        return JSONResponse(content=state)
    except (json.JSONDecodeError, IOError) as e:
        return JSONResponse(content={"error": f"Failed to read or parse state file: {e}"}, status_code=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
