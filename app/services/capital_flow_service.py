"""
资金流向与北向资金持股分析服务 (Capital Flow & Northbound Holding Service)
数据源设计：
1. 个股大单/超大单/中单/小单日度及多日资金流：新浪财经 MoneyFlow 官方开放接口 (高可用、毫秒级响应、包含2026最新收盘日数据)
2. 北向资金 (沪深港通) 个股持股画像：东方财富数据中心 (RPT_MUTUAL_HOLDSTOCKNORTH_STA & RPT_MUTUAL_HOLDSTOCKNDATE_STA)
"""

import logging
import asyncio
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://finance.sina.com.cn/"
}

EASTMONEY_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://data.eastmoney.com/"
}


class CapitalFlowService:
    """资金流向与北向持股数据服务"""

    @staticmethod
    def _normalize_code(code: str) -> tuple[str, str]:
        """标准化代码格式 -> (纯6位代码, 带市场前缀代码)"""
        c = str(code).strip().lower().replace("sh", "").replace("sz", "").replace("bj", "")
        if c.startswith(("6", "9", "5")):
            prefix = f"sh{c}"
        elif c.startswith(("8", "4", "920")):
            prefix = f"bj{c}"
        else:
            prefix = f"sz{c}"
        return c, prefix

    @classmethod
    def fetch_capital_flow(cls, code: str, days: int = 15) -> Dict[str, Any]:
        """
        拉取个股近 N 个交易日的大单、中单、小单及主力资金流向
        """
        c6, sym = cls._normalize_code(code)
        url = f"http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/MoneyFlow.ssl_qsfx_lscjfb?page=1&num={days}&sort=opendate&asc=0&daima={sym}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=6)
            if resp.status_code != 200:
                logger.warning(f"新浪资金流接口返回状态异常: {resp.status_code}")
                return {"items": [], "summary": {}}
            
            raw_items = resp.json()
            if not isinstance(raw_items, list) or not raw_items:
                return {"items": [], "summary": {}}

            items: List[Dict[str, Any]] = []
            for r in raw_items:
                try:
                    date_str = str(r.get("opendate") or "")
                    close_px = float(r.get("trade") or 0.0)
                    chg_pct = round(float(r.get("changeratio") or 0.0) * 100, 2)
                    turnover = float(r.get("turnover") or 0.0)

                    # 资金流向（单位折算为万元）
                    net_main_wan = round(float(r.get("netamount") or 0.0) / 10000.0, 2)
                    ratio_main_pct = round(float(r.get("ratioamount") or 0.0) * 100, 2)

                    # 分级成交额与净流入（单位万元）
                    super_large_in_wan = round(float(r.get("r0") or 0.0) / 10000.0, 2)
                    super_large_net_wan = round(float(r.get("r0_net") or 0.0) / 10000.0, 2)

                    large_in_wan = round(float(r.get("r1") or 0.0) / 10000.0, 2)
                    large_net_wan = round(float(r.get("r1_net") or 0.0) / 10000.0, 2)

                    mid_in_wan = round(float(r.get("r2") or 0.0) / 10000.0, 2)
                    mid_net_wan = round(float(r.get("r2_net") or 0.0) / 10000.0, 2)

                    small_in_wan = round(float(r.get("r3") or 0.0) / 10000.0, 2)
                    small_net_wan = round(float(r.get("r3_net") or 0.0) / 10000.0, 2)

                    items.append({
                        "date": date_str,
                        "close": close_px,
                        "pct_chg": chg_pct,
                        "turnover": turnover,
                        "main_net_wan": net_main_wan,
                        "main_ratio_pct": ratio_main_pct,
                        "super_large_in_wan": super_large_in_wan,
                        "super_large_net_wan": super_large_net_wan,
                        "large_in_wan": large_in_wan,
                        "large_net_wan": large_net_wan,
                        "mid_in_wan": mid_in_wan,
                        "mid_net_wan": mid_net_wan,
                        "small_in_wan": small_in_wan,
                        "small_net_wan": small_net_wan,
                    })
                except Exception as ex:
                    logger.debug(f"解析单日资金流异常: {ex}")
                    continue

            # 汇总多日动向
            summary = cls._compute_flow_summary(items)
            return {"items": items, "summary": summary}
        except Exception as e:
            logger.error(f"拉取标的 {code} 资金流数据失败: {e}")
            return {"items": [], "summary": {}}

    @classmethod
    def _compute_flow_summary(cls, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算近 1日、3日、5日的主力资金综合研判画像"""
        if not items:
            return {}

        latest = items[0]
        main_1d = latest["main_net_wan"]

        # 近 3 日与 5 日主力净流入累计
        items_3d = items[:min(3, len(items))]
        main_3d = round(sum(it["main_net_wan"] for it in items_3d), 2)

        items_5d = items[:min(5, len(items))]
        main_5d = round(sum(it["main_net_wan"] for it in items_5d), 2)

        # 超大单 + 大单合计算为主力净额
        super_5d = round(sum(it["super_large_net_wan"] for it in items_5d), 2)
        large_5d = round(sum(it["large_net_wan"] for it in items_5d), 2)
        retail_5d = round(sum(it["small_net_wan"] for it in items_5d), 2)

        # 主力博弈定性
        if main_1d >= 5000 and latest["main_ratio_pct"] >= 5.0:
            posture = "🔥 主力强势爆量抢筹"
            posture_tag = "success"
        elif main_1d > 0 and main_5d > 0:
            posture = "📈 主力资金持续净增配"
            posture_tag = "primary"
        elif main_1d < -5000 and latest["main_ratio_pct"] <= -5.0:
            posture = "⚠️ 主力资金大额减仓出逃"
            posture_tag = "danger"
        elif main_1d < 0 and main_5d < 0:
            posture = "📉 机构资金净流出承压"
            posture_tag = "warning"
        else:
            posture = "⚖️ 机构散户多空拉锯胶着"
            posture_tag = "info"

        return {
            "latest_date": latest["date"],
            "main_1d_wan": main_1d,
            "main_3d_wan": main_3d,
            "main_5d_wan": main_5d,
            "super_5d_wan": super_5d,
            "large_5d_wan": large_5d,
            "retail_5d_wan": retail_5d,
            "main_ratio_pct": latest["main_ratio_pct"],
            "posture": posture,
            "posture_tag": posture_tag
        }

    @classmethod
    def fetch_northbound_holding(cls, code: str) -> Dict[str, Any]:
        """
        获取标的北向资金 (陆股通 / 外资) 持股画像
        注：依据2024年8月19日交易所信披改革，个股全量明细调整为季度末披露
        """
        c6, _ = cls._normalize_code(code)
        url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
        
        # 1. 尝试查询最新季度末官方权威持股报告
        params_quarterly = {
            "reportName": "RPT_MUTUAL_HOLDSTOCKNORTH_STA",
            "columns": "TRADE_DATE,CLOSE_PRICE,HOLD_SHARES,HOLD_MARKET_CAP,HOLD_SHARES_RATIO,A_SHARES_RATIO,FREE_SHARES_RATIO",
            "filter": f'(SECURITY_CODE="{c6}")',
            "pageNumber": 1,
            "pageSize": 4,
            "sortTypes": -1,
            "sortColumns": "TRADE_DATE",
            "source": "WEB",
            "client": "WEB"
        }
        
        try:
            r = requests.get(url, params=params_quarterly, headers=EASTMONEY_HEADERS, timeout=5)
            data_json = r.json()
            raw_list = data_json.get("result", {}).get("data", [])
            
            quarterly_items = []
            if raw_list and isinstance(raw_list, list):
                for row in raw_list:
                    quarterly_items.append({
                        "report_date": str(row.get("TRADE_DATE") or "")[:10],
                        "hold_shares_wan": round((row.get("HOLD_SHARES") or 0.0) / 10000.0, 2),
                        "hold_market_cap_yi": round((row.get("HOLD_MARKET_CAP") or 0.0) / 100000000.0, 2),
                        "hold_ratio_pct": round(float(row.get("HOLD_SHARES_RATIO") or row.get("A_SHARES_RATIO") or 0.0), 2),
                        "free_shares_ratio_pct": round(float(row.get("FREE_SHARES_RATIO") or 0.0), 2),
                    })

            # 2. 检查是否有持股画像
            latest_quarter = quarterly_items[0] if quarterly_items else None
            is_heavy_north = bool(latest_quarter and latest_quarter["hold_ratio_pct"] >= 3.0)

            return {
                "code": c6,
                "has_northbound": bool(latest_quarter and latest_quarter["hold_shares_wan"] > 0),
                "is_heavy_north": is_heavy_north,
                "latest_holding": latest_quarter,
                "history_quarters": quarterly_items,
                "disclosure_notice": "注：根据2024年8月19日沪深港通监管新规，个股持股明细调整为每季度盘后权威披露；日内实时净买卖额已依规停更。"
            }
        except Exception as e:
            logger.error(f"拉取标的 {code} 北向持股失败: {e}")
            return {
                "code": c6,
                "has_northbound": False,
                "is_heavy_north": False,
                "latest_holding": None,
                "history_quarters": [],
                "disclosure_notice": "北向资金数据暂未披露或该标的未纳入陆股通可投资标的范围"
            }

    @classmethod
    async def get_combined_analysis(cls, code: str) -> Dict[str, Any]:
        """异步聚合个股资金流向与北向持股完整数据"""
        loop = asyncio.get_running_loop()
        flow_task = loop.run_in_executor(None, cls.fetch_capital_flow, code, 15)
        north_task = loop.run_in_executor(None, cls.fetch_northbound_holding, code)
        
        flow_data, north_data = await asyncio.gather(flow_task, north_task)
        return {
            "code": code,
            "flow": flow_data,
            "northbound": north_data,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
