"""
PE/PB 估值数据源专项测试
"""

import sys
import logging
from datetime import datetime, timedelta

import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

result_tests = []


def add_test(name, success, message="", preview=""):
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"\n{status}: {name}")
    if message:
        print(f"  消息: {message}")
    if preview:
        print(f"  预览:\n{preview[:300]}..." if len(preview) > 300 else f"  预览:\n{preview}")
    result_tests.append({"name": name, "success": success})


# ============================================================================
# 方案1: Baostock 财务数据计算 PE/PB
# ============================================================================

def test_baostock_pe_pb():
    """测试 Baostock 财务数据自行计算 PE/PB"""
    log.info("测试 Baostock 财务数据...")

    try:
        import baostock as bs

        # 登录
        lg = bs.login()
        if lg.error_code != '0':
            add_test("baostock: 登录", False, lg.error_msg)
            return

        # 测试1: 获取个股利润表
        try:
            rs = bs.query_profit_statement_data(
                code="sh.600519",  # 贵州茅台
                start_date="2023-01-01",
                end_date=datetime.now().strftime("%Y-%m-%d")
            )

            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())

            if len(data_list) > 0:
                df = pd.DataFrame(data_list, columns=rs.fields)
                add_test(
                    "baostock: 个股利润表",
                    True,
                    f"获取到 {len(df)} 条财务数据",
                    df.head(3).to_string()
                )
            else:
                add_test("baostock: 个股利润表", False, "无数据")
        except Exception as e:
            add_test("baostock: 个股利润表", False, str(e))

        # 测试2: 获取个股资产负债表
        try:
            rs = bs.query_balance_sheet_data(
                code="sh.600519",
                start_date="2023-01-01",
                end_date=datetime.now().strftime("%Y-%m-%d")
            )

            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())

            if len(data_list) > 0:
                df = pd.DataFrame(data_list, columns=rs.fields)
                add_test(
                    "baostock: 个股资产负债表",
                    True,
                    f"获取到 {len(df)} 条数据",
                    df.head(2).to_string()
                )
            else:
                add_test("baostock: 个股资产负债表", False, "无数据")
        except Exception as e:
            add_test("baostock: 个股资产负债表", False, str(e))

        # 测试3: 查询主要统计指标（包含 EPS, BVPS）
        try:
            rs = bs.query_performance_summary_date(
                code="sh.600519",
                start_date="2023-01-01",
                end_date=datetime.now().strftime("%Y-%m-%d")
            )

            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())

            if len(data_list) > 0:
                df = pd.DataFrame(data_list, columns=rs.fields)
                add_test(
                    "baostock: 业绩指标(EPS/BVPS)",
                    True,
                    f"获取到 {len(df)} 条数据",
                    df.head(3).to_string()
                )
            else:
                add_test("baostock: 业绩指标", False, "无数据")
        except Exception as e:
            add_test("baostock: 业绩指标", False, str(e))

        bs.logout()

    except ImportError:
        add_test("baostock", False, "请安装: pip install baostock")
    except Exception as e:
        add_test("baostock", False, str(e))


# ============================================================================
# 方案2: 申万行业指数估值
# ============================================================================

def test_shenwan():
    """测试申万行业指数估值"""
    log.info("测试申万行业估值...")

    try:
        import akshare as ak

        # 申万行业指数估值
        try:
            # 尝试申万行业指数历史 PE/PB
            df = ak.sw_index_second_individual_spot(
                end_date=datetime.now().strftime("%Y%m%d")
            )
            add_test(
                "申万行业指数实时估值",
                True,
                f"获取到 {len(df)} 个行业数据",
                df.head(3).to_string()
            )
        except Exception as e:
            add_test("申万行业指数实时估值", False, str(e))

        # 申万一级行业列表
        try:
            df = ak.sw_index_second_info()
            add_test(
                "申万二级行业列表",
                True,
                f"获取到 {len(df)} 个行业",
                df.head(5).to_string()
            )
        except Exception as e:
            add_test("申万二级行业列表", False, str(e))

    except Exception as e:
        add_test("申万接口", False, str(e))


# ============================================================================
# 方案3: 中证指数公司估值数据
# ============================================================================

def test_csi_index():
    """测试中证指数公司估值数据"""
    log.info("测试中证指数估值...")

    try:
        import requests

        # 中证指数公司官网
        url = "http://www.csindex.com.cn/zh-CN/indices/index-detail#/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            add_test(
                "中证指数公司官网",
                resp.status_code == 200,
                f"状态码: {resp.status_code}"
            )
        except Exception as e:
            add_test("中证指数公司官网", False, str(e))

        # 尝试获取估值数据 API
        try:
            # 中证指数 PE/PB 估值数据接口（如果存在）
            url = "http://www.csindex.com.cn/csindex-home/index/one-min/000300"
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=10)
            add_test(
                "中证指数API",
                resp.status_code == 200,
                f"状态码: {resp.status_code}, 响应: {resp.text[:100]}"
            )
        except Exception as e:
            add_test("中证指数API", False, str(e))

    except ImportError:
        add_test("requests", False, "requests 未安装")


# ============================================================================
# 方案4: 理杏仁估值数据
# ============================================================================

def test_lixinger():
    """测试理杏仁估值数据"""
    log.info("测试理杏仁估值...")

    try:
        import requests

        url = "https://www.lixinger.com/"
        headers = {'User-Agent': 'Mozilla/5.0'}

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            add_test(
                "理杏仁官网",
                resp.status_code == 200,
                f"状态码: {resp.status_code}"
            )
        except Exception as e:
            add_test("理杏仁官网", False, str(e))

    except ImportError:
        add_test("理杏仁", False, "requests 未安装")


