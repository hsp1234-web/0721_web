import asyncio
import websockets
import json

async def listen_logs():
    uri = "ws://127.0.0.1:8000/ws/logs"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"--- 連接到 {uri} ---")
            # 連線後，伺服器應該會馬上開始推送日誌
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    if data.get("event_type") == "LOG_MESSAGE":
                        log = data.get("payload", {})
                        print(f"[收到日誌] Level: {log.get('level')}, Msg: {log.get('message')}")
                    else:
                        print(f"[收到未知訊息]: {data}")
                except asyncio.TimeoutError:
                    print("--- 5秒內未收到新日誌，客戶端自動關閉 ---")
                    break
                except websockets.exceptions.ConnectionClosed:
                    print("--- 連線已由伺服器關閉 ---")
                    break
    except Exception as e:
        print(f"連線失敗: {e}")

if __name__ == "__main__":
    asyncio.run(listen_logs())
