"""
A股重要指数服务模块 (沪深300、中证500、科创综指、科创50、半导体指数、上证指数等)
提供：
1. 指数基础定义与代码映射
2. 实时行情获取与数据库同步入库 (Tencent API)
3. 历史/实时 K 线获取与缓存降级 (Tencent + Sina API)
"""
import logging
import datetime
import asyncio
from typing import List, Dict, Any, Tuple, Optional
import requests

logger = logging.getLogger(__name__)

_last_index_sync_time: Optional[datetime.datetime] = None
_sync_lock = asyncio.Lock()

# 核心指数配置清单
SUPPORTED_INDICES: Dict[str, Dict[str, Any]] = {
    "sh000300": {
        "code": "sh000300",
        "symbol": "000300.SH",
        "name": "沪深300",
        "market": "重要指数",
        "industry": "核心蓝筹",
        "category": "index_cn",
        "is_index": True,
        "status": "1",
        "source": "tencent",
        "tx_sym": "sh000300",
        "sina_sym": "sh000300",
    },
    "sh000905": {
        "code": "sh000905",
        "symbol": "000905.SH",
        "name": "中证500",
        "market": "重要指数",
        "industry": "中盘成长",
        "category": "index_cn",
        "is_index": True,
        "status": "1",
        "source": "tencent",
        "tx_sym": "sh000905",
        "sina_sym": "sh000905",
    },
    "sh000680": {
        "code": "sh000680",
        "symbol": "000680.SH",
        "name": "科创综指",
        "market": "重要指数",
        "industry": "硬核科技",
        "category": "index_cn",
        "is_index": True,
        "status": "1",
        "source": "tencent",
        "tx_sym": "sh000680",
        "sina_sym": "sh000680",
    },
    "sh000688": {
        "code": "sh000688",
        "symbol": "000688.SH",
        "name": "科创50",
        "market": "重要指数",
        "industry": "硬科技龙头",
        "category": "index_cn",
        "is_index": True,
        "status": "1",
        "source": "tencent",
        "tx_sym": "sh000688",
        "sina_sym": "sh000688",
    },
    "sz980017": {
        "code": "sz980017",
        "symbol": "980017.SZ",
        "name": "半导体指数",
        "market": "重要指数",
        "industry": "半导体芯片",
        "category": "index_cn",
        "is_index": True,
        "status": "1",
        "source": "tencent",
        "tx_sym": "sz980017",
        "sina_sym": "sz980017",
    },
    "sh000001": {
        "code": "sh000001",
        "symbol": "000001.SH",
        "name": "上证指数",
        "market": "重要指数",
        "industry": "大盘基准",
        "category": "index_cn",
        "is_index": True,
        "status": "1",
        "source": "tencent",
        "tx_sym": "sh000001",
        "sina_sym": "sh000001",
    },
    "sz399001": {
        "code": "sz399001",
        "symbol": "399001.SZ",
        "name": "深证成指",
        "market": "重要指数",
        "industry": "大盘宽基",
        "category": "index_cn",
        "is_index": True,
        "status": "1",
        "source": "tencent",
        "tx_sym": "sz399001",
        "sina_sym": "sz399001",
    },
    "sz399006": {
        "code": "sz399006",
        "symbol": "399006.SZ",
        "name": "创业板指",
        "market": "重要指数",
        "industry": "创新成长",
        "category": "index_cn",
        "is_index": True,
        "status": "1",
        "source": "tencent",
        "tx_sym": "sz399006",
        "sina_sym": "sz399006",
    },
    "sh000852": {
        "code": "sh000852",
        "symbol": "000852.SH",
        "name": "中证1000",
        "market": "重要指数",
        "industry": "小盘成长",
        "category": "index_cn",
        "is_index": True,
        "status": "1",
        "source": "tencent",
        "tx_sym": "sh000852",
        "sina_sym": "sh000852",
    },
    "sh000016": {
        "code": "sh000016",
        "symbol": "000016.SH",
        "name": "上证50",
        "market": "重要指数",
        "industry": "超大盘蓝筹",
        "category": "index_cn",
        "is_index": True,
        "status": "1",
        "source": "tencent",
        "tx_sym": "sh000016",
        "sina_sym": "sh000016",
    },
}

