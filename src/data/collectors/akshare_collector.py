"""
Akshare 数据采集器
获取申万行业估值和实时行情
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import pandas as pd
from loguru import logger

from .base_collector import BaseCollector


class AkshareCollector(BaseCollector):
    """Akshare 数据采集器"""

    def __init__(self, retry: int = 3, retry_interval: int = 2):
        super().__init__(retry, retry_interval)
        self._ak = None

    def connect(self) -> bool:
        """连接 Akshare（无需显式连接）"""
        try:
            import akshare as ak
            self._ak = ak
            self._connected = True
            logger.info("Akshare 初始化成功")
            return True
        except ImportError:
            logger.error("请安装 akshare: pip install akshare")
            return False
        except Exception as e:
            logger.error(f"Akshare 初始化异常: {e}")
            return False

    def disconnect(self) -> None:
        """Akshare 无需断开连接"""
        self._connected = False
        logger.info("Akshare 已标记为断开")

    def is_connected(self) -> bool:
        """检查是否已初始化"""
        return self._connected

    def get_sw_index_second_info(self) -> pd.DataFrame:
        """
        获取申万二级行业实时估值数据

        Returns:
            包含行业代码、名称、PE、PB等数据的 DataFrame
        """
        if not self._connected:
            raise RuntimeError("Akshare 未初始化")

        logger.info("获取申万二级行业实时估值...")

        def _do_fetch():
            return self._ak.sw_index_second_info()

        try:
            df = self._retry_wrapper(_do_fetch)
            if not df.empty:
                logger.info(f"获取到 {len(df)} 个申万二级行业的实时估值")
                # 标准化列名
                df.columns = [c.strip() for c in df.columns]
            return df
        except Exception as e:
            logger.error(f"获取申万二级行业估值失败: {e}")
            return pd.DataFrame()

    def get_sw_index_first_info(self) -> pd.DataFrame:
        """
        获取申万一级行业列表

        Returns:
            申万一级行业列表
        """
        if not self._connected:
            raise RuntimeError("Akshare 未初始化")

        logger.info("获取申万一级行业列表...")

        def _do_fetch():
            return self._ak.sw_index_first_info()

        try:
            df = self._retry_wrapper(_do_fetch)
            if not df.empty:
                logger.info(f"获取到 {len(df)} 个申万一级行业")
                df.columns = [c.strip() for c in df.columns]
            return df
        except Exception as e:
            logger.error(f"获取申万一级行业列表失败: {e}")
            return pd.DataFrame()

    def get_sw_index_daily(self, indicator: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取申万行业指数历史日线数据

        Args:
            indicator: 申万行业代码，如 "801991.SI"
            start_date: 开始日期 "YYYYMMDD"
            end_date: 结束日期 "YYYYMMDD"

        Returns:
            申万行业指数历史数据
        """
        if not self._connected:
            raise RuntimeError("Akshare 未初始化")

        logger.info(f"获取申万行业历史数据: {indicator}")

        def _do_fetch():
            return self._ak.sw_index_daily(indicator=indicator, start_date=start_date, end_date=end_date)

        try:
            df = self._retry_wrapper(_do_fetch)
            if not df.empty:
                logger.info(f"获取到 {len(df)} 条申万行业历史数据")
                df.columns = [c.strip() for c in df.columns]
            return df
        except Exception as e:
            logger.error(f"获取申万行业 {indicator} 历史数据失败: {e}")
            return pd.DataFrame()

    def get_industry_pe_pb(self, industry_name: str) -> Optional[Dict[str, float]]:
        """
        根据行业名称或代码获取 PE/PB

        Args:
            industry_name: 申万二级行业名称或代码（如"航空机场"或"801991.SI"）

        Returns:
            包含 pe_ttm, pb 的字典
        """
        df = self.get_sw_index_second_info()
        if df.empty:
            return None

        # 优先按代码匹配
        row = df[df['行业代码'] == industry_name]

        # 如果不是代码，尝试按名称匹配
        if row.empty:
            row = df[df['行业名称'] == industry_name]

        # 如果精确匹配失败，尝试模糊匹配
        if row.empty:
            row = df[df['行业名称'].str.contains(industry_name, na=False)]

        if not row.empty:
            result = {
                '行业代码': row.iloc[0]['行业代码'],
                '行业名称': row.iloc[0]['行业名称'],
                'pe_ttm': self._safe_float(row.iloc[0]['TTM(滚动)市盈率']) if pd.notna(row.iloc[0]['TTM(滚动)市盈率']) else None,
                'pe_static': self._safe_float(row.iloc[0]['静态市盈率']) if pd.notna(row.iloc[0]['静态市盈率']) else None,
                'pb': self._safe_float(row.iloc[0]['市净率']) if pd.notna(row.iloc[0]['市净率']) else None,
                '股息率': self._safe_float(row.iloc[0]['静态股息率']) if pd.notna(row.iloc[0]['静态股息率']) else None,
                '总市值': None,  # 该接口不提供总市值
            }
            logger.debug(f"行业 {industry_name} 的 PE/PB: {result}")
            return result

        logger.warning(f"未找到行业: {industry_name}")
        return None

    def get_market_industry_list(self) -> pd.DataFrame:
        """
        获取同花顺行业板块列表

        Returns:
            行业板块列表
        """
        if not self._connected:
            raise RuntimeError("Akshare 未初始化")

        logger.info("获取同花顺行业板块列表...")

        try:
            df = self._ak.stock_board_industry_name_em()
            if not df.empty:
                logger.info(f"获取到 {len(df)} 个同花顺行业板块")
                df.columns = [c.strip() for c in df.columns]
            return df
        except Exception as e:
            logger.warning(f"获取同花顺行业板块失败: {e}")
            return pd.DataFrame()

    def get_stock_spot(self, symbol: str = "上证指数") -> Optional[Dict]:
        """
        获取实时行情

        Args:
            symbol: 股票代码或指数代码

        Returns:
            实时行情数据
        """
        if not self._connected:
            raise RuntimeError("Akshare 未初始化")

        try:
            df = self._ak.stock_zh_a_spot_em()
            if not df.empty:
                row = df[df['代码'] == symbol]
                if not row.empty:
                    return row.iloc[0].to_dict()
        except Exception as e:
            logger.warning(f"获取实时行情失败: {e}")

        return None

    def batch_get_sw_industry_pe_pb(self, industry_codes: List[str]) -> pd.DataFrame:
        """
        批量获取多个申万行业的 PE/PB

        Args:
            industry_codes: 申万行业代码列表，如 ["801991.SI", "801017.SI"]

        Returns:
            多个行业的估值数据
        """
        df_all = self.get_sw_index_second_info()
        if df_all.empty:
            return pd.DataFrame()

        # 筛选指定的行业
        df_filtered = df_all[df_all['行业代码'].isin(industry_codes)]

        if df_filtered.empty:
            logger.warning(f"未找到指定的行业代码: {industry_codes}")
            return pd.DataFrame()

        logger.info(f"批量获取 {len(df_filtered)} 个行业的 PE/PB")
        return df_filtered

    def get_sh_index_daily(self, symbol: str = "000001", start_date: str = "20140101", end_date: str = "20241231") -> pd.DataFrame:
        """
        获取沪深指数历史数据

        Args:
            symbol: 指数代码，如 "000001"（上证指数）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            指数历史数据
        """
        if not self._connected:
            raise RuntimeError("Akshare 未初始化")

        logger.info(f"获取沪深指数历史数据: {symbol}")

        try:
            def _do_fetch():
                return self._ak.index_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date)

            df = self._retry_wrapper(_do_fetch)
            if not df.empty:
                logger.info(f"获取到 {len(df)} 条指数历史数据")
                df.columns = [c.strip() for c in df.columns]
            return df
        except Exception as e:
            logger.error(f"获取指数历史数据失败: {e}")
            return pd.DataFrame()
