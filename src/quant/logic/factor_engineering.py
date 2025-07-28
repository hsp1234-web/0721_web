# -*- coding: utf-8 -*-
"""
因子工程邏輯 (Factor Engineering)

負責計算各種技術指標和因子。
這些函式通常接收一個 pandas DataFrame，並返回一個添加了新因子欄位的 DataFrame。
"""
import pandas as pd


def calculate_moving_average(
    df: pd.DataFrame, window: int, price_col: str = 'close'
) -> pd.DataFrame:
    """
    計算移動平均線 (Moving Average)。

    :param df: 包含價格數據的 DataFrame，需要有 `price_col` 欄位。
    :param window: 移動平均的窗口大小。
    :param price_col: 用於計算的價格欄位名稱，預設為 'close'。
    :return: 增加了 'MA_{window}' 欄位的 DataFrame。
    """
    if price_col not in df.columns:
        raise ValueError(f"錯誤: DataFrame 中找不到價格欄位 '{price_col}'。")

    df[f'MA_{window}'] = df[price_col].rolling(window=window).mean()
    return df

def calculate_rsi(
    df: pd.DataFrame, window: int = 14, price_col: str = 'close'
) -> pd.DataFrame:
    """
    計算相對強弱指數 (RSI)。

    :param df: 包含價格數據的 DataFrame。
    :param window: RSI 的窗口大小，預設為 14。
    :param price_col: 用於計算的價格欄位名稱，預設為 'close'。
    :return: 增加了 'RSI_{window}' 欄位的 DataFrame。
    """
    if price_col not in df.columns:
        raise ValueError(f"錯誤: DataFrame 中找不到價格欄位 '{price_col}'。")

    delta = df[price_col].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    df[f'RSI_{window}'] = rsi
    return df

def add_all_factors(df: pd.DataFrame, price_col: str = 'close') -> pd.DataFrame:
    """
    一個方便的函式，用於一次性為 DataFrame 添加所有定義好的因子。
    """
    df = calculate_moving_average(df, window=10, price_col=price_col)
    df = calculate_moving_average(df, window=30, price_col=price_col)
    df = calculate_rsi(df, window=14, price_col=price_col)

    return df

# 你可以在這裡繼續添加更多的因子計算函式，例如 MACD, Bollinger Bands 等。