# 别名映射（用户可能输入的格式 -> 标准规范 code）
INDEX_ALIAS_MAP: Dict[str, str] = {
    # 沪深300
    "000300": "sh000300",
    "000300.sh": "sh000300",
    "sh000300": "sh000300",
    "沪深300": "sh000300",
    # 中证500
    "000905.sh": "sh000905",
    "sh000905": "sh000905",
    "中证500": "sh000905",
    # 科创综指
    "000680.sh": "sh000680",
    "sh000680": "sh000680",
    "科创综指": "sh000680",
    # 科创50
    "000688.sh": "sh000688",
    "sh000688": "sh000688",
    "科创50": "sh000688",
    # 半导体指数 (国证芯片)
    "980017": "sz980017",
    "980017.sz": "sz980017",
    "sz980017": "sz980017",
    "半导体指数": "sz980017",
    "国证芯片": "sz980017",
    # 上证指数
    "sh000001": "sh000001",
    "000001.sh": "sh000001",
    "上证指数": "sh000001",
    # 深证成指
    "399001": "sz399001",
    "399001.sz": "sz399001",
    "sz399001": "sz399001",
    "深证成指": "sz399001",
    # 创业板指
    "399006": "sz399006",
    "399006.sz": "sz399006",
    "sz399006": "sz399006",
    "创业板指": "sz399006",
    # 中证1000
    "000852.sh": "sh000852",
    "sh000852": "sh000852",
    "中证1000": "sh000852",
    # 上证50
    "000016.sh": "sh000016",
    "sh000016": "sh000016",
    "上证50": "sh000016",
}


def is_index_code(code: str) -> bool:
    """判断给定的代码是否为支持的指数"""
    if not code:
        return False
    c = str(code).strip().lower()
    return c in INDEX_ALIAS_MAP or c in SUPPORTED_INDICES


def normalize_index_code(code: str) -> str:
    """标准化指数代码，统一返回 sh000300, sz980017 这种内部唯一标识"""
    c = str(code).strip().lower()
    return INDEX_ALIAS_MAP.get(c, c)


def get_index_name(code: str) -> str:
    """获取指数名称"""
    norm = normalize_index_code(code)
    return SUPPORTED_INDICES.get(norm, {}).get("name", norm)


def fetch_all_index_quotes() -> List[Dict[str, Any]]:
    """
    通过腾讯行情接口毫秒级批量获取所有支持的指数最新行情
    """
    syms = [info["tx_sym"] for info in SUPPORTED_INDICES.values()]
    query_str = ",".join(syms)
    url = f"http://qt.gtimg.cn/q={query_str}"

    results = []
    try:
        r = requests.get(url, timeout=5)
        r.encoding = "gbk"
        lines = r.text.strip().split(";")
        for line in lines:
            line = line.strip()
            if not line or "=" not in line:
                continue
            parts = line.split("=")
            raw_sym = parts[0].replace("v_", "").strip().lower()
            norm_code = normalize_index_code(raw_sym)
            if norm_code not in SUPPORTED_INDICES:
                continue

            fields = parts[1].strip('"').split("~")
            if len(fields) < 38:
                continue

            clean_name = SUPPORTED_INDICES[norm_code].get("name") or fields[1]
            close = float(fields[3]) if fields[3] else 0.0
            prev_close = float(fields[4]) if fields[4] else close
            open_price = float(fields[5]) if fields[5] else close
            vol = float(fields[6]) if fields[6] else 0.0
            change = float(fields[31]) if fields[31] else 0.0
            pct_chg = float(fields[32]) if fields[32] else 0.0
            high = float(fields[33]) if fields[33] else close
            low = float(fields[34]) if fields[34] else close
            # fields[37] 是以万元为单位的成交额
            amount = float(fields[37]) * 10000.0 if fields[37] else 0.0

            # 交易时间
            time_str = fields[30] if len(fields) > 30 else ""
            trade_date = time_str[:8] if len(time_str) >= 8 else datetime.datetime.now().strftime("%Y%m%d")

            results.append({
                "code": norm_code,
                "symbol": SUPPORTED_INDICES[norm_code]["symbol"],
                "name": clean_name,
                "market": "重要指数",
                "close": close,
                "price": close,
                "current_price": close,
                "prev_close": prev_close,
                "open": open_price,
                "high": high,
                "low": low,
                "volume": vol,
                "amount": amount,
                "change": change,
                "pct_chg": pct_chg,
                "change_percent": pct_chg,
                "trade_date": trade_date,
                "updated_at": datetime.datetime.now(),
                "data_source": "tencent",
                "sync_status": "success",
                "is_index": True
            })
    except Exception as e:
        logger.error(f"❌ 批量获取指数行情失败: {e}")

    return results


