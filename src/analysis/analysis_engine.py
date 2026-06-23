"""
统一分析引擎入口

整合所有分析模块，提供单一分析入口
"""

from typing import Optional, Dict, List, Any
from datetime import datetime
from loguru import logger

from .percentile_calculator import PercentileCalculator
from .divergence_analyzer import DivergenceAnalyzer
from .signal_judgment import SignalJudgment
from .risk_filter import RiskFilter
from .reverse_scoring import ReverseScoring


class AnalysisResult:
    """
    分析结果数据结构
    """

    def __init__(self):
        self.industry_name: str = ""
        self.sw_code: str = ""
        self.analysis_time: datetime = datetime.now()

        # 原始数据
        self.raw_data: Dict = {}

        # 估值分位
        self.percentile_data: Dict = {}

        # 背离分析
        self.divergence_data: Dict = {}

        # 信号判定
        self.signal_data: Dict = {}

        # 风控过滤
        self.risk_data: Dict = {}

        # 逆向评分
        self.scoring_data: Dict = {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'industry_name': self.industry_name,
            'sw_code': self.sw_code,
            'analysis_time': self.analysis_time.isoformat(),
            'percentile': self.percentile_data,
            'divergence': self.divergence_data,
            'signal': self.signal_data,
            'risk': self.risk_data,
            'scoring': self.scoring_data,
            'raw_data': self.raw_data,
        }


