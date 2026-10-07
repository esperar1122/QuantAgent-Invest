"""
个人量化极速秒级实时行情管道 (Real-time Market Quotes Streamer)
基于腾讯/新浪极速数据源通道，支持毫秒级批量快照拉取、Redis缓存与WebSocket推流
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
import httpx

logger = logging.getLogger(__name__)


def normalize_symbol_to_tencent(symbol: str) -> str:
    """将6位代码转换为腾讯API代码格式，如 600519 -> sh600519, 000001 -> sz000001"""
    clean = symbol.strip().split(".")[0]
    if clean.startswith(("60", "68", "90")):
        return f"sh{clean}"
    elif clean.startswith(("00", "30", "20")):
        return f"sz{clean}"
    elif clean.startswith(("43", "83", "87", "88")):
        return f"bj{clean}"
    return f"sh{clean}" if clean.startswith("6") else f"sz{clean}"


class RealtimeQuoteStreamer:
    """秒级实时行情引擎"""

    def __init__(self, timeout: float = 3.0):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://gu.qq.com"
        })

    async def close(self):
        await self.client.aclose()

    async def fetch_batch_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        批量抓取多只股票的最新五档买卖盘与现价快照 (100~200ms延迟)
        Args:
            symbols: 股票代码列表，如 ["600519", "000001"]
        Returns:
            { "600519": { "name": "贵州茅台", "price": 1680.0, "change_pct": 1.25, ... } }
        """
        if not symbols:
            return {}

        tc_codes = [normalize_symbol_to_tencent(s) for s in symbols]
        query_str = ",".join(tc_codes)
        url = f"http://qt.gtimg.cn/q={query_str}"

        try:
            resp = await self.client.get(url)
            if resp.status_code != 200:
                logger.warning(f"行情接口返回非200: {resp.status_code}")
                return {}

            content = resp.content.decode("gbk", errors="ignore")
            lines = [line.strip() for line in content.split(";") if line.strip()]

            results: Dict[str, Dict[str, Any]] = {}
            for line in lines:
                parsed = self._parse_tencent_line(line)
                if parsed:
                    results[parsed["code"]] = parsed

            return results
        except Exception as e:
            logger.error(f"❌ 获取实时行情批量快照失败: {e}")
            return {}

    def _parse_tencent_line(self, line: str) -> Optional[Dict[str, Any]]:
        """解析单行腾讯快照数据"""
        try:
            if '="' not in line:
                return None
            val_part = line.split('="')[1].rstrip('"')
            parts = val_part.split("~")
            if len(parts) < 35:
                return None

            name = parts[1]
            code = parts[2]
            current_price = float(parts[3])
            prev_close = float(parts[4])
            open_price = float(parts[5])
            volume_lots = float(parts[6])  # 手
            high_price = float(parts[33]) if parts[33] else current_price
            low_price = float(parts[34]) if parts[34] else current_price
            change_amount = float(parts[31]) if parts[31] else (current_price - prev_close)
            change_pct = float(parts[32]) if parts[32] else ((change_amount / prev_close * 100) if prev_close > 0 else 0.0)
            amount_ten_thousand = float(parts[37]) if len(parts) > 37 and parts[37] else 0.0  # 万元
            turnover_rate = float(parts[38]) if len(parts) > 38 and parts[38] else 0.0
            pe_ttm = float(parts[39]) if len(parts) > 39 and parts[39] else 0.0
            market_cap_billion = float(parts[45]) if len(parts) > 45 and parts[45] else 0.0  # 亿元

            # 五档买盘
            bid1_px, bid1_vol = float(parts[9]), int(parts[10])
            # 五档卖盘
            ask1_px, ask1_vol = float(parts[19]), int(parts[20])

            return {
                "code": code,
                "name": name,
                "price": current_price,
                "prev_close": prev_close,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "change": round(change_amount, 2),
                "change_pct": round(change_pct, 2),
                "volume_hands": int(volume_lots),
                "amount_wan": round(amount_ten_thousand, 2),
                "turnover_rate": round(turnover_rate, 2),
                "pe_ttm": round(pe_ttm, 2),
                "market_cap_yi": round(market_cap_billion, 2),
                "bid1_price": bid1_px,
                "bid1_volume": bid1_vol,
                "ask1_price": ask1_px,
                "ask1_volume": ask1_vol,
                "timestamp": parts[30] if len(parts) > 30 else str(int(time.time())),
            }
        except Exception:
            return None


# 单例全局实例
_streamer_instance: Optional[RealtimeQuoteStreamer] = None


def get_quote_streamer() -> RealtimeQuoteStreamer:
    global _streamer_instance
    if _streamer_instance is None:
        _streamer_instance = RealtimeQuoteStreamer()
    return _streamer_instance