async def sync_indices_to_db(force: bool = False) -> int:
    """
    将核心指数基本信息与最新行情同步至 MongoDB
    通过 asyncio.to_thread 非阻塞执行，并加锁与冷却防抖以消除并发请求等待
    """
    global _last_index_sync_time
    now = datetime.datetime.now()
    if not force and _last_index_sync_time and (now - _last_index_sync_time).total_seconds() < 8:
        return 0

    async with _sync_lock:
        now = datetime.datetime.now()
        if not force and _last_index_sync_time and (now - _last_index_sync_time).total_seconds() < 8:
            return 0

        from app.core.database import get_mongo_db
        db = get_mongo_db()

        # 异步线程拉取腾讯行情，不阻塞主事件循环
        quotes = await asyncio.to_thread(fetch_all_index_quotes)
        if not quotes:
            return 0

        for q in quotes:
            code = q["code"]
            await db["market_quotes"].update_one(
                {"code": code},
                {"$set": q},
                upsert=True
            )

        _last_index_sync_time = datetime.datetime.now()
        logger.info(f"✅ 成功非阻塞同步 {len(quotes)} 只核心指数最新行情")
        return len(quotes)


def fetch_index_kline(code: str, period: str = "day", limit: int = 120) -> Tuple[List[Dict[str, Any]], str]:
    """
    获取指数历史与实时 K 线数据（双通道引擎）
    首选：腾讯 fqkline (毫秒级支持 day/week/month)
    备选：新浪 CN_MarketDataService (支持深证/国证系列指数)
    """
    norm_code = normalize_index_code(code)
    info = SUPPORTED_INDICES.get(norm_code, {})
    tx_sym = info.get("tx_sym", norm_code)
    sina_sym = info.get("sina_sym", norm_code)

    tx_period = "day"
    if period in ["week", "weekly"]:
        tx_period = "week"
    elif period in ["month", "monthly"]:
        tx_period = "month"

    # 1. 首选腾讯接口
    url_tx = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={tx_sym},{tx_period},,,{limit},qfq"
    try:
        r = requests.get(url_tx, timeout=4)
        data = r.json().get("data", {}).get(tx_sym, {})
        k_list = data.get(tx_period) or data.get(f"qfq{tx_period}") or []
        if len(k_list) >= 5:
            items = []
            for row in k_list:
                if not isinstance(row, list) or len(row) < 5:
                    continue
                try:
                    v = float(row[5]) if len(row) > 5 and not isinstance(row[5], (dict, list)) else 0.0
                    amt = 0.0
                    if len(row) > 6 and not isinstance(row[6], (dict, list)):
                        try:
                            amt = float(row[6])
                        except (ValueError, TypeError):
                            amt = 0.0
                    items.append({
                        "time": str(row[0]),
                        "open": float(row[1]),
                        "close": float(row[2]),
                        "high": float(row[3]),
                        "low": float(row[4]),
                        "volume": v,
                        "amount": amt
                    })
                except Exception:
                    continue
            return items[-limit:], "tencent"
    except Exception as e:
        logger.warning(f"⚠️ 腾讯指数K线获取异常 ({tx_sym}): {e}")

    # 2. 备选新浪接口
    scale_map = {"day": "240", "week": "1200", "month": "7200"}
    scale = scale_map.get(tx_period, "240")
    url_sina = f"https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData?symbol={sina_sym}&scale={scale}&ma=no&datalen={limit}"
    try:
        r = requests.get(url_sina, timeout=4)
        data = r.json()
        if isinstance(data, list) and len(data) >= 5:
            items = []
            for row in data:
                items.append({
                    "time": row["day"],
                    "open": float(row["open"]),
                    "close": float(row["close"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "volume": float(row["volume"]),
                    "amount": 0.0
                })
            return items[-limit:], "sina"
    except Exception as e:
        logger.warning(f"⚠️ 新浪指数K线获取异常 ({sina_sym}): {e}")

    return [], "none"


def fetch_timeline_data(code: str) -> Dict[str, Any]:
    """
    获取高保真分时走势数据（分钟线、均线、分时成交量）
    支持核心指数与A股个股
    """
    norm_code = normalize_index_code(code)
    raw_lower = str(code).strip().lower()

    if norm_code in SUPPORTED_INDICES:
        tx_sym = SUPPORTED_INDICES[norm_code]["tx_sym"]
        sina_sym = SUPPORTED_INDICES[norm_code]["sina_sym"]
        name = SUPPORTED_INDICES[norm_code]["name"]
    else:
        if raw_lower.startswith("sh"):
            prefix = "sh"
            clean_num = raw_lower[2:]
        elif raw_lower.startswith("sz"):
            prefix = "sz"
            clean_num = raw_lower[2:]
        elif raw_lower.startswith("bj"):
            prefix = "bj"
            clean_num = raw_lower[2:]
        elif raw_lower.endswith(".sh"):
            prefix = "sh"
            clean_num = raw_lower[:-3]
        elif raw_lower.endswith(".sz"):
            prefix = "sz"
            clean_num = raw_lower[:-3]
        elif raw_lower.endswith(".bj"):
            prefix = "bj"
            clean_num = raw_lower[:-3]
        else:
            clean_num = raw_lower
            if clean_num.startswith(("6", "900")):
                prefix = "sh"
            elif clean_num.startswith(("8", "4", "920")):
                prefix = "bj"
            else:
                prefix = "sz"
        tx_sym = f"{prefix}{clean_num}"
        sina_sym = f"{prefix}{clean_num}"
        name = code

    # 1. 毫秒级抓取最新盘口与昨收基准
    curr_price = 0.0
    prev_close = 0.0
    change_val = 0.0
    pct_val = 0.0
    tot_vol = 0.0
    tot_amt = 0.0

    try:
        url_q = f"http://qt.gtimg.cn/q=s_{tx_sym}"
        rq = requests.get(url_q, timeout=3)
        rq.encoding = "gbk"
        if "~" in rq.text:
            parts = rq.text.split("~")
            if len(parts) > 1 and parts[1]:
                name = parts[1]
            if len(parts) > 3 and parts[3]:
                curr_price = float(parts[3])
            if len(parts) > 4 and parts[4]:
                change_val = float(parts[4])
            if len(parts) > 5 and parts[5]:
                pct_val = float(parts[5])
            if len(parts) > 6 and parts[6]:
                tot_vol = float(parts[6])
            if len(parts) > 7 and parts[7]:
                tot_amt = float(parts[7]) * 10000.0  # 万元转元
            prev_close = curr_price - change_val
    except Exception as qe:
        logger.debug(f"抓取盘口昨收异常: {qe}")

    # 2. 获取1分钟分时序列 (Sina 1-min)
    items = []
    source = "sina"
    high_price = curr_price or 0.0
    low_price = curr_price or 0.0

    try:
        url_sina = f"https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData?symbol={sina_sym}&scale=1&ma=no&datalen=300"
        rk = requests.get(url_sina, timeout=4)
        raw_list = rk.json()
        if isinstance(raw_list, list) and raw_list:
            now = datetime.datetime.now()
            today_str = now.strftime("%Y-%m-%d")

            today_rows = [p for p in raw_list if p.get("day", "").startswith(today_str)]
            if not today_rows:
                dates = sorted(set(p.get("day", "")[:10] for p in raw_list if p.get("day")))
                if dates:
                    today_rows = [p for p in raw_list if p.get("day", "").startswith(dates[-1])]

            if today_rows:
                if not prev_close:
                    prev_close = float(today_rows[0].get("open", curr_price))

                cum_pa = 0.0
                cum_a = 0.0
                high_price = -1e9
                low_price = 1e9
                last_p = prev_close

                for row in today_rows:
                    day_str = row.get("day", "")
                    time_str = day_str[-8:-3] if len(day_str) >= 8 else "09:30"
                    p = float(row.get("close", 0.0))
                    a = float(row.get("amount", 0.0))
                    v = float(row.get("volume", 0.0))

                    cum_pa += p * a
                    cum_a += a
                    avg = (cum_pa / cum_a) if cum_a > 0 else p

                    high_price = max(high_price, p)
                    low_price = min(low_price, p)

                    diff = p - prev_close
                    pct = (diff / prev_close * 100.0) if prev_close else 0.0

                    items.append({
                        "time": time_str,
                        "day": day_str,
                        "price": round(p, 3),
                        "avg_price": round(avg, 3),
                        "volume": round(v, 2),
                        "amount": round(a, 2),
                        "change": round(diff, 3),
                        "pct_chg": round(pct, 2),
                        "is_up": p >= last_p
                    })
                    last_p = p

                if items:
                    curr_price = items[-1]["price"]
                    change_val = round(curr_price - prev_close, 3)
                    pct_val = round((change_val / prev_close * 100.0) if prev_close else 0.0, 2)
    except Exception as e:
        logger.warning(f"⚠️ 分时线获取异常 ({sina_sym}): {e}")

    # 计算对称动态量程比例 (默认最小 0.5%)
    max_diff = max(abs(high_price - prev_close), abs(low_price - prev_close), abs(change_val))
    max_ratio = max((max_diff / prev_close) if prev_close else 0.005, 0.005)

    return {
        "code": norm_code,
        "name": name,
        "prev_close": round(prev_close, 3),
        "current_price": round(curr_price, 3),
        "change": round(change_val, 3),
        "change_percent": round(pct_val, 2),
        "high": round(high_price, 3) if high_price > -1e8 else curr_price,
        "low": round(low_price, 3) if low_price < 1e8 else curr_price,
        "max_ratio": round(max_ratio, 5),
        "total_volume": tot_vol,
        "total_amount": tot_amt,
        "count": len(items),
        "items": items,
        "source": source
    }
