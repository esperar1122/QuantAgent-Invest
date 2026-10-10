"""
板块与交易特征超参数配置体系 (Board & Trading Profiles)
纯计算数学模型配置，无任何 I/O 依赖
"""

from typing import Dict, Any, NamedTuple


class BoardProfile(NamedTuple):
    board_type: str            # 板块名称代码: MAIN, 20CM, BSE, ST, ETF
    board_label: str           # 中文展示标签
    price_limit_pct: float     # 涨跌幅限制: 10.0, 20.0, 30.0, 5.0
    atr_factor: float          # ATR 弹性缩放乘数
    bias_threshold: float      # 超买乖离率预警阈值 (%)
    oversold_bias: float       # 极限超卖负乖离阈值 (%)
    trailing_atr_k: float      # 移动止盈 ATR 倍数
    initial_stop_k: float      # 初始宽止损 ATR 倍数
    profit_trigger_k: float    # 激活跟踪止盈的盈利门槛 (x ATR)
    is_etf: bool               # 是否为 ETF 基金
    stamp_duty_rate: float     # 卖出印花税率 (个股 0.05%, ETF 0%)
    commission_rate: float     # 佣金费率 (默认万 0.876)
    min_commission: float      # 最低佣金 (免5最低0.5元)


# 默认实盘券商低佣金与免5费率标准
DEFAULT_COMMISSION_RATE = 0.0000876   # 万分之0.876
DEFAULT_MIN_COMMISSION = 0.5          # 最低 0.5 元
STOCK_STAMP_DUTY_RATE = 0.0005        # 万分之 5 (0.05%)
ETF_STAMP_DUTY_RATE = 0.0             # ETF 免印花税


def get_board_profile(code: str, market: str = "", is_etf: bool = False) -> BoardProfile:
    """
    根据标的代码前缀及市场类型，自适应判定标的所属板块与风控参数
    """
    c = str(code).lower().strip().replace("sh", "").replace("sz", "").replace("bj", "")
    m = str(market).strip()

    # 1. 场内 ETF 基金 (51/56/58/50/15/16)
    if is_etf or c.startswith(("51", "56", "58", "50", "15", "16")) or "etf" in m.lower():
        return BoardProfile(
            board_type="ETF",
            board_label="场内低波ETF",
            price_limit_pct=20.0 if c.startswith("58") else 10.0,
            atr_factor=0.85,
            bias_threshold=2.8,
            oversold_bias=-3.0,
            trailing_atr_k=1.0,
            initial_stop_k=1.0,
            profit_trigger_k=0.8,
            is_etf=True,
            stamp_duty_rate=ETF_STAMP_DUTY_RATE,
            commission_rate=DEFAULT_COMMISSION_RATE,
            min_commission=DEFAULT_MIN_COMMISSION
        )

    # 2. 北交所 30cm (8/4/920 开头)
    if c.startswith(("8", "4", "920")) or m == "北交所":
        return BoardProfile(
            board_type="BSE",
            board_label="北交所(±30%)",
            price_limit_pct=30.0,
            atr_factor=1.50,
            bias_threshold=8.5,
            oversold_bias=-12.0,
            trailing_atr_k=2.0,
            initial_stop_k=1.8,
            profit_trigger_k=1.5,
            is_etf=False,
            stamp_duty_rate=STOCK_STAMP_DUTY_RATE,
            commission_rate=DEFAULT_COMMISSION_RATE,
            min_commission=DEFAULT_MIN_COMMISSION
        )

    # 3. 双创 20cm (创业板 300/301, 科创板 688)
    if c.startswith(("300", "301", "688")) or m in ["创业板", "科创板"]:
        return BoardProfile(
            board_type="20CM",
            board_label="双创板块(±20%)",
            price_limit_pct=20.0,
            atr_factor=1.25,
            bias_threshold=6.5,
            oversold_bias=-8.0,
            trailing_atr_k=1.6,
            initial_stop_k=1.5,
            profit_trigger_k=1.1,
            is_etf=False,
            stamp_duty_rate=STOCK_STAMP_DUTY_RATE,
            commission_rate=DEFAULT_COMMISSION_RATE,
            min_commission=DEFAULT_MIN_COMMISSION
        )

    # 4. 主板 10cm (默认 60/00)
    return BoardProfile(
        board_type="MAIN",
        board_label="主板(±10%)",
        price_limit_pct=10.0,
        atr_factor=1.0,
        bias_threshold=4.5,
        oversold_bias=-5.0,
        trailing_atr_k=1.3,
        initial_stop_k=1.2,
        profit_trigger_k=1.0,
        is_etf=False,
        stamp_duty_rate=STOCK_STAMP_DUTY_RATE,
        commission_rate=DEFAULT_COMMISSION_RATE,
        min_commission=DEFAULT_MIN_COMMISSION
    )
