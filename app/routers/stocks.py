"""
股票详情相关API
- 统一响应包: {success, data, message, timestamp}
- 所有端点均需鉴权 (Bearer Token)
- 路径前缀在 main.py 中挂载为 /api，当前路由自身前缀为 /stocks
"""
from typing import Optional, Dict, Any, List, Tuple
from fastapi import APIRouter, Depends, HTTPException, status, Query
import logging
import re
import datetime

from app.routers.auth_db import get_current_user, get_optional_current_user
from app.core.database import get_mongo_db
from app.core.response import ok

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
    if is_index_code(code6) and not q:
        logger.info(f"📊 首次初始化指数数据入库: {code6}")
        await sync_indices_to_db()
        q = await db["market_quotes"].find_one({"code": code6}, {"_id": 0})

    # 🔥 调试日志：查看查询结果
    logger.info(f"🔍 查询 market_quotes: code={code6}")
    if q:
        logger.info(f"  ✅ 找到数据: volume={q.get('volume')}, amount={q.get('amount')}, volume_ratio={q.get('volume_ratio')}")
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
    }

    return ok(data)


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
        data["roe"] = b.get("roe")

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
        import asyncio
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

    # 1. 优先从 MongoDB 缓存获取
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

    # 2. 如果 MongoDB 没有数据，降级到外部 API（带超时保护）
    if not items:
        logger.info(f"📡 MongoDB 无数据，降级到外部 API")
        try:
            import asyncio
            from app.services.data_sources.manager import DataSourceManager

            mgr = DataSourceManager()
            # 添加 10 秒超时保护
            items, source = await asyncio.wait_for(
                asyncio.to_thread(mgr.get_kline_with_fallback, code_padded, period, limit, adj_norm),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            logger.error(f"❌ 外部 API 获取 K 线超时（10秒）")
            raise HTTPException(status_code=504, detail="获取K线数据超时，请稍后重试")
        except Exception as e:
            logger.error(f"❌ 外部 API 获取 K 线失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取K线数据失败: {str(e)}")

    # 🔥 3. 检查是否需要添加当天实时数据（仅针对日线）
    if period == "day" and items:
        try:
            # 检查历史数据中是否已有当天的数据（支持两种日期格式）
            has_today_data = any(
                item.get("time") in [today_str_yyyymmdd, today_str_formatted]
                for item in items
            )

            # 判断是否在交易时间内或收盘后缓冲期
            current_time = now.time()
            is_weekday = now.weekday() < 5  # 周一到周五

            # 交易时间：9:30-11:30, 13:00-15:00
            # 收盘后缓冲期：15:00-15:30（确保获取到收盘价）
            is_trading_time = (
                is_weekday and (
                    (dtime(9, 30) <= current_time <= dtime(11, 30)) or
                    (dtime(13, 0) <= current_time <= dtime(15, 30))
                )
            )

            # 🔥 只在交易时间或收盘后缓冲期内才添加实时数据
            # 非交易日（周末、节假日）不添加实时数据
            should_fetch_realtime = is_trading_time

            if should_fetch_realtime:
                logger.info(f"🔥 尝试从 market_quotes 获取当天实时数据: {code_padded} (交易时间: {is_trading_time}, 已有当天数据: {has_today_data})")

                db = get_mongo_db()
                market_quotes_coll = db["market_quotes"]

                # 查询当天的实时行情
                realtime_quote = await market_quotes_coll.find_one({"code": code_padded})

                if realtime_quote:
                    # 🔥 构造当天的K线数据（使用统一的日期格式 YYYY-MM-DD）
                    today_kline = {
                        "time": today_str_formatted,  # 🔥 使用 YYYY-MM-DD 格式，与历史数据保持一致
                        "open": float(realtime_quote.get("open", 0)),
                        "high": float(realtime_quote.get("high", 0)),
                        "low": float(realtime_quote.get("low", 0)),
                        "close": float(realtime_quote.get("close", 0)),
                        "volume": float(realtime_quote.get("volume", 0)),
                        "amount": float(realtime_quote.get("amount", 0)),
                    }

                    # 如果历史数据中已有当天数据，替换；否则追加
                    if has_today_data:
                        # 替换最后一条数据（假设最后一条是当天的）
                        items[-1] = today_kline
                        logger.info(f"✅ 替换当天K线数据: {code_padded}")
                    else:
                        # 追加到末尾
                        items.append(today_kline)
                        logger.info(f"✅ 追加当天K线数据: {code_padded}")

                    source = f"{source}+market_quotes"
                else:
                    logger.warning(f"⚠️ market_quotes 中未找到当天数据: {code_padded}")
        except Exception as e:
            logger.warning(f"⚠️ 获取当天实时数据失败（忽略）: {e}")

    data = {
        "code": code_padded,
        "period": period,
        "limit": limit,
        "adj": adj if adj else "none",
        "source": source,
        "items": items or []
    }
    return ok(data)


@router.get("/{code}/indicators", response_model=dict)
async def get_technical_indicators(
    code: str,
    period: str = Query("day", description="周期: day/week/month"),
    limit: int = Query(120, ge=30, le=500, description="K线根数"),
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
        force_refresh=False,
        current_user=current_user
    )
    items = kline_res.get("data", {}).get("items", [])
    if not items or len(items) < 5:
        raise HTTPException(status_code=404, detail=f"暂无足够的K线数据计算技术指标: {code_padded}")

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
        "overall": overall_snapshot,
        "macd": macd_snapshot,
        "rsi": rsi_snapshot,
        "kdj": kdj_snapshot,
        "boll": boll_snapshot,
        "ma": ma_snapshot,
        "atr": {"atr14": _clean_num(atr14_val), "volatility_ratio": _clean_num(volatility_ratio, 2)},
        "obv": {"obv": _clean_num(obv_val, 0)},
    }

    return ok({
        "code": code_padded,
        "name": stock_name,
        "market": board_market,
        "period": period,
        "snapshot": snapshot_data,
        "series": series_data
    })


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

        service = await get_news_data_service()
        sync_service = await get_akshare_sync_service()

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

        # 1. 先从数据库查询
        logger.info(f"📊 步骤1: 从数据库查询新闻...")
        news_list = await service.query_news(params)
        logger.info(f"📊 数据库查询结果: 返回 {len(news_list)} 条新闻")

        data_source = "database"

        # 2. 如果数据库没有数据，调用同步服务
        if not news_list:
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
                logger.info(f"🔄 步骤3: 重新从数据库查询...")
                news_list = await service.query_news(params)
                logger.info(f"📊 重新查询结果: 返回 {len(news_list)} 条新闻")
                data_source = "realtime"

            except Exception as e:
                logger.error(f"❌ 同步服务异常: {e}", exc_info=True)

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


