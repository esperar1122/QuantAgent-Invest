"""
回测历史数据加载器
支持：MongoDB 本地数据 -> AKShare / BaoStock 降级在线获取，自动前复权
"""

import logging
import pandas as pd
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def load_backtest_data(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    加载用于回测的历史K线数据，确保字段包含 ['date', 'open', 'high', 'low', 'close', 'volume']
    """
    clean_sym = symbol.strip().split(".")[0]
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
    else:
        start_date = start_date.replace("-", "")

    if not end_date:
        end_date = datetime.now().strftime("%Y%m%d")
    else:
        end_date = end_date.replace("-", "")

    # 1. 优先尝试使用 AKShare 获取前复权历史日K
    try:
        import akshare as ak
        logger.info(f"📊 使用 AKShare 获取 {clean_sym} 前复权历史数据 ({start_date} - {end_date})...")
        df = ak.stock_zh_a_hist(
            symbol=clean_sym,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        if df is not None and not df.empty and len(df) >= 10:
            rename_map = {
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
            }
            res_df = df.rename(columns=rename_map)[["date", "open", "high", "low", "close", "volume"]].copy()
            res_df["date"] = pd.to_datetime(res_df["date"]).dt.strftime("%Y-%m-%d")
            res_df = res_df.sort_values("date").reset_index(drop=True)
            return res_df
    except Exception as e:
        logger.warning(f"⚠️ AKShare 获取历史数据异常: {e}，尝试使用备用通道...")

    # 2. 备用：BaoStock 获取前复权历史日K
    try:
        import baostock as bs
        lg = bs.login()
        market = "sh" if clean_sym.startswith(("60", "68")) else "sz"
        bs_code = f"{market}.{clean_sym}"
        rs = bs.query_history_k_data_plus(
            code=bs_code,
            fields="date,open,high,low,close,volume",
            start_date=f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}",
            end_date=f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}",
            frequency="d",
            adjustflag="2"  # 2: 前复权
        )
        data_list = []
        while (rs.error_code == '0') and rs.next():
            data_list.append(rs.get_row_data())
        bs.logout()

        if data_list:
            res_df = pd.DataFrame(data_list, columns=["date", "open", "high", "low", "close", "volume"])
            for c in ["open", "high", "low", "close", "volume"]:
                res_df[c] = pd.to_numeric(res_df[c], errors="coerce")
            res_df = res_df.dropna().sort_values("date").reset_index(drop=True)
            if len(res_df) >= 10:
                return res_df
    except Exception as e:
        logger.error(f"❌ BaoStock 获取历史数据失败: {e}")

    # 若在线获取均受网络限制，生成基准参考合成走势
    raise ValueError(f"无法获取股票 {clean_sym} 的历史日K线数据，请检查网络或股票代码是否正确")
