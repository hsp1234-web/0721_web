# -*- coding: utf-8 -*-
"""
核心工具：資源監控器 (Resource Monitor)
"""
import shutil
from typing import Dict, Any

def get_system_resources() -> Dict[str, Any]:
    """
    獲取當前系統的記憶體和磁碟使用情況。

    Returns:
        一個包含記憶體和磁碟資訊的字典。
    """
    import psutil
    memory = psutil.virtual_memory()
    disk_usage = shutil.disk_usage("/")

    return {
        "memory": {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_percent": memory.percent,
        },
        "disk": {
            "total_gb": round(disk_usage.total / (1024**3), 2),
            "used_gb": round(disk_usage.used / (1024**3), 2),
            "free_gb": round(disk_usage.free / (1024**3), 2),
            "used_percent": round((disk_usage.used / disk_usage.total) * 100, 2),
            "free_mb": round(disk_usage.free / (1024**2), 2),
        }
    }

def load_resource_settings(config_path: str = "config/resource_settings.yml") -> Dict[str, Any]:
    """
    從指定的 YAML 檔案載入資源監控的設定。

    Args:
        config_path: 設定檔的路徑。

    Returns:
        一個包含設定參數的字典。
    """
    import yaml
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"警告：找不到設定檔 {config_path}，將使用預設值。")
        return {
            "resource_monitoring": {
                "memory_usage_threshold_percent": 75.0,
                "min_disk_space_mb": 512,
            }
        }

def is_resource_sufficient(settings: Dict[str, Any]) -> tuple[bool, str]:
    """
    根據提供的設定，檢查系統資源是否充足。

    Args:
        settings: 從設定檔載入的參數字典。

    Returns:
        一個元組 (is_sufficient, message)，
        如果資源充足，is_sufficient 為 True，否則為 False，
        message 包含檢查的詳細資訊。
    """
    resources = get_system_resources()
    thresholds = settings.get("resource_monitoring", {})

    mem_threshold = thresholds.get("memory_usage_threshold_percent", 75.0)
    disk_threshold_mb = thresholds.get("min_disk_space_mb", 512)

    mem_ok = resources["memory"]["used_percent"] < mem_threshold
    disk_ok = resources["disk"]["free_mb"] > disk_threshold_mb

    # 產生詳細的訊息
    mem_percent = resources["memory"]["used_percent"]
    disk_free_mb = resources["disk"]["free_mb"]
    message = (
        f"Memory: {mem_percent:.1f}% < {mem_threshold:.1f}% -> {'OK' if mem_ok else 'FAIL'}. "
        f"Disk: {disk_free_mb:.0f}MB > {disk_threshold_mb}MB -> {'OK' if disk_ok else 'FAIL'}."
    )

    return mem_ok and disk_ok, message

if __name__ == "__main__":
    # 這個區塊允許我們獨立執行此檔案進行快速測試
    print("--- 執行資源監控器獨立測試 ---")

    # 測試載入設定
    config = load_resource_settings()
    print("\n載入的設定:")
    print(yaml.dump(config, indent=2))

    # 測試獲取資源
    current_resources = get_system_resources()
    print("\n當前系統資源:")
    print(yaml.dump(current_resources, indent=2))

    # 測試資源檢查
    is_ok, check_message = is_resource_sufficient(config)
    print("\n資源檢查結果:")
    print(f"  - 狀態: {'充足' if is_ok else '不足'}")
    print(f"  - 詳細資訊: {check_message}")
    print("\n--- 測試完成 ---")
