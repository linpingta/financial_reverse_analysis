"""
CLI 功能验证脚本

验证阶段五开发的 CLI 命令是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from click.testing import CliRunner
from src.cli.main import cli


def test_cli_commands():
    """测试 CLI 命令"""
    runner = CliRunner()

    print("=" * 80)
    print("CLI 功能验证测试")
    print("=" * 80)

    # 1. 测试 version 命令
    print("\n[1] 测试 version 命令")
    print("-" * 80)
    result = runner.invoke(cli, ['version'])
    print(f"退出码: {result.exit_code}")
    print(f"输出:\n{result.output}")
    assert result.exit_code == 0
    print("✓ version 命令测试通过")

    # 2. 测试 list_industries 命令
    print("\n[2] 测试 list_industries 命令")
    print("-" * 80)
    result = runner.invoke(cli, ['list-industries'])
    print(f"退出码: {result.exit_code}")
    print(f"输出:\n{result.output}")
    assert result.exit_code == 0
    print("✓ list_industries 命令测试通过")

    # 3. 测试 CLI 帮助信息
    print("\n[3] 测试 CLI 帮助信息")
    print("-" * 80)
    result = runner.invoke(cli, ['--help'])
    print(f"退出码: {result.exit_code}")
    print(f"输出:\n{result.output}")
    assert result.exit_code == 0
    print("✓ CLI 帮助信息测试通过")

    # 4. 测试 analyze 命令帮助
    print("\n[4] 测试 analyze 命令帮助")
    print("-" * 80)
    result = runner.invoke(cli, ['analyze', '--help'])
    print(f"退出码: {result.exit_code}")
    print(f"输出:\n{result.output}")
    assert result.exit_code == 0
    print("✓ analyze 命令帮助测试通过")

    # 5. 测试 history 命令帮助
    print("\n[5] 测试 history 命令帮助")
    print("-" * 80)
    result = runner.invoke(cli, ['history', '--help'])
    print(f"退出码: {result.exit_code}")
    print(f"输出:\n{result.output}")
    assert result.exit_code == 0
    print("✓ history 命令帮助测试通过")

    # 6. 测试 export 命令帮助
    print("\n[6] 测试 export 命令帮助")
    print("-" * 80)
    result = runner.invoke(cli, ['export', '--help'])
    print(f"退出码: {result.exit_code}")
    print(f"输出:\n{result.output}")
    assert result.exit_code == 0
    print("✓ export 命令帮助测试通过")

    # 7. 测试 analyze 命令错误提示
    print("\n[7] 测试 analyze 命令错误提示")
    print("-" * 80)
    result = runner.invoke(cli, ['analyze'])
    print(f"退出码: {result.exit_code}")
    print(f"输出:\n{result.output}")
    assert result.exit_code == 0
    assert '错误' in result.output
    print("✓ analyze 命令错误提示测试通过")

    # 8. 测试 history 命令无结果
    print("\n[8] 测试 history 命令无结果")
    print("-" * 80)
    result = runner.invoke(cli, ['history', '--date', '2099-01-01'])
    print(f"退出码: {result.exit_code}")
    print(f"输出:\n{result.output}")
    assert result.exit_code == 0
    assert '未找到符合条件的记录' in result.output
    print("✓ history 命令无结果测试通过")

    print("\n" + "=" * 80)
    print("所有 CLI 功能验证测试通过！")
    print("=" * 80)


if __name__ == '__main__':
    try:
        test_cli_commands()
        print("\n✓ CLI 验证成功")
    except Exception as e:
        print(f"\n✗ CLI 验证失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)