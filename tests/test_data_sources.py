"""
数据源可行性测试脚本
用于验证 Akshare 和 Tushare 数据获取能力

使用方法:
    python tests/test_data_sources.py

依赖安装:
    pip install akshare tushare pandas
"""

import sys
import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

# ============================================================================
# 数据源配置
# ============================================================================

# 预设周期行业及其对应的指数代码（待验证调整）
INDUSTRY_INDEX_MAP = {
    "航空机场": "881001",
    "生猪养殖": "801012",
    "基础化工": "801032",
    "煤炭": "801022",
    "有色金属": "801005",
    "远洋航运": "801014",
    "酒店旅游": "801010",
    "周期半导体": "801081",
    "光伏上游": "801023",
    "工程机械": "801018",
}

# Tushare Token（需要用户配置）
TUSHARE_TOKEN: Optional[str] = "7f3a04e7858fbe2451bc30d5170e08d366c5cfea68f70fb1f5323efb"


# ============================================================================
# 测试结果收集
# ============================================================================

class TestResult:
    def __init__(self):
        self.tests = []

    def add(self, name: str, success: bool, message: str = "", data_preview: str = ""):
        self.tests.append({
            "name": name,
            "success": success,
            "message": message,
            "data_preview": data_preview
        })

    def print_report(self):
        print("\n" + "=" * 70)
        print("数据源可行性测试报告")
        print("=" * 70)

        passed = sum(1 for t in self.tests if t["success"])
        total = len(self.tests)

        for t in self.tests:
            status = "✓ PASS" if t["success"] else "✗ FAIL"
            print(f"\n{status}: {t['name']}")
            if t["message"]:
                print(f"  消息: {t['message']}")
            if t["data_preview"]:
                print(f"  数据预览:\n{t['data_preview']}")

        print("\n" + "-" * 70)
        print(f"总计: {passed}/{total} 项测试通过")
        print("=" * 70)

        return passed == total


result = TestResult()


# ============================================================================
# Akshare 数据源测试
# ============================================================================

def test_akshare_index():
    """测试 Akshare 行业指数数据获取"""
    log.info("测试 Akshare 行业指数数据获取...")

    try:
        import akshare as ak

        # 测试1: 获取沪深京 A 股行业板块指数
        try:
            log.info("尝试获取行业板块数据...")
            df = ak.stock_board_industry_name_em()
            result.add(
                "akshare: 行业板块列表",
                True,
                f"获取到 {len(df)} 个行业",
                df.head(3).to_string() if len(df) > 0 else "无数据"
            )
        except Exception as e:
            log.warning(f"行业板块列表获取失败: {e}")
            result.add("akshare: 行业板块列表", False, str(e))

        # 测试2: 获取单个行业的历史数据
        try:
            # 使用 akshare 默认的航空行业代码
            symbol = "881001"  # 航空机场
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
            end_date = datetime.now().strftime("%Y%m%d")

            log.info(f"尝试获取行业指数历史数据: {symbol}")
            # 注意: akshare 的接口可能有变化，这里使用通用接口
            df = ak.stock_zh_index_daily(symbol=symbol)
            result.add(
                "akshare: 行业指数日线数据",
                True,
                f"获取到 {len(df)} 条数据",
                df.tail(5).to_string() if len(df) > 0 else "无数据"
            )
        except Exception as e:
            log.warning(f"行业指数获取失败: {e}")
            result.add("akshare: 行业指数日线数据", False, str(e))

        # 测试3: 获取市场概况（验证 akshare 整体可用性）
        try:
            df = ak.stock_board_industry_name_em()
            result.add(
                "akshare: 行业板块(同花顺)",
                True,
                "akshare 整体可用",
                f"获取到 {len(df)} 个行业板块"
            )
        except Exception as e:
            result.add("akshare: 行业板块(同花顺)", False, str(e))

    except ImportError:
        result.add("akshare: 导入测试", False, "请先安装: pip install akshare")
    except Exception as e:
        result.add("akshare: 未知错误", False, str(e))


def test_akshare_pe_pb():
    """测试 Akshare PE/PB 数据获取"""
    log.info("测试 Akshare PE/PB 数据获取...")

    try:
        import akshare as ak

        # 测试: 获取 A 股 PE/PB 数据
        try:
            # 使用沪深300指数
            df = ak.index_zh_a_hist(symbol="000300", period="daily")
            result.add(
                "akshare: 指数历史数据(沪深300)",
                True,
                f"获取到 {len(df)} 条数据",
                df.tail(3).to_string() if len(df) > 0 else "无数据"
            )
        except Exception as e:
            log.warning(f"指数数据获取失败: {e}")
            result.add("akshare: 指数历史数据(沪深300)", False, str(e))

    except ImportError:
        result.add("akshare: PE/PB", False, "akshare 未安装")
    except Exception as e:
        result.add("akshare: PE/PB", False, str(e))


