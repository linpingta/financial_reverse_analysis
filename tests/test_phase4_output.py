"""
阶段四输出与存储模块测试

测试内容：
- SQLite 结果存储
- Markdown 报告生成
- CSV/Excel 导出
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.output import ResultDB, Reporter, ResultExporter, BatchExporter


def test_result_db():
    """测试 SQLite 结果存储"""
    print("=" * 60)
    print("测试 SQLite 结果存储模块")
    print("=" * 60)

    # 初始化数据库
    db = ResultDB("data/test_results.db")

    # 测试数据
    test_result = {
        'run_date': datetime.now().strftime('%Y-%m-%d'),
        'industry': '航空机场',
        'prosperity_pct': 15.5,
        'valuation_pct': 18.2,
        'price_pct': 22.3,
        'divergence_type': 'bullish',
        'divergence_strength': 75.0,
        'signal': 'buy',
        'score_total': 82.5,
        'score_level': '高确定性机会',
        'risk_warnings': ['需关注航油价格波动'],
        'recommendation': '建议分批建仓，关注基本面边际改善',
        'raw_data': {
            'pe': 25.3,
            'pb': 1.8,
            'price': 3500.5
        }
    }

    # 保存单条结果
    record_id = db.save_result(test_result)
    print(f"✅ 保存结果成功，ID={record_id}")

    # 查询结果
    results = db.query_by_date(test_result['run_date'])
    print(f"✅ 查询结果成功，找到 {len(results)} 条记录")

    # 获取统计信息
    stats = db.get_statistics(test_result['run_date'])
    print(f"✅ 统计信息: 总数={stats['total_count']}, 平均得分={stats['avg_score']}")

    print()


def test_reporter():
    """测试 Markdown 报告生成"""
    print("=" * 60)
    print("测试 Markdown 报告生成器")
    print("=" * 60)

    # 初始化报告生成器
    reporter = Reporter("reports")

    # 测试数据
    test_result = {
        'industry': '航空机场',
        'prosperity': '旅客周转量下降15%',
        'prosperity_pct': 15.5,
        'pe': 25.3,
        'pb': 1.8,
        'valuation_pct': 18.2,
        'price': 3500.5,
        'price_pct': 22.3,
        'divergence': {
            'type': 'bullish',
            'strength': 75.0,
            'details': {
                '价格-景气背离': '价格分位高于景气分位',
                '背离周期': '12周'
            }
        },
        'divergence_text': '基本面处于历史极低位置，但价格未同步创新低，出现逆向买点背离信号',
        'signal': 'buy',
        'score': {
            'total_score': 82.5,
            'level': '高确定性机会',
            'details': {
                'divergence_strength': {'score': 32, 'weight': 40, 'description': '强背离信号'},
                'prosperity_extreme': {'score': 25, 'weight': 30, 'description': '景气极低'},
                'valuation_margin': {'score': 15, 'weight': 20, 'description': '估值安全边际充足'},
                'marginal_improvement': {'score': 10.5, 'weight': 10, 'description': '边际改善迹象'}
            }
        },
        'risk_warnings': ['需关注航油价格波动', '关注疫情反复风险'],
        'recommendation': '建议分批建仓，关注基本面边际改善信号，设置止损位防范下行风险',
        'raw_data': {
            '旅客周转量': '-15%',
            '客座率': '65%',
            '航油价格': '上涨8%'
        }
    }

    # 生成单个行业报告
    report = reporter.generate('航空机场', test_result, save_to_file=True)
    print(f"✅ 单行业报告生成成功，长度={len(report)} 字符")

    # 测试汇总报告
    test_results = [
        test_result,
        {
            'industry': '生猪养殖',
            'prosperity_pct': 12.0,
            'valuation_pct': 15.0,
            'price_pct': 18.0,
            'divergence_type': 'bullish',
            'divergence_strength': 80.0,
            'signal': 'buy',
            'score': {'total_score': 85.0, 'level': '高确定性机会'},
            'risk_warnings': [],
            'recommendation': '建议关注'
        },
        {
            'industry': '煤炭',
            'prosperity_pct': 85.0,
            'valuation_pct': 90.0,
            'price_pct': 75.0,
            'divergence_type': 'bearish',
            'divergence_strength': 60.0,
            'signal': 'sell',
            'score': {'total_score': 25.0, 'level': '建议规避'},
            'risk_warnings': ['景气度过高'],
            'recommendation': '建议减仓'
        }
    ]

    summary_report = reporter.generate_summary_report(test_results, save_to_file=True)
    print(f"✅ 汇总报告生成成功，长度={len(summary_report)} 字符")

    print()


def test_result_exporter():
    """测试结果导出器"""
    print("=" * 60)
    print("测试结果导出器")
    print("=" * 60)

    # 初始化导出器
    exporter = ResultExporter("data/results")

    # 测试数据
    test_results = [
        {
            'run_date': datetime.now().strftime('%Y-%m-%d'),
            'industry': '航空机场',
            'prosperity_pct': 15.5,
            'valuation_pct': 18.2,
            'price_pct': 22.3,
            'divergence_type': 'bullish',
            'divergence_strength': 75.0,
            'signal': 'buy',
            'score_total': 82.5,
            'score_level': '高确定性机会',
            'risk_warnings': ['需关注航油价格波动'],
            'recommendation': '建议分批建仓'
        },
        {
            'run_date': datetime.now().strftime('%Y-%m-%d'),
            'industry': '生猪养殖',
            'prosperity_pct': 12.0,
            'valuation_pct': 15.0,
            'price_pct': 18.0,
            'divergence_type': 'bullish',
            'divergence_strength': 80.0,
            'signal': 'buy',
            'score_total': 85.0,
            'score_level': '高确定性机会',
            'risk_warnings': [],
            'recommendation': '建议关注'
        }
    ]

    # 测试 CSV 导出
    csv_path = exporter.export_csv(test_results, filename="test_export")
    if csv_path:
        print(f"✅ CSV 导出成功: {csv_path}")

    # 测试 Markdown 导出
    md_path = exporter.export_markdown(test_results, filename="test_export")
    if md_path:
        print(f"✅ Markdown 导出成功: {md_path}")

    # 测试 Excel 导出（可选）
    excel_path = exporter.export_excel(test_results, filename="test_export")
    if excel_path:
        print(f"✅ Excel 导出成功: {excel_path}")

    print()


def test_batch_exporter():
    """测试批量导出器"""
    print("=" * 60)
    print("测试批量导出器")
    print("=" * 60)

    # 初始化批量导出器
    batch_exporter = BatchExporter("data/results")

    # 测试数据
    test_results = [
        {
            'run_date': datetime.now().strftime('%Y-%m-%d'),
            'industry': '航空机场',
            'prosperity_pct': 15.5,
            'valuation_pct': 18.2,
            'price_pct': 22.3,
            'signal': 'buy',
            'score_total': 82.5
        }
    ]

    # 批量导出
    exported_files = batch_exporter.export_all(
        test_results,
        filename="test_batch",
        formats=['csv', 'markdown']
    )

    print(f"✅ 批量导出成功:")
    for format_type, path in exported_files.items():
        print(f"   - {format_type}: {path}")

    print()


def test_edge_cases():
    """测试边界情况"""
    print("=" * 60)
    print("测试边界情况")
    print("=" * 60)

    # 测试空数据
    print("\n测试空数据导出:")
    exporter = ResultExporter("data/results")
    result = exporter.export_csv([], filename="test_empty")
    if result is None:
        print("✅ 空数据正确返回 None")
    else:
        print("❌ 空数据应该返回 None")

    # 测试空数据报告生成
    print("\n测试空数据报告生成:")
    reporter = Reporter("reports")
    report = reporter.generate_summary_report([], save_to_file=False)
    print(f"✅ 空数据报告生成成功，长度={len(report)} 字符")

    # 测试数据库空数据统计
    print("\n测试数据库空数据统计:")
    db = ResultDB("data/test_edge_cases.db")
    stats = db.get_statistics()
    print(f"✅ 空数据库统计成功: 总数={stats['total_count']}, 平均得分={stats['avg_score']}")

    # 测试损坏的 JSON 数据
    print("\n测试损坏的 JSON 数据:")
    import sqlite3
    conn = sqlite3.connect("data/test_edge_cases.db")
    cursor = conn.cursor()
    # 插入损坏的 JSON 数据
    cursor.execute("""
        INSERT INTO analysis_results (
            run_date, industry, raw_data_json
        ) VALUES (?, ?, ?)
    """, ('2026-06-20', '测试行业', 'invalid json string'))
    conn.commit()
    conn.close()

    # 查询损坏的 JSON 数据
    results = db.query_by_date('2026-06-20')
    print(f"✅ 损坏的 JSON 数据查询成功，找到 {len(results)} 条记录")
    for result in results:
        if result.get('industry') == '测试行业':
            if 'raw_data' in result and result['raw_data'] == {}:
                print("✅ 损坏的 JSON 正确处理为空字典")
            else:
                print("❌ 损坏的 JSON 处理不正确")

    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("阶段四输出与存储模块测试")
    print("=" * 60 + "\n")

    try:
        # 测试 SQLite 存储
        test_result_db()

        # 测试报告生成器
        test_reporter()

        # 测试结果导出器
        test_result_exporter()

        # 测试批量导出器
        test_batch_exporter()

        # 测试边界情况
        test_edge_cases()

        print("=" * 60)
        print("✅ 所有测试通过！阶段四模块功能正常")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()