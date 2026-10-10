"""
投资组合优化与调仓指令生成器
根据仓位模型和当前真实/模拟持仓，生成最小交易摩擦的调仓计划
"""

from typing import Dict, Any, List, Optional
from app.services.portfolio.position_sizer import PositionSizer


class PortfolioOptimizer:
    """组合优化与调仓计划管理器"""

    def __init__(
        self,
        rebalance_threshold: float = 0.03,  # 偏离阈值低于3%时不调仓，节省交易手续费
        cash_reserve_ratio: float = 0.05,   # 保持5%现金缓冲
        max_single_weight: float = 0.25,    # 单股持仓上限25%
    ):
        self.rebalance_threshold = rebalance_threshold
        self.cash_reserve_ratio = cash_reserve_ratio
        self.max_single_weight = max_single_weight

    def generate_rebalance_plan(
        self,
        current_cash: float,
        current_holdings: Dict[str, Dict[str, Any]],  # { "600519": {"shares": 200, "price": 1680.0} }
        target_symbols: List[str],
        strategy_type: str = "equal_weight",
        symbols_volatility: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        生成精确到整手（100股）的调仓计划
        """
        # 1. 计算当前总资产与持仓市值
        holdings_market_val = sum(
            h.get("shares", 0) * h.get("price", 0.0) for h in current_holdings.values()
        )
        total_equity = current_cash + holdings_market_val

        if total_equity <= 0:
            return {"error": "总资产必须大于0", "orders": []}

        # 2. 计算目标分配权重
        if strategy_type == "inverse_volatility" and symbols_volatility:
            sizing = PositionSizer.inverse_volatility(
                symbols_volatility=symbols_volatility,
                total_capital=total_equity,
                max_single_weight=self.max_single_weight,
                cash_reserve_ratio=self.cash_reserve_ratio
            )
        else:
            sizing = PositionSizer.equal_weight(
                symbols=target_symbols,
                total_capital=total_equity,
                cash_reserve_ratio=self.cash_reserve_ratio
            )

        # 3. 计算调仓订单列表 (先卖后买，确保有足够现金)
        sell_orders = []
        buy_orders = []

        all_relevant_symbols = set(list(current_holdings.keys()) + target_symbols)

        for sym in all_relevant_symbols:
            curr_pos = current_holdings.get(sym, {})
            curr_shares = int(curr_pos.get("shares", 0))
            price = float(curr_pos.get("price", 0.0))
            if price <= 0:
                continue

            curr_val = curr_shares * price
            curr_weight = curr_val / total_equity if total_equity > 0 else 0.0

            target_info = sizing.get(sym)
            if target_info:
                target_weight = target_info["weight"]
                target_val = target_info["target_amount"]
                target_shares = int((target_val / price) // 100) * 100
            else:
                # 不在目标组合中的股票，全部清仓
                target_weight = 0.0
                target_val = 0.0
                target_shares = 0

            weight_diff = target_weight - curr_weight
            shares_diff = target_shares - curr_shares

            # 如果权重偏离小于阈值，且目标仍需持仓，不触发微小调仓以省手续费
            if abs(weight_diff) < self.rebalance_threshold and target_shares > 0:
                continue

            if shares_diff < 0:  # 需要卖出
                sell_shares = abs(shares_diff)
                sell_orders.append({
                    "symbol": sym,
                    "action": "SELL",
                    "shares": sell_shares,
                    "price": price,
                    "estimated_amount": round(sell_shares * price, 2),
                    "current_shares": curr_shares,
                    "target_shares": target_shares,
                    "reason": "减仓至目标比例" if target_shares > 0 else "标的剔除，清仓卖出",
                })
            elif shares_diff >= 100:  # 需要买入
                buy_shares = (shares_diff // 100) * 100
                buy_orders.append({
                    "symbol": sym,
                    "action": "BUY",
                    "shares": buy_shares,
                    "price": price,
                    "estimated_amount": round(buy_shares * price, 2),
                    "current_shares": curr_shares,
                    "target_shares": target_shares,
                    "reason": "新标的建仓" if curr_shares == 0 else "加仓至目标比例",
                })

        return {
            "total_equity": round(total_equity, 2),
            "current_cash": round(current_cash, 2),
            "holdings_market_val": round(holdings_market_val, 2),
            "strategy": strategy_type,
            "target_allocation": sizing,
            "orders": sell_orders + buy_orders,
            "orders_count": len(sell_orders) + len(buy_orders),
        }
