"""
行业历史 PE/PB 计算器
基于申万行业数据计算历史分位
"""

from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from loguru import logger

from .collectors.akshare_collector import AkshareCollector
from .collectors.baostock_collector import BaostockCollector


class IndustryPEPBHistoryCalculator:
    """
    行业历史 PE/PB 计算器

    ⚠️ 重要说明 - 估值分位计算方法：

    由于申万官方不提供历史 PE/PB 数据，我们采用以下近似方案：

    【主要方案】使用点位分位作为估值代理
    - 原理：行业点位反映了成分股价格加权表现，与估值有一定相关性
    - 适用场景：行业整体盈利稳定时
    - 局限性：盈利大幅波动时可能失真

    【备选方案】使用 PB 分位
    - PB（ 市净率）比 PE 更稳定，受盈利波动影响小
    - 当有成分股 PB 数据时，可计算 PB 分位作为更准确的估值指标

    【说明】
    - 点位分位是"近似估算"，非精确的估值分位
    - 对于盈利稳定的成熟行业，近似效果较好
    - 对于盈利周期波动大的强周期行业，建议参考 PB 分位

    使用建议：
    1. 优先参考 PB 分位（更准确）
    2. 点位分位作为参考，用于验证一致性
    3. 两者背离时，需要人工判断
    """

    def __init__(
        self,
        akshare_collector: Optional[AkshareCollector] = None,
        baostock_collector: Optional[BaostockCollector] = None,
        history_years: int = 10
    ):
        """
        初始化计算器

        Args:
            akshare_collector: AkshareCollector 实例
            baostock_collector: BaostockCollector 实例
            history_years: 历史数据年数
        """
        self._ak = akshare_collector or AkshareCollector()
        self._baostock = baostock_collector
        self.history_years = history_years

        # 缓存
        self._current_pe_pb_cache: Optional[pd.DataFrame] = None
        self._index_history_cache: Dict[str, pd.DataFrame] = {}

    def connect(self) -> bool:
        """连接数据源"""
        return self._ak.connect()

    def disconnect(self) -> None:
        """断开连接"""
        self._ak.disconnect()
        if self._baostock:
            self._baostock.disconnect()

    def get_current_pe_pb(self, sw_index_code: str) -> Optional[Dict]:
        """
        获取当前申万行业 PE/PB

        Args:
            sw_index_code: 申万行业代码，如 "801991.SI"

        Returns:
            包含当前 PE/PB 的字典
        """
        # 使用缓存
        if self._current_pe_pb_cache is None:
            self._current_pe_pb_cache = self._ak.get_sw_index_second_info()

        if self._current_pe_pb_cache.empty:
            return None

        # 匹配指定行业
        row = self._current_pe_pb_cache[
            self._current_pe_pb_cache['行业代码'] == sw_index_code
        ]

        if row.empty:
            logger.warning(f"未找到申万行业: {sw_index_code}")
            return None

        result = {
            '行业代码': sw_index_code,
            '行业名称': row.iloc[0]['行业名称'],
            'pe_ttm': self._safe_float(row.iloc[0]['TTM(滚动)市盈率']),
            'pe_static': self._safe_float(row.iloc[0]['静态市盈率']),
            'pb': self._safe_float(row.iloc[0]['市净率']),
            '股息率': self._safe_float(row.iloc[0]['静态股息率']),
            'update_time': datetime.now(),
        }

        return result

    def get_industry_index_history(self, sw_index_code: str) -> pd.DataFrame:
        """
        获取申万行业指数历史数据

        Args:
            sw_index_code: 申万行业代码

        Returns:
            行业指数历史 DataFrame
        """
        # 使用缓存
        if sw_index_code in self._index_history_cache:
            return self._index_history_cache[sw_index_code]

        # 计算日期范围
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=365 * self.history_years)).strftime("%Y%m%d")

        df = self._ak.get_sw_index_daily(sw_index_code, start_date, end_date)

        if not df.empty:
            # 确保日期列是 datetime 类型
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            self._index_history_cache[sw_index_code] = df
            logger.info(f"缓存行业 {sw_index_code} 的 {len(df)} 条历史数据")

        return df

    def calculate_percentile(
        self,
        sw_index_code: str,
        current_value: Optional[float] = None,
        field: str = 'close'
    ) -> Dict[str, float]:
        """
        计算当前点位在历史中的分位

        Args:
            sw_index_code: 申万行业代码
            current_value: 当前点位（可选，不提供则取最新）
            field: 用于计算分位的字段

        Returns:
            包含分位值的字典
        """
        df = self.get_industry_index_history(sw_index_code)

        if df.empty:
            logger.warning(f"无法获取行业 {sw_index_code} 的历史数据")
            return {'percentile': None, 'current': None, 'history_min': None, 'history_max': None}

        # 获取当前值
        if current_value is None:
            current_value = df[field].iloc[-1]

        # 获取历史值
        history_values = df[field].dropna()

        if len(history_values) < 10:
            logger.warning(f"历史数据不足，无法计算分位")
            return {'percentile': None, 'current': current_value, 'history_min': None, 'history_max': None}

        # 计算分位
        percentile = (history_values < current_value).sum() / len(history_values) * 100

        result = {
            'percentile': round(percentile, 2),
            'current': round(current_value, 2),
            'history_min': round(history_values.min(), 2),
            'history_max': round(history_values.max(), 2),
            'history_mean': round(history_values.mean(), 2),
            'history_std': round(history_values.std(), 2),
            'data_points': len(history_values),
        }

        logger.debug(f"行业 {sw_index_code} 当前 {field}={current_value:.2f}, 分位={percentile:.1f}%")

        return result

    def calculate_pe_pb_percentile(self, sw_index_code: str) -> Dict:
        """
        计算行业 PE/PB 的历史分位

        Args:
            sw_index_code: 申万行业代码

        Returns:
            包含 PE/PB 分位的字典
        """
        # 获取当前 PE/PB
        current_data = self.get_current_pe_pb(sw_index_code)

        if current_data is None:
            return {}

        # 获取历史点位
        index_data = self.get_industry_index_history(sw_index_code)

        if index_data.empty:
            return current_data

        # 计算点位分位（作为估值的代理）
        pe_pb_percentile = self.calculate_percentile(sw_index_code, field='close')

        result = {
            **current_data,
            '点位分位': pe_pb_percentile.get('percentile'),
            '点位历史最低': pe_pb_percentile.get('history_min'),
            '点位历史最高': pe_pb_percentile.get('history_max'),
            '点位历史均值': pe_pb_percentile.get('history_mean'),
            '点位历史标准差': pe_pb_percentile.get('history_std'),
            '数据点数': pe_pb_percentile.get('data_points'),
        }

        return result

    def batch_calculate_pe_pb_percentile(
        self,
        sw_index_codes: List[str]
    ) -> List[Dict]:
        """
        批量计算多个行业的 PE/PB 分位

        Args:
            sw_index_codes: 申万行业代码列表

        Returns:
            各行业的 PE/PB 分位数据列表
        """
        results = []

        for code in sw_index_codes:
            try:
                data = self.calculate_pe_pb_percentile(code)
                if data:
                    results.append(data)
            except Exception as e:
                logger.error(f"计算行业 {code} 的 PE/PB 分位失败: {e}")

        logger.info(f"批量计算完成: {len(results)}/{len(sw_index_codes)} 个行业")
        return results

    def get_trend(
        self,
        sw_index_code: str,
        window: int = 12,
        field: str = 'close'
    ) -> Dict:
        """
        获取行业趋势（移动平均）

        Args:
            sw_index_code: 申万行业代码
            window: 窗口大小（周）
            field: 字段名

        Returns:
            趋势数据
        """
        df = self.get_industry_index_history(sw_index_code)

        if df.empty:
            return {}

        # 计算移动平均
        df['ma'] = df[field].rolling(window=window, min_periods=1).mean()

        # 计算变化率
        df['pct_change'] = df[field].pct_change(periods=window)

        # 获取最新趋势
        current = df[field].iloc[-1]
        ma_current = df['ma'].iloc[-1]
        pct_change = df['pct_change'].iloc[-1]

        # 判断趋势
        if current > ma_current:
            trend = "上涨" if pct_change > 0 else "反弹"
        else:
            trend = "下跌" if pct_change < 0 else "调整"

        return {
            '当前值': round(current, 2),
            '移动平均': round(ma_current, 2),
            '窗口变化率': round(pct_change * 100, 2) if pd.notna(pct_change) else None,
            '趋势': trend,
        }

    def get_divergence_signal(
        self,
        sw_index_code: str,
        price_window: int = 12,
        valuation_window: int = 12
    ) -> Dict:
        """
        检测价格-估值背离信号

        Args:
            sw_index_code: 申万行业代码
            price_window: 价格趋势窗口
            valuation_window: 估值趋势窗口

        Returns:
            背离信号
        """
        # 获取当前数据
        current_data = self.calculate_pe_pb_percentile(sw_index_code)

        if not current_data:
            return {}

        # 获取价格趋势
        price_trend = self.get_trend(sw_index_code, window=price_window)

        # 获取估值趋势
        valuation_trend = self.get_trend(sw_index_code, window=valuation_window)

        # 判断背离
        # 背离定义：价格下跌但估值分位上升，或价格上涨但估值分位下降
        price_change = price_trend.get('窗口变化率', 0)
        valuation_change = current_data.get('点位分位', 50) - 50  # 相对于中位的偏移

        # 信号判定
        if price_change < 0 and valuation_change > 10:
            signal = "正向背离（价格跌+估值升）= 潜在机会"
        elif price_change > 0 and valuation_change < -10:
            signal = "负向背离（价格涨+估值降）= 需要谨慎"
        else:
            signal = "无明显背离"

        return {
            '行业代码': sw_index_code,
            '行业名称': current_data.get('行业名称'),
            'PE(TTM)': current_data.get('pe_ttm'),
            'PB': current_data.get('pb'),
            '点位分位': current_data.get('点位分位'),
            '价格趋势': price_trend.get('趋势'),
            '价格变化': price_change,
            '估值趋势': valuation_trend.get('趋势'),
            '背离信号': signal,
        }

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """安全转换为浮点数"""
        if value is None or pd.isna(value):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def clear_cache(self) -> None:
        """清空缓存"""
        self._current_pe_pb_cache = None
        self._index_history_cache.clear()
        logger.debug("PE/PB 计算器缓存已清空")
