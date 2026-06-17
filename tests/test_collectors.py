"""
阶段二验证脚本
验证数据采集模块是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_imports():
    """测试模块导入"""
    print("\n[1/6] 测试模块导入...")

    try:
        from src.data.collectors import (
            BaseCollector,
            BaostockCollector,
            AkshareCollector,
            MacroCollector,
        )
        print("  ✓ collectors 模块导入成功")

        from src.data import (
            DataCollector,
            IndustryData,
            IndustryMapper,
            IndustryPEPBHistoryCalculator,
            DataCache,
        )
        print("  ✓ data 模块导入成功")

        return True
    except Exception as e:
        print(f"  ✗ 模块导入失败: {e}")
        return False


def test_industry_mapper():
    """测试行业映射"""
    print("\n[2/6] 测试行业映射...")

    try:
        from src.data import IndustryMapper

        mapper = IndustryMapper()
        names = mapper.get_all_names()

        print(f"  ✓ 加载了 {len(names)} 个行业映射")
        for name in names:
            sw_code = mapper.get_sw_code(name)
            print(f"    - {name}: {sw_code}")

        # 测试获取特定行业
        mapping = mapper.get_mapping("航空机场")
        if mapping:
            print(f"  ✓ 获取'航空机场'映射成功")
        else:
            print(f"  ✗ 获取'航空机场'映射失败")
            return False

        return True
    except Exception as e:
        print(f"  ✗ 行业映射测试失败: {e}")
        return False


def test_akshare_collector():
    """测试 Akshare 采集器"""
    print("\n[3/6] 测试 Akshare 采集器...")

    try:
        from src.data.collectors import AkshareCollector

        collector = AkshareCollector()

        # 连接
        if not collector.connect():
            print("  ✗ Akshare 连接失败")
            return False
        print("  ✓ Akshare 连接成功")

        # 获取申万行业列表
        df = collector.get_sw_index_first_info()
        if not df.empty:
            print(f"  ✓ 获取申万一级行业: {len(df)} 个")
        else:
            print("  ⚠ 获取申万一级行业为空")

        # 获取申万二级行业估值
        df = collector.get_sw_index_second_info()
        if not df.empty:
            print(f"  ✓ 获取申万二级行业实时估值: {len(df)} 个")
        else:
            print("  ✗ 获取申万二级行业实时估值失败")
            return False

        # 获取特定行业估值
        pe_pb = collector.get_industry_pe_pb("航空机场")
        if pe_pb:
            print(f"  ✓ 获取'航空机场'估值: PE={pe_pb.get('pe_ttm')}, PB={pe_pb.get('pb')}")
        else:
            print("  ⚠ 获取'航空机场'估值失败")

        collector.disconnect()
        return True

    except Exception as e:
        print(f"  ✗ Akshare 采集器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_baostock_collector():
    """测试 Baostock 采集器"""
    print("\n[4/6] 测试 Baostock 采集器...")

    try:
        from src.data.collectors import BaostockCollector

        collector = BaostockCollector()

        # 连接
        if not collector.connect():
            print("  ✗ Baostock 连接失败")
            return False
        print("  ✓ Baostock 连接成功")

        # 获取股票行业分类
        df = collector.get_stock_industry()
        if not df.empty:
            print(f"  ✓ 获取股票行业分类: {len(df)} 只股票")
        else:
            print("  ⚠ 获取股票行业分类为空")

        # 获取 K 线数据
        df = collector.get_history_kline(
            code="sh.600519",
            start_date="2023-01-01",
            end_date="2024-12-31"
        )
        if not df.empty:
            print(f"  ✓ 获取K线数据: {len(df)} 条")
        else:
            print("  ⚠ 获取K线数据为空")

        # 获取利润表数据
        df = collector.get_profit_data(code="sh.600519", year="2023")
        if not df.empty:
            print(f"  ✓ 获取利润表数据: {len(df)} 条")
        else:
            print("  ⚠ 获取利润表数据为空")

        collector.disconnect()
        return True

    except Exception as e:
        print(f"  ✗ Baostock 采集器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pe_pb_calculator():
    """测试 PE/PB 计算器"""
    print("\n[5/6] 测试 PE/PB 计算器...")

    try:
        from src.data import IndustryPEPBHistoryCalculator

        calculator = IndustryPEPBHistoryCalculator()

        # 连接
        if not calculator.connect():
            print("  ✗ PE/PB 计算器连接失败")
            return False
        print("  ✓ PE/PB 计算器连接成功")

        # 获取当前 PE/PB
        pe_pb = calculator.get_current_pe_pb("801991.SI")
        if pe_pb:
            print(f"  ✓ 获取'航空机场'当前PE/PB: PE={pe_pb.get('pe_ttm')}, PB={pe_pb.get('pb')}")
        else:
            print("  ✗ 获取当前PE/PB失败")
            return False

        # 计算分位
        percentile = calculator.calculate_percentile("801991.SI")
        if percentile.get('percentile') is not None:
            print(f"  ✓ 计算点位分位: {percentile.get('percentile')}%")
        else:
            print("  ⚠ 计算点位分位失败")

        # 获取趋势
        trend = calculator.get_trend("801991.SI", window=12)
        if trend:
            print(f"  ✓ 获取趋势: {trend.get('趋势')}, 变化={trend.get('窗口变化率')}%")

        calculator.disconnect()
        return True

    except Exception as e:
        print(f"  ✗ PE/PB 计算器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_collector():
    """测试统一数据采集器"""
    print("\n[6/6] 测试统一数据采集器...")

    try:
        from src.data import DataCollector

        collector = DataCollector()

        # 连接
        if not collector.connect():
            print("  ✗ 数据采集器连接失败")
            return False
        print("  ✓ 数据采集器连接成功")

        # 采集单个行业
        data = collector.collect_industry("航空机场")
        if data:
            print(f"  ✓ 采集'航空机场'数据成功:")
            print(f"    - PE(TTM): {data.current_pe}")
            print(f"    - PB: {data.current_pb}")
            print(f"    - 点位分位: {data.pe_percentile}%")
            print(f"    - 价格趋势: {data.price_trend}")
        else:
            print("  ⚠ 采集'航空机场'数据失败")

        collector.disconnect()
        return True

    except Exception as e:
        print(f"  ✗ 统一数据采集器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("阶段二验证：数据采集模块测试")
    print("=" * 60)

    results = []

    # 运行测试
    results.append(("模块导入", test_imports()))
    results.append(("行业映射", test_industry_mapper()))
    results.append(("Akshare 采集器", test_akshare_collector()))
    results.append(("Baostock 采集器", test_baostock_collector()))
    results.append(("PE/PB 计算器", test_pe_pb_calculator()))
    results.append(("统一数据采集器", test_data_collector()))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    print(f"\n通过: {passed}/{total}")

    if passed == total:
        print("\n✓ 阶段二验证全部通过！")
        return 0
    else:
        print(f"\n⚠ 阶段二验证有 {total - passed} 项未通过")
        return 1


if __name__ == "__main__":
    sys.exit(main())
