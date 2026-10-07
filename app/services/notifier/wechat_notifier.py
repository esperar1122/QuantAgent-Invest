"""
微信机器人与即时交易信号推送服务 (WeChat & Webhook Notifier)
支持：企业微信机器人 Webhook、Server酱（微信直达）、飞书机器人
"""

import os
import logging
from typing import Dict, Any, Optional
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)


class WeChatNotifier:
    """微信与即时通讯告警机器人"""

    def __init__(
        self,
        wecom_webhook: Optional[str] = None,
        serverchan_key: Optional[str] = None,
        feishu_webhook: Optional[str] = None,
    ):
        self.wecom_webhook = wecom_webhook or os.getenv("WECOM_WEBHOOK_URL", "")
        self.serverchan_key = serverchan_key or os.getenv("SERVERCHAN_KEY", "")
        self.feishu_webhook = feishu_webhook or os.getenv("FEISHU_WEBHOOK_URL", "")

    async def send_signal_alert(
        self,
        symbol: str,
        name: str,
        action: str,  # "BUY" / "SELL"
        price: float,
        shares: int,
        reason: str = "策略触发",
        stop_loss_price: Optional[float] = None,
        target_price: Optional[float] = None
    ) -> bool:
        """
        向微信推送格式化的交易信号卡片
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        action_text = "🟢 买入建仓" if action.upper() == "BUY" else "🔴 卖出平仓"
        est_amount = round(shares * price, 2)

        markdown_content = f"""### 📢 QuantAgent 交易信号提醒
**时间**：{now_str}
**标的**：`{symbol}` {name}
**指令**：<font color="{'info' if action.upper() == 'BUY' else 'warning'}">{action_text}</font>
**建议价格**：`{price:.2f}` 元
**数量**：`{shares}` 股（约 {est_amount:,.2f} 元）
"""
        if stop_loss_price:
            markdown_content += f"**建议止损**：`{stop_loss_price:.2f}` 元\n"
        if target_price:
            markdown_content += f"**目标价格**：`{target_price:.2f}` 元\n"
        markdown_content += f"**逻辑理由**：{reason}\n"
        markdown_content += f"> 请及时在手机券商客户端核对并手动确认委托。"

        title = f"【交易信号】{action_text} {name}({symbol}) {shares}股"
        return await self._dispatch(title, markdown_content)

    async def send_risk_alert(self, title: str, content: str, level: str = "WARNING") -> bool:
        """发送风控警报（如单日回撤触碰熔断线、某标的跌破止损位）"""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        card = f"""### ⚠️ QuantAgent 风控警报 [{level}]
**触发时间**：{now_str}
**警报摘要**：{title}
**详情**：{content}
"""
        return await self._dispatch(f"【风控告警】{title}", card)

    async def _dispatch(self, title: str, markdown_text: str) -> bool:
        """多通道分发"""
        success = False
        async with httpx.AsyncClient(timeout=5.0) as client:
            # 1. 企业微信机器人
            if self.wecom_webhook:
                try:
                    payload = {
                        "msgtype": "markdown",
                        "markdown": {"content": markdown_text}
                    }
                    r = await client.post(self.wecom_webhook, json=payload)
                    if r.status_code == 200:
                        logger.info("✅ 企业微信机器人推送成功")
                        success = True
                except Exception as e:
                    logger.error(f"企业微信推送失败: {e}")

            # 2. Server酱（个人微信服务号直推）
            if self.serverchan_key:
                try:
                    sc_url = f"https://sctapi.ftqq.com/{self.serverchan_key}.send"
                    payload = {
                        "title": title[:30],
                        "desp": markdown_text
                    }
                    r = await client.post(sc_url, data=payload)
                    if r.status_code == 200:
                        logger.info("✅ Server酱微信推送成功")
                        success = True
                except Exception as e:
                    logger.error(f"Server酱推送失败: {e}")

            # 3. 飞书机器人
            if self.feishu_webhook:
                try:
                    payload = {
                        "msg_type": "text",
                        "content": {"text": f"{title}\n\n{markdown_text}"}
                    }
                    r = await client.post(self.feishu_webhook, json=payload)
                    if r.status_code == 200:
                        logger.info("✅ 飞书机器人推送成功")
                        success = True
                except Exception as e:
                    logger.error(f"飞书推送失败: {e}")

        if not (self.wecom_webhook or self.serverchan_key or self.feishu_webhook):
            logger.info(f"ℹ️ 未配置微信/飞书Webhook，模拟控制台输出: {title}")
            return True

        return success


# 全局单例
wechat_notifier = WeChatNotifier()
