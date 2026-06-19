"""
背离分析引擎

检测价格与估值、价格与景气度之间的背离信号
"""

from typing import Optional, Dict, Any
import pandas as pd
from enum import Enum
from loguru import logger


class DivergenceType(Enum):
    """背离类型枚举"""
    NONE = "无背离"
    BULLISH = "正向背离"  # 价格跌+估值升 → 潜在买入机会
    BEARISH = "负向背离"  # 价格涨+估值降 → 潜在卖出信号
    WEAK_BULLISH = "弱正向背离"
    WEAK_BEARISH = "弱负向背离"


class DivergenceAnalyzer:
    """
    背离分析引擎

    检测多种背离类型：
    1. 价格-估值背离：价格趋势与估值分位趋势不一致
    2. 价格-景气背离：价格趋势与宏观景气指标趋势不一致
    """

    def __init__(self, divergence_threshold: float = 10.0, weak_threshold: float = 5.0):
        """
        初始化背离分析引擎

        Args:
            divergence_threshold: 背离阈值（百分点）
            weak_threshold: 弱背离阈值（百分点）
        """
        self.divergence_threshold = divergence_threshold
        self.weak_threshold = weak_threshold

    def analyze_price_valuation_divergence(
        self,
        price_change: float,
        valuation_percentile_change: float
    ) -> Dict[str, Any]:
        """
        分析价格-估值背离

        Args:
            price_change: 价格变化率（百分比）
            valuation_percentile_change: 估值分位变化（百分点）

        Returns:
            背离分析结果
        """
        # 判断背离类型
        if price_change < -self.weak_threshold and valuation_percentile_change > self.weak_threshold:
            if price_change < -self.divergence_threshold and valuation_percentile_change > self.divergence_threshold:
                divergence_type = DivergenceType.BULLISH
                strength = self._calculate_strength(price_change, valuation_percentile_change)
            else:
                divergence_type = DivergenceType.WEAK_BULLISH
                strength = self._calculate_strength(price_change, valuation_percentile_change) * 0.5
        elif price_change > self.weak_threshold and valuation_percentile_change < -self.weak_threshold:
            if price_change > self.divergence_threshold and valuation_percentile_change < -self.divergence_threshold:
                divergence_type = DivergenceType.BEARISH
                strength = self._calculate_strength(price_change, valuation_percentile_change)
            else:
                divergence_type = DivergenceType.WEAK_BEARISH
                strength = self._calculate_strength(price_change, valuation_percentile_change) * 0.5
        else:
            divergence_type = DivergenceType.NONE
            strength = 0.0

        return {
            'divergence_type': divergence_type.value,
            'divergence_code': divergence_type.name,
            'price_change': round(price_change, 2),
            'valuation_change': round(valuation_percentile_change, 2),
            'strength': round(strength, 2),
            'strength_level': self._get_strength_level(strength),
            'signal': self._get_signal(divergence_type),
        }

    def analyze_price_macro_divergence(
        self,
        price_change: float,
        macro_indicator_change: float,
        macro_name: str = "PMI"
    ) -> Dict[str, Any]:
        """
        分析价格-宏观景气背离

        Args:
            price_change: 价格变化率（百分比）
            macro_indicator_change: 宏观指标变化
            macro_name: 宏观指标名称

        Returns:
            背离分析结果
        """
        # 宏观指标上升通常意味着基本面改善
        # 如果宏观指标上升但价格下跌，可能是逆向投资机会

        if macro_indicator_change > self.weak_threshold and price_change < -self.weak_threshold:
            if macro_indicator_change > self.divergence_threshold and price_change < -self.divergence_threshold:
                divergence_type = DivergenceType.BULLISH
                strength = self._calculate_strength(macro_indicator_change, -price_change)
            else:
                divergence_type = DivergenceType.WEAK_BULLISH
                strength = self._calculate_strength(macro_indicator_change, -price_change) * 0.5
        elif macro_indicator_change < -self.weak_threshold and price_change > self.weak_threshold:
            if macro_indicator_change < -self.divergence_threshold and price_change > self.divergence_threshold:
                divergence_type = DivergenceType.BEARISH
                strength = self._calculate_strength(-macro_indicator_change, price_change)
            else:
                divergence_type = DivergenceType.WEAK_BEARISH
                strength = self._calculate_strength(-macro_indicator_change, price_change) * 0.5
        else:
            divergence_type = DivergenceType.NONE
            strength = 0.0

        return {
            'divergence_type': divergence_type.value,
            'divergence_code': divergence_type.name,
            'price_change': round(price_change, 2),
            'macro_indicator': macro_name,
            'macro_change': round(macro_indicator_change, 2),
            'strength': round(strength, 2),
            'strength_level': self._get_strength_level(strength),
            'signal': self._get_signal(divergence_type),
        }

    def analyze_multi_dimensional_divergence(
        self,
        price_change: float,
        valuation_percentile: float,
        macro_data: Optional[Dict[str, float]] = None,
        industry_data: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        多维背离分析

        Args:
            price_change: 价格变化率
            valuation_percentile: 当前估值分位
            macro_data: 宏观数据字典
            industry_data: 行业特定数据字典

        Returns:
            综合背离分析结果
        """
        results = {
            'price_valuation': None,
            'price_macro': None,
            'composite_signal': '观望',
            'composite_strength': 0.0,
            'factors': [],
        }

        # 价格-估值背离分析
        # 估值分位相对于中位的偏移作为变化指标
        valuation_deviation = valuation_percentile - 50
        pv_result = self.analyze_price_valuation_divergence(price_change, valuation_deviation)
        results['price_valuation'] = pv_result
        results['factors'].append({
            'type': 'price_valuation',
            'signal': pv_result['signal'],
            'strength': pv_result['strength'],
        })

        # 价格-宏观背离分析
        if macro_data:
            # 使用 PMI 作为景气度代理指标
            pmi_change = macro_data.get('pmi_change', 0)
            pm_result = self.analyze_price_macro_divergence(price_change, pmi_change, "PMI")
            results['price_macro'] = pm_result
            results['factors'].append({
                'type': 'price_macro',
                'signal': pm_result['signal'],
                'strength': pm_result['strength'],
            })

        # 综合信号判定
        signals = [f['signal'] for f in results['factors'] if f['signal'] != '观望']
        strengths = [f['strength'] for f in results['factors'] if f['strength'] > 0]

        if signals:
            # 多数决原则
            bullish_count = sum(1 for s in signals if s == '买入机会')
            bearish_count = sum(1 for s in signals if s == '卖出预警')

            if bullish_count > bearish_count:
                results['composite_signal'] = '买入机会'
            elif bearish_count > bullish_count:
                results['composite_signal'] = '卖出预警'
            else:
                results['composite_signal'] = '观望'

            if strengths:
                results['composite_strength'] = round(sum(strengths) / len(strengths), 2)

        return results

    def _calculate_strength(self, change1: float, change2: float) -> float:
        """
        计算背离强度

        Args:
            change1: 变化量1
            change2: 变化量2

        Returns:
            强度值 (0-100)
        """
        # 取绝对值计算强度
        abs1 = abs(change1)
        abs2 = abs(change2)

        # 基础强度
        base_strength = min((abs1 + abs2) / 2, 50)

        # 协同系数：两个变化方向相反且幅度相当
        if abs1 > 0 and abs2 > 0:
            synergy = min(abs1 / abs2, abs2 / abs1) * 50
        else:
            synergy = 0

        return min(100.0, base_strength + synergy)

    def _get_strength_level(self, strength: float) -> str:
        """
        根据强度值获取强度等级

        Args:
            strength: 强度值

        Returns:
            强度等级
        """
        if strength >= 80:
            return "极强"
        elif strength >= 60:
            return "强"
        elif strength >= 40:
            return "中等"
        elif strength >= 20:
            return "弱"
        else:
            return "无"

    def _get_signal(self, divergence_type: DivergenceType) -> str:
        """
        根据背离类型获取交易信号

        Args:
            divergence_type: 背离类型

        Returns:
            交易信号
        """
        if divergence_type in (DivergenceType.BULLISH, DivergenceType.WEAK_BULLISH):
            return "买入机会"
        elif divergence_type in (DivergenceType.BEARISH, DivergenceType.WEAK_BEARISH):
            return "卖出预警"
        else:
            return "观望"