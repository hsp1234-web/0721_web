# -*- coding: utf-8 -*-
"""
數據源邏輯 (Data Sourcing)

負責所有與外部數據 API 的互動，例如 FinMind, FRED, yfinance 等。
這個模組的目標是提供一個統一、乾淨的介面來獲取各種金融數據。
"""
import os

import pandas as pd
from FinMind.data import DataLoader
from fredapi import Fred

# --- 環境變數與設定 ---
# 建議將 API Keys 存放在環境變數中，而不是寫死在程式碼裡
# 這樣可以提高安全性與彈性
FINMIND_API_TOKEN = os.environ.get("FINMIND_API_TOKEN")
FRED_API_KEY = os.environ.get("FRED_API_KEY")

class FinMindSource:
    """
    對 FinMind API 的封裝。
    """
    def __init__(self, token: str = FINMIND_API_TOKEN):
        if not token:
            raise ValueError("FinMind API token 未設定。請設定 FINMIND_API_TOKEN 環境變數。")
        self.api = DataLoader()
        self.api.login_by_token(api_token=token)

    def get_stock_daily(self, stock_id: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取指定股票的日成交資訊。
        """
        df = self.api.taiwan_stock_daily(
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
        return df

class FredSource:
    """
    對 FRED (Federal Reserve Economic Data) API 的封裝。
    """
    def __init__(self, api_key: str = FRED_API_KEY):
        if not api_key:
            raise ValueError("FRED API key 未設定。請設定 FRED_API_KEY 環境變數。")
        self.fred = Fred(api_key=api_key)

    def get_series(self, series_id: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        獲取指定的經濟數據系列。
        例如，'DGS10' 代表 10 年期美國國債殖利率。
        """
        series_data = self.fred.get_series(series_id, observation_start=start_date, observation_end=end_date)
        return series_data.to_frame(name=series_id)

# --- yfinance 的簡易函式封裝 ---
# yfinance 通常不需要 API Key，使用起來更簡單
try:
    import yfinance as yf

    def get_crypto_daily(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        使用 yfinance 獲取加密貨幣的日成交資訊。
        例如，'BTC-USD' 代表比特幣對美元。
        """
        crypto = yf.Ticker(ticker)
        df = crypto.history(start=start_date, end=end_date)
        return df

except ImportError:
    def get_crypto_daily(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        如果 yfinance 未安裝，則返回一個錯誤訊息。
        """
        raise RuntimeError("yfinance 函式庫未安裝。請將 'yfinance' 加入 requirements.txt。")

# 你可以在這裡新增更多來自不同 client 的數據獲取函式...
