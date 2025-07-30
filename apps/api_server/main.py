from fastapi import FastAPI
import json

app = FastAPI()

# 在記憶體中儲存服務狀態
services_status = {}

@app.get("/")
def read_root():
    return {"message": "API Gateway is running"}

@app.get("/status")
def get_status():
    return services_status

@app.post("/report_status")
async def report_status(service: str, status: str):
    services_status[service] = status
    return {"message": f"Status of {service} updated to {status}"}
