#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一股票数据服务（A股专属，支持多数据源）

港股与美股模块已下线，系统专注于中国A股市场。
"""

import logging
from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger("webapi")


class UnifiedStockService:
    """统一股票数据服务（A股专属，支持多数据源）"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection_map = {
            "CN": {
                "basic_info": "stock_basic_info",
                "quotes": "market_quotes",
                "daily": "stock_daily_quotes",
                "financial": "stock_financial_data",
                "news": "stock_news"
            }
        }

    async def _get_source_priority(self) -> List[str]:
        try:
            groupings = await self.db.datasource_groupings.find(
                {"market_category_id": "a_shares", "enabled": True}
            ).sort("priority", -1).to_list(length=None)
            if groupings:
                return [g["data_source_name"] for g in groupings]
        except Exception as e:
            logger.warning(f"从数据库读取数据源优先级失败: {e}")
        return ["tushare", "akshare", "baostock"]

    async def get_stock_info(self, market: str, code: str, source: Optional[str] = None) -> Optional[Dict]:
        if market.upper() != "CN":
            return None
        col = self.db[self.collection_map["CN"]["basic_info"]]
        if source:
            return await col.find_one({"code": code, "source": source}, {"_id": 0})
        for src in await self._get_source_priority():
            doc = await col.find_one({"code": code, "source": src}, {"_id": 0})
            if doc:
                return doc
        return await col.find_one({"code": code}, {"_id": 0})

    async def get_stock_quote(self, market: str, code: str) -> Optional[Dict]:
        if market.upper() != "CN":
            return None
        return await self.db[self.collection_map["CN"]["quotes"]].find_one({"code": code}, {"_id": 0})

    async def search_stocks(self, market: str, query: str, limit: int = 20) -> List[Dict]:
        if market.upper() != "CN":
            return []
        col = self.db[self.collection_map["CN"]["basic_info"]]
        fq = {"$or": [{"code": {"$regex": query, "$options": "i"}}, {"name": {"$regex": query, "$options": "i"}}]}
        all_results = await col.find(fq).to_list(length=None)
        if not all_results:
            return []
        priority = await self._get_source_priority()
        unique: Dict[str, Dict] = {}
        for doc in all_results:
            c = doc.get("code")
            s = doc.get("source")
            if c not in unique:
                unique[c] = doc
            else:
                cs = unique[c].get("source")
                try:
                    if s in priority and cs in priority and priority.index(s) < priority.index(cs):
                        unique[c] = doc
                except ValueError:
                    pass
        result = list(unique.values())[:limit]
        logger.info(f"搜索A股: '{query}' -> {len(result)} 条结果")
        return result

    async def get_daily_quotes(self, market: str, code: str, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 100) -> List[Dict]:
        if market.upper() != "CN":
            return []
        col = self.db[self.collection_map["CN"]["daily"]]
        q: Dict = {"code": code}
        if start_date or end_date:
            q["trade_date"] = {}
            if start_date:
                q["trade_date"]["$gte"] = start_date
            if end_date:
                q["trade_date"]["$lte"] = end_date
        return await col.find(q, {"_id": 0}).sort("trade_date", -1).limit(limit).to_list(length=limit)

    async def get_supported_markets(self) -> List[Dict]:
        return [{"code": "CN", "name": "A股", "name_en": "China A-Share", "currency": "CNY", "timezone": "Asia/Shanghai"}]