def test_akshare_macro():
    """测试 Akshare 宏观数据获取"""
    log.info("测试 Akshare 宏观数据获取...")

    try:
        import akshare as ak

        # 测试1: PMI 数据
        try:
            df = ak.macro_china_pmi()
            result.add(
                "akshare: PMI数据",
                True,
                f"获取到 {len(df)} 条数据",
                df.tail(3).to_string() if len(df) > 0 else "无数据"
            )
        except Exception as e:
            log.warning(f"PMI获取失败: {e}")
            result.add("akshare: PMI数据", False, str(e))

        # 测试2: 工业企业利润
        try:
            df = ak.macro_china_industrial_enterprise_profit()
            result.add(
                "akshare: 工业企业利润",
                True,
                f"获取到 {len(df)} 条数据",
                df.tail(3).to_string() if len(df) > 0 else "无数据"
            )
        except Exception as e:
            result.add("akshare: 工业企业利润", False, str(e))

    except ImportError:
        result.add("akshare: 宏观数据", False, "akshare 未安装")
    except Exception as e:
        result.add("akshare: 宏观数据", False, str(e))


# ============================================================================
# Tushare 数据源测试
# ============================================================================

def test_tushare_connection():
    """测试 Tushare 连接"""
    log.info("测试 Tushare 连接...")

    if not TUSHARE_TOKEN:
        result.add(
            "tushare: Token配置",
            False,
            "未配置 Tushare Token，如需使用请设置 TUSHARE_TOKEN"
        )
        return

    try:
        import tushare as ts

        # 设置 token
        ts.set_token(TUSHARE_TOKEN)
        pro = ts.pro_api()

        # 测试: 获取交易日历
        df = pro.trade_cal(
            start_date=(datetime.now() - timedelta(days=30)).strftime("%Y%m%d"),
            end_date=datetime.now().strftime("%Y%m%d")
        )
        result.add(
            "tushare: 连接测试",
            True,
            f"连接成功，获取到 {len(df)} 条交易日数据",
            df.tail(3).to_string() if len(df) > 0 else "无数据"
        )

    except ImportError:
        result.add("tushare: 导入测试", False, "请先安装: pip install tushare")
    except Exception as e:
        result.add("tushare: 连接测试", False, str(e))


def test_tushare_index_data():
    """测试 Tushare 指数数据"""
    if not TUSHARE_TOKEN:
        log.info("跳过 Tushare 指数数据测试（未配置 Token）")
        return

    log.info("测试 Tushare 指数数据...")

    try:
        import tushare as ts
        pro = ts.pro_api()

        # 测试: 获取沪深300历史数据
        df = pro.index_dailybasic(
            ts_code="000300.SH",
            start_date=(datetime.now() - timedelta(days=365)).strftime("%Y%m%d"),
            end_date=datetime.now().strftime("%Y%m%d"),
            fields="ts_code,trade_date,pe,pb"
        )
        result.add(
            "tushare: 指数PE/PB数据",
            True,
            f"获取到 {len(df)} 条数据",
            df.tail(5).to_string() if len(df) > 0 else "无数据"
        )

    except Exception as e:
        result.add("tushare: 指数PE/PB数据", False, str(e))


def test_tushare_fund_holding():
    """测试 Tushare 机构持仓数据"""
    if not TUSHARE_TOKEN:
        log.info("跳过 Tushare 机构持仓测试（未配置 Token）")
        return

    log.info("测试 Tushare 机构持仓数据...")

    try:
        import tushare as ts
        pro = ts.pro_api()

        # 测试: 基金持仓数据
        df = pro.fund_hold(
            ts_code="000300.SH",
            end_date=datetime.now().strftime("%Y%m%d")
        )
        result.add(
            "tushare: 基金持仓数据",
            True,
            f"获取到 {len(df)} 条数据",
            df.head(3).to_string() if len(df) > 0 else "无数据"
        )

    except Exception as e:
        result.add("tushare: 基金持仓数据", False, str(e))


# ============================================================================
# 主函数
# ============================================================================

def main():
    print("\n" + "=" * 70)
    print("数据源可行性测试开始")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Akshare 测试
    print("\n>>> 开始 Akshare 数据源测试 <<<")
    test_akshare_index()
    test_akshare_pe_pb()
    test_akshare_macro()

    # Tushare 测试
    print("\n>>> 开始 Tushare 数据源测试 <<<")
    test_tushare_connection()
    test_tushare_index_data()
    test_tushare_fund_holding()

    # 输出报告
    success = result.print_report()

    # 建议
    print("\n>>> 后续建议 <<<")
    if success:
        print("所有测试通过，可以开始正式开发。")
    else:
        print("部分测试失败，请根据错误信息调整：")
        print("1. 确认 akshare 和 tushare 已正确安装")
        print("2. 如使用 Tushare，请配置有效的 token")
        print("3. 部分接口可能因网络或数据源问题暂时不可用，建议稍后重试")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
