"""
技术面与筹码结构特征量化提取 (Technical & Chip Factors)
纯数学向量/数值计算，无任何 I/O 依赖
"""

from typing import Dict, Any, Optional, List


def is_ma_bullish(
    ma5: Optional[float],
    ma10: Optional[float],
    ma20: Optional[float],
    ma60: Optional[float] = None
) -> bool:
    """
    判断均线是否处于标准多头排列
    """
    if not (ma5 and ma10 and ma20 and ma5 > 0 and ma10 > 0 and ma20 > 0):
        return False
    if ma60 and ma60 > 0:
        return ma5 >= ma10 >= ma20 >= ma60
    return ma5 >= ma10 >= ma20


def is_above_ma20(current_price: float, ma20: Optional[float]) -> bool:
    """
    判断收盘价是否站上 20 日生命线
    """
    if not (current_price > 0 and ma20 and ma20 > 0):
        return False
    return current_price >= ma20


def check_new_high_breakout(
    current_price: float,
    high_history: List[float],
    lookback_days: int = 20
) -> bool:
    """
    判断现价是否突破近 N 日最高价 (创新高突破战法)
    """
    if current_price <= 0 or not high_history:
        return False
    recent = high_history[-lookback_days:] if len(high_history) >= lookback_days else high_history
    if not recent:
        return False
    # 现价高于过去 N-1 天的历史最高点
    max_prev = max(recent[:-1]) if len(recent) > 1 else recent[0]
    return current_price >= max_prev


def evaluate_chip_structure(
    profit_ratio: Optional[float],
    concentration_70: Optional[float] = None,
    concentration_90: Optional[float] = None,
    current_price: float = 0.0,
    support_price: Optional[float] = None
) -> Dict[str, Any]:
    """
    评价 CYQ 筹码分布结构特征：
    - 获利盘比例
    - 筹码单峰密集度 (集中度 < 10% 为高密集)
    - 支撑位临近度 (距离主力密集峰 <= 3%)
    """
    pr = float(profit_ratio) if profit_ratio is not None else 50.0
    c90 = float(concentration_90) if concentration_90 is not None else (float(concentration_70 or 10.0) * 1.3)
    
    is_concentrated = c90 <= 12.0
    is_profit_dominant = pr >= 70.0
    is_deep_oversold = pr <= 10.0

    near_support = False
    if current_price > 0 and support_price and support_price > 0:
        diff_pct = abs(current_price - support_price) / current_price
        near_support = (diff_pct <= 0.035 and current_price >= support_price * 0.99)

    return {
        "profit_ratio": round(pr, 1),
        "concentration_90": round(c90, 1),
        "is_concentrated": is_concentrated,
        "is_profit_dominant": is_profit_dominant,
        "is_deep_oversold": is_deep_oversold,
        "near_support": near_support
    }
