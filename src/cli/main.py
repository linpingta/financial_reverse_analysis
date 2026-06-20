"""
CLI 主入口

使用 Click 框架实现命令行界面
"""

import click
from pathlib import Path
from typing import Optional, List
from loguru import logger
import yaml
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.analysis_engine import AnalysisEngine
from src.data.collector_factory import DataCollector
from src.output.reporter import Reporter
from src.output.result_db import ResultDB
from src.output.result_exporter import ResultExporter


def load_config(config_path: Optional[str] = None) -> dict:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径，默认使用 config/config.yaml

    Returns:
        配置字典
    """
    if config_path is None:
        config_path = project_root / "config" / "config.yaml"

    config_path = Path(config_path)
    if not config_path.exists():
        logger.error(f"配置文件不存在: {config_path}")
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    logger.info(f"配置文件加载成功: {config_path}")
    return config


@click.group()
@click.version_option(version='1.0.0', prog_name='逆向周期行业投资分析系统')
@click.option('--config', '-c', type=click.Path(exists=True), help='配置文件路径')
@click.option('--verbose', '-v', is_flag=True, help='详细输出模式')
@click.pass_context
def cli(ctx, config, verbose):
    """
    逆向周期行业投资分析系统

    基于基本面-估值-股价背离的逆向投资策略分析工具
    """
    # 配置日志级别
    if verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.remove()
        logger.add(sys.stderr, level="INFO")

    # 加载配置
    try:
        config_data = load_config(config)
    except FileNotFoundError as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)

    # 保存到上下文
    ctx.ensure_object(dict)
    ctx.obj['config'] = config_data
    ctx.obj['verbose'] = verbose


@cli.command()
@click.pass_context
def version(ctx):
    """显示版本信息"""
    config = ctx.obj['config']
    click.echo(f"{config['project']['name']}")
    click.echo(f"版本: {config['project']['version']}")
    click.echo(f"描述: {config['project']['description']}")


@cli.command()
@click.option('--industry', '-i', multiple=True, help='指定行业名称（可多次使用）')
@click.option('--all', 'analyze_all', is_flag=True, help='分析所有行业')
@click.option('--output', '-o', type=click.Choice(['console', 'file', 'both']), default='console', help='输出方式')
@click.option('--save-db', is_flag=True, help='保存结果到数据库')
@click.option('--generate-report', is_flag=True, help='生成Markdown报告')
@click.pass_context
def analyze(ctx, industry, analyze_all, output, save_db, generate_report):
    """
    分析行业投资机会

    示例:
        # 分析所有行业
        python -m src.cli.main analyze --all

        # 分析指定行业
        python -m src.cli.main analyze --industry 航空机场 --industry 生猪养殖

        # 分析并保存到数据库
        python -m src.cli.main analyze --all --save-db

        # 分析并生成报告
        python -m src.cli.main analyze --all --generate-report
    """
    config = ctx.obj['config']
    verbose = ctx.obj['verbose']

    # 获取目标行业列表
    target_industries = config.get('industries', {}).get('target_industries', [])

    if not target_industries:
        click.echo("错误: 未配置目标行业", err=True)
        return

    # 确定要分析的行业
    if analyze_all:
        industries_to_analyze = target_industries
    elif industry:
        # 过滤出指定的行业
        industries_to_analyze = [
            ind for ind in target_industries
            if ind['name'] in industry
        ]
        if not industries_to_analyze:
            click.echo(f"错误: 未找到指定行业: {', '.join(industry)}", err=True)
            return
    else:
        click.echo("错误: 请使用 --all 或 --industry 指定要分析的行业", err=True)
        return

    click.echo(f"\n开始分析 {len(industries_to_analyze)} 个行业...")
    click.echo("=" * 80)

    # 初始化组件
    try:
        collector = DataCollector()
        engine = AnalysisEngine(config.get('analysis', {}))
        reporter = Reporter(config.get('output', {}).get('report_dir', 'reports'))
        db = ResultDB(config.get('output', {}).get('database', 'data/results.db')) if save_db else None
    except Exception as e:
        click.echo(f"错误: 初始化失败 - {e}", err=True)
        return

    # 连接数据源
    click.echo("正在连接数据源...")
    if not collector.connect():
        click.echo("错误: 数据源连接失败", err=True)
        return

    # 分析结果列表
    results = []

    try:
        # 分析每个行业
        for idx, ind_config in enumerate(industries_to_analyze, 1):
            industry_name = ind_config['name']
            sw_code = ind_config['sw_index_code']
            baostock_code = ind_config['baostock_code']

            click.echo(f"\n[{idx}/{len(industries_to_analyze)}] 正在分析: {industry_name}")
            click.echo("-" * 80)

            try:
                # 采集数据
                click.echo("  → 采集行业数据...")
                industry_data = collector.collect_industry(
                    industry_name=industry_name,
                    sw_code=sw_code,
                    baostock_code=baostock_code
                )

                if industry_data is None:
                    click.echo(f"  ✗ 数据采集失败，跳过该行业", err=True)
                    continue

                # 执行分析
                click.echo("  → 执行分析引擎...")
                analysis_result = engine.analyze_industry(
                    industry_name=industry_name,
                    sw_code=sw_code,
                    pe_percentile=industry_data.pe_percentile,
                    pb_percentile=industry_data.pb_percentile,
                    current_pe=industry_data.current_pe,
                    current_pb=industry_data.current_pb,
                    prosperity_percentile=industry_data.pe_percentile,  # 使用PE分位作为景气度代理
                    price_percentile=industry_data.pb_percentile,  # 使用PB分位作为价格分位代理
                    valuation_percentile=industry_data.pe_percentile,
                    price_trend=industry_data.price_trend,
                )

                # 转换为字典
                result_dict = analysis_result.to_dict()
                result_dict['run_date'] = analysis_result.analysis_time.strftime('%Y-%m-%d')
                results.append(result_dict)

                # 显示结果
                if output in ['console', 'both']:
                    _display_analysis_result(industry_name, result_dict)

                # 保存到数据库
                if save_db and db:
                    db_result = {
                        'run_date': result_dict['run_date'],
                        'industry': industry_name,
                        'prosperity_pct': result_dict.get('percentile', {}).get('pe', {}).get('percentile'),
                        'valuation_pct': result_dict.get('percentile', {}).get('pe', {}).get('percentile'),
                        'price_pct': result_dict.get('percentile', {}).get('pb', {}).get('percentile'),
                        'divergence_type': result_dict.get('divergence', {}).get('divergence_type'),
                        'divergence_strength': result_dict.get('divergence', {}).get('divergence_strength'),
                        'signal': result_dict.get('signal', {}).get('signal'),
                        'score_total': result_dict.get('scoring', {}).get('total_score'),
                        'score_level': result_dict.get('scoring', {}).get('level'),
                        'risk_warnings': str(result_dict.get('risk', {}).get('warnings', [])),
                        'recommendation': result_dict.get('signal', {}).get('recommendation'),
                        'raw_data': result_dict,
                    }
                    db.save_result(db_result)
                    click.echo(f"  ✓ 结果已保存到数据库")

                # 生成报告
                if generate_report:
                    reporter.generate(industry_name, result_dict, save_to_file=True)
                    click.echo(f"  ✓ 报告已生成")

            except Exception as e:
                logger.error(f"分析行业 {industry_name} 时出错: {e}", exc_info=True)
                click.echo(f"  ✗ 分析失败: {e}", err=True)
                continue

        # 显示汇总
        click.echo("\n" + "=" * 80)
        click.echo(f"分析完成！共分析 {len(results)} 个行业")
        click.echo("=" * 80)

        # 生成汇总报告
        if generate_report and results:
            summary_report = reporter.generate_summary(results)
            click.echo(f"\n汇总报告已生成")

    finally:
        # 断开数据源
        collector.disconnect()


def _display_analysis_result(industry_name: str, result: dict):
    """在控制台显示分析结果"""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    # 核心指标表格
    table = Table(title=f"{industry_name} - 核心指标", show_header=True, header_style="bold magenta")
    table.add_column("指标", style="cyan", width=20)
    table.add_column("数值", style="green", width=15)
    table.add_column("分位", style="yellow", width=10)

    percentile = result.get('percentile', {})
    if percentile.get('pe'):
        table.add_row("PE估值", f"{percentile['pe'].get('current', 'N/A')}", f"{percentile['pe'].get('percentile', 'N/A')}%")
    if percentile.get('pb'):
        table.add_row("PB估值", f"{percentile['pb'].get('current', 'N/A')}", f"{percentile['pb'].get('percentile', 'N/A')}%")

    console.print(table)

    # 信号判定
    signal = result.get('signal', {})
    if signal:
        signal_text = signal.get('signal', 'N/A')
        signal_color = {
            'buy': 'green',
            'sell': 'red',
            'hold': 'yellow'
        }.get(signal_text, 'white')

        console.print(f"\n[bold]信号判定:[/bold] [{signal_color}]{signal_text}[/{signal_color}]")
        if signal.get('recommendation'):
            console.print(f"[bold]操作建议:[/bold] {signal['recommendation']}")

    # 逆向评分
    scoring = result.get('scoring', {})
    if scoring:
        console.print(f"\n[bold]逆向评分:[/bold] {scoring.get('total_score', 'N/A')} 分")
        console.print(f"[bold]评级:[/bold] {scoring.get('level', 'N/A')}")

    # 风险提示
    risk = result.get('risk', {})
    if risk and risk.get('warnings'):
        console.print(f"\n[bold red]风险提示:[/bold red]")
        for warning in risk['warnings']:
            console.print(f"  • {warning}")


@cli.command()
@click.option('--date', '-d', help='查询指定日期的记录 (YYYY-MM-DD)')
@click.option('--industry', '-i', help='查询指定行业的历史记录')
@click.option('--signal', '-s', type=click.Choice(['buy', 'sell', 'hold']), help='按信号类型筛选')
@click.option('--latest', '-l', is_flag=True, help='显示最新的记录')
@click.option('--limit', type=int, default=10, help='返回记录数量限制')
@click.pass_context
def history(ctx, date, industry, signal, latest, limit):
    """
    查询历史分析记录

    示例:
        # 查询今天的记录
        python -m src.cli.main history --date 2024-01-15

        # 查询指定行业的历史记录
        python -m src.cli.main history --industry 航空机场

        # 查询买入信号
        python -m src.cli.main history --signal buy

        # 查询最新10条记录
        python -m src.cli.main history --latest --limit 10
    """
    config = ctx.obj['config']

    # 初始化数据库
    db_path = config.get('output', {}).get('database', 'data/results.db')
    db = ResultDB(db_path)

    # 查询数据
    results = []
    if date:
        results = db.query_by_date(date)
        click.echo(f"\n查询日期: {date}")
    elif industry:
        results = db.query_by_industry(industry, limit)
        click.echo(f"\n查询行业: {industry}")
    elif signal:
        results = db.query_by_signal(signal)
        click.echo(f"\n查询信号: {signal}")
    elif latest:
        results = db.query_latest(limit)
        click.echo(f"\n最新 {limit} 条记录")
    else:
        # 默认显示最新记录
        results = db.query_latest(limit)
        click.echo(f"\n最新 {limit} 条记录")

    if not results:
        click.echo("\n未找到符合条件的记录")
        return

    # 显示结果
    click.echo("=" * 100)
    _display_history_results(results)
    click.echo("=" * 100)
    click.echo(f"\n共 {len(results)} 条记录\n")


def _display_history_results(results: list):
    """显示历史记录"""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    # 创建表格
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("日期", style="cyan", width=12)
    table.add_column("行业", style="green", width=12)
    table.add_column("景气分位", width=10)
    table.add_column("估值分位", width=10)
    table.add_column("信号", width=8)
    table.add_column("得分", width=8)
    table.add_column("评级", width=15)
    table.add_column("操作建议", width=30)

    for result in results:
        # 信号颜色
        signal = result.get('signal', 'N/A')
        signal_color = {
            'buy': 'green',
            'sell': 'red',
            'hold': 'yellow'
        }.get(signal, 'white')

        table.add_row(
            result.get('run_date', 'N/A'),
            result.get('industry', 'N/A'),
            f"{result.get('prosperity_pct', 'N/A'):.1f}%" if result.get('prosperity_pct') else 'N/A',
            f"{result.get('valuation_pct', 'N/A'):.1f}%" if result.get('valuation_pct') else 'N/A',
            f"[{signal_color}]{signal}[/{signal_color}]",
            f"{result.get('score_total', 'N/A'):.1f}" if result.get('score_total') else 'N/A',
            result.get('score_level', 'N/A'),
            result.get('recommendation', 'N/A')[:30] if result.get('recommendation') else 'N/A'
        )

    console.print(table)


@cli.command()
@click.option('--date', '-d', help='导出指定日期的记录 (YYYY-MM-DD)')
@click.option('--industry', '-i', help='导出指定行业的记录')
@click.option('--signal', '-s', type=click.Choice(['buy', 'sell', 'hold']), help='按信号类型筛选')
@click.option('--format', '-f', type=click.Choice(['csv', 'excel', 'markdown']), default='csv', help='导出格式')
@click.option('--output', '-o', type=click.Path(), help='输出文件路径（不含扩展名）')
@click.option('--limit', type=int, default=100, help='导出记录数量限制')
@click.pass_context
def export(ctx, date, industry, signal, format, output, limit):
    """
    导出分析结果

    示例:
        # 导出今天的记录为 CSV
        python -m src.cli.main export --date 2024-01-15 --format csv

        # 导出指定行业的记录为 Excel
        python -m src.cli.main export --industry 航空机场 --format excel

        # 导出买入信号为 Markdown
        python -m src.cli.main export --signal buy --format markdown

        # 导出到指定文件
        python -m src.cli.main export --latest --format csv --output ./data/results/analysis
    """
    config = ctx.obj['config']

    # 初始化数据库和导出器
    db_path = config.get('output', {}).get('database', 'data/results.db')
    db = ResultDB(db_path)
    exporter = ResultExporter(config.get('output', {}).get('report_dir', 'data/results'))

    # 查询数据
    results = []
    if date:
        results = db.query_by_date(date)
        click.echo(f"\n导出日期: {date}")
    elif industry:
        results = db.query_by_industry(industry, limit)
        click.echo(f"\n导出行业: {industry}")
    elif signal:
        results = db.query_by_signal(signal)
        click.echo(f"\n导出信号: {signal}")
    else:
        # 默认导出最新记录
        results = db.query_latest(limit)
        click.echo(f"\n导出最新 {limit} 条记录")

    if not results:
        click.echo("\n未找到符合条件的记录，无法导出")
        return

    click.echo(f"找到 {len(results)} 条记录")

    # 导出文件
    try:
        if format == 'csv':
            filepath = exporter.export_csv(results, filename=output)
            if filepath:
                click.echo(f"✓ CSV 导出成功: {filepath}")
            else:
                click.echo("✗ CSV 导出失败", err=True)

        elif format == 'excel':
            filepath = exporter.export_excel(results, filename=output)
            if filepath:
                click.echo(f"✓ Excel 导出成功: {filepath}")
            else:
                click.echo("✗ Excel 导出失败", err=True)

        elif format == 'markdown':
            # 使用 Reporter 生成 Markdown 报告
            reporter = Reporter(config.get('output', {}).get('report_dir', 'reports'))
            if output:
                filepath = Path(output)
                filename = filepath.name
            else:
                filename = f"导出报告_{results[0].get('run_date', 'latest')}"

            # 生成汇总报告
            report_content = reporter.generate_summary(results)

            # 保存到文件
            filepath = reporter.output_dir / f"{filename}.md"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)

            click.echo(f"✓ Markdown 导出成功: {filepath}")

    except Exception as e:
        logger.error(f"导出失败: {e}", exc_info=True)
        click.echo(f"✗ 导出失败: {e}", err=True)


@cli.command()
@click.pass_context
def list_industries(ctx):
    """列出所有目标行业"""
    config = ctx.obj['config']
    industries = config.get('industries', {}).get('target_industries', [])

    if not industries:
        click.echo("未配置目标行业")
        return

    click.echo("\n目标行业列表:")
    click.echo("-" * 80)
    for i, industry in enumerate(industries, 1):
        click.echo(f"{i:2d}. {industry['name']:12s} | 申万代码: {industry['sw_index_code']:12s} | Baostock代码: {industry['baostock_code']}")
    click.echo("-" * 80)
    click.echo(f"共 {len(industries)} 个行业\n")


if __name__ == '__main__':
    cli()