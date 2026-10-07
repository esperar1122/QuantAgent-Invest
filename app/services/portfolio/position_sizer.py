"""
量化头寸规模与仓位管理算法 (Position Sizing Models)
包含：等权重、逆波动率(风险平价)、ATR风险预算、半凯利公式
"""

import math
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd


class PositionSizer:
    """仓位管理计算器"""

    @staticmethod
    def equal_weight(
        symbols: List[str],
        total_capital: float,
        cash_reserve_ratio: float = 0.05
    ) -> Dict[str, Dict[str, Any]]:
        """
        等权重分配模型 (Equal Weight)
        """
        if not symbols:
            return {}
        investable_capital = total_capital * (1 - cash_reserve_ratio)
        weight_per_stock = round(1.0 / len(symbols), 4)
        target_capital_per_stock = round(investable_capital / len(symbols), 2)

        results = {}
        for sym in symbols:
            results[sym] = {
                "weight": weight_per_stock,
                "target_amount": target_capital_per_stock,
                "strategy": "equal_weight",
            }
        return results

    @staticmethod
    def inverse_volatility(
        symbols_volatility: Dict[str, float],
        total_capital: float,
        max_single_weight: float = 0.30,
        cash_reserve_ratio: float = 0.05
    ) -> Dict[str, Dict[str, Any]]:
        """
        波动率倒数加权 (Inverse Volatility / 简易风险平价)
        标的波动越大，配置仓位越小；波动越小，配置仓位越高
        Args:
            symbols_volatility: { "600519": 0.18, "000001": 0.25 } 年化波动率
            total_capital: 账户总资金
            max_single_weight: 单股最大持仓上限（默认30%）
            cash_reserve_ratio: 现金保留缓冲（默认5%）
        """
        if not symbols_volatility:
            return {}

        investable = total_capital * (1 - cash_reserve_ratio)
        # 计算 1 / vol
        inv_vols = {}
        for sym, vol in symbols_volatility.items():
            safe_vol = max(vol, 0.05)  # 避免过小波动率产生无穷大权重
            inv_vols[sym] = 1.0 / safe_vol

        sum_inv = sum(inv_vols.values())
        raw_weights = {sym: (v / sum_inv) for sym, v in inv_vols.items()}

        # 施加单股上限约束并归一化
        constrained_weights = {}
        excess = 0.0
        capped_symbols = set()

        for sym, w in raw_weights.items():
            if w > max_single_weight:
                constrained_weights[sym] = max_single_weight
                excess += (w - max_single_weight)
                capped_symbols.add(sym)
            else:
                constrained_weights[sym] = w

        # 将超额权重平摊给未触及上限的股票
        uncapped = [s for s in symbols_volatility if s not in capped_symbols]
        if uncapped and excess > 0:
            uncapped_sum = sum(constrained_weights[s] for s in uncapped)
            for s in uncapped:
                if uncapped_sum > 0:
                    constrained_weights[s] += excess * (constrained_weights[s] / uncapped_sum)

        results = {}
        for sym, w in constrained_weights.items():
            alloc = round(investable * w, 2)
            results[sym] = {
                "weight": round(w, 4),
                "target_amount": alloc,
                "annual_volatility": symbols_volatility[sym],
                "strategy": "inverse_volatility",
            }
        return results

    @staticmethod
    def atr_risk_budget(
        total_capital: float,
        price: float,
        atr_value: float,
        risk_ratio: float = 0.01,
        stop_loss_atr_multiplier: float = 2.0
    ) -> Dict[str, Any]:
        """
        ATR 真实波幅风险预算模型 (海龟交易头寸模型)
        根据单笔交易最大可承受亏损金额与标的波动区间，反推安全买入手数与止损价位
        Args:
            total_capital: 账户总资产
            price: 标的当前市价
            atr_value: 14日ATR均幅
            risk_ratio: 单笔最大容忍亏损比例（默认 1% 即 0.01）
            stop_loss_atr_multiplier: 止损距离倍数（默认 2.0 倍 ATR）
        """
        if price <= 0 or atr_value <= 0:
            return {
                "shares": 0,
                "hands": 0,
                "target_amount": 0.0,
                "weight": 0.0,
                "stop_loss_price": price,
                "risk_amount": 0.0,
            }

        max_risk_amount = total_capital * risk_ratio
        stop_distance = stop_loss_atr_multiplier * atr_value
        stop_loss_price = max(0.01, round(price - stop_distance, 2))

        # 理论应买股数 = 风险预算金额 / 单股止损距离
        raw_shares = max_risk_amount / stop_distance
        # A 股买入整手化 (1手 = 100股)
        shares = int(raw_shares // 100) * 100
        hands = shares // 100

        target_amount = round(shares * price, 2)
        weight = round(target_amount / total_capital, 4) if total_capital > 0 else 0.0

        return {
            "price": price,
            "atr": round(atr_value, 3),
            "max_risk_amount": round(max_risk_amount, 2),
            "stop_distance": round(stop_distance, 2),
            "stop_loss_price": stop_loss_price,
            "shares": shares,
            "hands": hands,
            "target_amount": target_amount,
            "weight": weight,
            "weight_pct": round(weight * 100, 2),
            "strategy": "atr_risk_budget",
        }

    @staticmethod
    def fractional_kelly(
        total_capital: float,
        win_rate: float,
        profit_loss_ratio: float,
        kelly_fraction: float = 0.5,
        max_position_limit: float = 0.30
    ) -> Dict[str, Any]:
        """
        半凯利公式模型 (Fractional Kelly Criterion)
        Args:
            total_capital: 账户总资产
            win_rate: 历史策略胜率 (0.0 ~ 1.0)
            profit_loss_ratio: 盈亏比 (平均盈利 / 平均亏损)
            kelly_fraction: 凯利安全比例（默认0.5，半凯利更平稳防黑天鹅）
            max_position_limit: 单次最高仓位上限 (默认30%)
        """
        if profit_loss_ratio <= 0 or win_rate <= 0:
            return {"recommended_weight": 0.0, "recommended_amount": 0.0}

        p = win_rate
        q = 1.0 - p
        b = profit_loss_ratio

        # 全凯利: f* = (p * (b + 1) - 1) / b = p - q / b
        full_kelly = p - (q / b)
        if full_kelly <= 0:
            # 数学期望为负，不应当建仓
            return {
                "raw_kelly": round(full_kelly, 4),
                "recommended_weight": 0.0,
                "recommended_amount": 0.0,
                "explanation": "策略期望收益为负，凯利公式建议不建仓"
            }

        fractional = full_kelly * kelly_fraction
        safe_weight = min(fractional, max_position_limit)
        safe_amount = round(total_capital * safe_weight, 2)

        return {
            "win_rate": round(win_rate, 4),
            "profit_loss_ratio": round(profit_loss_ratio, 2),
            "full_kelly_weight": round(full_kelly, 4),
            "recommended_weight": round(safe_weight, 4),
            "recommended_weight_pct": round(safe_weight * 100, 2),
            "recommended_amount": safe_amount,
            "strategy": "fractional_kelly",
        }
