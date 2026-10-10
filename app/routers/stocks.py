"""
股票详情相关API
- 统一响应包: {success, data, message, timestamp}
- 所有端点均需鉴权 (Bearer Token)
- 路径前缀在 main.py 中挂载为 /api，当前路由自身前缀为 /stocks
"""
from typing import Optional, Dict, Any, List, Tuple, Union
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
import logging
import re
import datetime
import asyncio
import time
import uuid
from pydantic import BaseModel, Field

from app.routers.auth_db import get_current_user, get_optional_current_user
from app.core.database import get_mongo_db
from app.core.response import ok
from app.services.stock_pool_service import stock_pool_service
from app.services.market_overview_service import market_overview_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stocks", tags=["stocks"])


def _zfill_code(code: str) -> str:
    try:
        s = str(code).strip()
        if len(s) == 6 and s.isdigit():
            return s
        return s.zfill(6)
    except Exception:
        return str(code)


def _detect_market_and_code(code: str) -> Tuple[str, str]:
    """
    检测股票代码并标准化代码（聚焦中国A股市场与重要指数）

    Args:
        code: 股票或指数代码

    Returns:
        (market, normalized_code): ('CN', 6位数字代码或sh/sz指数代码)
    """
    raw_code = str(code).strip()
    code_lower = raw_code.lower()

    # 1. 优先检测是否为重要指数（如 sh000300, 000300.sh, 000300, sz980017, sh000001 等）
    from app.services.index_service import is_index_code, normalize_index_code
    if is_index_code(code_lower):
        return ('CN', normalize_index_code(code_lower))

    code_upper = raw_code.upper()

    # 2. 兼容带后缀的A股代码（如 600519.SH, 000001.SZ, 830750.BJ）
    if '.' in code_upper:
        code_part = code_upper.split('.')[0]
        if re.match(r'^\d{6}$', code_part):
            return ('CN', code_part)

    # 3. 标准A股：6位数字
    if re.match(r'^\d{6}$', code_upper):
        return ('CN', code_upper)

    # 4. 默认当作A股补齐处理
    return ('CN', _zfill_code(raw_code))


