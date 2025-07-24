from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def transcriber_root():
    return {"message": "這裡是語音轉錄 (Transcriber) 服務"}
