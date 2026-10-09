"""
量化交易科学与市场大数据回测验证脚本 (Empirical Backtest & Trading Science Verification)

对比两种范式在真实 A 股历史行情中的实证表现：
1. Baseline Model (旧版静态固定比例): 静态 -4% 抄底买点、静态 +8% 止盈、静态 -3% 止损，破位也硬给买点，主升浪设死靶子卖飞；
2. Dynamic ATR & Regime Model (新版 ATR 动态标尺 + 状态机 + 移动止盈 + 空安全):
   - 破位禁区强制空仓 (Null Safety)，拒绝接飞刀；
   - 主升浪动态移动跟踪止盈 (Trailing Stop)，不破 MA5 坚决持股待涨，防卖飞；
   - 良性回踩以 ATR 动态防守垫低吸。
"""

import sys
import os
import pandas as pd
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 将项目根目录加入 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.backtest.data_loader import load_backtest_data


def calculate_atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """计算标准真实波动幅度 ATR14"""
    high = df["high"]
    low = df["low"]
    prev_close = df["close"].shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=n).mean().bfill()


def get_board_profile(symbol: str, name: str = "") -> dict:
    """
    板块与涨跌幅限制超参数适配器：
    主板(10%)、双创(20%)、北交所(30%)、ST(5%)与ETF各具备差异化波动率分布与风控垫
    """
    clean_code = str(symbol).replace("sh", "").replace("sz", "").replace("bj", "")

    if "ST" in name:
        return {
            "type": "ST",
            "name": "ST风险警示 (±5%)",
            "limit_pct": 5,
            "atr_factor": 0.75,          # 极小涨跌幅，标尺收窄
            "bias_threshold": 3.0,
            "trailing_atr_k": 0.9,        # 紧跟 0.9x ATR
            "initial_stop_k": 0.85,       # 阶段一防洗盘 0.85x ATR
            "profit_trigger_k": 0.7,      # 阶段二触发阈值
        }
    if clean_code.startswith(("92", "83", "43", "87")):
        return {
            "type": "BSE",
            "name": "北交所 (±30%)",
            "limit_pct": 30,
            "atr_factor": 1.50,          # 30cm 波动极大，标尺适度放大
            "bias_threshold": 8.5,
            "trailing_atr_k": 2.0,        # 移动止盈缓冲 2.0x ATR
            "initial_stop_k": 1.8,        # 阶段一防洗盘 1.8x ATR
            "profit_trigger_k": 1.5,      # 阶段二触发阈值
        }
    if clean_code.startswith(("300", "301", "688")):
        return {
            "type": "20CM",
            "name": "创业板/科创板 (±20%)",
            "limit_pct": 20,
            "atr_factor": 1.25,          # 20cm 弹性标尺 1.25x
            "bias_threshold": 6.5,
            "trailing_atr_k": 1.6,        # 移动止盈缓冲 1.6x ATR
            "initial_stop_k": 1.5,        # 阶段一防洗盘 1.5x ATR
            "profit_trigger_k": 1.1,      # 阶段二触发阈值
        }
    if clean_code.startswith(("51", "15", "58", "56")):
        return {
            "type": "ETF",
            "name": "场内ETF组合 (低波)",
            "limit_pct": 10,
            "atr_factor": 0.85,          # 一篮子组合消除特异风险，标尺收紧
            "bias_threshold": 2.8,
            "trailing_atr_k": 1.0,        # 移动止盈缓冲 1.0x ATR
            "initial_stop_k": 1.0,        # 阶段一防洗盘 1.0x ATR
            "profit_trigger_k": 0.8,      # 阶段二触发阈值
        }
    return {
        "type": "MAIN",
        "name": "主板常规 (±10%)",
        "limit_pct": 10,
        "atr_factor": 1.00,          # 10cm 标准标尺 1.0x
        "bias_threshold": 4.5,
        "trailing_atr_k": 1.3,        # 阶段二移动止盈缓冲 1.3x ATR
        "initial_stop_k": 1.2,        # 阶段一防洗盘 1.2x ATR
        "profit_trigger_k": 1.0,      # 阶段二触发阈值 (脱离成本区 1.0x ATR)
    }