# ============================================================================
# 方案5: 乐咕乐股/乌龟量化等
# ============================================================================

def test_other_sources():
    """测试其他估值数据源"""
    log.info("测试其他估值数据源...")

    try:
        import requests

        # 乐咕乐股
        try:
            url = "https://legulegu.com/stockdata/market-cap"
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=10)
            add_test(
                "乐咕乐股",
                resp.status_code == 200,
                f"状态码: {resp.status_code}"
            )
        except Exception as e:
            add_test("乐咕乐股", False, str(e))

        # 尝试 akshare 的估值相关接口
        try:
            import akshare as ak

            # 尝试获取 A 股恐慌贪婪指数（包含市场估值）
            df = ak.stock_fear_greed_index_em()
            add_test(
                "akshare: 市场情绪(恐慌贪婪)",
                True,
                f"获取到 {len(df)} 条数据",
                df.tail(3).to_string() if len(df) > 0 else "无数据"
            )
        except Exception as e:
            add_test("akshare: 市场情绪", False, str(e))

    except ImportError:
        add_test("其他数据源", False, "requests 未安装")


# ============================================================================
# 方案6: 基于指数点位和财务数据自行计算
# ============================================================================

def test_calculate_pe_pb():
    """测试自行计算 PE/PB"""
    log.info("测试自行计算 PE/PB...")

    try:
        import baostock as bs

        lg = bs.login()
        if lg.error_code != '0':
            add_test("自行计算PE/PB: 登录", False, lg.error_msg)
            return

        # 获取沪深300指数历史数据
        try:
            rs = bs.query_history_k_data_plus(
                "sh.000300",
                "date,close",
                start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                end_date=datetime.now().strftime("%Y-%m-%d"),
                frequency="d"
            )

            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())

            if len(data_list) > 0:
                df_price = pd.DataFrame(data_list, columns=rs.fields)
                add_test(
                    "沪深300历史价格数据",
                    True,
                    f"获取到 {len(df_price)} 条数据",
                    df_price.tail(3).to_string()
                )
            else:
                add_test("沪深300历史价格数据", False, "无数据")
        except Exception as e:
            add_test("沪深300历史价格数据", False, str(e))

        # 获取指数成分股
        try:
            rs = bs.query_hs300_stocks()
            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())

            if len(data_list) > 0:
                df = pd.DataFrame(data_list, columns=rs.fields)
                add_test(
                    "沪深300成分股",
                    True,
                    f"获取到 {len(df)} 只成分股",
                    df.head(3).to_string()
                )
            else:
                add_test("沪深300成分股", False, "无数据")
        except Exception as e:
            add_test("沪深300成分股", False, str(e))

        bs.logout()

        # 说明计算方法
        print("\n" + "=" * 50)
        print("【自行计算 PE/PB 的方法】")
        print("=" * 50)
        print("""
方案1: 指数 PE = 指数点位 / 指数 EPS
       - 需要获取指数的历史 EPS（成分股加权平均）

方案2: 指数 PB = 指数点位 / 指数 BPS
       - 需要获取指数的历史 BPS（成分股加权平均）

方案3: 使用 PE_TTM = 市值总和 / 净利润TTM总和
       - 需要获取所有成分股的当前市值和TTM净利润
       - 适合计算行业指数 PE

baostock 可以提供成分股财务数据，理论上可以计算
        """)

    except ImportError:
        add_test("baostock", False, "请安装: pip install baostock")
    except Exception as e:
        add_test("baostock", False, str(e))


# ============================================================================
# 主函数
# ============================================================================

def main():
    print("\n" + "=" * 70)
    print("PE/PB 估值数据源专项测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 方案1: Baostock 财务数据
    print("\n>>> 方案1: Baostock 财务数据 <<<")
    test_baostock_pe_pb()

    # 方案2: 申万行业指数
    print("\n>>> 方案2: 申万行业指数 <<<")
    test_shenwan()

    # 方案3: 中证指数公司
    print("\n>>> 方案3: 中证指数公司 <<<")
    test_csi_index()

    # 方案4: 理杏仁
    print("\n>>> 方案4: 理杏仁 <<<")
    test_lixinger()

    # 方案5: 其他来源
    print("\n>>> 方案5: 其他数据源 <<<")
    test_other_sources()

    # 方案6: 自行计算
    print("\n>>> 方案6: 自行计算 PE/PB <<<")
    test_calculate_pe_pb()

    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)

    passed = sum(1 for t in result_tests if t["success"])
    total = len(result_tests)

    print(f"\n通过: {passed}/{total}")
    for t in result_tests:
        status = "✓" if t["success"] else "✗"
        print(f"  {status} {t['name']}")

    print("\n>>> 最终建议 <<<")
    print("""
基于测试结果，推荐以下 PE/PB 数据方案：

【首选方案】申万行业指数
  - akshare.sw_index_second_individual_spot() 可获取实时行业估值
  - 覆盖主要行业，数据较为全面

【备选方案】Baostock 自行计算
  - 使用 query_hs300_stocks() 获取成分股
  - 使用 query_profit_statement_data() 获取财务数据
  - 自行计算加权 PE/PB

【说明】
  申万指数与中国证监行业分类不完全对应，需要做映射
  建议先用申万数据测试，如果覆盖不足再用 baostock 自行计算
""")


if __name__ == "__main__":
    main()
