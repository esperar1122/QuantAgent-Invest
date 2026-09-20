"""
统一数据源提供器包
按市场分类组织数据提供器
"""
from .base_provider import BaseStockDataProvider

# 导入中国市场提供器（新路径）
try:
    from .china import (
        AKShareProvider,
        TushareProvider,
        BaostockProvider as BaoStockProvider,
        AKSHARE_AVAILABLE,
        TUSHARE_AVAILABLE,
        BAOSTOCK_AVAILABLE
    )
except ImportError:
    # 向后兼容：尝试从旧路径导入
    try:
        from .tushare_provider import TushareProvider
    except ImportError:
        TushareProvider = None

    try:
        from .akshare_provider import AKShareProvider
    except ImportError:
        AKShareProvider = None

    try:
        from .baostock_provider import BaoStockProvider
    except ImportError:
        BaoStockProvider = None

    AKSHARE_AVAILABLE = AKShareProvider is not None
    TUSHARE_AVAILABLE = TushareProvider is not None
    BAOSTOCK_AVAILABLE = BaoStockProvider is not None

# 港股提供器已下线（系统纯化为A股量化体系）
ImprovedHKStockProvider = None
get_improved_hk_provider = None
HK_PROVIDER_AVAILABLE = False

# 美股提供器已下线（系统纯化为A股量化体系）
YFinanceUtils = None
OptimizedUSDataProvider = None
get_data_in_range = None
YFINANCE_AVAILABLE = False
OPTIMIZED_US_AVAILABLE = False
FINNHUB_AVAILABLE = False

# 其他提供器（预留）
try:
    from .yahoo_provider import YahooProvider
except ImportError:
    YahooProvider = None

try:
    from .finnhub_provider import FinnhubProvider
except ImportError:
    FinnhubProvider = None

__all__ = [
    # 基类
    'BaseStockDataProvider',

    # 中国市场
    'TushareProvider',
    'AKShareProvider',
    'BaoStockProvider',
    'AKSHARE_AVAILABLE',
    'TUSHARE_AVAILABLE',
    'BAOSTOCK_AVAILABLE',

    # 港股（已下线）
    'ImprovedHKStockProvider',
    'get_improved_hk_provider',
    'HK_PROVIDER_AVAILABLE',

    # 美股（已下线）
    'YFinanceUtils',
    'OptimizedUSDataProvider',
    'get_data_in_range',
    'YFINANCE_AVAILABLE',
    'OPTIMIZED_US_AVAILABLE',
    'FINNHUB_AVAILABLE',

    # 其他（预留）
    'YahooProvider',
    'FinnhubProvider',
]
