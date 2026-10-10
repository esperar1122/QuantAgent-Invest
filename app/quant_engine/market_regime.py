"""
量价五大生命周期状态机 (Market Regime State Machine)
纯计算数学模型，严格遵守：
- 破位阴跌禁区坚决不给买点
- 主升浪强势期采用移动跟踪止盈防卖飞
- 超跌衰竭期需负乖离与获利盘深度共振，防微涨假阳诱多
"""

from enum import Enum
from typing import Dict, Any, Optional
from .profiles import BoardProfile, get_board_profile


class MarketRegime(str, Enum):
    EXTREME_OVERSOLD = "EXTREME_OVERSOLD"    # 极度超跌衰竭区
    DOWNWARD_TREND = "DOWNWARD_TREND"        # 破位阴跌防守禁区
    STRONG_MOMENTUM = "STRONG_MOMENTUM"      # 主升浪强势加速期 / 稳健多头
    PULLBACK_SETUP = "PULLBACK_SETUP"        # 良性缩量回踩企稳区
    RANGE_BOUND = "RANGE_BOUND"              # 箱体震荡中枢


class MarketRegimeResult:
    def __init__(
        self,
        regime: MarketRegime,
        label: str,
        description: str,
        is_actionable: bool,
        tag_type: str = "info"
    ):
        self.regime = regime
        self.label = label
        self.description = description
        self.is_actionable = is_actionable
        self.tag_type = tag_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "regime": self.regime.value,
            "label": self.label,
            "description": self.description,
            "is_actionable": self.is_actionable,
            "tag_type": self.tag_type
        }


def detect_market_regime(
    current_price: float,
    pct_chg: float = 0.0,
    ma5: Optional[float] = None,
    ma10: Optional[float] = None,
    ma20: Optional[float] = None,
    ma60: Optional[float] = None,
    turnover_rate: float = 0.0,
    amount_yi: float = 0.0,
    profit_ratio: Optional[float] = None,
    concentration_70: Optional[float] = None,
    kdj_j: Optional[float] = None,
    board_profile: Optional[BoardProfile] = None,
    code: str = ""
) -> MarketRegimeResult:
    """
    全量量化判定五大量价生命周期状态机
    """
    px = float(current_price)
    if px <= 0:
        return MarketRegimeResult(
            regime=MarketRegime.RANGE_BOUND,
            label="行情未就绪",
            description="价格数据暂未就绪",
            is_actionable=False
        )

    bp = board_profile or get_board_profile(code)

    # 1. 均线与乖离率推导
    bias5 = (((px - ma5) / ma5) * 100.0) if (ma5 and ma5 > 0) else 0.0
    bias10 = (((px - ma10) / ma10) * 100.0) if (ma10 and ma10 > 0) else 0.0

    # 筹码结构
    pr = profit_ratio if profit_ratio is not None else (70.0 if pct_chg >= 0 else 30.0)
    trapped_ratio = max(0.0, 100.0 - pr)
    conc70 = concentration_70 if concentration_70 is not None else 10.0

    # 2. 状态判定
    # A. 极度超跌衰竭
    is_extreme_oversold = (
        bias5 <= bp.oversold_bias
        or (kdj_j is not None and kdj_j < 5.0)
        or (pr <= 10.0 and bias5 <= (bp.oversold_bias * 0.75) and pct_chg > 0)
    )

    # 爆发放量 / 强动能吞噬判定 (科技短线大阳线突破，即便套牢盘高也属于启动而非阴跌)
    is_explosive_absorption = (
        (turnover_rate >= 5.0 or amount_yi > 10.0)
        and pct_chg >= 2.0
        and px >= (ma5 or px * 0.99)
    )

    # B. 破位阴跌禁区 (MA5/MA10死叉下行或重度套牢破位，且无放量动能吞噬)
    is_downtrend_broken = (
        not is_extreme_oversold
        and not is_explosive_absorption
        and bool(
            (ma10 and px < ma10 and ma5 and ma5 <= ma10)
            or (trapped_ratio >= 68.0 and (not ma5 or px < ma5) and turnover_rate < 4.0)
            or (ma20 and ma60 and ma20 < ma60 and px < ma20)
        )
    )

    # C. 主升浪动量加速区
    is_strong_momentum = (
        not is_downtrend_broken
        and bool(
            px >= (ma5 or px * 0.99)
            and (px >= ma10 * 0.995 if ma10 else True)
            and (
                (pr >= 70.0 and conc70 <= 14.0)
                or (trapped_ratio <= 25.0 and pct_chg >= 1.0)
                or (turnover_rate >= 5.5 and pct_chg >= 2.0)
            )
        )
    )

    # D. 良性缩量回踩区
    is_pullback_setup = (
        not is_downtrend_broken
        and not is_strong_momentum
        and bool(
            (px >= ma10 * 0.985 if ma10 else True)
            and trapped_ratio < 58.0
            and abs(bias10) <= 2.8
        )
    )

    # 3. 构造输出
    is_low_vol = (turnover_rate > 0 and turnover_rate < 0.6) or bp.is_etf

    if is_extreme_oversold:
        return MarketRegimeResult(
            regime=MarketRegime.EXTREME_OVERSOLD,
            label="极度超跌衰竭区",
            description="深度负乖离与极限钝化共振，超跌反抽酝酿中，严控试错仓位",
            is_actionable=True,
            tag_type="warning"
        )
    elif is_downtrend_broken:
        return MarketRegimeResult(
            regime=MarketRegime.DOWNWARD_TREND,
            label="破位阴跌防守禁区",
            description="均线空头排列或深套牢盘压制，禁区严禁抄底逆势加仓",
            is_actionable=False,
            tag_type="danger"
        )
    elif is_strong_momentum:
        lbl = "稳健多头趋势波段" if is_low_vol else "主升浪强势加速期"
        desc = "均线多头排列，筹码锁定良好，建议移动止盈让利润奔跑" if is_low_vol else "动能强劲突破，处于主升加速段，不破MA5持股待涨"
        return MarketRegimeResult(
            regime=MarketRegime.STRONG_MOMENTUM,
            label=lbl,
            description=desc,
            is_actionable=True,
            tag_type="success"
        )
    elif is_pullback_setup:
        return MarketRegimeResult(
            regime=MarketRegime.PULLBACK_SETUP,
            label="良性缩量回踩企稳区",
            description="上升趋势未破，缩量回踩关键均线与筹码密集峰，低吸盈亏比佳",
            is_actionable=True,
            tag_type="primary"
        )
    else:
        return MarketRegimeResult(
            regime=MarketRegime.RANGE_BOUND,
            label="箱体震荡中枢",
            description="处于中枢蓄势整理期，半空中谨慎追高，等待箱底或放量突破",
            is_actionable=False,
            tag_type="info"
        )
