import html

class PresentationManager:
    """
    後端驅動前端的核心類別。
    負責生成所有用於渲染和更新前端 UI 的 JavaScript 指令。
    注意：在新架構下，此類別的職責已大幅縮減。
    它不再管理整個 HTML 頁面或啟動序列。
    """

    def _create_js_command(self, js_code: str) -> str:
        """將 JS 程式碼包裝成一個可執行的字串。"""
        # 移除換行符並轉義引號，使其可以安全地在 new Function() 中執行
        return js_code.replace('\\', '\\\\').replace("'", "\\'").replace('\n', ' ')

    def get_dashboard_update_js(self, stats: dict) -> str:
        """
        根據傳入的真實統計數據，生成更新儀表板的 JS 指令。
        """
        js_updates = []

        # --- Top Panel: Stats (僅在提供時更新) ---
        if 'cpu' in stats and 'ram' in stats:
            cpu = stats.get('cpu', 0)
            ram = stats.get('ram', 0)
            cpu_fill = round(cpu / 10)
            ram_fill = round(ram / 10)
            cpu_bar = '█' * cpu_fill + '░' * (10 - cpu_fill)
            ram_bar = '█' * ram_fill + '░' * (10 - ram_fill)
            stats_html = f"CPU: [{cpu_bar}] {cpu:.1f}%\\nRAM: [{ram_bar}] {ram:.1f}%"
            js_updates.append(f"document.getElementById('ascii-stats').innerText = '{self._create_js_command(stats_html)}';")

        # --- Top Panel: Services (僅在提供時更新) ---
        if 'services' in stats:
            services = stats.get('services', [])
            status_icons = {'ok': '✅', 'warn': '⚠️', 'error': '❌'}
            services_html = ""
            for s in services:
                icon = status_icons.get(s['status'], '❓')
                services_html += f"<div class='service-item'><span class='service-icon'>{icon}</span><span class='{s['status']}'>{s['name']}</span></div>"
            js_updates.append(f"document.getElementById('service-status').innerHTML = '{self._create_js_command(services_html)}';")

        # --- Status Bar (合併更新) ---
        if 'cpu' in stats or 'services' in stats:
            is_ok = all(s['status'] == 'ok' for s in stats.get('services', []))
            system_status_html = '<span class="ok">🟢 系統狀態正常</span>' if is_ok else '<span class="error">🔴 系統偵測到異常</span>'
            current_time = stats.get('time', 'N/A')
            status_bar_html = f"""
                <div class="status-group"><span>CPU: {stats.get('cpu', 0):.1f}%</span><span>RAM: {stats.get('ram', 0):.1f}%</span></div>
                <div>{system_status_html}</div>
                <div class="dim">{current_time}</div>
            """
            js_updates.append(f"document.getElementById('status-bar').innerHTML = '{self._create_js_command(status_bar_html)}';")

        # --- Main Stream Log (僅在提供時更新) ---
        if 'log' in stats and stats['log']:
            log_item = stats['log']
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
            if (container) {{
                container.prepend(newItem);
                while (container.children.length > 50) {{
                    container.lastChild.remove();
                }}
            }}
            """
            js_updates.append(log_html)

        return self._create_js_command("\n".join(js_updates))
