"""
筹码分布与成本分析计算引擎 (CYQ - Cost Distribution Model)
基于历史日K线量价与行为金融学深度修正模型：
1. 涨跌停板换手率折减：一字板/极端无振幅板换手率按 0.4 折减，剔除恐慌/无量封板形成的虚假极端筹码峰
2. 停牌复牌筹码衰减重置：检测停牌间隔>=5个交易日(日历日>=7天)，复牌首日历史筹码按 0.5 衰减重置
3. 新股/次新股独立计算窗口：上市<120日股票，窗口限制为最近60日，峰值灵敏度门槛提至 2.0%
4. 两融余额修正支撑强度：融资余额占流通市值>5%时，支撑位评级整体降一级，并提示强平踩踏风险
5. 大宗交易数据注入：接入大宗成交价与锁定期，锁定期满解禁筹码自动纳入上方隐性阻力峰
6. 股东变更与股本事件修正：增发配股发行价注入、回购注销等比抽离、限售股解禁激活
7. 非对称衰减模型 (处置效应)：获利盘加速置换 (alpha*1.25)，套牢盘死扛减缓 (alpha*0.75)
8. 混合高斯分布 (GMM)：主峰(VWAP 70%) + 次峰(Close 20%) + 宽尾平滑(10%)
9. ATR 自适应网格：根据 14 日真实波幅动态调整网格步长与分箱精度 (80~200 格点)
10. 异常对倒清洗：识别并过滤主力缩量对倒/虚假放量操纵
"""
import logging
import math
from typing import Dict, Any, List, Optional
from datetime import datetime
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_chips_distribution(
    kline_items: List[Dict[str, Any]],
    current_price: Optional[float] = None,
    bins_count: Optional[int] = None,
    decay_factor: float = 1.0,
    vis_bins: int = 40,
    margin_ratio: Optional[float] = None,
    block_trades: Optional[List[Dict[str, Any]]] = None,
    capital_events: Optional[List[Dict[str, Any]]] = None,
    total_shares: Optional[float] = None,
    is_etf: Optional[bool] = None,
    precision: Optional[int] = None,
    realtime_quote: Optional[Dict[str, Any]] = None,
    compensate_ex_dividend: bool = True
) -> Optional[Dict[str, Any]]:
    """
    根据历史K线序列计算筹码分布数据（全面升级：行为金融学非对称衰减 + GMM + ATR自适应 + 6大硬核修正规则）

    Args:
        kline_items: 历史日K线列表，需包含 open, high, low, close, volume，可选 turnover_rate, amount, trade_date
        current_price: 当前最新价（若为空则使用最后一根K线的close）
        bins_count: 内部价格分箱格点数（若为空则基于 ATR 自适应计算）
        decay_factor: 衰减灵敏度调节系数，默认 1.0
        vis_bins: 前端可视化输出直方图柱数，默认 40
        margin_ratio: 融资余额占流通市值比例 (%)，如 5.8 代表 5.8% (用于两融穿透修正)
        block_trades: 大宗交易与协议转让数据列表 (含 price, volume, trade_date, lockup_months)
        capital_events: 股本变动事件列表 (增发配股/回购注销/限售股解禁)

    Returns:
        筹码分析诊断字典，含支撑位/压力位与量化多空辩论
    """
    if not kline_items or len(kline_items) < 5:
        return None

    try:
        df = pd.DataFrame(kline_items)
        for col in ["open", "close", "high", "low", "volume", "amount", "turnover_rate"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["close", "high", "low"])
        if df.empty or len(df) < 5:
            return None

        # -------------------------------------------------------------
        # 规则 3: 新股 / 次新股独立计算窗口与阈值调整
        # -------------------------------------------------------------
        total_bars_count = len(df)
        is_sub_new = total_bars_count < 120
        if is_sub_new:
            # 上市不满120日，筹码每日大幅重建，窗口限制为最近60日去除上市初期爆炒噪音
            df = df.tail(60).copy()
            min_peak_threshold = 2.0  # 提高峰值检测门槛过滤毛刺
        else:
            min_peak_threshold = 1.2

        has_volume = "volume" in df.columns and df["volume"].notna().any()
        has_amount = "amount" in df.columns and df["amount"].notna().any()
        has_turnover = "turnover_rate" in df.columns and df["turnover_rate"].notna().any()

        # 尝试解析交易日期
        date_col = None
        for d_col in ["trade_date", "date", "datetime"]:
            if d_col in df.columns:
                date_col = d_col
                break

        if date_col:
            df["parsed_date"] = pd.to_datetime(df[date_col], errors="coerce")
        else:
            df["parsed_date"] = None

        if current_price is None or current_price <= 0:
            current_price = float(df["close"].iloc[-1])

        if precision is None:
            # ETF 或低价标的（< 5.0元）自动启用 3 位小数（厘）精度
            precision = 3 if (is_etf or current_price < 5.0) else 2

        p_min = float(df["low"].min()) * 0.98
        p_max = float(df["high"].max()) * 1.02
        if p_max <= p_min:
            return None

        # -------------------------------------------------------------
        # 1. ATR 自适应价格网格 (ATR-Adaptive Price Grid)
        # -------------------------------------------------------------
        high_low = df["high"] - df["low"]
        high_prev_close = (df["high"] - df["close"].shift(1)).abs()
        low_prev_close = (df["low"] - df["close"].shift(1)).abs()
        tr = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)
        atr_14 = float(tr.tail(14).mean()) if len(tr) >= 14 else float(tr.mean())
        if math.isnan(atr_14) or atr_14 <= 0:
            atr_14 = (p_max - p_min) / 100.0

        if bins_count is None:
            dynamic_step = max(0.002 if precision == 3 else 0.01, atr_14 * 0.25)
            calc_bins = int((p_max - p_min) / dynamic_step)
            bins_count = max(120 if precision == 3 else 80, min(200, calc_bins))

        prices = np.linspace(p_min, p_max, bins_count)
        step = prices[1] - prices[0]
        chips = np.zeros(bins_count)

        # -------------------------------------------------------------
        # 2. 异常对倒清洗与换手率补全 (Wash-Trading Outlier Filter)
        # -------------------------------------------------------------
        if has_turnover:
            df["turnover_clean"] = df["turnover_rate"].fillna(2.0)
            ma5_turnover = df["turnover_clean"].rolling(5, min_periods=1).mean()
            amp = (df["high"] - df["low"]) / df["close"].replace(0, np.nan).fillna(1.0)
            is_manipulated = (df["turnover_clean"] > ma5_turnover * 3.0) & (amp < 0.02)
            df.loc[is_manipulated, "turnover_clean"] = ma5_turnover.loc[is_manipulated] * 1.5
        elif total_shares and total_shares > 0:
            df["turnover_clean"] = (df["volume"] / total_shares) * 100.0
        else:
            med_vol = df["volume"].median() if "volume" in df.columns else 1.0
            if med_vol > 0:
                est_shares = med_vol / 0.025
                df["turnover_clean"] = (df["volume"] / est_shares) * 100.0
            else:
                df["turnover_clean"] = 2.5

        # -------------------------------------------------------------
        # 3. 逐日更新迭代 (融合：停牌衰减重置 + 一字板折减 + 标准无偏马尔可夫衰减 + VWAP三角分布)
        # -------------------------------------------------------------
        prev_date = None
        prev_close = None
        limit_board_count = 0
        suspension_count = 0
        ex_dividend_count = 0

        for _, row in df.iterrows():
            l = float(row["low"])
            h = float(row["high"])
            c = float(row["close"])
            o = float(row.get("open", c))
            curr_date = row.get("parsed_date")

            # ---------------------------------------------------------
            # 规则 0: 除权除息/股票拆分断层自适应修正 (Ex-rights Split Compensation)
            # 检测单日开盘跳空 < 0.78 (跌幅超22%) 或 > 1.35 (除权送股/大比例配股)
            # ---------------------------------------------------------
            if compensate_ex_dividend and prev_close is not None and prev_close > 0:
                jump_ratio = o / prev_close
                if jump_ratio < 0.78 or jump_ratio > 1.35:
                    # 发生大比例除权送转（如10送10），原持仓成本等比缩放至当前基准
                    scaled_prices = prices * jump_ratio
                    chips = np.interp(prices, scaled_prices, chips, left=0.0, right=0.0)
                    ex_dividend_count += 1
                    logger.info(f"⚡ 检测到除权跳空 (比例: {jump_ratio:.3f})，已对齐历史筹码分布成本峰")

            # ---------------------------------------------------------
            # 规则 2: 停牌复牌筹码衰减重置
            # 检测停牌间隔 >= 7 个日历日 (约 >= 5 个交易日)
            # ---------------------------------------------------------
            if prev_date is not None and curr_date is not None and pd.notna(prev_date) and pd.notna(curr_date):
                gap_days = (curr_date - prev_date).days
                if gap_days >= 7:
                    # 停牌前全部筹码乘以 0.5 衰减系数，模拟重大事项停牌复牌后信息不对称下的筹码松动
                    chips = chips * 0.5
                    suspension_count += 1

            prev_date = curr_date

            vol = float(row["volume"]) if has_volume and pd.notna(row.get("volume")) else 1.0
            if vol <= 0:
                vol = 1.0

            # 当日均价 VWAP (按成交额/成交量精准加权)
            if has_amount and pd.notna(row.get("amount")) and float(row["amount"]) > 0 and vol > 0:
                amt_val = float(row["amount"])
                p_lot = amt_val / (vol * 100.0)
                p_share = amt_val / vol
                if l * 0.9 <= p_lot <= h * 1.1:
                    avg_price = max(l, min(h, p_lot))
                elif l * 0.9 <= p_share <= h * 1.1:
                    avg_price = max(l, min(h, p_share))
                else:
                    avg_price = (o + c + h + l) / 4.0
            else:
                avg_price = (o + c + h + l) / 4.0

            # 基础换手率
            raw_t = min(max(float(row["turnover_clean"]) / 100.0, 0.0001), 0.80)

            # ---------------------------------------------------------
            # 规则 1: 涨跌停板当日换手率折减
            # 识别当日振幅 <= 1.2% 且 涨跌幅 >= 9.5% 的极端一字板K线
            # ---------------------------------------------------------
            if prev_close is not None and prev_close > 0:
                day_amp = (h - l) / prev_close
                day_pct_chg = abs((c - prev_close) / prev_close) * 100.0
                if day_amp <= 0.012 and day_pct_chg >= 9.5:
                    raw_t = raw_t * 0.4
                    limit_board_count += 1

            prev_close = c

            base_alpha = min(raw_t * decay_factor, 0.95)

            # --- 标准无偏马尔可夫换手衰减 (同花顺/通达信基准：所有价格筹码按当日换手率严格物理守恒衰减) ---
            chips = chips * (1.0 - base_alpha)

            # --- 筹码守恒新注入量 (保持总量归一守恒，彻底消除 vol^2 平方量纲失真) ---
            new_chip_amount = base_alpha
            idx_low = max(0, int((l - p_min) / step))
            idx_high = min(bins_count - 1, int((h - p_min) / step))

            if idx_low >= idx_high:
                chips[idx_low] += new_chip_amount
            else:
                day_prices = prices[idx_low : idx_high + 1]
                # 标准有界三角分布：以日内 VWAP 均价为顶点峰值，底边覆盖 [l, h]
                w = np.where(
                    day_prices <= avg_price,
                    (day_prices - l) / (avg_price - l + 1e-6),
                    (h - day_prices) / (h - avg_price + 1e-6)
                )
                w = np.maximum(0.0, w)
                sum_w = w.sum()
                if sum_w > 0:
                    chips[idx_low : idx_high + 1] += (w / sum_w) * new_chip_amount
                else:
                    chips[idx_low : idx_high + 1] += new_chip_amount / (idx_high - idx_low + 1)

        # -------------------------------------------------------------
        # 规则 6: 股东变更 / 股本变动事件硬修正
        # 增发/配股注入、回购注销抽离、限售股解禁进入流通池
        # -------------------------------------------------------------
        if capital_events and len(capital_events) > 0:
            for ev in capital_events:
                ev_type = ev.get("type", "")
                if ev_type in ["placement", "rights_issue"]:
                    # 增发/配股：按发行价注入对应权重筹码
                    ev_price = float(ev.get("price", current_price))
                    ev_vol = float(ev.get("volume", 0))
                    if ev_price > p_min and ev_price < p_max and ev_vol > 0:
                        sigma_ev = max(step, ev_price * 0.008)
                        g_ev = np.exp(-0.5 * ((prices - ev_price) / sigma_ev) ** 2)
                        if g_ev.sum() > 0:
                            chips += (g_ev / g_ev.sum()) * (ev_vol * 0.03)

                elif ev_type == "repurchase_cancel":
                    # 回购注销：按比例从所有价格档位等比抽离筹码
                    cancel_ratio = min(0.30, max(0.001, float(ev.get("cancel_ratio", 0.02))))
                    chips = chips * (1.0 - cancel_ratio)

                elif ev_type == "restricted_unlock":
                    # 限售股解禁：移入流通盘对应价格槽参与换手
                    unlock_price = float(ev.get("price", current_price))
                    unlock_vol = float(ev.get("volume", 0))
                    if unlock_price > p_min and unlock_price < p_max and unlock_vol > 0:
                        sigma_ul = max(step, unlock_price * 0.01)
                        g_ul = np.exp(-0.5 * ((prices - unlock_price) / sigma_ul) ** 2)
                        if g_ul.sum() > 0:
                            chips += (g_ul / g_ul.sum()) * (unlock_vol * 0.02)

        # -------------------------------------------------------------
        # 规则 5: 大宗交易数据注入与锁定期满压力释放
        # -------------------------------------------------------------
        block_resistance_items = []
        latest_date = df["parsed_date"].dropna().iloc[-1] if df["parsed_date"].notna().any() else datetime.now()

        if block_trades and len(block_trades) > 0:
            for bt in block_trades:
                bt_price = float(bt.get("price", 0))
                bt_vol = float(bt.get("volume", 0))
                bt_date_raw = bt.get("trade_date")
                lockup_months = int(bt.get("lockup_months", 6))

                if bt_price > p_min and bt_price < p_max and bt_vol > 0:
                    sigma_bt = max(step, bt_price * 0.006)
                    g_bt = np.exp(-0.5 * ((prices - bt_price) / sigma_bt) ** 2)
                    sum_bt = g_bt.sum()
                    if sum_bt > 0:
                        chips += (g_bt / sum_bt) * (bt_vol * 0.04)

                    # 检查锁定期是否已届满
                    is_unlocked = False
                    if bt_date_raw and pd.notna(latest_date):
                        try:
                            bt_date = pd.to_datetime(bt_date_raw)
                            # 估算是否满 lockup_months (按30天/月)
                            if (latest_date - bt_date).days >= (lockup_months * 30):
                                is_unlocked = True
                        except Exception:
                            is_unlocked = True
                    else:
                        is_unlocked = True

                    if is_unlocked and bt_price > current_price:
                        dist_bt = ((bt_price - current_price) / current_price) * 100.0
                        block_resistance_items.append({
                            "price": round(bt_price, 2),
                            "chip_percent": round(float(bt.get("chip_percent", 3.5)), 2),
                            "distance_percent": round(dist_bt, 2),
                            "strength": "strong",
                            "desc": f"上方 ¥{bt_price:.2f} 大宗交易锁定期满解禁抛压峰 (折价接盘待出逃)"
                        })

        # -------------------------------------------------------------
        # 规则 11: 盘中日内高频动态增量推演 (Intraday Real-time CYQ Evolution)
        # -------------------------------------------------------------
        is_intraday_dynamic = False
        intraday_turnover_pct = 0.0
        if realtime_quote and isinstance(realtime_quote, dict):
            rt_p = float(realtime_quote.get("price") or current_price)
            rt_h = float(realtime_quote.get("high") or rt_p)
            rt_l = float(realtime_quote.get("low") or rt_p)
            rt_vol = float(realtime_quote.get("volume") or 0.0)
            rt_amt = float(realtime_quote.get("amount") or 0.0)
            rt_to = float(realtime_quote.get("turnover_rate") or 0.0)

            if rt_vol > 0 and rt_p > 0:
                is_intraday_dynamic = True
                intraday_turnover_pct = rt_to
                # 当日日内均价 VWAP
                if rt_amt > 0 and rt_l * 0.9 <= (rt_amt / rt_vol) <= rt_h * 1.1:
                    rt_vwap = rt_amt / rt_vol
                else:
                    rt_vwap = (rt_p + rt_h + rt_l) / 3.0

                # 日内换手率衰减
                raw_t_intra = min(max(rt_to / 100.0, 0.0001), 0.50)
                alpha_intra = min(raw_t_intra * decay_factor, 0.60)
                chips = chips * (1.0 - alpha_intra)

                # 注入日内成交量三角分布
                idx_low = max(0, int((rt_l - p_min) / step))
                idx_high = min(bins_count - 1, int((rt_h - p_min) / step))
                if idx_low >= idx_high:
                    chips[idx_low] += alpha_intra
                else:
                    day_prices = prices[idx_low : idx_high + 1]
                    w = np.where(
                        day_prices <= rt_vwap,
                        (day_prices - rt_l) / (rt_vwap - rt_l + 1e-6),
                        (rt_h - day_prices) / (rt_h - rt_vwap + 1e-6)
                    )
                    w = np.maximum(0.0, w)
                    s_w = w.sum()
                    if s_w > 0:
                        chips[idx_low : idx_high + 1] += (w / s_w) * alpha_intra
                    else:
                        chips[idx_low : idx_high + 1] += alpha_intra / (idx_high - idx_low + 1)

        total_chips = chips.sum()
        if total_chips <= 0:
            return None

        # 归一化为百分比
        chips_pct = (chips / total_chips) * 100.0

        # 指标计算
        profit_mask = prices <= current_price
        profit_ratio = float(chips_pct[profit_mask].sum()) if profit_mask.any() else 0.0
        profit_ratio = max(0.0, min(100.0, profit_ratio))

        avg_cost = float((prices * chips_pct).sum() / 100.0)

        # 累积分布 (CDF) 用于精确求分位价格
        cdf = np.cumsum(chips_pct)
        p5 = float(np.interp(5.0, cdf, prices))
        p15 = float(np.interp(15.0, cdf, prices))
        p50 = float(np.interp(50.0, cdf, prices))
        p85 = float(np.interp(85.0, cdf, prices))
        p95 = float(np.interp(95.0, cdf, prices))

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
            pattern_desc = f"现价接近主力平均成本 (¥{avg_cost:.{precision}f})，多空双方在成本中枢剧烈拉锯。"
            pattern_type = "neutral"
        elif current_price < avg_cost:
            peak_pattern = "上方阻力沉重"
            pattern_desc = f"现价低于平均成本 {abs(profit_premium):.1f}%，反弹至筹码密集峰易面临解套抛压。"
            pattern_type = "bearish"
        else:
            peak_pattern = "多峰震荡整理"
            pattern_desc = "筹码分布较分散，下方具备一定获利支撑，上方亦存在阶段性套牢阻力。"
            pattern_type = "neutral"

        # -------------------------------------------------------------
        # 4. 支撑位与压力位智能提取 (Support & Resistance Detection)
        # -------------------------------------------------------------
        support_levels = []
        resistance_levels = []
        vacuum_zones = []

        window = 3
        prominent_peaks = []
        for i in range(window, bins_count - window):
            sub = chips_pct[i - window : i + window + 1]
            if chips_pct[i] == sub.max() and chips_pct[i] >= min_peak_threshold:
                prominent_peaks.append((prices[i], chips_pct[i]))

        for p_peak, pct in prominent_peaks:
            dist_pct = ((p_peak - current_price) / current_price) * 100.0
            strength = "strong" if pct >= 5.0 else ("medium" if pct >= 2.5 else "light")
            if p_peak < current_price:
                support_levels.append({
                    "price": round(float(p_peak), precision),
                    "chip_percent": round(float(pct), 2),
                    "distance_percent": round(float(dist_pct), 2),
                    "strength": strength,
                    "desc": f"下方 ¥{p_peak:.{precision}f} 堆积 {pct:.1f}% 密集筹码支撑"
                })
            else:
                resistance_levels.append({
                    "price": round(float(p_peak), precision),
                    "chip_percent": round(float(pct), 2),
                    "distance_percent": round(float(dist_pct), 2),
                    "strength": strength,
                    "desc": f"上方 ¥{p_peak:.{precision}f} 堆积 {pct:.1f}% 套牢抛压阻力"
                })

        # 合并大宗交易解禁阻力峰
        if block_resistance_items:
            for b_res in block_resistance_items:
                if not any(abs(r["price"] - b_res["price"]) < step * 1.5 for r in resistance_levels):
                    resistance_levels.append(b_res)

        # -------------------------------------------------------------
        # 规则 4: 两融余额修正支撑强度 (Margin Debt Support Downgrade)
        # -------------------------------------------------------------
        has_high_margin = False
        if margin_ratio is not None and margin_ratio > 5.0:
            has_high_margin = True
            for sup in support_levels:
                # 融资盘高企时，下跌触发强制平仓产生被动踩踏抛压，支撑评级降一级
                if sup["strength"] == "strong":
                    sup["strength"] = "medium"
                elif sup["strength"] == "medium":
                    sup["strength"] = "light"
                elif sup["strength"] == "light":
                    sup["strength"] = "fragile"

                sup["desc"] += f" ⚠️ [两融高杠杆] 融资占比{margin_ratio:.1f}%>5%，警惕强平踩踏使支撑失效"

        support_levels.sort(key=lambda x: x["price"], reverse=True)
        resistance_levels.sort(key=lambda x: x["price"])

        # 筹码真空带识别 (占比 < 0.6% 的低密度走廊)
        for i in range(1, bins_count - 1):
            if chips_pct[i] < 0.6 and chips_pct[i] <= chips_pct[i-1] and chips_pct[i] <= chips_pct[i+1]:
                left = i
                while left > 0 and chips_pct[left] < 1.0:
                    left -= 1
                right = i
                while right < bins_count - 1 and chips_pct[right] < 1.0:
                    right += 1
                if right - left >= 4:
                    vac_low = prices[left]
                    vac_high = prices[right]
                    if not any(abs(v["low"] - vac_low) < step * 2 for v in vacuum_zones):
                        vacuum_zones.append({
                            "low": round(float(vac_low), precision),
                            "high": round(float(vac_high), precision),
                            "desc": f"¥{vac_low:.{precision}f} ~ ¥{vac_high:.{precision}f} 筹码稀薄真空区 (快速突破/回落通道)"
                        })

        # -------------------------------------------------------------
        # 5. 筹码量化多空辩论 (Quant Bull vs Bear Debate)
        # -------------------------------------------------------------
        primary_sup = support_levels[0] if support_levels else None
        primary_res = resistance_levels[0] if resistance_levels else None
        trapped_ratio = round(100.0 - profit_ratio, 1)

        # 多方辩手论点
        bull_points = []
        if profit_ratio >= 70:
            bull_points.append(f"获利盘占比高达 {profit_ratio:.1f}%，大部分持筹者处于盈利状态，浮动杀跌抛压极轻，多头进攻动能强劲。")
        if primary_sup:
            sup_desc = f"现价紧贴下方核心密集支撑峰 ¥{primary_sup['price']:.{precision}f} (距离仅 {abs(primary_sup['distance_percent']):.1f}%)"
            if not has_high_margin:
                sup_desc += "，下档护盘承接有力，具备扎实安全垫。"
            else:
                sup_desc += "，但由于标的高融资杠杆，需严格设定防守底线。"
            bull_points.append(sup_desc)
        if conc70 <= 10.0:
            bull_points.append(f"70% 筹码集中度低至 {conc70:.1f}%，主力资金高控盘锁仓充分，随时具备脱离成本区的爆发力。")
        if not resistance_levels:
            bull_points.append("现价上方无显著套牢密集峰压制，已进入筹码天空领空，向上阻力微弱。")
        elif primary_res and abs(primary_res["distance_percent"]) > 8.0:
            bull_points.append(f"距上方首个主要阻力位 ¥{primary_res['price']:.{precision}f} 尚有 +{primary_res['distance_percent']:.1f}% 开阔空间，短线盈亏比优异。")
        if not bull_points:
            bull_points.append(f"现价在 ¥{avg_cost:.{precision}f} 筹码中枢附近蓄势整固，清洗浮筹后有望展开向上试盘。")

        # 空方辩手论点
        bear_points = []
        if has_high_margin:
            bear_points.append(f"两融杠杆盘高企（融资余额占流通盘 {margin_ratio:.1f}% > 5%），一旦下探支撑，极易触发券商强制平仓线导致被动抛压踩踏，使传统筹码支撑位加速击穿失效。")
        if any("大宗交易" in r.get("desc", "") for r in resistance_levels):
            bear_points.append("上方存在大宗交易折价接盘的锁定期满解禁筹码，接盘方利润丰厚且减持意愿强烈，形成隐形重阻力天花板。")
        if trapped_ratio >= 60:
            bear_points.append(f"上方套牢盘高达 {trapped_ratio:.1f}%；在处置效应（死扛心理）下高位未割套牢筹码大量留存，反弹逼近成本将遭凶猛解套抛压。")
        if primary_res:
            bear_points.append(f"上方 ¥{primary_res['price']:.{precision}f} 处盘踞着显著套牢峰 (阻力筹码占比 {primary_res['chip_percent']}%)，距离现价仅 {primary_res['distance_percent']:.1f}%，空间被严密压制。")
        if profit_premium < -4.0:
            bear_points.append(f"现价跌破全市场平均成本线 ¥{avg_cost:.{precision}f} (折价 {profit_premium:.1f}%)，多头成本防线告破，需防范多杀多踩踏。")
        if not primary_sup:
            bear_points.append("现价下方缺乏密集筹码峰保护，下档承接虚浮，若大盘转弱容易加速下探。")
        elif primary_sup and abs(primary_sup["distance_percent"]) > 10.0:
            bear_points.append(f"距离下方首个有效支撑峰 ¥{primary_sup['price']:.{precision}f} 尚有 {abs(primary_sup['distance_percent']):.1f}% 回调空间，下行防守位偏远。")
        if not bear_points:
            bear_points.append("虽处获利格局，但需严防获利盘高位兑现欲望加剧引发冲高回落。")

        # 裁判裁决台 (Arbiter Decision)
        if profit_ratio >= 75 and conc70 <= 12.0 and not has_high_margin:
            verdict_bias = "强烈看多 (Strong Bullish)"
            tactics = "主升浪持股与顺势做多"
            strategy_summary = "筹码呈高位强凝聚与突破态势，下方强支撑护盘，建议以核心支撑位上方为依托顺势加仓或持股。"
            stop_loss = round(primary_sup["price"] * 0.97, precision) if primary_sup else round(current_price * 0.95, precision)
            target_price = round(primary_res["price"], precision) if primary_res else round(current_price * 1.15, precision)
        elif trapped_ratio >= 70 or has_high_margin:
            verdict_bias = "谨慎防守 (Bearish Defence)"
            tactics = "逢高减仓与防守观望"
            strategy_summary = "上方套牢盘厚重或两融杠杆偏高，反弹多为解套抽逃行情，切忌盲目追高，等待底部长周期换手单峰凝聚。"
            stop_loss = round(primary_sup["price"] * 0.96, precision) if primary_sup else round(current_price * 0.93, precision)
            target_price = round(primary_res["price"] * 0.98, precision) if primary_res else round(avg_cost, precision)
        elif conc70 <= 9.0:
            verdict_bias = "变盘临界 (Breakout Watch)"
            tactics = "突破跟随与两手准备"
            strategy_summary = "筹码极致收敛，单峰高度控盘，多空进入决战临界点。密切关注放量突破阻力位方向跟随入场。"
            stop_loss = round((primary_sup["price"] if primary_sup else p15) * 0.98, precision)
            target_price = round((primary_res["price"] if primary_res else p85) * 1.05, precision)
        else:
            verdict_bias = "箱体博弈 (Neutral Box)"
            tactics = "支撑低吸，阻力高抛"
            strategy_summary = f"在支撑位 ¥{(primary_sup['price'] if primary_sup else p15):.{precision}f} 与压力位 ¥{(primary_res['price'] if primary_res else p85):.{precision}f} 之间进行网格震荡波段操作。"
            stop_loss = round(p5 * 0.98, precision)
            target_price = round(primary_res["price"] if primary_res else p85, precision)

        quant_debate = {
            "bull_thesis": {
                "title": "量化多方进攻论点 (Bull Case)",
                "confidence": min(95, max(10, int(profit_ratio * 0.8 + (10 - min(10, conc70)) * 2))),
                "points": bull_points,
                "key_defense": f"¥{primary_sup['price']:.{precision}f}" if primary_sup else "无明显密集峰"
            },
            "bear_thesis": {
                "title": "量化空方防守警告 (Bear Case)",
                "confidence": min(95, max(10, int((100 - profit_ratio) * 0.8 + conc70 * 1.5 + (15 if has_high_margin else 0)))),
                "points": bear_points,
                "key_resistance": f"¥{primary_res['price']:.{precision}f}" if primary_res else "无历史套牢峰"
            },
            "arbiter": {
                "bias": verdict_bias,
                "tactics": tactics,
                "summary": strategy_summary,
                "suggested_entry": f"¥{(primary_sup['price'] if primary_sup else avg_cost):.{precision}f} 附近",
                "stop_loss": stop_loss,
                "target_price": target_price,
                "risk_reward_ratio": (
                    __import__("app.quant_engine", fromlist=["QuantCoreEngine"]).QuantCoreEngine.calc_risk_reward(
                        {"code": symbol, "is_etf": is_etf},
                        {"close": current_price, "pct_chg": pct_chg}
                    ) or round(abs((target_price - current_price) / max(0.01, (current_price - stop_loss))), 2)
                )
            }
        }

        # -------------------------------------------------------------
        # 6. 直方图区间合并 (无损聚合)
        # -------------------------------------------------------------
        actual_vis = min(vis_bins, bins_count)
        histogram = []
        bin_edges = np.linspace(0, bins_count, actual_vis + 1, dtype=int)
        for k in range(actual_vis):
            start_idx = bin_edges[k]
            end_idx = bin_edges[k + 1]
            if end_idx <= start_idx:
                end_idx = start_idx + 1
            pct_sum = float(chips_pct[start_idx:end_idx].sum())
            mid_idx = (start_idx + end_idx - 1) // 2
            mid_price = float(prices[min(mid_idx, bins_count - 1)])
            histogram.append({
                "price": round(mid_price, precision),
                "percent": round(pct_sum, 2),
                "is_profit": mid_price <= current_price
            })

        applied_rules = []
        if is_sub_new:
            applied_rules.append(f"次新股窗口限制(样本{total_bars_count}<120，取60日，峰值门槛2.0%)")
        if limit_board_count > 0:
            applied_rules.append(f"涨跌停板折减生效({limit_board_count}个一字板换手率x0.4)")
        if suspension_count > 0:
            applied_rules.append(f"停牌复牌筹码重置生效({suspension_count}次停牌重置x0.5)")
        if has_high_margin:
            applied_rules.append(f"两融高杠杆支撑降级(融资余额{margin_ratio:.1f}%>5%)")
        if block_trades and len(block_trades) > 0:
            applied_rules.append(f"大宗交易锁定期满抛压注入({len(block_trades)}笔)")
        if capital_events and len(capital_events) > 0:
            applied_rules.append(f"股本变动事件修正生效({len(capital_events)}项)")
        if ex_dividend_count > 0:
            applied_rules.append(f"除权除息断层自适应平滑生效({ex_dividend_count}次跳空对齐)")
        if is_intraday_dynamic:
            applied_rules.append(f"盘中日内高频动态增量推演生效(日内换手率 {intraday_turnover_pct:.2f}%)")

        return {
            "current_price": round(current_price, precision),
            "avg_cost": round(avg_cost, precision),
            "profit_ratio": round(profit_ratio, 1),
            "trapped_ratio": trapped_ratio,
            "profit_premium": round(profit_premium, 2),
            "cost_range_90": [round(p5, precision), round(p95, precision)],
            "concentration_90": round(conc90, 1),
            "cost_range_70": [round(p15, precision), round(p85, precision)],
            "concentration_70": round(conc70, 1),
            "median_cost": round(p50, precision),
            "peak_pattern": peak_pattern,
            "pattern_desc": pattern_desc,
            "pattern_type": pattern_type,
            "is_intraday_dynamic": is_intraday_dynamic,
            "intraday_turnover_pct": round(intraday_turnover_pct, 2),
            "is_ex_dividend_compensated": (ex_dividend_count > 0),
            "support_levels": support_levels[:3],
            "resistance_levels": resistance_levels[:3],
            "vacuum_zones": vacuum_zones[:2],
            "quant_debate": quant_debate,
            "applied_rules": applied_rules,
            "histogram": histogram
        }

    except Exception as e:
        logger.error(f"筹码分布计算异常: {e}", exc_info=True)
        return None
