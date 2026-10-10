"""
股票池与多维量化筛选业务服务
负责全市场档案与实时行情的多因子预筛选、聚合管道、量化全息画像装配与分页排序
"""

import asyncio
from typing import Optional, Union, Dict, Any, List
from app.quant_engine import QuantCoreEngine


class StockPoolService:
    """股票池多维量化筛选与状态装配服务"""

    @staticmethod
    def _num(v: Any) -> Optional[float]:
        if v is None or hasattr(v, "default") or v == "" or v == "null" or v == "undefined":
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _str(v: Any) -> Optional[str]:
        if v is None or hasattr(v, "default") or v == "" or v == "null" or v == "undefined":
            return None
        return str(v)

    @staticmethod
    def _bool(v: Any) -> bool:
        if v is None or hasattr(v, "default") or v == "" or v == "null" or v == "undefined":
            return False
        if isinstance(v, bool):
            return v
        return str(v).lower() in ["true", "1", "yes"]

    @staticmethod
    def _parse_amount_wan(val: Optional[float]) -> Optional[float]:
        if val is None:
            return None
        if val <= 1000.0:
            return val * 10000.0
        if val >= 100000.0:
            return val / 10000.0
        return val

    async def get_quant_candidate_strategy(self, db) -> dict:
        """获取量化初筛候选池策略配置（动态同源）"""
        strat = await db["user_quant_strategies"].find_one({"id": "preset_quant_candidate"})
        if strat and isinstance(strat.get("params"), dict):
            return strat["params"]
        return {
            "preset": "quant_candidate",
            "min_pe": 0.01,
            "max_pe": 60.0,
            "min_amount": 80_000_000.0
        }

    async def query_stock_pool(
        self,
        db,
        preset: Optional[str] = None,
        keyword: Optional[str] = None,
        market: Optional[str] = None,
        source: Optional[str] = None,
        min_pe: Optional[Union[float, str]] = None,
        max_pe: Optional[Union[float, str]] = None,
        min_pb: Optional[Union[float, str]] = None,
        max_pb: Optional[Union[float, str]] = None,
        min_ps: Optional[Union[float, str]] = None,
        max_ps: Optional[Union[float, str]] = None,
        min_close: Optional[Union[float, str]] = None,
        max_close: Optional[Union[float, str]] = None,
        min_pct_chg: Optional[Union[float, str]] = None,
        max_pct_chg: Optional[Union[float, str]] = None,
        volume_level: Optional[str] = None,
        min_turnover_rate: Optional[Union[float, str]] = None,
        max_turnover_rate: Optional[Union[float, str]] = None,
        min_volume_ratio: Optional[Union[float, str]] = None,
        max_volume_ratio: Optional[Union[float, str]] = None,
        market_cap_range: Optional[str] = None,
        min_market_cap: Optional[Union[float, str]] = None,
        max_market_cap: Optional[Union[float, str]] = None,
        min_roe: Optional[Union[float, str]] = None,
        max_roe: Optional[Union[float, str]] = None,
        min_net_profit_growth: Optional[Union[float, str]] = None,
        max_net_profit_growth: Optional[Union[float, str]] = None,
        min_revenue_growth: Optional[Union[float, str]] = None,
        max_revenue_growth: Optional[Union[float, str]] = None,
        min_gross_margin: Optional[Union[float, str]] = None,
        max_gross_margin: Optional[Union[float, str]] = None,
        min_risk_reward_ratio: Optional[Union[float, str]] = None,
        max_risk_reward_ratio: Optional[Union[float, str]] = None,
        min_amount: Optional[Union[float, str]] = None,
        max_amount: Optional[Union[float, str]] = None,
        min_north_ratio: Optional[Union[float, str]] = None,
        max_north_ratio: Optional[Union[float, str]] = None,
        is_heavy_north: Optional[Union[bool, str]] = None,
        ma_bullish_only: Optional[Union[bool, str]] = None,
        above_ma20_only: Optional[Union[bool, str]] = None,
        min_profit_ratio: Optional[Union[float, str]] = None,
        max_concentration_90: Optional[Union[float, str]] = None,
        exclude_st: Optional[Union[bool, str]] = None,
        max_debt_ratio: Optional[Union[float, str]] = None,
        page: int = 1,
        page_size: int = 20,
        sort_field: str = "code",
        sort_order: str = "asc"
    ) -> Dict[str, Any]:
        """A股股票池列表与多维量化筛选业务实现"""
        c_preset = self._str(preset)
        c_min_close = self._num(min_close)
        c_max_close = self._num(max_close)
        c_min_pct_chg = self._num(min_pct_chg)
        c_max_pct_chg = self._num(max_pct_chg)
        c_min_tr = self._num(min_turnover_rate)
        c_max_tr = self._num(max_turnover_rate)
        c_min_vr = self._num(min_volume_ratio)
        c_max_vr = self._num(max_volume_ratio)
        c_vol_level = self._str(volume_level)
        c_kw = self._str(keyword)
        c_market = self._str(market)
        c_source = self._str(source)
        c_min_pe = self._num(min_pe)
        c_max_pe = self._num(max_pe)
        c_min_pb = self._num(min_pb)
        c_max_pb = self._num(max_pb)
        c_min_ps = self._num(min_ps)
        c_max_ps = self._num(max_ps)
        c_cap_range = self._str(market_cap_range)
        c_min_cap = self._num(min_market_cap)
        c_max_cap = self._num(max_market_cap)
        c_min_roe = self._num(min_roe)
        c_max_roe = self._num(max_roe)
        c_min_npg = self._num(min_net_profit_growth)
        c_max_npg = self._num(max_net_profit_growth)
        c_min_rg = self._num(min_revenue_growth)
        c_max_rg = self._num(max_revenue_growth)
        c_min_gm = self._num(min_gross_margin)
        c_max_gm = self._num(max_gross_margin)
        c_min_rrr = self._num(min_risk_reward_ratio)
        c_max_rrr = self._num(max_risk_reward_ratio)
        c_min_amount = self._num(min_amount)
        c_max_amount = self._num(max_amount)
        c_sort_field = self._str(sort_field) or "code"
        c_sort_order = self._str(sort_order) or "asc"
        c_page = int(self._num(page) or 1)
        c_page_size = int(self._num(page_size) or 20)

        c_min_north = self._num(min_north_ratio)
        c_max_north = self._num(max_north_ratio)
        c_is_heavy_north = self._bool(is_heavy_north)
        c_ma_bullish_only = self._bool(ma_bullish_only)
        c_above_ma20_only = self._bool(above_ma20_only)
        c_min_profit_ratio = self._num(min_profit_ratio)
        c_max_conc90 = self._num(max_concentration_90)
        c_exclude_st = self._bool(exclude_st) if exclude_st is not None else False
        c_max_debt = self._num(max_debt_ratio)

        # 1. 行情条件预筛选 (market_quotes) - amount 存储单位为万元
        quote_filter: Dict[str, Any] = {}
        cand_params: Optional[Dict[str, Any]] = None
        if c_preset == "quant_candidate":
            cand_params = await self.get_quant_candidate_strategy(db)
            cand_min_amount = cand_params.get("min_amount")
            if cand_min_amount is not None:
                cand_wan = self._parse_amount_wan(float(cand_min_amount))
                if cand_wan is not None:
                    quote_filter.setdefault("amount", {})["$gte"] = cand_wan
            else:
                quote_filter.setdefault("amount", {})["$gte"] = 8000.0

        min_amt_wan = self._parse_amount_wan(c_min_amount)
        max_amt_wan = self._parse_amount_wan(c_max_amount)
        if min_amt_wan is not None:
            quote_filter.setdefault("amount", {})["$gte"] = min_amt_wan
        if max_amt_wan is not None:
            quote_filter.setdefault("amount", {})["$lte"] = max_amt_wan

        if min_amt_wan is None and max_amt_wan is None:
            if c_vol_level == "high":
                quote_filter.setdefault("amount", {})["$gte"] = 100000.0
            elif c_vol_level == "medium":
                quote_filter.setdefault("amount", {})["$gte"] = 30000.0
                quote_filter.setdefault("amount", {})["$lt"] = 100000.0
            elif c_vol_level == "low":
                quote_filter.setdefault("amount", {})["$lt"] = 30000.0

        if c_min_close is not None:
            quote_filter.setdefault("close", {})["$gte"] = c_min_close
        if c_max_close is not None:
            quote_filter.setdefault("close", {})["$lte"] = c_max_close
        if c_min_pct_chg is not None:
            quote_filter.setdefault("pct_chg", {})["$gte"] = c_min_pct_chg
        if c_max_pct_chg is not None:
            quote_filter.setdefault("pct_chg", {})["$lte"] = c_max_pct_chg
        if c_min_tr is not None:
            quote_filter.setdefault("turnover_rate", {})["$gte"] = c_min_tr
        if c_max_tr is not None:
            quote_filter.setdefault("turnover_rate", {})["$lte"] = c_max_tr
        if c_min_vr is not None:
            quote_filter.setdefault("volume_ratio", {})["$gte"] = c_min_vr
        if c_max_vr is not None:
            quote_filter.setdefault("volume_ratio", {})["$lte"] = c_max_vr
        if c_min_rrr is not None:
            quote_filter.setdefault("risk_reward_ratio", {})["$gte"] = c_min_rrr
        if c_max_rrr is not None:
            quote_filter.setdefault("risk_reward_ratio", {})["$lte"] = c_max_rrr

        quote_codes = None
        if quote_filter:
            quote_codes = await db["market_quotes"].distinct("code", quote_filter)

        # 2. 构造基础信息过滤条件（剔除退市标的）
        name_regex = r"退|^PT|ST|\*ST" if c_exclude_st else r"退|^PT"
        filter_query: Dict[str, Any] = {
            "name": {"$not": {"$regex": name_regex, "$options": "i"}},
            "status": {"$nin": ["0", "delisted", "D", "退市"]}
        }
        if c_max_debt is not None:
            filter_query["debt_ratio"] = {"$lte": c_max_debt}
        if quote_codes is not None:
            filter_query["code"] = {"$in": quote_codes}

        if c_kw and c_kw.strip():
            kw_clean = c_kw.strip()
            filter_query["$and"] = [
                {
                    "$or": [
                        {"code": {"$regex": kw_clean, "$options": "i"}},
                        {"name": {"$regex": kw_clean, "$options": "i"}},
                        {"symbol": {"$regex": kw_clean, "$options": "i"}}
                    ]
                }
            ]
        if c_market and c_market != "全部":
            filter_query["market"] = c_market
        if c_source and c_source != "全部":
            filter_query["source"] = c_source

        # 估值因子
        if c_min_pe is not None:
            filter_query.setdefault("pe", {})["$gte"] = c_min_pe
        elif cand_params and cand_params.get("min_pe") is not None:
            filter_query.setdefault("pe", {})["$gt"] = float(cand_params["min_pe"])
        elif c_preset == "quant_candidate":
            filter_query.setdefault("pe", {})["$gt"] = 0

        if c_max_pe is not None:
            filter_query.setdefault("pe", {})["$lte"] = c_max_pe
        elif cand_params and cand_params.get("max_pe") is not None:
            filter_query.setdefault("pe", {})["$lte"] = float(cand_params["max_pe"])
        elif c_preset == "quant_candidate":
            filter_query.setdefault("pe", {})["$lte"] = 60

        if c_min_pb is not None:
            filter_query.setdefault("pb", {})["$gte"] = c_min_pb
        elif cand_params and cand_params.get("min_pb") is not None:
            filter_query.setdefault("pb", {})["$gte"] = float(cand_params["min_pb"])

        if c_max_pb is not None:
            filter_query.setdefault("pb", {})["$lte"] = c_max_pb
        elif cand_params and cand_params.get("max_pb") is not None:
            filter_query.setdefault("pb", {})["$lte"] = float(cand_params["max_pb"])

        if c_min_ps is not None:
            filter_query.setdefault("ps", {})["$gte"] = c_min_ps
        if c_max_ps is not None:
            filter_query.setdefault("ps", {})["$lte"] = c_max_ps

        # 市值筛选
        if c_min_cap is not None:
            filter_query.setdefault("total_mv", {})["$gte"] = c_min_cap
        if c_max_cap is not None:
            filter_query.setdefault("total_mv", {})["$lte"] = c_max_cap

        if c_min_cap is None and c_max_cap is None:
            if c_cap_range == "small":
                filter_query.setdefault("total_mv", {})["$lt"] = 100.0
            elif c_cap_range == "medium":
                filter_query.setdefault("total_mv", {})["$gte"] = 100.0
                filter_query.setdefault("total_mv", {})["$lt"] = 500.0
            elif c_cap_range == "large":
                filter_query.setdefault("total_mv", {})["$gte"] = 500.0

        # 财务因子
        if c_min_roe is not None:
            filter_query.setdefault("roe", {})["$gte"] = c_min_roe
        elif cand_params and cand_params.get("min_roe") is not None:
            filter_query.setdefault("roe", {})["$gte"] = float(cand_params["min_roe"])
        if c_max_roe is not None:
            filter_query.setdefault("roe", {})["$lte"] = c_max_roe
        if c_min_npg is not None:
            filter_query.setdefault("net_profit_growth", {})["$gte"] = c_min_npg
        if c_max_npg is not None:
            filter_query.setdefault("net_profit_growth", {})["$lte"] = c_max_npg
        if c_min_rg is not None:
            filter_query.setdefault("revenue_growth", {})["$gte"] = c_min_rg
        if c_max_rg is not None:
            filter_query.setdefault("revenue_growth", {})["$lte"] = c_max_rg
        if c_min_gm is not None:
            filter_query.setdefault("gross_margin", {})["$gte"] = c_min_gm
        if c_max_gm is not None:
            filter_query.setdefault("gross_margin", {})["$lte"] = c_max_gm

        total = await db["stock_basic_info"].count_documents(filter_query)

        # 3. 分页与全局排序
        direction = 1 if c_sort_order.lower() == "asc" else -1
        skip = (c_page - 1) * c_page_size

        if c_sort_field in ["close", "pct_chg", "amount", "volume", "turnover_rate", "volume_ratio", "pe", "pb", "total_mv", "circ_mv", "risk_reward_ratio"]:
            mq_query = {"code": {"$in": quote_codes}} if quote_codes is not None else {}
            cursor = db["market_quotes"].find(mq_query, {"code": 1, c_sort_field: 1}).sort(c_sort_field, direction)
            sorted_quote_codes = [doc["code"] async for doc in cursor]

            all_matching_codes = set(await db["stock_basic_info"].distinct("code", filter_query))
            final_sorted_codes = [c for c in sorted_quote_codes if c in all_matching_codes]
            total = len(final_sorted_codes)
            page_codes = final_sorted_codes[skip : skip + c_page_size]

            items_map = {doc["code"]: doc async for doc in db["stock_basic_info"].find({"code": {"$in": page_codes}}, {"_id": 0})}
            items = [items_map[c] for c in page_codes if c in items_map]
        else:
            mongo_sort_field = c_sort_field if c_sort_field in [
                "code", "name", "pe", "pb", "ps", "total_mv", "circ_mv", "turnover_rate",
                "roe", "net_profit_growth", "revenue_growth", "gross_margin", "risk_reward_ratio"
            ] else "code"
            cursor = db["stock_basic_info"].find(filter_query, {"_id": 0}).sort(mongo_sort_field, direction).skip(skip).limit(c_page_size)
            items = await cursor.to_list(length=c_page_size)

        # 4. 批量关联行情数据并装配量化全息画像
        codes = [item.get("code") for item in items if item.get("code")]
        quote_map = {}
        if codes:
            quotes = await db["market_quotes"].find({"code": {"$in": codes}}, {"_id": 0}).to_list(length=len(codes))
            quote_map = {q["code"]: q for q in quotes if "code" in q}

        enriched_items = []
        for item in items:
            code = item.get("code") or item.get("symbol") or ""
            q = quote_map.get(code, {})

            close = q.get("close") if q.get("close") is not None else item.get("close")
            updated_at = item.get("updated_at")
            if hasattr(updated_at, "isoformat"):
                updated_at = updated_at.isoformat()

            turnover_rate = q.get("turnover_rate") if q.get("turnover_rate") is not None else item.get("turnover_rate")
            volume_ratio = q.get("volume_ratio") if q.get("volume_ratio") is not None else item.get("volume_ratio")
            circ_mv = q.get("circ_mv") if q.get("circ_mv") is not None else item.get("circ_mv")
            total_mv = q.get("total_mv") if q.get("total_mv") is not None else item.get("total_mv")

            pe = q.get("pe") if q.get("pe") is not None else item.get("pe")
            pb = q.get("pb") if q.get("pb") is not None else item.get("pb")
            ps = q.get("ps") if q.get("ps") is not None else item.get("ps")
            roe = item.get("roe") if item.get("roe") is not None else q.get("roe")
            net_profit_growth = item.get("net_profit_growth") if item.get("net_profit_growth") is not None else q.get("net_profit_growth")
            revenue_growth = item.get("revenue_growth") if item.get("revenue_growth") is not None else q.get("revenue_growth")
            gross_margin = item.get("gross_margin") if item.get("gross_margin") is not None else q.get("gross_margin")
            debt_ratio = item.get("debt_ratio") if item.get("debt_ratio") is not None else q.get("debt_ratio")
            north_ratio = float(item.get("north_hold_ratio") or q.get("north_hold_ratio") or 0.0)

            # 统一量化引擎评估全息画像 (Regime + R:R + Tech + Risk)
            ev = QuantCoreEngine.evaluate_stock(item, q)
            risk_reward_ratio = ev["risk_reward"]["risk_reward_ratio"]
            regime = ev["regime"]
            ma_bullish = ev["technical"]["ma_bullish"]
            above_ma20 = ev["technical"]["above_ma20"]
            risk_passed = ev["risk_control"]["is_passed"]
            target_price = ev["risk_reward"]["target_price"]
            stop_price = ev["risk_reward"]["stop_price"]

            # 异步回写更新到 market_quotes 以便全局排序索引
            if risk_reward_ratio is not None and code and q.get("risk_reward_ratio") != risk_reward_ratio:
                try:
                    asyncio.create_task(db["market_quotes"].update_one(
                        {"code": code},
                        {"$set": {"risk_reward_ratio": risk_reward_ratio}}
                    ))
                except Exception:
                    pass

            enriched_items.append({
                "code": code,
                "symbol": code,
                "name": item.get("name", ""),
                "market": item.get("market", "主板"),
                "industry": item.get("industry") or "A股通用",
                "source": item.get("source", "baostock"),
                "close": close,
                "pct_chg": q.get("pct_chg"),
                "amount": q.get("amount"),
                "volume": q.get("volume"),
                "turnover_rate": turnover_rate,
                "volume_ratio": volume_ratio,
                "pe": pe,
                "pb": pb,
                "ps": ps,
                "circ_mv": circ_mv,
                "total_mv": total_mv,
                "roe": roe,
                "net_profit_growth": net_profit_growth,
                "revenue_growth": revenue_growth,
                "gross_margin": gross_margin,
                "debt_ratio": debt_ratio,
                "risk_reward_ratio": risk_reward_ratio,
                "regime": regime,
                "target_price": target_price,
                "stop_price": stop_price,
                "ma_bullish": ma_bullish,
                "above_ma20": above_ma20,
                "risk_passed": risk_passed,
                "north_ratio": north_ratio,
                "trade_date": q.get("trade_date") or item.get("trade_date", ""),
                "updated_at": updated_at
            })

        # 4.1 盈亏比范围多维筛选
        if c_min_rrr is not None or c_max_rrr is not None:
            enriched_items = [
                itm for itm in enriched_items
                if itm.get("risk_reward_ratio") is not None
                and (c_min_rrr is None or itm["risk_reward_ratio"] >= c_min_rrr)
                and (c_max_rrr is None or itm["risk_reward_ratio"] <= c_max_rrr)
            ]

        # 4.2 技术面均线多头与生命线筛选
        if c_ma_bullish_only:
            enriched_items = [itm for itm in enriched_items if itm.get("ma_bullish")]
        if c_above_ma20_only:
            enriched_items = [itm for itm in enriched_items if itm.get("above_ma20")]

        # 4.3 资金面北向持股筛选
        if c_is_heavy_north:
            enriched_items = [itm for itm in enriched_items if (itm.get("north_ratio") or 0.0) >= 3.0]
        elif c_min_north is not None or c_max_north is not None:
            enriched_items = [
                itm for itm in enriched_items
                if (c_min_north is None or (itm.get("north_ratio") or 0.0) >= c_min_north)
                and (c_max_north is None or (itm.get("north_ratio") or 0.0) <= c_max_north)
            ]

        # 4.4 排除 ST 风险股 (后道二次防御)
        if c_exclude_st:
            enriched_items = [
                itm for itm in enriched_items
                if not any(tag in (itm.get("name") or "") for tag in ["ST", "*ST", "退"])
            ]

        # 按字段排序
        if sort_field in [
            "close", "pct_chg", "amount", "volume", "turnover_rate", "volume_ratio",
            "pe", "pb", "ps", "circ_mv", "total_mv", "roe", "net_profit_growth",
            "revenue_growth", "gross_margin", "risk_reward_ratio", "north_ratio"
        ]:
            reverse = (sort_order.lower() == "desc")
            enriched_items.sort(
                key=lambda x: (x.get(sort_field) is not None, x.get(sort_field) or 0),
                reverse=reverse
            )

        # 统计信息
        active_filter = {
            "name": {"$not": {"$regex": r"退|^PT"}},
            "status": {"$nin": ["0", "delisted", "D", "退市"]}
        }
        stats = {
            "total_stocks": await db["stock_basic_info"].count_documents(active_filter),
            "main_board_count": await db["stock_basic_info"].count_documents({**active_filter, "market": "主板"}),
            "chinext_count": await db["stock_basic_info"].count_documents({**active_filter, "market": "创业板"}),
            "star_count": await db["stock_basic_info"].count_documents({**active_filter, "market": "科创板"}),
            "bse_count": await db["stock_basic_info"].count_documents({**active_filter, "market": "北交所"}),
            "index_count": await db["stock_basic_info"].count_documents({**active_filter, "market": "重要指数"}),
        }

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": enriched_items,
            "stats": stats
        }


stock_pool_service = StockPoolService()
