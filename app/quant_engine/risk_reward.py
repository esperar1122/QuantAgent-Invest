"""
统一实战扣费净盈亏比与量化买卖点推演核心 (Risk-Reward & Sizing Math)
全系统 Single Source of Truth，杜绝任何地方粗暴 (target-px)/(px-stop) 导致低价股/低波股失真
"""

from typing import Dict, Any, Optional, Tuple
from .profiles import BoardProfile, get_board_profile
from .market_regime import MarketRegime, detect_market_regime


def calc_dynamic_atr(
    current_price: float,
    amplitude: Optional[float] = None,
    high: Optional[float] = None,
    low: Optional[float] = None,
    atr14: Optional[float] = None,
    turnover_rate: Optional[float] = None,
    board_profile: Optional[BoardProfile] = None,
    code: str = ""
) -> float:
    """
    计算标的动态 ATR 波动标尺 (自适应板块弹性系数)
    """
    px = float(current_price)
    if px <= 0:
        return 0.0

    bp = board_profile or get_board_profile(code)

    # 1. 优先提取标准 14 日 ATR
    if atr14 is not None and atr14 > 0:
        return round(float(atr14) * bp.atr_factor, 3 if bp.is_etf else 2)

    # 2. 真实日内振幅 (amplitude %)
    if amplitude is not None and amplitude > 0:
        vol_pct = max(0.012, min(0.12, float(amplitude) / 100.0))
        return round(px * vol_pct * bp.atr_factor, 3 if bp.is_etf else 2)

    # 3. 日内高低价差
    if high is not None and low is not None and high > low:
        diff = float(high - low)
        return round(diff * bp.atr_factor, 3 if bp.is_etf else 2)

    # 4. 板块基础波动率兜底
    base_vols = {
        "ETF": 0.016,
        "20CM": 0.045,
        "BSE": 0.055,
        "MAIN": 0.030,
        "ST": 0.020
    }
    b_vol = base_vols.get(bp.board_type, 0.030)
    tr = float(turnover_rate or 2.0)
    vol_adjusted = b_vol * (0.8 + min(1.5, tr / 3.0) * 0.4)
    return round(px * vol_adjusted * bp.atr_factor, 3 if bp.is_etf else 2)


def calc_net_risk_reward_ratio(
    current_price: float,
    code: str = "",
    market: str = "",
    is_etf: bool = False,
    pct_chg: float = 0.0,
    amplitude: Optional[float] = None,
    high: Optional[float] = None,
    low: Optional[float] = None,
    atr14: Optional[float] = None,
    turnover_rate: Optional[float] = None,
    pe: Optional[float] = None,
    roe: Optional[float] = None,
    support_price: Optional[float] = None,
    resistance_price: Optional[float] = None,
    regime: Optional[MarketRegime] = None
) -> Dict[str, Any]:
    """
    全量推演标的扣费实战净盈亏比 (Net R:R) 与点位空间
    严格扣除实盘券商交易摩擦：
    - 佣金万 0.876，免 5 最低 0.5 元起收
    - 股票卖出万 5 印花税，ETF 免征印花税
    - 双边万 0.1 过户费
    """
    px = float(current_price)
    if px <= 0:
        return {
            "risk_reward_ratio": 1.0,
            "target_price": 0.0,
            "stop_price": 0.0,
            "net_gain": 0.0,
            "net_loss": 0.0,
            "is_valid": False
        }

    bp = get_board_profile(code, market=market, is_etf=is_etf)
    atr = calc_dynamic_atr(
        current_price=px,
        amplitude=amplitude,
        high=high,
        low=low,
        atr14=atr14,
        turnover_rate=turnover_rate,
        board_profile=bp,
        code=code
    )

    prec = 3 if bp.is_etf else 2

    # 1. 量价动能空间判定
    if pct_chg >= 8.0:
        # 日内极端冲高/超买，追高风险极大，向上弹性收窄，止损拉宽防高位反杀
        target_dist = 1.2 * atr
        stop_dist = 1.6 * atr
    elif pct_chg >= 1.5:
        # 突破/强势主升波段，动能充足，向上弹性充分
        target_dist = 2.2 * atr
        stop_dist = 1.1 * atr
    elif pct_chg <= -3.0:
        # 破位下行/弱势阴跌，多头受压，向上反弹空间逼仄
        target_dist = 0.85 * atr
        stop_dist = 1.4 * atr
    else:
        # 震荡横盘/良性蓄势
        target_dist = 1.5 * atr
        stop_dist = 1.0 * atr

    # 结合真实有效筹码支撑与阻力位做微观收敛
    if support_price is not None and 0 < support_price < px:
        chip_stop_dist = px - support_price
        stop_dist = max(0.5 * atr, min(stop_dist, chip_stop_dist * 1.05))
    if resistance_price is not None and resistance_price > px:
        chip_target_dist = resistance_price - px
        target_dist = max(0.6 * atr, min(target_dist, chip_target_dist * 0.95))

    # 2. 基本面估值与质地安全垫加成
    if pe is not None:
        try:
            pe_val = float(pe)
            roe_val = float(roe) if roe is not None else None
            if 0 < pe_val <= 30 and (roe_val is None or roe_val >= 8.0):
                target_dist *= 1.15
            elif pe_val < 0 or pe_val > 80:
                target_dist *= 0.88
        except (ValueError, TypeError):
            pass

    target_px = round(px + target_dist, prec)
    stop_px = round(max(0.01, px - stop_dist), prec)

    # 3. 券商实盘交易摩擦扣除 (以标准 1000 股测算)
    test_shares = 1000.0
    b_val = test_shares * px
    t_val = test_shares * target_px
    s_val = test_shares * stop_px

    buy_comm = max(bp.min_commission, b_val * bp.commission_rate)
    target_comm = max(bp.min_commission, t_val * bp.commission_rate)
    stop_comm = max(bp.min_commission, s_val * bp.commission_rate)

    target_stamp = t_val * bp.stamp_duty_rate
    stop_stamp = s_val * bp.stamp_duty_rate

    # 过户费 (十万分之1双边)
    transfer_fee = (b_val + t_val) * 0.00001

    net_gain = max(0.0, (t_val - b_val) - buy_comm - target_comm - target_stamp - transfer_fee)
    net_loss = max(0.01, (b_val - s_val) + buy_comm + stop_comm + stop_stamp + transfer_fee)

    net_rr = round(net_gain / net_loss, 2)
    clamped_rr = round(max(0.3, min(6.0, net_rr)), 2)

    return {
        "risk_reward_ratio": clamped_rr,
        "target_price": target_px,
        "stop_price": stop_px,
        "net_gain": round(net_gain, 2),
        "net_loss": round(net_loss, 2),
        "atr": atr,
        "is_valid": True
    }
