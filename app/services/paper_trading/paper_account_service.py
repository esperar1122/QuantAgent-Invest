"""
虚拟模拟盘交易账户管理服务 (Paper Trading Engine)
提供完整的虚拟资金、持仓、T+1交易撮合、五档盘口深度穿透、挂单排队撮合、流动性冲击限制与历史净值跟踪
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.quotes.realtime_streamer import get_quote_streamer
from app.services.notifier.wechat_notifier import wechat_notifier

logger = logging.getLogger(__name__)


class PaperAccountService:
    """虚拟仿真账户服务（支持五档盘口撮合、排队挂单与流动性风控）"""

    # 券商佣金与交易摩擦费率（用户专享: 万0.876，免5最低0.5元起收；ETF免印花税）
    DEFAULT_COMMISSION_RATE = 0.0000876  # 佣金万0.876
    DEFAULT_MIN_COMMISSION = 0.5         # 免5，最低0.5元起收
    DEFAULT_STAMP_DUTY_RATE = 0.0005     # 普通股票卖出印花税万5 (ETF免征)
    DEFAULT_TRANSFER_FEE_RATE = 0.00001  # 过户费万0.1

    @staticmethod
    def is_etf(symbol: str) -> bool:
        s = (symbol or "").lower().replace("sh", "").replace("sz", "").replace("bj", "")
        return (
            s.startswith("51") or
            s.startswith("56") or
            s.startswith("58") or
            s.startswith("50") or
            s.startswith("15") or
            s.startswith("16")
        )

    @classmethod
    def calc_fees(cls, symbol: str, gross_amount: float, action: str) -> tuple[float, float, float]:
        """计算佣金、印花税、过户费 (返回 commission, stamp_duty, transfer_fee)"""
        commission = max(cls.DEFAULT_MIN_COMMISSION, round(gross_amount * cls.DEFAULT_COMMISSION_RATE, 2))
        transfer_fee = round(gross_amount * cls.DEFAULT_TRANSFER_FEE_RATE, 2)
        if action == "SELL":
            stamp_duty = 0.0 if cls.is_etf(symbol) else round(gross_amount * cls.DEFAULT_STAMP_DUTY_RATE, 2)
        else:
            stamp_duty = 0.0
        return commission, stamp_duty, transfer_fee

    def __init__(self):
        # 内存缓存（配合 MongoDB 持久化）
        self._memory_accounts: Dict[str, Dict[str, Any]] = {}

    def _get_collection(self):
        """获取 MongoDB 集合"""
        try:
            from app.core.database import get_database
            db = get_database()
            if db is not None:
                return db.paper_accounts
            return None
        except Exception:
            return None

    async def get_or_create_account(self, account_id: str = "default", initial_cash: float = 100000.0) -> Dict[str, Any]:
        """获取或创建模拟账户"""
        col = self._get_collection()
        if col is not None:
            try:
                acc = await col.find_one({"account_id": account_id})
                if acc:
                    acc.pop("_id", None)
                    acc.setdefault("frozen_cash", 0.0)
                    acc.setdefault("pending_orders", [])
                    return acc
            except Exception as e:
                logger.warning(f"从MongoDB查询模拟账户异常: {e}")

        # 若数据库没有，则创建新账户
        if account_id in self._memory_accounts:
            acc = self._memory_accounts[account_id]
            acc.setdefault("frozen_cash", 0.0)
            acc.setdefault("pending_orders", [])
            return acc

        new_acc = {
            "account_id": account_id,
            "initial_cash": float(initial_cash),
            "cash": float(initial_cash),
            "frozen_cash": 0.0,
            "positions": {},  # { "600519": { "symbol": "600519", "name": "贵州茅台", "shares": 200, "avail_shares": 200, "avg_cost": 1600.0, ... } }
            "orders": [],
            "pending_orders": [],
            "equity_history": [
                {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "total_equity": float(initial_cash),
                    "cash": float(initial_cash),
                    "market_value": 0.0,
                    "pnl": 0.0
                }
            ],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        if col is not None:
            try:
                await col.insert_one(new_acc.copy())
            except Exception as e:
                logger.warning(f"模拟账户持久化失败: {e}")

        self._memory_accounts[account_id] = new_acc
        return new_acc

    def _match_with_depth(
        self,
        action: str,
        shares: int,
        limit_price: Optional[float],
        quote: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        基于真实五档盘口深度 (5-Level Order Book) 逐档穿透撮合，计算加权均价与冲击滑点
        """
        cur_px = float(quote.get("price") or 0.0)
        if cur_px <= 0:
            cur_px = float(limit_price or 10.0)

        bids = quote.get("bids") or []
        asks = quote.get("asks") or []

        # 若盘口暂无五档数据（如盘后或离线单测），基于当前价合成高保真五档微观盘口
        if not bids or not asks:
            step = round(max(0.01, cur_px * 0.001), 2)
            bids = [
                {"level": i + 1, "price": round(cur_px - (i * step), 2), "volume": (10 + i * 5) * 100}
                for i in range(5)
            ]
            asks = [
                {"level": i + 1, "price": round(cur_px + (i * step), 2), "volume": (10 + i * 5) * 100}
                for i in range(5)
            ]

        ladder = asks if action == "BUY" else bids
        remaining = shares
        filled_shares = 0
        filled_amount = 0.0
        fills_info = []

        for level in ladder:
            l_px = float(level["price"])
            l_vol = int(level["volume"])
            if l_vol <= 0 or l_px <= 0:
                continue

            # 限价单价格拦截
            if limit_price is not None and limit_price > 0:
                if action == "BUY" and l_px > limit_price:
                    break
                if action == "SELL" and l_px < limit_price:
                    break

            take = min(remaining, l_vol)
            filled_shares += take
            filled_amount += take * l_px
            remaining -= take
            fills_info.append(f"{'卖' if action == 'BUY' else '买'}{level.get('level', 1)}档 {take}股@¥{l_px:.2f}")

            if remaining <= 0:
                break

        # 若五档全部吃完仍有剩余委托
        if remaining > 0:
            if limit_price is not None and limit_price > 0:
                # 限价单：超过五档且后续价格劣于限价，剩余部分不予强制成交
                pass
            else:
                # 市价单：穿透五档进入深层流动性，承受市场冲击滑点 (Market Impact)
                deep_px = ladder[-1]["price"] if ladder else cur_px
                impact_ratio = min(0.03, (remaining / 10000.0) * 0.002)  # 每超1万股滑点 0.2%
                fill_px = round(deep_px * (1.0 + impact_ratio if action == "BUY" else 1.0 - impact_ratio), 3)
                filled_shares += remaining
                filled_amount += remaining * fill_px
                fills_info.append(f"深层流动性穿透(滑点{impact_ratio*100:.2f}%) {remaining}股@¥{fill_px:.2f}")
                remaining = 0

        if filled_shares <= 0:
            return {
                "status": "UNFILLED",
                "filled_shares": 0,
                "avg_price": cur_px,
                "slippage_cost": 0.0,
                "details": "盘口无符合限价条件的流动性"
            }

        avg_px = round(filled_amount / filled_shares, 3)
        slippage_cost = round(abs(avg_px - cur_px) * filled_shares, 2)

        return {
            "status": "FILLED" if remaining == 0 else "PARTIAL",
            "filled_shares": filled_shares,
            "avg_price": avg_px,
            "slippage_cost": slippage_cost,
            "details": "; ".join(fills_info)
        }

    async def execute_trade(
        self,
        account_id: str,
        symbol: str,
        name: str,
        action: str,  # "BUY" / "SELL"
        shares: int,
        price: Optional[float] = None,
        order_type: str = "AUTO",  # "AUTO" / "MARKET" / "LIMIT"
        allow_queue: bool = False,
        reason: str = "手动模拟交易"
    ) -> Dict[str, Any]:
        """
        在虚拟账户中执行模拟买入/卖出委托
        具备五档盘口深度撮合、限价排队挂单、T+1限制、涨跌停熔断与流动性冲击约束
        """
        acc = await self.get_or_create_account(account_id)
        action = action.upper()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. 获取实时行情快照
        streamer = get_quote_streamer()
        quotes = await streamer.fetch_batch_quotes([symbol])
        q = quotes.get(symbol) or {}

        # 若行情服务因离线等未返回，基于输入价格或默认值构造兜底快照
        if not q or q.get("price", 0) <= 0:
            if price is not None and price > 0:
                q = {
                    "symbol": symbol,
                    "code": symbol,
                    "name": name,
                    "price": price,
                    "prev_close": price,
                    "open": price,
                    "volume_hands": 50000,
                    "bids": [{"level": 1, "price": price, "volume": 50000}],
                    "asks": [{"level": 1, "price": price, "volume": 50000}],
                }
            else:
                raise ValueError(f"无法获取标的 {symbol} 的当前最新市价，请手动指定价格")

        name = q.get("name", name)
        cur_px = float(q.get("price") or 0.0)
        prev_close = float(q.get("prev_close") or cur_px)

        # 若调用方显式指定了仿真成交价且未开启排队模式，以指定价格构建撮合基准
        if price is not None and price > 0 and not allow_queue and order_type != "LIMIT":
            cur_px = price
            prev_close = price
            q["price"] = price
            q["prev_close"] = price
            q["bids"] = [{"level": 1, "price": price, "volume": 50000}]
            q["asks"] = [{"level": 1, "price": price, "volume": 50000}]

        # 2. 交易合规与风控硬性校验
        # 2.1 停牌检查
        vol_hands = int(q.get("volume_hands") or 0)
        open_px = float(q.get("open") or 0.0)
        if cur_px <= 0 or (vol_hands == 0 and open_px == 0 and prev_close > 0):
            raise ValueError(f"标的 {symbol} 当前处于停牌状态，禁止任何交易委托撮合")

        # 2.2 涨跌停封死检查
        code_str = symbol.replace("sh", "").replace("sz", "").replace("bj", "")
        limit_pct = 0.20 if code_str.startswith(("300", "301", "688")) else (0.30 if code_str.startswith(("4", "8", "9")) else 0.10)
        limit_up = round(prev_close * (1.0 + limit_pct), 2)
        limit_down = round(prev_close * (1.0 - limit_pct), 2)

        ask1_v = q.get("ask1_volume", 0)
        bid1_v = q.get("bid1_volume", 0)
        if action == "BUY" and cur_px >= limit_up and ask1_v == 0:
            raise ValueError(f"标的 {symbol} 已封死涨停板（¥{limit_up:.2f}），卖盘流动性耗尽，买单无法即时撮合")
        if action == "SELL" and cur_px <= limit_down and bid1_v == 0:
            raise ValueError(f"标的 {symbol} 已封死跌停板（¥{limit_down:.2f}），买盘流动性耗尽，卖单无法即时撮合")

        # 2.3 流动性冲击限制（单笔交易不超过当日成交量的 15%）
        day_vol_shares = vol_hands * 100
        if day_vol_shares >= 10000:
            max_single_allowed = max(50000, int(day_vol_shares * 0.15))
            if shares > max_single_allowed:
                raise ValueError(
                    f"单笔委托股数 ({shares}股) 超过该标的当日成交总量的 15%（单笔上限: {max_single_allowed}股），触发交易所流动性冲击熔断"
                )

        # 3. 基础股数与方向校验
        if action == "BUY":
            shares = (shares // 100) * 100
            if shares < 100:
                raise ValueError("A股买入数量至少为 100 股（1手）且必须为整百数")
        elif action == "SELL":
            pos = acc["positions"].get(symbol)
            if not pos:
                raise ValueError(f"当前未持有标的 {symbol}")
            avail = pos.get("avail_shares", 0)
            if avail < shares:
                raise ValueError(f"可用持仓不足（T+1限制）！可卖: {avail} 股，申请卖出: {shares} 股")
        else:
            raise ValueError(f"不支持的操作类型: {action}")

        # 4. 限价排队挂单逻辑判断 (Limit Queue)
        bids = q.get("bids") or []
        asks = q.get("asks") or []
        ask1_px = asks[0]["price"] if asks else cur_px
        bid1_px = bids[0]["price"] if bids else cur_px

        is_limit_order = (order_type == "LIMIT") or (price is not None and price > 0 and allow_queue)

        # 4.1 限价买单价格低于卖一价 -> 挂单排队
        if is_limit_order and action == "BUY" and price is not None and price < ask1_px:
            gross_amount = round(shares * price, 2)
            commission, _, transfer_fee = self.calc_fees(symbol, gross_amount, "BUY")
            total_needed = gross_amount + commission + transfer_fee

            if total_needed > acc["cash"]:
                raise ValueError(f"虚拟账户现金不足！需冻结 {total_needed:.2f} 元，当前可用现金 {acc['cash']:.2f} 元")

            # 冻结现金
            acc["cash"] = round(acc["cash"] - total_needed, 2)
            acc["frozen_cash"] = round(acc.get("frozen_cash", 0.0) + total_needed, 2)

            pending_order = {
                "order_id": f"ORD_{int(datetime.now().timestamp()*1000)}",
                "time": now_str,
                "trade_time": now_str,
                "symbol": symbol,
                "name": name,
                "action": "BUY",
                "order_type": "LIMIT",
                "shares": shares,
                "filled_shares": 0,
                "price": price,
                "avg_price": 0.0,
                "amount": gross_amount,
                "frozen_amount": total_needed,
                "fee": round(commission + transfer_fee, 2),
                "status": "PENDING",
                "details": f"限价买单 ¥{price:.2f} 低于当前卖一价 ¥{ask1_px:.2f}，已进入委托买盘队列等待行情回踩",
                "reason": reason
            }
            acc["pending_orders"].insert(0, pending_order)
            await self._persist_account(acc)
            return await self.get_account_summary(account_id)

        # 4.2 限价卖单价格高于买一价 -> 挂单排队
        if is_limit_order and action == "SELL" and price is not None and price > bid1_px:
            pos = acc["positions"][symbol]
            pos["avail_shares"] -= shares  # 冻结可用持仓

            pending_order = {
                "order_id": f"ORD_{int(datetime.now().timestamp()*1000)}",
                "time": now_str,
                "trade_time": now_str,
                "symbol": symbol,
                "name": name,
                "action": "SELL",
                "order_type": "LIMIT",
                "shares": shares,
                "filled_shares": 0,
                "price": price,
                "avg_price": 0.0,
                "amount": round(shares * price, 2),
                "status": "PENDING",
                "details": f"限价卖单 ¥{price:.2f} 高于当前买一价 ¥{bid1_px:.2f}，已进入委托卖盘队列等待冲高成交",
                "reason": reason
            }
            acc["pending_orders"].insert(0, pending_order)
            await self._persist_account(acc)
            return await self.get_account_summary(account_id)

        # 5. 即时盘口深度撮合 (Execute Matching with 5-Level Depth)
        # 若用户传入 price 且 allow_queue 为 False，则优先在指定限价范围内撮合
        match_res = self._match_with_depth(
            action=action,
            shares=shares,
            limit_price=price if (order_type == "LIMIT" or allow_queue) else None,
            quote=q
        )

        if match_res["status"] == "UNFILLED" or match_res["filled_shares"] <= 0:
            raise ValueError(f"模拟撮合失败: {match_res['details']}")

        filled_shares = match_res["filled_shares"]
        exec_price = match_res["avg_price"]
        gross_amount = round(filled_shares * exec_price, 2)

        # 6. 结算买入/卖出资金与持仓
        if action == "BUY":
            commission, _, transfer_fee = self.calc_fees(symbol, gross_amount, "BUY")
            total_cost = gross_amount + commission + transfer_fee

            if total_cost > acc["cash"]:
                raise ValueError(f"虚拟账户现金不足！需 {total_cost:.2f} 元，当前可用现金 {acc['cash']:.2f} 元")

            acc["cash"] = round(acc["cash"] - total_cost, 2)

            pos = acc["positions"].get(symbol)
            if not pos:
                acc["positions"][symbol] = {
                    "symbol": symbol,
                    "name": name,
                    "shares": filled_shares,
                    "avail_shares": 0,  # T+1 当天买入不可卖
                    "avg_cost": round(exec_price, 3),
                    "last_price": exec_price,
                }
            else:
                old_shares = pos["shares"]
                old_cost = pos["avg_cost"]
                new_shares = old_shares + filled_shares
                new_avg_cost = (old_shares * old_cost + gross_amount) / new_shares
                pos["shares"] = new_shares
                pos["avg_cost"] = round(new_avg_cost, 3)
                pos["last_price"] = exec_price

            order_record = {
                "order_id": f"ORD_{int(datetime.now().timestamp()*1000)}",
                "time": now_str,
                "trade_time": now_str,
                "symbol": symbol,
                "name": name,
                "action": "BUY",
                "order_type": order_type,
                "shares": filled_shares,
                "filled_shares": filled_shares,
                "price": exec_price,
                "avg_price": exec_price,
                "amount": gross_amount,
                "fee": round(commission + transfer_fee, 2),
                "slippage_cost": match_res["slippage_cost"],
                "status": match_res["status"],
                "details": match_res["details"],
                "reason": reason
            }
            acc["orders"].insert(0, order_record)

            # 微信推送交易提醒
            await wechat_notifier.send_signal_alert(
                symbol=symbol,
                name=name,
                action="BUY",
                price=exec_price,
                shares=filled_shares,
                reason=f"[模拟盘成交] {reason} ({match_res['details']})"
            )

        elif action == "SELL":
            pos = acc["positions"][symbol]
            commission, stamp_duty, transfer_fee = self.calc_fees(symbol, gross_amount, "SELL")
            total_fee = commission + stamp_duty + transfer_fee

            net_proceeds = round(gross_amount - total_fee, 2)
            acc["cash"] = round(acc["cash"] + net_proceeds, 2)

            cost_basis = filled_shares * pos["avg_cost"]
            pnl = round(gross_amount - cost_basis - total_fee, 2)
            pnl_pct = round((pnl / cost_basis) * 100, 2) if cost_basis > 0 else 0.0

            pos["shares"] -= filled_shares
            pos["avail_shares"] -= filled_shares
            if pos["shares"] <= 0:
                del acc["positions"][symbol]

            order_record = {
                "order_id": f"ORD_{int(datetime.now().timestamp()*1000)}",
                "time": now_str,
                "trade_time": now_str,
                "symbol": symbol,
                "name": name,
                "action": "SELL",
                "order_type": order_type,
                "shares": filled_shares,
                "filled_shares": filled_shares,
                "price": exec_price,
                "avg_price": exec_price,
                "amount": gross_amount,
                "fee": round(total_fee, 2),
                "slippage_cost": match_res["slippage_cost"],
                "pnl": pnl,
                "realized_pnl": pnl,
                "pnl_pct": pnl_pct,
                "status": match_res["status"],
                "details": match_res["details"],
                "reason": reason
            }
            acc["orders"].insert(0, order_record)

            # 微信推送交易提醒
            await wechat_notifier.send_signal_alert(
                symbol=symbol,
                name=name,
                action="SELL",
                price=exec_price,
                shares=filled_shares,
                reason=f"[模拟盘成交] 盈亏: {pnl:+,.2f}元 ({pnl_pct:+,.2f}%) [{match_res['details']}]"
            )

        await self._persist_account(acc)
        return await self.get_account_summary(account_id)

    async def cancel_order(self, account_id: str, order_id: str) -> Dict[str, Any]:
        """撤销处于排队中的委托挂单并释放冻结资金/持仓"""
        acc = await self.get_or_create_account(account_id)
        pending = acc.get("pending_orders", [])

        target_order = None
        target_idx = -1
        for idx, o in enumerate(pending):
            if o.get("order_id") == order_id:
                target_order = o
                target_idx = idx
                break

        if not target_order:
            raise ValueError(f"未找到可撤销的挂单 {order_id}，可能已成交或已撤单")

        # 释放冻结资产
        if target_order["action"] == "BUY":
            frozen_amt = target_order.get("frozen_amount", target_order.get("amount", 0.0))
            acc["cash"] = round(acc["cash"] + frozen_amt, 2)
            acc["frozen_cash"] = round(max(0.0, acc.get("frozen_cash", 0.0) - frozen_amt), 2)
        elif target_order["action"] == "SELL":
            sym = target_order["symbol"]
            shs = target_order["shares"]
            if sym in acc["positions"]:
                acc["positions"][sym]["avail_shares"] += shs

        target_order["status"] = "CANCELLED"
        target_order["details"] = "委托由用户主动撤销并解冻"
        pending.pop(target_idx)
        acc["orders"].insert(0, target_order)

        await self._persist_account(acc)
        return await self.get_account_summary(account_id)

    async def check_and_match_pending_orders(
        self,
        account_id: str,
        quotes: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        行情跳动时对排队委托挂单进行重检撮合
        若当前市价击穿委托价，则自动触发撮合成交
        """
        acc = await self.get_or_create_account(account_id)
        pending = acc.get("pending_orders", [])
        if not pending:
            return False

        if quotes is None:
            symbols = list({o["symbol"] for o in pending})
            streamer = get_quote_streamer()
            quotes = await streamer.fetch_batch_quotes(symbols)

        changed = False
        remaining_pending = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for o in pending:
            sym = o["symbol"]
            q = quotes.get(sym) or {}
            px = float(q.get("price") or 0.0)
            low_p = float(q.get("low") or px)
            high_p = float(q.get("high") or px)

            if px <= 0:
                remaining_pending.append(o)
                continue

            matched = False
            # 买单触发条件：最新价或最低价回踩至限价以下
            if o["action"] == "BUY" and (low_p <= o["price"] or px <= o["price"]):
                matched = True
                exec_px = o["price"]
                shs = o["shares"]
                gross = round(shs * exec_px, 2)
                frozen_amt = o.get("frozen_amount", gross)
                fee = o.get("fee", 0.5)

                # 解冻并结算
                acc["frozen_cash"] = round(max(0.0, acc.get("frozen_cash", 0.0) - frozen_amt), 2)
                # 若实际金额与冻结金额有差价退回现金
                diff = round(frozen_amt - (gross + fee), 2)
                if diff > 0:
                    acc["cash"] = round(acc["cash"] + diff, 2)

                pos = acc["positions"].get(sym)
                if not pos:
                    acc["positions"][sym] = {
                        "symbol": sym,
                        "name": o["name"],
                        "shares": shs,
                        "avail_shares": 0,
                        "avg_cost": round(exec_px, 3),
                        "last_price": px,
                    }
                else:
                    old_s = pos["shares"]
                    old_c = pos["avg_cost"]
                    new_s = old_s + shs
                    pos["shares"] = new_s
                    pos["avg_cost"] = round((old_s * old_c + gross) / new_s, 3)
                    pos["last_price"] = px

                o["status"] = "FILLED"
                o["filled_shares"] = shs
                o["avg_price"] = exec_px
                o["time"] = now_str
                o["details"] = f"盘口回踩至 ¥{low_p:.2f}，排队买单全部撮合成交"
                acc["orders"].insert(0, o)
                changed = True

            # 卖单触发条件：最新价或最高价冲高至限价以上
            elif o["action"] == "SELL" and (high_p >= o["price"] or px >= o["price"]):
                matched = True
                exec_px = o["price"]
                shs = o["shares"]
                gross = round(shs * exec_px, 2)
                commission, stamp_duty, transfer_fee = self.calc_fees(sym, gross, "SELL")
                total_fee = commission + stamp_duty + transfer_fee
                net_proceeds = round(gross - total_fee, 2)

                acc["cash"] = round(acc["cash"] + net_proceeds, 2)
                pos = acc["positions"].get(sym)
                cost_basis = shs * (pos["avg_cost"] if pos else exec_px)
                pnl = round(gross - cost_basis - total_fee, 2)
                pnl_pct = round((pnl / cost_basis) * 100, 2) if cost_basis > 0 else 0.0

                if pos:
                    pos["shares"] -= shs
                    if pos["shares"] <= 0:
                        del acc["positions"][sym]

                o["status"] = "FILLED"
                o["filled_shares"] = shs
                o["avg_price"] = exec_px
                o["fee"] = total_fee
                o["pnl"] = pnl
                o["realized_pnl"] = pnl
                o["pnl_pct"] = pnl_pct
                o["time"] = now_str
                o["details"] = f"盘口冲高至 ¥{high_p:.2f}，排队卖单全部撮合成交"
                acc["orders"].insert(0, o)
                changed = True

            if not matched:
                remaining_pending.append(o)

        acc["pending_orders"] = remaining_pending
        if changed:
            await self._persist_account(acc)
        return changed

    async def get_account_summary(self, account_id: str = "default") -> Dict[str, Any]:
        """获取账户当前资产总览及实时盈亏（全面对齐前后端字段）"""
        acc = await self.get_or_create_account(account_id)

        # 批量获取持仓与挂单标的的最新价格
        symbols = list(acc["positions"].keys()) + [po["symbol"] for po in acc.get("pending_orders", [])]
        symbols = list(set(symbols))
        quotes: Dict[str, Any] = {}

        if symbols:
            streamer = get_quote_streamer()
            quotes = await streamer.fetch_batch_quotes(symbols)
            # 尝试撮合挂单
            await self.check_and_match_pending_orders(account_id, quotes)

        market_val = 0.0
        today_pnl = 0.0
        holdings_list = []

        for sym, pos in acc["positions"].items():
            q = quotes.get(sym) or {}
            cur_px = float(q.get("price") or pos.get("last_price") or pos.get("avg_cost") or 0.0)
            prev_close = float(q.get("prev_close") or cur_px)
            if cur_px > 0:
                pos["last_price"] = cur_px

            shs = pos["shares"]
            cost_px = pos["avg_cost"]
            pos_val = round(shs * cur_px, 2)
            cost_val = round(shs * cost_px, 2)
            u_pnl = round(pos_val - cost_val, 2)
            u_pnl_pct = round((u_pnl / cost_val * 100), 2) if cost_val > 0 else 0.0

            pos["market_value"] = pos_val
            pos["unrealized_pnl"] = u_pnl
            pos["unrealized_pnl_pct"] = u_pnl_pct

            # 计算当日浮动盈亏
            t_pnl = round((cur_px - prev_close) * shs, 2)
            today_pnl += t_pnl

            market_val += pos_val

            # 对齐 PaperHolding 格式
            holdings_list.append({
                "symbol": sym,
                "name": pos.get("name", sym),
                "shares": shs,
                "available_shares": pos.get("avail_shares", 0),
                "avail_shares": pos.get("avail_shares", 0),
                "cost_price": cost_px,
                "avg_cost": cost_px,
                "current_price": cur_px,
                "last_price": cur_px,
                "market_value": pos_val,
                "floating_pnl": u_pnl,
                "unrealized_pnl": u_pnl,
                "floating_pnl_pct": u_pnl_pct,
                "unrealized_pnl_pct": u_pnl_pct,
            })

        cash = round(acc["cash"], 2)
        frozen_cash = round(acc.get("frozen_cash", 0.0), 2)
        total_assets = round(cash + frozen_cash + market_val, 2)
        initial_cash = acc.get("initial_cash", 100000.0)
        total_pnl = round(total_assets - initial_cash, 2)
        total_pnl_pct = round((total_pnl / initial_cash) * 100, 2) if initial_cash > 0 else 0.0

        # 对齐历史成交明细与老字段
        recent_trades = []
        for o in acc.get("orders", [])[:30]:
            recent_trades.append({
                "order_id": o.get("order_id"),
                "trade_time": o.get("trade_time") or o.get("time"),
                "time": o.get("time") or o.get("trade_time"),
                "symbol": o.get("symbol"),
                "name": o.get("name"),
                "action": o.get("action"),
                "order_type": o.get("order_type", "MARKET"),
                "shares": o.get("shares"),
                "price": o.get("price"),
                "avg_price": o.get("avg_price", o.get("price")),
                "amount": o.get("amount"),
                "fee": o.get("fee", 0.0),
                "slippage_cost": o.get("slippage_cost", 0.0),
                "realized_pnl": o.get("realized_pnl") or o.get("pnl", 0.0),
                "pnl": o.get("pnl") or o.get("realized_pnl", 0.0),
                "pnl_pct": o.get("pnl_pct", 0.0),
                "status": o.get("status", "FILLED"),
                "details": o.get("details", ""),
                "reason": o.get("reason", "")
            })

        pending_orders = []
        for po in acc.get("pending_orders", []):
            pending_orders.append({
                "order_id": po.get("order_id"),
                "trade_time": po.get("trade_time") or po.get("time"),
                "time": po.get("time") or po.get("trade_time"),
                "symbol": po.get("symbol"),
                "name": po.get("name"),
                "action": po.get("action"),
                "order_type": po.get("order_type", "LIMIT"),
                "shares": po.get("shares"),
                "price": po.get("price"),
                "amount": po.get("amount"),
                "status": po.get("status", "PENDING"),
                "details": po.get("details", "挂单排队中"),
                "reason": po.get("reason", "")
            })

        return {
            "account_id": account_id,
            "initial_cash": initial_cash,
            "initial_capital": initial_cash,
            "cash": cash,
            "frozen_cash": frozen_cash,
            "market_value": round(market_val, 2),
            "holdings_value": round(market_val, 2),
            "total_assets": total_assets,
            "total_equity": total_assets,
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct,
            "total_return_pct": total_pnl_pct,
            "today_pnl": round(today_pnl, 2),
            "positions": list(acc["positions"].values()),
            "holdings": holdings_list,
            "recent_orders": recent_trades,
            "recent_trades": recent_trades,
            "pending_orders": pending_orders,
            "equity_history": acc.get("equity_history", []),
        }

    async def _persist_account(self, acc: Dict[str, Any]):
        """异步落库 MongoDB"""
        acc["updated_at"] = datetime.now().isoformat()
        col = self._get_collection()
        if col is not None:
            try:
                await col.update_one(
                    {"account_id": acc["account_id"]},
                    {"$set": acc},
                    upsert=True
                )
            except Exception as e:
                logger.error(f"更新模拟账户持久化失败: {e}")


# 全局单例
paper_account_service = PaperAccountService()
