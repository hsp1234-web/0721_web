# -*- coding: utf-8 -*-
"""
核心工具：埠號管理器 (Port Manager)
"""
import socket
import psutil
import signal
import os
from typing import Optional

def find_available_port(start_port: int = 8000, end_port: int = 9000) -> Optional[int]:
    """
    在指定範圍內尋找一個可用的 TCP 埠號。

    Args:
        start_port: 搜尋的起始埠號。
        end_port: 搜尋的結束埠號。

    Returns:
        一個可用的埠號，如果範圍內沒有可用的埠號則返回 None。
    """
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                # 埠號已被佔用
                continue
    return None

def kill_processes_using_port(port: int):
    """
    找到並終止所有正在使用指定 TCP 埠號的程序。

    Args:
        port: 要清理的埠號。
    """
    if not isinstance(port, int):
        return

    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            for conn in proc.info.get('connections', []):
                if conn.laddr.port == port:
                    print(f"找到正在使用埠號 {port} 的程序: PID={proc.pid}, 名稱={proc.info['name']}。正在嘗試終止...")
                    try:
                        # 使用 SIGTERM 嘗試優雅關閉
                        os.kill(proc.pid, signal.SIGTERM)
                        print(f"  - 已向 PID {proc.pid} 發送 SIGTERM 信號。")
                    except ProcessLookupError:
                        print(f"  - 警告：程序 PID {proc.pid} 在嘗試終止時已不存在。")
                    except Exception as e:
                        print(f"  - 錯誤：終止程序 PID {proc.pid} 時發生錯誤: {e}。嘗試使用 SIGKILL...")
                        try:
                            # 如果優雅關閉失敗，強制終止
                            os.kill(proc.pid, signal.SIGKILL)
                            print(f"  - 已向 PID {proc.pid} 發送 SIGKILL 信號。")
                        except Exception as kill_e:
                            print(f"  - 錯誤：使用 SIGKILL 終止程序 PID {proc.pid} 失敗: {kill_e}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # 忽略無法訪問或已經結束的程序
            pass
