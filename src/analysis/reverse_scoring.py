"""
逆向评分计算器

对齐设计文档5.1条评分体系
评分维度（0-100分）：
- 背离强度得分：最高 40 分
- 基本面极值得分：最高 30 分
- 估值安全边际得分：最高 20 分
- 边际改善得分：最高 10 分

评分等级（设计文档5.1条）：
- 0 ~ 30分：无逆向投资价值，建议规避
- 30 ~ 60分：周期底部观察区间，持续跟踪
- 60 ~ 100分：高确定性逆向投资机会，重点跟踪
"""

from typing import Optional, Dict, Any
from enum import Enum
from loguru import logger


class ScoreLevel(Enum):
    """评分等级枚举（对齐设计文档5.1条）"""
    OPPORTUNITY = "机会"      # 60-100分：高确定性逆向投资机会
    WATCH = "观察"            # 30-60分：周期底部观察区间
    AVOID = "规避"            # 0-30分：无逆向投资价值


class ReverseScoring:
    """
    逆向评分计算器（对齐设计文档5.1条）

    评分维度及权重：
    1. 背离强度得分：最高 40 分
    2. 基本面极值得分：最高 30 分
    3. 估值安全边际得分：最高 20 分
    4. 边际改善得分：最高 10 分
    """

    # 默认权重（总分100分）
    DEFAULT_WEIGHTS = {
        'divergence_strength': 40.0,  # 背离强度（设计文档最高40分）
        'prosperity_extreme': 30.0,   # 基本面极值（设计文档最高30分）
        'valuation_margin': 20.0,      # 估值安全边际（设计文档最高20分）
        'marginal_improvement': 10.0, # 边际改善（设计文档最高10分）
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        初始化评分计算器

        Args:
            weights: 各维度权重字典（可选，默认使用设计文档权重）
        """
        # 默认使用设计文档权重
        self._weights = weights or self.DEFAULT_WEIGHTS.copy()

        # 确保权重总和为100
        total_weight = sum(self._weights.values())
        if abs(total_weight - 100.0) > 0.01:
            logger.warning(f"权重总和不为100 ({total_weight})，将自动归一化")
            self._weights = {k: v / total_weight * 100 for k, v in self._weights.items()}

    def calculate_divergence_strength_score(
        self,
        divergence_detected: bool,
        divergence_type: Optional[str] = None,
        divergence_strength: float = 0.0,
        price_percentile: Optional[float] = None,
        prosperity_percentile: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        计算背离强度得分（最高40分，对齐设计文档5.1条）

        背离类型得分：
        - 逆向买点背离：40分
        - 正向背离（强）：30分
        - 正向背离（弱）：20分
        - 无背离：0分
        - 逆向卖点背离：-20分
        - 负向背离：-10分

        Args:
            divergence_detected: 是否检测到背离
            divergence_type: 背离类型
            divergence_strength: 背离强度（0-100）
            price_percentile: 价格分位
            prosperity_percentile: 景气度分位

        Returns:
            背离强度得分结果
        """
        # 基础分计算
        if divergence_type == '逆向买点背离':
            base_score = 40
            reason = "逆向买点背离（设计文档核心买点条件）"
        elif divergence_type == '正向背离' and divergence_strength >= 60:
            base_score = 30
            reason = "强正向背离"
        elif divergence_type == '正向背离':
            base_score = 20
            reason = "弱正向背离"
        elif divergence_detected and price_percentile is not None and prosperity_percentile is not None:
            # 根据分位差计算
            diff = price_percentile - prosperity_percentile
            if diff > 20:
                base_score = 35
                reason = f"价格分位显著高于景气度分位 ({diff:.1f}%)"
            elif diff > 10:
                base_score = 25
                reason = f"价格分位高于景气度分位 ({diff:.1f}%)"
            elif diff > 0:
                base_score = 15
                reason = f"存在轻微背离 ({diff:.1f}%)"
            else:
                base_score = 0
                reason = "无背离或反向背离"
        elif not divergence_detected:
            base_score = 0
            reason = "未检测到背离"
        else:
            base_score = 0
            reason = "背离类型未知"

        # 强度加成（基于传入的强度值）
        strength_bonus = 0
        if divergence_strength > 0:
            strength_bonus = min(10, divergence_strength / 10)

        score = min(40, base_score + strength_bonus)

        return {
            'score': round(score, 1),
            'max_score': 40,
            'weight': self._weights.get('divergence_strength', 40.0),
            'contribution': round(score / 100 * self._weights.get('divergence_strength', 40.0), 2),
            'base_score': base_score,
            'strength_bonus': strength_bonus,
            'reason': reason,
            'divergence_type': divergence_type,
        }

    def calculate_prosperity_extreme_score(
        self,
        prosperity_percentile: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        计算基本面极值得分（最高30分，对齐设计文档5.1条）

        分位区间得分：
        - 0-10%：30分（历史极致底部）
        - 10-20%：25分（历史底部）
        - 20-30%：18分
        - 30-50%：10分
        - 50-70%：5分
        - 70-80%：0分
        - 80-90%：-10分（历史顶部）
        - 90-100%：-20分（历史极致顶部）

        Args:
            prosperity_percentile: 景气度分位

        Returns:
            基本面极值得分结果
        """
        if prosperity_percentile is None:
            return {
                'score': 0,
                'max_score': 30,
                'weight': self._weights.get('prosperity_extreme', 30.0),
                'contribution': 0,
                'reason': '缺少景气度数据',
                'prosperity_percentile': None,
            }

        # 根据分位区间计算得分
        if prosperity_percentile <= 10:
            score = 30
            reason = f"基本面处于历史极致底部 ({prosperity_percentile}%)"
        elif prosperity_percentile <= 20:
            score = 25
            reason = f"基本面处于历史底部 ({prosperity_percentile}%)"
        elif prosperity_percentile <= 30:
            score = 18
            reason = f"基本面接近历史底部 ({prosperity_percentile}%)"
        elif prosperity_percentile <= 50:
            score = 10
            reason = f"基本面处于偏低位置 ({prosperity_percentile}%)"
        elif prosperity_percentile <= 70:
            score = 5
            reason = f"基本面处于中性偏低 ({prosperity_percentile}%)"
        elif prosperity_percentile <= 80:
            score = 0
            reason = f"基本面处于中性偏高 ({prosperity_percentile}%)"
        elif prosperity_percentile <= 90:
            score = -10
            reason = f"基本面接近历史顶部 ({prosperity_percentile}%)"
        else:
            score = -20
            reason = f"基本面处于历史极致顶部 ({prosperity_percentile}%)"

        # 确保最低0分（避免负分拉低总分过多）
        score = max(0, score)

        return {
            'score': round(score, 1),
            'max_score': 30,
            'weight': self._weights.get('prosperity_extreme', 30.0),
            'contribution': round(score / 30 * self._weights.get('prosperity_extreme', 30.0), 2),
            'reason': reason,
            'prosperity_percentile': prosperity_percentile,
        }

    def calculate_valuation_margin_score(
        self,
        valuation_percentile: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        计算估值安全边际得分（最高20分，对齐设计文档5.1条）

        分位区间得分：
        - 0-10%：20分（估值极低）
        - 10-25%：18分（估值低位）
        - 25-40%：12分
        - 40-60%：6分
        - 60-80%：0分
        - 80-100%：-10分（估值极高）

        Args:
            valuation_percentile: 估值分位

        Returns:
            估值安全边际得分结果
        """
        if valuation_percentile is None:
            return {
                'score': 0,
                'max_score': 20,
                'weight': self._weights.get('valuation_margin', 20.0),
                'contribution': 0,
                'reason': '缺少估值数据',
                'valuation_percentile': None,
            }

        # 根据分位区间计算得分
        if valuation_percentile <= 10:
            score = 20
            reason = f"估值处于历史极低位置 ({valuation_percentile}%)"
        elif valuation_percentile <= 25:
            score = 18
            reason = f"估值处于历史低位 ({valuation_percentile}%)"
        elif valuation_percentile <= 40:
            score = 12
            reason = f"估值处于偏低位置 ({valuation_percentile}%)"
        elif valuation_percentile <= 60:
            score = 6
            reason = f"估值处于中性位置 ({valuation_percentile}%)"
        elif valuation_percentile <= 80:
            score = 0
            reason = f"估值处于偏高位置 ({valuation_percentile}%)"
        else:
            score = -10
            reason = f"估值处于历史高位 ({valuation_percentile}%)"

        # 确保最低0分
        score = max(0, score)

        return {
            'score': round(score, 1),
            'max_score': 20,
            'weight': self._weights.get('valuation_margin', 20.0),
            'contribution': round(score / 20 * self._weights.get('valuation_margin', 20.0), 2),
            'reason': reason,
            'valuation_percentile': valuation_percentile,
        }

    def calculate_marginal_improvement_score(
        self,
        marginal_improvement: Optional[bool] = None,
        improvement_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        计算边际改善得分（最高10分，对齐设计文档5.1条）

        改善类型得分：
        - 明显改善：10分
        - 小幅改善：8分
        - 持平转正：6分
        - 无数据/持续恶化：0分

        Args:
            marginal_improvement: 边际改善标志
            improvement_type: 改善类型描述

        Returns:
            边际改善得分结果
        """
        if marginal_improvement is None:
            return {
                'score': 0,
                'max_score': 10,
                'weight': self._weights.get('marginal_improvement', 10.0),
                'contribution': 0,
                'reason': '缺少边际改善数据',
                'marginal_improvement': None,
            }

        if not marginal_improvement:
            score = 0
            reason = "景气未边际改善"
        elif improvement_type == "明显改善":
            score = 10
            reason = "景气边际明显改善"
        elif improvement_type == "小幅改善":
            score = 8
            reason = "景气边际小幅改善"
        elif improvement_type == "持平转正":
            score = 6
            reason = "景气持平转正"
        else:
            score = 0
            reason = "边际改善状态未知"

        return {
            'score': round(score, 1),
            'max_score': 10,
            'weight': self._weights.get('marginal_improvement', 10.0),
            'contribution': round(score / 10 * self._weights.get('marginal_improvement', 10.0), 2),
            'reason': reason,
            'marginal_improvement': marginal_improvement,
        }

    def calculate_overall_score(
        self,
        divergence_detected: bool = False,
        divergence_type: Optional[str] = None,
        divergence_strength: float = 0.0,
        prosperity_percentile: Optional[float] = None,
        valuation_percentile: Optional[float] = None,
        price_percentile: Optional[float] = None,
        marginal_improvement: Optional[bool] = None,
        improvement_type: Optional[str] = None,
        risk_passed: bool = True,
    ) -> Dict[str, Any]:
        """
        计算综合逆向评分（对齐设计文档5.1条）

        Args:
            divergence_detected: 是否检测到背离
            divergence_type: 背离类型
            divergence_strength: 背离强度
            prosperity_percentile: 景气度分位
            valuation_percentile: 估值分位
            price_percentile: 价格分位
            marginal_improvement: 边际改善标志
            improvement_type: 改善类型
            risk_passed: 风控是否通过

        Returns:
            综合评分结果
        """
        # 计算各维度得分
        divergence = self.calculate_divergence_strength_score(
            divergence_detected=divergence_detected,
            divergence_type=divergence_type,
            divergence_strength=divergence_strength,
            price_percentile=price_percentile,
            prosperity_percentile=prosperity_percentile,
        )

        prosperity = self.calculate_prosperity_extreme_score(prosperity_percentile)

        valuation = self.calculate_valuation_margin_score(valuation_percentile)

        improvement = self.calculate_marginal_improvement_score(
            marginal_improvement=marginal_improvement,
            improvement_type=improvement_type,
        )

        # 计算总分
        if not risk_passed:
            # 风控未通过，直接判定为规避
            overall_score = 0
        else:
            # 各维度得分加权求和
            overall_score = (
                divergence['contribution'] +
                prosperity['contribution'] +
                valuation['contribution'] +
                improvement['contribution']
            )

        # 确定评分等级（对齐设计文档5.1条）
        level, level_code = self._determine_level(overall_score, risk_passed)

        return {
            'overall_score': round(overall_score, 2),
            'level': level,
            'level_code': level_code,
            'risk_passed': risk_passed,
            'weights': self._weights.copy(),
            'breakdown': {
                'divergence_strength': divergence,
                'prosperity_extreme': prosperity,
                'valuation_margin': valuation,
                'marginal_improvement': improvement,
            },
            'summary': self._generate_summary(divergence, prosperity, valuation, improvement, risk_passed),
        }

    def _determine_level(self, score: float, risk_passed: bool) -> tuple:
        """
        根据总分确定等级（对齐设计文档5.1条）

        Args:
            score: 综合评分
            risk_passed: 风控是否通过

        Returns:
            (等级名称, 等级代码)
        """
        if not risk_passed or score is None:
            return (ScoreLevel.AVOID.value, ScoreLevel.AVOID.name)

        if score >= 60:
            return (ScoreLevel.OPPORTUNITY.value, ScoreLevel.OPPORTUNITY.name)
        elif score >= 30:
            return (ScoreLevel.WATCH.value, ScoreLevel.WATCH.name)
        else:
            return (ScoreLevel.AVOID.value, ScoreLevel.AVOID.name)

    def _generate_summary(
        self,
        divergence: Dict,
        prosperity: Dict,
        valuation: Dict,
        improvement: Dict,
        risk_passed: bool
    ) -> str:
        """
        生成评分摘要

        Args:
            divergence: 背离得分
            prosperity: 基本面得分
            valuation: 估值得分
            improvement: 边际改善得分
            risk_passed: 风控是否通过

        Returns:
            摘要字符串
        """
        if not risk_passed:
            return "风控未通过，建议规避"

        reasons = []
        if divergence['score'] >= 30:
            reasons.append(divergence['reason'])
        if prosperity['score'] >= 20:
            reasons.append(prosperity['reason'])
        if valuation['score'] >= 15:
            reasons.append(valuation['reason'])
        if improvement['score'] >= 8:
            reasons.append(improvement['reason'])

        if not reasons:
            reasons = ["综合评分处于观察区间"]

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
        if abs(total_weight - 100.0) > 0.01:
            logger.warning(f"权重总和不为100 ({total_weight})，将自动归一化")
            self._weights = {k: v / total_weight * 100 for k, v in weights.items()}
        else:
            self._weights = weights.copy()

        logger.info(f"权重配置已更新: {self._weights}")
