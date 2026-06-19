"""
Baostock 数据采集器
获取行情数据和财务数据
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger

from .base_collector import BaseCollector


class BaostockCollector(BaseCollector):
    """Baostock 数据采集器"""

    def __init__(self, retry: int = 3, retry_interval: int = 2):
        super().__init__(retry, retry_interval)
        self._bs = None
        self._connected = False

    def connect(self) -> bool:
        """连接 Baostock"""
        try:
            import baostock as bs
            self._bs = bs

            # 登录
            lg = self._bs.login()
            if lg.error_code == '0':
                self._connected = True
                logger.info(f"Baostock 连接成功: {lg.error_msg}")
                return True
            else:
                logger.error(f"Baostock 连接失败: {lg.error_msg}")
                return False

        except ImportError:
            logger.error("请安装 baostock: pip install baostock")
            return False
        except Exception as e:
            logger.error(f"Baostock 连接异常: {e}")
            return False

    def disconnect(self) -> None:
        """断开 Baostock 连接"""
        if self._bs and self._connected:
            try:
                self._bs.logout()
                self._connected = False
                logger.info("Baostock 已断开连接")
            except Exception as e:
                logger.error(f"Baostock 断开连接异常: {e}")

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected

    def _query_wrapper(self, query_func, *args, **kwargs) -> List[Dict]:
        """
        通用的查询包装器

        Args:
            query_func: 查询函数
            *args, **kwargs: 查询参数

        Returns:
            查询结果列表
        """
        def _do_query():
            rs = query_func(*args, **kwargs)
            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())
            return data_list, rs.fields

        data_list, fields = self._retry_wrapper(_do_query)
        if data_list:
            return [dict(zip(fields, row)) for row in data_list]
        return []

    def get_stock_industry(self) -> pd.DataFrame:
        """
        获取所有股票的行业分类

        Returns:
            包含股票代码、名称、行业分类的 DataFrame
        """
        if not self._connected:
            raise RuntimeError("Baostock 未连接")

        logger.info("获取股票行业分类...")
        data = self._query_wrapper(self._bs.query_stock_industry)

        if data:
            df = pd.DataFrame(data)
            logger.info(f"获取到 {len(df)} 只股票的行业分类")
            return df
        else:
            logger.warning("未获取到股票行业分类数据")
            return pd.DataFrame()

    def get_history_kline(
        self,
        code: str,
        start_date: str,
        end_date: str,
        frequency: str = "d",
        fields: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取股票历史K线数据

        Args:
            code: 股票代码，如 "sh.600519" 或 "sz.000001"
            start_date: 开始日期 "YYYY-MM-DD"
            end_date: 结束日期 "YYYY-MM-DD"
            frequency: 数据频率 "d"=日线 "w"=周线 "m"=月线
            fields: 字段列表，逗号分隔

        Returns:
            K线数据 DataFrame
        """
        if not self._connected:
            raise RuntimeError("Baostock 未连接")

        if fields is None:
            fields = "date,code,open,high,low,close,volume,amount"

        logger.info(f"获取K线数据: {code}, {start_date} ~ {end_date}")

        def _do_query():
            return self._bs.query_history_k_data_plus(
                code,
                fields,
                start_date,
                end_date,
                frequency,
                adjustflag="3"  # 前复权
            )

        data = self._query_wrapper(_do_query)

        if data:
            df = pd.DataFrame(data)
            # 转换数值列
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount', 'turn']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            logger.info(f"获取到 {len(df)} 条K线数据")
            return df
        else:
            logger.warning(f"未获取到 {code} 的K线数据")
            return pd.DataFrame()

    def get_profit_data(self, code: str, year: str, quarter: str = "4") -> pd.DataFrame:
        """
        获取个股利润表数据

        Args:
            code: 股票代码，如 "sh.600519"
            year: 年份，如 "2023"
            quarter: 季度 "1" ~ "4"

        Returns:
            利润表数据 DataFrame
        """
        if not self._connected:
            raise RuntimeError("Baostock 未连接")

        logger.info(f"获取利润表数据: {code}, {year}年第{quarter}季度")

        def _do_query():
            return self._bs.query_profit_data(code, year, quarter)

        data = self._query_wrapper(_do_query)

        if data:
            df = pd.DataFrame(data)
            logger.info(f"获取到 {len(df)} 条利润表数据")
            return df
        else:
            logger.warning(f"未获取到 {code} 的利润表数据")
            return pd.DataFrame()

    def get_quarterly_profit_rate(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取季频利润率数据

        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            季频利润率数据
        """
        if not self._connected:
            raise RuntimeError("Baostock 未连接")

        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365 * 5)).strftime("%Y-%m-%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"获取季频利润率: {code}")

        def _do_query():
            return self._bs.query_quarterly_profit_rate(code, start_date, end_date)

        data = self._query_wrapper(_do_query)

        if data:
            df = pd.DataFrame(data)
            logger.info(f"获取到 {len(df)} 条季频利润率数据")
            return df
        else:
            logger.warning(f"未获取到 {code} 的季频利润率数据")
            return pd.DataFrame()

    def get_hs300_stocks(self) -> pd.DataFrame:
        """
        获取沪深300成分股

        Returns:
            沪深300成分股列表
        """
        if not self._connected:
            raise RuntimeError("Baostock 未连接")

        logger.info("获取沪深300成分股...")

        data = self._query_wrapper(self._bs.query_hs300_stocks)

        if data:
            df = pd.DataFrame(data)
            logger.info(f"获取到 {len(df)} 只沪深300成分股")
            return df
        else:
            logger.warning("未获取到沪深300成分股数据")
            return pd.DataFrame()

    def get_stocks_by_industry(self, industry_code: str) -> List[str]:
        """
        根据行业代码获取成分股列表

        Args:
            industry_code: Baostock 行业代码，如 "G56"

        Returns:
            股票代码列表
        """
        df = self.get_stock_industry()
        if df.empty:
            return []

        # 过滤指定行业的股票
        # 使用列名代替列索引，避免依赖列顺序
        if 'industry' in df.columns and 'code' in df.columns:
            mask = df['industry'].str.contains(industry_code, na=False)
            stocks = df.loc[mask, 'code'].tolist()
        else:
            # Fallback: 使用列索引（兼容旧代码）
            stocks = df[df.iloc[:, 3].str.contains(industry_code, na=False)][df.columns[1]].tolist()
        logger.info(f"行业 {industry_code} 包含 {len(stocks)} 只股票")
        return stocks

    def batch_get_profit(
        self,
        codes: List[str],
        years: List[str],
        quarter: str = "4"
    ) -> Dict[str, pd.DataFrame]:
        """
        批量获取多只股票的利润数据

        Args:
            codes: 股票代码列表
            years: 年份列表
            quarter: 季度

        Returns:
            {股票代码: 利润表DataFrame}
        """
        results = {}
        for code in codes:
            for year in years:
                try:
                    df = self.get_profit_data(code, year, quarter)
                    if not df.empty:
                        if code not in results:
                            results[code] = df
                        else:
                            # 合并并去重
                            results[code] = pd.concat([results[code], df], ignore_index=True).drop_duplicates()
                except Exception as e:
                    logger.warning(f"获取 {code} {year} 年利润数据失败: {e}")

        return results