@router.get("/pool", response_model=dict)
async def get_stock_pool(
    keyword: Optional[str] = Query(None, description="搜索代码或名称"),
    market: Optional[str] = Query(None, description="板块分类 (主板/创业板/科创板/北交所)"),
    source: Optional[str] = Query(None, description="数据源 (baostock/akshare/tushare)"),
    min_pe: Optional[float] = Query(None, description="最小市盈率 PE"),
    max_pe: Optional[float] = Query(None, description="最大市盈率 PE"),
    min_pb: Optional[float] = Query(None, description="最小市净率 PB"),
    max_pb: Optional[float] = Query(None, description="最大市净率 PB"),
    min_ps: Optional[float] = Query(None, description="最小市销率 PS"),
    max_ps: Optional[float] = Query(None, description="最大市销率 PS"),
    min_close: Optional[float] = Query(None, description="最低股价"),
    max_close: Optional[float] = Query(None, description="最高股价"),
    min_pct_chg: Optional[float] = Query(None, description="最小涨跌幅(%)"),
    max_pct_chg: Optional[float] = Query(None, description="最大涨跌幅(%)"),
    volume_level: Optional[str] = Query(None, description="成交活跃度 (high/medium/low)"),
    min_turnover_rate: Optional[float] = Query(None, description="最小换手率(%)"),
    max_turnover_rate: Optional[float] = Query(None, description="最大换手率(%)"),
    min_volume_ratio: Optional[float] = Query(None, description="最小量比"),
    max_volume_ratio: Optional[float] = Query(None, description="最大量比"),
    market_cap_range: Optional[str] = Query(None, description="市值范围 (small/medium/large)"),
    min_market_cap: Optional[float] = Query(None, description="最小市值(亿元)"),
    max_market_cap: Optional[float] = Query(None, description="最大市值(亿元)"),
    min_roe: Optional[float] = Query(None, description="最小净资产收益率 ROE (%)"),
    max_roe: Optional[float] = Query(None, description="最大净资产收益率 ROE (%)"),
    min_net_profit_growth: Optional[float] = Query(None, description="最小净利润同比增长率 (%)"),
    max_net_profit_growth: Optional[float] = Query(None, description="最大净利润同比增长率 (%)"),
    min_revenue_growth: Optional[float] = Query(None, description="最小营收同比增长率 (%)"),
    max_revenue_growth: Optional[float] = Query(None, description="最大营收同比增长率 (%)"),
    min_gross_margin: Optional[float] = Query(None, description="最小销售毛利率 (%)"),
    max_gross_margin: Optional[float] = Query(None, description="最大销售毛利率 (%)"),
    page: int = Query(1, ge=1, description="当前页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort_field: str = Query("code", description="排序字段 (code/name/close/pct_chg/amount/turnover_rate/volume_ratio/pe/pb/ps/total_mv/roe/net_profit_growth/revenue_growth/gross_margin)"),
    sort_order: str = Query("asc", description="排序方式 (asc/desc)"),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    A股股票池列表与多维量化筛选API
    整合全市场档案、实时行情与多因子量化指标
    """
    db = get_mongo_db()

    def _num(v):
        if v is None or hasattr(v, "default"):
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    def _str(v):
        if v is None or hasattr(v, "default"):
            return None
        return str(v)

    c_min_close = _num(min_close)
    c_max_close = _num(max_close)
    c_min_pct_chg = _num(min_pct_chg)
    c_max_pct_chg = _num(max_pct_chg)
    c_min_tr = _num(min_turnover_rate)
    c_max_tr = _num(max_turnover_rate)
    c_min_vr = _num(min_volume_ratio)
    c_max_vr = _num(max_volume_ratio)
    c_vol_level = _str(volume_level)
    c_kw = _str(keyword)
    c_market = _str(market)
    c_source = _str(source)
    c_min_pe = _num(min_pe)
    c_max_pe = _num(max_pe)
    c_min_pb = _num(min_pb)
    c_max_pb = _num(max_pb)
    c_min_ps = _num(min_ps)
    c_max_ps = _num(max_ps)
    c_cap_range = _str(market_cap_range)
    c_min_cap = _num(min_market_cap)
    c_max_cap = _num(max_market_cap)
    c_min_roe = _num(min_roe)
    c_max_roe = _num(max_roe)
    c_min_npg = _num(min_net_profit_growth)
    c_max_npg = _num(max_net_profit_growth)
    c_min_rg = _num(min_revenue_growth)
    c_max_rg = _num(max_revenue_growth)
    c_min_gm = _num(min_gross_margin)
    c_max_gm = _num(max_gross_margin)
    c_sort_field = _str(sort_field) or "code"
    c_sort_order = _str(sort_order) or "asc"
    c_page = int(_num(page) or 1)
    c_page_size = int(_num(page_size) or 20)

    # 1. 行情条件预筛选 (market_quotes)
    quote_filter: Dict[str, Any] = {}
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
    if c_vol_level == "high":
        quote_filter.setdefault("amount", {})["$gte"] = 1_000_000_000  # >10亿元
    elif c_vol_level == "medium":
        quote_filter.setdefault("amount", {})["$gte"] = 300_000_000
        quote_filter.setdefault("amount", {})["$lt"] = 1_000_000_000  # 3-10亿元
    elif c_vol_level == "low":
        quote_filter.setdefault("amount", {})["$lt"] = 300_000_000    # <3亿元

    quote_codes = None
    if quote_filter:
        quote_codes = await db["market_quotes"].distinct("code", quote_filter)

    # 2. 构造基础信息过滤条件（强制剔除退市标的：名称含“退”或“PT”，或上市状态为退市）
    filter_query: Dict[str, Any] = {
        "name": {"$not": {"$regex": r"退|^PT"}},
        "status": {"$nin": ["0", "delisted", "D", "退市"]}
    }
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

    # 估值因子条件
    if c_min_pe is not None:
        filter_query.setdefault("pe", {})["$gte"] = c_min_pe
    if c_max_pe is not None:
        filter_query.setdefault("pe", {})["$lte"] = c_max_pe
    if c_min_pb is not None:
        filter_query.setdefault("pb", {})["$gte"] = c_min_pb
    if c_max_pb is not None:
        filter_query.setdefault("pb", {})["$lte"] = c_max_pb
    if c_min_ps is not None:
        filter_query.setdefault("ps", {})["$gte"] = c_min_ps
    if c_max_ps is not None:
        filter_query.setdefault("ps", {})["$lte"] = c_max_ps

    # 市值范围 (total_mv 存储单位为万元)
    if c_cap_range == "small":
        filter_query.setdefault("total_mv", {})["$lt"] = 100 * 10000  # <100亿
    elif c_cap_range == "medium":
        filter_query.setdefault("total_mv", {})["$gte"] = 100 * 10000
        filter_query.setdefault("total_mv", {})["$lt"] = 500 * 10000  # 100-500亿
    elif c_cap_range == "large":
        filter_query.setdefault("total_mv", {})["$gte"] = 500 * 10000  # >500亿

    if c_min_cap is not None:
        filter_query.setdefault("total_mv", {})["$gte"] = c_min_cap * 10000
    if c_max_cap is not None:
        filter_query.setdefault("total_mv", {})["$lte"] = c_max_cap * 10000

    # 财务质量与成长因子条件
    if c_min_roe is not None:
        filter_query.setdefault("roe", {})["$gte"] = c_min_roe
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

    if c_sort_field in ["close", "pct_chg", "amount", "volume", "turnover_rate", "volume_ratio"]:
        # 基于行情数据的全市场排序
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
            "roe", "net_profit_growth", "revenue_growth", "gross_margin"
        ] else "code"
        cursor = db["stock_basic_info"].find(filter_query, {"_id": 0}).sort(mongo_sort_field, direction).skip(skip).limit(c_page_size)
        items = await cursor.to_list(length=c_page_size)

    # 4. 批量关联行情数据 (market_quotes)
    codes = [item.get("code") for item in items if item.get("code")]
    quote_map = {}
    if codes:
        quotes = await db["market_quotes"].find({"code": {"$in": codes}}, {"_id": 0}).to_list(length=len(codes))
        quote_map = {q["code"]: q for q in quotes if "code" in q}

    enriched_items = []
    for item in items:
        code = item.get("code") or item.get("symbol") or ""
        q = quote_map.get(code, {})

        close = q.get("close")
        if close is None:
            close = item.get("close")

        updated_at = item.get("updated_at")
        if hasattr(updated_at, "isoformat"):
            updated_at = updated_at.isoformat()

        turnover_rate = q.get("turnover_rate") if q.get("turnover_rate") is not None else item.get("turnover_rate")
        volume_ratio = q.get("volume_ratio") if q.get("volume_ratio") is not None else item.get("volume_ratio")
        circ_mv = q.get("circ_mv") if q.get("circ_mv") is not None else item.get("circ_mv")
        total_mv = item.get("total_mv") if item.get("total_mv") is not None else q.get("total_mv")

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
            "pe": item.get("pe"),
            "pb": item.get("pb"),
            "ps": item.get("ps"),
            "circ_mv": circ_mv,
            "total_mv": total_mv,
            "roe": item.get("roe"),
            "net_profit_growth": item.get("net_profit_growth"),
            "revenue_growth": item.get("revenue_growth"),
            "gross_margin": item.get("gross_margin"),
            "trade_date": q.get("trade_date") or item.get("trade_date", ""),
            "updated_at": updated_at
        })

    # 若根据行情字段排序，在当前批次内按需求排定
    if sort_field in ["close", "pct_chg", "amount", "volume", "turnover_rate", "volume_ratio"]:
        reverse = (sort_order.lower() == "desc")
        enriched_items.sort(
            key=lambda x: (x.get(sort_field) is not None, x.get(sort_field) or 0),
            reverse=reverse
        )

    # 统计信息（板块分布与整体指标，严格基于正常上市股票）
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

    return ok(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": enriched_items,
        "stats": stats
    })


