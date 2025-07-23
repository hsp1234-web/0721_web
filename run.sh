#!/bin/bash
# 思路框架：此腳本是整個部署流程的起點，必須保持極簡與專注。

# --- 階段一：安裝引導工具 ---
# 作法: 使用 pip 安裝 Poetry 本身以及我們的智慧管理器所依賴的 psutil。
#       ipython 是 colab_run.py 儀表板的前置依賴。
echo "--- 正在安裝核心引導工具 ---"
pip install poetry psutil ipython toml

# --- 階段二：啟動智慧安裝器 ---
# 作法: 執行我們在階段三設計的 poetry_manager.py，
#       讓它接管後續所有複雜的依賴安裝工作。
echo "--- 移交控制權至智慧安裝管理器 ---"
python poetry_manager.py
