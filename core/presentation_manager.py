import html

class PresentationManager:
    """
    後端驅動前端的核心類別。
    負責生成所有用於渲染和更新前端 UI 的 JavaScript 指令。
    """

    def get_initial_html_structure(self) -> str:
        """返回儀表板的基礎 HTML 結構和 CSS 樣式。"""
        # 這段程式碼直接從使用者提供的 HTML 檔案中提取，並進行了簡化
        return """
        <!DOCTYPE html>
        <html lang="zh-Hant">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>鳳凰之心 - 指揮中心</title>
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&family=Noto+Sans+TC:wght@400;700&display=swap" rel="stylesheet">
            <style>
                :root {
                    --color-bg: #131314; --color-panel-bg: #1e1f20; --color-border: #3c4043;
                    --color-text: #e8eaed; --color-dim: #9aa0a6; --color-header: #8ab4f8;
                    --color-ok: #34a853; --color-warn: #fbbc04; --color-error: #ea4335;
                    --color-info: #4285f4; --color-battle: #8ab4f8;
                    --font-mono: 'Fira Code', 'Courier New', monospace; --font-sans: 'Noto Sans TC', sans-serif;
                    --base-font-size: 15px; --line-height: 1.8;
                }
                html, body { height: 100%; margin: 0; overflow: hidden; box-sizing: border-box; }
                body {
                    background-color: var(--color-bg); color: var(--color-text); font-family: var(--font-mono);
                    font-size: var(--base-font-size); line-height: var(--line-height); display: flex; flex-direction: column;
                }
                .ok { color: var(--color-ok); } .warn { color: var(--color-warn); } .error { color: var(--color-error); }
                .info { color: var(--color-info); } .battle { color: var(--color-battle); } .header { color: var(--color-header); }
                .dim { color: var(--color-dim); } .highlight { color: #ffffff; font-weight: bold; }
                pre { margin: 0; white-space: pre-wrap; word-wrap: break-word; }
                .hidden { display: none !important; }
                #boot-screen { padding: 20px; flex-grow: 1; overflow-y: auto; }
                .progress-bar-container { display: flex; align-items: center; gap: 10px; }
                .progress-bar-container .label { min-width: 220px; }
                #dashboard { display: flex; flex-direction: column; height: 100%; }
                #top-panel { padding: 15px 20px; border-bottom: 1px solid var(--color-border); background-color: var(--color-panel-bg); display: flex; flex-wrap: wrap; gap: 20px 30px; align-items: flex-start; flex-shrink: 0; }
                .panel-section { flex: 1; min-width: 280px; }
                .panel-title { font-family: var(--font-sans); font-weight: bold; color: var(--color-header); margin-bottom: 10px; }
                .service-item { display: flex; align-items: center; margin-bottom: 5px; }
                .service-icon { min-width: 2.2em; }
                .app-button { background-color: var(--color-battle); color: var(--color-bg); border: none; border-radius: 5px; padding: 10px 15px; font-family: var(--font-sans); font-weight: bold; font-size: 1em; cursor: pointer; transition: background-color 0.2s; white-space: nowrap; }
                .app-button:hover { background-color: #a8c7fa; }
                #main-stream-container { flex-grow: 1; overflow-y: auto; padding: 10px 20px 60px 20px; }
                .stream-item { margin-bottom: 15px; word-wrap: break-word; overflow-wrap: break-word; }
                .stream-meta { display: flex; gap: 15px; align-items: center; }
                .stream-icon { min-width: 2em; }
                .stream-ts { color: var(--color-dim); }
                .stream-level { font-weight: bold; min-width: 90px; }
                .stream-text-content { padding-left: calc(2em + 15px); margin-top: 5px; }
                .stream-block-content { margin-top: 0.8em; padding-left: 0; padding-bottom: 0.8em; }
                .data-stream-table { border: 1px solid var(--color-border); padding: 10px; background: rgba(0,0,0,0.2); border-radius: 5px; display: block; width: 100%; max-width: 100%; box-sizing: border-box; margin: 0; }
                .ds-row { display: flex; flex-wrap: wrap; }
                .ds-cell { flex: 1; padding: 2px 10px; border-bottom: 1px solid var(--color-border); min-width: 80px; word-wrap: break-word; overflow-wrap: break-word; }
                .ds-row:last-child .ds-cell { border-bottom: none; }
                .ds-header .ds-cell { font-weight: bold; color: var(--color-header); }
                .ds-separator .ds-cell { padding: 0; height: 1px; background: var(--color-border); flex-basis: 100%; }
                #status-bar { position: fixed; bottom: 0; left: 0; width: 100%; background: var(--color-panel-bg); padding: 8px 20px; border-top: 1px solid var(--color-border); display: flex; justify-content: space-between; align-items: center; font-size: 14px; z-index: 10; box-sizing: border-box; }
                .status-group { display: flex; gap: 25px; }
                @media (max-width: 767px) {
                    body { font-size: 13px; line-height: 1.6; }
                    #top-panel { flex-direction: column; padding: 10px 15px; gap: 15px; }
                    .panel-section { min-width: auto; width: 100%; }
                    #main-stream-container { padding: 10px 15px 60px 15px; }
                    .stream-meta { flex-direction: column; align-items: flex-start; gap: 5px; }
                    .stream-icon, .stream-level { min-width: auto; }
                    .stream-text-content { padding-left: 0; }
                    .stream-block-content { margin-top: 0.5em; padding-bottom: 0.5em; }
                    .data-stream-table .ds-cell, .ds-row { flex-direction: column; }
                    .ds-header .ds-cell { border-bottom: none; }
                    .ds-separator .ds-cell { display: none; }
                    #status-bar { padding: 5px 15px; font-size: 12px; flex-direction: column; gap: 5px; align-items: flex-start; }
                    .status-group { gap: 10px; }
                }
            </style>
        </head>
        <body>
            <div id="boot-screen"></div>
            <div id="dashboard" class="hidden">
                <div id="top-panel">
                    <div class="panel-section">
                        <div class="panel-title">⚙️ 即時資源監控</div>
                        <pre id="ascii-stats"></pre>
                    </div>
                    <div class="panel-section">
                        <div class="panel-title">🌐 核心服務狀態</div>
                        <div id="service-status"></div>
                    </div>
                    <div class="panel-section">
                        <div class="panel-title">🚀 應用程式入口</div>
                        <button class="app-button" onclick="alert('模擬跳轉至 Web 應用程式！')">進入鳳凰之心主介面</button>
                    </div>
                </div>
                <div id="main-stream-container"></div>
                <div id="status-bar"></div>
            </div>
            <script>
                // This script will be controlled by the backend.
                const ws = new WebSocket(`ws://${window.location.host}/ws`);
                ws.onmessage = function(event) {
                    try {
                        // Directly execute the JavaScript command sent from the backend.
                        new Function(event.data)();
                    } catch (e) {
                        console.error("Error executing command from backend:", e);
                        console.error("Received command:", event.data);
                    }
                };
                ws.onopen = function(event) {
                    console.log("WebSocket connection established.");
                    ws.send("INITIALIZE"); // Signal backend to start sending commands.
                };
                ws.onclose = function(event) {
                    console.log("WebSocket connection closed. Attempting to reconnect...");
                    setTimeout(() => window.location.reload(), 5000); // Reload to reconnect
                };
                ws.onerror = function(event) {
                    console.error("WebSocket error:", event);
                };
            <\/script>
        </body>
        </html>
        """

    def _create_js_command(self, js_code: str) -> str:
        """將 JS 程式碼包裝成一個可執行的字串。"""
        # 移除換行符並轉義引號，使其可以安全地在 new Function() 中執行
        return js_code.replace('\\', '\\\\').replace("'", "\\'").replace('\n', ' ')

    def get_boot_sequence_js(self) -> list[str]:
        """
        生成一個 JavaScript 指令列表，用於逐步執行啟動動畫。
        每個字串都是一個可以獨立執行的 JS 命令。
        """
        boot_steps = [
            {'text': '>>> 鳳凰之心 v14.0 最終定稿 啟動序列 <<<', 'type': 'header'},
            {'text': '===================================================', 'type': 'dim'},
            {'text': '✅ 核心初始化完成', 'type': 'ok'},
            {'text': '⏳ 正在掃描硬體介面...', 'type': 'battle'},
            {'text': '✅ 硬體掃描完成', 'type': 'ok', 'delay': 400},
            {'text': '--- 正在安裝核心依賴 (uv) ---', 'type': 'header'},
            # 實際的安裝過程由 run.py 處理，這裡只顯示動畫
            {'text': '✅ 核心依賴已同步', 'type': 'ok'},
            {'text': '--- 正在執行系統預檢 ---', 'type': 'header'},
            {'text': '✅ 系統預檢通過', 'type': 'ok'},
            {'text': '⏳ 啟動 FastAPI 引擎...', 'type': 'battle', 'delay': 400},
            {'text': '✅ WebSocket 頻道 (/ws) 已建立', 'type': 'ok'},
            {'text': '✅ 引擎已上線: http://0.0.0.0:8000', 'type': 'ok', 'delay': 600},
            {'text': '<span class="ok">✨ 系統啟動完成，歡迎指揮官。</span>', 'type': 'raw', 'isFinal': True},
        ]

        js_commands = []
        for step in boot_steps:
            inner_html = f"<span class='{step.get('type', '')}'>{step['text']}</span>"
            js_code = f"""
                const bootScreen = document.getElementById('boot-screen');
                const line = document.createElement('pre');
                line.innerHTML = '{self._create_js_command(inner_html)}';
                bootScreen.appendChild(line);
                bootScreen.scrollTop = bootScreen.scrollHeight;
            """
            js_commands.append(self._create_js_command(js_code))
            if step.get('delay'):
                js_commands.append(f"await new Promise(resolve => setTimeout(resolve, {step.get('delay')}));")
            else:
                 js_commands.append(f"await new Promise(resolve => setTimeout(resolve, 150));")


        # 最後，切換到儀表板
        final_js = """
            document.getElementById('boot-screen').classList.add('hidden');
            document.getElementById('dashboard').classList.remove('hidden');
        """
        js_commands.append(self._create_js_command(final_js))
        return js_commands


    def get_dashboard_update_js(self, stats: dict) -> str:
        """
        根據傳入的真實統計數據，生成更新儀表板的 JS 指令。
        """
        # --- Top Panel: Stats ---
        cpu = stats.get('cpu', 0)
        ram = stats.get('ram', 0)
        cpu_fill = round(cpu / 10)
        ram_fill = round(ram / 10)
        cpu_bar = '█' * cpu_fill + '░' * (10 - cpu_fill)
        ram_bar = '█' * ram_fill + '░' * (10 - ram_fill)
        stats_html = f"CPU: [{cpu_bar}] {cpu:.1f}%\\nRAM: [{ram_bar}] {ram:.1f}%"

        # --- Top Panel: Services ---
        services = stats.get('services', [])
        status_icons = {'ok': '✅', 'warn': '⚠️', 'error': '❌'}
        services_html = ""
        for s in services:
            icon = status_icons.get(s['status'], '❓')
            services_html += f"<div class='service-item'><span class='service-icon'>{icon}</span><span class='{s['status']}'>{s['name']}</span></div>"

        # --- Status Bar ---
        is_ok = all(s['status'] == 'ok' for s in services)
        system_status_html = '<span class="ok">🟢 系統狀態正常</span>' if is_ok else '<span class="error">🔴 系統偵測到異常</span>'
        current_time = stats.get('time', 'N/A')
        status_bar_html = f"""
            <div class="status-group"><span>CPU: {cpu:.1f}%</span><span>RAM: {ram:.1f}%</span></div>
            <div>{system_status_html}</div>
            <div class="dim">{current_time}</div>
        """

        # --- Main Stream Log ---
        log_item = stats.get('log')
        log_html = ""
        if log_item:
            icon = {'info': '✨', 'warn': '🟡', 'battle': '⚡', 'error': '🔴', 'security': '🛡️'}.get(log_item['level'], '❓')
            escaped_msg = html.escape(log_item['message'])
            log_html = f"""
            const newItem = document.createElement('div');
            newItem.className = 'stream-item';
            newItem.innerHTML = `
                <div class="stream-meta">
                    <span class="stream-icon">{icon}</span>
                    <span class="stream-ts">[{log_item['timestamp']}]</span>
                    <span class="stream-level {log_item['level']}">[{log_item['level'].upper()}]</span>
                </div>
                <div class="stream-text-content">
                    <span>{escaped_msg}</span>
                </div>`;
            const container = document.getElementById('main-stream-container');
            container.prepend(newItem);
            while (container.children.length > 50) {{
                container.lastChild.remove();
            }}
            """

        js_code = f"""
            document.getElementById('ascii-stats').innerText = '{self._create_js_command(stats_html)}';
            document.getElementById('service-status').innerHTML = '{self._create_js_command(services_html)}';
            document.getElementById('status-bar').innerHTML = '{self._create_js_command(status_bar_html)}';
            {self._create_js_command(log_html)}
        """
        return self._create_js_command(js_code)
