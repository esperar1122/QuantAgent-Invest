"""
实时股票行情获取服务 (毫秒级快照，支持A股全市场直连与五档盘口提取)
"""
import logging
import json
import urllib.request
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def fetch_realtime_stock_kline(code: str, period: str = "day", limit: int = 120) -> List[Dict[str, Any]]:
    """
    通过腾讯高并发实时K线接口极速获取历史与包含当天实盘的K线序列 (50ms响应)
    """
    if not code:
        return []
    code_raw = str(code).strip()
    code_clean = code_raw.lower().replace("sh", "").replace("sz", "").replace("bj", "")

    if code_clean.startswith(("60", "68", "90")):
        tx_sym = f"sh{code_clean}"
    elif code_clean.startswith(("00", "30", "20")):
        tx_sym = f"sz{code_clean}"
    elif code_clean.startswith(("8", "4", "92")):
        tx_sym = f"bj{code_clean}"
    else:
        tx_sym = f"sz{code_clean}" if code_clean.startswith("0") else f"sh{code_clean}"

    tx_period = "day"
    if period in ["week", "weekly"]:
        tx_period = "week"
    elif period in ["month", "monthly"]:
        tx_period = "month"

    url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={tx_sym},{tx_period},,,{limit},qfq"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode())
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
        return items[-limit:]
    except Exception as e:
        logger.warning(f"获取实时K线异常 ({code}): {e}")
        return []



def fetch_realtime_stock_quote(code: str) -> Optional[Dict[str, Any]]:
    """
    通过腾讯高并发实时行情接口毫秒级获取单只标的极速快照
    包含：现价、昨收、今开、最高、最低、成交量、成交额、换手率、振幅、PE、PB、总市值、五档盘口、交易日期
    """
    if not code:
        return None
    code_raw = str(code).strip()
    code_clean = code_raw.lower().replace("sh", "").replace("sz", "").replace("bj", "")

    # 判断交易所前缀
    if code_clean.startswith(("60", "68", "90")):
        tx_sym = f"sh{code_clean}"
    elif code_clean.startswith(("00", "30", "20")):
        tx_sym = f"sz{code_clean}"
    elif code_clean.startswith(("8", "4", "92")):
        tx_sym = f"bj{code_clean}"
    else:
        tx_sym = f"sz{code_clean}" if code_clean.startswith("0") else f"sh{code_clean}"

    url = f"http://qt.gtimg.cn/q={tx_sym}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = resp.read().decode("gbk", errors="ignore")

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
        vol = float(fields[6]) * 100.0 if fields[6] else 0.0
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

        return {
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
    except Exception as e:
        logger.warning(f"获取腾讯实时行情异常 ({code}): {e}")
        return None
