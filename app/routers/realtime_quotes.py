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
