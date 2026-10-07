"""
A 股交易撮合与账户仿真器
严格遵守 A 股交易制度：T+1、涨跌停板、印花税、过户费、最低佣金与滑点损耗
"""

import math
from typing import Dict, Any, List, Optional
from datetime import datetime


class TradeSimulator:
    """A 股模拟账户撮合器"""

    def __init__(
        self,
        initial_cash: float = 100000.0,
        commission_rate: float = 0.00025,   # 万分之2.5佣金
        min_commission: float = 5.0,        # 最低5元佣金
        stamp_duty_rate: float = 0.0005,    # 万分之5印花税（仅卖出）
        transfer_fee_rate: float = 0.00001, # 十万分之1过户费（双边）
        slippage: float = 0.001,            # 0.1% 滑点
    ):
        self.initial_cash = float(initial_cash)
        self.cash = float(initial_cash)
        self.commission_rate = commission_rate
        self.min_commission = min_commission
        self.stamp_duty_rate = stamp_duty_rate
        self.transfer_fee_rate = transfer_fee_rate
        self.slippage = slippage

        # 持仓字典: { symbol: { "shares": int (总持股), "avail_shares": int (T+1可用持股), "avg_cost": float } }
        self.positions: Dict[str, Dict[str, Any]] = {}
        # 历史撮合明细记录
        self.trades_history: List[Dict[str, Any]] = []

    def start_new_trading_day(self):
        """进入新交易日，执行 T+1 解冻逻辑：将所有持仓转为可用"""
        for sym, pos in self.positions.items():
            pos["avail_shares"] = pos["shares"]

    def buy(
        self,
        date_str: str,
        symbol: str,
        price: float,
        target_shares: int,
        is_limit_up: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        执行买入撮合
        Args:
            date_str: 交易日期
            symbol: 股票代码
            price: 当日参考基准价（如开盘价或收盘价）
            target_shares: 拟买入股数
            is_limit_up: 当日是否封涨停（封涨停则买单无法撮合）
        """
        if is_limit_up:
            return None  # 涨停无法买入

        if target_shares <= 0 or price <= 0:
            return None

        # A股买入必须是整百股（1手=100股）
        shares = (target_shares // 100) * 100
        if shares <= 0:
            return None

        # 考虑买入滑点 (买入成交价略高于基准价)
        exec_price = round(price * (1 + self.slippage), 2)
        gross_amount = shares * exec_price

        # 计算费用
        commission = max(self.min_commission, gross_amount * self.commission_rate)
        transfer_fee = gross_amount * self.transfer_fee_rate
        total_cost = gross_amount + commission + transfer_fee

        # 检查可用资金是否充足，若不足则降额调整股数
        if total_cost > self.cash:
            # 重新计算可用资金最多能买的手数
            max_shares = int(self.cash / (exec_price * (1 + self.commission_rate + self.transfer_fee_rate)))
            shares = (max_shares // 100) * 100
            if shares <= 0:
                return None
            gross_amount = shares * exec_price
            commission = max(self.min_commission, gross_amount * self.commission_rate)
            transfer_fee = gross_amount * self.transfer_fee_rate
            total_cost = gross_amount + commission + transfer_fee

        self.cash -= total_cost

        # 更新持仓（注意：当日买入的 shares 进入持仓，但 avail_shares 不增加，次日才解冻）
        if symbol not in self.positions:
            self.positions[symbol] = {
                "shares": shares,
                "avail_shares": 0,  # T+1 当日不可卖
                "avg_cost": exec_price,
            }
        else:
            old_pos = self.positions[symbol]
            new_shares = old_pos["shares"] + shares
            new_cost = (old_pos["shares"] * old_pos["avg_cost"] + gross_amount) / new_shares
            old_pos["shares"] = new_shares
            old_pos["avg_cost"] = round(new_cost, 3)

        trade_record = {
            "date": date_str,
            "action": "BUY",
            "symbol": symbol,
            "shares": shares,
            "price": exec_price,
            "amount": round(gross_amount, 2),
            "fee": round(commission + transfer_fee, 2),
            "cash_after": round(self.cash, 2),
            "pnl": 0.0,
            "return_pct": 0.0,
        }
        self.trades_history.append(trade_record)
        return trade_record

    def sell(
        self,
        date_str: str,
        symbol: str,
        price: float,
        target_shares: Optional[int] = None,
        is_limit_down: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        执行卖出撮合
        Args:
            date_str: 交易日期
            symbol: 股票代码
            price: 当日参考基准价
            target_shares: 拟卖出股数，若为 None 则全部清仓
            is_limit_down: 当日是否跌停（跌停则无法撮合成交）
        """
        if is_limit_down:
            return None  # 跌停无法卖出

        if symbol not in self.positions or price <= 0:
            return None

        pos = self.positions[symbol]
        avail = pos["avail_shares"]
        if avail <= 0:
            return None  # 无可用持仓 (受 T+1 限制)

        shares_to_sell = avail if target_shares is None else min(avail, target_shares)
        if shares_to_sell <= 0:
            return None

        # 考虑卖出滑点 (卖出成交价略低于基准价)
        exec_price = round(price * (1 - self.slippage), 2)
        gross_amount = shares_to_sell * exec_price

        # 计算卖出费用 (包含印花税)
        commission = max(self.min_commission, gross_amount * self.commission_rate)
        stamp_duty = gross_amount * self.stamp_duty_rate
        transfer_fee = gross_amount * self.transfer_fee_rate
        total_fee = commission + stamp_duty + transfer_fee

        net_income = gross_amount - total_fee
        self.cash += net_income

        # 计算本笔交易实现盈亏 (PnL)
        avg_cost = pos["avg_cost"]
        cost_basis = shares_to_sell * avg_cost
        pnl = round(gross_amount - cost_basis - total_fee, 2)
        return_pct = round((pnl / cost_basis) * 100, 2) if cost_basis > 0 else 0.0

        # 更新持仓
        pos["shares"] -= shares_to_sell
        pos["avail_shares"] -= shares_to_sell
        if pos["shares"] <= 0:
            del self.positions[symbol]

        trade_record = {
            "date": date_str,
            "action": "SELL",
            "symbol": symbol,
            "shares": shares_to_sell,
            "price": exec_price,
            "amount": round(gross_amount, 2),
            "fee": round(total_fee, 2),
            "cash_after": round(self.cash, 2),
            "pnl": pnl,
            "return_pct": return_pct,
        }
        self.trades_history.append(trade_record)
        return trade_record

    def get_portfolio_market_value(self, current_prices: Dict[str, float]) -> float:
        """根据当前最新市价计算持仓股票总市值"""
        market_val = 0.0
        for sym, pos in self.positions.items():
            price = current_prices.get(sym, pos["avg_cost"])
            market_val += pos["shares"] * price
        return market_val

    def get_total_equity(self, current_prices: Dict[str, float]) -> float:
        """获取账户当前总动态净资产 = 可用现金 + 持仓市值"""
        return self.cash + self.get_portfolio_market_value(current_prices)
