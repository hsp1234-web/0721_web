# integrated_platform/src/config.py
import os
from pathlib import Path

# --- 專案根目錄 ---
# 使得所有路徑配置都基於專案的實際位置，增強可移植性
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# --- 應用程式日誌與檔案路徑 ---
# 從環境變數讀取，若無則提供預設值
# 這允許在 Colab 或其他部署環境中透過設定環境變數來靈活調整
LOG_DB_PATH = os.getenv("LOG_DB_PATH", str(PROJECT_ROOT / "logs.sqlite"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", str(PROJECT_ROOT / "uploads"))

# --- FastAPI 服務配置 ---
UVICORN_PORT = int(os.getenv("UVICORN_PORT", 8000))
HEALTH_CHECK_ENDPOINT = os.getenv("HEALTH_CHECK_ENDPOINT", "/health")

# --- 鳳凰專案 - 語音轉寫模型配置 ---
# 預設使用 'small' 模型，可根據需求調整為 'base', 'medium', 'large' 等
WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL_NAME", "small")

# --- 普羅米修斯之火 - 金融數據配置 ---
FACTORS_DB_PATH = os.getenv("FACTORS_DB_PATH", str(PROJECT_ROOT / "factors.duckdb"))
