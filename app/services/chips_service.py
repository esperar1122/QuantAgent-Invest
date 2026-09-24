"""
筹码分布与成本分析计算引擎 (CYQ - Cost Distribution Model)
基于历史日K线量价与换手率衰减模型（Turnover Decay Model），精准推算：
- 获利盘比例 (Profit Ratio)
- 全市场平均持仓成本 (Average Cost)
- 90% / 70% 筹码集中度与价格分布区间
- 筹码多峰/单峰形态识别
- 筹码价格直方图 (用于右侧筹码峰可视化)

算法要点：
1. 换手衰减模型：chips[t] = chips[t-1] * (1 - turnover_rate * decay_factor)
2. 三角分布注入：峰值取当日均价（VWAP 或四价均值），非收盘价
3. 成交量加权：新注入筹码量 = turnover_rate * volume，量能越大筹码越多
4. 一字涨跌停特殊处理：筹码归集到唯一价位
"""
import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_chips_distribution(
    kline_items: List[Dict[str, Any]],
    current_price: Optional[float] = None,
    bins_count: int = 100,
    decay_factor: float = 1.0,
    vis_bins: int = 40
) -> Optional[Dict[str, Any]]:
    """
    根据历史K线序列计算筹码分布数据

    Args:
        kline_items: 历史日K线列表，需包含 open, high, low, close, volume，可选 turnover_rate, amount
        current_price: 当前最新价（若为空则使用最后一根K线的close）
        bins_count: 内部计算价格分箱格点数，默认 100 个（提高精度）
        decay_factor: 衰减系数（通常 1.0），控制历史筹码衰减灵敏度
        vis_bins: 前端可视化输出直方图柱数，默认 40

    Returns:
        筹码分析诊断字典
    """
    if not kline_items or len(kline_items) < 5:
        return None

    try:
        df = pd.DataFrame(kline_items)
        for col in ["open", "close", "high", "low", "volume", "amount"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["close", "high", "low"])
        if df.empty or len(df) < 5:
            return None

        # 确保 volume 列存在且可用
        has_volume = "volume" in df.columns and df["volume"].notna().any()
        has_amount = "amount" in df.columns and df["amount"].notna().any()

        if current_price is None or current_price <= 0:
            current_price = float(df["close"].iloc[-1])

        p_min = float(df["low"].min()) * 0.98
        p_max = float(df["high"].max()) * 1.02
        if p_max <= p_min:
            return None

        # 构建价格分箱格点
        prices = np.linspace(p_min, p_max, bins_count)
        step = prices[1] - prices[0]
        chips = np.zeros(bins_count)

        # 换手衰减积分模型 (Turnover Decay & Triangle Distribution)
        for _, row in df.iterrows():
            l = float(row["low"])
            h = float(row["high"])
            c = float(row["close"])
            o = float(row.get("open", c))

            # 成交量
            vol = float(row["volume"]) if has_volume and pd.notna(row.get("volume")) else 1.0
            if vol <= 0:
                vol = 1.0

            # 当日均价（VWAP）：优先用 amount/volume，退化用四价均值
            if has_amount and pd.notna(row.get("amount")) and float(row["amount"]) > 0 and vol > 0:
                avg_price = float(row["amount"]) / vol
                # 均价合理性检查：应在 [low, high] 范围内
                avg_price = max(l, min(h, avg_price))
            else:
                avg_price = (o + c + h + l) / 4.0

            # 换手率：优先使用真实换手率；若无，估算为合理的常态换手
            turnover = row.get("turnover_rate")
            if turnover is not None and pd.notna(turnover) and float(turnover) > 0:
                # 换手率上限 80%（小盘股单日可达 60-80%）
                t = min(float(turnover) / 100.0, 0.80)
            else:
                # 默认基准换手 2.0%
                t = 0.02

            # 有效衰减率 = 换手率 * 衰减系数
            effective_decay = min(t * decay_factor, 0.95)

            # 1. 历史筹码按换手率衰减
            chips = chips * (1.0 - effective_decay)

            # 2. 当日新增筹码按三角分布注入
            #    三角分布：[low, high] 区间，峰值在均价 (avg_price)
            #    新增筹码总量 = effective_decay * volume（成交量加权）
            new_chip_amount = effective_decay * vol

            idx_low = max(0, int((l - p_min) / step))
            idx_high = min(bins_count - 1, int((h - p_min) / step))
            idx_avg = min(bins_count - 1, max(0, int((avg_price - p_min) / step)))

            # 一字涨/跌停板特殊处理：high ≈ low 时筹码归集到单一价位
            if idx_low >= idx_high:
                chips[idx_low] += new_chip_amount
            else:
                daily_weights = np.zeros(bins_count)
                for i in range(idx_low, idx_high + 1):
                    p = prices[i]
                    if avg_price <= l:
                        # 均价在低点，退化为递减分布
                        w = (h - p) / (h - l + 1e-9)
                    elif avg_price >= h:
                        # 均价在高点，退化为递增分布
                        w = (p - l) / (h - l + 1e-9)
                    elif p <= avg_price:
                        w = (p - l) / (avg_price - l + 1e-9)
                    else:
                        w = (h - p) / (h - avg_price + 1e-9)
                    daily_weights[i] = max(0.0, w)

                total_w = daily_weights.sum()
                if total_w > 0:
                    chips += (daily_weights / total_w) * new_chip_amount

        total_chips = chips.sum()
        if total_chips <= 0:
            return None

        # 归一化为百分比 (总和 100%)
        chips_pct = (chips / total_chips) * 100.0

        # 指标计算
        profit_mask = prices <= current_price
        profit_ratio = float(chips_pct[profit_mask].sum()) if profit_mask.any() else 0.0
        profit_ratio = max(0.0, min(100.0, profit_ratio))

        # 加权平均成本
        avg_cost = float((prices * chips_pct).sum() / 100.0)

        # 累积分布 (CDF) 用于精确求分位价格
        cdf = np.cumsum(chips_pct)

        p5 = float(np.interp(5.0, cdf, prices))
        p15 = float(np.interp(15.0, cdf, prices))
        p50 = float(np.interp(50.0, cdf, prices))
        p85 = float(np.interp(85.0, cdf, prices))
        p95 = float(np.interp(95.0, cdf, prices))

        # 集中度公式 (通达信标准)：(高界 - 低界) / (高界 + 低界) * 100%
        conc90 = ((p95 - p5) / (p95 + p5)) * 100.0 if (p95 + p5) > 0 else 0.0
        conc70 = ((p85 - p15) / (p85 + p15)) * 100.0 if (p85 + p15) > 0 else 0.0

        profit_premium = ((current_price - avg_cost) / avg_cost) * 100.0 if avg_cost > 0 else 0.0

        # 形态研判
        if profit_ratio >= 90.0:
            peak_pattern = "全员获利主升"
            pattern_desc = "获利盘比例超90%，无上方套牢阻力，持筹心态极佳；关注量能配合防范冲高回落。"
            pattern_type = "bullish"
        elif profit_ratio <= 10.0:
            peak_pattern = "深度超跌套牢"
            pattern_desc = "获利盘不足10%，全员深套割肉盘释放殆尽，做空动能衰竭，酝酿超跌反弹。"
            pattern_type = "bullish"
        elif conc70 <= 8.5 or conc90 <= 12.0:
            peak_pattern = "单峰高度密集"
            pattern_desc = f"筹码高度凝聚（70%集中度{conc70:.1f}%），主力吸筹控盘充分，面临突破变盘临界点。"
            pattern_type = "bullish" if current_price >= avg_cost else "neutral"
        elif abs(current_price - avg_cost) / avg_cost <= 0.025:
            peak_pattern = "成本线胶着博弈"
            pattern_desc = f"现价接近主力平均成本 (¥{avg_cost:.2f})，多空双方在成本中枢剧烈拉锯。"
            pattern_type = "neutral"
        elif current_price < avg_cost:
            peak_pattern = "上方阻力沉重"
            pattern_desc = f"现价低于平均成本 {abs(profit_premium):.1f}%，反弹至筹码密集峰易面临解套抛压。"
            pattern_type = "bearish"
        else:
            peak_pattern = "多峰震荡整理"
            pattern_desc = "筹码分布较分散，下方具备一定获利支撑，上方亦存在阶段性套牢阻力。"
            pattern_type = "neutral"

        # 构造供前端可视化的价格直方图 (区间合并法，无信息丢失)
        actual_vis = min(vis_bins, bins_count)
        histogram = []
        # 将 bins_count 个格点合并为 actual_vis 个区间
        bin_edges = np.linspace(0, bins_count, actual_vis + 1, dtype=int)
        for k in range(actual_vis):
            start_idx = bin_edges[k]
            end_idx = bin_edges[k + 1]
            if end_idx <= start_idx:
                end_idx = start_idx + 1
            # 区间内筹码百分比求和
            pct_sum = float(chips_pct[start_idx:end_idx].sum())
            # 区间中心价格
            mid_idx = (start_idx + end_idx - 1) // 2
            mid_price = float(prices[min(mid_idx, bins_count - 1)])
            histogram.append({
                "price": round(mid_price, 2),
                "percent": round(pct_sum, 2),
                "is_profit": mid_price <= current_price
            })

        return {
            "current_price": round(current_price, 2),
            "avg_cost": round(avg_cost, 2),
            "profit_ratio": round(profit_ratio, 1),
            "trapped_ratio": round(100.0 - profit_ratio, 1),
            "profit_premium": round(profit_premium, 2),
            "cost_range_90": [round(p5, 2), round(p95, 2)],
            "concentration_90": round(conc90, 1),
            "cost_range_70": [round(p15, 2), round(p85, 2)],
            "concentration_70": round(conc70, 1),
            "median_cost": round(p50, 2),
            "peak_pattern": peak_pattern,
            "pattern_desc": pattern_desc,
            "pattern_type": pattern_type,
            "histogram": histogram
        }

    except Exception as e:
        logger.error(f"筹码分布计算异常: {e}", exc_info=True)
        return None
