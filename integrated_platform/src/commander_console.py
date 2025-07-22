# src/commander_console.py
# -*- coding: utf-8 -*-
"""
鳳凰轉錄儀 - 後勤與特種作戰中心 (Commander Console)
本檔案是所有線下任務、數據處理、系統維護的唯一入口。
"""
import typer

# 初始化 Typer 應用程式
app = typer.Typer(help="鳳凰轉錄儀 - 指揮官控制台")

@app.command()
def hello(name: str = typer.Argument("指揮官", help="要問候對象的姓名。")):
    """
    一個用於驗證控制台是否正常運作的簡單問候指令。
    """
    print(f"你好, {name}！控制台已準備就緒。")

if __name__ == "__main__":
    app()
