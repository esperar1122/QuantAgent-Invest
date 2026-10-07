"""
内置量化策略信号生成器
包含：双均线趋势、MACD动量、布林带突破、多因子打分轮动
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List


class BaseStrategy:
    """策略基类"""
    name = "BaseStrategy"

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        根据历史行情生成买卖信号
        输入 DataFrame 必须包含: ['date', 'open', 'high', 'low', 'close', 'volume']
        输出包含 'signal': 1 (买入), -1 (卖出), 0 (持有/无动作)
        """
        raise NotImplementedError


class DualMAStrategy(BaseStrategy):
    """双均线金叉死叉策略 (Dual Moving Average)"""
    name = "dual_ma"

    def __init__(self, short_window: int = 5, long_window: int = 20):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy().sort_values("date").reset_index(drop=True)
        data[f"ma_short"] = data["close"].rolling(window=self.short_window).mean()
        data[f"ma_long"] = data["close"].rolling(window=self.long_window).mean()

        data["signal"] = 0
        # 短均线上穿长均线为金叉买入
        cross_up = (data["ma_short"] > data["ma_long"]) & (data["ma_short"].shift(1) <= data["ma_long"].shift(1))
        # 短均线下穿长均线为死叉卖出
        cross_down = (data["ma_short"] < data["ma_long"]) & (data["ma_short"].shift(1) >= data["ma_long"].shift(1))

        data.loc[cross_up, "signal"] = 1
        data.loc[cross_down, "signal"] = -1
        return data


class MACDStrategy(BaseStrategy):
    """MACD 动量金叉策略"""
    name = "macd"

    def __init__(self, fast: int = 12, slow: int = 26, signal_span: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal_span = signal_span

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy().sort_values("date").reset_index(drop=True)
        ema_fast = data["close"].ewm(span=self.fast, adjust=False).mean()
        ema_slow = data["close"].ewm(span=self.slow, adjust=False).mean()
        data["dif"] = ema_fast - ema_slow
        data["dea"] = data["dif"].ewm(span=self.signal_span, adjust=False).mean()
        data["macd"] = (data["dif"] - data["dea"]) * 2

        data["signal"] = 0
        gold_cross = (data["dif"] > data["dea"]) & (data["dif"].shift(1) <= data["dea"].shift(1))
        death_cross = (data["dif"] < data["dea"]) & (data["dif"].shift(1) >= data["dea"].shift(1))

        data.loc[gold_cross, "signal"] = 1
        data.loc[death_cross, "signal"] = -1
        return data


class BollingerBandsStrategy(BaseStrategy):
    """布林带均值回归策略"""
    name = "bollinger"

    def __init__(self, window: int = 20, num_std: float = 2.0):
        self.window = window
        self.num_std = num_std

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy().sort_values("date").reset_index(drop=True)
        ma = data["close"].rolling(window=self.window).mean()
        std = data["close"].rolling(window=self.window).std()
        data["upper_band"] = ma + self.num_std * std
        data["lower_band"] = ma - self.num_std * std

        data["signal"] = 0
        # 价格向上突破下轨视为超跌反弹买入
        buy_cond = (data["close"] > data["lower_band"]) & (data["close"].shift(1) <= data["lower_band"].shift(1))
        # 价格触及上轨视为超买止盈卖出
        sell_cond = (data["close"] >= data["upper_band"])

        data.loc[buy_cond, "signal"] = 1
        data.loc[sell_cond, "signal"] = -1
        return data


def get_strategy_by_name(name: str, params: Dict[str, Any] = None) -> BaseStrategy:
    params = params or {}
    name = name.lower()
    if name in ("dual_ma", "ma", "moving_average"):
        return DualMAStrategy(
            short_window=int(params.get("short_window", 5)),
            long_window=int(params.get("long_window", 20))
        )
    elif name in ("macd", "macd_trend"):
        return MACDStrategy(
            fast=int(params.get("fast", 12)),
            slow=int(params.get("slow", 26)),
            signal_span=int(params.get("signal_span", 9))
        )
    elif name in ("bollinger", "bollinger_bands"):
        return BollingerBandsStrategy(
            window=int(params.get("window", 20)),
            num_std=float(params.get("num_std", 2.0))
        )
    else:
        # 默认双均线
        return DualMAStrategy(short_window=5, long_window=20)
