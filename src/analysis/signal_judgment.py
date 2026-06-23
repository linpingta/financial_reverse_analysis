"""
信号判定器

根据设计文档3.3条判定买入/卖出/观望信号
- 买入条件：全部条件同时满足（AND 逻辑）
- 卖出条件：任意2条触发（宽松条件）
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from loguru import logger


class SignalType(Enum):
    """信号类型枚举"""
    BUY = "买入信号"
    SELL = "卖出信号"
    HOLD = "观望"


class SignalJudgment:
    """
    信号判定器（对齐设计文档3.3条）

    买入判定（严格AND逻辑，全部条件同时满足）：
    1. 景气度分位 <= 20%
    2. 估值水位分位 <= 25%
    3. 核心背离：价格分位 > 景气度分位
    4. 边际改善：当期货景气环比降幅收窄或小幅转正
    5. 风控前置校验通过

    卖出判定（任意2条触发）：
    1. 景气度分位 >= 80%
    2. 核心背离：景气持续创新高，但近3/12月行业指数持续下跌
    3. 估值条件：估值从历史高位持续回落
    """

    def __init__(
        self,
        prosperity_buy_threshold: float = 20.0,
        prosperity_sell_threshold: float = 80.0,
        valuation_buy_threshold: float = 25.0,
    ):
        """
        初始化信号判定器

        Args:
            prosperity_buy_threshold: 景气度买点阈值（默认20%）
            prosperity_sell_threshold: 景气度卖点阈值（默认80%）
            valuation_buy_threshold: 估值买点阈值（默认25%）
        """
        self.prosperity_buy_threshold = prosperity_buy_threshold
        self.prosperity_sell_threshold = prosperity_sell_threshold
        self.valuation_buy_threshold = valuation_buy_threshold

    def judge_buy_signal_strict(
        self,
        prosperity_percentile: float,
        valuation_percentile: float,
        price_percentile: float,
        marginal_improvement: bool,
        risk_passed: bool,
    ) -> Dict[str, Any]:
        """
        严格买入信号判定（设计文档3.2条，全部条件同时满足）

        条件：
        1. 景气度分位 <= 20%
        2. 估值水位分位 <= 25%
        3. 核心背离：价格分位 > 景气度分位
        4. 边际改善：当期货景气环比降幅收窄或小幅转正
        5. 风控前置校验通过

        Args:
            prosperity_percentile: 景气度分位（0-100）
            valuation_percentile: 估值分位（0-100）
            price_percentile: 价格分位（0-100）
            marginal_improvement: 边际改善标志
            risk_passed: 风控是否通过

        Returns:
            严格买入判定结果
        """
        conditions: List[Dict[str, Any]] = []
        all_satisfied = True
        reasons = []

        # 条件1：景气度分位 <= 20%
        cond1 = prosperity_percentile <= self.prosperity_buy_threshold
        conditions.append({
            'id': 1,
            'name': '景气度分位',
            'required': True,
            'condition': f'<= {self.prosperity_buy_threshold}%',
            'actual': prosperity_percentile,
            'satisfied': cond1,
        })
        if cond1:
            reasons.append(f"景气度分位处于低位 ({prosperity_percentile}%)")
        else:
            reasons.append(f"景气度分位未达低位要求 ({prosperity_percentile}%)")
            all_satisfied = False

        # 条件2：估值水位分位 <= 25%
        cond2 = valuation_percentile <= self.valuation_buy_threshold
        conditions.append({
            'id': 2,
            'name': '估值水位',
            'required': True,
            'condition': f'<= {self.valuation_buy_threshold}%',
            'actual': valuation_percentile,
            'satisfied': cond2,
        })
        if cond2:
            reasons.append(f"估值分位处于低位 ({valuation_percentile}%)")
        else:
            reasons.append(f"估值分位未达低位要求 ({valuation_percentile}%)")
            all_satisfied = False

        # 条件3：核心背离：价格分位 > 景气度分位
        cond3 = price_percentile > prosperity_percentile
        conditions.append({
            'id': 3,
            'name': '核心背离',
            'required': True,
            'condition': f'价格分位 > 景气度分位',
            'actual': f'{price_percentile}% > {prosperity_percentile}%',
            'satisfied': cond3,
        })
        if cond3:
            reasons.append(f"核心背离成立：价格({price_percentile}%) > 景气度({prosperity_percentile}%)")
        else:
            reasons.append(f"核心背离不成立：价格({price_percentile}%) <= 景气度({prosperity_percentile}%)")
            all_satisfied = False

        # 条件4：边际改善
        cond4 = marginal_improvement
        conditions.append({
            'id': 4,
            'name': '边际改善',
            'required': True,
            'condition': '当期货景气环比降幅收窄或小幅转正',
            'actual': marginal_improvement,
            'satisfied': cond4,
        })
        if cond4:
            reasons.append("景气边际改善")
        else:
            reasons.append("景气未边际改善")
            all_satisfied = False

        # 条件5：风控通过
        cond5 = risk_passed
        conditions.append({
            'id': 5,
            'name': '风控校验',
            'required': True,
            'condition': '通过价值陷阱过滤规则',
            'actual': '通过' if risk_passed else '未通过',
            'satisfied': cond5,
        })
        if cond5:
            reasons.append("风控校验通过")
        else:
            reasons.append("风控校验未通过")
            all_satisfied = False

        # 判定结果
        if all_satisfied:
            signal = SignalType.BUY
            conclusion = "满足全部买入条件"
        else:
            signal = SignalType.HOLD
            conclusion = "未满足全部买入条件"

        return {
            'signal': signal.value,
            'signal_code': signal.name,
            'all_conditions_met': all_satisfied,
            'conditions_satisfied': sum(1 for c in conditions if c['satisfied']),
            'conditions_total': len(conditions),
            'conditions': conditions,
            'reasons': reasons,
            'conclusion': conclusion,
        }

    def judge_sell_signal_relaxed(
        self,
        prosperity_percentile: float,
        valuation_percentile: Optional[float] = None,
        price_trend_3m: Optional[str] = None,
        price_trend_12m: Optional[str] = None,
        valuation_trend: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        宽松卖出信号判定（设计文档3.3条，任意2条触发）

        条件：
        1. 景气度分位 >= 80%
        2. 核心背离：景气持续创新高，但近3/12月行业指数持续下跌
        3. 估值条件：估值从历史高位持续回落

        Args:
            prosperity_percentile: 景气度分位（0-100）
            valuation_percentile: 估值分位（可选）
            price_trend_3m: 近3月价格趋势
            price_trend_12m: 近12月价格趋势
            valuation_trend: 估值趋势（上涨/下跌/持平）

        Returns:
            宽松卖出判定结果
        """
        conditions: List[Dict[str, Any]] = []
        reasons = []
        satisfied_count = 0

        # 条件1：景气度分位 >= 80%
        cond1 = prosperity_percentile >= self.prosperity_sell_threshold
        conditions.append({
            'id': 1,
            'name': '景气度分位',
            'condition': f'>= {self.prosperity_sell_threshold}%',
            'actual': prosperity_percentile,
            'satisfied': cond1,
        })
        if cond1:
            reasons.append(f"景气度分位处于高位 ({prosperity_percentile}%)")
            satisfied_count += 1

        # 条件2：价格持续下跌（核心背离）
        # 严格判定：要求3月和12月趋势都显示下跌，才认为是价格持续下跌
        price_declining_3m = price_trend_3m in ('下跌', '调整') if price_trend_3m else False
        price_declining_12m = price_trend_12m in ('下跌', '调整') if price_trend_12m else False
        # 价格持续下跌：短期调整或长期下跌，或两者同时下跌
        price_declining = price_declining_3m or price_declining_12m

        cond2 = cond1 and price_declining  # 需要同时满足景气高位和价格下跌
        conditions.append({
            'id': 2,
            'name': '核心背离',
            'condition': '景气高位 + 价格下跌(短期或长期)',
            'actual': f'景气{prosperity_percentile}%, 3月:{price_trend_3m}, 12月:{price_trend_12m}',
            'satisfied': cond2,
        })
        if cond2:
            reasons.append(f"核心背离成立：景气高位 + 价格下跌(3m:{price_declining_3m}, 12m:{price_declining_12m})")
            satisfied_count += 1

        # 条件3：估值从历史高位回落
        cond3 = False
        if valuation_percentile is not None and valuation_trend == '下跌':
            # 估值高于50%且趋势下跌，视为从高位回落
            if valuation_percentile > 50:
                cond3 = True

        conditions.append({
            'id': 3,
            'name': '估值回落',
            'condition': '估值从历史高位持续回落',
            'actual': f'估值分位:{valuation_percentile}%, 趋势:{valuation_trend}',
            'satisfied': cond3,
        })
        if cond3:
            reasons.append(f"估值从高位回落 ({valuation_percentile}%)")
            satisfied_count += 1

        # 判定结果
        if satisfied_count >= 2:
            signal = SignalType.SELL
            conclusion = f"满足 {satisfied_count} 条卖出条件，触发卖出预警"
        else:
            signal = SignalType.HOLD
            conclusion = f"仅满足 {satisfied_count} 条卖出条件，未触发预警"

        return {
            'signal': signal.value,
            'signal_code': signal.name,
            'conditions_triggered': satisfied_count,
            'conditions_required': 2,
            'conditions': conditions,
            'reasons': reasons,
            'conclusion': conclusion,
        }

    def judge_watch_zone(
        self,
        prosperity_percentile: float,
        price_percentile: Optional[float] = None,
        prosperity_change: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        观望区间判定（设计文档3.4条）

        满足任意一条即划入观望池：
        1. 景气度分位处于20%~80%中性区间
        2. 基本面走势与行业指数涨跌同向
        3. 周期底部/顶部拐点未确认

        Args:
            prosperity_percentile: 景气度分位
            price_percentile: 价格分位（可选）
            prosperity_change: 景气度变化（可选）

        Returns:
            观望区间判定结果
        """
        in_watch_zone = False
        reasons = []

        # 条件1：景气度分位处于中性区间
        if 20 < prosperity_percentile < 80:
            in_watch_zone = True
            reasons.append(f"景气度分位处于中性区间 ({prosperity_percentile}%)")

        # 条件2：基本面与价格同向
        if price_percentile is not None and prosperity_change is not None:
            # 同向判断（简化处理）
            if (prosperity_change > 0 and price_percentile > 50) or \
               (prosperity_change < 0 and price_percentile < 50):
                in_watch_zone = True
                reasons.append("基本面与价格同向波动")

        # 条件3：拐点未确认（中性区间隐含拐点未确认）
        if 20 <= prosperity_percentile <= 80:
            reasons.append("周期拐点未确认")

        return {
            'in_watch_zone': in_watch_zone,
            'prosperity_percentile': prosperity_percentile,
            'reasons': reasons if in_watch_zone else [],
            'signal': SignalType.HOLD.value,
            'signal_code': SignalType.HOLD.name,
        }

    def judge_signal_comprehensive(
        self,
        prosperity_percentile: float,
        valuation_percentile: float,
        price_percentile: float,
        marginal_improvement: bool,
        risk_passed: bool,
        price_trend_3m: Optional[str] = None,
        price_trend_12m: Optional[str] = None,
        valuation_trend: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        综合信号判定

        优先判定买入（严格AND），其次判定卖出（宽松OR），最后判定观望

        Args:
            prosperity_percentile: 景气度分位
            valuation_percentile: 估值分位
            price_percentile: 价格分位
            marginal_improvement: 边际改善标志
            risk_passed: 风控是否通过
            price_trend_3m: 近3月价格趋势
            price_trend_12m: 近12月价格趋势
            valuation_trend: 估值趋势

        Returns:
            综合信号判定结果
        """
        # 1. 先判定观望区间
        watch_result = self.judge_watch_zone(prosperity_percentile)

        # 2. 判定买入信号
        buy_result = self.judge_buy_signal_strict(
            prosperity_percentile=prosperity_percentile,
            valuation_percentile=valuation_percentile,
            price_percentile=price_percentile,
            marginal_improvement=marginal_improvement,
            risk_passed=risk_passed,
        )

        # 3. 判定卖出信号
        sell_result = self.judge_sell_signal_relaxed(
            prosperity_percentile=prosperity_percentile,
            valuation_percentile=valuation_percentile,
            price_trend_3m=price_trend_3m,
            price_trend_12m=price_trend_12m,
            valuation_trend=valuation_trend,
        )

        # 综合判定优先级：买入 > 卖出 > 观望
        if buy_result['signal_code'] == 'BUY':
            final_signal = buy_result
            final_signal['priority'] = '买入信号（优先）'
        elif sell_result['signal_code'] == 'SELL':
            final_signal = sell_result
            final_signal['priority'] = '卖出预警'
        else:
            final_signal = watch_result
            final_signal['priority'] = '观望区间'

        final_signal['buy_analysis'] = buy_result
        final_signal['sell_analysis'] = sell_result
        final_signal['watch_analysis'] = watch_result

        return final_signal

    def _get_strength_label(self, strength: float) -> str:
        """
        获取信号强度标签

        Args:
            strength: 信号强度 (0-100)

        Returns:
            强度标签
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
