# -*- coding: utf-8 -*-
"""
共享狀態模組

使用 multiprocessing.Manager 來創建一個跨程序共享的狀態字典。
- launch.py 作為狀態的生產者 (Producer)，更新狀態字典。
- apps/dashboard_api/main.py 作為狀態的消費者 (Consumer)，讀取狀態字典。
"""
from multiprocessing import Manager

# 初始化一個 Manager
# 注意：這個 manager 需要在主啟動腳本 (colab_runner.py) 中被創建和傳遞
# 我們在這裡只定義一個創建函式
def get_shared_state_manager():
    return Manager()

# 全域變數，用於在單一程序內共享（備用）
_state = {}

def update_state(key, value):
    _state[key] = value

def get_state():
    return _state.copy()
