"""
风控过滤器

过滤存在风险的行业/标的
"""

from typing import Optional, Dict, List, Any
from enum import Enum
from loguru import logger


class RiskLevel(Enum):
    """风险等级枚举"""
    LOW = "低风险"
    MEDIUM = "中风险"
    HIGH = "高风险"
    CRITICAL = "极高风险"


class RiskType(Enum):
    """风险类型枚举"""
    SUNSET_INDUSTRY = "夕阳行业"
    OVERCAPACITY = "产能过剩"
    POLICY_RISK = "政策风险"
    LIQUIDITY_RISK = "流动性风险"
    FINANCIAL_RISK = "财务风险"


class RiskFilter:
    """
    风控过滤器

    过滤规则：
    1. 夕阳行业过滤：黑名单机制
    2. 产能过剩检测：产能利用率判断
    3. 政策风险检测：政策压制识别
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化风控过滤器

        Args:
            config: 配置字典
        """
        self._config = config or {}

        # 夕阳行业黑名单（真正的夕阳行业，非强周期行业）
        # 注意：煤炭开采、钢铁、有色金属、传统能源等是强周期行业，是系统核心分析对象，不列入黑名单
        self._sunset_industries = self._config.get('sunset_industries', [
            '教培',      # 永久衰退行业
            '传统媒体',  # 受互联网冲击
            '胶片',      # 被数字化替代
        ])

        # 产能过剩行业（可配置）
        self._overcapacity_industries = self._config.get('overcapacity_industries', [
            '钢铁',
            '水泥',
            '平板玻璃',
            '电解铝',
        ])

        # 政策风险行业（可配置）
        self._policy_risk_industries = self._config.get('policy_risk_industries', [
            '房地产',
            '教培',
            '互联网平台',
        ])

        # 产能利用率阈值
        self._capacity_utilization_threshold = self._config.get(
            'capacity_utilization_threshold', 75.0
        )

    def filter_sunset_industry(self, industry_name: str) -> Dict[str, Any]:
        """
        检查是否为夕阳行业

        Args:
            industry_name: 行业名称

        Returns:
            过滤结果
        """
        is_sunset = any(keyword in industry_name for keyword in self._sunset_industries)

        return {
            'risk_type': RiskType.SUNSET_INDUSTRY.value,
            'risk_code': RiskType.SUNSET_INDUSTRY.name,
            'risk_level': RiskLevel.HIGH.value if is_sunset else RiskLevel.LOW.value,
            'is_blocked': is_sunset,
            'reason': f"行业 '{industry_name}' 属于夕阳行业" if is_sunset else None,
            'keywords': self._sunset_industries,
        }

    def filter_overcapacity(self, industry_name: str, capacity_utilization: Optional[float] = None) -> Dict[str, Any]:
        """
        检查产能过剩风险

        Args:
            industry_name: 行业名称
            capacity_utilization: 产能利用率（可选）

        Returns:
            过滤结果
        """
        # 首先检查是否在产能过剩行业列表中
        in_overcapacity_list = any(keyword in industry_name for keyword in self._overcapacity_industries)

        # 检查产能利用率
        utilization_low = False
        if capacity_utilization is not None:
            utilization_low = capacity_utilization < self._capacity_utilization_threshold

        # 判定风险等级
        if in_overcapacity_list and utilization_low:
            risk_level = RiskLevel.CRITICAL
            is_blocked = True
            reason = f"行业 '{industry_name}' 产能过剩且利用率低 ({capacity_utilization}%)"
        elif in_overcapacity_list:
            risk_level = RiskLevel.HIGH
            is_blocked = True
            reason = f"行业 '{industry_name}' 属于产能过剩行业"
        elif utilization_low:
            risk_level = RiskLevel.MEDIUM
            is_blocked = False
            reason = f"行业 '{industry_name}' 产能利用率较低 ({capacity_utilization}%)"
        else:
            risk_level = RiskLevel.LOW
            is_blocked = False
            reason = None

        return {
            'risk_type': RiskType.OVERCAPACITY.value,
            'risk_code': RiskType.OVERCAPACITY.name,
            'risk_level': risk_level.value,
            'is_blocked': is_blocked,
            'reason': reason,
            'capacity_utilization': capacity_utilization,
            'threshold': self._capacity_utilization_threshold,
        }

    def filter_policy_risk(self, industry_name: str, policy_score: Optional[float] = None) -> Dict[str, Any]:
        """
        检查政策风险

        Args:
            industry_name: 行业名称
            policy_score: 政策友好度评分（0-100，越低风险越高）

        Returns:
            过滤结果
        """
        # 检查是否在政策风险行业列表中
        in_policy_risk_list = any(keyword in industry_name for keyword in self._policy_risk_industries)

        # 检查政策评分
        policy_risk_high = False
        if policy_score is not None:
            policy_risk_high = policy_score < 50  # 低于50分为高风险

        # 判定风险等级
        if in_policy_risk_list and policy_risk_high:
            risk_level = RiskLevel.CRITICAL
            is_blocked = True
            reason = f"行业 '{industry_name}' 面临政策压制且政策评分低"
        elif in_policy_risk_list:
            risk_level = RiskLevel.HIGH
            is_blocked = True
            reason = f"行业 '{industry_name}' 面临政策风险"
        elif policy_risk_high:
            risk_level = RiskLevel.MEDIUM
            is_blocked = False
            reason = f"行业 '{industry_name}' 政策友好度较低"
        else:
            risk_level = RiskLevel.LOW
            is_blocked = False
            reason = None

        return {
            'risk_type': RiskType.POLICY_RISK.value,
            'risk_code': RiskType.POLICY_RISK.name,
            'risk_level': risk_level.value,
            'is_blocked': is_blocked,
            'reason': reason,
            'policy_score': policy_score,
        }

    def filter_liquidity(self, avg_volume: Optional[float] = None, market_cap: Optional[float] = None) -> Dict[str, Any]:
        """
        检查流动性风险

        Args:
            avg_volume: 日均成交量（亿元）
            market_cap: 市值（亿元）

        Returns:
            过滤结果
        """
        volume_low = False
        cap_low = False

        if avg_volume is not None and avg_volume < 1.0:  # 日均成交额低于1亿
            volume_low = True

        if market_cap is not None and market_cap < 50.0:  # 市值低于50亿
            cap_low = True

        if volume_low and cap_low:
            risk_level = RiskLevel.HIGH
            is_blocked = True
            reason = f"流动性风险高：日均成交额 {avg_volume} 亿，市值 {market_cap} 亿"
        elif volume_low:
            risk_level = RiskLevel.MEDIUM
            is_blocked = False
            reason = f"日均成交额较低 ({avg_volume} 亿)"
        elif cap_low:
            risk_level = RiskLevel.MEDIUM
            is_blocked = False
            reason = f"市值较小 ({market_cap} 亿)"
        else:
            risk_level = RiskLevel.LOW
            is_blocked = False
            reason = None

        return {
            'risk_type': RiskType.LIQUIDITY_RISK.value,
            'risk_code': RiskType.LIQUIDITY_RISK.name,
            'risk_level': risk_level.value,
            'is_blocked': is_blocked,
            'reason': reason,
            'avg_volume': avg_volume,
            'market_cap': market_cap,
        }

    def filter_financial(self, pe: Optional[float] = None, pb: Optional[float] = None, debt_ratio: Optional[float] = None) -> Dict[str, Any]:
        """
        检查财务风险

        Args:
            pe: 市盈率
            pb: 市净率
            debt_ratio: 资产负债率

        Returns:
            过滤结果
        """
        high_pe = False
        high_pb = False
        high_debt = False

        if pe is not None and pe > 100:  # PE过高
            high_pe = True

        if pb is not None and pb > 10:  # PB过高
            high_pb = True

        if debt_ratio is not None and debt_ratio > 70:  # 资产负债率高于70%
            high_debt = True

        risk_count = sum([high_pe, high_pb, high_debt])

        if risk_count >= 2:
            risk_level = RiskLevel.HIGH
            is_blocked = True
            reason = f"多项财务指标异常：PE={pe}, PB={pb}, 负债率={debt_ratio}%"
        elif risk_count == 1:
            risk_level = RiskLevel.MEDIUM
            is_blocked = False
            if high_pe:
                reason = f"PE过高 ({pe})"
            elif high_pb:
                reason = f"PB过高 ({pb})"
            else:
                reason = f"资产负债率较高 ({debt_ratio}%)"
        else:
            risk_level = RiskLevel.LOW
            is_blocked = False
            reason = None

        return {
            'risk_type': RiskType.FINANCIAL_RISK.value,
            'risk_code': RiskType.FINANCIAL_RISK.name,
            'risk_level': risk_level.value,
            'is_blocked': is_blocked,
            'reason': reason,
            'pe': pe,
            'pb': pb,
            'debt_ratio': debt_ratio,
        }

    def apply_all_filters(
        self,
        industry_name: str,
        capacity_utilization: Optional[float] = None,
        policy_score: Optional[float] = None,
        avg_volume: Optional[float] = None,
        market_cap: Optional[float] = None,
        pe: Optional[float] = None,
        pb: Optional[float] = None,
        debt_ratio: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        应用所有过滤器

        Args:
            industry_name: 行业名称
            capacity_utilization: 产能利用率
            policy_score: 政策友好度评分
            avg_volume: 日均成交量
            market_cap: 市值
            pe: 市盈率
            pb: 市净率
            debt_ratio: 资产负债率

        Returns:
            综合过滤结果
        """
        results = {
            'industry_name': industry_name,
            'filters': [],
            'blocked_by': [],
            'overall_risk_level': RiskLevel.LOW.value,
            'is_blocked': False,
            'risk_summary': [],
        }

        # 应用各个过滤器
        filters_to_apply = [
            ('sunset', lambda: self.filter_sunset_industry(industry_name)),
            ('overcapacity', lambda: self.filter_overcapacity(industry_name, capacity_utilization)),
            ('policy', lambda: self.filter_policy_risk(industry_name, policy_score)),
            ('liquidity', lambda: self.filter_liquidity(avg_volume, market_cap)),
            ('financial', lambda: self.filter_financial(pe, pb, debt_ratio)),
        ]

        for filter_name, filter_func in filters_to_apply:
            try:
                result = filter_func()
                results['filters'].append(result)

                if result['is_blocked']:
                    results['blocked_by'].append(filter_name)
                    results['is_blocked'] = True

                if result['reason']:
                    results['risk_summary'].append(result['reason'])

                # 更新整体风险等级
                current_level = RiskLevel[result['risk_level'].replace('风险', '')]
                overall_level = RiskLevel[results['overall_risk_level'].replace('风险', '')]
                if current_level.value > overall_level.value:
                    results['overall_risk_level'] = result['risk_level']

            except Exception as e:
                logger.error(f"应用 {filter_name} 过滤器失败: {e}")

        return results

    def update_config(self, config: Dict) -> None:
        """
        更新配置

        Args:
            config: 新配置字典
        """
        self._config.update(config)
        if 'sunset_industries' in config:
            self._sunset_industries = config['sunset_industries']
        if 'overcapacity_industries' in config:
            self._overcapacity_industries = config['overcapacity_industries']
        if 'policy_risk_industries' in config:
            self._policy_risk_industries = config['policy_risk_industries']
        if 'capacity_utilization_threshold' in config:
            self._capacity_utilization_threshold = config['capacity_utilization_threshold']

        logger.info("风控过滤器配置已更新")