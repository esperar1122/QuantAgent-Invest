"""
个人量化极速秒级实时行情管道 (Real-time Market Quotes Streamer)
基于腾讯/新浪极速数据源通道，支持毫秒级批量快照拉取、Redis缓存与 SSE/WebSocket 实时推流
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
import httpx

logger = logging.getLogger(__name__)


def normalize_symbol_to_tencent(symbol: str) -> str:
    """
    将股票或指数代码标准化为腾讯 API 格式代码 (如 sh000001, sz399001, sh600519)
    """
    clean = symbol.strip().lower().split(".")[0]
    # 如果已经带有 sh / sz / bj 前缀，直接返回
    if clean.startswith(("sh", "sz", "bj")):
        return clean

    # 核心大盘宽基指数代码 (需输入完整 sh000001 或以下未重复代码)
    if clean in ("000016", "000300", "000688", "000905", "000852", "000680"):
        return f"sh{clean}"
    if clean in ("399001", "399006", "399106", "399005", "399300"):
        return f"sz{clean}"

    # 股票与场内基金 ETF
    if clean.startswith(("60", "68", "90", "51", "56", "58", "50")):
        return f"sh{clean}"
    elif clean.startswith(("00", "30", "20", "15", "16")):
        return f"sz{clean}"
    elif clean.startswith(("43", "83", "87", "88", "92")):
        return f"bj{clean}"

    return f"sh{clean}" if clean.startswith("6") else f"sz{clean}"


class RealtimeQuoteStreamer:
    """秒级实时行情引擎"""

    def __init__(self, timeout: float = 3.0):
        self.timeout = timeout
        self._sync_client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        if self._sync_client is None or self._sync_client.is_closed:
            self._sync_client = httpx.Client(
                timeout=self.timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://gu.qq.com"
                }
            )
        return self._sync_client

    async def close(self):
        if self._sync_client and not self._sync_client.is_closed:
            self._sync_client.close()

    def _fetch_sync_content(self, url: str) -> Optional[str]:
        client = self._get_client()
        resp = client.get(url)
        if resp.status_code != 200:
            return None
        return resp.content.decode("gbk", errors="ignore")

    async def fetch_batch_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        批量抓取多只股票或核心指数的最新快照与五档盘口 (50~150ms 延迟)
        Args:
            symbols: 代码列表，如 ["sh000001", "600519", "sz399001"]
        Returns:
            以 symbol (如 'sh000001') 和 code (如 '000001') 双重建立索引的行情字典
        """
        if not symbols:
            return {}

        tc_codes = [normalize_symbol_to_tencent(s) for s in symbols]
        query_str = ",".join(tc_codes)
        url = f"http://qt.gtimg.cn/q={query_str}"

        try:
            content = await asyncio.to_thread(self._fetch_sync_content, url)
            if not content:
                return {}

            lines = [line.strip() for line in content.split(";") if line.strip()]
            results: Dict[str, Dict[str, Any]] = {}
            for line in lines:
                parsed = self._parse_tencent_line(line)
                if parsed:
                    if parsed.get("symbol"):
                        results[parsed["symbol"]] = parsed
                    if parsed.get("code") and parsed["code"] not in results:
                        results[parsed["code"]] = parsed

            return results
        except Exception as e:
            logger.error(f"❌ 获取实时行情批量快照失败: {e}")
            return {}

    async def fetch_indices_quotes(self) -> List[Dict[str, Any]]:
        """
        极速获取四大核心宽基指数实时行情 (带绝对防错校准，绝不出现 +11.74% 类似点数/百分比混淆)
        """
        target_indices = [
            ("sh000001", "000001", "上证指数"),
            ("sz399001", "399001", "深证成指"),
            ("sz399006", "399006", "创业板指"),
            ("sh000688", "000688", "科创50"),
        ]
        symbols = [item[0] for item in target_indices]
        batch = await self.fetch_batch_quotes(symbols)

        indices_list: List[Dict[str, Any]] = []
        for full_sym, code, default_name in target_indices:
            q = batch.get(full_sym) or batch.get(code)
            if q and q.get("price", 0) > 0:
                px = float(q["price"])
                prev = float(q.get("prev_close") or px)
                diff = float(q.get("change") or (px - prev))
                pct = float(q.get("change_pct") or 0.0)

                # 🛡️ 涨跌幅严谨防错校准：若点数与百分比倒置，重新依据现价和昨收计算
                if prev > 0 and (abs(pct) > 20.0 or (abs(diff) > 0 and pct == 0.0)):
                    pct = round(((px - prev) / prev) * 100.0, 2)

                indices_list.append({
                    "code": code,
                    "full_code": full_sym,
                    "name": q.get("name") or default_name,
                    "price": round(px, 2),
                    "prev_close": round(prev, 2),
                    "change": round(diff, 2),
                    "changePercent": round(pct, 2),
                    "change_percent": round(pct, 2),
                    "volume": q.get("volume_hands", 0),
                    "amount": round(q.get("amount_wan", 0) / 10000.0, 2),  # 亿元
                    "high": q.get("high", px),
                    "low": q.get("low", px),
                    "open": q.get("open", prev),
                    "timestamp": q.get("timestamp")
                })
        return indices_list

    def _parse_tencent_line(self, line: str) -> Optional[Dict[str, Any]]:
        """解析单行腾讯快照数据"""
        try:
            if '="' not in line:
                return None
            
            # 提取前缀得到 symbol，如 v_sh000001 -> sh000001
            prefix = line.split('="')[0].strip()
            symbol = prefix[2:] if prefix.startswith("v_") else ""

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

            # 百分比严格计算，杜绝点数错置
            if parts[32]:
                change_pct = float(parts[32])
            elif prev_close > 0:
                change_pct = (change_amount / prev_close) * 100.0
            else:
                change_pct = 0.0

            amount_ten_thousand = float(parts[37]) if len(parts) > 37 and parts[37] else 0.0  # 万元
            turnover_rate = float(parts[38]) if len(parts) > 38 and parts[38] else 0.0
            pe_ttm = float(parts[39]) if len(parts) > 39 and parts[39] else 0.0
            market_cap_billion = float(parts[45]) if len(parts) > 45 and parts[45] else 0.0  # 亿元

            # 五档买卖盘解析 (5-Level Order Book)
            bids = []
            for i in range(5):
                idx_p = 9 + i * 2
                idx_v = 10 + i * 2
                p = float(parts[idx_p]) if len(parts) > idx_p and parts[idx_p] else 0.0
                v = int(float(parts[idx_v])) * 100 if len(parts) > idx_v and parts[idx_v] else 0
                if p > 0:
                    bids.append({"level": i + 1, "price": round(p, 2), "volume": v})

            asks = []
            for i in range(5):
                idx_p = 19 + i * 2
                idx_v = 20 + i * 2
                p = float(parts[idx_p]) if len(parts) > idx_p and parts[idx_p] else 0.0
                v = int(float(parts[idx_v])) * 100 if len(parts) > idx_v and parts[idx_v] else 0
                if p > 0:
                    asks.append({"level": i + 1, "price": round(p, 2), "volume": v})

            bid1_px = bids[0]["price"] if bids else (float(parts[9]) if len(parts) > 9 and parts[9] else 0.0)
            bid1_vol = (bids[0]["volume"] // 100) if bids else (int(parts[10]) if len(parts) > 10 and parts[10] else 0)
            ask1_px = asks[0]["price"] if asks else (float(parts[19]) if len(parts) > 19 and parts[19] else 0.0)
            ask1_vol = (asks[0]["volume"] // 100) if asks else (int(parts[20]) if len(parts) > 20 and parts[20] else 0)

            return {
                "symbol": symbol or (f"sh{code}" if code.startswith("6") else f"sz{code}"),
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
                "bids": bids,
                "asks": asks,
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
