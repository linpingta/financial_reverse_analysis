"""
宏观数据采集器
获取 PMI、CPI、PPI、M2 等宏观指标
"""

from typing import Optional, Dict, List
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger

from .base_collector import BaseCollector


class MacroCollector(BaseCollector):
    """宏观数据采集器（基于 Akshare）"""

    # 宏观指标配置
    MACRO_INDICATORS = {
        'pmi': {
            'api': 'macro_china_pmi',
            'name': '中国PMI',
            'direction': 'positive',  # 上升为利好
        },
        'cpi': {
            'api': 'macro_china_cpi',
            'name': '中国CPI',
            'direction': 'neutral',
        },
        'ppi': {
            'api': 'macro_china_ppi',
            'name': '中国PPI',
            'direction': 'positive',  # 上升为利好
        },
        'm2': {
            'api': 'macro_china_money_supply',
            'name': '货币供应量M2',
            'direction': 'positive',
        },
        'gdp': {
            'api': 'macro_china_gdp',
            'name': '中国GDP',
            'direction': 'positive',
        },
        'industrial_profit': {
            'api': 'macro_china_industrial_enterprise_profit',
            'name': '工业企业利润',
            'direction': 'positive',
        },
    }

    def __init__(self, akshare_collector=None, retry: int = 3, retry_interval: int = 5):
        """
        初始化宏观数据采集器

        Args:
            akshare_collector: AkshareCollector 实例
            retry: 重试次数
            retry_interval: 重试间隔（秒）
        """
        super().__init__(retry, retry_interval)
        self._ak = akshare_collector
        self._cache: Dict[str, pd.DataFrame] = {}

    def connect(self) -> bool:
        """连接 Akshare（如果未提供则初始化）"""
        if self._ak is None:
            from .akshare_collector import AkshareCollector
            self._ak = AkshareCollector()

        return self._ak.connect()

    def disconnect(self) -> None:
        """断开连接"""
        if self._ak:
            self._ak.disconnect()
        self._cache.clear()

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._ak is not None and self._ak.is_connected()

    def _get_api(self, api_name: str):
        """获取 API 函数"""
        if self._ak is None or self._ak._ak is None:
            raise RuntimeError("Akshare 未初始化")
        return getattr(self._ak._ak, api_name, None)

    def get_pmi(self) -> Optional[pd.DataFrame]:
        """
        获取中国 PMI 数据

        Returns:
            PMI 数据 DataFrame
        """
        logger.info("获取 PMI 数据...")

        # 检查缓存
        if 'pmi' in self._cache:
            return self._cache['pmi']

        try:
            api = self._get_api('macro_china_pmi')
            if api is None:
                logger.error("macro_china_pmi API 不存在")
                return None

            def _do_fetch():
                return api()

            df = self._retry_wrapper(_do_fetch)

            if not df.empty:
                self._cache['pmi'] = df
                logger.info(f"获取到 {len(df)} 条 PMI 数据")
            return df

        except Exception as e:
            logger.error(f"获取 PMI 数据失败: {e}")
            return None

    def get_cpi(self) -> Optional[pd.DataFrame]:
        """
        获取中国 CPI 数据

        Returns:
            CPI 数据 DataFrame
        """
        logger.info("获取 CPI 数据...")

        if 'cpi' in self._cache:
            return self._cache['cpi']

        try:
            api = self._get_api('macro_china_cpi')
            if api is None:
                logger.error("macro_china_cpi API 不存在")
                return None

            def _do_fetch():
                return api()

            df = self._retry_wrapper(_do_fetch)

            if not df.empty:
                self._cache['cpi'] = df
                logger.info(f"获取到 {len(df)} 条 CPI 数据")
            return df

        except Exception as e:
            logger.error(f"获取 CPI 数据失败: {e}")
            return None

    def get_ppi(self) -> Optional[pd.DataFrame]:
        """
        获取中国 PPI 数据

        Returns:
            PPI 数据 DataFrame
        """
        logger.info("获取 PPI 数据...")

        if 'ppi' in self._cache:
            return self._cache['ppi']

        try:
            api = self._get_api('macro_china_ppi')
            if api is None:
                logger.error("macro_china_ppi API 不存在")
                return None

            def _do_fetch():
                return api()

            df = self._retry_wrapper(_do_fetch)

            if not df.empty:
                self._cache['ppi'] = df
                logger.info(f"获取到 {len(df)} 条 PPI 数据")
            return df

        except Exception as e:
            logger.error(f"获取 PPI 数据失败: {e}")
            return None

    def get_money_supply(self) -> Optional[pd.DataFrame]:
        """
        获取货币供应量数据

        Returns:
            M0、M1、M2 数据
        """
        logger.info("获取货币供应量数据...")

        if 'm2' in self._cache:
            return self._cache['m2']

        try:
            api = self._get_api('macro_china_money_supply')
            if api is None:
                logger.error("macro_china_money_supply API 不存在")
                return None

            def _do_fetch():
                return api()

            df = self._retry_wrapper(_do_fetch)

            if not df.empty:
                self._cache['m2'] = df
                logger.info(f"获取到 {len(df)} 条货币供应量数据")
            return df

        except Exception as e:
            logger.error(f"获取货币供应量数据失败: {e}")
            return None

    def get_industrial_profit(self) -> Optional[pd.DataFrame]:
        """
        获取工业企业利润数据

        Returns:
            工业企业利润数据
        """
        logger.info("获取工业企业利润数据...")

        if 'industrial_profit' in self._cache:
            return self._cache['industrial_profit']

        try:
            api = self._get_api('macro_china_industrial_enterprise_profit')
            if api is None:
                logger.error("macro_china_industrial_enterprise_profit API 不存在")
                return None

            def _do_fetch():
                return api()

            df = self._retry_wrapper(_do_fetch)

            if not df.empty:
                self._cache['industrial_profit'] = df
                logger.info(f"获取到 {len(df)} 条工业企业利润数据")
            return df

        except Exception as e:
            logger.error(f"获取工业企业利润数据失败: {e}")
            return None

    def get_gdp(self) -> Optional[pd.DataFrame]:
        """
        获取 GDP 数据

        Returns:
            GDP 数据
        """
        logger.info("获取 GDP 数据...")

        if 'gdp' in self._cache:
            return self._cache['gdp']

        try:
            api = self._get_api('macro_china_gdp')
            if api is None:
                logger.error("macro_china_gdp API 不存在")
                return None

            def _do_fetch():
                return api()

            df = self._retry_wrapper(_do_fetch)

            if not df.empty:
                self._cache['gdp'] = df
                logger.info(f"获取到 {len(df)} 条 GDP 数据")
            return df

        except Exception as e:
            logger.error(f"获取 GDP 数据失败: {e}")
            return None

    def get_all_macro_data(self) -> Dict[str, pd.DataFrame]:
        """
        获取所有宏观数据

        Returns:
            各种宏观数据的字典
        """
        results = {}

        # PMI
        pmi_df = self.get_pmi()
        if pmi_df is not None and not pmi_df.empty:
            results['pmi'] = pmi_df

        # CPI
        cpi_df = self.get_cpi()
        if cpi_df is not None and not cpi_df.empty:
            results['cpi'] = cpi_df

        # PPI
        ppi_df = self.get_ppi()
        if ppi_df is not None and not ppi_df.empty:
            results['ppi'] = ppi_df

        # M2
        m2_df = self.get_money_supply()
        if m2_df is not None and not m2_df.empty:
            results['m2'] = m2_df

        # GDP
        gdp_df = self.get_gdp()
        if gdp_df is not None and not gdp_df.empty:
            results['gdp'] = gdp_df

        # 工业企业利润
        profit_df = self.get_industrial_profit()
        if profit_df is not None and not profit_df.empty:
            results['industrial_profit'] = profit_df

        logger.info(f"成功获取 {len(results)} 种宏观数据")
        return results

    def get_latest_macro(self) -> Dict[str, Optional[Dict]]:
        """
        获取最新一期宏观数据

        Returns:
            各种宏观指标的最新值
        """
        latest = {}

        # PMI
        pmi_df = self.get_pmi()
        if pmi_df is not None and not pmi_df.empty:
            latest['pmi'] = pmi_df.iloc[0].to_dict()

        # CPI
        cpi_df = self.get_cpi()
        if cpi_df is not None and not cpi_df.empty:
            latest['cpi'] = cpi_df.iloc[0].to_dict()

        # PPI
        ppi_df = self.get_ppi()
        if ppi_df is not None and not ppi_df.empty:
            latest['ppi'] = ppi_df.iloc[0].to_dict()

        # M2
        m2_df = self.get_money_supply()
        if m2_df is not None and not m2_df.empty:
            latest['m2'] = m2_df.iloc[0].to_dict()

        # GDP
        gdp_df = self.get_gdp()
        if gdp_df is not None and not gdp_df.empty:
            latest['gdp'] = gdp_df.iloc[0].to_dict()

        # 工业企业利润
        profit_df = self.get_industrial_profit()
        if profit_df is not None and not profit_df.empty:
            latest['industrial_profit'] = profit_df.iloc[0].to_dict()

        logger.info(f"获取到 {len(latest)} 项最新宏观数据")
        return latest

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
        logger.debug("宏观数据缓存已清空")
