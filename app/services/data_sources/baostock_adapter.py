"""
BaoStock data source adapter
"""
from typing import Optional
import logging
from datetime import datetime, timedelta
import pandas as pd

from .base import DataSourceAdapter

logger = logging.getLogger(__name__)


class BaoStockAdapter(DataSourceAdapter):
    """BaoStockdata source adapter"""

    def __init__(self):
        super().__init__()  # 调用父类初始化

    @property
    def name(self) -> str:
        return "baostock"

    def _get_default_priority(self) -> int:
        return 1  # lowest priority (数字越大优先级越高)

    def is_available(self) -> bool:
        try:
            import baostock as bs  # noqa: F401
            return True
        except ImportError:
            return False

    def get_stock_list(self) -> Optional[pd.DataFrame]:
        if not self.is_available():
            return None
        try:
            import baostock as bs
            lg = bs.login()
            if lg.error_code != '0':
                logger.error(f"BaoStock: Login failed: {lg.error_msg}")
                return None
            try:
                logger.info("BaoStock: Querying stock basic info...")
                rs = bs.query_stock_basic()
                if rs.error_code != '0':
                    logger.error(f"BaoStock: Query failed: {rs.error_msg}")
                    return None
                data_list = []
                while (rs.error_code == '0') & rs.next():
                    data_list.append(rs.get_row_data())
                if not data_list:
                    return None
                df = pd.DataFrame(data_list, columns=rs.fields)
                # 仅保留处于正常上市状态的A股标的（type='1' 股票，status='1' 上市中；剔除 status='0' 已退市标的）
                if 'status' in df.columns:
                    df = df[(df['type'] == '1') & (df['status'] == '1')]
                else:
                    df = df[df['type'] == '1']

                # 剔除名称含“退”或“PT”的退市/整理期标的
                if 'code_name' in df.columns:
                    df = df[~df['code_name'].str.contains(r'退|PT', regex=True, na=False)]

                df['symbol'] = df['code'].str.replace(r'^(sh|sz)\.', '', regex=True)
                df['ts_code'] = (
                    df['code'].str.replace('sh.', '').str.replace('sz.', '')
                    + df['code'].str.extract(r'^(sh|sz)\.').iloc[:, 0].str.upper().str.replace('SH', '.SH').str.replace('SZ', '.SZ')
                )
                df['name'] = df['code_name']
                df['area'] = ''

                # 行业信息通过基础信息或快速映射获取，跳过可能无响应的服务端 industry 接口
                df['industry'] = ''
                logger.info(f"BaoStock: 正常上市股票列表已就绪 ({len(df)} 只，已剔除退市标的)")

                def classify_market(sym: str) -> str:
                    s = str(sym).strip()
                    if s.startswith(('688', '689')):
                        return '科创板'
                    elif s.startswith(('300', '301')):
                        return '创业板'
                    elif s.startswith(('8', '4', '920')):
                        return '北交所'
                    return '主板'

                df['market'] = df['symbol'].apply(classify_market)
                df['list_date'] = ''
                logger.info(f"BaoStock: Successfully fetched {len(df)} stocks")
                return df[['symbol', 'name', 'ts_code', 'area', 'industry', 'market', 'list_date']]
            finally:
                bs.logout()
        except Exception as e:
            logger.error(f"BaoStock: Failed to fetch stock list: {e}")
            return None

    def get_daily_basic(self, trade_date: str, max_stocks: int = None) -> Optional[pd.DataFrame]:
        """
        获取每日基础数据（包含PE、PB、总市值等）

        Args:
            trade_date: 交易日期 (YYYYMMDD)
            max_stocks: 最大处理股票数量，None表示处理所有股票
        """
        if not self.is_available():
            return None
        try:
            import baostock as bs
            logger.info(f"BaoStock: Attempting to get valuation data for {trade_date}")
            lg = bs.login()
            if lg.error_code != '0':
                logger.error(f"BaoStock: Login failed: {lg.error_msg}")
                return None
            try:
                logger.info("BaoStock: Querying stock basic info...")
                rs = bs.query_stock_basic()
                if rs.error_code != '0':
                    logger.error(f"BaoStock: Query stock list failed: {rs.error_msg}")
                    return None
                stock_list = []
                while (rs.error_code == '0') & rs.next():
                    stock_list.append(rs.get_row_data())
                if not stock_list:
                    logger.warning("BaoStock: No stocks found")
                    return None

                # 过滤正常上市A股
                active_stocks = []
                for s in stock_list:
                    c_name = s[1] if len(s) > 1 else ''
                    s_type = s[4] if len(s) > 4 else '0'
                    s_status = s[5] if len(s) > 5 else '0'
                    if s_type == '1' and s_status == '1' and '退' not in c_name and not c_name.startswith('PT'):
                        active_stocks.append(s)

                stock_list = active_stocks
                total_stocks = len(stock_list)

                # 默认限制最大处理数量为 200 只，避免全量 5000 只无休止查询
                actual_max = max_stocks if max_stocks is not None else 200
                logger.info(f"📊 BaoStock: 找到 {total_stocks} 只活跃股票，开始处理 (上限: {actual_max} 只，最长30秒)...")

                import time
                start_time = time.time()
                max_duration = 30.0  # 最多执行30秒，避免长时间挂起

                basic_data = []
                processed_count = 0
                failed_count = 0
                for stock in stock_list:
                    if processed_count >= actual_max:
                        break
                    if time.time() - start_time > max_duration:
                        logger.warning(f"⏱️ BaoStock: 达到最大耗时限制 ({max_duration}秒)，已处理 {processed_count} 只股票，提前返回")
                        break
                    code = stock[0] if len(stock) > 0 else ''
                    name = stock[1] if len(stock) > 1 else ''
                    stock_type = stock[4] if len(stock) > 4 else '0'
                    status = stock[5] if len(stock) > 5 else '0'
                    if stock_type == '1' and status == '1':
                        try:
                            formatted_date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
                            # 🔥 获取估值数据和总股本
                            rs_valuation = bs.query_history_k_data_plus(
                                code,
                                "date,code,close,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                                start_date=formatted_date,
                                end_date=formatted_date,
                                frequency="d",
                                adjustflag="3",
                            )
                            if rs_valuation.error_code == '0':
                                valuation_data = []
                                while (rs_valuation.error_code == '0') & rs_valuation.next():
                                    valuation_data.append(rs_valuation.get_row_data())
                                if valuation_data:
                                    row = valuation_data[0]
                                    symbol = code.replace('sh.', '').replace('sz.', '')
                                    ts_code = f"{symbol}.SH" if code.startswith('sh.') else f"{symbol}.SZ"
                                    pe_ttm = self._safe_float(row[3]) if len(row) > 3 else None
                                    pb_mrq = self._safe_float(row[4]) if len(row) > 4 else None
                                    ps_ttm = self._safe_float(row[5]) if len(row) > 5 else None
                                    pcf_ttm = self._safe_float(row[6]) if len(row) > 6 else None
                                    close_price = self._safe_float(row[2]) if len(row) > 2 else None

                                    # 🔥 BaoStock 不直接提供总市值和总股本
                                    # 为了避免同步超时，这里不调用额外的 API 获取总股本
                                    # total_mv 留空，后续可以通过其他数据源补充
                                    total_mv = None

                                    basic_data.append({
                                        'ts_code': ts_code,
                                        'trade_date': trade_date,
                                        'name': name,
                                        'pe': pe_ttm,  # 🔥 市盈率（TTM）
                                        'pb': pb_mrq,  # 🔥 市净率（MRQ）
                                        'ps': ps_ttm,  # 市销率
                                        'pcf': pcf_ttm,  # 市现率
                                        'close': close_price,
                                        'total_mv': total_mv,  # ⚠️ BaoStock 不提供，留空
                                        'turnover_rate': None,  # ⚠️ BaoStock 不提供
                                    })
                                    processed_count += 1

                                    # 🔥 每处理50只股票输出一次进度日志
                                    if processed_count % 50 == 0:
                                        progress_pct = (processed_count / total_stocks) * 100
                                        logger.info(f"📈 BaoStock 同步进度: {processed_count}/{total_stocks} ({progress_pct:.1f}%) - 最新: {name}({ts_code})")
                                else:
                                    failed_count += 1
                            else:
                                failed_count += 1
                        except Exception as e:
                            failed_count += 1
                            if failed_count % 50 == 0:
                                logger.warning(f"⚠️ BaoStock: 已有 {failed_count} 只股票获取失败")
                            logger.debug(f"BaoStock: Failed to get valuation for {code}: {e}")
                            continue
                if basic_data:
                    df = pd.DataFrame(basic_data)
                    logger.info(f"✅ BaoStock 同步完成: 成功 {len(df)} 只，失败 {failed_count} 只，日期 {trade_date}")
                    return df
                else:
                    logger.warning(f"⚠️ BaoStock: 未获取到任何估值数据（失败 {failed_count} 只）")
                    return None
            finally:
                bs.logout()
        except Exception as e:
            logger.error(f"BaoStock: Failed to fetch valuation data for {trade_date}: {e}")
            return None

    def _safe_float(self, value) -> Optional[float]:
        try:
            if value is None or value == '' or value == 'None':
                return None
            return float(value)
        except (ValueError, TypeError):
            return None


    def get_realtime_quotes(self):
        """Placeholder: BaoStock does not provide full-market realtime snapshot in our adapter.
        Return None to allow fallback to higher-priority sources.
        """
        if not self.is_available():
            return None
        return None

    def get_kline(self, code: str, period: str = "day", limit: int = 120, adj: Optional[str] = None):
        """BaoStock K-line implementation for day/week/month"""
        if not self.is_available():
            return None
        try:
            import baostock as bs
            code_str = str(code).strip()
            # Normalize to BaoStock symbol (sh.600519 or sz.000001 or bj.xxxxxx)
            if not (code_str.startswith("sh.") or code_str.startswith("sz.") or code_str.startswith("bj.")):
                c6 = code_str.zfill(6)
                if c6.startswith(("60", "68", "90")):
                    bs_code = f"sh.{c6}"
                elif c6.startswith(("00", "30", "20")):
                    bs_code = f"sz.{c6}"
                elif c6.startswith(("43", "83", "87", "88", "92")):
                    bs_code = f"bj.{c6}"
                else:
                    bs_code = f"sh.{c6}"
            else:
                bs_code = code_str

            freq_map = {"day": "d", "week": "w", "month": "m", "5m": "5", "15m": "15", "30m": "30", "60m": "60"}
            freq = freq_map.get(period, "d")
            # adjustflag: 1后复权 2前复权 3不复权
            adj_flag = "2" if adj == "qfq" else "1" if adj == "hfq" else "3"

            end_d = datetime.now().strftime("%Y-%m-%d")
            start_d = (datetime.now() - timedelta(days=max(limit * 3, 100))).strftime("%Y-%m-%d")

            lg = bs.login()
            if lg.error_code != '0':
                return None
            try:
                rs = bs.query_history_k_data_plus(
                    bs_code,
                    "date,open,high,low,close,volume,amount",
                    start_date=start_d,
                    end_date=end_d,
                    frequency=freq,
                    adjustflag=adj_flag
                )
                items = []
                while (rs.error_code == '0') & rs.next():
                    row = rs.get_row_data()
                    items.append({
                        "time": row[0],
                        "open": self._safe_float(row[1]),
                        "high": self._safe_float(row[2]),
                        "low": self._safe_float(row[3]),
                        "close": self._safe_float(row[4]),
                        "volume": self._safe_float(row[5]),
                        "amount": self._safe_float(row[6]),
                    })
                if items:
                    return items[-limit:]
                return None
            finally:
                bs.logout()
        except Exception as e:
            logger.error(f"BaoStock get_kline failed: {e}")
            return None

    def get_news(self, code: str, days: int = 2, limit: int = 50, include_announcements: bool = True):
        """BaoStock does not provide news in this adapter; return None"""
        if not self.is_available():
            return None
        return None

        """Placeholder: BaoStock  does not provide full-market realtime snapshot in our adapter.
        Return None to allow fallback to higher-priority sources.
        """

    def find_latest_trade_date(self) -> Optional[str]:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        logger.info(f"BaoStock: Using yesterday as trade date: {yesterday}")
        return yesterday

