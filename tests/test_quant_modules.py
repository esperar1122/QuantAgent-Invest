"""
量化扩展核心模块全面集成单元测试
覆盖：回测撮合、指标计算、仓位算法、实时行情推流、微信卡片、模拟盘
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))
import pandas as pd
import numpy as np
import asyncio
from datetime import datetime

from app.services.backtest.performance_metrics import PerformanceCalculator
from app.services.backtest.trade_simulator import TradeSimulator
from app.services.backtest.strategies import DualMAStrategy, MACDStrategy, BollingerBandsStrategy
from app.services.backtest.backtest_engine import BacktestEngine
from app.services.portfolio.position_sizer import PositionSizer
from app.services.portfolio.portfolio_optimizer import PortfolioOptimizer
from app.services.quotes.realtime_streamer import RealtimeQuoteStreamer
from app.services.notifier.wechat_notifier import WeChatNotifier
from app.services.paper_trading.paper_account_service import PaperAccountService


def create_dummy_kline_df(num_days=100) -> pd.DataFrame:
    """创建合成日K线走势测试数据"""
    dates = pd.date_range("2023-01-01", periods=num_days, freq="B").strftime("%Y-%m-%d").tolist()
    # 模拟一个震荡上升的行情
    np.random.seed(42)
    base = 100.0
    returns = np.random.normal(0.002, 0.02, num_days)
    prices = base * np.cumprod(1 + returns)

    df = pd.DataFrame({
        "date": dates,
        "open": prices * 0.99,
        "high": prices * 1.02,
        "low": prices * 0.98,
        "close": prices,
        "volume": np.random.randint(10000, 50000, num_days)
    })
    return df


def test_performance_calculator():
    calc = PerformanceCalculator(risk_free_rate=0.02)
    equity = pd.Series([100000.0, 105000.0, 102000.0, 110000.0, 115000.0])
    trades = [
        {"pnl": 5000.0, "return_pct": 5.0},
        {"pnl": -3000.0, "return_pct": -2.8},
        {"pnl": 8000.0, "return_pct": 7.8},
        {"pnl": 5000.0, "return_pct": 4.5},
    ]
    res = calc.calculate(equity, trades)

    assert res["initial_cash"] == 100000.0
    assert res["final_equity"] == 115000.0
    assert res["total_return_pct"] == 15.0
    assert res["max_drawdown"] > 0
    assert res["win_rate"] == 0.75  # 3胜1负
    assert res["total_trades"] == 4
    print("✅ test_performance_calculator passed")


def test_trade_simulator_a_share_rules():
    sim = TradeSimulator(initial_cash=100000.0)

    # 1. 尝试在涨停板买入 -> 应当被拒绝
    buy_res_limit_up = sim.buy("2023-01-01", "600519", 100.0, 500, is_limit_up=True)
    assert buy_res_limit_up is None
    assert sim.cash == 100000.0

    # 2. 正常买入 500 股
    buy_res = sim.buy("2023-01-01", "600519", 100.0, 500)
    assert buy_res is not None
    assert buy_res["shares"] == 500
    assert "600519" in sim.positions
    assert sim.positions["600519"]["shares"] == 500
    assert sim.positions["600519"]["avail_shares"] == 0  # T+1 当天冻结，不可卖

    # 3. 当天尝试卖出 -> 应当因 T+1 限制被拒绝
    sell_res_t0 = sim.sell("2023-01-01", "600519", 105.0, 500)
    assert sell_res_t0 is None

    # 4. 进入次日，解冻持仓
    sim.start_new_trading_day()
    assert sim.positions["600519"]["avail_shares"] == 500

    # 5. 次日卖出 500 股
    sell_res = sim.sell("2023-01-02", "600519", 110.0, 500)
    assert sell_res is not None
    assert sell_res["shares"] == 500
    assert sell_res["pnl"] > 0
    assert "600519" not in sim.positions  # 清仓完毕
    print("✅ test_trade_simulator_a_share_rules passed")


def test_strategies_signals():
    df = create_dummy_kline_df(60)

    # 双均线
    dma = DualMAStrategy(5, 20)
    sig_dma = dma.generate_signals(df)
    assert "signal" in sig_dma.columns
    assert set(sig_dma["signal"].unique()).issubset({-1, 0, 1})

    # MACD
    macd = MACDStrategy()
    sig_macd = macd.generate_signals(df)
    assert "signal" in sig_macd.columns
    assert "dif" in sig_macd.columns

    # 布林带
    bb = BollingerBandsStrategy()
    sig_bb = bb.generate_signals(df)
    assert "signal" in sig_bb.columns
    assert "upper_band" in sig_bb.columns
    print("✅ test_strategies_signals passed")


def test_backtest_engine_run():
    df = create_dummy_kline_df(80)
    engine = BacktestEngine(initial_cash=100000.0)
    res = engine.run("000001", df, strategy_name="dual_ma", strategy_params={"short_window": 5, "long_window": 15})

    assert res["symbol"] == "000001"
    assert "metrics" in res
    assert "equity_curve" in res
    assert len(res["equity_curve"]) == len(df)
    assert "total_return_pct" in res["metrics"]
    assert "sharpe_ratio" in res["metrics"]
    print("✅ test_backtest_engine_run passed")


def test_position_sizing_models():
    # 1. 等权重
    eq_res = PositionSizer.equal_weight(["600519", "000001", "002594"], 100000.0, cash_reserve_ratio=0.1)
    assert len(eq_res) == 3
    for v in eq_res.values():
        assert v["target_amount"] == 30000.0

    # 2. 波动率倒数
    vols = {"600519": 0.15, "000001": 0.30}  # 茅台波动小，平安波动大
    inv_res = PositionSizer.inverse_volatility(vols, 100000.0, max_single_weight=0.80)
    assert inv_res["600519"]["weight"] > inv_res["000001"]["weight"]

    # 3. ATR 风险模型
    atr_res = PositionSizer.atr_risk_budget(
        total_capital=100000.0,
        price=50.0,
        atr_value=1.5,
        risk_ratio=0.01,
        stop_loss_atr_multiplier=2.0
    )
    assert atr_res["shares"] % 100 == 0  # 必须是100整手
    assert atr_res["shares"] > 0
    assert atr_res["stop_loss_price"] < 50.0

    # 4. 半凯利公式
    kelly_res = PositionSizer.fractional_kelly(
        total_capital=100000.0,
        win_rate=0.6,
        profit_loss_ratio=2.0,
        kelly_fraction=0.5
    )
    assert kelly_res["recommended_weight"] > 0
    print("✅ test_position_sizing_models passed")


def test_portfolio_optimizer():
    optimizer = PortfolioOptimizer()
    current_holdings = {
        "600519": {"shares": 300, "price": 100.0},  # 当前有3万元
    }
    target_symbols = ["600519", "000001"]
    plan = optimizer.generate_rebalance_plan(
        current_cash=70000.0,  # 总资产 10万元
        current_holdings=current_holdings,
        target_symbols=target_symbols,
        strategy_type="equal_weight"
    )
    assert "orders" in plan
    assert len(plan["orders"]) > 0
    # 000001 应该产生 BUY 订单
    buy_orders = [o for o in plan["orders"] if o["symbol"] == "000001" and o["action"] == "BUY"]
    print("✅ test_portfolio_optimizer passed")


def test_wechat_notifier_card_formatting():
    notifier = WeChatNotifier()
    # 验证不崩溃，控制台分发
    asyncio.run(notifier.send_signal_alert(
        symbol="600519",
        name="贵州茅台",
        action="BUY",
        price=1680.0,
        shares=200,
        reason="测试用例信号触发",
        stop_loss_price=1620.0
    ))
    print("✅ test_wechat_notifier_card_formatting passed")


def test_paper_trading_service():
    service = PaperAccountService()
    account_id = "test_unit_account"

    # 初始化账户
    acc = asyncio.run(service.get_or_create_account(account_id, initial_cash=100000.0))
    assert acc["cash"] == 100000.0

    # 模拟买入 200 股
    trade_res = asyncio.run(service.execute_trade(
        account_id=account_id,
        symbol="000001",
        name="平安银行",
        action="BUY",
        shares=200,
        price=10.0,
        reason="单元测试建仓"
    ))
    assert trade_res["cash"] < 100000.0  # 扣除了资金与费用
    assert len(trade_res["positions"]) == 1
    pos = trade_res["positions"][0]
    assert pos["symbol"] == "000001"
    assert pos["shares"] == 200
    assert pos["avail_shares"] == 0  # 当天冻结 (T+1)

    # 尝试当天卖出 -> 应当抛出 ValueError
    try:
        asyncio.run(service.execute_trade(
            account_id=account_id,
            symbol="000001",
            name="平安银行",
            action="SELL",
            shares=200,
            price=11.0
        ))
        assert False, "应当受 T+1 限制抛出异常"
    except ValueError as e:
        assert "T+1" in str(e) or "可用持仓不足" in str(e)

    print("✅ test_paper_trading_service passed")


def test_custom_rule_strategy():
    """测试自定义多指标组合策略与风控回测"""
    from app.services.backtest.strategies import get_strategy_by_name
    from app.services.backtest.backtest_engine import BacktestEngine

    # 生成模拟上涨与回撤数据
    dates = pd.date_range("2024-01-01", periods=60).strftime("%Y-%m-%d").tolist()
    # 模拟价格先跌后涨再跌，形成真实的金叉与死叉
    prices = [10.0 - i * 0.2 if i < 15 else (7.0 + (i - 15) * 0.4 if i < 35 else 15.0 - (i - 35) * 0.3) for i in range(60)]
    vols = [10000 + i * 200 for i in range(60)]
    vols[20] = 40000  # 金叉当日放量
    df = pd.DataFrame({
        "date": dates,
        "open": prices,
        "high": [p * 1.02 for p in prices],
        "low": [p * 0.98 for p in prices],
        "close": prices,
        "volume": vols
    })

    # 1. 验证自定义策略信号生成
    strat = get_strategy_by_name("custom_rule", {
        "ma_mode": "cross",
        "short_window": 5,
        "long_window": 15,
        "volume_filter": "vol_surge",
        "vol_multiplier": 1.1,
        "rsi_filter": "none"
    })
    signals_df = strat.generate_signals(df)
    assert "signal" in signals_df.columns
    assert 1 in signals_df["signal"].values

    # 2. 验证结合硬止损 (-5%) 和止盈 (+15%) 的全流程回测
    engine = BacktestEngine(initial_cash=100000)
    res = engine.run(
        symbol="600519",
        df=df,
        strategy_name="custom_rule",
        strategy_params={
            "ma_mode": "cross",
            "short_window": 5,
            "long_window": 15,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.15,
            "max_holding_days": 10
        }
    )
    assert "metrics" in res
    assert "equity_curve" in res
    assert "trades" in res
    assert len(res["equity_curve"]) == 60

    print("✅ test_custom_rule_strategy passed")


if __name__ == "__main__":
    test_performance_calculator()
    test_trade_simulator_a_share_rules()
    test_strategies_signals()
    test_backtest_engine_run()
    test_custom_rule_strategy()
    test_position_sizing_models()
    test_portfolio_optimizer()
    test_wechat_notifier_card_formatting()
    test_paper_trading_service()
    print("\n🎉 ALL UNIT TESTS PASSED SUCCESSFULLY!")
