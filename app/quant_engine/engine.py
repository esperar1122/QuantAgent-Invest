"""
统一量化计算核心引擎门面 (Quant Core Engine Facade)
Single Source of Truth - 全系统算法统一调度中枢
纯计算、零 I/O、纳秒级响应，向后 100% 兼容
"""

from typing import Dict, Any, Optional, List
from .profiles import get_board_profile, BoardProfile
from .market_regime import detect_market_regime, MarketRegime, MarketRegimeResult
from .risk_reward import calc_net_risk_reward_ratio, calc_dynamic_atr
from .technical_factors import is_ma_bullish, is_above_ma20, evaluate_chip_structure
from .capital_factors import evaluate_northbound_holding, evaluate_main_money_flow
from .negative_filter import check_negative_filters


class QuantCoreEngine:
    """全系统统一量化算法引擎"""

    @classmethod
    def calc_risk_reward(cls, item: dict, q: dict) -> Optional[float]:
        """
        全系统统一调用的盈亏比计算入口 (向后 100% 兼容原 _calc_risk_reward_ratio)
        """
        close = q.get("close") if q.get("close") is not None else item.get("close")
        if close is None:
            return None
        try:
            c = float(close)
            if c <= 0:
                return None
        except (ValueError, TypeError):
            return None

        code = str(item.get("code") or q.get("code") or "").strip()
        market = str(item.get("market") or q.get("market") or "")
        is_etf = bool(item.get("is_etf") or q.get("is_etf"))
        pct_chg = float(q.get("pct_chg") or item.get("pct_chg") or 0.0)
        amp = q.get("amplitude") or item.get("amplitude")
        high = q.get("high") or item.get("high")
        low = q.get("low") or item.get("low")
        tr = q.get("turnover_rate") or item.get("turnover_rate")
        pe = q.get("pe") or item.get("pe")
        roe = item.get("roe") or q.get("roe")

        res = calc_net_risk_reward_ratio(
            current_price=c,
            code=code,
            market=market,
            is_etf=is_etf,
            pct_chg=pct_chg,
            amplitude=float(amp) if amp is not None else None,
            high=float(high) if high is not None else None,
            low=float(low) if low is not None else None,
            turnover_rate=float(tr) if tr is not None else None,
            pe=float(pe) if pe is not None else None,
            roe=float(roe) if roe is not None else None
        )
        return res.get("risk_reward_ratio")

    @classmethod
    def evaluate_stock(
        cls,
        item: dict,
        q: dict,
        chips: Optional[dict] = None,
        capital_flow: Optional[dict] = None
    ) -> Dict[str, Any]:
        """
        全量推演单标的的量化全息画像 (Regime + R:R + Tech + Capital + Risk)
        """
        code = str(item.get("code") or q.get("code") or "").strip()
        name = str(item.get("name") or q.get("name") or "").strip()
        close = float(q.get("close") or item.get("close") or 0.0)
        pct_chg = float(q.get("pct_chg") or item.get("pct_chg") or 0.0)
        tr = float(q.get("turnover_rate") or item.get("turnover_rate") or 0.0)
        amount_yi = float(q.get("amount") or item.get("amount") or 0.0)
        if amount_yi > 10000.0:  # 单位修正 (若是元则转为亿元)
            amount_yi = amount_yi / 100000000.0

        bp = get_board_profile(code, market=str(item.get("market") or ""), is_etf=bool(item.get("is_etf")))

        # 1. 均线推导
        ma5 = float(q.get("ma5") or item.get("ma5") or 0.0) or None
        ma10 = float(q.get("ma10") or item.get("ma10") or 0.0) or None
        ma20 = float(q.get("ma20") or item.get("ma20") or 0.0) or None
        ma60 = float(q.get("ma60") or item.get("ma60") or 0.0) or None

        # 2. 筹码推导
        chips_dict = chips or item.get("chips") or {}
        pr = chips_dict.get("profit_ratio")
        c70 = chips_dict.get("concentration_70")
        c90 = chips_dict.get("concentration_90")
        sup = None
        if chips_dict.get("support_levels"):
            try:
                sup = float(chips_dict["support_levels"][0]["price"])
            except (KeyError, IndexError, TypeError):
                sup = None

        # 3. 状态机
        regime_res = detect_market_regime(
            current_price=close,
            pct_chg=pct_chg,
            ma5=ma5,
            ma10=ma10,
            ma20=ma20,
            ma60=ma60,
            turnover_rate=tr,
            amount_yi=amount_yi,
            profit_ratio=pr,
            concentration_70=c70,
            board_profile=bp,
            code=code
        )

        # 4. 盈亏比
        rr_res = calc_net_risk_reward_ratio(
            current_price=close,
            code=code,
            market=str(item.get("market") or ""),
            is_etf=bp.is_etf,
            pct_chg=pct_chg,
            amplitude=float(q.get("amplitude") or 0.0) or None,
            high=float(q.get("high") or 0.0) or None,
            low=float(q.get("low") or 0.0) or None,
            turnover_rate=tr,
            pe=float(q.get("pe") or item.get("pe") or 0.0) or None,
            roe=float(item.get("roe") or q.get("roe") or 0.0) or None,
            support_price=sup,
            regime=regime_res.regime
        )

        # 5. 技术面因子
        ma_bullish = is_ma_bullish(ma5, ma10, ma20, ma60)
        above_20 = is_above_ma20(close, ma20)
        chip_eval = evaluate_chip_structure(pr, c70, c90, current_price=close, support_price=sup)

        # 6. 资金面与北向
        cf_summary = (capital_flow or {}).get("flow", {}).get("summary", {})
        nb_data = (capital_flow or {}).get("northbound", {})
        nb_eval = evaluate_northbound_holding(
            hold_ratio_pct=nb_data.get("latest_holding", {}).get("hold_ratio_pct"),
            hold_market_cap_yi=nb_data.get("latest_holding", {}).get("hold_market_cap_yi")
        )
        flow_eval = evaluate_main_money_flow(
            main_1d_wan=cf_summary.get("main_1d_wan"),
            main_5d_wan=cf_summary.get("main_5d_wan"),
            super_large_5d_wan=cf_summary.get("super_5d_wan"),
            retail_5d_wan=cf_summary.get("retail_5d_wan"),
            main_ratio_pct=cf_summary.get("main_ratio_pct")
        )

        # 7. 风控负面清单
        debt = float(item.get("debt_ratio") or q.get("debt_ratio") or 0.0) or None
        bias5 = (((close - ma5) / ma5) * 100.0) if (ma5 and ma5 > 0) else None
        risk_res = check_negative_filters(
            name=name,
            code=code,
            debt_ratio=debt,
            amount_yi=amount_yi,
            turnover_rate=tr,
            bias5=bias5
        )

        return {
            "code": code,
            "name": name,
            "close": close,
            "pct_chg": pct_chg,
            "board": bp.board_type,
            "board_label": bp.board_label,
            "regime": regime_res.to_dict(),
            "risk_reward": rr_res,
            "technical": {
                "ma_bullish": ma_bullish,
                "above_ma20": above_20,
                "chips": chip_eval
            },
            "capital": {
                "northbound": nb_eval,
                "main_flow": flow_eval
            },
            "risk_control": risk_res
        }
