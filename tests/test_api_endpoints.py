"""
API 端点集成测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from app.routers import backtest, portfolio, realtime_quotes, paper_trading

app = FastAPI()
app.include_router(backtest.router)
app.include_router(portfolio.router)
app.include_router(realtime_quotes.router)
app.include_router(paper_trading.router)


async def test_all_new_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. 回测策略列表
        resp = await client.get("/api/backtest/strategies")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]) >= 3
        print("✅ GET /api/backtest/strategies passed")

        # 2. 仓位计算：ATR
        resp = await client.post("/api/portfolio/calculate-atr", json={
            "total_capital": 100000.0,
            "price": 1600.0,
            "atr_value": 35.0,
            "risk_ratio": 0.01
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["shares"] >= 0
        print("✅ POST /api/portfolio/calculate-atr passed")

        # 3. 仓位计算：凯利公式
        resp = await client.post("/api/portfolio/calculate-kelly", json={
            "total_capital": 100000.0,
            "win_rate": 0.58,
            "profit_loss_ratio": 2.1
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["recommended_weight"] > 0
        print("✅ POST /api/portfolio/calculate-kelly passed")

        # 4. 实时行情快照
        resp = await client.get("/api/quotes/live/600519,000001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "600519" in data["data"]
        print("✅ GET /api/quotes/live/600519,000001 passed, name:", data["data"]["600519"]["name"], "price:", data["data"]["600519"]["price"])

        # 5. 模拟账户总览
        resp = await client.get("/api/paper-trading/account?account_id=test_api_acc")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["cash"] > 0
        print("✅ GET /api/paper-trading/account passed")

        # 6. 模拟账户下单
        resp = await client.post("/api/paper-trading/order", json={
            "account_id": "test_api_acc",
            "symbol": "000001",
            "name": "平安银行",
            "action": "BUY",
            "shares": 500,
            "price": 10.5,
            "reason": "API自动化集成测试"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        print("✅ POST /api/paper-trading/order passed")

    print("\n🎉 ALL NEW API ENDPOINTS TESTED AND PASSED!")


if __name__ == "__main__":
    asyncio.run(test_all_new_endpoints())
