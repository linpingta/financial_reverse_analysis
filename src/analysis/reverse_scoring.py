"""
逆向评分计算器

计算行业的逆向投资评分，综合多个维度
"""

from typing import Optional, Dict, Any
from enum import Enum
from loguru import logger


class ScoreLevel(Enum):
    """评分等级枚举"""
    OPPORTUNITY = "机会"
    WATCH = "观察"
    AVOID = "规避"


class ReverseScoring:
    """
    逆向评分计算器

    评分维度：
    1. 估值分位得分
    2. 背离信号得分
    3. 趋势得分
    4. 风控过滤得分
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        初始化评分计算器

        Args:
            weights: 各维度权重字典
        """
        # 默认权重配置
        self._weights = weights or {
            'valuation': 35.0,      # 估值分位
            'divergence': 30.0,     # 背离信号
            'trend': 15.0,          # 趋势
            'risk': 20.0,           # 风控
        }

        # 确保权重总和为100
        total_weight = sum(self._weights.values())
        if total_weight != 100.0:
            logger.warning(f"权重总和不为100 ({total_weight})，将自动归一化")
            self._weights = {k: v / total_weight * 100 for k, v in self._weights.items()}

    def calculate_valuation_score(self, pe_percentile: Optional[float], pb_percentile: Optional[float]) -> Dict[str, Any]:
        """
        计算估值分位得分

        估值越低，得分越高（逆向投资逻辑）

        Args:
            pe_percentile: PE 分位
            pb_percentile: PB 分位

        Returns:
            估值得分结果
        """
        valid_percentiles = [p for p in [pe_percentile, pb_percentile] if p is not None]

        if not valid_percentiles:
            return {
                'score': None,
                'weight': self._weights['valuation'],
                'contribution': None,
                'reason': '缺少估值数据',
                'pe_percentile': pe_percentile,
                'pb_percentile': pb_percentile,
            }

        # 取 PE 和 PB 的平均作为综合估值分位
        composite_percentile = sum(valid_percentiles) / len(valid_percentiles)

        # 逆向评分：分位越低，得分越高
        # 使用指数函数给予低估值更高权重
        if composite_percentile <= 10:
            score = 100
            reason = f"估值极低 ({composite_percentile:.1f}%)"
        elif composite_percentile <= 20:
            score = 90
            reason = f"估值很低 ({composite_percentile:.1f}%)"
        elif composite_percentile <= 30:
            score = 75
            reason = f"估值较低 ({composite_percentile:.1f}%)"
        elif composite_percentile <= 50:
            score = 50
            reason = f"估值适中 ({composite_percentile:.1f}%)"
        elif composite_percentile <= 70:
            score = 30
            reason = f"估值较高 ({composite_percentile:.1f}%)"
        elif composite_percentile <= 85:
            score = 15
            reason = f"估值很高 ({composite_percentile:.1f}%)"
        else:
            score = 5
            reason = f"估值极高 ({composite_percentile:.1f}%)"

        return {
            'score': score,
            'weight': self._weights['valuation'],
            'contribution': round(score * self._weights['valuation'] / 100, 2),
            'reason': reason,
            'pe_percentile': pe_percentile,
            'pb_percentile': pb_percentile,
            'composite_percentile': round(composite_percentile, 2),
        }

    def calculate_divergence_score(self, divergence_signal: Optional[str]) -> Dict[str, Any]:
        """
        计算背离信号得分

        Args:
            divergence_signal: 背离信号

        Returns:
            背离得分结果
        """
        if not divergence_signal:
            return {
                'score': 50,
                'weight': self._weights['divergence'],
                'contribution': round(50 * self._weights['divergence'] / 100, 2),
                'reason': '无背离信号数据',
                'divergence_signal': None,
            }

        if '正向背离' in divergence_signal:
            if '极强' in divergence_signal or '强' in divergence_signal:
                score = 90
                reason = '强正向背离信号'
            else:
                score = 75
                reason = '正向背离信号'
        elif '负向背离' in divergence_signal:
            if '极强' in divergence_signal or '强' in divergence_signal:
                score = 10
                reason = '强负向背离信号'
            else:
                score = 25
                reason = '负向背离信号'
        else:
            score = 50
            reason = '无明显背离'

        return {
            'score': score,
            'weight': self._weights['divergence'],
            'contribution': round(score * self._weights['divergence'] / 100, 2),
            'reason': reason,
            'divergence_signal': divergence_signal,
        }

    def calculate_trend_score(self, price_trend: Optional[str], pe_percentile: Optional[float] = None) -> Dict[str, Any]:
        """
        计算趋势得分

        逆向投资逻辑：价格下跌在低估值时是加分项

        Args:
            price_trend: 价格趋势
            pe_percentile: PE 分位（用于判断是否为低估值环境）

        Returns:
            趋势得分结果
        """
        if not price_trend:
            return {
                'score': 50,
                'weight': self._weights['trend'],
                'contribution': round(50 * self._weights['trend'] / 100, 2),
                'reason': '无趋势数据',
                'price_trend': None,
            }

        # 判断是否为低估值环境
        is_low_valuation = pe_percentile is not None and pe_percentile <= 30

        # 逆向投资逻辑
        if price_trend in ('下跌', '调整'):
            if is_low_valuation:
                score = 80
                reason = f"价格下跌 + 低估值 = 逆向机会"
            else:
                score = 40
                reason = f"价格下跌，但估值不低"
        elif price_trend in ('上涨', '反弹'):
            if is_low_valuation:
                score = 60
                reason = f"价格上涨 + 低估值 = 趋势确认"
            else:
                score = 25
                reason = f"价格上涨 + 高估值 = 谨慎"
        else:
            score = 50
            reason = f"趋势不明"

        return {
            'score': score,
            'weight': self._weights['trend'],
            'contribution': round(score * self._weights['trend'] / 100, 2),
            'reason': reason,
            'price_trend': price_trend,
            'is_low_valuation': is_low_valuation,
        }

    def calculate_risk_score(self, risk_level: str, is_blocked: bool = False) -> Dict[str, Any]:
        """
        计算风控得分

        Args:
            risk_level: 风险等级
            is_blocked: 是否被风控阻止

        Returns:
            风控得分结果
        """
        if is_blocked:
            return {
                'score': 0,
                'weight': self._weights['risk'],
                'contribution': 0,
                'reason': '行业被风控阻止',
                'risk_level': risk_level,
                'is_blocked': True,
            }

        if risk_level == '低风险':
            score = 95
            reason = '风险低'
        elif risk_level == '中风险':
            score = 70
            reason = '存在一定风险'
        elif risk_level == '高风险':
            score = 30
            reason = '风险较高'
        elif risk_level == '极高风险':
            score = 10
            reason = '风险极高'
        else:
            score = 50
            reason = '风险等级未知'

        return {
            'score': score,
            'weight': self._weights['risk'],
            'contribution': round(score * self._weights['risk'] / 100, 2),
            'reason': reason,
            'risk_level': risk_level,
            'is_blocked': False,
        }

    def calculate_overall_score(
        self,
        pe_percentile: Optional[float] = None,
        pb_percentile: Optional[float] = None,
        divergence_signal: Optional[str] = None,
        price_trend: Optional[str] = None,
        risk_level: str = '低风险',
        is_blocked: bool = False,
    ) -> Dict[str, Any]:
        """
        计算综合评分

        Args:
            pe_percentile: PE 分位
            pb_percentile: PB 分位
            divergence_signal: 背离信号
            price_trend: 价格趋势
            risk_level: 风险等级
            is_blocked: 是否被风控阻止

        Returns:
            综合评分结果
        """
        # 计算各维度得分
        valuation = self.calculate_valuation_score(pe_percentile, pb_percentile)
        divergence = self.calculate_divergence_score(divergence_signal)
        trend = self.calculate_trend_score(price_trend, pe_percentile)
        risk = self.calculate_risk_score(risk_level, is_blocked)

        # 计算总分
        contributions = [
            valuation['contribution'],
            divergence['contribution'],
            trend['contribution'],
            risk['contribution'],
        ]

        # 处理 None 值
        valid_contributions = [c for c in contributions if c is not None]

        if not valid_contributions:
            overall_score = None
        else:
            overall_score = round(sum(valid_contributions), 2)

        # 确定评分等级
        level, level_code = self._determine_level(overall_score, is_blocked)

        return {
            'overall_score': overall_score,
            'level': level,
            'level_code': level_code,
            'is_blocked': is_blocked,
            'weights': self._weights.copy(),
            'breakdown': {
                'valuation': valuation,
                'divergence': divergence,
                'trend': trend,
                'risk': risk,
            },
            'summary': self._generate_summary(valuation, divergence, trend, risk),
        }

    def _determine_level(self, score: Optional[float], is_blocked: bool) -> tuple:
        """
        根据总分确定等级

        Args:
            score: 综合评分
            is_blocked: 是否被风控阻止

        Returns:
            (等级名称, 等级代码)
        """
        if is_blocked or score is None:
            return (ScoreLevel.AVOID.value, ScoreLevel.AVOID.name)
        if score >= 70:
            return (ScoreLevel.OPPORTUNITY.value, ScoreLevel.OPPORTUNITY.name)
        if score >= 40:
            return (ScoreLevel.WATCH.value, ScoreLevel.WATCH.name)
        return (ScoreLevel.AVOID.value, ScoreLevel.AVOID.name)

    def _generate_summary(self, valuation, divergence, trend, risk) -> str:
        """
        生成评分摘要

        Args:
            valuation: 估值得分
            divergence: 背离得分
            trend: 趋势得分
            risk: 风控得分

        Returns:
            摘要字符串
        """
        reasons = []
        if valuation['reason']:
            reasons.append(valuation['reason'])
        if divergence['reason']:
            reasons.append(divergence['reason'])
        if trend['reason']:
            reasons.append(trend['reason'])
        if risk['reason']:
            reasons.append(risk['reason'])

        return '; '.join(reasons)

    def get_weights(self) -> Dict[str, float]:
        """
        获取当前权重配置

        Returns:
            权重字典
        """
        return self._weights.copy()

    def set_weights(self, weights: Dict[str, float]) -> None:
        """
        设置权重配置

        Args:
            weights: 新权重字典
        """
        total_weight = sum(weights.values())
        if total_weight != 100.0:
            logger.warning(f"权重总和不为100 ({total_weight})，将自动归一化")
            self._weights = {k: v / total_weight * 100 for k, v in weights.items()}
        else:
            self._weights = weights.copy()

        logger.info(f"权重配置已更新: {self._weights}")