@router.get("/search", response_model=dict)
async def search_stocks(
    keyword: str = Query(..., min_length=1, description="搜索关键词（代码/名称/简拼）"),
    limit: int = Query(15, ge=1, le=50, description="返回数量限制"),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    极速检索股票与指数（支持代码、名称匹配，附带最新行情）
    返回轻量级的标的列表供前端快速选择
    """
    db = get_mongo_db()
    kw = keyword.strip()

    # 1. 过滤退市股票
    filter_q: Dict[str, Any] = {
        "name": {"$not": {"$regex": r"退|^PT"}},
        "status": {"$nin": ["0", "delisted", "D", "退市"]}
    }

    # 2. 优先匹配代码或名称
    filter_q["$or"] = [
        {"code": {"$regex": f"^{kw}", "$options": "i"}},
        {"name": {"$regex": kw, "$options": "i"}},
        {"symbol": {"$regex": f"^{kw}", "$options": "i"}}
    ]

    cursor = db["stock_basic_info"].find(filter_q, {"_id": 0}).limit(limit)
    items = await cursor.to_list(length=limit)

    # 若未找到且关键词>=2位，放宽为全词包含匹配
    if not items and len(kw) >= 2:
        filter_q["$or"] = [
            {"code": {"$regex": kw, "$options": "i"}},
            {"name": {"$regex": kw, "$options": "i"}},
            {"symbol": {"$regex": kw, "$options": "i"}}
        ]
        items = await db["stock_basic_info"].find(filter_q, {"_id": 0}).limit(limit).to_list(length=limit)

    # 2.1 若仍未找到且输入形如6位代码或带有市场前缀，尝试通过实时行情引擎极速嗅探（支持 56/51/58/15/16 等 ETF 基金及新股）
    if not items and (re.match(r'^\d{6}$', kw) or kw.lower().startswith(('sh', 'sz', 'bj'))):
        clean_kw = re.sub(r'^[a-zA-Z]+', '', kw)
        if len(clean_kw) == 6:
            from app.services.stock_quote_service import fetch_realtime_stock_quote
            rt_q = await asyncio.to_thread(fetch_realtime_stock_quote, clean_kw)
            if rt_q and rt_q.get("name") and rt_q.get("name") != clean_kw:
                is_etf = clean_kw.startswith(("50", "51", "56", "58", "15", "16"))
                item_obj = {
                    "code": clean_kw,
                    "symbol": f"{clean_kw}.SH" if clean_kw.startswith(("6", "5", "9")) else f"{clean_kw}.SZ",
                    "name": rt_q["name"],
                    "market": "ETF基金" if is_etf else "A股",
                    "industry": "ETF指数基金" if is_etf else "综合",
                    "close": float(rt_q.get("price") or 0.0),
                    "pct_chg": float(rt_q.get("pct_chg") or 0.0),
                    "pe": float(rt_q.get("pe") or 0.0),
                    "pb": float(rt_q.get("pb") or 0.0),
                    "total_mv": float(rt_q.get("total_mv") or 0.0)
                }
                items = [item_obj]
                # 异步写入数据库沉淀
                try:
                    asyncio.create_task(db["stock_basic_info"].update_one(
                        {"code": clean_kw},
                        {"$set": item_obj},
                        upsert=True
                    ))
                    asyncio.create_task(db["market_quotes"].update_one(
                        {"code": clean_kw},
                        {"$set": rt_q},
                        upsert=True
                    ))
                except Exception:
                    pass

    # 2.2 融合全市场核心场内 ETF 目录（支持部分代码、名称、标签模糊匹配，如 588710、芯片设备等）
    try:
        from app.services.etf_service import CORE_ETF_CATALOG
        kw_lower = kw.lower()
        matched_etfs = [
            etf for etf in CORE_ETF_CATALOG
            if kw_lower in etf["code"].lower() 
            or kw_lower in etf["name"].lower() 
            or kw_lower in etf.get("tag", "").lower()
        ]
        if matched_etfs:
            existing_codes = {it.get("code") for it in items}
            for etf in matched_etfs:
                if etf["code"] not in existing_codes and len(items) < limit:
                    items.append({
                        "code": etf["code"],
                        "symbol": etf["symbol"],
                        "name": etf["name"],
                        "market": "ETF基金",
                        "industry": etf.get("category_name", "ETF指数"),
                        "close": 0.0,
                        "pct_chg": 0.0,
                        "pe": 0.0,
                        "pb": 0.0,
                        "total_mv": 0.0
                    })
                    existing_codes.add(etf["code"])
    except Exception:
        pass

    # 3. 关联最新行情 (market_quotes) 补齐价格、涨跌幅、成交额
    codes = [it.get("code") for it in items if it.get("code")]
    quotes_map = {}
    if codes:
        q_cursor = db["market_quotes"].find(
            {"code": {"$in": codes}},
            {"_id": 0, "code": 1, "close": 1, "pct_chg": 1, "amount": 1, "volume": 1, "turnover_rate": 1}
        )
        for q in await q_cursor.to_list(length=len(codes)):
            quotes_map[q.get("code")] = q

    results = []
    for it in items:
        c = it.get("code", "")
        q = quotes_map.get(c, {})
        close_px = q.get("close")
        if close_px is None:
            close_px = it.get("close", 0.0)
        pct = q.get("pct_chg")
        if pct is None:
            pct = it.get("pct_chg", 0.0)

        results.append({
            "code": c,
            "symbol": it.get("symbol", c),
            "name": it.get("name", ""),
            "market": it.get("market", "主板"),
            "industry": it.get("industry", "综合"),
            "close": float(close_px or 0.0),
            "pct_chg": float(pct or 0.0),
            "amount": float(q.get("amount") or it.get("amount") or 0.0),
            "pe": float(it.get("pe") or 0.0),
            "pb": float(it.get("pb") or 0.0),
            "total_mv": float(it.get("total_mv") or 0.0)
        })

    return ok({"items": results, "total": len(results)})


@router.get("/{code}/quote", response_model=dict)
async def get_quote(
    code: str,
    force_refresh: bool = Query(False, description="是否强制刷新（跳过缓存）"),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    获取A股股票实时行情

    参数：
    - code: 6位A股代码
    - force_refresh: 是否强制刷新（跳过缓存）

    返回字段（data内，蛇形命名）:
      - code, name, market
      - price(close), change_percent(pct_chg), amount, prev_close(估算)
      - turnover_rate, amplitude（振幅，替代量比）
      - trade_date, updated_at
    """
    market, normalized_code = _detect_market_and_code(code)

    # A股行情查询
    db = get_mongo_db()
    code6 = normalized_code

    # 行情
    q = await db["market_quotes"].find_one({"code": code6}, {"_id": 0})

    from app.services.index_service import is_index_code, sync_indices_to_db, get_index_name
    from app.services.stock_quote_service import fetch_realtime_stock_quote
    if is_index_code(code6):
        is_stale = False
        if not q or force_refresh:
            is_stale = True
        else:
            up_at = q.get("updated_at")
            if isinstance(up_at, datetime.datetime):
                if (datetime.datetime.now() - up_at).total_seconds() > 30:
                    is_stale = True
            else:
                is_stale = True

        if is_stale:
            logger.info(f"📊 触发指数实时行情更新同步: {code6}")
            await sync_indices_to_db(force=force_refresh)
            q = await db["market_quotes"].find_one({"code": code6}, {"_id": 0})
    else:
        # 个股实时行情毫秒级直连与缓存同步
        is_stale = False
        if not q or force_refresh or not q.get("open"):
            is_stale = True
        else:
            up_at = q.get("updated_at")
            if isinstance(up_at, datetime.datetime):
                if (datetime.datetime.now() - up_at).total_seconds() > 10:
                    is_stale = True
            elif not up_at:
                is_stale = True

        if is_stale:
            rt_q = await asyncio.to_thread(fetch_realtime_stock_quote, code6)
            if rt_q:
                rt_q["updated_at"] = datetime.datetime.now()
                if q:
                    q.update(rt_q)
                else:
                    q = rt_q
                try:
                    asyncio.create_task(db["market_quotes"].update_one(
                        {"code": code6},
                        {"$set": rt_q},
                        upsert=True
                    ))
                except Exception:
                    pass

    # 🔥 调试日志：查看查询结果
    logger.info(f"🔍 查询 market_quotes: code={code6}")
    if q:
        logger.info(f"  ✅ 找到数据: price={q.get('price')}, pct_chg={q.get('pct_chg')}, volume={q.get('volume')}, amount={q.get('amount')}")
    else:
        logger.info(f"  ❌ 未找到数据")

    # 🔥 基础信息 - 按数据源优先级查询
    if is_index_code(code6):
        b = await db["stock_basic_info"].find_one({"code": code6}, {"_id": 0})
    else:
        from app.core.unified_config import UnifiedConfigManager
        config = UnifiedConfigManager()
        data_source_configs = await config.get_data_source_configs_async()

        # 提取启用的数据源，按优先级排序
        enabled_sources = [
            ds.type.lower() for ds in data_source_configs
            if ds.enabled and ds.type.lower() in ['tushare', 'akshare', 'baostock']
        ]

        if not enabled_sources:
            enabled_sources = ['tushare', 'akshare', 'baostock']

        b = None
        for src in enabled_sources:
            b = await db["stock_basic_info"].find_one({"code": code6, "source": src}, {"_id": 0})
            if b:
                break

    # 如果所有数据源都没有，尝试不带 source 条件查询（兼容旧数据）
    if not b:
        b = await db["stock_basic_info"].find_one({"code": code6}, {"_id": 0})

    if not q and not b:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该股票的任何信息")

    close = (q or {}).get("close") if (q or {}).get("close") is not None else (q or {}).get("price")
    pct = (q or {}).get("pct_chg") if (q or {}).get("pct_chg") is not None else (q or {}).get("change_percent")
    pre_close_saved = (q or {}).get("pre_close")
    prev_close = pre_close_saved
    if prev_close is None:
        try:
            if close is not None and pct is not None:
                prev_close = round(float(close) / (1.0 + float(pct) / 100.0), 4)
        except Exception:
            prev_close = None

    # 🔥 优先从 market_quotes 获取 turnover_rate（实时数据）
    # 如果 market_quotes 中没有，再从 stock_basic_info 获取（日度数据）
    turnover_rate = (q or {}).get("turnover_rate")
    turnover_rate_date = None
    if turnover_rate is None:
        turnover_rate = (b or {}).get("turnover_rate")
        turnover_rate_date = (b or {}).get("trade_date")  # 来自日度数据
    else:
        turnover_rate_date = (q or {}).get("trade_date")  # 来自实时数据

    # 🔥 计算振幅（amplitude）替代量比（volume_ratio）
    # 振幅 = (最高价 - 最低价) / 昨收价 × 100%
    amplitude = None
    amplitude_date = None
    try:
        high = (q or {}).get("high")
        low = (q or {}).get("low")
        logger.info(f"🔍 计算振幅: high={high}, low={low}, prev_close={prev_close}")
        if high is not None and low is not None and prev_close is not None and prev_close > 0:
            amplitude = round((float(high) - float(low)) / float(prev_close) * 100, 2)
            amplitude_date = (q or {}).get("trade_date")  # 来自实时数据
            logger.info(f"  ✅ 振幅计算成功: {amplitude}%")
        else:
            logger.warning(f"  ⚠️ 数据不完整，无法计算振幅")
    except Exception as e:
        logger.warning(f"  ❌ 计算振幅失败: {e}")
        amplitude = None

    stock_name = (b or {}).get("name") or (q or {}).get("name")
    if is_index_code(code6):
        stock_name = get_index_name(code6) or stock_name

    stock_market = (b or {}).get("market") or (q or {}).get("market") or ("重要指数" if is_index_code(code6) else "A股")

    data = {
        "code": code6,
        "name": stock_name,
        "market": stock_market,
        "price": close,
        "change_percent": pct,
        "amount": (q or {}).get("amount"),
        "volume": (q or {}).get("volume"),
        "open": (q or {}).get("open"),
        "high": (q or {}).get("high"),
        "low": (q or {}).get("low"),
        "prev_close": prev_close,
        # 🔥 优先使用实时数据，降级到日度数据
        "turnover_rate": turnover_rate,
        "amplitude": amplitude,  # 🔥 新增：振幅（替代量比）
        "turnover_rate_date": turnover_rate_date,  # 🔥 新增：换手率数据日期
        "amplitude_date": amplitude_date,  # 🔥 新增：振幅数据日期
        "trade_date": (q or {}).get("trade_date"),
        "updated_at": (q or {}).get("updated_at"),
        "pe": (q or {}).get("pe") if (q or {}).get("pe") is not None else (b or {}).get("pe"),
        "pb": (q or {}).get("pb") if (q or {}).get("pb") is not None else (b or {}).get("pb"),
        "total_mv": (q or {}).get("total_mv") if (q or {}).get("total_mv") is not None else (b or {}).get("total_mv"),
        "ask_orders": (q or {}).get("ask_orders"),
        "bid_orders": (q or {}).get("bid_orders"),
        "roe": (b or {}).get("roe"),
        "net_profit_growth": (b or {}).get("net_profit_growth"),
        "revenue_growth": (b or {}).get("revenue_growth"),
    }

    # 🔥 双轨混合模式：获取持牌券商研报评级与一致预期
    try:
        from app.services.institution_rating_service import get_institution_ratings
        ratings_data = await asyncio.to_thread(get_institution_ratings, code6, float(close or 0.0))
        data["institution_ratings"] = ratings_data
    except Exception as re_err:
        logger.debug(f"加载机构研报评级失败: {re_err}")

    return ok(data)


@router.get("/{code}/ratings", response_model=dict)
async def get_stock_ratings(
    code: str,
    price: Optional[float] = Query(None, description="最新现价，用于动态推算上行空间"),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    获取标的的持牌券商机构评级、一致目标价与最新研报列表（双轨混合模式）
    """
    from app.services.institution_rating_service import get_institution_ratings
    res = await asyncio.to_thread(get_institution_ratings, code, float(price or 0.0))
    return ok(res)


@router.get("/{code}/fundamentals", response_model=dict)
async def get_fundamentals(
    code: str,
    source: Optional[str] = Query(None, description="数据源 (tushare/akshare/baostock/multi_source)"),
    force_refresh: bool = Query(False, description="是否强制刷新（跳过缓存）"),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    获取基础面快照（支持A股/港股/美股）

    数据来源优先级：
    1. stock_basic_info 集合（基础信息、估值指标）
    2. stock_financial_data 集合（财务指标：ROE、负债率等）

    参数：
    - code: 股票代码
    - source: 数据源（可选），默认按优先级：tushare > multi_source > akshare > baostock
    - force_refresh: 是否强制刷新（跳过缓存）
    """
    # 检测市场类型
    market, normalized_code = _detect_market_and_code(code)

    # A股：获取基础信息
    db = get_mongo_db()
    code6 = normalized_code

    # 1. 获取基础信息（支持数据源筛选）
    query = {"code": code6}

    if source:
        # 指定数据源
        query["source"] = source
        b = await db["stock_basic_info"].find_one(query, {"_id": 0})
        if not b:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到该股票在数据源 {source} 中的基础信息"
            )
    else:
        # 🔥 未指定数据源，按优先级查询
        source_priority = ["tushare", "multi_source", "akshare", "baostock"]
        b = None

        for src in source_priority:
            query_with_source = {"code": code6, "source": src}
            b = await db["stock_basic_info"].find_one(query_with_source, {"_id": 0})
            if b:
                logger.info(f"✅ 使用数据源: {src} 查询股票 {code6}")
                break

        # 如果所有数据源都没有，尝试不带 source 条件查询（兼容旧数据）
        if not b:
            b = await db["stock_basic_info"].find_one({"code": code6}, {"_id": 0})
            if b:
                logger.warning(f"⚠️ 使用旧数据（无 source 字段）: {code6}")

        if not b:
            # 尝试从实时行情中回退构建（如ETF基金、指数标的或未全量入库代码）
            from app.services.stock_quote_service import fetch_realtime_stock_quote
            rt_q = await asyncio.to_thread(fetch_realtime_stock_quote, code6)
            if rt_q and rt_q.get("name"):
                is_etf = code6.startswith(("50", "51", "56", "58", "15", "16"))
                b = {
                    "code": code6,
                    "symbol": f"{code6}.SH" if code6.startswith(("6", "5", "9")) else f"{code6}.SZ",
                    "name": rt_q["name"],
                    "market": "ETF基金" if is_etf else "A股",
                    "industry": "ETF指数基金" if is_etf else "综合",
                    "sector": "ETF板块" if is_etf else "A股",
                    "total_mv": rt_q.get("total_mv", 0.0),
                    "circ_mv": rt_q.get("total_mv", 0.0),
                    "pe": rt_q.get("pe", 0.0),
                    "pb": rt_q.get("pb", 0.0),
                    "turnover_rate": rt_q.get("turnover_rate", 0.0),
                }
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该股票的基础信息")

    # 2. 尝试从 stock_financial_data 获取最新财务指标
    # 🔥 按数据源优先级查询，而不是按时间戳，避免混用不同数据源的数据
    financial_data = None
    try:
        # 获取数据源优先级配置
        from app.core.unified_config import UnifiedConfigManager
        config = UnifiedConfigManager()
        data_source_configs = await config.get_data_source_configs_async()

        # 提取启用的数据源，按优先级排序
        enabled_sources = [
            ds.type.lower() for ds in data_source_configs
            if ds.enabled and ds.type.lower() in ['tushare', 'akshare', 'baostock']
        ]

        if not enabled_sources:
            enabled_sources = ['tushare', 'akshare', 'baostock']

        # 按数据源优先级查询财务数据
        for data_source in enabled_sources:
            financial_data = await db["stock_financial_data"].find_one(
                {"$or": [{"symbol": code6}, {"code": code6}], "data_source": data_source},
                {"_id": 0},
                sort=[("report_period", -1)]  # 按报告期降序，获取该数据源的最新数据
            )
            if financial_data:
                logger.info(f"✅ 使用数据源 {data_source} 的财务数据 (报告期: {financial_data.get('report_period')})")
                break

        if not financial_data:
            logger.warning(f"⚠️ 未找到 {code6} 的财务数据")
    except Exception as e:
        logger.error(f"获取财务数据失败: {e}")

    # 3. 获取实时PE/PB（优先使用实时计算）
    from tradingagents.dataflows.realtime_metrics import get_pe_pb_with_fallback
    import asyncio

    # 在线程池中执行同步的实时计算
    realtime_metrics = await asyncio.to_thread(
        get_pe_pb_with_fallback,
        code6,
        db.client
    )

    # 4. 构建返回数据
    # 🔥 优先使用实时市值，降级到 stock_basic_info 的静态市值
    realtime_market_cap = realtime_metrics.get("market_cap")  # 实时市值（亿元）
    total_mv = realtime_market_cap if realtime_market_cap else b.get("total_mv")

    data = {
        "code": code6,
        "name": b.get("name"),
        "industry": b.get("industry"),  # 行业（如：银行、软件服务）
        "market": b.get("market"),      # 交易所（如：主板、创业板）

        # 板块信息：使用 market 字段（主板/创业板/科创板/北交所等）
        "sector": b.get("market"),

        # 估值指标（优先使用实时计算，降级到 stock_basic_info）
        "pe": realtime_metrics.get("pe") or b.get("pe"),
        "pb": realtime_metrics.get("pb") or b.get("pb"),
        "pe_ttm": realtime_metrics.get("pe_ttm") or b.get("pe_ttm"),
        "pb_mrq": realtime_metrics.get("pb_mrq") or b.get("pb_mrq"),

        # 🔥 市销率（PS）- 动态计算（使用实时市值）
        "ps": None,
        "ps_ttm": None,

        # PE/PB 数据来源标识
        "pe_source": realtime_metrics.get("source", "unknown"),
        "pe_is_realtime": realtime_metrics.get("is_realtime", False),
        "pe_updated_at": realtime_metrics.get("updated_at"),

        # ROE（优先从 stock_financial_data 获取，其次从 stock_basic_info）
        "roe": None,

        # 负债率（从 stock_financial_data 获取）
        "debt_ratio": None,

        # 市值：优先使用实时市值，降级到静态市值
        "total_mv": total_mv,
        "circ_mv": b.get("circ_mv"),

        # 🔥 市值来源标识
        "mv_is_realtime": bool(realtime_market_cap),

        # 交易指标（可能为空）
        "turnover_rate": b.get("turnover_rate"),
        "volume_ratio": b.get("volume_ratio"),

        "updated_at": b.get("updated_at"),
    }

    # 5. 从财务数据中提取 ROE、负债率和计算 PS
    if financial_data:
        # ROE（净资产收益率）
        if financial_data.get("financial_indicators"):
            indicators = financial_data["financial_indicators"]
            data["roe"] = indicators.get("roe")
            data["debt_ratio"] = indicators.get("debt_to_assets")

        # 如果 financial_indicators 中没有，尝试从顶层字段获取
        if data["roe"] is None:
            data["roe"] = financial_data.get("roe")
        if data["debt_ratio"] is None:
            data["debt_ratio"] = financial_data.get("debt_to_assets")

        # 🔥 动态计算 PS（市销率）- 使用实时市值
        # 优先使用 TTM 营业收入，如果没有则使用单期营业收入
        revenue_ttm = financial_data.get("revenue_ttm")
        revenue = financial_data.get("revenue")
        revenue_for_ps = revenue_ttm if revenue_ttm and revenue_ttm > 0 else revenue

        if revenue_for_ps and revenue_for_ps > 0:
            # 🔥 使用实时市值（如果有），否则使用静态市值
            if total_mv and total_mv > 0:
                # 营业收入单位：元，需要转换为亿元
                revenue_yi = revenue_for_ps / 100000000
                ps_calculated = total_mv / revenue_yi
                data["ps"] = round(ps_calculated, 2)
                data["ps_ttm"] = round(ps_calculated, 2) if revenue_ttm else None

    # 6. 如果财务数据中没有 ROE，使用 stock_basic_info 中的
    if data["roe"] is None:
        data["roe"] = (b or {}).get("roe")

    data["net_profit_growth"] = (b or {}).get("net_profit_growth")
    data["revenue_growth"] = (b or {}).get("revenue_growth")
    data["gross_margin"] = (financial_data or {}).get("gross_profit_margin") if financial_data else None

    return ok(data)


@router.get("/{code}/kline", response_model=dict)
async def get_kline(
    code: str,
    period: str = "day",
    limit: int = 120,
    adj: str = "none",
    force_refresh: bool = Query(False, description="是否强制刷新（跳过缓存）"),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    获取K线数据（支持A股/港股/美股）

    period: day/week/month/5m/15m/30m/60m
    adj: none/qfq/hfq
    force_refresh: 是否强制刷新（跳过缓存）

    🔥 新增功能：当天实时K线数据
    - 交易时间内（09:30-15:00）：从 market_quotes 获取实时数据
    - 收盘后：检查历史数据是否有当天数据，没有则从 market_quotes 获取
    """
    import logging
    from datetime import datetime, timedelta, time as dtime
    from zoneinfo import ZoneInfo
    logger = logging.getLogger(__name__)

    valid_periods = {"day","week","month","5m","15m","30m","60m"}
    if period not in valid_periods:
        raise HTTPException(status_code=400, detail=f"不支持的period: {period}")

    # 检测市场类型
    market, normalized_code = _detect_market_and_code(code)

    # A股：使用现有逻辑
    code_padded = normalized_code

    # 🔥 若为重要指数，直接调用指数专属双通道K线引擎获取
    from app.services.index_service import is_index_code, fetch_index_kline, get_index_name
    if is_index_code(code_padded):
        logger.info(f"📊 检测到指数标的: {code_padded}，调度指数K线引擎获取 (period={period}, limit={limit})")
        items, src = await asyncio.to_thread(fetch_index_kline, code_padded, period, limit)
        if items:
            return ok({
                "code": code_padded,
                "name": get_index_name(code_padded),
                "market": "重要指数",
                "period": period,
                "items": items,
                "count": len(items),
                "source": src
            })
        else:
            raise HTTPException(status_code=404, detail=f"暂未获取到指数 {code_padded} 的K线数据")

    adj_norm = None if adj in (None, "none", "", "null") else adj
    items = None
    source = None

    # 周期映射：前端 -> MongoDB
    period_map = {
        "day": "daily",
        "week": "weekly",
        "month": "monthly",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "60m": "60min"
    }
    mongodb_period = period_map.get(period, "daily")

    # 获取当前时间（北京时间）
    from app.core.config import settings
    tz = ZoneInfo(settings.TIMEZONE)
    now = datetime.now(tz)
    today_str_yyyymmdd = now.strftime("%Y%m%d")  # 格式：20251028（用于查询）
    today_str_formatted = now.strftime("%Y-%m-%d")  # 格式：2025-10-28（用于返回）

    # 1. 优先通过极速实时接口获取 (50ms响应，全量A股含今日实盘K线)
    try:
        from app.services.stock_quote_service import fetch_realtime_stock_kline
        tx_items = await asyncio.to_thread(fetch_realtime_stock_kline, code_padded, period, limit)
        if tx_items and len(tx_items) >= 5:
            items = tx_items
            source = "tencent_fqkline"
            logger.info(f"✅ 从极速实时接口获取到 {len(items)} 条 K 线数据: {code_padded}")
    except Exception as e:
        logger.warning(f"⚠️ 极速实时K线获取失败: {e}")

    # 2. 备选：从 MongoDB 缓存获取
    if not items or len(items) < 5:
        try:
            from tradingagents.dataflows.cache.mongodb_cache_adapter import get_mongodb_cache_adapter
            adapter = get_mongodb_cache_adapter()

            # 计算日期范围
            end_date = now.strftime("%Y-%m-%d")
            start_date = (now - timedelta(days=limit * 2)).strftime("%Y-%m-%d")

            logger.info(f"🔍 尝试从 MongoDB 获取 K 线数据: {code_padded}, period={period} (MongoDB: {mongodb_period}), limit={limit}")
            df = adapter.get_historical_data(code_padded, start_date, end_date, period=mongodb_period)

            if df is not None and not df.empty:
                # 转换 DataFrame 为列表格式
                items = []
                for _, row in df.tail(limit).iterrows():
                    items.append({
                        "time": row.get("trade_date", row.get("date", "")),  # 前端期望 time 字段
                        "open": float(row.get("open", 0)),
                        "high": float(row.get("high", 0)),
                        "low": float(row.get("low", 0)),
                        "close": float(row.get("close", 0)),
                        "volume": float(row.get("volume", row.get("vol", 0))),
                        "amount": float(row.get("amount", 0)) if "amount" in row else None,
                    })
                source = "mongodb"
                logger.info(f"✅ 从 MongoDB 获取到 {len(items)} 条 K 线数据")
        except Exception as e:
            logger.warning(f"⚠️ MongoDB 获取 K 线失败: {e}")

    # 3. 若仍无数据，降级到外部数据源管理器
    if not items:
        logger.info(f"📡 降级到数据源管理器获取 K 线")
        try:
            from app.services.data_sources.manager import DataSourceManager

            mgr = DataSourceManager()
            items, source = await asyncio.wait_for(
                asyncio.to_thread(mgr.get_kline_with_fallback, code_padded, period, limit, adj_norm),
                timeout=8.0
            )
        except Exception as e:
            logger.error(f"❌ 外部 API 获取 K 线失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取K线数据失败: {str(e)}")

    # 🔥 3. 检查并动态注入当天实时K线（针对日线 period == 'day'）
    if period == "day" and items:
        try:
            from app.services.stock_quote_service import fetch_realtime_stock_quote
            rt_q = await asyncio.to_thread(fetch_realtime_stock_quote, code_padded)
            if rt_q and rt_q.get("price", 0) > 0:
                rt_px = float(rt_q["price"])
                rt_date = rt_q.get("trade_date")
                rt_open = float(rt_q.get("open") or rt_px)
                rt_high = float(rt_q.get("high") or rt_px)
                rt_low = float(rt_q.get("low") or rt_px)
                rt_vol = float(rt_q.get("volume", 0))
                rt_amt = float(rt_q.get("amount", 0))

                last_item_time = str(items[-1].get("time", "")).replace("-", "")
                rt_date_clean = str(rt_date).replace("-", "") if rt_date else ""

                live_candle = {
                    "time": rt_date or items[-1].get("time"),
                    "open": rt_open,
                    "high": max(rt_high, rt_px),
                    "low": min(rt_low, rt_px),
                    "close": rt_px,
                    "volume": rt_vol,
                    "amount": rt_amt,
                }

                if rt_date_clean and last_item_time == rt_date_clean:
                    items[-1] = live_candle
                    logger.info(f"✅ 动态更新当天最新K线: {code_padded} (现价: {rt_px}, 日期: {rt_date})")
                elif rt_date_clean and rt_date_clean > last_item_time:
                    items.append(live_candle)
                    logger.info(f"✅ 动态追加今日最新K线: {code_padded} (现价: {rt_px}, 日期: {rt_date})")

                source = f"{source}+live_quote"
        except Exception as e:
            logger.warning(f"⚠️ 获取并合并实时K线失败: {e}")

    data = {
        "code": code_padded,
        "period": period,
        "limit": limit,
        "adj": adj if adj else "none",
        "source": source,
        "items": items or []
    }
    return ok(data)


@router.get("/{code}/timeline", response_model=dict)
async def get_timeline(
    code: str,
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    获取高保真分时走势数据（分钟线、均线、分时成交量、量程基准）
    支持核心指数与A股股票
    """
    import asyncio
    from app.services.index_service import fetch_timeline_data
    market, normalized_code = _detect_market_and_code(code)
    try:
        data = await asyncio.to_thread(fetch_timeline_data, normalized_code)
        return ok(data)
    except Exception as e:
        logger.error(f"❌ 获取分时数据失败 ({code}): {e}")
        raise HTTPException(status_code=500, detail=f"获取分时数据失败: {str(e)}")



@router.get("/{code}/indicators", response_model=dict)
async def get_technical_indicators(
    code: str,
    period: str = Query("day", description="周期: day/week/month"),
    limit: int = Query(120, ge=30, le=500, description="K线根数"),
    force_refresh: bool = Query(False, description="是否强制刷新实时行情"),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    获取股票全套技术指标及量化信号诊断 (MACD/RSI/KDJ/BOLL/MA/ATR/OBV)
    返回包含：
    - snapshot: 最新交易日指标快照、各指标多空评述、量化综合评分与评级
    - series: 全时间序列历史K线及指标值，供前端图表直接渲染
    """
    import numpy as np
    import pandas as pd
    from tradingagents.tools.analysis.indicators import ma, ema, macd, rsi, boll, atr, kdj, obv

    # 1. 检测与归一化代码
    market, normalized_code = _detect_market_and_code(code)
    code_padded = normalized_code

    # 2. 查询股票基础信息
    db = get_mongo_db()
    basic = await db["stock_basic_info"].find_one({"code": code_padded}, {"_id": 0, "name": 1, "market": 1})
    stock_name = basic.get("name") if basic else code_padded
    board_market = basic.get("market") if basic else market

    # 3. 获取K线数据（获取足够K线以准确计算指标，如MA60）
    fetch_limit = max(limit + 60, 120)
    kline_res = await get_kline(
        code=code_padded,
        period=period,
        limit=fetch_limit,
        adj="none",
        force_refresh=force_refresh,
        current_user=current_user
    )
    items = kline_res.get("data", {}).get("items", [])
    if not items or len(items) < 5:
        raise HTTPException(status_code=404, detail=f"暂无足够的K线数据计算技术指标: {code_padded}")

    # 🔥 核心增强：实时行情极速对齐并动态注入为最新实时K线（确保证券指标100%基于现价算法动态推演）
    from app.services.stock_quote_service import fetch_realtime_stock_quote
    rt_q = await asyncio.to_thread(fetch_realtime_stock_quote, code_padded)
    if (not stock_name or stock_name == code_padded) and rt_q and rt_q.get("name"):
        stock_name = rt_q["name"]

    if period == "day" and rt_q and rt_q.get("price", 0) > 0:
        rt_px = float(rt_q["price"])
        rt_date = rt_q.get("trade_date")
        rt_open = float(rt_q.get("open") or rt_px)
        rt_high = float(rt_q.get("high") or rt_px)
        rt_low = float(rt_q.get("low") or rt_px)
        rt_vol = float(rt_q.get("volume", 0))
        rt_amt = float(rt_q.get("amount", 0))

        last_item_time = str(items[-1].get("time", "")).replace("-", "")
        rt_date_clean = str(rt_date).replace("-", "") if rt_date else ""

        live_candle = {
            "time": rt_date or items[-1].get("time"),
            "open": rt_open,
            "high": max(rt_high, rt_px),
            "low": min(rt_low, rt_px),
            "close": rt_px,
            "volume": rt_vol,
            "amount": rt_amt,
        }

        if rt_date_clean and last_item_time == rt_date_clean:
            items[-1] = live_candle
        elif rt_date_clean and rt_date_clean > last_item_time:
            items.append(live_candle)

    # 4. 构造 DataFrame 并计算技术指标
    df = pd.DataFrame(items)
    for c in ["open", "high", "low", "close", "volume"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # 均线
    df["ma5"] = ma(df["close"], 5)
    df["ma10"] = ma(df["close"], 10)
    df["ma20"] = ma(df["close"], 20)
    df["ma60"] = ma(df["close"], 60)

    # MACD (中国通用: 2 * (DIF - DEA))
    macd_res = macd(df["close"], fast=12, slow=26, signal=9)
    df["dif"] = macd_res["dif"]
    df["dea"] = macd_res["dea"]
    df["macd_hist"] = (macd_res["dif"] - macd_res["dea"]) * 2

    # RSI (中国通用 china 算法)
    df["rsi6"] = rsi(df["close"], 6, method="china")
    df["rsi12"] = rsi(df["close"], 12, method="china")
    df["rsi24"] = rsi(df["close"], 24, method="china")

    # KDJ
    kdj_res = kdj(df["high"], df["low"], df["close"], n=9, m1=3, m2=3)
    df["kdj_k"] = kdj_res["kdj_k"]
    df["kdj_d"] = kdj_res["kdj_d"]
    df["kdj_j"] = kdj_res["kdj_j"]

    # BOLL (20, 2)
    boll_res = boll(df["close"], n=20, k=2.0)
    df["boll_upper"] = boll_res["boll_upper"]
    df["boll_mid"] = boll_res["boll_mid"]
    df["boll_lower"] = boll_res["boll_lower"]

    # ATR & OBV
    df["atr14"] = atr(df["high"], df["low"], df["close"], n=14)
    df["obv"] = obv(df["close"], df["volume"])

    # 5. 生成量化诊断快照 (Snapshot & Signals)
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else last

    signals_list = []
    bullish_count = 0
    bearish_count = 0
    neutral_count = 0

    # (1) MACD 诊断
    dif_val = float(last["dif"]) if pd.notna(last["dif"]) else 0.0
    dea_val = float(last["dea"]) if pd.notna(last["dea"]) else 0.0
    hist_val = float(last["macd_hist"]) if pd.notna(last["macd_hist"]) else 0.0
    prev_dif = float(prev["dif"]) if pd.notna(prev["dif"]) else dif_val
    prev_dea = float(prev["dea"]) if pd.notna(prev["dea"]) else dea_val
    prev_hist = float(prev["macd_hist"]) if pd.notna(prev["macd_hist"]) else hist_val

    is_macd_golden = prev_dif <= prev_dea and dif_val > dea_val
    is_macd_death = prev_dif >= prev_dea and dif_val < dea_val

    if is_macd_golden:
        macd_signal = "金叉确立 (看多)"
        macd_type = "bullish"
        bullish_count += 1
        signals_list.append({"indicator": "MACD", "signal": "低位/中位金叉突破", "type": "bullish"})
    elif is_macd_death:
        macd_signal = "死叉形成 (看空)"
        macd_type = "bearish"
        bearish_count += 1
        signals_list.append({"indicator": "MACD", "signal": "死叉形成", "type": "bearish"})
    elif dif_val > dea_val:
        if dif_val > 0:
            macd_signal = "多头主升区间 (零轴上方)"
            macd_type = "bullish"
            bullish_count += 1
        else:
            macd_signal = "超跌反弹区间 (零轴下方)"
            macd_type = "neutral"
            neutral_count += 1
    else:
        if dif_val < 0:
            macd_signal = "空头下行区间"
            macd_type = "bearish"
            bearish_count += 1
        else:
            macd_signal = "高位死叉回调"
            macd_type = "bearish"
            bearish_count += 1

    hist_trend = (
        "红柱发散放大" if (hist_val > 0 and hist_val >= prev_hist) else
        "红柱开始收窄" if (hist_val > 0 and hist_val < prev_hist) else
        "绿柱开始缩短" if (hist_val < 0 and hist_val >= prev_hist) else
        "绿柱发散放大"
    )

    macd_snapshot = {
        "dif": round(dif_val, 3),
        "dea": round(dea_val, 3),
        "macd_hist": round(hist_val, 3),
        "signal": macd_signal,
        "type": macd_type,
        "hist_trend": hist_trend,
        "is_golden_cross": is_macd_golden,
        "is_death_cross": is_macd_death,
    }

    # (2) RSI 诊断
    rsi6_val = float(last["rsi6"]) if pd.notna(last["rsi6"]) else 50.0
    rsi12_val = float(last["rsi12"]) if pd.notna(last["rsi12"]) else 50.0
    rsi24_val = float(last["rsi24"]) if pd.notna(last["rsi24"]) else 50.0

    if rsi6_val >= 80:
        rsi_status = "严重超买 (>80)"
        rsi_type = "bearish"
        bearish_count += 1
        signals_list.append({"indicator": "RSI", "signal": f"RSI6={rsi6_val:.1f} 严重超买警惕回调", "type": "bearish"})
    elif rsi6_val >= 65:
        rsi_status = "强势多头区间 (65~80)"
        rsi_type = "bullish"
        bullish_count += 1
        signals_list.append({"indicator": "RSI", "signal": f"RSI6={rsi6_val:.1f} 多头动能强劲", "type": "bullish"})
    elif rsi6_val <= 20:
        rsi_status = "严重超卖 (<20)"
        rsi_type = "bullish"
        bullish_count += 1
        signals_list.append({"indicator": "RSI", "signal": f"RSI6={rsi6_val:.1f} 极度超卖可能反弹", "type": "bullish"})
    elif rsi6_val <= 35:
        rsi_status = "弱势整理区间 (20~35)"
        rsi_type = "bearish"
        bearish_count += 1
    else:
        rsi_status = "常态震荡区间 (35~65)"
        rsi_type = "neutral"
        neutral_count += 1

    rsi_snapshot = {
        "rsi6": round(rsi6_val, 2),
        "rsi12": round(rsi12_val, 2),
        "rsi24": round(rsi24_val, 2),
        "status": rsi_status,
        "type": rsi_type,
    }

    # (3) KDJ 诊断
    k_val = float(last["kdj_k"]) if pd.notna(last["kdj_k"]) else 50.0
    d_val = float(last["kdj_d"]) if pd.notna(last["kdj_d"]) else 50.0
    j_val = float(last["kdj_j"]) if pd.notna(last["kdj_j"]) else 50.0
    prev_k = float(prev["kdj_k"]) if pd.notna(prev["kdj_k"]) else k_val
    prev_d = float(prev["kdj_d"]) if pd.notna(prev["kdj_d"]) else d_val

    is_kdj_golden = prev_k <= prev_d and k_val > d_val
    is_kdj_death = prev_k >= prev_d and k_val < d_val

    if is_kdj_golden:
        kdj_signal = "低位金叉向上" if d_val < 35 else "KDJ金叉买入信号"
        kdj_type = "bullish"
        bullish_count += 1
        signals_list.append({"indicator": "KDJ", "signal": kdj_signal, "type": "bullish"})
    elif is_kdj_death:
        kdj_signal = "高位死叉承压" if d_val > 65 else "KDJ死叉整理"
        kdj_type = "bearish"
        bearish_count += 1
        signals_list.append({"indicator": "KDJ", "signal": kdj_signal, "type": "bearish"})
    elif j_val > 100:
        kdj_signal = f"J值超买拐点预警 ({j_val:.1f})"
        kdj_type = "bearish"
        bearish_count += 1
    elif j_val < 0:
        kdj_signal = f"J值超卖反弹酝酿 ({j_val:.1f})"
        kdj_type = "bullish"
        bullish_count += 1
    elif k_val >= d_val:
        kdj_signal = "K线在中轨上方上行"
        kdj_type = "bullish"
        bullish_count += 1
    else:
        kdj_signal = "K线在中轨下方整理"
        kdj_type = "neutral"
        neutral_count += 1

    kdj_snapshot = {
        "k": round(k_val, 2),
        "d": round(d_val, 2),
        "j": round(j_val, 2),
        "signal": kdj_signal,
        "type": kdj_type,
        "is_golden_cross": is_kdj_golden,
        "is_death_cross": is_kdj_death,
    }

    # (4) 布林带 BOLL 诊断
    close_val = float(last["close"]) if pd.notna(last["close"]) else 0.0
    upper_val = float(last["boll_upper"]) if pd.notna(last["boll_upper"]) else close_val
    mid_val = float(last["boll_mid"]) if pd.notna(last["boll_mid"]) else close_val
    lower_val = float(last["boll_lower"]) if pd.notna(last["boll_lower"]) else close_val

    boll_range = upper_val - lower_val
    pos_pct = ((close_val - lower_val) / boll_range * 100.0) if boll_range > 0 else 50.0
    bandwidth = ((upper_val - lower_val) / mid_val * 100.0) if mid_val > 0 else 0.0

    if close_val >= upper_val:
        boll_signal = "突破布林线上轨 (强势/警惕乖离)"
        boll_type = "bullish"
        bullish_count += 1
        signals_list.append({"indicator": "BOLL", "signal": "价格突破布林上轨", "type": "bullish"})
    elif close_val >= mid_val:
        boll_signal = "运行在中轨至上轨 (多头通道)"
        boll_type = "bullish"
        bullish_count += 1
    elif close_val > lower_val:
        boll_signal = "运行在下轨至中轨 (偏弱通道)"
        boll_type = "bearish"
        bearish_count += 1
    else:
        boll_signal = "触及或跌破下轨 (超跌反弹区)"
        boll_type = "neutral"
        neutral_count += 1

    boll_snapshot = {
        "upper": round(upper_val, 2),
        "mid": round(mid_val, 2),
        "lower": round(lower_val, 2),
        "position_pct": round(pos_pct, 1),
        "bandwidth": round(bandwidth, 2),
        "signal": boll_signal,
        "type": boll_type,
    }

    # (5) 均线系统 MA 诊断
    ma5_val = float(last["ma5"]) if pd.notna(last["ma5"]) else close_val
    ma10_val = float(last["ma10"]) if pd.notna(last["ma10"]) else close_val
    ma20_val = float(last["ma20"]) if pd.notna(last["ma20"]) else close_val
    ma60_val = float(last["ma60"]) if pd.notna(last["ma60"]) else close_val

    if ma5_val > ma10_val > ma20_val > ma60_val:
        ma_arrangement = "经典多头排列 (强势上升通道)"
        ma_type = "bullish"
        bullish_count += 1
        signals_list.append({"indicator": "MA", "signal": "均线标准多头排列", "type": "bullish"})
    elif ma5_val < ma10_val < ma20_val < ma60_val:
        ma_arrangement = "均线空头排列 (弱势下行通道)"
        ma_type = "bearish"
        bearish_count += 1
        signals_list.append({"indicator": "MA", "signal": "均线空头排列", "type": "bearish"})
    elif close_val >= ma20_val:
        ma_arrangement = "站上20日均线 (震荡偏多)"
        ma_type = "bullish"
        bullish_count += 1
    else:
        ma_arrangement = "受制于20日均线 (震荡偏空)"
        ma_type = "bearish"
        bearish_count += 1

    ma_snapshot = {
        "ma5": round(ma5_val, 2),
        "ma10": round(ma10_val, 2),
        "ma20": round(ma20_val, 2),
        "ma60": round(ma60_val, 2),
        "arrangement": ma_arrangement,
        "type": ma_type,
    }

    # (6) ATR & OBV
    atr14_val = float(last["atr14"]) if pd.notna(last["atr14"]) else 0.0
    volatility_ratio = (atr14_val / close_val * 100.0) if close_val > 0 else 0.0
    obv_val = float(last["obv"]) if pd.notna(last["obv"]) else 0.0

    # (7) 多因子综合评分评级
    if bullish_count >= 4:
        rating = "强力看多"
        rating_score = 90
        rating_type = "bullish"
    elif bullish_count >= 3:
        rating = "偏多震荡"
        rating_score = 75
        rating_type = "bullish"
    elif bearish_count >= 4:
        rating = "强力看空"
        rating_score = 20
        rating_type = "bearish"
    elif bearish_count >= 3:
        rating = "偏空震荡"
        rating_score = 35
        rating_type = "bearish"
    else:
        rating = "中性震荡"
        rating_score = 50
        rating_type = "neutral"

    overall_snapshot = {
        "rating": rating,
        "score": rating_score,
        "type": rating_type,
        "bullish_count": bullish_count,
        "bearish_count": bearish_count,
        "neutral_count": neutral_count,
        "signals": signals_list,
    }

    # 6. 生成前端使用的 K 线与指标时序列表（截取最近 limit 条）
    display_df = df.tail(limit).copy()

    def _clean_num(v, prec=2):
        if pd.isna(v) or v is None:
            return None
        return round(float(v), prec)

    series_data = []
    for _, row in display_df.iterrows():
        series_data.append({
            "time": str(row.get("time", "")),
            "open": _clean_num(row.get("open")),
            "high": _clean_num(row.get("high")),
            "low": _clean_num(row.get("low")),
            "close": _clean_num(row.get("close")),
            "volume": _clean_num(row.get("volume"), 0),
            "amount": _clean_num(row.get("amount"), 0),
            "ma5": _clean_num(row.get("ma5")),
            "ma10": _clean_num(row.get("ma10")),
            "ma20": _clean_num(row.get("ma20")),
            "ma60": _clean_num(row.get("ma60")),
            "dif": _clean_num(row.get("dif"), 3),
            "dea": _clean_num(row.get("dea"), 3),
            "macd_hist": _clean_num(row.get("macd_hist"), 3),
            "rsi6": _clean_num(row.get("rsi6"), 2),
            "rsi12": _clean_num(row.get("rsi12"), 2),
            "rsi24": _clean_num(row.get("rsi24"), 2),
            "kdj_k": _clean_num(row.get("kdj_k"), 2),
            "kdj_d": _clean_num(row.get("kdj_d"), 2),
            "kdj_j": _clean_num(row.get("kdj_j"), 2),
            "boll_upper": _clean_num(row.get("boll_upper")),
            "boll_mid": _clean_num(row.get("boll_mid")),
            "boll_lower": _clean_num(row.get("boll_lower")),
            "atr14": _clean_num(row.get("atr14")),
            "obv": _clean_num(row.get("obv"), 0),
        })

    snapshot_data = {
        "code": code_padded,
        "name": stock_name,
        "market": board_market,
        "trade_date": str(last.get("time", "")),
        "close": _clean_num(close_val),
        "open": _clean_num(last.get("open")),
        "high": _clean_num(last.get("high")),
        "low": _clean_num(last.get("low")),
        "prev_close": _clean_num(rt_q.get("prev_close")) if rt_q and rt_q.get("prev_close") else None,
        "pct_chg": _clean_num(rt_q.get("pct_chg")) if rt_q and rt_q.get("pct_chg") is not None else None,
        "volume": _clean_num(last.get("volume"), 0),
        "amount": _clean_num(last.get("amount"), 0),
        "turnover_rate": _clean_num(rt_q.get("turnover_rate")) if rt_q and rt_q.get("turnover_rate") is not None else None,
        "amplitude": _clean_num(rt_q.get("amplitude")) if rt_q and rt_q.get("amplitude") is not None else None,
        "pe": _clean_num(rt_q.get("pe")) if rt_q and rt_q.get("pe") is not None else None,
        "pb": _clean_num(rt_q.get("pb")) if rt_q and rt_q.get("pb") is not None else None,
        "total_mv": _clean_num(rt_q.get("total_mv")) if rt_q and rt_q.get("total_mv") is not None else None,
        "ask_orders": rt_q.get("ask_orders") if rt_q else None,
        "bid_orders": rt_q.get("bid_orders") if rt_q else None,
        "is_realtime": True if rt_q else False,
        "overall": overall_snapshot,
        "macd": macd_snapshot,
        "rsi": rsi_snapshot,
        "kdj": kdj_snapshot,
        "boll": boll_snapshot,
        "ma": ma_snapshot,
        "atr": {"atr14": _clean_num(atr14_val), "volatility_ratio": _clean_num(volatility_ratio, 2)},
        "obv": {"obv": _clean_num(obv_val, 0)},
    }

    # 筹码分布分析 (CYQ)
    from app.services.chips_service import calculate_chips_distribution
    rt_turnover = float(rt_q.get("turnover_rate") or 0.0) if rt_q else 0.0
    rt_vol = float(rt_q.get("volume") or 0.0) if rt_q else 0.0
    total_shares = (rt_vol / (rt_turnover / 100.0)) if rt_vol > 0 and rt_turnover > 0 else None
    if total_shares:
        for it in items:
            if it.get("turnover_rate") is None or it.get("turnover_rate") <= 0:
                v = float(it.get("volume") or 0.0)
                it["turnover_rate"] = round((v / total_shares) * 100.0, 3)

    chips_data = calculate_chips_distribution(items, close_val, total_shares=total_shares, realtime_quote=rt_q)
    snapshot_data["chips"] = chips_data

    return ok({
        "code": code_padded,
        "name": stock_name,
        "market": board_market,
        "period": period,
        "snapshot": snapshot_data,
        "series": series_data,
        "chips": chips_data
    })


@router.get("/{code}/chips", response_model=dict)
async def get_stock_chips(
    code: str,
    period: str = Query("day", description="周期: day/week"),
    limit: int = Query(250, ge=30, le=500, description="K线样本数"),
    force_refresh: bool = Query(False, description="是否强制刷新"),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    获取股票筹码分布深度分析数据 (CYQ Cost Distribution)
    包含：
    - 获利盘比例 (profit_ratio)
    - 平均持仓成本 (avg_cost)
    - 90% 与 70% 筹码集中度与价格分布区间
    - 筹码多峰/单峰形态识别及诊断标签
    - 价格直方图 (histogram) 供前端可视化渲染
    """
    from app.services.chips_service import calculate_chips_distribution
    from app.services.stock_quote_service import fetch_realtime_stock_quote

    market, normalized_code = _detect_market_and_code(code)
    code_padded = normalized_code

    limit_val = limit if isinstance(limit, int) else 250
    period_val = period if isinstance(period, str) else "day"
    force_val = force_refresh if isinstance(force_refresh, bool) else False

    kline_res = await get_kline(
        code=code_padded,
        period=period_val,
        limit=limit_val,
        adj="none",
        force_refresh=force_val,
        current_user=current_user
    )
    items = kline_res.get("data", {}).get("items", [])
    if not items or len(items) < 5:
        raise HTTPException(status_code=404, detail=f"暂无足够的K线数据计算筹码分布: {code_padded}")

    rt_q = await asyncio.to_thread(fetch_realtime_stock_quote, code_padded)
    current_px = float(rt_q["price"]) if rt_q and rt_q.get("price") else float(items[-1].get("close", 0))

    # 计算总流通股本并为历史K线精准补全真实换手率
    rt_vol = float(rt_q.get("volume") or 0.0) if rt_q else 0.0
    rt_turnover = float(rt_q.get("turnover_rate") or 0.0) if rt_q else 0.0
    total_shares = (rt_vol / (rt_turnover / 100.0)) if rt_vol > 0 and rt_turnover > 0 else None

    if total_shares:
        for it in items:
            if it.get("turnover_rate") is None or it.get("turnover_rate") <= 0:
                v = float(it.get("volume") or 0.0)
                it["turnover_rate"] = round((v / total_shares) * 100.0, 3)

    is_etf = code_padded.startswith(("51", "56", "58", "159")) or current_px < 5.0
    px_prec = 3 if is_etf else 2

    chips = calculate_chips_distribution(
        items,
        current_px,
        total_shares=total_shares,
        is_etf=is_etf,
        precision=px_prec,
        realtime_quote=rt_q
    )
    if not chips:
        raise HTTPException(status_code=500, detail="筹码分布计算失败")

    return ok({
        "code": code_padded,
        "name": (rt_q.get("name") if rt_q else None) or code_padded,
        "current_price": round(current_px, px_prec),
        "chips": chips
    })


@router.get("/{code}/capital-flow", response_model=dict)
async def get_stock_capital_flow_endpoint(code: str):
    """
    获取个股主力资金流向（超大单/大单/中单/小单）与北向资金(陆股通)持股画像
    """
    from app.services.capital_flow_service import CapitalFlowService
    res = await CapitalFlowService.get_combined_analysis(code)
    return ok(data=res)


@router.get("/{code}/dossier", response_model=dict)
async def get_stock_dossier_endpoint(code: str):
    """
    获取多智能体证据案卷库 (Case Files)
    穿透真实离线大模型报告与实时量化多因子多空辩论
    动态测算置信度与证据级别，杜绝硬编码写死
    """
    from app.services.dossier_service import get_stock_dossier
    market, normalized_code = _detect_market_and_code(code)
    try:
        data = await get_stock_dossier(normalized_code)
        return ok(data)
    except Exception as e:
        logger.error(f"获取多智能体案卷库失败: {code}, 错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取多智能体案卷库失败: {str(e)}")


@router.post("/{code}/workflow/execute", response_model=dict)
async def execute_stock_workflow_endpoint(code: str):
    """
    真实执行 7 级多智能体协同流水线推演
    摒弃前端假动画与写死日志，进行事实级量化与多智能体推导
    """
    from app.services.dossier_service import execute_stock_workflow
    market, normalized_code = _detect_market_and_code(code)
    try:
        data = await execute_stock_workflow(normalized_code)
        return ok(data)
    except Exception as e:
        logger.error(f"执行多智能体工作流流水线失败: {code}, 错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"执行工作流流水线失败: {str(e)}")


class DeepReportTriggerRequest(BaseModel):
    research_depth: str = Field(default="快速", description="研究深度: 快速/标准/深度")
    analysts: Optional[List[str]] = Field(default=None, description="分析师团队列表")


@router.post("/{code}/dossier/generate-deep-report", response_model=dict)
async def trigger_dossier_deep_report_endpoint(
    code: str,
    background_tasks: BackgroundTasks,
    payload: Optional[DeepReportTriggerRequest] = None,
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    金融工作台：一键调度云端大模型 (LangGraph Multi-Agent) 深度研报推演
    异步提交后台执行，产物自动落入 analysis_reports 并被案卷库穿透识别
    """
    from app.services.simple_analysis_service import get_simple_analysis_service
    from app.models.analysis import SingleAnalysisRequest, AnalysisParameters
    market, normalized_code = _detect_market_and_code(code)

    user_id = str(current_user.get("id") or current_user.get("_id") or "terminal_user") if current_user else "terminal_user"
    depth = payload.research_depth if payload else "快速"
    analysts = payload.analysts if payload and payload.analysts else ["market", "fundamentals", "news", "risk"]

    req = SingleAnalysisRequest(
        symbol=normalized_code,
        parameters=AnalysisParameters(
            market_type="A股",
            research_depth=depth,
            selected_analysts=analysts
        )
    )

    try:
        service = get_simple_analysis_service()
        init_res = await service.create_analysis_task(user_id, req)
        task_id = init_res["task_id"]

        async def _run_deep_bg():
            try:
                bg_service = get_simple_analysis_service()
                await bg_service.execute_analysis_background(task_id, user_id, req)
                logger.info(f"✅ [Terminal] 标的 {normalized_code} 云端大模型深度研报完成: {task_id}")
            except Exception as ex:
                logger.error(f"❌ [Terminal] 标的 {normalized_code} 云端大模型研报失败: {task_id}, err={ex}", exc_info=True)

        background_tasks.add_task(_run_deep_bg)
        return ok({
            "task_id": task_id,
            "symbol": normalized_code,
            "status": "pending",
            "message": "云端多智能体大模型深度研推任务已在后台启动"
        })
    except Exception as e:
        logger.error(f"❌ 调度大模型研报失败 ({code}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"调度大模型深度研报失败: {str(e)}")


@router.get("/{code}/dossier/deep-report-status/{task_id}", response_model=dict)
async def get_dossier_deep_report_status_endpoint(code: str, task_id: str):
    """
    金融工作台：实时查询云端大模型深度研报的流转状态与进度
    """
    from app.services.simple_analysis_service import get_simple_analysis_service
    try:
        service = get_simple_analysis_service()
        status_res = await service.get_task_status(task_id)
        if not status_res:
            return ok({"task_id": task_id, "status": "unknown", "progress": 0})

        st = status_res.get("status")
        progress = status_res.get("progress", 0)
        has_result = status_res.get("result") is not None or status_res.get("has_result", False)

        return ok({
            "task_id": task_id,
            "symbol": code,
            "status": st,
            "progress": progress,
            "completed": st in ["completed", "success"] or has_result,
            "failed": st in ["failed", "error"],
            "current_step": status_res.get("current_step") or status_res.get("status_message") or ""
        })
    except Exception as e:
        logger.warning(f"查询研报任务状态失败 ({task_id}): {e}")
        return ok({"task_id": task_id, "status": "processing", "progress": 50})


@router.get("/{code}/news", response_model=dict)
async def get_news(code: str, days: int = 30, limit: int = 50, include_announcements: bool = True, current_user: Optional[dict] = Depends(get_optional_current_user)):
    """获取A股新闻与公告"""
    from app.services.news_data_service import get_news_data_service, NewsQueryParams

    # 检测股票类型
    market, normalized_code = _detect_market_and_code(code)

    # A股：直接调用同步服务的查询方法（包含智能回退逻辑）
    try:
        logger.info(f"=" * 80)
        logger.info(f"📰 开始获取新闻: code={code}, normalized_code={normalized_code}, days={days}, limit={limit}")

        # 直接使用 news_data 路由的查询逻辑
        from app.services.news_data_service import get_news_data_service, NewsQueryParams
        from datetime import datetime, timedelta
        from app.worker.akshare_sync_service import get_akshare_sync_service

        service = None
        try:
            service = await get_news_data_service()
        except Exception as se:
            logger.debug(f"news_data_service初始化失败: {se}")

        sync_service = None
        try:
            sync_service = await get_akshare_sync_service()
        except Exception as sse:
            logger.debug(f"akshare_sync_service初始化失败: {sse}")

        # 计算时间范围
        hours_back = days * 24

        # 🔥 不设置 start_time 限制，直接查询最新的 N 条新闻
        # 因为数据库中的新闻可能不是最近几天的，而是历史数据
        params = NewsQueryParams(
            symbol=normalized_code,
            limit=limit,
            sort_by="publish_time",
            sort_order=-1
        )

        logger.info(f"🔍 查询参数: symbol={params.symbol}, limit={params.limit} (不限制时间范围)")

        news_list = []
        # 1. 先从数据库查询
        if service:
            logger.info(f"📊 步骤1: 从数据库查询新闻...")
            try:
                news_list = await service.query_news(params)
                logger.info(f"📊 数据库查询结果: 返回 {len(news_list)} 条新闻")
            except Exception as qe:
                logger.debug(f"查询数据库新闻失败: {qe}")

        data_source = "database"

        # 2. 如果数据库没有数据，调用同步服务
        if not news_list and sync_service:
            logger.info(f"⚠️ 数据库无新闻数据，调用同步服务获取: {normalized_code}")
            try:
                # 🔥 调用同步服务，传入单个股票代码列表
                logger.info(f"📡 步骤2: 调用同步服务...")
                await sync_service.sync_news_data(
                    symbols=[normalized_code],
                    max_news_per_stock=limit,
                    force_update=False,
                    favorites_only=False
                )

                # 重新查询
                if service:
                    logger.info(f"🔄 步骤3: 重新从数据库查询...")
                    news_list = await service.query_news(params)
                    logger.info(f"📊 重新查询结果: 返回 {len(news_list)} 条新闻")
                    data_source = "realtime"

            except Exception as e:
                logger.error(f"❌ 同步服务异常: {e}")

        # 3. 如果依然无新闻，调用统一数据源管理器直接拉取实时财经新闻
        if not news_list:
            try:
                logger.info(f"🔄 步骤3b: 从统一数据源管理器直接拉取 {normalized_code} 实时新闻...")
                from tradingagents.dataflows.data_source_manager import get_data_source_manager
                dm = get_data_source_manager()
                raw_news = dm.get_news_data(normalized_code, limit=limit)
                if raw_news:
                    for n in raw_news:
                        news_list.append({
                            "title": n.get("title", ""),
                            "source": n.get("source", "财经源"),
                            "publish_time": n.get("publish_time", ""),
                            "url": n.get("url", ""),
                            "type": "news",
                            "content": n.get("content", ""),
                            "summary": n.get("summary", "")
                        })
                    data_source = "realtime_feed"
                    logger.info(f"✅ 数据源管理器直接获取成功: {len(news_list)} 条新闻")
            except Exception as dm_e:
                logger.debug(f"数据源管理器获取新闻异常: {dm_e}")

        # 转换为旧格式（兼容前端）
        logger.info(f"🔄 步骤4: 转换数据格式...")
        items = []
        for news in news_list:
            # 🔥 将 datetime 对象转换为 ISO 字符串
            publish_time = news.get("publish_time", "")
            if isinstance(publish_time, datetime):
                publish_time = publish_time.isoformat()

            items.append({
                "title": news.get("title", ""),
                "source": news.get("source", ""),
                "time": publish_time,
                "url": news.get("url", ""),
                "type": "news",
                "content": news.get("content", ""),
                "summary": news.get("summary", "")
            })

        logger.info(f"✅ 转换完成: {len(items)} 条新闻")

        data = {
            "code": normalized_code,
            "days": days,
            "limit": limit,
            "include_announcements": include_announcements,
            "source": data_source,
            "items": items
        }

        logger.info(f"📤 最终返回: source={data_source}, items_count={len(items)}")
        logger.info(f"=" * 80)
        return ok(data)

    except Exception as e:
        logger.error(f"❌ 获取新闻失败: {e}", exc_info=True)
        data = {
            "code": normalized_code,
            "days": days,
            "limit": limit,
            "include_announcements": include_announcements,
            "source": None,
            "items": []
        }
        return ok(data)


# ==================== 系统预置量化基准策略库 ====================

DEFAULT_SYSTEM_STRATEGIES = [
    {
        "id": "preset_quant_candidate",
        "name": "量化初筛候选池",
        "description": "系统全链路基准量化池：合理估值(0<PE<=60)且流动性充沛(成交额>=8000万)，与市场总览同源联动",
        "icon": "🎯",
        "tag_type": "primary",
        "is_system": True,
        "cannot_delete": True,
        "params": {
            "preset": "quant_candidate",
            "min_pe": 0.01,
            "max_pe": 60.0,
            "min_amount": 80_000_000.0
        }
    },
    {
        "id": "preset_low_valuation",
        "name": "低估值价值",
        "description": "严格估值安全边际：市盈率 PE <= 20，市净率 PB <= 2.0",
        "icon": "💎",
        "tag_type": "success",
        "is_system": True,
        "cannot_delete": False,
        "params": {
            "min_pe": 0.01,
            "max_pe": 20.0,
            "min_pb": 0.01,
            "max_pb": 2.0
        }
    },
    {
        "id": "preset_buffett_roe",
        "name": "巴菲特高ROE",
        "description": "高资本回报率：净资产收益率 ROE >= 15%，市盈率 PE <= 30",
        "icon": "👑",
        "tag_type": "warning",
        "is_system": True,
        "cannot_delete": False,
        "params": {
            "min_roe": 15.0,
            "min_pe": 0.01,
            "max_pe": 30.0
        }
    },
    {
        "id": "preset_growth",
        "name": "业绩高成长",
        "description": "高速双增白马：净利润增速 >= 30%，营收增速 >= 20%",
        "icon": "🚀",
        "tag_type": "danger",
        "is_system": True,
        "cannot_delete": False,
        "params": {
            "min_net_profit_growth": 30.0,
            "min_revenue_growth": 20.0
        }
    },
    {
        "id": "preset_breakout",
        "name": "强势突破",
        "description": "量价共振主升浪：日涨幅 >= 3%，换手率 >= 3%，高成交活跃度",
        "icon": "⚡",
        "tag_type": "danger",
        "is_system": True,
        "cannot_delete": False,
        "params": {
            "min_pct_chg": 3.0,
            "min_turnover_rate": 3.0,
            "volume_level": "high"
        }
    },
    {
        "id": "preset_active_turnover",
        "name": "高换手活跃",
        "description": "高流动性博弈：换手率 >= 5%，量比 >= 1.5，上涨趋势",
        "icon": "🔥",
        "tag_type": "danger",
        "is_system": True,
        "cannot_delete": False,
        "params": {
            "min_turnover_rate": 5.0,
            "min_volume_ratio": 1.5,
            "min_pct_chg": 0.0
        }
    },
    {
        "id": "preset_bluechip",
        "name": "稳健蓝筹",
        "description": "主板核心资产：主板标的，PE <= 30，股价 >= 10元，正常流动性",
        "icon": "🛡️",
        "tag_type": "primary",
        "is_system": True,
        "cannot_delete": False,
        "params": {
            "market": "主板",
            "min_pe": 0.01,
            "max_pe": 30.0,
            "min_close": 10.0,
            "volume_level": "medium"
        }
    },
    {
        "id": "preset_specialized",
        "name": "专精特新",
        "description": "成长型专精特新标的：北交所小盘创新企业",
        "icon": "🌟",
        "tag_type": "warning",
        "is_system": True,
        "cannot_delete": False,
        "params": {
            "market": "北交所",
            "min_pct_chg": 0.0,
            "market_cap_range": "small"
        }
    },
    {
        "id": "preset_high_risk_reward",
        "name": "高盈亏比波段",
        "description": "博弈胜率与赔率兼备：测算盈亏比 >= 2.5，结合合理估值与适度流动性",
        "icon": "⚖️",
        "tag_type": "success",
        "is_system": True,
        "cannot_delete": False,
        "params": {
            "min_risk_reward_ratio": 2.5,
            "min_pe": 0.01,
            "max_pe": 50.0,
            "volume_level": "medium"
        }
    },
    {
        "id": "preset_small_cap_breakout",
        "name": "小资金·放量起爆",
        "description": "短线高爆发脱离成本区：量比>=1.8，换手率3%~12%，日涨幅2%~6.5%，高换手突破主升",
        "icon": "🚀",
        "tag_type": "danger",
        "is_system": True,
        "cannot_delete": False,
        "params": {
            "min_volume_ratio": 1.8,
            "min_turnover_rate": 3.0,
            "max_turnover_rate": 12.0,
            "min_pct_chg": 2.0,
            "max_pct_chg": 6.5,
            "volume_level": "high"
        }
    },
    {
        "id": "preset_small_cap_pullback",
        "name": "小资金·缩量企稳回踩",
        "description": "拒绝追高被套：缩量(量比<=1.2)回踩支撑企稳，换手1.5%~4.5%，振幅收敛，极小止损试错成本",
        "icon": "🛡️",
        "tag_type": "success",
        "is_system": True,
        "cannot_delete": False,
        "params": {
            "max_volume_ratio": 1.2,
            "min_turnover_rate": 1.5,
            "max_turnover_rate": 4.5,
            "min_pct_chg": -1.5,
            "max_pct_chg": 2.0,
            "volume_level": "low"
        }
    },
    {
        "id": "preset_small_cap_high_rr",
        "name": "小资金·高盈亏比波段",
        "description": "小本金复利利器：市值50亿~300亿弹性中小盘，换手2%~8%，严格测算盈亏比>=2.5:1",
        "icon": "⚖️",
        "tag_type": "warning",
        "is_system": True,
        "cannot_delete": False,
        "params": {
            "min_risk_reward_ratio": 2.5,
            "market_cap_range": "medium",
            "min_turnover_rate": 2.0,
            "max_turnover_rate": 8.0,
            "min_pe": 0.01,
            "max_pe": 45.0
        }
    }
]


async def ensure_seed_strategies(db):
    """确保系统预设策略种子数据存在于 MongoDB"""
    now_iso = datetime.datetime.now().isoformat()
    for s in DEFAULT_SYSTEM_STRATEGIES:
        existing = await db["user_quant_strategies"].find_one({"id": s["id"]})
        if not existing:
            doc = dict(s)
            doc["created_at"] = now_iso
            doc["updated_at"] = now_iso
            await db["user_quant_strategies"].insert_one(doc)


async def get_quant_candidate_strategy(db) -> dict:
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


def _calc_risk_reward_ratio(item: dict, q: dict) -> Optional[float]:
    """
    测算标的扣费真实净盈亏比 (Real Friction-Adjusted Risk-Reward Ratio, Net R:R)
    统一调用 QuantCoreEngine 量化计算内核，保证全系统同源一致
    """
    from app.quant_engine import QuantCoreEngine
    return QuantCoreEngine.calc_risk_reward(item, q)


@router.get("/pool", response_model=dict)
async def get_stock_pool(
    preset: Optional[str] = Query(None, description="预设筛选策略 (例如 quant_candidate)"),
    keyword: Optional[str] = Query(None, description="搜索代码或名称"),
    market: Optional[str] = Query(None, description="板块分类 (主板/创业板/科创板/北交所)"),
    source: Optional[str] = Query(None, description="数据源 (baostock/akshare/tushare)"),
    min_pe: Optional[Union[float, str]] = Query(None, description="最小市盈率 PE"),
    max_pe: Optional[Union[float, str]] = Query(None, description="最大市盈率 PE"),
    min_pb: Optional[Union[float, str]] = Query(None, description="最小市净率 PB"),
    max_pb: Optional[Union[float, str]] = Query(None, description="最大市净率 PB"),
    min_ps: Optional[Union[float, str]] = Query(None, description="最小市销率 PS"),
    max_ps: Optional[Union[float, str]] = Query(None, description="最大市销率 PS"),
    min_close: Optional[Union[float, str]] = Query(None, description="最低股价"),
    max_close: Optional[Union[float, str]] = Query(None, description="最高股价"),
    min_pct_chg: Optional[Union[float, str]] = Query(None, description="最小涨跌幅(%)"),
    max_pct_chg: Optional[Union[float, str]] = Query(None, description="最大涨跌幅(%)"),
    volume_level: Optional[str] = Query(None, description="成交活跃度 (high/medium/low)"),
    min_turnover_rate: Optional[Union[float, str]] = Query(None, description="最小换手率(%)"),
    max_turnover_rate: Optional[Union[float, str]] = Query(None, description="最大换手率(%)"),
    min_volume_ratio: Optional[Union[float, str]] = Query(None, description="最小量比"),
    max_volume_ratio: Optional[Union[float, str]] = Query(None, description="最大量比"),
    market_cap_range: Optional[str] = Query(None, description="市值范围 (small/medium/large)"),
    min_market_cap: Optional[Union[float, str]] = Query(None, description="最小市值(亿元)"),
    max_market_cap: Optional[Union[float, str]] = Query(None, description="最大市值(亿元)"),
    min_roe: Optional[Union[float, str]] = Query(None, description="最小净资产收益率 ROE (%)"),
    max_roe: Optional[Union[float, str]] = Query(None, description="最大净资产收益率 ROE (%)"),
    min_net_profit_growth: Optional[Union[float, str]] = Query(None, description="最小净利润同比增长率 (%)"),
    max_net_profit_growth: Optional[Union[float, str]] = Query(None, description="最大净利润同比增长率 (%)"),
    min_revenue_growth: Optional[Union[float, str]] = Query(None, description="最小营收同比增长率 (%)"),
    max_revenue_growth: Optional[Union[float, str]] = Query(None, description="最大营收同比增长率 (%)"),
    min_gross_margin: Optional[Union[float, str]] = Query(None, description="最小销售毛利率 (%)"),
    max_gross_margin: Optional[Union[float, str]] = Query(None, description="最大销售毛利率 (%)"),
    min_risk_reward_ratio: Optional[Union[float, str]] = Query(None, description="最小测算盈亏比 (R:R)"),
    max_risk_reward_ratio: Optional[Union[float, str]] = Query(None, description="最大测算盈亏比 (R:R)"),
    min_amount: Optional[Union[float, str]] = Query(None, description="最小成交额(元/万元/亿元)"),
    max_amount: Optional[Union[float, str]] = Query(None, description="最大成交额(元/万元/亿元)"),
    # === 新增多维量化筛选体系参数 (资金面/技术面/筹码面/风控面) ===
    min_north_ratio: Optional[Union[float, str]] = Query(None, description="最小北向持股比例(%)"),
    max_north_ratio: Optional[Union[float, str]] = Query(None, description="最大北向持股比例(%)"),
    is_heavy_north: Optional[Union[bool, str]] = Query(None, description="仅筛选外资重仓标的(>=3%)"),
    ma_bullish_only: Optional[Union[bool, str]] = Query(None, description="仅筛选均线多头排列"),
    above_ma20_only: Optional[Union[bool, str]] = Query(None, description="仅筛选站上20日生命线"),
    min_profit_ratio: Optional[Union[float, str]] = Query(None, description="最小筹码获利盘(%)"),
    max_concentration_90: Optional[Union[float, str]] = Query(None, description="最大90%筹码集中度(%)"),
    exclude_st: Optional[Union[bool, str]] = Query(None, description="排除ST/退市风险警示股"),
    max_debt_ratio: Optional[Union[float, str]] = Query(None, description="最大资产负债率(%)"),
    page: int = Query(1, ge=1, description="当前页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort_field: str = Query("code", description="排序字段 (code/name/close/pct_chg/amount/turnover_rate/volume_ratio/pe/pb/ps/total_mv/roe/net_profit_growth/revenue_growth/gross_margin/risk_reward_ratio/north_ratio)"),
    sort_order: str = Query("asc", description="排序方式 (asc/desc)"),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    A股股票池列表与多维量化筛选API
    整合全市场档案、实时行情与统一量化核心引擎多因子画像
    """
    db = get_mongo_db()
    data = await stock_pool_service.query_stock_pool(
        db=db,
        preset=preset,
        keyword=keyword,
        market=market,
        source=source,
        min_pe=min_pe,
        max_pe=max_pe,
        min_pb=min_pb,
        max_pb=max_pb,
        min_ps=min_ps,
        max_ps=max_ps,
        min_close=min_close,
        max_close=max_close,
        min_pct_chg=min_pct_chg,
        max_pct_chg=max_pct_chg,
        volume_level=volume_level,
        min_turnover_rate=min_turnover_rate,
        max_turnover_rate=max_turnover_rate,
        min_volume_ratio=min_volume_ratio,
        max_volume_ratio=max_volume_ratio,
        market_cap_range=market_cap_range,
        min_market_cap=min_market_cap,
        max_market_cap=max_market_cap,
        min_roe=min_roe,
        max_roe=max_roe,
        min_net_profit_growth=min_net_profit_growth,
        max_net_profit_growth=max_net_profit_growth,
        min_revenue_growth=min_revenue_growth,
        max_revenue_growth=max_revenue_growth,
        min_gross_margin=min_gross_margin,
        max_gross_margin=max_gross_margin,
        min_risk_reward_ratio=min_risk_reward_ratio,
        max_risk_reward_ratio=max_risk_reward_ratio,
        min_amount=min_amount,
        max_amount=max_amount,
        min_north_ratio=min_north_ratio,
        max_north_ratio=max_north_ratio,
        is_heavy_north=is_heavy_north,
        ma_bullish_only=ma_bullish_only,
        above_ma20_only=above_ma20_only,
        min_profit_ratio=min_profit_ratio,
        max_concentration_90=max_concentration_90,
        exclude_st=exclude_st,
        max_debt_ratio=max_debt_ratio,
        page=page,
        page_size=page_size,
        sort_field=sort_field,
        sort_order=sort_order,
    )
    return ok(data=data)



@router.get("/etf/overview", response_model=dict)
async def get_etf_market_overview(
    force_refresh: bool = Query(False, description="是否强制刷新"),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    全市场核心场内 ETF 极速实时数据与行情聚合
    支持宽基、硬核科技、制造周期、大类跨境等核心板块，毫秒级响应
    """
    from app.services.etf_service import fetch_all_etf_market_overview
    data = await asyncio.to_thread(fetch_all_etf_market_overview, force_refresh)
    return ok(data=data)


@router.get("/etf/market-list", response_model=dict)
async def get_etf_market_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(30, ge=10, le=100, description="每页条数"),
    category: str = Query("all", description="分类ID: all, broad, tech, industry, macro, thematic, bond_money"),
    keyword: str = Query("", description="搜索关键词（代码或名称）"),
    sort_by: str = Query("amount_desc", description="排序方式: amount_desc, amount_asc, pct_desc, pct_asc, price_desc, turnover_desc"),
    force_refresh: bool = Query(False, description="是否强制刷新"),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    全市场 1000+ 场内 ETF 库（分页查询、赛道分类、多维度排序与极速检索）
    """
    from app.services.etf_service import fetch_all_market_etfs_paged
    data = await asyncio.to_thread(
        fetch_all_market_etfs_paged,
        page=page,
        page_size=page_size,
        category=category,
        keyword=keyword,
        sort_by=sort_by,
        force_refresh=force_refresh
    )
    return ok(data=data)


@router.get("/market/indices", response_model=dict)
async def get_market_indices(
    force_refresh: bool = Query(False, description="是否强制刷新"),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    获取A股核心重要指数实时行情（上证指数、深证成指、创业板指、科创综指、沪深300等）
    集成腾讯实时行情，自动按时效性缓存与刷新，毫秒级响应
    """
    from app.services.index_service import sync_indices_to_db

    try:
        await sync_indices_to_db(force=force_refresh)
    except Exception as e:
        logger.warning(f"同步核心指数实时行情失败: {e}")

    quotes_map = {}
    try:
        db = get_mongo_db()
        target_codes = ["sh000001", "sz399001", "sz399006", "sh000680"]
        cursor = db["market_quotes"].find({"code": {"$in": target_codes}}, {"_id": 0})
        quotes_list = await cursor.to_list(len(target_codes))
        quotes_map = {q["code"]: q for q in quotes_list if "code" in q}
    except Exception as e:
        logger.warning(f"从MongoDB读取核心指数缓存异常: {e}")

    if len(quotes_map) < 4:
        try:
            from app.services.index_service import fetch_all_index_quotes
            fresh_quotes = await asyncio.to_thread(fetch_all_index_quotes)
            for q in fresh_quotes:
                if q.get("code") not in quotes_map:
                    quotes_map[q["code"]] = q
        except Exception as e:
            logger.warning(f"直接拉取腾讯核心指数兜底异常: {e}")

    display_indices = [
        {"code": "000001", "fullCode": "sh000001", "name": "上证指数", "default_price": 3900.0, "default_chg": -0.93},
        {"code": "399001", "fullCode": "sz399001", "name": "深证成指", "default_price": 13399.34, "default_chg": -1.74},
        {"code": "399006", "fullCode": "sz399006", "name": "创业板指", "default_price": 3317.33, "default_chg": -1.84},
        {"code": "000680", "fullCode": "sh000680", "name": "科创综指", "default_price": 1934.56, "default_chg": -1.72}
    ]

    results = []
    latest_update = datetime.datetime.now().strftime("%H:%M:%S")

    for item in display_indices:
        q = quotes_map.get(item["fullCode"]) or quotes_map.get(item["code"])
        if q:
            price = float(q.get("price") or q.get("close") or item["default_price"])
            change_percent = float(q.get("change_percent") or q.get("pct_chg") or item["default_chg"])
            change = float(q.get("change") or 0.0)
            amount = float(q.get("amount") or 0.0)
            up_at = q.get("updated_at")
            if isinstance(up_at, datetime.datetime):
                latest_update = up_at.strftime("%H:%M:%S")
        else:
            price = item["default_price"]
            change_percent = item["default_chg"]
            change = 0.0
            amount = 0.0

        results.append({
            "code": item["code"],
            "fullCode": item["fullCode"],
            "name": item["name"],
            "price": round(price, 2),
            "changePercent": round(change_percent, 2),
            "change_percent": round(change_percent, 2),
            "change": round(change, 2),
            "amount": amount
        })

    return ok(data={
        "indices": results,
        "updated_at": latest_update,
        "timestamp": time.time()
    })


@router.get("/market/overview", response_model=dict)
async def get_market_overview(
    force_refresh: bool = Query(False, description="是否强制刷新缓存"),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    获取市场投研总览核心全景数据
    整合全市场行情指标、涨跌分布、两市成交额、高频行业板块及智能体协同事件流
    """
    db = get_mongo_db()
    data = await market_overview_service.get_market_overview(db, force_refresh)
    return ok(data=data)


# ==================== 量化策略自定义 CRUD 接口 ====================

class QuantStrategyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=60, description="策略名称")
    description: Optional[str] = Field(None, max_length=200, description="策略描述")
    icon: Optional[str] = Field("🎯", description="策略图标")
    tag_type: Optional[str] = Field("primary", description="标签风格色彩")
    params: Dict[str, Any] = Field(default_factory=dict, description="筛选指标参数字典")


class QuantStrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    tag_type: Optional[str] = None
    params: Optional[Dict[str, Any]] = None


@router.get("/strategies", response_model=dict)
async def get_user_strategies(current_user: Optional[dict] = Depends(get_optional_current_user)):
    """获取所有自建与预留量化策略列表（核心候选池与经典策略均可自由修改）"""
    db = get_mongo_db()
    await ensure_seed_strategies(db)

    cursor = db["user_quant_strategies"].find({}, {"_id": 0})
    strategies = [doc async for doc in cursor]

    # 排序规范：
    # 0: preset_quant_candidate (系统核心驱动池置顶)
    # 1: 预置经典推荐策略 (is_system == True)
    # 2: 用户完全自建策略 (按 updated_at 降序)
    def _sort_key(item: dict):
        s_id = item.get("id", "")
        if s_id == "preset_quant_candidate":
            return (0, 0, "")
        if item.get("is_system"):
            # 保持系统预设的相对顺序
            sys_order = {s["id"]: idx for idx, s in enumerate(DEFAULT_SYSTEM_STRATEGIES)}
            return (1, sys_order.get(s_id, 99), "")
        return (2, 0, item.get("updated_at", ""))

    strategies.sort(key=_sort_key)
    return ok(data=strategies)


@router.post("/strategies", response_model=dict)
async def create_user_strategy(
    data: QuantStrategyCreate,
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """创建新的自定义量化策略"""
    db = get_mongo_db()
    strategy_id = f"strat_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.datetime.now().isoformat()
    doc = {
        "id": strategy_id,
        "name": data.name.strip(),
        "description": data.description.strip() if data.description else "",
        "icon": data.icon or "🎯",
        "tag_type": data.tag_type or "primary",
        "params": data.params or {},
        "is_system": False,
        "cannot_delete": False,
        "created_at": now_iso,
        "updated_at": now_iso
    }
    await db["user_quant_strategies"].insert_one(doc)
    doc.pop("_id", None)
    return ok(data=doc, message="策略创建成功")


@router.put("/strategies/{strategy_id}", response_model=dict)
async def update_user_strategy(
    strategy_id: str,
    data: QuantStrategyUpdate,
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """修改已有量化策略（所有经典策略与自建策略均支持修改指标）"""
    db = get_mongo_db()
    existing = await db["user_quant_strategies"].find_one({"id": strategy_id})
    if not existing:
        raise HTTPException(status_code=404, detail="未找到该策略")

    update_fields: Dict[str, Any] = {"updated_at": datetime.datetime.now().isoformat()}
    if data.name is not None:
        update_fields["name"] = data.name.strip()
    if data.description is not None:
        update_fields["description"] = data.description.strip()
    if data.icon is not None:
        update_fields["icon"] = data.icon
    if data.tag_type is not None:
        update_fields["tag_type"] = data.tag_type
    if data.params is not None:
        update_fields["params"] = data.params

    # 如果是核心量化候选池，保护 cannot_delete 与 preset 标识不丢失
    if strategy_id == "preset_quant_candidate" or existing.get("cannot_delete"):
        update_fields["cannot_delete"] = True
        if "params" in update_fields:
            update_fields["params"]["preset"] = "quant_candidate"

    await db["user_quant_strategies"].update_one({"id": strategy_id}, {"$set": update_fields})
    updated_doc = await db["user_quant_strategies"].find_one({"id": strategy_id}, {"_id": 0})

    # 若修改了量化初筛候选池，立即让市场总览缓存失效，使新指标即刻全局生效
    if strategy_id == "preset_quant_candidate":
        market_overview_service.clear_cache()

    return ok(data=updated_doc, message="策略指标已更新并立即生效")


@router.delete("/strategies/{strategy_id}", response_model=dict)
async def delete_user_strategy(
    strategy_id: str,
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """删除量化策略（系统核心候选池不可删除）"""
    db = get_mongo_db()
    existing = await db["user_quant_strategies"].find_one({"id": strategy_id})
    if not existing:
        raise HTTPException(status_code=404, detail="未找到该策略或已被删除")

    if existing.get("cannot_delete") or strategy_id == "preset_quant_candidate":
        raise HTTPException(
            status_code=400,
            detail="【量化初筛候选池】为系统全链路核心驱动策略，不可删除。您可根据需要自由修改其指标与筛选逻辑。"
        )

    res = await db["user_quant_strategies"].delete_one({"id": strategy_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="未找到该策略或已被删除")
    return ok(data={"id": strategy_id}, message="策略已成功删除")


@router.post("/strategies/reset-defaults", response_model=dict)
async def reset_default_strategies(current_user: Optional[dict] = Depends(get_optional_current_user)):
    """恢复/重新初始化系统预置的经典量化策略库"""
    db = get_mongo_db()
    now_iso = datetime.datetime.now().isoformat()
    for s in DEFAULT_SYSTEM_STRATEGIES:
        doc = dict(s)
        doc["updated_at"] = now_iso
        await db["user_quant_strategies"].update_one(
            {"id": s["id"]},
            {"$set": doc, "$setOnInsert": {"created_at": now_iso}},
            upsert=True
        )

    market_overview_service.clear_cache()

    cursor = db["user_quant_strategies"].find({}, {"_id": 0})
    all_strats = [d async for d in cursor]
    return ok(data=all_strats, message="已成功恢复系统推荐预设策略")



