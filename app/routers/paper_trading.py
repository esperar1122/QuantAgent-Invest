"""
虚拟模拟盘交易 REST API 路由
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.paper_trading.paper_account_service import paper_account_service
from app.services.notifier.wechat_notifier import wechat_notifier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/paper-trading", tags=["模拟交易"])


class PaperOrderRequest(BaseModel):
    symbol: str = Field(..., description="股票代码，例如 600519")
    name: str = Field(default="股票标的", description="股票名称")
    action: str = Field(..., description="BUY 或 SELL")
    shares: int = Field(..., gt=0, description="委托股数 (买入需为100整倍数)")
    price: Optional[float] = Field(default=None, description="委托价格 (若为空则自动获取当前最新市价)")
    order_type: str = Field(default="AUTO", description="委托类型: AUTO, MARKET, LIMIT")
    allow_queue: bool = Field(default=False, description="是否允许限价排队挂单")
    reason: str = Field(default="用户手动委托", description="委托理由")
    account_id: str = Field(default="default", description="模拟账户ID")


class CancelOrderRequest(BaseModel):
    order_id: str = Field(..., description="要撤销的委托ID")
    account_id: str = Field(default="default", description="模拟账户ID")


class WeChatTestRequest(BaseModel):
    webhook_url: Optional[str] = Field(default=None, description="企业微信Webhook链接(可选)")
    serverchan_key: Optional[str] = Field(default=None, description="Server酱SendKey(可选)")


@router.get("/account")
async def get_paper_account(account_id: str = Query("default", description="账户ID")):
    """
    获取虚拟模拟账户总览（现金、各持仓实时市值、浮动盈亏、历史净值曲线）
    """
    try:
        summary = await paper_account_service.get_account_summary(account_id)
        return {"success": True, "data": summary}
    except Exception as e:
        logger.error(f"获取模拟账户异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/order")
async def place_paper_order(req: PaperOrderRequest):
    """
    在虚拟账户中执行模拟买入/卖出委托（支持五档盘口深度撮合与排队挂单）
    """
    try:
        updated_summary = await paper_account_service.execute_trade(
            account_id=req.account_id,
            symbol=req.symbol,
            name=req.name,
            action=req.action,
            shares=req.shares,
            price=req.price,
            order_type=req.order_type,
            allow_queue=req.allow_queue,
            reason=req.reason
        )
        return {
            "success": True,
            "data": updated_summary,
            "message": f"模拟委托提交成功: {req.action} {req.name}({req.symbol}) {req.shares}股"
        }
    except ValueError as ve:
        return {"success": False, "data": None, "message": str(ve)}
    except Exception as e:
        logger.error(f"模拟委托执行异常: {e}")
        return {"success": False, "data": None, "message": f"系统错误: {str(e)}"}


@router.post("/cancel-order")
async def cancel_paper_order(req: CancelOrderRequest):
    """
    撤销排队挂单并释放冻结资金/持仓
    """
    try:
        updated_summary = await paper_account_service.cancel_order(
            account_id=req.account_id,
            order_id=req.order_id
        )
        return {
            "success": True,
            "data": updated_summary,
            "message": f"委托挂单 {req.order_id} 已成功撤销并释放冻结"
        }
    except ValueError as ve:
        return {"success": False, "data": None, "message": str(ve)}
    except Exception as e:
        logger.error(f"撤单异常: {e}")
        return {"success": False, "data": None, "message": f"系统错误: {str(e)}"}


@router.post("/test-wechat")
async def test_wechat_notification(req: WeChatTestRequest):
    """
    测试微信机器人/Server酱信号推送联通性
    """
    from app.services.notifier.wechat_notifier import WeChatNotifier
    notifier = WeChatNotifier(
        wecom_webhook=req.webhook_url,
        serverchan_key=req.serverchan_key
    )
    ok = await notifier.send_signal_alert(
        symbol="600519",
        name="贵州茅台",
        action="BUY",
        price=1680.00,
        shares=200,
        reason="【测试联通性】双均线策略金叉信号触发，ATR模型计算建仓2手",
        stop_loss_price=1620.00,
        target_price=1850.00
    )
    return {
        "success": ok,
        "message": "测试信号已发送，请检查微信/企业微信群是否收到提醒" if ok else "发送失败，请检查 Webhook 或 SendKey 配置"
    }
