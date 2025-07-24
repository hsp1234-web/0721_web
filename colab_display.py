from IPython.display import display, HTML
import time

def display_system_status(status_data: dict):
    """
    在 Colab 中渲染一個漂亮的 HTML 狀態介面。

    Args:
        status_data (dict): 包含系統狀態資訊的字典。
                           預期鍵值: 'status', 'pid', 'start_time', 'message'
    """
    status = status_data.get('status', 'UNKNOWN')
    pid = status_data.get('pid', 'N/A')
    start_time = status_data.get('start_time', 'N/A')
    message = status_data.get('message', '')

    if status == 'RUNNING':
        color = '#28a745' # 綠色
        icon = '🚀'
    elif status == 'STARTING':
        color = '#ffc107' # 黃色
        icon = '⏳'
    else:
        color = '#dc3545' # 紅色
        icon = '❌'

    html_content = f"""
    <div style="border: 2px solid {color}; border-radius: 10px; padding: 15px; font-family: sans-serif; margin: 10px;">
        <h2 style="margin-top: 0; color: {color};">{icon} 後端系統狀態</h2>
        <p><strong>狀態:</strong> <span style="font-weight: bold; color: {color};">{status}</span></p>
        <p><strong>主進程 PID:</strong> {pid}</p>
        <p><strong>啟動時間:</strong> {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time)) if isinstance(start_time, float) else 'N/A'}</p>
        <p><strong>訊息:</strong> {message}</p>
    </div>
    """

    # 使用 display 來渲染 HTML
    display(HTML(html_content))

def display_error(message: str):
    """顯示一個錯誤訊息"""
    display_system_status({
        'status': 'ERROR',
        'message': message,
    })

def display_log_message(message: str):
    """以簡單的格式顯示日誌訊息"""
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

if __name__ == '__main__':
    # --- 用於在本機環境測試顯示效果 ---
    print("--- 測試顯示效果 ---")
    print("\n1. 啟動中狀態:")
    display_system_status({
        'status': 'STARTING',
        'pid': 12345,
        'start_time': time.time(),
        'message': '正在初始化核心進程...'
    })

    time.sleep(1)

    print("\n2. 運行中狀態:")
    display_system_status({
        'status': 'RUNNING',
        'pid': 12345,
        'start_time': time.time() - 5,
        'message': '所有服務已上線，系統正常運行。'
    })

    print("\n3. 錯誤狀態:")
    display_error("無法綁定埠號 8000，可能已被佔用。")
