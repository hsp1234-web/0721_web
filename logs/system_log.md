- **INFO**: 日誌系統初始化完成，日誌將記錄於: logs/system_log.md
- **INFO**: 鳳凰之心伺服器開始啟動...
- **INFO**: 正在從 /app/templates 載入模板...
### ❌ 嚴重錯誤
- **ERROR**: Traceback (most recent call last):
  File "/app/.e2e_venv/lib/python3.12/site-packages/starlette/routing.py", line 694, in lifespan
    async with self.lifespan_context(app) as maybe_state:
               ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jules/.pyenv/versions/3.12.11/lib/python3.12/contextlib.py", line 210, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/app/.e2e_venv/lib/python3.12/site-packages/fastapi/routing.py", line 134, in merged_lifespan
    async with original_context(app) as maybe_original_state:
               ^^^^^^^^^^^^^^^^^^^^^
  File "/home/jules/.pyenv/versions/3.12.11/lib/python3.12/contextlib.py", line 210, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/app/.e2e_venv/lib/python3.12/site-packages/fastapi/routing.py", line 134, in merged_lifespan
    async with original_context(app) as maybe_original_state:
               ^^^^^^^^^^^^^^^^^^^^^
  File "/home/jules/.pyenv/versions/3.12.11/lib/python3.12/contextlib.py", line 210, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/app/server_main.py", line 41, in lifespan
    app.state.templates = Jinja2Templates(directory=str(templates_dir))
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.e2e_venv/lib/python3.12/site-packages/starlette/templating.py", line 97, in __init__
    assert jinja2 is not None, "jinja2 must be installed to use Jinja2Templates"
           ^^^^^^^^^^^^^^^^^^
AssertionError: jinja2 must be installed to use Jinja2Templates

### ❌ 嚴重錯誤
- **ERROR**: Application startup failed. Exiting.
- **INFO**: 日誌系統初始化完成，日誌將記錄於: logs/system_log.md
- **INFO**: 鳳凰之心伺服器開始啟動...
- **INFO**: 正在從 /app/templates 載入模板...
- **INFO**: Application startup complete.
- **INFO**: Shutting down
- **INFO**: Waiting for application shutdown.
- **INFO**: FastAPI 應用程式正在關閉...
- **INFO**: Application shutdown complete.
- **INFO**: Finished server process [4611]
- **INFO**: 日誌系統初始化完成，日誌將記錄於: logs/system_log.md
- **INFO**: 鳳凰之心伺服器開始啟動...
- **INFO**: 正在從 /app/templates 載入模板...
- **INFO**: Application startup complete.
- **INFO**: Uvicorn running on http://127.0.0.1:8002 (Press CTRL+C to quit)
- **INFO**: 127.0.0.1:38770 - "GET / HTTP/1.1" 200
- **INFO**: 127.0.0.1:38786 - "GET /docs HTTP/1.1" 200
- **INFO**: 127.0.0.1:38796 - "GET /quant/data HTTP/1.1" 200
- **INFO**: 127.0.0.1:38802 - "POST /transcriber/upload HTTP/1.1" 200
- **INFO**: 127.0.0.1:58692 - "POST /transcriber/upload HTTP/1.1" 200
- **INFO**: Shutting down
- **INFO**: Waiting for application shutdown.
- **INFO**: FastAPI 應用程式正在關閉...
- **INFO**: Application shutdown complete.
- **INFO**: Finished server process [5112]
