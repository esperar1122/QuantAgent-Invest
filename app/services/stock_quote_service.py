import logging
import json
import time
import datetime
import requests
from requests.adapters import HTTPAdapter
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# 全局高复用 HTTP 会话连接池 (复用 TCP/TLS 握手，延迟降低 65%+)
_session = requests.Session()
_adapter = HTTPAdapter(pool_connections=20, pool_maxsize=50, max_retries=1)
_session.mount("http://", _adapter)
_session.mount("https://", _adapter)
_session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

# 内存二级高频行情/K线缓存 (key -> (expire_time, data))
_KLINE_CACHE: Dict[str, tuple[float, List[Dict[str, Any]]]] = {}
_QUOTE_CACHE: Dict[str, tuple[float, Dict[str, Any]]] = {}


def _is_trading_time() -> bool:
    """判断当前时间是否处于A股交易窗口（交易时间段短TTL，休市时间段长TTL）"""
    now = datetime.datetime.now()
    if now.weekday() >= 5:  # 周末休市
        return False
    t = now.time()
    return (datetime.time(9, 15) <= t <= datetime.time(11, 35)) or (datetime.time(12, 55) <= t <= datetime.time(15, 5))


def fetch_realtime_stock_kline(code: str, period: str = "day", limit: int = 120, force_refresh: bool = False) -> List[Dict[str, Any]]:
    """
    通过腾讯高并发实时K线接口极速获取历史与包含当天实盘的K线序列 (连接池复用 + 市场感知多级缓存)
    """
    if not code:
        return []
    code_raw = str(code).strip()
    code_clean = code_raw.lower().replace("sh", "").replace("sz", "").replace("bj", "")

    tx_period = "day"
    if period in ["week", "weekly"]:
        tx_period = "week"
    elif period in ["month", "monthly"]:
        tx_period = "month"

    cache_key = f"{code_clean}_{tx_period}_{limit}"
    now_ts = time.time()

    # 1. 检查内存缓存
    if not force_refresh and cache_key in _KLINE_CACHE:
        expire_at, cached_items = _KLINE_CACHE[cache_key]
        if now_ts < expire_at:
            return [dict(it) for it in cached_items]

    if code_clean.startswith(("60", "68", "90", "50", "51", "56", "58")):
        tx_sym = f"sh{code_clean}"
    elif code_clean.startswith(("00", "30", "20", "15", "16", "39")):
        tx_sym = f"sz{code_clean}"
    elif code_clean.startswith(("8", "4", "92")):
        tx_sym = f"bj{code_clean}"
    else:
        tx_sym = f"sz{code_clean}" if code_clean.startswith("0") else f"sh{code_clean}"

    url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={tx_sym},{tx_period},,,{limit},qfq"
    try:
        resp = _session.get(url, timeout=3.0)
        data = resp.json()
        d = data.get("data", {}).get(tx_sym, {})
        k_list = d.get(tx_period) or d.get(f"qfq{tx_period}") or []
        items = []
        for row in k_list:
            if not isinstance(row, list) or len(row) < 5:
                continue
            try:
                t = str(row[0])
                o = float(row[1])
                c = float(row[2])
                h = float(row[3])
                l = float(row[4])
                v = float(row[5]) if len(row) > 5 and not isinstance(row[5], (dict, list)) else 0.0

                # 安全提取成交额（腾讯除权日会在 row[6] 插入分红送配字典，需过滤）
                amt = 0.0
                if len(row) > 6 and not isinstance(row[6], (dict, list)):
                    try:
                        amt = float(row[6]) * 10000.0
                    except (ValueError, TypeError):
                        amt = 0.0
                if amt <= 0.0 and v > 0:
                    amt = round(((o + c + h + l) / 4.0) * v * 100.0, 2)

                items.append({
                    "time": t,
                    "open": o,
                    "close": c,
                    "high": h,
                    "low": l,
                    "volume": v,
                    "amount": amt
                })
            except Exception as row_err:
                logger.debug(f"跳过异常K线行: {row_err}")
                continue
        res = items[-limit:]
        # 写入内存缓存 (交易时间 30s，盘后/周末 30分钟)
        ttl = 30.0 if _is_trading_time() else 1800.0
        _KLINE_CACHE[cache_key] = (now_ts + ttl, res)
        if len(_KLINE_CACHE) > 500:
            expired_keys = [k for k, v in _KLINE_CACHE.items() if v[0] < now_ts]
            for k in expired_keys:
                _KLINE_CACHE.pop(k, None)
        return res
    except Exception as e:
        logger.warning(f"获取实时K线异常 ({code}): {e}")
        return []



