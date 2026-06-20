"""
结果导出器

功能：
- 导出 CSV 格式
- 导出 Markdown 格式
- 导出 Excel 格式（可选）
"""

from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas 未安装，CSV/Excel 导出功能不可用")

try:
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    logger.warning("openpyxl 未安装，Excel 导出功能不可用")


class ResultExporter:
    """结果导出器"""

    def __init__(self, output_dir: str = "data/results"):
        """
        初始化导出器

        Args:
            output_dir: 导出文件保存目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_csv(
        self,
        results: List[Dict[str, Any]],
        filename: Optional[str] = None,
        include_raw_data: bool = False
    ) -> Optional[str]:
        """
        导出为 CSV 格式

        Args:
            results: 分析结果列表
            filename: 文件名（不含扩展名），默认自动生成
            include_raw_data: 是否包含原始数据字段

        Returns:
            导出文件路径，失败返回 None
        """
        if not PANDAS_AVAILABLE:
            logger.error("需要安装 pandas: pip install pandas")
            return None

        if not results:
            logger.warning("没有数据可导出")
            return None

        # 生成文件名
        if not filename:
            filename = f"分析结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        filepath = self.output_dir / f"{filename}.csv"

        try:
            # 转换为 DataFrame
            df = self._to_dataframe(results, include_raw_data)

            # 导出 CSV
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            logger.info(f"CSV 导出成功: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"CSV 导出失败: {e}")
            return None

    def export_excel(
        self,
        results: List[Dict[str, Any]],
        filename: Optional[str] = None,
        include_raw_data: bool = False,
        sheet_name: str = "分析结果"
    ) -> Optional[str]:
        """
        导出为 Excel 格式

        Args:
            results: 分析结果列表
            filename: 文件名（不含扩展名），默认自动生成
            include_raw_data: 是否包含原始数据字段
            sheet_name: Excel 工作表名称

        Returns:
            导出文件路径，失败返回 None
        """
        if not PANDAS_AVAILABLE:
            logger.error("需要安装 pandas: pip install pandas")
            return None

        if not OPENPYXL_AVAILABLE:
            logger.error("需要安装 openpyxl: pip install openpyxl")
            return None

        if not results:
            logger.warning("没有数据可导出")
            return None

        # 生成文件名
        if not filename:
            filename = f"分析结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        filepath = self.output_dir / f"{filename}.xlsx"

        try:
            # 转换为 DataFrame
            df = self._to_dataframe(results, include_raw_data)

            # 导出 Excel
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)

                # 自动调整列宽
                worksheet = writer.sheets[sheet_name]
                for idx, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).map(len).max(),
                        len(col)
                    )
                    worksheet.column_dimensions[get_column_letter(idx + 1)].width = min(max_length + 2, 50)

            logger.info(f"Excel 导出成功: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Excel 导出失败: {e}")
            return None

    def export_markdown(
        self,
        results: List[Dict[str, Any]],
        filename: Optional[str] = None,
        title: str = "周期行业逆向分析结果"
    ) -> Optional[str]:
        """
        导出为 Markdown 格式

        Args:
            results: 分析结果列表
            filename: 文件名（不含扩展名），默认自动生成
            title: 报告标题

        Returns:
            导出文件路径，失败返回 None
        """
        if not results:
            logger.warning("没有数据可导出")
            return None

        # 生成文件名
        if not filename:
            filename = f"分析结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        filepath = self.output_dir / f"{filename}.md"

        try:
            # 生成 Markdown 内容
            lines = self._generate_markdown(results, title)

            # 写入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))

            logger.info(f"Markdown 导出成功: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Markdown 导出失败: {e}")
            return None

    def _to_dataframe(
        self,
        results: List[Dict[str, Any]],
        include_raw_data: bool = False
    ):
        """
        将结果列表转换为 DataFrame

        Args:
            results: 分析结果列表
            include_raw_data: 是否包含原始数据字段

        Returns:
            pandas.DataFrame
        """
        # 提取主要字段
        rows = []
        for result in results:
            row = {
                '运行日期': result.get('run_date', ''),
                '行业': result.get('industry', ''),
                '景气分位': self._format_value(result.get('prosperity_pct')),
                '估值分位': self._format_value(result.get('valuation_pct')),
                '价格分位': self._format_value(result.get('price_pct')),
                '背离类型': result.get('divergence_type', ''),
                '背离强度': self._format_value(result.get('divergence_strength')),
                '信号': self._format_signal(result.get('signal')),
                '综合得分': self._format_value(result.get('score_total')),
                '得分等级': result.get('score_level', ''),
                '风险提示': '; '.join(result.get('risk_warnings', [])) if isinstance(result.get('risk_warnings'), list) else result.get('risk_warnings', ''),
                '操作建议': result.get('recommendation', '')
            }

            # 添加原始数据字段
            if include_raw_data and 'raw_data' in result:
                raw_data = result['raw_data']
                if isinstance(raw_data, dict):
                    for key, value in raw_data.items():
                        row[f'原始_{key}'] = str(value)

            rows.append(row)

        return pd.DataFrame(rows)

    def _generate_markdown(
        self,
        results: List[Dict[str, Any]],
        title: str
    ) -> List[str]:
        """
        生成 Markdown 内容

        Args:
            results: 分析结果列表
            title: 报告标题

        Returns:
            Markdown 行列表
        """
        lines = [
            f"# {title}",
            "",
            f"> 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            ""
        ]

        # 统计摘要
        lines.extend(self._generate_summary_section(results))

        # 详细结果表格
        lines.extend(self._generate_detail_table(results))

        return lines

    def _generate_summary_section(self, results: List[Dict[str, Any]]) -> List[str]:
        """生成统计摘要部分"""
        lines = [
            "## 📊 统计摘要",
            ""
        ]

        total = len(results)
        buy_count = sum(1 for r in results if r.get('signal') == 'buy')
        sell_count = sum(1 for r in results if r.get('signal') == 'sell')
        hold_count = total - buy_count - sell_count

        avg_score = sum(r.get('score_total', 0) for r in results) / total if total > 0 else 0

        lines.append(f"- **分析行业总数**: {total}")
        lines.append(f"- **买入机会**: {buy_count} 个")
        lines.append(f"- **卖出预警**: {sell_count} 个")
        lines.append(f"- **观望区间**: {hold_count} 个")
        lines.append(f"- **平均得分**: {avg_score:.1f} 分")
        lines.append("")

        return lines

    def _generate_detail_table(self, results: List[Dict[str, Any]]) -> List[str]:
        """生成详细结果表格"""
        lines = [
            "## 📋 详细结果",
            "",
            "| 行业 | 信号 | 得分 | 景气分位 | 估值分位 | 价格分位 | 背离类型 | 背离强度 |",
            "|------|------|------|----------|----------|----------|----------|----------|"
        ]

        # 按得分排序
        sorted_results = sorted(
            results,
            key=lambda r: r.get('score_total', 0),
            reverse=True
        )

        for result in sorted_results:
            industry = result.get('industry', '未知')
            signal = self._format_signal(result.get('signal'))
            score = self._format_value(result.get('score_total'))
            prosperity_pct = self._format_value(result.get('prosperity_pct'), suffix='%')
            valuation_pct = self._format_value(result.get('valuation_pct'), suffix='%')
            price_pct = self._format_value(result.get('price_pct'), suffix='%')
            divergence_type = result.get('divergence_type', '无')
            divergence_strength = self._format_value(result.get('divergence_strength'))

            lines.append(
                f"| {industry} | {signal} | {score} | {prosperity_pct} | "
                f"{valuation_pct} | {price_pct} | {divergence_type} | {divergence_strength} |"
            )

        lines.append("")
        return lines

    def _format_value(self, value: Any, suffix: str = '') -> str:
        """格式化数值"""
        if value is None:
            return 'N/A'
        try:
            if isinstance(value, (int, float)):
                return f"{value:.1f}{suffix}"
            return str(value)
        except (ValueError, TypeError):
            return str(value)

    def _format_signal(self, signal: str) -> str:
        """格式化信号类型"""
        signal_map = {
            'buy': '✅ 买入',
            'sell': '⚠️ 卖出',
            'hold': '⏸️ 观望'
        }
        return signal_map.get(signal, signal)


class BatchExporter:
    """批量导出器（支持多种格式同时导出）"""

    def __init__(self, output_dir: str = "data/results"):
        """
        初始化批量导出器

        Args:
            output_dir: 导出文件保存目录
        """
        self.exporter = ResultExporter(output_dir)

    def export_all(
        self,
        results: List[Dict[str, Any]],
        filename: Optional[str] = None,
        formats: List[str] = None
    ) -> Dict[str, str]:
        """
        批量导出多种格式

        Args:
            results: 分析结果列表
            filename: 文件名（不含扩展名）
            formats: 导出格式列表 ['csv', 'excel', 'markdown']

        Returns:
            导出文件路径字典 {'csv': path, 'excel': path, 'markdown': path}
        """
        if formats is None:
            formats = ['csv', 'markdown']

        exported_files = {}

        if 'csv' in formats:
            path = self.exporter.export_csv(results, filename)
            if path:
                exported_files['csv'] = path

        if 'excel' in formats:
            path = self.exporter.export_excel(results, filename)
            if path:
                exported_files['excel'] = path

        if 'markdown' in formats:
            path = self.exporter.export_markdown(results, filename)
            if path:
                exported_files['markdown'] = path

        return exported_files