"""
秒级实时行情 REST API 与 SSE 流式推送路由
"""

import asyncio
import json
import logging
from typing import List
from fastapi import APIRouter, Query
from sse_starlette.sse import EventSourceResponse

from app.services.quotes.realtime_streamer import get_quote_streamer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quotes", tags=["实时行情"])


@router.get("/live/{symbols}")
async def get_live_quotes(symbols: str):
    """
    极速获取指定股票池的实时买卖盘快照 (延迟 100~300ms)
    例如: /api/quotes/live/600519,000001,002594
    """
    sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
    if not sym_list:
        return {"success": False, "data": {}, "message": "代码列表为空"}

    streamer = get_quote_streamer()
    quotes = await streamer.fetch_batch_quotes(sym_list)
    return {"success": True, "data": quotes, "count": len(quotes)}


@router.get("/stream")
async def stream_live_quotes(symbols: str = Query(..., description="逗号分隔的股票代码列表")):
    """
    通过 Server-Sent Events (SSE) 持续秒级推流最新盘口快照
    前端直接建立 EventSource 即可接收毫秒级价格跳动
    """
    sym_list = [s.strip() for s in symbols.split(",") if s.strip()]

    async def event_generator():
        streamer = get_quote_streamer()
        while True:
            try:
                quotes = await streamer.fetch_batch_quotes(sym_list)
                if quotes:
                    yield {
                        "event": "quote_update",
                        "data": json.dumps(quotes, ensure_ascii=False)
                    }
                await asyncio.sleep(2.0)  # 2秒刷新间隔
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"SSE推流异常: {e}")
                await asyncio.sleep(3.0)

    return EventSourceResponse(event_generator())


@router.get("/indices")
async def get_live_indices():
    """
    极速获取四大核心宽基指数实时行情 (上证指数/深证成指/创业板指/科创50)
    毫秒级直连，防错校准，绝无点数/百分比混淆
    """
    streamer = get_quote_streamer()
    indices = await streamer.fetch_indices_quotes()
    return {"success": True, "data": {"indices": indices}, "count": len(indices)}


@router.get("/indices/stream")
async def stream_live_indices(interval: float = Query(2.5, ge=1.0, le=10.0, description="推流间隔(秒)")):
    """
    通过 Server-Sent Events (SSE) 持续秒级推流四大核心指数最新行情
    前端 TopTickerBar 与 MarketTrendChart 均可直接接入，彻底告别频繁轮询
    """
    import time

    async def event_generator():
        streamer = get_quote_streamer()
        while True:
            try:
                indices = await streamer.fetch_indices_quotes()
                payload = {
                    "indices": indices,
                    "timestamp": time.strftime("%H:%M:%S")
                }
                yield {
                    "event": "indices_update",
                    "data": json.dumps(payload, ensure_ascii=False)
                }
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"指数SSE推流异常: {e}")
                await asyncio.sleep(3.0)

    return EventSourceResponse(event_generator())