def fetch_realtime_stock_quote(code: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
    """
    通过腾讯高并发实时行情接口毫秒级获取单只标的极速快照 (连接池复用 + 亚秒级短期缓存)
    包含：现价、昨收、今开、最高、最低、成交量、成交额、换手率、振幅、PE、PB、总市值、五档盘口、交易日期
    """
    if not code:
        return None
    code_raw = str(code).strip()
    code_clean = code_raw.lower().replace("sh", "").replace("sz", "").replace("bj", "")

    cache_key = code_clean
    now_ts = time.time()
    if not force_refresh and cache_key in _QUOTE_CACHE:
        expire_at, cached_item = _QUOTE_CACHE[cache_key]
        if now_ts < expire_at:
            return dict(cached_item)

    # 判断交易所前缀
    if code_clean.startswith(("60", "68", "90", "50", "51", "56", "58")):
        tx_sym = f"sh{code_clean}"
    elif code_clean.startswith(("00", "30", "20", "15", "16", "39")):
        tx_sym = f"sz{code_clean}"
    elif code_clean.startswith(("8", "4", "92")):
        tx_sym = f"bj{code_clean}"
    else:
        tx_sym = f"sz{code_clean}" if code_clean.startswith("0") else f"sh{code_clean}"

    url = f"http://qt.gtimg.cn/q={tx_sym}"
    try:
        resp = _session.get(url, timeout=2.5)
        data = resp.content.decode("gbk", errors="ignore")

        if "=" not in data or "~" not in data:
            return None

        fields = data.strip().split("~")
        if len(fields) < 38:
            return None

        t_str = fields[30] if len(fields) > 30 else ""
        trade_date = f"{t_str[:4]}-{t_str[4:6]}-{t_str[6:8]}" if len(t_str) >= 8 else ""

        px = float(fields[3]) if fields[3] else 0.0
        pre_close = float(fields[4]) if fields[4] else px
        open_px = float(fields[5]) if fields[5] else pre_close
        high_px = float(fields[33]) if fields[33] else max(px, open_px)
        low_px = float(fields[34]) if fields[34] else min(px, open_px)
        vol = float(fields[6]) if fields[6] else 0.0
        amt = float(fields[37]) * 10000.0 if fields[37] else 0.0
        chg = float(fields[31]) if fields[31] else (px - pre_close)
        pct = float(fields[32]) if fields[32] else 0.0
        turnover = float(fields[38]) if fields[38] else 0.0
        amp = float(fields[43]) if len(fields) > 43 and fields[43] else 0.0
        pe_val = float(fields[39]) if len(fields) > 39 and fields[39] else 0.0
        pb_val = float(fields[46]) if len(fields) > 46 and fields[46] else 0.0
        mv_val = float(fields[45]) if len(fields) > 45 and fields[45] else 0.0

        # 五档买卖挂单
        ask_orders = [
            {"level": "卖五", "price": float(fields[27]) if fields[27] else 0.0, "qty": int(fields[28]) if fields[28] else 0},
            {"level": "卖四", "price": float(fields[25]) if fields[25] else 0.0, "qty": int(fields[26]) if fields[26] else 0},
            {"level": "卖三", "price": float(fields[23]) if fields[23] else 0.0, "qty": int(fields[24]) if fields[24] else 0},
            {"level": "卖二", "price": float(fields[21]) if fields[21] else 0.0, "qty": int(fields[22]) if fields[22] else 0},
            {"level": "卖一", "price": float(fields[19]) if fields[19] else 0.0, "qty": int(fields[20]) if fields[20] else 0},
        ]
        bid_orders = [
            {"level": "买一", "price": float(fields[9]) if fields[9] else 0.0, "qty": int(fields[10]) if fields[10] else 0},
            {"level": "买二", "price": float(fields[11]) if fields[11] else 0.0, "qty": int(fields[12]) if fields[12] else 0},
            {"level": "买三", "price": float(fields[13]) if fields[13] else 0.0, "qty": int(fields[14]) if fields[14] else 0},
            {"level": "买四", "price": float(fields[15]) if fields[15] else 0.0, "qty": int(fields[16]) if fields[16] else 0},
            {"level": "买五", "price": float(fields[17]) if fields[17] else 0.0, "qty": int(fields[18]) if fields[18] else 0},
        ]

        result = {
            "code": code_clean,
            "name": fields[1],
            "price": px,
            "close": px,
            "prev_close": pre_close,
            "open": open_px,
            "high": high_px,
            "low": low_px,
            "volume": vol,
            "amount": amt,
            "change": round(chg, 2),
            "pct_chg": round(pct, 2),
            "change_percent": round(pct, 2),
            "turnover_rate": turnover,
            "amplitude": amp,
            "pe": pe_val,
            "pb": pb_val,
            "total_mv": mv_val,
            "trade_date": trade_date,
            "ask_orders": ask_orders,
            "bid_orders": bid_orders
        }

        # 缓存极速行情 (交易时间 2.5s，休市 60s)
        ttl = 2.5 if _is_trading_time() else 60.0
        _QUOTE_CACHE[cache_key] = (now_ts + ttl, result)
        if len(_QUOTE_CACHE) > 500:
            expired_keys = [k for k, v in _QUOTE_CACHE.items() if v[0] < now_ts]
            for k in expired_keys:
                _QUOTE_CACHE.pop(k, None)

        return result
    except Exception as e:
        logger.warning(f"获取腾讯实时行情异常 ({code}): {e}")
        return None
