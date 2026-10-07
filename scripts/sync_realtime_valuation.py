#!/usr/bin/env python3
"""
A股全市场估值指标（PE-TTM、PB-MRQ、总市值、流通市值、实时盘口）极速同步脚本
基于腾讯极速行情高并发接口（免Token、0成本、100ms延迟），切片批量拉取全市场在市股票估值并写入 market_quotes 与 stock_basic_info
"""
import sys
import os
import time
import logging
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional
from pymongo import UpdateOne

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.database import get_mongo_db_sync

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("sync_realtime_valuation")


def to_tencent_symbol(code: str) -> str:
    clean = str(code).strip().lower().replace("sh", "").replace("sz", "").replace("bj", "")
    if clean.startswith(("60", "68", "90", "50", "51", "56", "58")):
        return f"sh{clean}"
    elif clean.startswith(("00", "30", "20", "15", "16", "39")):
        return f"sz{clean}"
    elif clean.startswith(("8", "4", "92")):
        return f"bj{clean}"
    return f"sz{clean}" if clean.startswith("0") else f"sh{clean}"


def safe_float(val: Any) -> Optional[float]:
    if val is None or val == "" or str(val).lower() in ["none", "nan", "null"]:
        return None
    try:
        f = float(val)
        import math
        if math.isnan(f) or math.isinf(f):
            return None
        return round(f, 4)
    except (ValueError, TypeError):
        return None


def fetch_tencent_batch(batch_symbols: List[str]) -> List[Dict[str, Any]]:
    """拉取一个批次 (最多80只) 的腾讯极速行情数据"""
    tx_symbols = [to_tencent_symbol(s) for s in batch_symbols]
    url = "http://qt.gtimg.cn/q=" + ",".join(tx_symbols)
    results = []

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            data = resp.read().decode("gbk", errors="ignore")

        lines = data.strip().split(";")
        for line in lines:
            if not line.strip():
                continue
            parts = line.strip().split("~")
            if len(parts) < 47:
                continue

            code_clean = parts[2].strip()
            name = parts[1].strip()
            price = safe_float(parts[3])
            prev_close = safe_float(parts[4])
            open_px = safe_float(parts[5])
            volume = safe_float(parts[6])
            amount = safe_float(parts[37]) * 10000.0 if parts[37] else 0.0
            pct_chg = safe_float(parts[32])
            high_px = safe_float(parts[33])
            low_px = safe_float(parts[34])
            turnover = safe_float(parts[38])
            pe_val = safe_float(parts[39])
            pb_val = safe_float(parts[46])
            mv_val = safe_float(parts[45])  # 总市值（亿元）
            circ_val = safe_float(parts[44]) if len(parts) > 44 else None  # 流通市值（亿元）

            t_str = parts[30] if len(parts) > 30 else ""
            trade_date = f"{t_str[:4]}-{t_str[4:6]}-{t_str[6:8]}" if len(t_str) >= 8 else ""

            results.append({
                "code": code_clean,
                "name": name,
                "price": price,
                "close": price,
                "prev_close": prev_close,
                "open": open_px,
                "high": high_px,
                "low": low_px,
                "volume": volume,
                "amount": amount,
                "pct_chg": pct_chg,
                "turnover_rate": turnover,
                "pe": pe_val,
                "pb": pb_val,
                "total_mv": mv_val,
                "circ_mv": circ_val,
                "trade_date": trade_date
            })
    except Exception as e:
        logger.warning(f"⚠️ 拉取批次行情失败: {e}")

    return results


def sync_all_valuation():
    db = get_mongo_db_sync()
    info_col = db["stock_basic_info"]
    quote_col = db["market_quotes"]

    # 获取全市场在市股票代码
    cursor = info_col.find(
        {"status": {"$nin": ["0", "delisted", "D", "退市"]}},
        {"code": 1, "_id": 0}
    )
    all_codes = [doc["code"] for doc in cursor if doc.get("code")]
    total_count = len(all_codes)
    logger.info(f"🚀 开始全市场估值与行情同步，共检索到 {total_count} 只标的...")

    start_time = time.time()
    batch_size = 70
    batches = [all_codes[i:i + batch_size] for i in range(0, total_count, batch_size)]

    all_quote_items = []
    # 8 并发拉取
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_tencent_batch, b): b for b in batches}
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                all_quote_items.extend(res)

    fetch_elapsed = time.time() - start_time
    logger.info(f"✅ 行情与估值抓取完成，耗时 {fetch_elapsed:.2f} 秒，共获取 {len(all_quote_items)} 只标的数据")

    # 批量写入 MongoDB (同时更新 market_quotes 与 stock_basic_info)
    logger.info("📦 正在生成批量更新指令...")
    quote_ops = []
    info_ops = []

    for item in all_quote_items:
        code = item["code"]
        quote_doc = {**item}

        quote_ops.append(
            UpdateOne(
                {"code": code},
                {"$set": quote_doc},
                upsert=True
            )
        )

        # 同时向 stock_basic_info 注入 pe, pb, total_mv, circ_mv
        info_update = {}
        if item.get("pe") is not None:
            info_update["pe"] = item["pe"]
        if item.get("pb") is not None:
            info_update["pb"] = item["pb"]
        if item.get("total_mv") is not None:
            info_update["total_mv"] = item["total_mv"]
        if item.get("circ_mv") is not None:
            info_update["circ_mv"] = item["circ_mv"]

        if info_update:
            info_ops.append(
                UpdateOne(
                    {"code": code},
                    {"$set": info_update}
                )
            )

    if quote_ops:
        logger.info(f"🔄 正在批量写入 market_quotes ({len(quote_ops)} 条)...")
        for i in range(0, len(quote_ops), 1000):
            quote_col.bulk_write(quote_ops[i:i + 1000], ordered=False)

    if info_ops:
        logger.info(f"🔄 正在批量更新 stock_basic_info 估值字段 ({len(info_ops)} 条)...")
        for i in range(0, len(info_ops), 1000):
            info_col.bulk_write(info_ops[i:i + 1000], ordered=False)

    total_elapsed = time.time() - start_time
    logger.info(f"🎉 全市场估值同步成功！总耗时: {total_elapsed:.2f} 秒")


if __name__ == "__main__":
    sync_all_valuation()
