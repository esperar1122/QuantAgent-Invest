"""
量化回测主调度引擎 (Backtest Engine)
支持单标的与多标的组合、策略选择、A股撮合与表现评估全流程
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.backtest.trade_simulator import TradeSimulator
from app.services.backtest.performance_metrics import PerformanceCalculator
from app.services.backtest.strategies import get_strategy_by_name, BaseStrategy


class BacktestEngine:
    """回测调度引擎"""

    def __init__(
        self,
        initial_cash: float = 100000.0,
        commission_rate: float = 0.00025,
        stamp_duty_rate: float = 0.0005,
        slippage: float = 0.001,
        position_ratio: float = 0.95,  # 每次买入占用可用资金比例
    ):
        self.initial_cash = initial_cash
        self.commission_rate = commission_rate
        self.stamp_duty_rate = stamp_duty_rate
        self.slippage = slippage
        self.position_ratio = position_ratio

    def run(
        self,
        symbol: str,
        df: pd.DataFrame,
        strategy_name: str = "dual_ma",
        strategy_params: Optional[Dict[str, Any]] = None,
        benchmark_df: Optional[pd.DataFrame] = None,
    ) -> Dict[str, Any]:
        """
        运行单标的回测

        Args:
            symbol: 股票代码（例如 600519 或 000001）
            df: 历史K线 DataFrame，必须包含 ['date', 'open', 'high', 'low', 'close', 'volume']
            strategy_name: 策略名 (dual_ma, macd, bollinger)
            strategy_params: 策略参数
            benchmark_df: 基准K线 DataFrame (可选)
        """
        if df.empty or len(df) < 20:
            raise ValueError(f"标的 {symbol} 历史数据不足（至少需要 20 条K线记录）")

        # 规范化列名
        data = df.copy().sort_values("date").reset_index(drop=True)
        data["date"] = data["date"].astype(str)
        for col in ["open", "high", "low", "close", "volume"]:
            data[col] = pd.to_numeric(data[col], errors="coerce")

        # 1. 实例化策略并生成买卖信号
        strategy = get_strategy_by_name(strategy_name, strategy_params)
        data_with_signals = strategy.generate_signals(data)

        # 2. 初始化交易仿真器
        sim = TradeSimulator(
            initial_cash=self.initial_cash,
            commission_rate=self.commission_rate,
            stamp_duty_rate=self.stamp_duty_rate,
            slippage=self.slippage
        )

        equity_curve: List[Dict[str, Any]] = []
        equity_series_data = []
        dates_list = []

        # 判断涨跌停限制（主板 10%，创业板/科创板 20%）
        is_chinext_or_star = symbol.startswith(("300", "301", "688"))
        limit_threshold = 0.198 if is_chinext_or_star else 0.098

        prev_close = None

        # 3. 逐日事件驱动仿真
        for idx, row in data_with_signals.iterrows():
            date_str = str(row["date"])
            close_px = float(row["close"])
            open_px = float(row["open"]) if not np.isnan(row["open"]) else close_px
            signal = int(row.get("signal", 0))

            # 新交易日开始，T+1 解冻
            sim.start_new_trading_day()

            # 涨跌停检测
            is_limit_up = False
            is_limit_down = False
            if prev_close and prev_close > 0:
                pct_chg = (close_px - prev_close) / prev_close
                if pct_chg >= limit_threshold:
                    is_limit_up = True
                elif pct_chg <= -limit_threshold:
                    is_limit_down = True

            # 撮合买卖信号 (使用当日收盘价撮合)
            if signal == 1:  # 买入信号
                # 计算目标购买股数
                alloc_cash = sim.cash * self.position_ratio
                if alloc_cash > 2000 and close_px > 0:
                    raw_shares = int(alloc_cash / close_px)
                    target_shares = (raw_shares // 100) * 100
                    if target_shares >= 100:
                        sim.buy(
                            date_str=date_str,
                            symbol=symbol,
                            price=close_px,
                            target_shares=target_shares,
                            is_limit_up=is_limit_up
                        )
            elif signal == -1:  # 卖出信号
                # 全仓清仓
                sim.sell(
                    date_str=date_str,
                    symbol=symbol,
                    price=close_px,
                    target_shares=None,
                    is_limit_down=is_limit_down
                )

            # 记录当日收盘后的账户总资产
            cur_prices = {symbol: close_px}
            total_eq = sim.get_total_equity(cur_prices)
            cash_val = sim.cash
            holdings_val = sim.get_portfolio_market_value(cur_prices)
            current_shares = sim.positions.get(symbol, {}).get("shares", 0)

            dates_list.append(date_str)
            equity_series_data.append(total_eq)

            equity_curve.append({
                "date": date_str,
                "total_equity": round(total_eq, 2),
                "cash": round(cash_val, 2),
                "market_value": round(holdings_val, 2),
                "holdings_shares": current_shares,
                "close_price": round(close_px, 2),
            })

            prev_close = close_px

        # 4. 构建净值序列并计算量化绩效指标
        equity_series = pd.Series(equity_series_data, index=dates_list)

        benchmark_series = None
        if benchmark_df is not None and not benchmark_df.empty and "close" in benchmark_df.columns:
            bench_clean = benchmark_df.sort_values("date").reset_index(drop=True)
            bench_clean["close"] = pd.to_numeric(bench_clean["close"], errors="coerce")
            benchmark_series = pd.Series(bench_clean["close"].values, index=bench_clean["date"].astype(str).values)

        calc = PerformanceCalculator()
        metrics = calc.calculate(equity_series, sim.trades_history, benchmark_series)

        # 5. 组装归一化净值（基准化为 1.0），方便前端 ECharts 对比
        norm_initial = equity_series_data[0] if equity_series_data else 1.0
        normalized_equity = [round(v / norm_initial, 4) for v in equity_series_data]

        for i, item in enumerate(equity_curve):
            item["nav"] = normalized_equity[i]

        return {
            "symbol": symbol,
            "strategy": strategy_name,
            "params": strategy_params or {},
            "metrics": metrics,
            "trades_count": len(sim.trades_history),
            "trades": sim.trades_history,
            "equity_curve": equity_curve,
            "final_positions": sim.positions,
        }
