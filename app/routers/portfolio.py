"""
仓位管理与投资组合优化 REST API 路由
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.portfolio.position_sizer import PositionSizer
from app.services.portfolio.portfolio_optimizer import PortfolioOptimizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portfolio", tags=["仓位与组合优化"])


class ATRSizingRequest(BaseModel):
    total_capital: float = Field(..., ge=1000, description="账户总资产 (元)")
    price: float = Field(..., gt=0, description="标的当前市价")
    atr_value: float = Field(..., gt=0, description="标的14日真实波动幅度 ATR")
    risk_ratio: float = Field(default=0.01, ge=0.001, le=0.05, description="单笔最大容忍亏损比例(默认1%)")
    stop_loss_atr_multiplier: float = Field(default=2.0, ge=1.0, le=5.0, description="止损距离乘数")


class KellySizingRequest(BaseModel):
    total_capital: float = Field(..., ge=1000, description="账户总资产")
    win_rate: float = Field(..., ge=0.0, le=1.0, description="策略历史胜率 (如 0.55)")
    profit_loss_ratio: float = Field(..., gt=0, description="历史盈亏比 (如 1.8)")
    kelly_fraction: float = Field(default=0.5, ge=0.1, le=1.0, description="凯利分数(默认0.5半凯利)")
    max_position_limit: float = Field(default=0.3, ge=0.05, le=1.0, description="单仓位硬上限(默认30%)")


class RebalancePlanRequest(BaseModel):
    current_cash: float = Field(..., ge=0, description="当前可用现金")
    current_holdings: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="当前持仓字典，例如: {'600519': {'shares': 200, 'price': 1680.0}}"
    )
    target_symbols: List[str] = Field(..., description="目标持仓股票代码列表")
    strategy_type: str = Field(default="equal_weight", description="equal_weight 或 inverse_volatility")
    symbols_volatility: Optional[Dict[str, float]] = Field(default=None, description="各股票年化波动率(可选)")
    rebalance_threshold: float = Field(default=0.03, description="调仓摩擦阈值(低于3%偏离不换手)")


@router.post("/calculate-atr")
async def calculate_atr_sizing(req: ATRSizingRequest):
    """
    根据海龟 ATR 风险预算模型，精准测算建仓股数（整百股）与止损价位
    """
    res = PositionSizer.atr_risk_budget(
        total_capital=req.total_capital,
        price=req.price,
        atr_value=req.atr_value,
        risk_ratio=req.risk_ratio,
        stop_loss_atr_multiplier=req.stop_loss_atr_multiplier
    )
    return {"success": True, "data": res}


@router.post("/calculate-kelly")
async def calculate_kelly_sizing(req: KellySizingRequest):
    """
    根据半凯利公式 (Fractional Kelly) 计算数学期望最优建仓比例
    """
    res = PositionSizer.fractional_kelly(
        total_capital=req.total_capital,
        win_rate=req.win_rate,
        profit_loss_ratio=req.profit_loss_ratio,
        kelly_fraction=req.kelly_fraction,
        max_position_limit=req.max_position_limit
    )
    return {"success": True, "data": res}


@router.post("/rebalance-plan")
async def generate_rebalance_plan(req: RebalancePlanRequest):
    """
    生成组合再平衡计划，输出最小摩擦的买入/卖出调仓指令清单
    """
    optimizer = PortfolioOptimizer(
        rebalance_threshold=req.rebalance_threshold
    )
    plan = optimizer.generate_rebalance_plan(
        current_cash=req.current_cash,
        current_holdings=req.current_holdings,
        target_symbols=req.target_symbols,
        strategy_type=req.strategy_type,
        symbols_volatility=req.symbols_volatility
    )
    return {"success": True, "data": plan}
