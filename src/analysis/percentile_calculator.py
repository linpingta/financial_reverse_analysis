"""
分位计算器模块

计算指标在历史数据中的分位位置，用于判断当前估值水平
"""

from typing import Optional, Dict, List, Any
import numpy as np
import pandas as pd
from datetime import datetime
from loguru import logger


class PercentileCalculator:
    """
    分位计算器

    支持单指标和多指标的分位计算，处理边界情况
    """

    def __init__(self, history_years: int = 10, min_data_points: int = 520):
        """
        初始化分位计算器

        Args:
            history_years: 历史数据年限（用于计算期望最小数据点）
            min_data_points: 最小数据点数要求
                             - 10年 * 52周 = 520（周数据）
                             - 低于此值不计算分位或降低置信度
        """
        self.history_years = history_years
        # 自动计算期望的最小数据点数：history_years * 52
        self.min_data_points = min_data_points or (history_years * 52)
        self._cache: Dict[str, pd.DataFrame] = {}

    def calculate_single_percentile(
        self,
        data_series: pd.Series,
        current_value: Optional[float] = None,
        method: str = 'rank',
        use_dynamic_window: bool = True
    ) -> Dict[str, Any]:
        """
        计算单个指标的分位

        Args:
            data_series: 历史数据序列
            current_value: 当前值（可选，不提供则取序列最后一个值）
            method: 计算方法 ('rank' 或 'cdf')
            use_dynamic_window: 是否使用动态窗口调整（数据不足时降低阈值）

        Returns:
            分位计算结果字典
        """
        # 数据预处理
        data = data_series.dropna()
        data_len = len(data)

        # 获取当前值
        if current_value is None:
            current_value = data.iloc[-1] if not data.empty else None

        if current_value is None:
            logger.warning("当前值为空")
            return self._create_empty_result(None)

        # 动态窗口调整机制
        window_adjusted = False
        effective_min_points = self.min_data_points

        if data_len < self.min_data_points:
            if use_dynamic_window and data_len >= 52:  # 至少1年数据
                # 动态降低阈值：使用实际可用的数据点
                effective_min_points = data_len
                window_adjusted = True
                logger.info(f"数据点不足 ({data_len} < {self.min_data_points})，"
                           f"启用动态窗口，使用 {data_len} 个数据点计算")
            else:
                logger.warning(f"数据点严重不足 ({data_len} < {self.min_data_points})，无法计算分位")
                result = self._create_empty_result(current_value)
                result['data_insufficient'] = True
                result['data_points'] = data_len
                result['required_points'] = self.min_data_points
                return result

        # 计算分位
        if method == 'cdf':
            # 使用CDF方法
            sorted_data = np.sort(data)
            percentile = np.searchsorted(sorted_data, current_value, side='right') / len(sorted_data) * 100
        else:
            # 使用排名方法（默认）
            percentile = (data < current_value).sum() / len(data) * 100

        # 计算统计量
        result = {
            'percentile': round(percentile, 2),
            'current_value': round(current_value, 2),
            'history_min': round(data.min(), 2),
            'history_max': round(data.max(), 2),
            'history_mean': round(data.mean(), 2),
            'history_median': round(data.median(), 2),
            'history_std': round(data.std(), 2),
            'data_points': data_len,
            'method': method,
            'confidence': self._calculate_confidence(data_len),
            'window_adjusted': window_adjusted,  # 标记是否启用了动态窗口
        }

        logger.debug(f"分位计算完成: 当前值={current_value:.2f}, 分位={percentile:.2f}%")
        return result

    def calculate_multiple_percentiles(
        self,
        data_df: pd.DataFrame,
        fields: List[str],
        current_values: Optional[Dict[str, float]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        批量计算多个指标的分位

        Args:
            data_df: 包含多个指标的 DataFrame
            fields: 要计算的字段列表
            current_values: 当前值字典（可选）

        Returns:
            各指标分位结果字典
        """
        results = {}
        current_values = current_values or {}

        for field in fields:
            if field not in data_df.columns:
                logger.warning(f"字段 {field} 不存在于数据中")
                continue

            try:
                current_val = current_values.get(field)
                results[field] = self.calculate_single_percentile(
                    data_df[field],
                    current_value=current_val
                )
            except Exception as e:
                logger.error(f"计算字段 {field} 分位失败: {e}")
                results[field] = {'percentile': None, 'error': str(e)}

        return results

    def calculate_pe_pb_percentile(
        self,
        pe_history: Optional[pd.Series] = None,
        pb_history: Optional[pd.Series] = None,
        current_pe: Optional[float] = None,
        current_pb: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        计算 PE/PB 分位

        Args:
            pe_history: PE 历史序列
            pb_history: PB 历史序列
            current_pe: 当前 PE 值
            current_pb: 当前 PB 值

        Returns:
            PE/PB 分位结果
        """
        result = {}

        # 计算 PE 分位
        if pe_history is not None and not pe_history.empty:
            pe_result = self.calculate_single_percentile(pe_history, current_pe)
            result['pe'] = pe_result
        else:
            result['pe'] = {'percentile': None, 'reason': '缺少 PE 历史数据'}

        # 计算 PB 分位
        if pb_history is not None and not pb_history.empty:
            pb_result = self.calculate_single_percentile(pb_history, current_pb)
            result['pb'] = pb_result
        else:
            result['pb'] = {'percentile': None, 'reason': '缺少 PB 历史数据'}

        # 综合分位（取 PE 和 PB 的平均）
        pe_pct = result['pe'].get('percentile')
        pb_pct = result['pb'].get('percentile')
        valid_pct = [p for p in [pe_pct, pb_pct] if p is not None]

        if valid_pct:
            result['combined_percentile'] = round(sum(valid_pct) / len(valid_pct), 2)
        else:
            result['combined_percentile'] = None

        return result

    def _calculate_confidence(self, data_points: int) -> float:
        """
        根据数据点数量计算置信度

        Args:
            data_points: 数据点数量

        Returns:
            置信度 (0-100)
        """
        if data_points < self.min_data_points:
            return 0.0
        if data_points >= 5 * self.min_data_points:  # 5年周数据
            return 100.0
        # 线性插值
        return min(100.0, (data_points / (5 * self.min_data_points)) * 100)

    def _create_empty_result(self, current_value: Optional[float]) -> Dict[str, Any]:
        """
        创建空结果（数据不足时使用）

        Args:
            current_value: 当前值

        Returns:
            空结果字典
        """
        return {
            'percentile': None,
            'current_value': round(current_value, 2) if current_value else None,
            'history_min': None,
            'history_max': None,
            'history_mean': None,
            'history_median': None,
            'history_std': None,
            'data_points': 0,
            'method': None,
            'confidence': 0.0,
        }

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
        logger.debug("分位计算器缓存已清空")