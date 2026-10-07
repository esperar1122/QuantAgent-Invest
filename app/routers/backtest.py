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
    symbol: str = Field(..., description="A股股票代码，例如 600519 或 000001")
    strategy: str = Field(default="dual_ma", description="策略名称: dual_ma, macd, bollinger, custom_rule")
    strategy_name: Optional[str] = Field(default=None, description="策略名称别名")
    params: Optional[Dict[str, Any]] = Field(default=None, description="策略超参数")
    strategy_params: Optional[Dict[str, Any]] = Field(default=None, description="策略参数别名")
    start_date: Optional[str] = Field(default=None, description="开始日期 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="结束日期 (YYYY-MM-DD)")
    initial_cash: float = Field(default=100000.0, ge=1000, description="初始资金 (元)")
    initial_capital: Optional[float] = Field(default=None, description="初始资金别名")
    commission_rate: float = Field(default=0.00025, description="佣金费率 (默认万2.5)")
    stamp_duty_rate: float = Field(default=0.0005, description="印花税率 (默认万5，仅卖出)")
    slippage: float = Field(default=0.001, description="滑点 (默认0.1%)")
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

        logger.info(f"🚀 开始执行回测: {req.symbol}, 策略: {strat}")
        # 1. 加载历史K线
        df = load_backtest_data(
            symbol=req.symbol,
            start_date=req.start_date,
            end_date=req.end_date
        )

        # 2. 实例化引擎并执行
        engine = BacktestEngine(
            initial_cash=init_cash,
            commission_rate=req.commission_rate,
            stamp_duty_rate=req.stamp_duty_rate,
            slippage=req.slippage,
            position_ratio=req.position_ratio
        )

        result = engine.run(
            symbol=req.symbol,
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
