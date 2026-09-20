#!/usr/bin/env python3
"""
A股全市场核心财务指标（ROE、净利润增长率、营收增长率、毛利率、股息率）同步脚本
基于东方财富高并发数据接口，秒级拉取全市场上市公司最新财务数据并更新至 stock_basic_info
"""
import sys
import os
import time
import logging
from typing import Dict, Any, List, Optional
import requests
from pymongo import UpdateOne

# 确保项目根目录在 sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.database import get_mongo_db_sync

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("sync_financial_indicators")


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


def fetch_all_em_financials(report_date: str = "2024-09-30") -> Dict[str, Dict[str, Any]]:
    """
    分页拉取东方财富全市场上市公司财务报表
    reportName: RPT_LICO_FN_CPD
    """
    url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    page_size = 500
    page_number = 1
    stock_data_map: Dict[str, Dict[str, Any]] = {}

    logger.info(f"🚀 开始抓取 {report_date} 全市场上市公司业绩报表...")
    start_time = time.time()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    while True:
        params = {
            "sortColumns": "UPDATE_DATE,SECURITY_CODE",
            "sortTypes": "-1,-1",
            "pageSize": str(page_size),
            "pageNumber": str(page_number),
            "reportName": "RPT_LICO_FN_CPD",
            "columns": "ALL",
            "filter": f"(REPORTDATE='{report_date}')"
        }

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=12)
            if resp.status_code != 200:
                logger.warning(f"⚠️ 第 {page_number} 页 HTTP {resp.status_code}，重试中...")
                time.sleep(1)
                continue

            res_json = resp.json()
            result = res_json.get("result")
            if not result or not result.get("data"):
                break

            total_pages = result.get("pages", 0)
            data_list = result.get("data", [])

            for item in data_list:
                secu_code = str(item.get("SECURITY_CODE", "")).strip()
                if not secu_code or len(secu_code) != 6:
                    continue

                roe = safe_float(item.get("WEIGHTAVG_ROE"))
                rev_growth = safe_float(item.get("YSTZ"))
                net_growth = safe_float(item.get("SJLTZ"))
                gross_margin = safe_float(item.get("XSMLL"))
                div_yield = safe_float(item.get("ZXGXL"))

                # 仅在非重复或更新更完整的记录时存储
                stock_data_map[secu_code] = {
                    "roe": roe,
                    "revenue_growth": rev_growth,
                    "net_profit_growth": net_growth,
                    "gross_margin": gross_margin,
                    "dividend_yield": div_yield
                }

            logger.info(f"  已获取第 {page_number}/{total_pages} 页，当前累积标的数: {len(stock_data_map)}")

            if page_number >= total_pages:
                break
            page_number += 1
            time.sleep(0.3)  # 温和频控

        except Exception as e:
            logger.error(f"❌ 获取第 {page_number} 页异常: {e}")
            time.sleep(1)
            # 连续重试机制（如果页码不变多试两次）
            break

    elapsed = time.time() - start_time
    logger.info(f"✅ 全市场财务数据拉取完成，用时 {elapsed:.2f} 秒，共提取 {len(stock_data_map)} 家上市公司指标")
    return stock_data_map


def sync_to_mongodb(stock_data_map: Dict[str, Dict[str, Any]]):
    """批量同步至 MongoDB stock_basic_info 集合"""
    if not stock_data_map:
        logger.warning("⚠️ 没有待同步的财务数据")
        return

    db = get_mongo_db_sync()
    collection = db["stock_basic_info"]

    logger.info("📦 正在生成批量更新指令...")
    bulk_ops = []
    for code, data in stock_data_map.items():
        # 仅更新非 None 字段或完整设置
        update_fields = {}
        for k, v in data.items():
            if v is not None:
                update_fields[k] = v

        if update_fields:
            bulk_ops.append(
                UpdateOne(
                    {"code": code},
                    {"$set": update_fields}
                )
            )

    if not bulk_ops:
        logger.info("没有需要更新的记录")
        return

    logger.info(f"🔄 正在执行 MongoDB 批量写入 (总计 {len(bulk_ops)} 条)...")
    batch_size = 1000
    matched_count = 0
    modified_count = 0

    for i in range(0, len(bulk_ops), batch_size):
        chunk = bulk_ops[i: i + batch_size]
        res = collection.bulk_write(chunk, ordered=False)
        matched_count += res.matched_count
        modified_count += res.modified_count

    logger.info(f"🎉 批量更新完成！匹配到标的数: {matched_count}, 实际更新数: {modified_count}")

    # 统计更新覆盖情况
    active_filter = {
        "name": {"$not": {"$regex": r"退|^PT"}},
        "status": {"$nin": ["0", "delisted", "D", "退市"]}
    }
    total_active = collection.count_documents(active_filter)
    with_roe = collection.count_documents({**active_filter, "roe": {"$ne": None}})
    with_npg = collection.count_documents({**active_filter, "net_profit_growth": {"$ne": None}})
    with_rev = collection.count_documents({**active_filter, "revenue_growth": {"$ne": None}})
    with_gm = collection.count_documents({**active_filter, "gross_margin": {"$ne": None}})

    logger.info(f"📊 数据库指标覆盖度统计 (正常在市股票总数: {total_active}):")
    logger.info(f"  - ROE 覆盖: {with_roe} / {total_active} ({with_roe / total_active * 100:.1f}%)")
    logger.info(f"  - 净利润增长率 覆盖: {with_npg} / {total_active} ({with_npg / total_active * 100:.1f}%)")
    logger.info(f"  - 营收增长率 覆盖: {with_rev} / {total_active} ({with_rev / total_active * 100:.1f}%)")
    logger.info(f"  - 销售毛利率 覆盖: {with_gm} / {total_active} ({with_gm / total_active * 100:.1f}%)")


if __name__ == "__main__":
    report_period = sys.argv[1] if len(sys.argv) > 1 else "2024-09-30"
    data_map = fetch_all_em_financials(report_period)
    sync_to_mongodb(data_map)
