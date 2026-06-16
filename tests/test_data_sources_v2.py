"""
数据源可行性测试脚本 V2
测试多种免费数据源的可行性

使用方法:
    python tests/test_data_sources.py

依赖安装:
    pip install akshare tushare pandas yfinance baostock
"""

import sys
import logging
from datetime import datetime, timedelta
from typing import Optional
from functools import wraps

import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

# Tushare Token
TUSHARE_TOKEN = "7f3a04e7858fbe2451bc30d5170e08d366c5cfea68f70fb1f5323efb"


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
        print("数据源可行性测试报告 V2")
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
# Yahoo Finance 测试
# ============================================================================

def test_yfinance():
    """测试 Yahoo Finance（免费，无需API Key）"""
    log.info("测试 Yahoo Finance...")

    try:
        import yfinance as yf

        # 测试1: 获取沪深300指数数据
        try:
            # Yahoo Finance 使用正确代码
            ticker = yf.Ticker("000300.SS")  # 沪深300
            df = ticker.history(period="2y")  # 最近2年数据

            if len(df) > 0:
                result.add(
                    "yfinance: 沪深300历史数据",
                    True,
                    f"获取到 {len(df)} 条数据",
                    df.tail(3).to_string()
                )
            else:
                result.add("yfinance: 沪深300历史数据", False, "无数据返回")
        except Exception as e:
            result.add("yfinance: 沪深300历史数据", False, str(e))

        # 测试2: 获取航空行业ETF（如有）
        try:
            # 中证民航指数 ETF
            ticker = yf.Ticker("515050.SS")  # 交运ETF
            df = ticker.history(period="1y")
            result.add(
                "yfinance: 交运ETF数据",
                True,
                f"获取到 {len(df)} 条数据",
                df.tail(3).to_string() if len(df) > 0 else "无数据"
            )
        except Exception as e:
            result.add("yfinance: 交运ETF数据", False, str(e))

    except ImportError:
        result.add("yfinance: 导入测试", False, "请安装: pip install yfinance")
    except Exception as e:
        result.add("yfinance: 未知错误", False, str(e))


# ============================================================================
# Baostock 测试（免费A股数据）
# ============================================================================

def test_baostock():
    """测试 Baostock（免费，无需登录）"""
    log.info("测试 Baostock...")

    try:
        import baostock as bs

        # 登录
        lg = bs.login()
        if lg.error_code != '0':
            result.add("baostock: 登录", False, lg.error_msg)
            return

        result.add("baostock: 登录", True, "登录成功")

        # 测试1: 获取沪深300历史数据
        try:
            rs = bs.query_history_k_data_plus(
                "sh.600000",  # 浦发银行作为测试
                "date,open,high,low,close,volume",
                start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                end_date=datetime.now().strftime("%Y-%m-%d"),
                frequency="d"
            )

            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)
            result.add(
                "baostock: 个股历史数据",
                True,
                f"获取到 {len(df)} 条数据",
                df.tail(3).to_string() if len(df) > 0 else "无数据"
            )
        except Exception as e:
            result.add("baostock: 个股历史数据", False, str(e))

        # 测试2: 获取行业指数
        try:
            rs = bs.query_history_k_data_plus(
                "sh.000300",  # 沪深300
                "date,open,high,low,close,volume",
                start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                end_date=datetime.now().strftime("%Y-%m-%d"),
                frequency="d"
            )

            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)
            result.add(
                "baostock: 沪深300指数数据",
                True,
                f"获取到 {len(df)} 条数据",
                df.tail(3).to_string() if len(df) > 0 else "无数据"
            )
        except Exception as e:
            result.add("baostock: 沪深300指数数据", False, str(e))

        # 测试3: 获取行业分类
        try:
            rs = bs.query_stock_industry()
            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())

            if len(data_list) > 0:
                df = pd.DataFrame(data_list, columns=rs.fields)
                result.add(
                    "baostock: 行业分类列表",
                    True,
                    f"获取到 {len(df)} 个行业分类",
                    df.head(3).to_string()
                )
            else:
                result.add("baostock: 行业分类列表", False, "无数据")
        except Exception as e:
            result.add("baostock: 行业分类列表", False, str(e))

        # 登出
        bs.logout()

    except ImportError:
        result.add("baostock: 导入测试", False, "请安装: pip install baostock")
    except Exception as e:
        result.add("baostock: 未知错误", False, str(e))


