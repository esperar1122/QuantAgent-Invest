"""
量化回测性能评估与风险指标计算器
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd


class PerformanceCalculator:
    """量化策略评价指标计算器"""

    def __init__(self, risk_free_rate: float = 0.02):
        """
        Args:
            risk_free_rate: 年化无风险利率（默认 2.0%）
        """
        self.risk_free_rate = risk_free_rate

    def calculate(
        self,
        equity_series: pd.Series,
        trades: List[Dict[str, Any]],
        benchmark_series: Optional[pd.Series] = None
    ) -> Dict[str, Any]:
        """
        计算全套量化表现与风险指标

        Args:
            equity_series: 每日账户总资产序列，索引为日期/时间
            trades: 交易明细列表，每笔记录包含 pnl, return_pct 等
            benchmark_series: 基准（如沪深300）净值/点位序列（可选）

        Returns:
            指标字典
        """
        if equity_series.empty or len(equity_series) < 2:
            return {
                "total_return": 0.0,
                "annualized_return": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "calmar_ratio": 0.0,
                "win_rate": 0.0,
                "profit_loss_ratio": 0.0,
                "total_trades": len(trades),
                "volatility": 0.0,
                "alpha": 0.0,
                "beta": 0.0,
            }

        # 基础收益统计
        initial_val = float(equity_series.iloc[0])
        final_val = float(equity_series.iloc[-1])
        total_return = (final_val - initial_val) / initial_val if initial_val > 0 else 0.0

        num_bars = len(equity_series)
        annual_factor = 252  # A股年化交易日通常按252天计算
        
        if num_bars > 1 and initial_val > 0 and final_val > 0:
            cagr = (final_val / initial_val) ** (annual_factor / max(num_bars, 1)) - 1
        else:
            cagr = 0.0

        # 日收益率序列
        daily_returns = equity_series.pct_change().dropna()
        if len(daily_returns) == 0:
            daily_returns = pd.Series([0.0])

        # 波动率 (年化)
        daily_std = float(daily_returns.std(ddof=1)) if len(daily_returns) > 1 else 0.0
        annual_volatility = daily_std * np.sqrt(annual_factor)

        # 最大回撤与回撤序列
        cum_max = equity_series.cummax()
        drawdown_series = (equity_series - cum_max) / cum_max
        max_drawdown = float(abs(drawdown_series.min())) if not drawdown_series.empty else 0.0

        # 最长回撤期（天数）
        underwater = drawdown_series < 0
        longest_dd_duration = 0
        current_dd_duration = 0
        for is_down in underwater:
            if is_down:
                current_dd_duration += 1
                if current_dd_duration > longest_dd_duration:
                    longest_dd_duration = current_dd_duration
            else:
                current_dd_duration = 0

        # 夏普比率 (Sharpe Ratio)
        rf_daily = self.risk_free_rate / annual_factor
        excess_returns = daily_returns - rf_daily
        if daily_std > 1e-7:
            sharpe_ratio = float((excess_returns.mean() / daily_std) * np.sqrt(annual_factor))
        else:
            sharpe_ratio = 0.0

        # 索提诺比率 (Sortino Ratio - 仅惩罚下行波动)
        downside_returns = daily_returns[daily_returns < rf_daily]
        downside_std = float(downside_returns.std(ddof=1)) if len(downside_returns) > 1 else 0.0
        if downside_std > 1e-7:
            sortino_ratio = float((excess_returns.mean() / downside_std) * np.sqrt(annual_factor))
        else:
            sortino_ratio = 0.0

        # 卡玛比率 (Calmar Ratio = 年化收益 / 最大回撤)
        calmar_ratio = float(cagr / max_drawdown) if max_drawdown > 1e-5 else 0.0

        # 交易维度的统计
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.get("pnl", 0) > 0]
        losing_trades = [t for t in trades if t.get("pnl", 0) < 0]
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        win_rate = (win_count / total_trades) if total_trades > 0 else 0.0

        avg_win = float(np.mean([t["pnl"] for t in winning_trades])) if winning_trades else 0.0
        avg_loss = float(abs(np.mean([t["pnl"] for t in losing_trades]))) if losing_trades else 0.0
        profit_loss_ratio = (avg_win / avg_loss) if avg_loss > 1e-5 else (999.0 if avg_win > 0 else 0.0)

        # 基准对比 (Alpha / Beta)
        alpha = 0.0
        beta = 1.0
        benchmark_total_return = 0.0

        if benchmark_series is not None and not benchmark_series.empty and len(benchmark_series) >= len(equity_series):
            # 对齐数据长度
            aligned_bench = benchmark_series.iloc[-len(equity_series):]
            bench_initial = float(aligned_bench.iloc[0])
            bench_final = float(aligned_bench.iloc[-1])
            if bench_initial > 0:
                benchmark_total_return = (bench_final - bench_initial) / bench_initial

            bench_returns = aligned_bench.pct_change().dropna()
            if len(bench_returns) == len(daily_returns) and len(bench_returns) > 2:
                cov = np.cov(daily_returns, bench_returns)[0][1]
                var_bench = np.var(bench_returns, ddof=1)
                if var_bench > 1e-7:
                    beta = float(cov / var_bench)
                    alpha = float((cagr - (self.risk_free_rate + beta * (benchmark_total_return - self.risk_free_rate))))

        return {
            "initial_cash": round(initial_val, 2),
            "final_equity": round(final_val, 2),
            "total_return": round(total_return, 4),
            "total_return_pct": round(total_return * 100, 2),
            "annualized_return": round(cagr, 4),
            "annualized_return_pct": round(cagr * 100, 2),
            "annual_volatility": round(annual_volatility, 4),
            "max_drawdown": round(max_drawdown, 4),
            "max_drawdown_pct": round(max_drawdown * 100, 2),
            "longest_drawdown_days": int(longest_dd_duration),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "sortino_ratio": round(sortino_ratio, 2),
            "calmar_ratio": round(calmar_ratio, 2),
            "total_trades": total_trades,
            "win_trades": win_count,
            "loss_trades": loss_count,
            "win_rate": round(win_rate, 4),
            "win_rate_pct": round(win_rate * 100, 2),
            "profit_loss_ratio": round(profit_loss_ratio, 2),
            "benchmark_return_pct": round(benchmark_total_return * 100, 2),
            "alpha": round(alpha, 4),
            "beta": round(beta, 2),
        }