def simulate_fixed_baseline(df: pd.DataFrame, initial_capital: float = 200000.0) -> dict:
    """
    模型 A：旧版固定乘数静态模型
    规则：
    - 买入：在均线下方静态下浮 4% (px * 0.96) 或死叉阴跌时依然硬挂买点；
    - 卖点：达到成本 +8% 强制全部止盈（死靶子，易卖飞）；
    - 止损：跌破买入价 -3.5% 强制止损；
    - 缺陷：破位阴跌通道依然不断试探抄底接飞刀。
    """
    data = df.copy().reset_index(drop=True)
    n = len(data)
    capital = initial_capital
    position = 0
    entry_price = 0.0
    trades = []
    equity_curve = [initial_capital]

    # 计算 5日均线与 10日均线
    data["ma5"] = data["close"].rolling(5).mean()
    data["ma10"] = data["close"].rolling(10).mean()

    for i in range(10, n):
        row = data.iloc[i]
        prev = data.iloc[i - 1]
        close = row["close"]
        high = row["high"]
        low = row["low"]
        date = row["date"]

        if position == 0:
            # 旧版逻辑：只要触碰或回踩（哪怕处于破位死叉下行通道），依然给出买点并开仓
            is_dip = (low <= prev["close"] * 0.96) or (prev["ma5"] < prev["ma10"] and close < prev["ma5"])
            if is_dip:
                entry_price = close
                position = int(capital // (entry_price * 100)) * 100
                if position >= 100:
                    capital -= position * entry_price
        else:
            # 持仓中：检查固定 +8% 止盈 或 -3.5% 止损
            gain_pct = (high - entry_price) / entry_price
            loss_pct = (low - entry_price) / entry_price

            hit_tp = gain_pct >= 0.08
            hit_sl = loss_pct <= -0.035

            if hit_tp:
                exit_price = entry_price * 1.08
                pnl = position * (exit_price - entry_price)
                capital += position * exit_price
                trades.append({"pnl": pnl, "pct": 8.0, "type": "tp", "entry": entry_price, "exit": exit_price, "date": date})
                position = 0
            elif hit_sl:
                exit_price = entry_price * 0.965
                pnl = position * (exit_price - entry_price)
                capital += position * exit_price
                trades.append({"pnl": pnl, "pct": -3.5, "type": "sl", "entry": entry_price, "exit": exit_price, "date": date})
                position = 0

        current_val = capital + (position * close if position > 0 else 0)
        equity_curve.append(current_val)

    # 结算最后剩余持仓
    if position > 0:
        last_price = data.iloc[-1]["close"]
        capital += position * last_price
        pnl = position * (last_price - entry_price)
        trades.append({"pnl": pnl, "pct": ((last_price - entry_price) / entry_price) * 100, "type": "close", "date": data.iloc[-1]["date"]})

    return calculate_metrics("旧版静态固定比例模型", initial_capital, capital, trades, equity_curve)


def simulate_dynamic_atr_regime(
    df: pd.DataFrame,
    symbol: str = "",
    name: str = "",
    initial_capital: float = 200000.0
) -> dict:
    """
    模型 B：新版 ATR 动态波动标尺 + 五大状态机 + 两阶段防洗盘移动跟踪止盈 + 空安全
    规则：
    1. 板块超参数自适应适配：主板(10%)、双创(20%)、北交所(30%)与ETF自适应缩放 ATR 标尺与系数。
    2. 状态机识别：
       - DOWNWARD_TREND: ma5 < ma10 且 close < ma10 -> 买点为 NULL，坚决不开仓（空安全防御）！
       - STRONG_MOMENTUM: ma5 >= ma10 且 close >= ma5 -> 顺势做多，开启两阶段 Trailing Stop 移动止盈！
       - PULLBACK_SETUP: 缩量回踩 ma10 或支撑位 -> 动态 ATR 止损低吸。
    3. 两阶段止盈防抖机制 (Two-Phase Execution)：
       - 阶段 1 (试仓/蓄势初期): 维持初始宽止损 initial_stop_k * ATR，防范早盘前 15 分钟毛刺假摔；
       - 阶段 2 (脱离成本区): 浮盈超过 profit_trigger_k * ATR 后，正式激活紧身移动止盈线：
         trailing_stop = max(保本线, 最高价 - trailing_atr_k * ATR, ma5 * 0.995)，随新高逐日爬升，彻底防卖飞！
    """
    data = df.copy().reset_index(drop=True)
    n = len(data)

    profile = get_board_profile(symbol, name)
    data["raw_atr"] = calculate_atr(data, 14)
    data["atr"] = data["raw_atr"] * profile["atr_factor"]
    data["ma5"] = data["close"].rolling(5).mean()
    data["ma10"] = data["close"].rolling(10).mean()
    data["ma20"] = data["close"].rolling(20).mean()

    capital = initial_capital
    position = 0
    entry_price = 0.0
    highest_after_entry = 0.0
    trades = []
    equity_curve = [initial_capital]

    for i in range(15, n):
        row = data.iloc[i]
        prev = data.iloc[i - 1]
        close = row["close"]
        high = row["high"]
        low = row["low"]
        atr = row["atr"]
        ma5 = row["ma5"]
        ma10 = row["ma10"]
        date = row["date"]

        # 状态判定
        is_downward = (ma5 < ma10) and (close < ma10)
        is_strong_momentum = (ma5 >= ma10) and (close >= ma5) and (row["close"] > prev["close"])
        is_pullback = (close >= ma10 * 0.985) and (abs(close - ma10) / close <= 0.02) and not is_downward

        if position == 0:
            if is_downward:
                # 破位阴跌防守禁区 -> 买点 NULL，强制空仓观望，绝不接飞刀！
                pass
            elif is_strong_momentum or is_pullback:
                # 顺势突破或良性回踩开仓
                entry_price = close
                highest_after_entry = high
                position = int(capital // (entry_price * 100)) * 100
                if position >= 100:
                    capital -= position * entry_price
        else:
            # 持仓中：动态跟踪入场后的最高价
            highest_after_entry = max(highest_after_entry, high)
            gain_from_entry_atr = (highest_after_entry - entry_price) / max(0.001, atr)

            # -----------------------------------------------------------------
            # 两阶段止盈防抖逻辑 (Two-Phase Execution)
            # -----------------------------------------------------------------
            initial_stop = entry_price - profile["initial_stop_k"] * atr
            is_phase2 = gain_from_entry_atr >= profile["profit_trigger_k"]

            if is_phase2:
                # 阶段 2：已确认脱离成本区，启动紧身移动止盈线 (锁定利润 + 追随新高)
                trailing_stop = max(
                    entry_price * 1.002,                       # 保本线
                    highest_after_entry - profile["trailing_atr_k"] * atr,  # 动态ATR移动回撤线
                    ma5 * 0.995 if ma5 else entry_price        # MA5 攻击线托底
                )
                current_defense = max(initial_stop, trailing_stop)
            else:
                # 阶段 1：蓄势/建仓初期，执行板块专属宽止损，容忍早盘杂波假摔
                current_defense = initial_stop

            # 离场判断：收盘击穿当前防守线
            if close <= current_defense:
                exit_price = min(row["open"], close)
                pnl = position * (exit_price - entry_price)
                pct = ((exit_price - entry_price) / entry_price) * 100
                capital += position * exit_price
                trades.append({
                    "pnl": pnl,
                    "pct": pct,
                    "type": f"phase{2 if is_phase2 else 1}_{'trailing' if pct > 0 else 'stop'}",
                    "phase": 2 if is_phase2 else 1,
                    "entry": entry_price,
                    "exit": exit_price,
                    "date": date
                })
                position = 0

        current_val = capital + (position * close if position > 0 else 0)
        equity_curve.append(current_val)

    # 结算最后剩余持仓
    if position > 0:
        last_price = data.iloc[-1]["close"]
        capital += position * last_price
        pnl = position * (last_price - entry_price)
        pct = ((last_price - entry_price) / entry_price) * 100
        trades.append({"pnl": pnl, "pct": pct, "type": "close", "phase": 2, "date": data.iloc[-1]["date"]})

    return calculate_metrics(f"新版 ATR 动态状态机 ({profile['name']})", initial_capital, capital, trades, equity_curve)


def calculate_metrics(name: str, initial: float, final: float, trades: list, equity_curve: list) -> dict:
    """计算标准量化绩效指标"""
    total_return = ((final - initial) / initial) * 100
    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    total_trades = len(trades)
    win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0.0

    avg_win = np.mean([t["pct"] for t in wins]) if wins else 0.0
    avg_loss = abs(np.mean([t["pct"] for t in losses])) if losses else 0.0
    profit_loss_ratio = (avg_win / avg_loss) if avg_loss > 0 else (avg_win if avg_win > 0 else 0.0)

    # 最大回撤 (Max Drawdown)
    eq = np.array(equity_curve)
    peaks = np.maximum.accumulate(eq)
    drawdowns = (peaks - eq) / peaks
    max_drawdown = np.max(drawdowns) * 100 if len(drawdowns) > 0 else 0.0

    # 单笔数学期望 (Expectancy per trade)
    expectancy = (win_rate / 100 * avg_win) - ((100 - win_rate) / 100 * avg_loss)

    # 最大单笔盈利 (Max single win)
    max_win = max([t["pct"] for t in trades]) if trades else 0.0

    return {
        "name": name,
        "initial": initial,
        "final": final,
        "total_return": total_return,
        "total_trades": total_trades,
        "win_rate": win_rate,
        "profit_loss_ratio": profit_loss_ratio,
        "max_drawdown": max_drawdown,
        "expectancy": expectancy,
        "max_win": max_win,
        "avg_win": avg_win,
        "avg_loss": avg_loss
    }


def run_benchmark():
    test_symbols = [
        {"code": "601127", "name": "赛力斯 (主板 10% · 主升龙头)"},
        {"code": "300308", "name": "中际旭创 (创业板 20% · 高弹性算力)"},
        {"code": "510300", "name": "300ETF (场内ETF · 低波组合)"},
        {"code": "002594", "name": "比亚迪 (主板 10% · 行业权重)"},
        {"code": "600519", "name": "贵州茅台 (主板 10% · 核心蓝筹)"}
    ]

    print("=" * 80)
    print(" 真实市场历史大数据回测验证：旧版固定乘数 vs 新版 ATR 板块自适应与两阶段止盈")
    print("=" * 80)

    for item in test_symbols:
        code = item["code"]
        name = item["name"]
        try:
            df = load_backtest_data(code)
            if df is None or len(df) < 50:
                print(f"[-] {name} 数据不足，跳过")
                continue

            prof = get_board_profile(code, name)
            res_a = simulate_fixed_baseline(df, initial_capital=200000.0)
            res_b = simulate_dynamic_atr_regime(df, symbol=code, name=name, initial_capital=200000.0)

            print(f"\n【标的评估】: {name} ({code}) | 所属板块: {prof['name']} (ATR标尺: {prof['atr_factor']}x, 跟踪K: {prof['trailing_atr_k']})")
            print(f"回测样本: {len(df)} 根真实日K线 (区间: {df.iloc[0]['date']} ~ {df.iloc[-1]['date']}) | 初始本金: ¥200,000")
            print("-" * 80)
            print(f"{'量化绩效指标':<22} | {'旧版静态固定比例模型':<22} | {'新版 ATR 动态状态机模型':<22} | {'提升优势':<12}")
            print("-" * 80)
            print(f"{'累计收益率 (Total Return)':<20} | {res_a['total_return']:>+18.2f}% | {res_b['total_return']:>+18.2f}% | {res_b['total_return'] - res_a['total_return']:>+10.2f}%")
            print(f"{'最大回撤 (Max Drawdown)':<22} | {res_a['max_drawdown']:>18.2f}% | {res_b['max_drawdown']:>18.2f}% | {res_a['max_drawdown'] - res_b['max_drawdown']:>+10.2f}% (回撤改善)")
            print(f"{'交易胜率 (Win Rate)':<24} | {res_a['win_rate']:>18.2f}% | {res_b['win_rate']:>18.2f}% | {res_b['win_rate'] - res_a['win_rate']:>+10.2f}%")
            print(f"{'盈亏比 (Profit/Loss Ratio)':<22} | {res_a['profit_loss_ratio']:>18.2f}:1 | {res_b['profit_loss_ratio']:>18.2f}:1 | {res_b['profit_loss_ratio'] - res_a['profit_loss_ratio']:>+10.2f}")
            print(f"{'单笔期望收益 (Expectancy)':<20} | {res_a['expectancy']:>+18.2f}% | {res_b['expectancy']:>+18.2f}% | {res_b['expectancy'] - res_a['expectancy']:>+10.2f}%")
            print(f"{'单笔最大盈利 (Max Win)':<22} | {res_a['max_win']:>18.2f}% | {res_b['max_win']:>18.2f}% | {'突破8%卖飞' if res_b['max_win'] > 8.0 else '持平'}")
            print(f"{'总交易笔数 (Trades)':<24} | {res_a['total_trades']:>18}笔 | {res_b['total_trades']:>18}笔 | {'过滤无效杂波' if res_b['total_trades'] < res_a['total_trades'] else '平稳'}")
            print("-" * 80)

        except Exception as e:
            print(f"[!] 标的 {name} 回测出错: {e}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    run_benchmark()
