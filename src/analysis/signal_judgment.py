"""
信号判定器

根据多维度条件判定买入/卖出/观望信号
"""

from typing import Optional, Dict, Any
from enum import Enum
from loguru import logger


class SignalType(Enum):
    """信号类型枚举"""
    BUY = "买入信号"
    SELL = "卖出信号"
    HOLD = "观望"


class SignalJudgment:
    """
    信号判定器

    根据以下条件判定信号：
    1. 估值分位条件
    2. 背离信号条件
    3. 趋势条件
    """

    def __init__(
        self,
        buy_valuation_threshold: float = 20.0,
        sell_valuation_threshold: float = 80.0,
        strong_buy_threshold: float = 10.0,
        strong_sell_threshold: float = 90.0,
    ):
        """
        初始化信号判定器

        Args:
            buy_valuation_threshold: 买入估值分位阈值（低于此值可能触发买入）
            sell_valuation_threshold: 卖出估值分位阈值（高于此值可能触发卖出）
            strong_buy_threshold: 强买入阈值
            strong_sell_threshold: 强卖出阈值
        """
        self.buy_valuation_threshold = buy_valuation_threshold
        self.sell_valuation_threshold = sell_valuation_threshold
        self.strong_buy_threshold = strong_buy_threshold
        self.strong_sell_threshold = strong_sell_threshold

    def judge_signal(
        self,
        pe_percentile: Optional[float] = None,
        pb_percentile: Optional[float] = None,
        divergence_signal: Optional[str] = None,
        price_trend: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        综合判定交易信号

        Args:
            pe_percentile: PE 分位
            pb_percentile: PB 分位
            divergence_signal: 背离信号
            price_trend: 价格趋势

        Returns:
            信号判定结果
        """
        conditions = []
        signal = SignalType.HOLD
        signal_strength = 0.0
        reasons = []

        # 使用综合估值分位
        valid_percentiles = [p for p in [pe_percentile, pb_percentile] if p is not None]
        composite_percentile = sum(valid_percentiles) / len(valid_percentiles) if valid_percentiles else None

        # 估值条件判断
        if composite_percentile is not None:
            conditions.append({
                'type': 'valuation',
                'value': round(composite_percentile, 2),
                'threshold': self.buy_valuation_threshold,
                'satisfied': composite_percentile <= self.buy_valuation_threshold,
            })

            # 估值分位信号
            if composite_percentile <= self.strong_buy_threshold:
                reasons.append(f"估值分位极低 ({composite_percentile:.1f}%)")
                signal_strength += 40
            elif composite_percentile <= self.buy_valuation_threshold:
                reasons.append(f"估值分位较低 ({composite_percentile:.1f}%)")
                signal_strength += 25
            elif composite_percentile >= self.strong_sell_threshold:
                reasons.append(f"估值分位极高 ({composite_percentile:.1f}%)")
                signal_strength -= 40
            elif composite_percentile >= self.sell_valuation_threshold:
                reasons.append(f"估值分位较高 ({composite_percentile:.1f}%)")
                signal_strength -= 25

        # 背离信号判断
        if divergence_signal:
            conditions.append({
                'type': 'divergence',
                'value': divergence_signal,
                'threshold': '正向背离',
                'satisfied': '正向背离' in divergence_signal,
            })

            if '正向背离' in divergence_signal:
                reasons.append(f"检测到正向背离信号")
                signal_strength += 30
            elif '负向背离' in divergence_signal:
                reasons.append(f"检测到负向背离信号")
                signal_strength -= 30

        # 价格趋势判断
        if price_trend:
            conditions.append({
                'type': 'trend',
                'value': price_trend,
                'threshold': '下跌',
                'satisfied': price_trend == '下跌',
            })

            # 逆向投资逻辑：价格下跌在低估值时是机会
            if composite_percentile is not None:
                if price_trend in ('下跌', '调整') and composite_percentile <= self.buy_valuation_threshold:
                    reasons.append(f"价格处于下跌趋势，低估值下是逆向机会")
                    signal_strength += 20
                elif price_trend in ('上涨', '反弹') and composite_percentile >= self.sell_valuation_threshold:
                    reasons.append(f"价格处于上涨趋势，高估值下需谨慎")
                    signal_strength -= 20

        # 综合判定信号类型
        if signal_strength >= 50:
            signal = SignalType.BUY
        elif signal_strength <= -30:
            signal = SignalType.SELL
        else:
            signal = SignalType.HOLD

        # 确保强度在 0-100 范围内
        normalized_strength = min(100.0, max(0.0, (signal_strength + 100) / 2))

        return {
            'signal': signal.value,
            'signal_code': signal.name,
            'signal_strength': round(normalized_strength, 2),
            'signal_strength_label': self._get_strength_label(normalized_strength),
            'reasons': reasons,
            'conditions': conditions,
            'composite_percentile': round(composite_percentile, 2) if composite_percentile else None,
        }

    def judge_buy_signal(
        self,
        pe_percentile: Optional[float] = None,
        pb_percentile: Optional[float] = None,
        divergence_signal: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        判断买入信号（严格条件）

        买入条件：全部满足
        1. PE 分位低于买入阈值 OR PB 分位低于买入阈值
        2. 检测到正向背离信号
        3. 价格趋势为下跌或调整

        Args:
            pe_percentile: PE 分位
            pb_percentile: PB 分位
            divergence_signal: 背离信号

        Returns:
            是否满足买入条件
        """
        valid_percentiles = [p for p in [pe_percentile, pb_percentile] if p is not None]

        if not valid_percentiles:
            return False

        # 条件1：估值分位低于阈值
        condition1 = any(p <= self.buy_valuation_threshold for p in valid_percentiles)

        # 条件2：正向背离信号
        condition2 = divergence_signal is not None and '正向背离' in divergence_signal

        # 条件3：价格趋势为下跌或调整
        price_trend = kwargs.get('price_trend')
        condition3 = price_trend is None or price_trend in ('下跌', '调整')

        return condition1 and condition2 and condition3

    def judge_sell_signal(
        self,
        pe_percentile: Optional[float] = None,
        pb_percentile: Optional[float] = None,
        divergence_signal: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        判断卖出信号（宽松条件）

        卖出条件：任意2条满足
        1. PE 分位高于卖出阈值 OR PB 分位高于卖出阈值
        2. 检测到负向背离信号
        3. 价格趋势为上涨但估值分位下降

        Args:
            pe_percentile: PE 分位
            pb_percentile: PB 分位
            divergence_signal: 背离信号

        Returns:
            是否满足卖出条件
        """
        valid_percentiles = [p for p in [pe_percentile, pb_percentile] if p is not None]
        satisfied_count = 0

        # 条件1：估值分位高于阈值
        if valid_percentiles and any(p >= self.sell_valuation_threshold for p in valid_percentiles):
            satisfied_count += 1

        # 条件2：负向背离信号
        if divergence_signal is not None and '负向背离' in divergence_signal:
            satisfied_count += 1

        # 条件3：价格上涨但估值分位下降（隐含在背离信号中）
        # 这里简化处理，检查是否有负向背离

        return satisfied_count >= 2

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