# -*- coding: utf-8 -*-
"""
分析與策略邏輯 (Analysis & Strategy)

負責執行核心的金融分析，例如回測、壓力指數計算、遺傳演算法等。
"""
import pandas as pd

from . import data_sourcing, factor_engineering


def run_simple_backtest(stock_id: str, start_date: str, end_date: str) -> dict:
    """
    執行一個簡單的移動平均線交叉策略回測。

    策略：
    - 當 10 日均線 (MA10) 向上穿越 30 日均線 (MA30) 時，買入。
    - 當 10 日均線 (MA10) 向下穿越 30 日均線 (MA30) 時，賣出。

    :param stock_id: 要回測的股票 ID (e.g., '2330')。
    :param start_date: 回測開始日期 (e.g., '2023-01-01')。
    :param end_date: 回測結束日期 (e.g., '2024-01-01')。
    :return: 一個包含回測結果的字典。
    """
    # 步驟 1: 獲取數據
    # 注意：這裡假設 FinMindSource 已被正確配置 API token
    try:
        finmind_source = data_sourcing.FinMindSource()
        # FinMind 的欄位名稱是 'Close'
        price_df = finmind_source.get_stock_daily(stock_id, start_date, end_date)
        # 為了統一，我們將欄位名改為小寫
        price_df.rename(columns={'Close': 'close'}, inplace=True)
        price_df['date'] = pd.to_datetime(price_df['date'])
        price_df.set_index('date', inplace=True)

    except Exception as e:
        return {"error": f"數據獲取失敗: {e}"}

    # 步驟 2: 計算因子
    price_df = factor_engineering.calculate_moving_average(price_df, window=10, price_col='close')
    price_df = factor_engineering.calculate_moving_average(price_df, window=30, price_col='close')
    price_df.dropna(inplace=True) # 刪除包含 NaN 的行，因為移動平均線初期沒有值

    # 步驟 3: 生成交易信號
    # 當 MA10 > MA30 時，我們希望持有倉位 (信號為 1)
    price_df['signal'] = 0
    price_df.loc[price_df['MA_10'] > price_df['MA_30'], 'signal'] = 1

    # 計算信號的變化，以確定交易點
    # 當信號從 0 變為 1 時，是買入點 (positions = 1)
    # 當信號從 1 變為 0 時，是賣出點 (positions = -1)
    price_df['positions'] = price_df['signal'].diff()

    # 步驟 4: 計算投資組合表現
    initial_capital = 100000.0
    positions = pd.DataFrame(index=price_df.index).fillna(0.0)

    # 在買入點，用全部資金買入股票
    positions[stock_id] = price_df['signal'] * initial_capital / price_df['close']

    # 計算投資組合的每日市值
    portfolio = positions.multiply(price_df['close'], axis=0)

    # 計算現金部分
    pos_diff = positions.diff()
    portfolio['cash'] = initial_capital - (pos_diff.multiply(price_df['close'], axis=0)).sum(axis=1).cumsum()

    # 總市值
    portfolio['total'] = portfolio['cash'] + portfolio[stock_id]
    portfolio['returns'] = portfolio['total'].pct_change()

    # 步驟 5: 返回結果
    final_value = portfolio['total'].iloc[-1]
    total_return = (final_value / initial_capital) - 1

    # 找到交易日
    trades = price_df[price_df['positions'] != 0]

    return {
        "stock_id": stock_id,
        "start_date": start_date,
        "end_date": end_date,
        "initial_capital": initial_capital,
        "final_value": final_value,
        "total_return_pct": total_return * 100,
        "trade_count": len(trades),
        "buy_signals": trades[trades['positions'] == 1].index.strftime('%Y-%m-%d').tolist(),
        "sell_signals": trades[trades['positions'] == -1].index.strftime('%Y-%m-%d').tolist(),
    }
