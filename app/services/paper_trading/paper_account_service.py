"""
虚拟模拟盘交易账户管理服务 (Paper Trading Engine)
提供完整的虚拟资金、持仓、T+1交易撮合、盈亏核算与历史净值跟踪
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.quotes.realtime_streamer import get_quote_streamer
from app.services.notifier.wechat_notifier import wechat_notifier

logger = logging.getLogger(__name__)


class PaperAccountService:
    """虚拟仿真账户服务"""

    def __init__(self):
        # 内存缓存（配合 MongoDB 持久化）
        self._memory_accounts: Dict[str, Dict[str, Any]] = {}

    def _get_collection(self):
        """获取 MongoDB 集合"""
        try:
            from app.core.database import get_database
            db = get_database()
            return db.paper_accounts
        except Exception:
            return None

    async def get_or_create_account(self, account_id: str = "default", initial_cash: float = 100000.0) -> Dict[str, Any]:
        """获取或创建模拟账户"""
        col = self._get_collection()
        if col:
            try:
                acc = await col.find_one({"account_id": account_id})
                if acc:
                    acc.pop("_id", None)
                    return acc
            except Exception as e:
                logger.warning(f"从MongoDB查询模拟账户异常: {e}")

        # 若数据库没有，则创建新账户
        if account_id in self._memory_accounts:
            return self._memory_accounts[account_id]

        new_acc = {
            "account_id": account_id,
            "initial_cash": float(initial_cash),
            "cash": float(initial_cash),
            "positions": {},  # { "600519": { "symbol": "600519", "name": "贵州茅台", "shares": 200, "avail_shares": 200, "avg_cost": 1600.0, ... } }
            "orders": [],
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

        if col:
            try:
                await col.insert_one(new_acc.copy())
            except Exception as e:
                logger.warning(f"模拟账户持久化失败: {e}")

        self._memory_accounts[account_id] = new_acc
        return new_acc

    async def execute_trade(
        self,
        account_id: str,
        symbol: str,
        name: str,
        action: str,  # "BUY" / "SELL"
        shares: int,
        price: Optional[float] = None,
        reason: str = "手动模拟交易"
    ) -> Dict[str, Any]:
        """
        在虚拟账户中执行模拟买入/卖出委托
        严格遵循 A 股规则：买入按 100 股整倍，卖出受 T+1 限制，扣减手续费
        """
        acc = await self.get_or_create_account(account_id)

        # 1. 如果未传价格，从实时行情拉取最新快照价
        if price is None or price <= 0:
            streamer = get_quote_streamer()
            quotes = await streamer.fetch_batch_quotes([symbol])
            q = quotes.get(symbol)
            if q and q.get("price", 0) > 0:
                price = q["price"]
                name = q.get("name", name)
            else:
                raise ValueError(f"无法获取标的 {symbol} 的当前最新市价，请手动指定价格")

        action = action.upper()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 2. 买入逻辑
        if action == "BUY":
            shares = (shares // 100) * 100
            if shares < 100:
                raise ValueError("A股买入数量至少为 100 股（1手）且必须为整百数")

            gross_amount = round(shares * price, 2)
            # 佣金 万2.5，最低5元
            commission = max(5.0, round(gross_amount * 0.00025, 2))
            transfer_fee = round(gross_amount * 0.00001, 2)
            total_cost = gross_amount + commission + transfer_fee

            if total_cost > acc["cash"]:
                raise ValueError(f"虚拟账户现金不足！需 {total_cost:.2f} 元，当前可用现金 {acc['cash']:.2f} 元")

            acc["cash"] = round(acc["cash"] - total_cost, 2)

            pos = acc["positions"].get(symbol)
            if not pos:
                acc["positions"][symbol] = {
                    "symbol": symbol,
                    "name": name,
                    "shares": shares,
                    "avail_shares": 0,  # T+1 当天买入不可卖
                    "avg_cost": round(price, 3),
                    "last_price": price,
                }
            else:
                old_shares = pos["shares"]
                old_cost = pos["avg_cost"]
                new_shares = old_shares + shares
                new_avg_cost = (old_shares * old_cost + gross_amount) / new_shares
                pos["shares"] = new_shares
                pos["avg_cost"] = round(new_avg_cost, 3)
                pos["last_price"] = price

            order_record = {
                "order_id": f"ORD_{int(datetime.now().timestamp()*1000)}",
                "time": now_str,
                "symbol": symbol,
                "name": name,
                "action": "BUY",
                "shares": shares,
                "price": price,
                "amount": gross_amount,
                "fee": round(commission + transfer_fee, 2),
                "reason": reason
            }
            acc["orders"].insert(0, order_record)

            # 微信推送交易提醒
            await wechat_notifier.send_signal_alert(
                symbol=symbol,
                name=name,
                action="BUY",
                price=price,
                shares=shares,
                reason=f"[模拟盘成交] {reason}"
            )

        # 3. 卖出逻辑
        elif action == "SELL":
            pos = acc["positions"].get(symbol)
            if not pos:
                raise ValueError(f"当前未持有标的 {symbol}")

            avail = pos.get("avail_shares", 0)
            if avail < shares:
                raise ValueError(f"可用持仓不足（T+1限制）！可卖: {avail} 股，申请卖出: {shares} 股")

            gross_amount = round(shares * price, 2)
            commission = max(5.0, round(gross_amount * 0.00025, 2))
            stamp_duty = round(gross_amount * 0.0005, 2)  # 印花税万5
            transfer_fee = round(gross_amount * 0.00001, 2)
            total_fee = commission + stamp_duty + transfer_fee

            net_proceeds = round(gross_amount - total_fee, 2)
            acc["cash"] = round(acc["cash"] + net_proceeds, 2)

            cost_basis = shares * pos["avg_cost"]
            pnl = round(gross_amount - cost_basis - total_fee, 2)
            pnl_pct = round((pnl / cost_basis) * 100, 2) if cost_basis > 0 else 0.0

            pos["shares"] -= shares
            pos["avail_shares"] -= shares
            if pos["shares"] <= 0:
                del acc["positions"][symbol]

            order_record = {
                "order_id": f"ORD_{int(datetime.now().timestamp()*1000)}",
                "time": now_str,
                "symbol": symbol,
                "name": name,
                "action": "SELL",
                "shares": shares,
                "price": price,
                "amount": gross_amount,
                "fee": round(total_fee, 2),
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "reason": reason
            }
            acc["orders"].insert(0, order_record)

            # 微信推送交易提醒
            await wechat_notifier.send_signal_alert(
                symbol=symbol,
                name=name,
                action="SELL",
                price=price,
                shares=shares,
                reason=f"[模拟盘成交] 盈亏: {pnl:+,.2f}元 ({pnl_pct:+,.2f}%)"
            )
        else:
            raise ValueError(f"不支持的操作类型: {action}")

        # 4. 持久化并返回最新账户概览
        acc["updated_at"] = datetime.now().isoformat()
        col = self._get_collection()
        if col:
            try:
                await col.update_one(
                    {"account_id": account_id},
                    {"$set": acc},
                    upsert=True
                )
            except Exception as e:
                logger.error(f"更新模拟账户持久化失败: {e}")

        return await self.get_account_summary(account_id)

    async def get_account_summary(self, account_id: str = "default") -> Dict[str, Any]:
        """获取账户当前资产总览及实时盈亏"""
        acc = await self.get_or_create_account(account_id)

        # 批量获取持仓标的的最新价格
        symbols = list(acc["positions"].keys())
        market_val = 0.0

        if symbols:
            streamer = get_quote_streamer()
            quotes = await streamer.fetch_batch_quotes(symbols)
            for sym, pos in acc["positions"].items():
                q = quotes.get(sym)
                if q and q.get("price", 0) > 0:
                    pos["last_price"] = q["price"]
                cur_px = pos.get("last_price", pos["avg_cost"])
                pos_val = round(pos["shares"] * cur_px, 2)
                cost_val = round(pos["shares"] * pos["avg_cost"], 2)
                pos["market_value"] = pos_val
                pos["unrealized_pnl"] = round(pos_val - cost_val, 2)
                pos["unrealized_pnl_pct"] = round((pos["unrealized_pnl"] / cost_val * 100), 2) if cost_val > 0 else 0.0
                market_val += pos_val

        total_assets = round(acc["cash"] + market_val, 2)
        total_pnl = round(total_assets - acc["initial_cash"], 2)
        total_pnl_pct = round((total_pnl / acc["initial_cash"]) * 100, 2) if acc["initial_cash"] > 0 else 0.0

        return {
            "account_id": account_id,
            "initial_cash": acc["initial_cash"],
            "cash": acc["cash"],
            "market_value": round(market_val, 2),
            "total_assets": total_assets,
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct,
            "positions": list(acc["positions"].values()),
            "recent_orders": acc["orders"][:20],
            "equity_history": acc["equity_history"],
        }


# 全局单例
paper_account_service = PaperAccountService()
