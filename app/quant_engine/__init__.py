"""
统一量化计算核心引擎 (Quant Core Engine)
Single Source of Truth (SSOT) 权威量化算法包
"""

from .profiles import get_board_profile, BoardProfile
from .market_regime import MarketRegime, MarketRegimeResult, detect_market_regime
from .risk_reward import calc_net_risk_reward_ratio, calc_dynamic_atr
from .technical_factors import is_ma_bullish, is_above_ma20, evaluate_chip_structure, check_new_high_breakout
from .capital_factors import evaluate_northbound_holding, evaluate_main_money_flow
from .negative_filter import check_negative_filters
from .engine import QuantCoreEngine

__all__ = [
    "get_board_profile",
    "BoardProfile",
    "MarketRegime",
    "MarketRegimeResult",
    "detect_market_regime",
    "calc_net_risk_reward_ratio",
    "calc_dynamic_atr",
    "is_ma_bullish",
    "is_above_ma20",
    "evaluate_chip_structure",
    "check_new_high_breakout",
    "evaluate_northbound_holding",
    "evaluate_main_money_flow",
    "check_negative_filters",
    "QuantCoreEngine",
]
