"""
资金面与北向资金特征量化分析 (Capital Flow & Northbound Factors)
纯数学与逻辑判定，无任何网络 I/O
"""

from typing import Dict, Any, Optional


def evaluate_northbound_holding(
    hold_ratio_pct: Optional[float],
    hold_market_cap_yi: Optional[float] = None
) -> Dict[str, Any]:
    """
    评估北向资金持仓量化属性
    - 持股比例 >= 3% 为重要配置，>= 5% 为核心重仓
    - 持股市值 >= 10 亿元为大底仓资产
    """
    ratio = float(hold_ratio_pct or 0.0)
    cap = float(hold_market_cap_yi or 0.0)

    is_heavy_north = ratio >= 3.0
    is_core_north = ratio >= 5.0
    is_large_cap_holding = cap >= 10.0

    if is_core_north:
        tier_label = "外资核心重仓 (>5%)"
    elif is_heavy_north:
        tier_label = "外资重要配置 (>3%)"
    elif ratio > 0.5:
        tier_label = "外资常规持仓"
    else:
        tier_label = "外资微量/未持仓"

    return {
        "hold_ratio_pct": round(ratio, 2),
        "hold_market_cap_yi": round(cap, 2),
        "is_heavy_north": is_heavy_north,
        "is_core_north": is_core_north,
        "is_large_cap_holding": is_large_cap_holding,
        "tier_label": tier_label
    }


def evaluate_main_money_flow(
    main_1d_wan: Optional[float] = None,
    main_5d_wan: Optional[float] = None,
    super_large_5d_wan: Optional[float] = None,
    retail_5d_wan: Optional[float] = None,
    main_ratio_pct: Optional[float] = None
) -> Dict[str, Any]:
    """
    评估主力资金流向形态与多空定性
    - 吸筹剪刀差 (Scissor Divergence): 主力连续进 + 散户被动出
    - 超大单火力强劲
    """
    m1 = float(main_1d_wan or 0.0)
    m5 = float(main_5d_wan or 0.0)
    s5 = float(super_large_5d_wan or 0.0)
    r5 = float(retail_5d_wan or 0.0)
    ratio = float(main_ratio_pct or 0.0)

    # 主力散户多空剪刀差：主力 5 日大幅正流入，散户(小单)大幅净流出
    has_scissor_divergence = bool(m5 > 1000.0 and r5 < -100.0)

    if m5 > 50000.0 or ratio >= 12.0:
        posture = "🔥 主力强势爆量抢筹"
        posture_tag = "success"
    elif m5 > 10000.0 or ratio >= 5.0:
        posture = "🛡️ 主力温和增配蓄势"
        posture_tag = "primary"
    elif m5 < -50000.0 or ratio <= -12.0:
        posture = "⚠️ 主力资金大幅出逃"
        posture_tag = "danger"
    elif m5 < -10000.0 or ratio <= -5.0:
        posture = "📉 主力资金震荡承压"
        posture_tag = "warning"
    else:
        posture = "⚖️ 多空资金均衡拉锯"
        posture_tag = "info"

    return {
        "main_1d_wan": round(m1, 2),
        "main_5d_wan": round(m5, 2),
        "super_large_5d_wan": round(s5, 2),
        "retail_5d_wan": round(r5, 2),
        "main_ratio_pct": round(ratio, 2),
        "has_scissor_divergence": has_scissor_divergence,
        "posture": posture,
        "posture_tag": posture_tag
    }
