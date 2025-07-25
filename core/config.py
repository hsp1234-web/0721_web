from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LOG_DISPLAY_LINES: int = 100
    STATUS_REFRESH_INTERVAL: float = 0.5
    TARGET_FOLDER_NAME: str = "WEB"
    ARCHIVE_FOLDER_NAME: str = "作戰日誌歸檔"
    FASTAPI_PORT: int = 8000

settings = Settings()
