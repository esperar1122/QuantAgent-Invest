"""
自适应冷启动静默初始化守护服务 (Adaptive Cold-Start Bootstrapper)
当数据库为空或全新部署时，自动静默注入全市场核心蓝筹、白马股、核心宽基/行业ETF股票池与基础元数据，
杜绝新用户部署启动后股票池为空、无标的可查、指标与推演冷启动崩溃问题。
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from pymongo import UpdateOne

from app.core.database import get_mongo_db
from app.services.quotes.realtime_streamer import get_quote_streamer
from app.services.paper_trading.paper_account_service import paper_account_service

logger = logging.getLogger(__name__)

# 权威核心种子标的池（涵盖A股各大行业核心龙头、科技自主可控及全系列核心宽基与行业ETF）
SEED_STOCKS: List[Dict[str, Any]] = [
    # 1. 核心宽基与行业ETF
    {"code": "510300", "symbol": "sh510300", "name": "沪深300ETF", "industry": "多元金融", "market": "ETF", "is_etf": True, "pe": 12.5, "pb": 1.3},
    {"code": "510050", "symbol": "sh510050", "name": "上证50ETF", "industry": "多元金融", "market": "ETF", "is_etf": True, "pe": 10.2, "pb": 1.1},
    {"code": "588000", "symbol": "sh588000", "name": "科创50ETF", "industry": "多元金融", "market": "ETF", "is_etf": True, "pe": 45.0, "pb": 3.8},
    {"code": "159915", "symbol": "sz159915", "name": "创业板ETF", "industry": "多元金融", "market": "ETF", "is_etf": True, "pe": 28.5, "pb": 3.2},
    {"code": "510500", "symbol": "sh510500", "name": "中证500ETF", "industry": "多元金融", "market": "ETF", "is_etf": True, "pe": 18.0, "pb": 1.6},
    {"code": "512880", "symbol": "sh512880", "name": "证券ETF", "industry": "非银金融", "market": "ETF", "is_etf": True, "pe": 19.5, "pb": 1.4},
    {"code": "512690", "symbol": "sh512690", "name": "酒ETF", "industry": "食品饮料", "market": "ETF", "is_etf": True, "pe": 21.0, "pb": 4.5},
    {"code": "512480", "symbol": "sh512480", "name": "半导体ETF", "industry": "电子", "market": "ETF", "is_etf": True, "pe": 55.0, "pb": 4.2},
    {"code": "515050", "symbol": "sh515050", "name": "5G通信ETF", "industry": "通信", "market": "ETF", "is_etf": True, "pe": 26.0, "pb": 2.5},

    # 2. 消费与白酒龙头
    {"code": "600519", "symbol": "sh600519", "name": "贵州茅台", "industry": "食品饮料", "market": "主板", "is_etf": False, "pe": 24.5, "pb": 7.8},
    {"code": "000858", "symbol": "sz000858", "name": "五粮液", "industry": "食品饮料", "market": "主板", "is_etf": False, "pe": 16.8, "pb": 4.1},
    {"code": "000568", "symbol": "sz000568", "name": "泸州老窖", "industry": "食品饮料", "market": "主板", "is_etf": False, "pe": 15.5, "pb": 3.9},
    {"code": "600887", "symbol": "sh600887", "name": "伊利股份", "industry": "食品饮料", "market": "主板", "is_etf": False, "pe": 14.2, "pb": 3.1},
    {"code": "603288", "symbol": "sh603288", "name": "海天味业", "industry": "食品饮料", "market": "主板", "is_etf": False, "pe": 32.0, "pb": 6.2},

    # 3. 新能源、汽车与绿色电力
    {"code": "300750", "symbol": "sz300750", "name": "宁德时代", "industry": "电力设备", "market": "创业板", "is_etf": False, "pe": 18.5, "pb": 4.5},
    {"code": "002594", "symbol": "sz002594", "name": "比亚迪", "industry": "汽车", "market": "主板", "is_etf": False, "pe": 22.0, "pb": 4.8},
    {"code": "601012", "symbol": "sh601012", "name": "隆基绿能", "industry": "电力设备", "market": "主板", "is_etf": False, "pe": 15.0, "pb": 1.8},
    {"code": "600900", "symbol": "sh600900", "name": "长江电力", "industry": "公用事业", "market": "主板", "is_etf": False, "pe": 21.0, "pb": 3.2},
    {"code": "601899", "symbol": "sh601899", "name": "紫金矿业", "industry": "有色金属", "market": "主板", "is_etf": False, "pe": 14.5, "pb": 3.0},

    # 4. 金融核心支柱
    {"code": "601318", "symbol": "sh601318", "name": "中国平安", "industry": "非银金融", "market": "主板", "is_etf": False, "pe": 9.5, "pb": 1.0},
    {"code": "600036", "symbol": "sh600036", "name": "招商银行", "industry": "银行", "market": "主板", "is_etf": False, "pe": 6.2, "pb": 0.85},
    {"code": "000001", "symbol": "sz000001", "name": "平安银行", "industry": "银行", "market": "主板", "is_etf": False, "pe": 5.1, "pb": 0.55},
    {"code": "601398", "symbol": "sh601398", "name": "工商银行", "industry": "银行", "market": "主板", "is_etf": False, "pe": 5.4, "pb": 0.58},
    {"code": "600030", "symbol": "sh600030", "name": "中信证券", "industry": "非银金融", "market": "主板", "is_etf": False, "pe": 16.0, "pb": 1.25},
    {"code": "300059", "symbol": "sz300059", "name": "东方财富", "industry": "非银金融", "market": "创业板", "is_etf": False, "pe": 28.0, "pb": 2.9},

    # 5. 半导体与科技自主可控
    {"code": "688981", "symbol": "sh688981", "name": "中芯国际", "industry": "电子", "market": "科创板", "is_etf": False, "pe": 65.0, "pb": 3.5},
    {"code": "002415", "symbol": "sz002415", "name": "海康威视", "industry": "电子", "market": "主板", "is_etf": False, "pe": 19.0, "pb": 3.2},
    {"code": "002230", "symbol": "sz002230", "name": "科大讯飞", "industry": "计算机", "market": "主板", "is_etf": False, "pe": 52.0, "pb": 4.1},
    {"code": "688041", "symbol": "sh688041", "name": "海光信息", "industry": "电子", "market": "科创板", "is_etf": False, "pe": 78.0, "pb": 8.5},
    {"code": "603501", "symbol": "sh603501", "name": "韦尔股份", "industry": "电子", "market": "主板", "is_etf": False, "pe": 42.0, "pb": 4.3},
    {"code": "002371", "symbol": "sz002371", "name": "北方华创", "industry": "电子", "market": "主板", "is_etf": False, "pe": 35.0, "pb": 5.8},
    {"code": "688008", "symbol": "sh688008", "name": "澜起科技", "industry": "电子", "market": "科创板", "is_etf": False, "pe": 48.0, "pb": 4.9},

    # 6. 生物医药与医疗健康
    {"code": "600276", "symbol": "sh600276", "name": "恒瑞医药", "industry": "医药生物", "market": "主板", "is_etf": False, "pe": 45.0, "pb": 5.2},
    {"code": "300760", "symbol": "sz300760", "name": "迈瑞医疗", "industry": "医药生物", "market": "创业板", "is_etf": False, "pe": 26.0, "pb": 6.8},
    {"code": "603259", "symbol": "sh603259", "name": "药明康德", "industry": "医药生物", "market": "主板", "is_etf": False, "pe": 18.0, "pb": 2.8},
    {"code": "000538", "symbol": "sz000538", "name": "云南白药", "industry": "医药生物", "market": "主板", "is_etf": False, "pe": 21.0, "pb": 2.4},

    # 7. 央企中特估、能源与基础设施
    {"code": "601857", "symbol": "sh601857", "name": "中国石油", "industry": "石油石化", "market": "主板", "is_etf": False, "pe": 9.2, "pb": 1.05},
    {"code": "600938", "symbol": "sh600938", "name": "中国海油", "industry": "石油石化", "market": "主板", "is_etf": False, "pe": 8.5, "pb": 1.55},
    {"code": "601088", "symbol": "sh601088", "name": "中国神华", "industry": "煤炭", "market": "主板", "is_etf": False, "pe": 10.5, "pb": 1.7},
    {"code": "600941", "symbol": "sh600941", "name": "中国移动", "industry": "通信", "market": "主板", "is_etf": False, "pe": 14.5, "pb": 1.5},
    {"code": "601728", "symbol": "sh601728", "name": "中国电信", "industry": "通信", "market": "主板", "is_etf": False, "pe": 15.0, "pb": 1.2},
    {"code": "600050", "symbol": "sh600050", "name": "中国联通", "industry": "通信", "market": "主板", "is_etf": False, "pe": 16.5, "pb": 1.0},
    {"code": "601127", "symbol": "sh601127", "name": "赛力斯", "industry": "汽车", "market": "主板", "is_etf": False, "pe": 32.0, "pb": 7.0},
]


class ColdStartService:
    """自适应冷启动守护服务"""

    async def bootstrap_if_needed(self) -> Dict[str, Any]:
        """
        在系统启动阶段自检：
        若基础库为空，静默注入种子核心股票池并异步补齐实时盘口与默认模拟盘账户
        """
        try:
            from app.core.database import get_mongo_db, get_database
            try:
                db = get_mongo_db()
            except Exception:
                db = get_database()
        except Exception:
            db = None

        if db is None:
            logger.info("MongoDB未连接或未初始化，跳过冷启动静默初始化")
            return {"status": "skipped", "reason": "db_not_ready"}

        try:
            # 1. 检查股票基础信息池 stock_basic_info
            col_basics = db["stock_basic_info"]
            count = await col_basics.count_documents({})

            injected_count = 0
            if count < 20:
                logger.info(f"🌱 [Cold-Start] 检测到 stock_basic_info 数量极少 ({count} 条)，触发自适应冷启动种子注入...")
                now_str = datetime.now().isoformat()
                operations = []
                for item in SEED_STOCKS:
                    doc = item.copy()
                    doc["status"] = "L"
                    doc["source"] = "cold_start_seed"
                    doc["created_at"] = now_str
                    doc["updated_at"] = now_str
                    operations.append(
                        UpdateOne(
                            {"code": item["code"]},
                            {"$set": doc},
                            upsert=True
                        )
                    )
                if operations:
                    res = await col_basics.bulk_write(operations, ordered=False)
                    injected_count = res.upserted_count + res.modified_count
                    logger.info(f"✅ [Cold-Start] 成功注入 {injected_count} 只核心蓝筹与ETF基础标的")

            # 2. 建立必要的高性能索引
            try:
                await col_basics.create_index("code", unique=True)
                await col_basics.create_index("symbol")
                await col_basics.create_index("name")
            except Exception as ie:
                logger.debug(f"创建索引提示: {ie}")

            # 3. 检查并初始化默认模拟盘账户
            try:
                await paper_account_service.get_or_create_account("default", initial_cash=100000.0)
            except Exception as pe:
                logger.warning(f"默认模拟盘账户初始化异常: {pe}")

            # 4. 后台静默抓取并刷新种子标的实时行情快照 (不阻塞主线程)
            if injected_count > 0 or count < 20:
                asyncio.create_task(self._async_refresh_seed_quotes())

            return {
                "status": "success",
                "injected_count": injected_count,
                "current_total": count + injected_count
            }
        except Exception as e:
            logger.error(f"❌ [Cold-Start] 冷启动初始化失败: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def _async_refresh_seed_quotes(self):
        """异步拉取种子标的秒级行情并填充至 market_quotes 与 stock_basic_info"""
        try:
            symbols = [s["symbol"] for s in SEED_STOCKS]
            streamer = get_quote_streamer()
            quotes = await streamer.fetch_batch_quotes(symbols)
            if not quotes:
                return

            db = get_mongo_db()
            if db is None:
                return

            col_basics = db["stock_basic_info"]
            col_quotes = db["market_quotes"]

            basic_ops = []
            quote_ops = []
            now_iso = datetime.now().isoformat()

            for sym, q in quotes.items():
                code = q.get("code")
                if not code:
                    continue

                px = q.get("price", 0.0)
                if px <= 0:
                    continue

                basic_ops.append(
                    UpdateOne(
                        {"code": code},
                        {
                            "$set": {
                                "price": px,
                                "change_pct": q.get("change_pct", 0.0),
                                "turnover_rate": q.get("turnover_rate", 0.0),
                                "pe": q.get("pe_ttm") or 15.0,
                                "market_cap": q.get("market_cap_yi", 0.0),
                                "last_quote_time": now_iso
                            }
                        }
                    )
                )

                quote_ops.append(
                    UpdateOne(
                        {"code": code},
                        {"$set": {**q, "updated_at": now_iso}},
                        upsert=True
                    )
                )

            if basic_ops:
                await col_basics.bulk_write(basic_ops, ordered=False)
            if quote_ops:
                await col_quotes.bulk_write(quote_ops, ordered=False)

            logger.info(f"✨ [Cold-Start] 已异步更新 {len(basic_ops)} 只种子标的实时行情与估值数据")
        except Exception as e:
            logger.warning(f"⚠️ [Cold-Start] 种子标的行情异步刷新失败 (不影响正常运行): {e}")


# 全局单例
cold_start_service = ColdStartService()