class AnalysisEngine:
    """
    统一分析引擎

    整合分位计算、背离分析、信号判定、风控过滤、逆向评分
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化分析引擎

        Args:
            config: 配置字典
        """
        self._config = config or {}

        # 初始化分析模块
        self._percentile_calculator = PercentileCalculator(
            history_years=self._config.get('history_years', 10),
            min_data_points=self._config.get('min_data_points', 520),
        )

        self._divergence_analyzer = DivergenceAnalyzer(
            divergence_threshold=self._config.get('divergence_threshold', 10.0),
            weak_threshold=self._config.get('weak_threshold', 5.0),
        )

        self._signal_judgment = SignalJudgment(
            buy_valuation_threshold=self._config.get('buy_valuation_threshold', 20.0),
            sell_valuation_threshold=self._config.get('sell_valuation_threshold', 80.0),
            strong_buy_threshold=self._config.get('strong_buy_threshold', 10.0),
            strong_sell_threshold=self._config.get('strong_sell_threshold', 90.0),
        )

        self._risk_filter = RiskFilter(self._config.get('risk_config', {}))

        self._reverse_scoring = ReverseScoring(self._config.get('scoring_weights', {}))

        logger.info("分析引擎初始化完成")

    def analyze_industry(
        self,
        industry_name: str,
        sw_code: str,
        pe_percentile: Optional[float] = None,
        pb_percentile: Optional[float] = None,
        price_change: Optional[float] = None,
        price_trend: Optional[str] = None,
        divergence_signal: Optional[str] = None,
        **kwargs
    ) -> AnalysisResult:
        """
        分析单个行业

        Args:
            industry_name: 行业名称
            sw_code: 申万行业代码
            pe_percentile: PE 分位
            pb_percentile: PB 分位
            price_change: 价格变化率
            price_trend: 价格趋势
            divergence_signal: 背离信号
            **kwargs: 其他参数（风控相关）

        Returns:
            分析结果
        """
        logger.info(f"开始分析行业: {industry_name} ({sw_code})")

        result = AnalysisResult()
        result.industry_name = industry_name
        result.sw_code = sw_code
        result.analysis_time = datetime.now()

        # 1. 估值分位分析
        logger.debug("执行估值分位分析...")
        percentile_result = self._percentile_calculator.calculate_pe_pb_percentile(
            pe_history=None,  # 由数据采集层提供
            pb_history=None,
            current_pe=kwargs.get('current_pe'),
            current_pb=kwargs.get('current_pb'),
        )
        # 补充传入的分位数据
        if pe_percentile is not None:
            percentile_result['pe'] = {'percentile': pe_percentile}
        if pb_percentile is not None:
            percentile_result['pb'] = {'percentile': pb_percentile}
        result.percentile_data = percentile_result

        # 2. 背离分析 - 核心背离分析
        logger.debug("执行核心背离分析...")
        # 使用传入的景气度、价格、估值分位进行分析
        # 注：以下使用 PE 分位作为代理是当前数据采集层的限制，阶段六将完善独立的数据源
        prosperity_pct = kwargs.get('prosperity_percentile', pe_percentile)
        price_pct = kwargs.get('price_percentile', pe_percentile)  # 如未单独传入，使用PE分位作为代理
        valuation_pct = kwargs.get('valuation_percentile', pe_percentile)

        # 检查数据完整性并记录警告
        if prosperity_pct is None:
            logger.warning(f"行业 {industry_name} 景气度分位数据缺失，使用默认值50.0代替")
            prosperity_pct = 50.0
        if price_pct is None:
            logger.warning(f"行业 {industry_name} 价格分位数据缺失，使用默认值50.0代替")
            price_pct = 50.0
        if valuation_pct is None:
            logger.warning(f"行业 {industry_name} 估值分位数据缺失，使用默认值50.0代替")
            valuation_pct = 50.0

        divergence_result = {}
        if prosperity_pct is not None and price_pct is not None:
            # 调用核心背离分析
            divergence_result = self._divergence_analyzer.analyze_core_divergence(
                prosperity_percentile=prosperity_pct,
                price_percentile=price_pct,
                valuation_percentile=valuation_pct,
                marginal_improvement=kwargs.get('marginal_improvement'),
                price_trend_3m=price_trend,
                price_trend_12m=kwargs.get('price_trend_12m'),
            )
        elif divergence_signal:
            # 使用传入的背离信号
            divergence_result = {
                'divergence_type': divergence_signal,
                'divergence_code': self._parse_divergence_code(divergence_signal),
                'signal': self._get_signal_from_divergence(divergence_signal),
                'divergence_detected': divergence_signal in ('正向背离', '逆向买点背离', '负向背离', '逆向卖点背离'),
            }
        result.divergence_data = divergence_result

        # 3. 风控过滤（先于信号判定执行，因为信号判定需要风控结果）
        logger.debug("执行风控过滤...")
        risk_result = self._risk_filter.apply_all_filters(
            industry_name=industry_name,
            capacity_utilization=kwargs.get('capacity_utilization'),
            policy_score=kwargs.get('policy_score'),
            avg_volume=kwargs.get('avg_volume'),
            market_cap=kwargs.get('market_cap'),
            pe=kwargs.get('current_pe'),
            pb=kwargs.get('current_pb'),
            debt_ratio=kwargs.get('debt_ratio'),
        )
        result.risk_data = risk_result

        # 4. 信号判定 - 综合信号判定
        logger.debug("执行综合信号判定...")
        risk_passed = not risk_result.get('is_blocked', False)

        signal_result = self._signal_judgment.judge_signal_comprehensive(
            prosperity_percentile=prosperity_pct,
            valuation_percentile=valuation_pct,
            price_percentile=price_pct,
            marginal_improvement=divergence_result.get('marginal_improvement', False),
            risk_passed=risk_passed,
            price_trend_3m=price_trend,
            price_trend_12m=kwargs.get('price_trend_12m'),
            valuation_trend=kwargs.get('valuation_trend'),
        )
        result.signal_data = signal_result

        # 5. 逆向评分
        logger.debug("执行逆向评分...")
        # 获取背离分析结果
        div_type = divergence_result.get('divergence_type', None)
        div_detected = divergence_result.get('divergence_detected', False)
        div_strength = divergence_result.get('divergence_strength', 0.0)

        scoring_result = self._reverse_scoring.calculate_overall_score(
            divergence_detected=div_detected,
            divergence_type=div_type,
            divergence_strength=div_strength,
            prosperity_percentile=kwargs.get('prosperity_percentile'),
            valuation_percentile=kwargs.get('valuation_percentile'),
            price_percentile=kwargs.get('price_percentile'),
            marginal_improvement=divergence_result.get('marginal_improvement'),
            improvement_type=divergence_result.get('improvement_type'),
            risk_passed=not risk_result.get('is_blocked', False),
        )
        result.scoring_data = scoring_result

        # 保存原始数据
        result.raw_data = {
            'pe_percentile': pe_percentile,
            'pb_percentile': pb_percentile,
            'price_change': price_change,
            'price_trend': price_trend,
            'divergence_signal': divergence_signal,
            'kwargs': kwargs,
        }

        logger.info(f"行业分析完成: {industry_name} - 评分: {scoring_result.get('overall_score')}")
        return result

    def analyze_multiple_industries(
        self,
        industries_data: List[Dict[str, Any]]
    ) -> List[AnalysisResult]:
        """
        批量分析多个行业

        Args:
            industries_data: 行业数据列表，每个元素包含行业信息

        Returns:
            分析结果列表
        """
        results = []

        logger.info(f"开始批量分析 {len(industries_data)} 个行业...")

        for industry_data in industries_data:
            try:
                result = self.analyze_industry(
                    industry_name=industry_data.get('name', ''),
                    sw_code=industry_data.get('sw_code', ''),
                    pe_percentile=industry_data.get('pe_percentile'),
                    pb_percentile=industry_data.get('pb_percentile'),
                    price_change=industry_data.get('price_change'),
                    price_trend=industry_data.get('price_trend'),
                    divergence_signal=industry_data.get('divergence_signal'),
                    **industry_data.get('kwargs', {}),
                )
                results.append(result)
            except Exception as e:
                logger.error(f"分析行业 {industry_data.get('name')} 失败: {e}")

        logger.info(f"批量分析完成: {len(results)}/{len(industries_data)} 个成功")
        return results

    def get_summary(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """
        生成分析摘要

        Args:
            results: 分析结果列表

        Returns:
            摘要统计
        """
        if not results:
            return {'total_industries': 0}

        # 统计各等级数量
        level_counts = {'机会': 0, '观察': 0, '规避': 0}
        signal_counts = {'买入信号': 0, '卖出信号': 0, '观望': 0}
        risk_counts = {'低风险': 0, '中风险': 0, '高风险': 0, '极高风险': 0}

        scores = []

        for result in results:
            # 评分等级统计
            level = result.scoring_data.get('level', '规避')
            if level in level_counts:
                level_counts[level] += 1

            # 信号统计
            signal = result.signal_data.get('signal', '观望')
            if signal in signal_counts:
                signal_counts[signal] += 1

            # 风险统计
            risk_level = result.risk_data.get('overall_risk_level', '低风险')
            if risk_level in risk_counts:
                risk_counts[risk_level] += 1

            # 收集评分
            score = result.scoring_data.get('overall_score')
            if score is not None:
                scores.append(score)

        # 计算平均评分
        avg_score = sum(scores) / len(scores) if scores else None

        return {
            'total_industries': len(results),
            'level_distribution': level_counts,
            'signal_distribution': signal_counts,
            'risk_distribution': risk_counts,
            'average_score': round(avg_score, 2) if avg_score else None,
            'highest_score_industry': self._get_highest_score_industry(results),
            'lowest_score_industry': self._get_lowest_score_industry(results),
            'analysis_time': datetime.now().isoformat(),
        }

    def _parse_divergence_code(self, divergence_signal: str) -> str:
        """
        解析背离信号代码

        Args:
            divergence_signal: 背离信号字符串

        Returns:
            信号代码
        """
        if '正向背离' in divergence_signal:
            return 'BULLISH'
        elif '负向背离' in divergence_signal:
            return 'BEARISH'
        else:
            return 'NONE'

    def _get_signal_from_divergence(self, divergence_signal: str) -> str:
        """
        从背离信号获取交易信号

        Args:
            divergence_signal: 背离信号

        Returns:
            交易信号
        """
        if '正向背离' in divergence_signal:
            return '买入机会'
        elif '负向背离' in divergence_signal:
            return '卖出预警'
        else:
            return '观望'

    def _get_highest_score_industry(self, results: List[AnalysisResult]) -> Optional[str]:
        """
        获取评分最高的行业

        Args:
            results: 分析结果列表

        Returns:
            行业名称（如果有）
        """
        highest = None
        max_score = -1

        for result in results:
            score = result.scoring_data.get('overall_score', -1)
            if score > max_score:
                max_score = score
                highest = result.industry_name

        return highest

    def _get_lowest_score_industry(self, results: List[AnalysisResult]) -> Optional[str]:
        """
        获取评分最低的行业

        Args:
            results: 分析结果列表

        Returns:
            行业名称（如果有）
        """
        lowest = None
        min_score = float('inf')

        for result in results:
            score = result.scoring_data.get('overall_score', float('inf'))
            if score < min_score:
                min_score = score
                lowest = result.industry_name

        return lowest

    def update_config(self, config: Dict) -> None:
        """
        更新配置

        Args:
            config: 新配置字典
        """
        self._config.update(config)

        # 更新各模块配置
        if 'history_years' in config or 'min_data_points' in config:
            self._percentile_calculator = PercentileCalculator(
                history_years=self._config.get('history_years', 10),
                min_data_points=self._config.get('min_data_points', 520),
            )

        if 'divergence_threshold' in config or 'weak_threshold' in config:
            self._divergence_analyzer = DivergenceAnalyzer(
                divergence_threshold=self._config.get('divergence_threshold', 10.0),
                weak_threshold=self._config.get('weak_threshold', 5.0),
            )

        if any(k in config for k in ['buy_valuation_threshold', 'sell_valuation_threshold',
                                      'strong_buy_threshold', 'strong_sell_threshold']):
            self._signal_judgment = SignalJudgment(
                buy_valuation_threshold=self._config.get('buy_valuation_threshold', 20.0),
                sell_valuation_threshold=self._config.get('sell_valuation_threshold', 80.0),
                strong_buy_threshold=self._config.get('strong_buy_threshold', 10.0),
                strong_sell_threshold=self._config.get('strong_sell_threshold', 90.0),
            )

        if 'risk_config' in config:
            self._risk_filter.update_config(config['risk_config'])

        if 'scoring_weights' in config:
            self._reverse_scoring.set_weights(config['scoring_weights'])

        logger.info("分析引擎配置已更新")

    def get_config(self) -> Dict[str, Any]:
        """
        获取当前配置

        Returns:
            配置字典
        """
        return self._config.copy()