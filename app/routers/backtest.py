"""
量化回测 REST API 路由
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.backtest.backtest_engine import BacktestEngine
from app.services.backtest.data_loader import load_backtest_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backtest", tags=["量化回测"])


class BacktestRunRequest(BaseModel):
    symbol: str = Field(..., description="A股股票代码，例如 600519，或组合代码如 600519, 000001")
    symbols: Optional[List[str]] = Field(default=None, description="组合股票代码列表 (若提供则执行组合回测)")
    sizing_model: str = Field(default="equal_weight", description="组合资金分配模型: equal_weight (等权重), inverse_volatility (波动率倒数)")
    strategy: str = Field(default="dual_ma", description="策略名称: dual_ma, macd, bollinger, custom_rule")
    strategy_name: Optional[str] = Field(default=None, description="策略名称别名")
    params: Optional[Dict[str, Any]] = Field(default=None, description="策略超参数")
    strategy_params: Optional[Dict[str, Any]] = Field(default=None, description="策略参数别名")
    start_date: Optional[str] = Field(default=None, description="开始日期 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="结束日期 (YYYY-MM-DD)")
    initial_cash: float = Field(default=100000.0, ge=1000, description="初始资金 (元)")
    initial_capital: Optional[float] = Field(default=None, description="初始资金别名")
    commission_rate: float = Field(default=0.00025, description="佣金费率 (默认万2.5)")
    min_commission: float = Field(default=5.0, ge=0.0, description="最低佣金 (元，默认5元)")
    stamp_duty_rate: float = Field(default=0.0005, description="印花税率 (默认万5，仅卖出)")
    transfer_fee_rate: float = Field(default=0.00001, ge=0.0, description="过户费率 (默认十万分之1)")
    slippage: float = Field(default=0.001, description="滑点参数 (默认0.1%)")
    slippage_type: str = Field(default="percent", description="滑点模型: percent, fixed_points, volume_impact, none")
    position_ratio: float = Field(default=0.95, ge=0.1, le=1.0, description="单次买入资金占用比例")


class BacktestResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str


@router.get("/strategies")
async def list_strategies():
    """获取系统支持的内置量化回测策略列表"""
    return {
        "success": True,
        "data": [
            {
                "id": "dual_ma",
                "name": "双均线交叉趋势策略",
                "description": "短期均线金叉长期均线全仓买入，死叉卖出清仓。适合强趋势行情。",
                "params": {
                    "short_window": {"type": "int", "default": 5, "label": "短期MA周期"},
                    "long_window": {"type": "int", "default": 20, "label": "长期MA周期"},
                }
            },
            {
                "id": "macd",
                "name": "MACD 动量金叉策略",
                "description": "DIF上穿DEA金叉买入，死叉卖出。捕捉动量转折点。",
                "params": {
                    "fast": {"type": "int", "default": 12, "label": "快线EMA"},
                    "slow": {"type": "int", "default": 26, "label": "慢线EMA"},
                    "signal_span": {"type": "int", "default": 9, "label": "信号线DEA周期"},
                }
            },
            {
                "id": "bollinger",
                "name": "布林带均值回归策略",
                "description": "价格触及下轨超跌反弹买入，触及上轨超买止盈。适合震荡行情。",
                "params": {
                    "window": {"type": "int", "default": 20, "label": "均线周期"},
                    "num_std": {"type": "float", "default": 2.0, "label": "标准差倍数"},
                }
            },
            {
                "id": "custom_rule",
                "name": "🌟 自定义多指标组合策略",
                "description": "自主自由组合均线趋势、量能突破、RSI超跌、KDJ金叉与硬止损/动态止盈风控。",
                "params": {
                    "ma_mode": {"type": "str", "default": "cross", "label": "均线模式 (cross/bull/above_long/none)"},
                    "short_window": {"type": "int", "default": 5, "label": "短均线周期"},
                    "long_window": {"type": "int", "default": 20, "label": "长均线周期"},
                    "volume_filter": {"type": "str", "default": "none", "label": "量能过滤 (vol_surge/vol_expand/none)"},
                    "vol_multiplier": {"type": "float", "default": 1.5, "label": "放量倍数"},
                    "rsi_filter": {"type": "str", "default": "none", "label": "RSI过滤 (oversold/rebound/none)"},
                    "rsi_threshold": {"type": "float", "default": 35.0, "label": "RSI阈值"},
                    "kdj_filter": {"type": "str", "default": "none", "label": "KDJ过滤 (golden_cross/low_j/none)"},
                    "breakout_filter": {"type": "str", "default": "none", "label": "突破形态 (new_high/none)"},
                    "breakout_period": {"type": "int", "default": 20, "label": "突破周期"},
                    "condition_mode": {"type": "str", "default": "and", "label": "组合逻辑 (and/or)"},
                    "stop_loss_pct": {"type": "float", "default": 0.05, "label": "硬止损比例 (如0.05为-5%)"},
                    "take_profit_pct": {"type": "float", "default": 0.15, "label": "止盈目标比例 (如0.15为+15%)"},
                    "max_holding_days": {"type": "int", "default": 15, "label": "最长持仓天数"}
                }
            }
        ]
    }


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(req: BacktestRunRequest):
    """
    触发量化回测计算
    严格执行 A 股 T+1、涨跌停、手续费、印花税和滑点撮合
    """
    try:
        strat = req.strategy_name or req.strategy
        prms = req.strategy_params if req.strategy_params is not None else (req.params or {})
        init_cash = req.initial_capital if req.initial_capital is not None else req.initial_cash

        # 1. 实例化回测引擎
        engine = BacktestEngine(
            initial_cash=init_cash,
            commission_rate=req.commission_rate,
            min_commission=req.min_commission,
            stamp_duty_rate=req.stamp_duty_rate,
            transfer_fee_rate=req.transfer_fee_rate,
            slippage=req.slippage,
            slippage_type=req.slippage_type,
            position_ratio=req.position_ratio
        )

        # 2. 解析单标的或多标的组合
        symbols_list = req.symbols
        if not symbols_list and req.symbol:
            raw_syms = [s.strip() for s in req.symbol.replace("，", ",").replace(";", ",").split(",") if s.strip()]
            if len(raw_syms) > 1:
                symbols_list = raw_syms

        # 3. 执行单标的或组合回测
        if symbols_list and len(symbols_list) > 1:
            logger.info(f"🚀 开始执行多标的组合回测: {symbols_list}, 策略: {strat}, 仓位模型: {req.sizing_model}")
            dfs_dict = {}
            for s in symbols_list:
                try:
                    dfs_dict[s] = load_backtest_data(symbol=s, start_date=req.start_date, end_date=req.end_date)
                except Exception as ex:
                    logger.warning(f"组合标的 {s} 历史数据加载异常: {ex}")

            if not dfs_dict:
                raise ValueError(f"候选组合中所有标的历史数据均无法加载: {symbols_list}")

            result = engine.run_portfolio(
                symbols=symbols_list,
                dfs_dict=dfs_dict,
                strategy_name=strat,
                strategy_params=prms,
                sizing_model=req.sizing_model
            )
        else:
            single_sym = symbols_list[0] if (symbols_list and len(symbols_list) == 1) else req.symbol.strip()
            logger.info(f"🚀 开始执行单标的回测: {single_sym}, 策略: {strat}")
            df = load_backtest_data(
                symbol=single_sym,
                start_date=req.start_date,
                end_date=req.end_date
            )
            result = engine.run(
                symbol=single_sym,
                df=df,
                strategy_name=strat,
                strategy_params=prms
            )

        return BacktestResponse(
            success=True,
            data=result,
            message=f"回测完成，总收益率: {result['metrics']['total_return_pct']}%"
        )
    except Exception as e:
        logger.error(f"❌ 回测执行失败: {e}", exc_info=True)
        return BacktestResponse(
            success=False,
            data=None,
            message=f"回测执行失败: {str(e)}"
        )