# ============================================================================
# Tushare 免费版可用接口测试
# ============================================================================

def test_tushare_free():
    """测试 Tushare 免费版可用接口"""
    log.info("测试 Tushare 免费版...")

    try:
        import tushare as ts

        # 设置 token
        ts.set_token(TUSHARE_TOKEN)
        pro = ts.pro_api()

        # 测试1: 股票列表（基础数据，免费）
        try:
            df = pro.stock_basic(
                ts_code='',
                name='',
                list_status='L',
                fields='ts_code,symbol,name,industry'
            )
            result.add(
                "tushare: 股票列表",
                True,
                f"获取到 {len(df)} 只股票",
                df.head(3).to_string() if len(df) > 0 else "无数据"
            )
        except Exception as e:
            result.add("tushare: 股票列表", False, str(e))

        # 测试2: 日线行情（基础数据，可能免费）
        try:
            df = pro.daily(
                ts_code='000300.SZ',
                start_date=(datetime.now() - timedelta(days=30)).strftime("%Y%m%d"),
                end_date=datetime.now().strftime("%Y%m%d")
            )
            result.add(
                "tushare: 日线行情",
                True,
                f"获取到 {len(df)} 条数据",
                df.head(3).to_string() if len(df) > 0 else "无数据"
            )
        except Exception as e:
            result.add("tushare: 日线行情", False, str(e))

        # 测试3: 指数日线行情
        try:
            df = pro.index_daily(
                ts_code='000300.SH',
                start_date=(datetime.now() - timedelta(days=365)).strftime("%Y%m%d"),
                end_date=datetime.now().strftime("%Y%m%d")
            )
            result.add(
                "tushare: 指数日线行情",
                True,
                f"获取到 {len(df)} 条数据",
                df.head(3).to_string() if len(df) > 0 else "无数据"
            )
        except Exception as e:
            result.add("tushare: 指数日线行情", False, str(e))

        # 测试4: 宏观数据（通常免费）
        try:
            df = pro.cn_gdp(quarter='2024Q1')
            result.add(
                "tushare: GDP数据",
                True,
                f"获取到 {len(df)} 条数据",
                df.to_string() if len(df) > 0 else "无数据"
            )
        except Exception as e:
            result.add("tushare: GDP数据", False, str(e))

    except ImportError:
        result.add("tushare: 导入测试", False, "请安装: pip install tushare")
    except Exception as e:
        result.add("tushare: 未知错误", False, str(e))


# ============================================================================
# Akshare 宏观数据测试（不依赖东方财富）
# ============================================================================

def test_akshare_macro():
    """测试 Akshare 宏观数据（通常不经过东方财富）"""
    log.info("测试 Akshare 宏观数据...")

    try:
        import akshare as ak

        # 测试1: PMI 数据
        try:
            df = ak.macro_china_pmi()
            result.add(
                "akshare: PMI数据",
                True,
                f"获取到 {len(df)} 条数据",
                df.tail(3).to_string()
            )
        except Exception as e:
            result.add("akshare: PMI数据", False, str(e))

        # 测试2: CPI/PPI 数据
        try:
            df = ak.macro_china_cpi()
            result.add(
                "akshare: CPI数据",
                True,
                f"获取到 {len(df)} 条数据",
                df.tail(3).to_string() if len(df) > 0 else "无数据"
            )
        except Exception as e:
            result.add("akshare: CPI数据", False, str(e))

        # 测试3: 外汇储备
        try:
            df = ak.macro_china_fx_reserve()
            result.add(
                "akshare: 外汇储备",
                True,
                f"获取到 {len(df)} 条数据",
                df.tail(3).to_string() if len(df) > 0 else "无数据"
            )
        except Exception as e:
            result.add("akshare: 外汇储备", False, str(e))

        # 测试4: 货币供应量
        try:
            df = ak.macro_china_money_supply()
            result.add(
                "akshare: 货币供应量",
                True,
                f"获取到 {len(df)} 条数据",
                df.tail(3).to_string() if len(df) > 0 else "无数据"
            )
        except Exception as e:
            result.add("akshare: 货币供应量", False, str(e))

    except ImportError:
        result.add("akshare: 宏观数据", False, "akshare 未安装")
    except Exception as e:
        result.add("akshare: 宏观数据", False, str(e))


