"""
背离分析引擎

检测价格与估值、价格与景气度之间的背离信号

设计文档核心逻辑（3.2条）：
- 逆向买点背离：基本面（景气度）跌至历史最差，但股价未同步创新低
                核心条件：价格分位 > 景气度分位
- 逆向卖点背离：基本面升至历史最优，但股价持续走弱
                核心条件：景气度分位 >= 80% 且近3/12月指数持续下跌
"""

from typing import Optional, Dict, Any
import pandas as pd
from enum import Enum
from loguru import logger


class DivergenceType(Enum):
    """背离类型枚举（与设计文档 3.2 条对应）"""
    NONE = "无背离"
    # 正向背离（买入机会）
    BULLISH = "正向背离"           # 价格跌+估值升 或 价格分位>景气度分位
    WEAK_BULLISH = "弱正向背离"
    # 逆向买点背离（设计文档核心）
    REVERSE_BUY = "逆向买点背离"     # 价格分位 > 景气度分位（基本面已见底，股价未创新低）
    # 负向背离（卖出预警）
    BEARISH = "负向背离"           # 价格涨+估值降
    WEAK_BEARISH = "弱负向背离"
    # 逆向卖点背离（设计文档核心）
    REVERSE_SELL = "逆向卖点背离"   # 景气高位+价格下跌（基本面见顶，股价走弱）


