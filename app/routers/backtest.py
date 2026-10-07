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
    strategy: str = Field(default="dual_ma", description="策略名称: dual_ma (双均线), macd (MACD动量), bollinger (布林带)")
    params: Optional[Dict[str, Any]] = Field(default=None, description="策略超参数")
    start_date: Optional[str] = Field(default=None, description="开始日期 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="结束日期 (YYYY-MM-DD)")
    initial_cash: float = Field(default=100000.0, ge=1000, description="初始资金 (元)")
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
        logger.info(f"🚀 开始执行回测: {req.symbol}, 策略: {req.strategy}")
        # 1. 加载历史K线
        df = load_backtest_data(
            symbol=req.symbol,
            start_date=req.start_date,
            end_date=req.end_date
        )

        # 2. 实例化引擎并执行
        engine = BacktestEngine(
            initial_cash=req.initial_cash,
            commission_rate=req.commission_rate,
            stamp_duty_rate=req.stamp_duty_rate,
            slippage=req.slippage,
            position_ratio=req.position_ratio
        )

        result = engine.run(
            symbol=req.symbol,
            df=df,
            strategy_name=req.strategy,
            strategy_params=req.params
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