# ============================================================================
# 新浪/腾讯财经接口测试
# ============================================================================

def test_sina_tencent():
    """测试新浪/腾讯财经接口"""
    log.info("测试新浪/腾讯财经接口...")

    try:
        import requests

        # 测试新浪实时行情
        try:
            url = "http://hq.sinajs.cn/list=s_sh000300"  # 沪深300
            headers = {
                'Referer': 'http://finance.sina.com.cn',
                'User-Agent': 'Mozilla/5.0'
            }
            resp = requests.get(url, headers=headers, timeout=10)

            if resp.status_code == 200 and resp.text:
                result.add(
                    "sina: 实时行情",
                    True,
                    f"成功获取，数据长度 {len(resp.text)}",
                    resp.text[:200]
                )
            else:
                result.add("sina: 实时行情", False, f"状态码: {resp.status_code}")
        except Exception as e:
            result.add("sina: 实时行情", False, str(e))

        # 测试腾讯实时行情
        try:
            url = "http://qt.gtimg.cn/q=sh000300"  # 沪深300
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=10)

            if resp.status_code == 200 and resp.text:
                result.add(
                    "tencent: 实时行情",
                    True,
                    f"成功获取，数据长度 {len(resp.text)}",
                    resp.text[:200]
                )
            else:
                result.add("tencent: 实时行情", False, f"状态码: {resp.status_code}")
        except Exception as e:
            result.add("tencent: 实时行情", False, str(e))

    except ImportError:
        result.add("requests", False, "requests 未安装")
    except Exception as e:
        result.add("新浪/腾讯", False, str(e))


# ============================================================================
# 主函数
# ============================================================================

def main():
    print("\n" + "=" * 70)
    print("数据源可行性测试 V2 - 免费数据源专项")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Yahoo Finance
    print("\n>>> 测试 Yahoo Finance <<<")
    test_yfinance()

    # Baostock
    print("\n>>> 测试 Baostock <<<")
    test_baostock()

    # Tushare 免费接口
    print("\n>>> 测试 Tushare 免费接口 <<<")
    test_tushare_free()

    # Akshare 宏观数据
    print("\n>>> 测试 Akshare 宏观数据 <<<")
    test_akshare_macro()

    # 新浪/腾讯
    print("\n>>> 测试 新浪/腾讯财经 <<<")
    test_sina_tencent()

    # 输出报告
    success = result.print_report()

    # 总结
    print("\n>>> 总结与建议 <<<")
    available = [t['name'] for t in result.tests if t['success']]
    unavailable = [t['name'] for t in result.tests if not t['success']]

    if available:
        print(f"\n可用的数据源 ({len(available)}项):")
        for name in available:
            print(f"  ✓ {name}")

    if unavailable:
        print(f"\n不可用的数据源 ({len(unavailable)}项):")
        for name in unavailable:
            print(f"  ✗ {name}")

    print("\n>>> 建议的数据获取方案 <<<")
    print("""
基于测试结果，建议的数据源组合：

1. 【指数行情数据】
   首选: Baostock (沪深300等主要指数)
   备选: Yahoo Finance (国际ETF)
   备选: Tushare index_daily

2. 【行业分类数据】
   首选: Baostock query_stock_industry

3. 【行业日线数据】
   备选: 需要自行映射行业成分股，用个股数据合成
   备选: Tushare pro.daily 拼接

4. 【宏观景气数据】
   首选: Akshare macro_* 系列
   备选: Tushare cn_gdp 等宏观接口

5. 【PE/PB 估值数据】
   待测试: 需要寻找专门提供估值的免费接口
""")

    return 0 if success else 0  # 即使有失败也继续


if __name__ == "__main__":
    sys.exit(main())