class DivergenceAnalyzer:
    """
    背离分析引擎

    检测多种背离类型：
    1. 价格-估值背离：价格趋势与估值分位趋势不一致
    2. 价格-景气背离：价格趋势与宏观景气指标趋势不一致
    3. 基本面-价格核心背离：设计文档3.2条核心逻辑
       - 逆向买点：价格分位 > 景气度分位
       - 逆向卖点：景气分位 >= 80% 且价格持续下跌
    """

    def __init__(
        self,
        divergence_threshold: float = 10.0,
        weak_threshold: float = 5.0,
        prosperity_buy_threshold: float = 20.0,
        prosperity_sell_threshold: float = 80.0
    ):
        """
        初始化背离分析引擎

        Args:
            divergence_threshold: 背离阈值（百分点）
            weak_threshold: 弱背离阈值（百分点）
            prosperity_buy_threshold: 景气度买点阈值（默认20%）
            prosperity_sell_threshold: 景气度卖点阈值（默认80%）
        """
        self.divergence_threshold = divergence_threshold
        self.weak_threshold = weak_threshold
        self.prosperity_buy_threshold = prosperity_buy_threshold
        self.prosperity_sell_threshold = prosperity_sell_threshold

    def analyze_core_divergence(
        self,
        prosperity_percentile: float,
        price_percentile: float,
        valuation_percentile: Optional[float] = None,
        marginal_improvement: Optional[bool] = None,
        price_trend_3m: Optional[str] = None,
        price_trend_12m: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析核心背离（设计文档3.2条）

        核心逻辑：
        - 逆向买点背离：景气度分位 <= 20% 且 价格分位 > 景气度分位
        - 逆向卖点背离：景气度分位 >= 80% 且 近3/12月价格持续下跌

        Args:
            prosperity_percentile: 景气度分位（0-100）
            price_percentile: 价格分位（0-100）
            valuation_percentile: 估值分位（可选）
            marginal_improvement: 边际改善标志（True/False/None）
            price_trend_3m: 近3月价格趋势（上涨/下跌/持平）
            price_trend_12m: 近12月价格趋势（上涨/下跌/持平）

        Returns:
            核心背离分析结果
        """
        result = {
            'prosperity_percentile': prosperity_percentile,
            'price_percentile': price_percentile,
            'valuation_percentile': valuation_percentile,
            'divergence_detected': False,
            'divergence_type': DivergenceType.NONE.value,
            'divergence_code': DivergenceType.NONE.name,
            'signal': '观望',
            'strength': 0.0,
            'conditions_met': [],
            'conditions_failed': [],
            'marginal_improvement': marginal_improvement,
        }

        # ===== 买点背离分析（设计文档3.2条买点核心条件）=====
        if prosperity_percentile <= self.prosperity_buy_threshold:
            result['conditions_met'].append(f"景气度分位 <= {self.prosperity_buy_threshold}% ({prosperity_percentile}%)")

            # 核心背离条件：价格分位 > 景气度分位
            if price_percentile > prosperity_percentile:
                result['divergence_detected'] = True
                result['divergence_type'] = DivergenceType.REVERSE_BUY.value
                result['divergence_code'] = DivergenceType.REVERSE_BUY.name
                result['signal'] = '买入机会'
                result['conditions_met'].append(f"核心背离：价格分位({price_percentile}%) > 景气度分位({prosperity_percentile}%)")
                result['strength'] = self._calculate_core_divergence_strength(
                    prosperity_percentile, price_percentile, prosperity_buy=True
                )

                # 检查边际改善条件
                if marginal_improvement is True:
                    result['conditions_met'].append('边际改善：景气环比降幅收窄或转正')
                elif marginal_improvement is False:
                    result['conditions_failed'].append('边际未改善：景气仍持续恶化')
            else:
                result['conditions_failed'].append(f"无背离：价格分位({price_percentile}%) <= 景气度分位({prosperity_percentile}%)")

            # 检查估值条件
            if valuation_percentile is not None and valuation_percentile <= 25:
                result['conditions_met'].append(f"估值分位 <= 25% ({valuation_percentile}%)")
            elif valuation_percentile is not None:
                result['conditions_failed'].append(f"估值分位 > 25% ({valuation_percentile}%)")

        # ===== 卖点背离分析（设计文档3.2条卖点核心条件）=====
        elif prosperity_percentile >= self.prosperity_sell_threshold:
            result['conditions_met'].append(f"景气度分位 >= {self.prosperity_sell_threshold}% ({prosperity_percentile}%)")

            # 检查价格持续下跌
            price_declining = False
            decline_count = 0

            if price_trend_3m in ('下跌', '调整'):
                decline_count += 1
            if price_trend_12m in ('下跌', '调整'):
                decline_count += 1

            if decline_count >= 1:
                price_declining = True

            if price_declining:
                result['divergence_detected'] = True
                result['divergence_type'] = DivergenceType.REVERSE_SELL.value
                result['divergence_code'] = DivergenceType.REVERSE_SELL.name
                result['signal'] = '卖出预警'
                result['conditions_met'].append(f'价格持续下跌（3月:{price_trend_3m}, 12月:{price_trend_12m}）')
                result['strength'] = self._calculate_core_divergence_strength(
                    prosperity_percentile, price_percentile, prosperity_buy=False
                )
            else:
                result['conditions_failed'].append(f'价格未持续下跌（3月:{price_trend_3m}, 12月:{price_trend_12m}）')

        # ===== 中性区间 =====
        else:
            result['signal'] = '观望'
            result['conditions_failed'].append(f'景气度分位处于中性区间 ({prosperity_percentile}%)')

        return result

    def analyze_marginal_improvement(
        self,
        current_prosperity: float,
        previous_prosperity: float,
        threshold: float = 0.0
    ) -> Dict[str, Any]:
        """
        检测边际改善（设计文档3.2条买点条件2）

        边际改善定义：当期景气环比降幅收窄或小幅转正

        Args:
            current_prosperity: 当期景气度
            previous_prosperity: 上期景气度
            threshold: 改善阈值（0表示转正）

        Returns:
            边际改善检测结果
        """
        change = current_prosperity - previous_prosperity

        # 判断边际改善：变化率收窄或转正
        # 例如：从 -10% 改善到 -5%（降幅收窄），或从 -5% 改善到 +2%（转正）
        is_improving = change >= threshold

        # 计算改善幅度
        if previous_prosperity != 0:
            improvement_rate = (change / abs(previous_prosperity)) * 100
        else:
            improvement_rate = 100 if change > 0 else 0

        result = {
            'current_prosperity': current_prosperity,
            'previous_prosperity': previous_prosperity,
            'change': round(change, 2),
            'improvement_rate': round(improvement_rate, 2),
            'is_improving': is_improving,
            'improvement_type': self._classify_improvement(change, threshold),
        }

        return result

    def _classify_improvement(self, change: float, threshold: float) -> str:
        """
        分类边际改善类型

        Args:
            change: 变化值
            threshold: 阈值

        Returns:
            改善类型描述
        """
        if change > threshold * 2:
            return "明显改善"
        elif change > threshold:
            return "小幅改善"
        elif change >= 0:
            return "持平转正"
        else:
            return "持续恶化"

    def _calculate_core_divergence_strength(
        self,
        prosperity_percentile: float,
        price_percentile: float,
        prosperity_buy: bool = True
    ) -> float:
        """
        计算核心背离强度

        计算公式设计说明：
        1. 背离强度基于三个维度：
           - 分位差 (base_score): 价格分位与景气分位的差值，反映背离程度
           - 景气极值加成 (prosperity_score): 景气越极端，背离信号越强
           - 价格位置加成 (price_score): 买点背离时价格相对高更安全，卖点反之

        2. 系数选择依据：
           - percentile_diff * 2: 差值每1%得2分，满分50分（差值25%时满分）
           - 1.5: 景气加成系数，当景气从20%降到0%时增加30分
           - 0.25: 价格位置系数，当价格分位100%时再加25分

        3. 设计原则：
           - 背离强度上限100分
           - 各维度贡献相对均衡
           - 参数敏感性在阶段六验证调整

        Args:
            prosperity_percentile: 景气度分位
            price_percentile: 价格分位
            prosperity_buy: 是否为买点背离

        Returns:
            强度值 (0-100)
        """
        if prosperity_buy:
            # 买点背离强度：景气越低、价格相对越高，背离越强
            # 基础强度：基于分位差
            percentile_diff = price_percentile - prosperity_percentile
            # 基础分（最高50分）：差值每1%得2分，25%差值时满分
            base_score = min(50, percentile_diff * 2)
            # 景气极值加成（最高30分）：景气越低越好，20%以下时加成最大
            prosperity_score = max(0, (20 - prosperity_percentile)) * 1.5
            # 价格相对位置加成（最高25分）：价格在高位时加分
            price_score = min(25, price_percentile * 0.25)
        else:
            # 卖点背离强度：景气越高、价格越低，背离越强
            percentile_diff = prosperity_percentile - price_percentile
            base_score = min(50, percentile_diff * 2)
            # 景气高位加成（最高25分）：景气超过80%时开始加分
            prosperity_score = min(25, (prosperity_percentile - 80) * 1.25)
            # 价格低位加成（最高25分）：价格在低位时加分
            price_score = max(0, 25 - price_percentile * 0.25)

        strength = base_score + prosperity_score + price_score
        return min(100.0, max(0.0, strength))

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
        if divergence_type in (
            DivergenceType.BULLISH,
            DivergenceType.WEAK_BULLISH,
            DivergenceType.REVERSE_BUY
        ):
            return "买入机会"
        elif divergence_type in (
            DivergenceType.BEARISH,
            DivergenceType.WEAK_BEARISH,
            DivergenceType.REVERSE_SELL
        ):
            return "卖出预警"
        else:
            return "观望"