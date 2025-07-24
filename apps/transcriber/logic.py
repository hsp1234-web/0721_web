import time
import os
from fastapi import UploadFile

# --- 懶加載 (Lazy Loading) 的核心 ---

# 這是一個全域變數，用於快取（cache）"重型"資源，例如 AI 模型。
# 它的初始值是 None。當第一次有請求進來時，它會被實例化。
# 後續所有請求都會直接使用這個已經加載好的實例。
AI_MODEL = None

def _load_model():
    """
    一個模擬的、耗時的模型加載函數。
    在真實應用中，這裡會是 `torch.load()` 或類似的操作。
    """
    print("[Transcriber Logic] 開始加載大型 AI 模型... (這會需要幾秒鐘)")
    # 模擬 IO 或計算密集型操作
    time.sleep(5)
    model_data = {"version": "1.0", "load_time": time.time()}
    print(f"[Transcriber Logic] 模型加載完畢！資料: {model_data}")
    return model_data

def get_model():
    """
    獲取模型的接口。這是實現懶加載的關鍵。
    """
    global AI_MODEL

    # 這是 "Double-Checked Locking" 模式的一個簡化版，適用於 Python 的 GIL。
    if AI_MODEL is None:
        # 首次調用時，執行加載
        AI_MODEL = _load_model()

    return AI_MODEL

# --- 業務邏輯函數 ---

def transcribe_audio(file: UploadFile):
    """
    處理音訊轉錄的核心業務邏輯。
    """
    # 1. 獲取（可能需要加載）模型
    model = get_model()

    # 2. 模擬使用模型進行轉錄
    print(f"[Transcriber Logic] 正在使用模型 {model['version']} 處理檔案: {file.filename}")
    # 模擬轉錄耗時
    time.sleep(1)

    # 3. 讀取檔案內容並產生結果
    # 為了安全起見，在真實世界中你需要對檔案大小和內容進行更嚴格的檢查
    file_size = file.size
    content = file.file.read(100) # 只讀取前 100 字節作為範例

    transcription_result = f"檔案 '{file.filename}' (大小: {file_size} 字節) 的模擬轉錄結果。內容開頭: {content[:50]}..."

    print("[Transcriber Logic] 處理完畢。")

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "transcription": transcription_result,
        "model_used": model
    }
