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
        min_commission: float = 5.0,
        stamp_duty_rate: float = 0.0005,
        transfer_fee_rate: float = 0.00001,
        slippage: float = 0.001,
        slippage_type: str = "percent",
        position_ratio: float = 0.95,  # 每次买入占用可用资金比例
    ):
        self.initial_cash = initial_cash
        self.commission_rate = commission_rate
        self.min_commission = min_commission
        self.stamp_duty_rate = stamp_duty_rate
        self.transfer_fee_rate = transfer_fee_rate
        self.slippage = slippage
        self.slippage_type = slippage_type
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
            min_commission=self.min_commission,
            stamp_duty_rate=self.stamp_duty_rate,
            transfer_fee_rate=self.transfer_fee_rate,
            slippage=self.slippage,
            slippage_type=self.slippage_type,
        )

        equity_curve: List[Dict[str, Any]] = []
        equity_series_data = []
        dates_list = []

        # 判断涨跌停限制（主板 10%，创业板/科创板 20%）
        is_chinext_or_star = symbol.startswith(("300", "301", "688"))
        limit_threshold = 0.198 if is_chinext_or_star else 0.098

        # 提取风控参数 (适用于所有预设与自定义策略)
        stop_loss_pct = float(strategy_params.get("stop_loss_pct", 0.0)) if strategy_params else 0.0
        take_profit_pct = float(strategy_params.get("take_profit_pct", 0.0)) if strategy_params else 0.0
        max_holding_days = int(strategy_params.get("max_holding_days", 0)) if strategy_params else 0

        # 持仓天数追踪
        holding_days_counter = 0
        prev_close = None

        # 3. 逐日事件驱动仿真
        for idx, row in data_with_signals.iterrows():
            date_str = str(row["date"])
            close_px = float(row["close"])
            open_px = float(row["open"]) if not np.isnan(row["open"]) else close_px
            volume = float(row.get("volume", 0.0)) if not np.isnan(row.get("volume", 0.0)) else 0.0
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

            pos = sim.positions.get(symbol)
            has_position = pos is not None and pos.get("shares", 0) > 0
            if has_position:
                holding_days_counter += 1
            else:
                holding_days_counter = 0

            # 优先执行风控规则检测 (止损 / 止盈 / 最大持仓天数)
            risk_exit_triggered = False
            if has_position and pos.get("avail_shares", 0) > 0:
                avg_cost = pos.get("avg_cost", close_px)
                if avg_cost > 0:
                    current_gain_pct = (close_px - avg_cost) / avg_cost
                    # 1. 严格止损检测 (例如设定 0.05 即 -5% 止损)
                    if stop_loss_pct > 0 and current_gain_pct <= -stop_loss_pct:
                        sim.sell(
                            date_str=date_str,
                            symbol=symbol,
                            price=close_px,
                            target_shares=None,
                            is_limit_down=is_limit_down,
                            day_volume=volume,
                            reason=f"止损触发 ({round(current_gain_pct * 100, 1)}%)"
                        )
                        risk_exit_triggered = True
                        holding_days_counter = 0
                    # 2. 动态止盈检测 (例如设定 0.15 即 +15% 止盈)
                    elif take_profit_pct > 0 and current_gain_pct >= take_profit_pct:
                        sim.sell(
                            date_str=date_str,
                            symbol=symbol,
                            price=close_px,
                            target_shares=None,
                            is_limit_down=is_limit_down,
                            day_volume=volume,
                            reason=f"止盈达成 (+{round(current_gain_pct * 100, 1)}%)"
                        )
                        risk_exit_triggered = True
                        holding_days_counter = 0
                    # 3. 最大持仓交易日周期到期平仓
                    elif max_holding_days > 0 and holding_days_counter >= max_holding_days:
                        sim.sell(
                            date_str=date_str,
                            symbol=symbol,
                            price=close_px,
                            target_shares=None,
                            is_limit_down=is_limit_down,
                            day_volume=volume,
                            reason=f"持仓周期到期 ({holding_days_counter}天)"
                        )
                        risk_exit_triggered = True
                        holding_days_counter = 0

            # 撮合买卖信号 (使用当日收盘价撮合)
            if not risk_exit_triggered:
                if signal == 1 and not has_position:  # 买入信号（空仓时买入）
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
                                is_limit_up=is_limit_up,
                                day_volume=volume,
                                reason="策略买入信号"
                            )
                            holding_days_counter = 0
                elif signal == -1 and has_position:  # 卖出信号
                    # 全仓清仓
                    sim.sell(
                        date_str=date_str,
                        symbol=symbol,
                        price=close_px,
                        target_shares=None,
                        is_limit_down=is_limit_down,
                        day_volume=volume,
                        reason="指标死叉平仓"
                    )
                    holding_days_counter = 0

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

        cum_max = 1.0
        for i, item in enumerate(equity_curve):
            nav_val = normalized_equity[i]
            item["nav"] = nav_val
            cum_max = max(cum_max, nav_val)
            dd_pct = ((nav_val - cum_max) / cum_max * 100) if cum_max > 0 else 0.0
            item["drawdown_pct"] = round(dd_pct, 2)
            # 基准净值计算
            if benchmark_series is not None and not benchmark_series.empty and i < len(benchmark_series):
                b_init = benchmark_series.iloc[0]
                b_val = benchmark_series.iloc[i]
                item["benchmark_nav"] = round(b_val / b_init, 4) if b_init > 0 else 1.0
            else:
                item["benchmark_nav"] = 1.0

        return {
            "symbol": symbol,
            "strategy": strategy_name,
            "params": strategy_params or {},
            "metrics": metrics,
            "frictions": sim.get_friction_summary(),
            "trades_count": len(sim.trades_history),
            "trades": sim.trades_history,
            "equity_curve": equity_curve,
            "daily_nav": equity_curve,
            "final_positions": sim.positions,
        }

    def run_portfolio(
        self,
        symbols: List[str],
        dfs_dict: Dict[str, pd.DataFrame],
        strategy_name: str = "dual_ma",
        strategy_params: Optional[Dict[str, Any]] = None,
        benchmark_df: Optional[pd.DataFrame] = None,
        sizing_model: str = "equal_weight",
    ) -> Dict[str, Any]:
        """
        运行多标的组合量化回测 (Portfolio Backtest)
        支持多资产截面信号撮合、动态仓位再平衡、真实A股摩擦约束与资产贡献归因
        """
        valid_symbols = []
        symbol_rows_by_date = {}
        volatilities = {}

        # 1. 对每只股票生成策略信号并解析数据
        for sym in symbols:
            raw_df = dfs_dict.get(sym)
            if raw_df is None or raw_df.empty or len(raw_df) < 15:
                continue
            data = raw_df.copy().sort_values("date").reset_index(drop=True)
            data["date"] = data["date"].astype(str)
            for col in ["open", "high", "low", "close", "volume"]:
                data[col] = pd.to_numeric(data[col], errors="coerce")
            
            strategy = get_strategy_by_name(strategy_name, strategy_params)
            with_sig = strategy.generate_signals(data)
            valid_symbols.append(sym)

            # 计算波动率用于 inverse_volatility 仓位分配
            daily_ret = with_sig["close"].pct_change().dropna()
            vol = float(daily_ret.std(ddof=1)) if len(daily_ret) > 5 else 0.02
            volatilities[sym] = max(0.005, vol)

            row_map = {}
            for _, r in with_sig.iterrows():
                row_map[str(r["date"])] = r
            symbol_rows_by_date[sym] = row_map

        if not valid_symbols:
            raise ValueError(f"候选组合中所有标的历史数据不足或为空，无法执行组合回测 (已传入: {symbols})")

        # 2. 提取组合全局交易日历对齐
        all_dates_set = set()
        for r_map in symbol_rows_by_date.values():
            all_dates_set.update(r_map.keys())
        all_dates = sorted(list(all_dates_set))

        # 3. 计算各标的目标基础权重
        if sizing_model == "inverse_volatility" and len(valid_symbols) > 1:
            inv_vols = {s: 1.0 / volatilities[s] for s in valid_symbols}
            tot_inv = sum(inv_vols.values())
            target_weights = {s: (inv_vols[s] / tot_inv) * self.position_ratio for s in valid_symbols}
        else:
            eq_w = self.position_ratio / len(valid_symbols)
            target_weights = {s: eq_w for s in valid_symbols}

        # 4. 初始化仿真器与状态追踪
        sim = TradeSimulator(
            initial_cash=self.initial_cash,
            commission_rate=self.commission_rate,
            min_commission=self.min_commission,
            stamp_duty_rate=self.stamp_duty_rate,
            transfer_fee_rate=self.transfer_fee_rate,
            slippage=self.slippage,
            slippage_type=self.slippage_type,
        )

        stop_loss_pct = float(strategy_params.get("stop_loss_pct", 0.0)) if strategy_params else 0.0
        take_profit_pct = float(strategy_params.get("take_profit_pct", 0.0)) if strategy_params else 0.0
        max_holding_days = int(strategy_params.get("max_holding_days", 0)) if strategy_params else 0

        holding_days = {s: 0 for s in valid_symbols}
        prev_closes = {s: None for s in valid_symbols}
        last_known_price = {}

        equity_curve: List[Dict[str, Any]] = []
        equity_series_data = []
        dates_list = []

        # 5. 逐日截面多资产事件驱动撮合
        for date_str in all_dates:
            sim.start_new_trading_day()

            day_prices = {}
            day_volumes = {}
            day_signals = {}
            limit_ups = {}
            limit_downs = {}

            for sym in valid_symbols:
                r = symbol_rows_by_date[sym].get(date_str)
                if r is not None:
                    c_px = float(r["close"])
                    last_known_price[sym] = c_px
                    day_prices[sym] = c_px
                    day_volumes[sym] = float(r.get("volume", 0.0)) if not np.isnan(r.get("volume", 0.0)) else 0.0
                    day_signals[sym] = int(r.get("signal", 0))

                    # 涨跌停判断
                    p_close = prev_closes[sym]
                    is_star = sym.startswith(("300", "301", "688"))
                    thresh = 0.198 if is_star else 0.098
                    l_up = False
                    l_down = False
                    if p_close and p_close > 0:
                        chg = (c_px - p_close) / p_close
                        if chg >= thresh:
                            l_up = True
                        elif chg <= -thresh:
                            l_down = True
                    limit_ups[sym] = l_up
                    limit_downs[sym] = l_down
                    prev_closes[sym] = c_px
                else:
                    if sym in last_known_price:
                        day_prices[sym] = last_known_price[sym]
                    day_signals[sym] = 0
                    limit_ups[sym] = True
                    limit_downs[sym] = True

            current_portfolio_eq = sim.get_total_equity(day_prices)

            # 阶段 A: 优先执行各标的平仓与止损止盈（回笼现金）
            for sym in valid_symbols:
                pos = sim.positions.get(sym)
                has_pos = pos is not None and pos.get("shares", 0) > 0
                if has_pos:
                    holding_days[sym] += 1
                else:
                    holding_days[sym] = 0

                if not has_pos or pos.get("avail_shares", 0) <= 0:
                    continue

                c_px = day_prices.get(sym, 0.0)
                if c_px <= 0:
                    continue

                avg_cost = pos.get("avg_cost", c_px)
                gain_pct = (c_px - avg_cost) / avg_cost if avg_cost > 0 else 0.0

                exit_reason = None
                if stop_loss_pct > 0 and gain_pct <= -stop_loss_pct:
                    exit_reason = f"止损触发 ({round(gain_pct * 100, 1)}%)"
                elif take_profit_pct > 0 and gain_pct >= take_profit_pct:
                    exit_reason = f"止盈达成 (+{round(gain_pct * 100, 1)}%)"
                elif max_holding_days > 0 and holding_days[sym] >= max_holding_days:
                    exit_reason = f"持仓到期 ({holding_days[sym]}天)"
                elif day_signals.get(sym) == -1:
                    exit_reason = "指标死叉平仓"

                if exit_reason:
                    sim.sell(
                        date_str=date_str,
                        symbol=sym,
                        price=c_px,
                        target_shares=None,
                        is_limit_down=limit_downs.get(sym, False),
                        day_volume=day_volumes.get(sym, 0.0),
                        reason=exit_reason
                    )
                    holding_days[sym] = 0

            # 阶段 B: 买入信号建仓
            buy_candidates = [
                sym for sym in valid_symbols
                if day_signals.get(sym) == 1 and (sim.positions.get(sym) is None or sim.positions[sym].get("shares", 0) == 0)
            ]

            for sym in buy_candidates:
                c_px = day_prices.get(sym, 0.0)
                if c_px <= 0 or limit_ups.get(sym, False):
                    continue

                w = target_weights.get(sym, 1.0 / len(valid_symbols))
                target_alloc = current_portfolio_eq * w
                alloc_cash = min(target_alloc, sim.cash * 0.95)

                if alloc_cash > 2000:
                    raw_shares = int(alloc_cash / c_px)
                    target_shares = (raw_shares // 100) * 100
                    if target_shares >= 100:
                        sim.buy(
                            date_str=date_str,
                            symbol=sym,
                            price=c_px,
                            target_shares=target_shares,
                            is_limit_up=limit_ups.get(sym, False),
                            day_volume=day_volumes.get(sym, 0.0),
                            reason="组合策略买入"
                        )
                        holding_days[sym] = 0

            # 阶段 C: 记录每日组合资产
            tot_eq = sim.get_total_equity(day_prices)
            cash_val = sim.cash
            holdings_val = sim.get_portfolio_market_value(day_prices)
            active_holdings = len([p for p in sim.positions.values() if p.get("shares", 0) > 0])

            dates_list.append(date_str)
            equity_series_data.append(tot_eq)

            equity_curve.append({
                "date": date_str,
                "total_equity": round(tot_eq, 2),
                "cash": round(cash_val, 2),
                "market_value": round(holdings_val, 2),
                "active_holdings": active_holdings,
            })

        # 6. 计算量化绩效
        equity_series = pd.Series(equity_series_data, index=dates_list)
        benchmark_series = None
        if benchmark_df is not None and not benchmark_df.empty and "close" in benchmark_df.columns:
            bench_clean = benchmark_df.sort_values("date").reset_index(drop=True)
            bench_clean["close"] = pd.to_numeric(bench_clean["close"], errors="coerce")
            benchmark_series = pd.Series(bench_clean["close"].values, index=bench_clean["date"].astype(str).values)

        calc = PerformanceCalculator()
        metrics = calc.calculate(equity_series, sim.trades_history, benchmark_series)

        # 7. 归一化净值与动态回撤
        norm_initial = equity_series_data[0] if equity_series_data else 1.0
        normalized_equity = [round(v / norm_initial, 4) for v in equity_series_data]

        cum_max = 1.0
        for i, item in enumerate(equity_curve):
            nav_val = normalized_equity[i]
            item["nav"] = nav_val
            cum_max = max(cum_max, nav_val)
            dd_pct = ((nav_val - cum_max) / cum_max * 100) if cum_max > 0 else 0.0
            item["drawdown_pct"] = round(dd_pct, 2)
            if benchmark_series is not None and not benchmark_series.empty and i < len(benchmark_series):
                b_init = benchmark_series.iloc[0]
                b_val = benchmark_series.iloc[i]
                item["benchmark_nav"] = round(b_val / b_init, 4) if b_init > 0 else 1.0
            else:
                item["benchmark_nav"] = 1.0

        # 8. 各标的收益贡献与表现归因 (Asset Attribution)
        attribution: Dict[str, Any] = {}
        for sym in valid_symbols:
            sym_trades = [t for t in sim.trades_history if t.get("symbol") == sym]
            sell_trades = [t for t in sym_trades if t.get("action") == "SELL"]
            sym_pnl = sum(t.get("pnl", 0.0) for t in sell_trades)
            sym_wins = len([t for t in sell_trades if t.get("pnl", 0.0) > 0])
            sym_losses = len([t for t in sell_trades if t.get("pnl", 0.0) < 0])
            win_r = round((sym_wins / len(sell_trades) * 100), 1) if sell_trades else 0.0

            attribution[sym] = {
                "symbol": sym,
                "trades_count": len(sym_trades),
                "sell_count": len(sell_trades),
                "win_count": sym_wins,
                "loss_count": sym_losses,
                "win_rate_pct": win_r,
                "realized_pnl": round(sym_pnl, 2),
                "contribution_pct": round((sym_pnl / self.initial_cash * 100), 2) if self.initial_cash > 0 else 0.0,
                "current_shares": sim.positions.get(sym, {}).get("shares", 0),
                "target_weight_pct": round(target_weights.get(sym, 0.0) * 100, 1),
            }

        return {
            "is_portfolio": True,
            "symbols": valid_symbols,
            "symbol": ", ".join(valid_symbols),
            "strategy": strategy_name,
            "params": strategy_params or {},
            "sizing_model": sizing_model,
            "metrics": metrics,
            "frictions": sim.get_friction_summary(),
            "asset_attribution": attribution,
            "trades_count": len(sim.trades_history),
            "trades": sim.trades_history,
            "equity_curve": equity_curve,
            "daily_nav": equity_curve,
            "final_positions": sim.positions,
        }
