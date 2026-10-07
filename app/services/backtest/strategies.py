"""
内置量化策略信号生成器
包含：双均线趋势、MACD动量、布林带突破、多因子打分轮动
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional


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


class CustomRuleStrategy(BaseStrategy):
    """
    自定义多指标量化组合策略 (Custom Rule Strategy)
    支持用户自由组合均线、量能、RSI、KDJ、通道突破等技术条件
    """
    name = "custom_rule"

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        self.params = params or {}
        # 1. 均线设置
        self.ma_mode = self.params.get("ma_mode", "cross")  # cross | bull | above_long | none
        self.short_window = int(self.params.get("short_window", 5))
        self.long_window = int(self.params.get("long_window", 20))

        # 2. 量能过滤
        self.volume_filter = self.params.get("volume_filter", "none")  # vol_surge | vol_expand | none
        self.vol_multiplier = float(self.params.get("vol_multiplier", 1.5))

        # 3. RSI 过滤
        self.rsi_filter = self.params.get("rsi_filter", "none")  # oversold | rebound | none
        self.rsi_threshold = float(self.params.get("rsi_threshold", 35.0))

        # 4. KDJ 过滤
        self.kdj_filter = self.params.get("kdj_filter", "none")  # golden_cross | low_j | none

        # 5. 突破形态
        self.breakout_filter = self.params.get("breakout_filter", "none")  # new_high | none
        self.breakout_period = int(self.params.get("breakout_period", 20))

        # 6. 多条件逻辑组合: "and" (全部满足) 或 "or" (满足其一)
        self.condition_mode = self.params.get("condition_mode", "and").lower()

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy().sort_values("date").reset_index(drop=True)
        n = len(data)
        data["signal"] = 0

        # 计算指标
        data["ma_short"] = data["close"].rolling(window=self.short_window).mean()
        data["ma_long"] = data["close"].rolling(window=self.long_window).mean()
        data["vol_ma5"] = data["volume"].rolling(window=5).mean()

        # 计算 RSI(14)
        delta = data["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        data["rsi"] = 100 - (100 / (1 + rs))

        # 计算 KDJ(9, 3, 3)
        low_9 = data["low"].rolling(window=9).min()
        high_9 = data["high"].rolling(window=9).max()
        rsv = (data["close"] - low_9) / (high_9 - low_9 + 1e-9) * 100
        data["kdj_k"] = rsv.ewm(com=2, adjust=False).mean()
        data["kdj_d"] = data["kdj_k"].ewm(com=2, adjust=False).mean()
        data["kdj_j"] = 3 * data["kdj_k"] - 2 * data["kdj_d"]

        # 买入信号子条件收集
        buy_conditions: List[pd.Series] = []

        # 1. 均线买入条件
        if self.ma_mode == "cross":
            c_ma = (data["ma_short"] > data["ma_long"]) & (data["ma_short"].shift(1) <= data["ma_long"].shift(1))
            buy_conditions.append(c_ma)
        elif self.ma_mode == "bull":
            c_ma = (data["close"] > data["ma_short"]) & (data["ma_short"] > data["ma_long"])
            buy_conditions.append(c_ma)
        elif self.ma_mode == "above_long":
            c_ma = (data["close"] > data["ma_long"]) & (data["close"].shift(1) <= data["ma_long"].shift(1))
            buy_conditions.append(c_ma)

        # 2. 量能买入条件
        if self.volume_filter == "vol_surge":
            c_vol = data["volume"] >= data["vol_ma5"] * self.vol_multiplier
            buy_conditions.append(c_vol)
        elif self.volume_filter == "vol_expand":
            c_vol = data["volume"] > data["volume"].shift(1)
            buy_conditions.append(c_vol)

        # 3. RSI 买入条件
        if self.rsi_filter == "oversold":
            c_rsi = data["rsi"] <= self.rsi_threshold
            buy_conditions.append(c_rsi)
        elif self.rsi_filter == "rebound":
            c_rsi = (data["rsi"] > self.rsi_threshold) & (data["rsi"].shift(1) <= self.rsi_threshold)
            buy_conditions.append(c_rsi)

        # 4. KDJ 买入条件
        if self.kdj_filter == "golden_cross":
            c_kdj = (data["kdj_k"] > data["kdj_d"]) & (data["kdj_k"].shift(1) <= data["kdj_d"].shift(1)) & (data["kdj_j"] < 50)
            buy_conditions.append(c_kdj)
        elif self.kdj_filter == "low_j":
            c_kdj = data["kdj_j"] < 20
            buy_conditions.append(c_kdj)

        # 5. 突破形态
        if self.breakout_filter == "new_high":
            high_prev = data["high"].shift(1).rolling(window=self.breakout_period).max()
            c_bo = data["close"] >= high_prev
            buy_conditions.append(c_bo)

        # 如果没有开启任何条件，则兜底为双均线金叉
        if not buy_conditions:
            final_buy = (data["ma_short"] > data["ma_long"]) & (data["ma_short"].shift(1) <= data["ma_long"].shift(1))
        else:
            if self.condition_mode == "or":
                final_buy = buy_conditions[0]
                for cond in buy_conditions[1:]:
                    final_buy = final_buy | cond
            else:  # 默认 and
                final_buy = buy_conditions[0]
                for cond in buy_conditions[1:]:
                    final_buy = final_buy & cond

        # 卖出条件 (MA死叉或收盘价跌破长均线)
        final_sell = (data["ma_short"] < data["ma_long"]) & (data["ma_short"].shift(1) >= data["ma_long"].shift(1))

        data.loc[final_buy, "signal"] = 1
        data.loc[final_sell, "signal"] = -1
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
    elif name in ("custom", "custom_rule", "user_defined"):
        return CustomRuleStrategy(params=params)
    else:
        # 默认双均线
        return DualMAStrategy(short_window=5, long_window=20)
