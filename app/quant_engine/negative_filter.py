"""
风控负面清单与一票否决规则 (Negative Risk Filters)
防暴雷、防流动性陷阱、防极限追高
"""

from typing import Dict, Any, List, Optional


def check_negative_filters(
    name: str = "",
    code: str = "",
    debt_ratio: Optional[float] = None,
    amount_yi: Optional[float] = None,
    turnover_rate: Optional[float] = None,
    bias5: Optional[float] = None,
    exclude_st: bool = True,
    max_debt_ratio: float = 75.0,
    min_amount_yi: float = 0.5,
    min_turnover_rate: float = 0.3,
    max_bias5: float = 8.5
) -> Dict[str, Any]:
    """
    检查标的是否触发负面清单一票否决规则
    """
    violations: List[str] = []
    n = str(name).upper().strip()

    # 1. ST / *ST 风险警示排除
    if exclude_st and ("ST" in n or "*ST" in n or "退" in n):
        violations.append("触发风险警示 (ST/*ST/退市整理期)")

    # 2. 高资产负债率风险排除 (非金融地产默认 > 75%)
    if debt_ratio is not None:
        try:
            d = float(debt_ratio)
            if d > max_debt_ratio:
                violations.append(f"资产负债率过高 ({d:.1f}% > {max_debt_ratio}%)")
        except (ValueError, TypeError):
            pass

    # 3. 微盘流动性枯竭陷阱
    if amount_yi is not None and turnover_rate is not None:
        try:
            a = float(amount_yi)
            t = float(turnover_rate)
            if a < min_amount_yi and t < min_turnover_rate:
                violations.append(f"流动性极其匮乏 (日成交 {a:.2f}亿 < {min_amount_yi}亿)")
        except (ValueError, TypeError):
            pass

    # 4. 极端超买追高风险 (BIAS5 > 8.5%)
    if bias5 is not None:
        try:
            b = float(bias5)
            if b > max_bias5:
                violations.append(f"短期严重脉冲超买 (5日乖离 {b:.1f}% > {max_bias5}%)")
        except (ValueError, TypeError):
            pass

    is_passed = (len(violations) == 0)
    return {
        "is_passed": is_passed,
        "violations": violations,
        "reject_reason": " · ".join(violations) if violations else "风控合规通过"
    }
