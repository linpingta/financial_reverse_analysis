"""
CLI 单元测试

测试内容：
- CLI 主入口
- analyze 命令
- history 命令
- export 命令
- list_industries 命令
"""

import sys
import pytest
from pathlib import Path
from click.testing import CliRunner
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.cli.main import cli
from src.output.result_db import ResultDB


@pytest.fixture
def runner():
    """Click 测试运行器"""
    return CliRunner()


@pytest.fixture
def test_db():
    """测试数据库"""
    db = ResultDB("data/test_cli.db")

    # 插入测试数据
    test_results = [
        {
            'run_date': '2024-01-15',
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
            'recommendation': '建议分批建仓',
            'raw_data': {}
        },
        {
            'run_date': '2024-01-15',
            'industry': '生猪养殖',
            'prosperity_pct': 25.0,
            'valuation_pct': 30.0,
            'price_pct': 35.0,
            'divergence_type': 'none',
            'divergence_strength': 0.0,
            'signal': 'hold',
            'score_total': 50.0,
            'score_level': '观察期',
            'risk_warnings': [],
            'recommendation': '建议观望',
            'raw_data': {}
        },
        {
            'run_date': '2024-01-14',
            'industry': '航空机场',
            'prosperity_pct': 20.0,
            'valuation_pct': 25.0,
            'price_pct': 30.0,
            'divergence_type': 'bearish',
            'divergence_strength': 60.0,
            'signal': 'sell',
            'score_total': 30.0,
            'score_level': '风险较高',
            'risk_warnings': ['产能过剩风险'],
            'recommendation': '建议减仓',
            'raw_data': {}
        }
    ]

    for result in test_results:
        db.save_result(result)

    yield db

    # 清理测试数据库
    Path("data/test_cli.db").unlink(missing_ok=True)


class TestCLI:
    """CLI 主入口测试"""

    def test_version_command(self, runner):
        """测试 version 命令"""
        result = runner.invoke(cli, ['version'])
        assert result.exit_code == 0
        assert '逆向周期行业投资分析系统' in result.output
        assert '版本' in result.output

    def test_list_industries_command(self, runner):
        """测试 list_industries 命令"""
        result = runner.invoke(cli, ['list-industries'])
        assert result.exit_code == 0
        assert '目标行业列表' in result.output
        assert '航空机场' in result.output
        assert '生猪养殖' in result.output

    def test_cli_help(self, runner):
        """测试 CLI 帮助信息"""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert '逆向周期行业投资分析系统' in result.output
        assert 'analyze' in result.output
        assert 'history' in result.output
        assert 'export' in result.output


class TestHistoryCommand:
    """history 命令测试"""

    def test_history_latest(self, runner, test_db):
        """测试查询最新记录"""
        result = runner.invoke(cli, ['history', '--latest'])
        assert result.exit_code == 0
        assert '最新' in result.output

    def test_history_by_date(self, runner, test_db):
        """测试按日期查询"""
        result = runner.invoke(cli, ['history', '--date', '2024-01-15'])
        assert result.exit_code == 0
        assert '2024-01-15' in result.output

    def test_history_by_industry(self, runner, test_db):
        """测试按行业查询"""
        result = runner.invoke(cli, ['history', '--industry', '航空机场'])
        assert result.exit_code == 0
        assert '航空机场' in result.output

    def test_history_by_signal(self, runner, test_db):
        """测试按信号查询"""
        result = runner.invoke(cli, ['history', '--signal', 'buy'])
        assert result.exit_code == 0
        assert 'buy' in result.output

    def test_history_no_results(self, runner):
        """测试无结果查询"""
        result = runner.invoke(cli, ['history', '--date', '2099-01-01'])
        assert result.exit_code == 0
        assert '未找到符合条件的记录' in result.output


class TestExportCommand:
    """export 命令测试"""

    def test_export_csv(self, runner, test_db):
        """测试导出 CSV"""
        result = runner.invoke(cli, ['export', '--latest', '--format', 'csv'])
        assert result.exit_code == 0
        assert '导出最新' in result.output

    def test_export_excel(self, runner, test_db):
        """测试导出 Excel"""
        result = runner.invoke(cli, ['export', '--latest', '--format', 'excel'])
        assert result.exit_code == 0
        assert '导出最新' in result.output

    def test_export_markdown(self, runner, test_db):
        """测试导出 Markdown"""
        result = runner.invoke(cli, ['export', '--latest', '--format', 'markdown'])
        assert result.exit_code == 0
        assert '导出最新' in result.output

    def test_export_no_results(self, runner):
        """测试无结果导出"""
        result = runner.invoke(cli, ['export', '--date', '2099-01-01'])
        assert result.exit_code == 0
        assert '未找到符合条件的记录' in result.output


class TestAnalyzeCommand:
    """analyze 命令测试"""

    def test_analyze_help(self, runner):
        """测试 analyze 命令帮助"""
        result = runner.invoke(cli, ['analyze', '--help'])
        assert result.exit_code == 0
        assert '分析行业投资机会' in result.output
        assert '--all' in result.output
        assert '--industry' in result.output

    def test_analyze_no_options(self, runner):
        """测试无选项时的错误提示"""
        result = runner.invoke(cli, ['analyze'])
        assert result.exit_code == 0
        assert '错误' in result.output
        assert '请使用 --all 或 --industry' in result.output

    def test_analyze_invalid_industry(self, runner):
        """测试无效行业名称"""
        result = runner.invoke(cli, ['analyze', '--industry', '无效行业'])
        assert result.exit_code == 0
        assert '错误' in result.output
        assert '未找到指定行业' in result.output


def test_cli_integration():
    """CLI 集成测试"""
    runner = CliRunner()

    # 测试完整流程
    # 1. 查看版本
    result = runner.invoke(cli, ['version'])
    assert result.exit_code == 0

    # 2. 列出行业
    result = runner.invoke(cli, ['list-industries'])
    assert result.exit_code == 0

    # 3. 查看历史（使用测试数据库）
    result = runner.invoke(cli, ['history', '--latest'])
    assert result.exit_code == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])