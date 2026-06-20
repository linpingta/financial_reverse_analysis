"""
Markdown 报告生成器

功能：
- 生成单个行业详细分析报告
- 生成多行业汇总报告
- 支持自定义报告模板
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger


class Reporter:
    """行业分析报告生成器"""

    def __init__(self, output_dir: str = "reports"):
        """
        初始化报告生成器

        Args:
            output_dir: 报告输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        industry_name: str,
        result: Dict[str, Any],
        save_to_file: bool = True
    ) -> str:
        """
        生成单个行业的 Markdown 分析报告

        Args:
            industry_name: 行业名称
            result: 分析结果字典
            save_to_file: 是否保存到文件

        Returns:
            Markdown 格式的报告内容
        """
        # 报告头部
        lines = [
            f"# {industry_name} 逆向投资分析报告",
            "",
            f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            ""
        ]

        # 一、核心指标
        lines.extend(self._generate_core_indicators(result))

        # 二、背离分析
        lines.extend(self._generate_divergence_analysis(result))

        # 三、信号判定
        lines.extend(self._generate_signal_judgment(result))

        # 四、风险提示
        lines.extend(self._generate_risk_warnings(result))

        # 五、操作建议
        lines.extend(self._generate_recommendation(result))

        # 六、详细数据
        lines.extend(self._generate_detailed_data(result))

        # 拼接报告
        report_content = '\n'.join(lines)

        # 保存到文件
        if save_to_file:
            filename = f"{industry_name}_{datetime.now().strftime('%Y%m%d')}.md"
            filepath = self.output_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"报告已保存: {filepath}")

        return report_content

    def _generate_core_indicators(self, result: Dict[str, Any]) -> List[str]:
        """生成核心指标部分"""
        lines = [
            "## 一、核心指标",
            "",
            "| 指标 | 数值 | 历史分位 | 说明 |",
            "|------|------|----------|------|"
        ]

        # 景气度指标
        prosperity = result.get('prosperity', 'N/A')
        prosperity_pct = result.get('prosperity_pct', 'N/A')
        prosperity_desc = self._get_percentile_description(prosperity_pct)
        lines.append(
            f"| 景气度 | {prosperity} | {self._format_percentile(prosperity_pct)} | {prosperity_desc} |"
        )

        # 估值指标（PE）
        pe = result.get('pe', 'N/A')
        valuation_pct = result.get('valuation_pct', 'N/A')
        valuation_desc = self._get_percentile_description(valuation_pct)
        lines.append(
            f"| 估值(PE) | {pe} | {self._format_percentile(valuation_pct)} | {valuation_desc} |"
        )

        # 价格指标
        price = result.get('price', 'N/A')
        price_pct = result.get('price_pct', 'N/A')
        price_desc = self._get_percentile_description(price_pct)
        lines.append(
            f"| 价格 | {price} | {self._format_percentile(price_pct)} | {price_desc} |"
        )

        # PB 指标（如果有）
        pb = result.get('pb')
        if pb is not None:
            pb_pct = result.get('pb_pct', 'N/A')
            pb_desc = self._get_percentile_description(pb_pct)
            lines.append(
                f"| 估值(PB) | {pb} | {self._format_percentile(pb_pct)} | {pb_desc} |"
            )

        lines.append("")
        return lines

    def _generate_divergence_analysis(self, result: Dict[str, Any]) -> List[str]:
        """生成背离分析部分"""
        lines = [
            "## 二、背离分析",
            ""
        ]

        divergence = result.get('divergence', {})
        divergence_type = divergence.get('type', '无背离')
        divergence_strength = divergence.get('strength', 0)
        divergence_text = result.get('divergence_text', '暂无背离信号')

        # 背离类型说明
        type_desc = {
            'bullish': '正向背离（买点信号）',
            'bearish': '负向背离（卖点信号）',
            'none': '无背离',
            '无背离': '无背离'
        }

        lines.append(f"**背离类型**: {type_desc.get(divergence_type, divergence_type)}")
        lines.append(f"**背离强度**: {divergence_strength:.1f} 分")
        lines.append("")
        lines.append("**核心逻辑**:")
        lines.append(f"{divergence_text}")
        lines.append("")

        # 背离详情（如果有）
        if 'details' in divergence:
            lines.append("**背离详情**:")
            for key, value in divergence['details'].items():
                lines.append(f"- {key}: {value}")
            lines.append("")

        return lines

    def _generate_signal_judgment(self, result: Dict[str, Any]) -> List[str]:
        """生成信号判定部分"""
        lines = [
            "## 三、信号判定",
            ""
        ]

        signal = result.get('signal', 'hold')
        score = result.get('score', {})

        # 信号类型说明
        signal_desc = {
            'buy': '✅ **买入机会**',
            'sell': '⚠️ **卖出预警**',
            'hold': '⏸️ **观望区间**'
        }

        lines.append(f"**判定结果**: {signal_desc.get(signal, signal)}")
        lines.append("")

        # 逆向评分
        total_score = score.get('total_score', 0)
        score_level = score.get('level', '未知')
        lines.append(f"**逆向评分**: {total_score:.1f} 分（{score_level}）")
        lines.append("")

        # 评分明细
        if 'details' in score:
            lines.append("**评分明细**:")
            lines.append("")
            lines.append("| 维度 | 得分 | 权重 | 说明 |")
            lines.append("|------|------|------|------|")

            for key, value in score['details'].items():
                dimension_name = self._get_dimension_name(key)
                dimension_score = value.get('score', 0)
                dimension_weight = value.get('weight', 0)
                dimension_desc = value.get('description', '')
                lines.append(
                    f"| {dimension_name} | {dimension_score:.1f} | {dimension_weight:.1f} | {dimension_desc} |"
                )

            lines.append("")

        return lines

    def _generate_risk_warnings(self, result: Dict[str, Any]) -> List[str]:
        """生成风险提示部分"""
        lines = [
            "## 四、风险提示",
            ""
        ]

        risk_warnings = result.get('risk_warnings', [])

        if not risk_warnings:
            lines.append("✅ 暂无明显风险提示")
        else:
            lines.append("⚠️ **以下风险需关注**:")
            lines.append("")
            for i, warning in enumerate(risk_warnings, 1):
                lines.append(f"{i}. {warning}")

        lines.append("")
        return lines

    def _generate_recommendation(self, result: Dict[str, Any]) -> List[str]:
        """生成操作建议部分"""
        lines = [
            "## 五、操作建议",
            ""
        ]

        recommendation = result.get('recommendation', '暂无操作建议')
        lines.append(recommendation)
        lines.append("")

        # 根据信号类型添加建议
        signal = result.get('signal', 'hold')
        if signal == 'buy':
            lines.append("**建议操作**:")
            lines.append("- 密切关注行业基本面边际改善信号")
            lines.append("- 分批建仓，控制仓位")
            lines.append("- 设置止损位，防范下行风险")
        elif signal == 'sell':
            lines.append("**建议操作**:")
            lines.append("- 考虑逐步减仓")
            lines.append("- 关注景气度见顶信号")
            lines.append("- 避免追高")
        else:
            lines.append("**建议操作**:")
            lines.append("- 继续观望，等待更明确信号")
            lines.append("- 持续跟踪行业景气度变化")

        lines.append("")
        return lines

    def _generate_detailed_data(self, result: Dict[str, Any]) -> List[str]:
        """生成详细数据部分"""
        lines = [
            "---",
            "",
            "## 六、详细数据",
            ""
        ]

        raw_data = result.get('raw_data', {})
        if raw_data:
            lines.append("```json")
            import json
            lines.append(json.dumps(raw_data, indent=2, ensure_ascii=False))
            lines.append("```")
        else:
            lines.append("*暂无详细数据*")

        lines.append("")
        return lines

    def generate_summary_report(
        self,
        results: List[Dict[str, Any]],
        title: str = "周期行业逆向分析周报",
        save_to_file: bool = True
    ) -> str:
        """
        生成多行业汇总报告

        Args:
            results: 多个行业的分析结果列表
            title: 报告标题
            save_to_file: 是否保存到文件

        Returns:
            Markdown 格式的汇总报告
        """
        lines = [
            f"# {title}",
            "",
            f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            ""
        ]

        # 统计摘要
        lines.extend(self._generate_summary_statistics(results))

        # 买入机会
        buy_signals = [r for r in results if r.get('signal') == 'buy']
        if buy_signals:
            lines.extend(self._generate_signal_section(buy_signals, "买入机会", "✅"))

        # 卖出预警
        sell_signals = [r for r in results if r.get('signal') == 'sell']
        if sell_signals:
            lines.extend(self._generate_signal_section(sell_signals, "卖出预警", "⚠️"))

        # 观望区间
        hold_signals = [r for r in results if r.get('signal') == 'hold']
        if hold_signals:
            lines.extend(self._generate_signal_section(hold_signals, "观望区间", "⏸️"))

        # 汇总表格
        lines.extend(self._generate_summary_table(results))

        # 拼接报告
        report_content = '\n'.join(lines)

        # 保存到文件
        if save_to_file:
            filename = f"汇总报告_{datetime.now().strftime('%Y%m%d')}.md"
            filepath = self.output_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"汇总报告已保存: {filepath}")

        return report_content

    def _generate_summary_statistics(self, results: List[Dict[str, Any]]) -> List[str]:
        """生成统计摘要"""
        lines = [
            "## 📊 统计摘要",
            ""
        ]

        total = len(results)
        buy_count = sum(1 for r in results if r.get('signal') == 'buy')
        sell_count = sum(1 for r in results if r.get('signal') == 'sell')
        hold_count = total - buy_count - sell_count

        avg_score = sum(r.get('score', {}).get('total_score', 0) for r in results) / total if total > 0 else 0

        lines.append(f"- **分析行业总数**: {total}")
        lines.append(f"- **买入机会**: {buy_count} 个")
        lines.append(f"- **卖出预警**: {sell_count} 个")
        lines.append(f"- **观望区间**: {hold_count} 个")
        lines.append(f"- **平均逆向评分**: {avg_score:.1f} 分")
        lines.append("")

        return lines

    def _generate_signal_section(
        self,
        results: List[Dict[str, Any]],
        section_title: str,
        emoji: str
    ) -> List[str]:
        """生成信号分类部分"""
        lines = [
            f"## {emoji} {section_title}",
            ""
        ]

        # 按得分排序
        sorted_results = sorted(
            results,
            key=lambda r: r.get('score', {}).get('total_score', 0),
            reverse=True
        )

        for result in sorted_results:
            industry = result.get('industry', '未知行业')
            score = result.get('score', {}).get('total_score', 0)
            prosperity_pct = result.get('prosperity_pct', 'N/A')
            valuation_pct = result.get('valuation_pct', 'N/A')
            price_pct = result.get('price_pct', 'N/A')

            lines.append(f"### {industry}")
            lines.append("")
            lines.append(f"- **逆向评分**: {score:.1f} 分")
            lines.append(f"- **景气分位**: {self._format_percentile(prosperity_pct)}")
            lines.append(f"- **估值分位**: {self._format_percentile(valuation_pct)}")
            lines.append(f"- **价格分位**: {self._format_percentile(price_pct)}")
            lines.append("")

        return lines

    def _generate_summary_table(self, results: List[Dict[str, Any]]) -> List[str]:
        """生成汇总表格"""
        lines = [
            "## 📋 全部行业汇总表",
            "",
            "| 行业 | 信号 | 评分 | 景气分位 | 估值分位 | 价格分位 |",
            "|------|------|------|----------|----------|----------|"
        ]

        # 按得分排序
        sorted_results = sorted(
            results,
            key=lambda r: r.get('score', {}).get('total_score', 0),
            reverse=True
        )

        for result in sorted_results:
            industry = result.get('industry', '未知')
            signal = result.get('signal', 'hold')
            score = result.get('score', {}).get('total_score', 0)
            prosperity_pct = result.get('prosperity_pct', 'N/A')
            valuation_pct = result.get('valuation_pct', 'N/A')
            price_pct = result.get('price_pct', 'N/A')

            signal_emoji = {'buy': '✅', 'sell': '⚠️', 'hold': '⏸️'}.get(signal, '⏸️')

            lines.append(
                f"| {industry} | {signal_emoji} {signal} | {score:.1f} | "
                f"{self._format_percentile(prosperity_pct)} | "
                f"{self._format_percentile(valuation_pct)} | "
                f"{self._format_percentile(price_pct)} |"
            )

        lines.append("")
        return lines

    def _format_percentile(self, percentile: Any) -> str:
        """格式化分位显示"""
        if percentile is None or percentile == 'N/A':
            return 'N/A'
        try:
            return f"{float(percentile):.1f}%"
        except (ValueError, TypeError):
            return str(percentile)

    def _get_percentile_description(self, percentile: Any) -> str:
        """获取分位描述"""
        if percentile is None or percentile == 'N/A':
            return '数据不足'

        try:
            pct = float(percentile)
            if pct <= 20:
                return '历史极低位置'
            elif pct <= 40:
                return '历史较低位置'
            elif pct <= 60:
                return '历史中等位置'
            elif pct <= 80:
                return '历史较高位置'
            else:
                return '历史极高位置'
        except (ValueError, TypeError):
            return '数据异常'

    def _get_dimension_name(self, key: str) -> str:
        """获取评分维度名称"""
        dimension_names = {
            'divergence_strength': '背离强度',
            'prosperity_extreme': '基本面极值',
            'valuation_margin': '估值安全边际',
            'marginal_improvement': '边际改善',
            'valuation': '估值维度',
            'divergence': '背离维度',
            'trend': '趋势维度',
            'risk': '风险维度'
        }
        return dimension_names.get(key, key)