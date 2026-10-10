"""
数据提供器基类抽象定义
规范所有金融数据源（A股、美股、港股、公募基金、ETF、另类数据等）统一接入标准
"""
from app.data_sources.providers.base_provider import BaseStockDataProvider

__all__ = ["BaseStockDataProvider"]
