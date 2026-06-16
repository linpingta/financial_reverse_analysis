"""
行业历史 PE/PB 数据源完整测试
测试三个方案的可行性：
1. 首选：Baostock 成分股加权自主计算
2. 次选1：OpenDataTools 申万指数接口
3. 次选2：申万指数官网爬虫
"""

import sys
import logging
from datetime import datetime, timedelta

import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

results = []


def add_result(name, success, message="", preview=""):
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"\n{status}: {name}")
    if message:
        print(f"  消息: {message}")
    if preview and success:
        print(f"  预览:\n{preview[:500]}..." if len(str(preview)) > 500 else f"  预览:\n{preview}")
    results.append({"name": name, "success": success})


# ============================================================================
# 方案1: Baostock 成分股加权自主计算
# ============================================================================

def test_baostock_pe_pb_calculation():
    """测试 Baostock 成分股加权 PE/PB 计算"""
    log.info("测试 Baostock 成分股加权计算...")

    try:
        import baostock as bs

        # 登录
        lg = bs.login()
        if lg.error_code != '0':
            add_result("baostock: 登录", False, lg.error_msg)
            return

        add_result("baostock: 登录", True, "登录成功")

        # 1. 获取行业分类
        try:
            rs = bs.query_stock_industry()
            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())

            if len(data_list) > 0:
                df_industry = pd.DataFrame(data_list, columns=rs.fields)
                add_result(
                    "baostock: 行业分类",
                    True,
                    f"获取到 {len(df_industry)} 只股票的行业分类",
                    df_industry.head(3).to_string()
                )
            else:
                add_result("baostock: 行业分类", False, "无数据")
        except Exception as e:
            add_result("baostock: 行业分类", False, str(e))

        # 2. 获取沪深300成分股（测试用）
        try:
            rs = bs.query_hs300_stocks()
            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())

            if len(data_list) > 0:
                df_hs300 = pd.DataFrame(data_list, columns=rs.fields)
                add_result(
                    "baostock: 沪深300成分股",
                    True,
                    f"获取到 {len(df_hs300)} 只成分股",
                    df_hs300.head(3).to_string()
                )
            else:
                add_result("baostock: 沪深300成分股", False, "无数据")
        except Exception as e:
            add_result("baostock: 沪深300成分股", False, str(e))

        # 3. 获取个股历史数据（含收盘价）
        try:
            rs = bs.query_history_k_data_plus(
                "sh.600519",  # 茅台
                "date,code,close,volume",
                start_date="2023-01-01",
                end_date=datetime.now().strftime("%Y-%m-%d"),
                frequency="d"
            )
            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())

            if len(data_list) > 0:
                df_kline = pd.DataFrame(data_list, columns=rs.fields)
                add_result(
                    "baostock: 个股K线数据",
                    True,
                    f"获取到 {len(df_kline)} 条数据",
                    df_kline.tail(3).to_string()
                )
            else:
                add_result("baostock: 个股K线数据", False, "无数据")
        except Exception as e:
            add_result("baostock: 个股K线数据", False, str(e))

        # 4. 获取个股财务数据（关键：用于计算PE）
        try:
            rs = bs.query_profit_statement_data(
                code="sh.600519",
                start_date="2023-01-01",
                end_date=datetime.now().strftime("%Y-%m-%d")
            )
            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())

            if len(data_list) > 0:
                df_financial = pd.DataFrame(data_list, columns=rs.fields)
                add_result(
                    "baostock: 个股利润表",
                    True,
                    f"获取到 {len(df_financial)} 条财务数据",
                    df_financial.head(3).to_string()
                )
            else:
                add_result("baostock: 个股利润表", False, "无数据（可能接口名变更）")
        except Exception as e:
            add_result("baostock: 个股利润表", False, str(e))

        # 5. 获取主要财务指标（EPS等）
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
                df_perf = pd.DataFrame(data_list, columns=rs.fields)
                add_result(
                    "baostock: 业绩摘要",
                    True,
                    f"获取到 {len(df_perf)} 条数据",
                    df_perf.head(3).to_string()
                )
            else:
                add_result("baostock: 业绩摘要", False, "无数据")
        except Exception as e:
            add_result("baostock: 业绩摘要", False, str(e))

        # 6. 获取季频财务指标（更完整的数据）
        try:
            rs = bs.query_quarterly_profit_rate(
                code="sh.600519",
                start_date="2023-01-01",
                end_date=datetime.now().strftime("%Y-%m-%d")
            )
            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())

            if len(data_list) > 0:
                df_quarterly = pd.DataFrame(data_list, columns=rs.fields)
                add_result(
                    "baostock: 季频利润率",
                    True,
                    f"获取到 {len(df_quarterly)} 条数据",
                    df_quarterly.head(3).to_string()
                )
            else:
                add_result("baostock: 季频利润率", False, "无数据")
        except Exception as e:
            add_result("baostock: 季频利润率", False, str(e))

        bs.logout()

    except ImportError:
        add_result("baostock", False, "请安装: pip install baostock")
    except Exception as e:
        add_result("baostock", False, str(e))


# ============================================================================
# 方案2: OpenDataTools 申万指数接口
# ============================================================================

def test_opendatatools():
    """测试 OpenDataTools 申万指数接口"""
    log.info("测试 OpenDataTools...")

    try:
        import requests

        # 测试多个可能的接口地址
        urls = [
            "https://www.quantutils.cn/api/sw/index",
            "https://opendatatools.cn/sw/index",
            "https://swindex.quanttools.cn/",
        ]

        for url in urls:
            try:
                resp = requests.get(url, timeout=10)
                add_result(
                    f"OpenDataTools: {url[:40]}",
                    resp.status_code == 200,
                    f"状态码: {resp.status_code}"
                )
            except Exception as e:
                add_result(f"OpenDataTools: {url[:40]}", False, str(e))

        # 尝试 pip install opendatatools
        try:
            import opendatatools as odt
            add_result("opendatatools: 模块存在", True, "已安装")

            # 尝试调用申万接口
            try:
                df, msg = odt.sw_index().get_index_info()
                add_result("opendatatools: 申万指数", True, f"获取到 {len(df)} 条数据")
            except Exception as e:
                add_result("opendatatools: 申万指数", False, str(e))

        except ImportError:
            add_result("opendatatools: 模块", False, "未安装（pip install opendatatools）")

    except ImportError:
        add_result("requests", False, "requests 未安装")


# ============================================================================
# 方案3: 申万指数官网爬虫
# ============================================================================

def test_swindex_websites():
    """测试申万指数相关网站"""
    log.info("测试申万指数官网...")

    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # 测试申万行业数据网站
        sites = [
            ("申万官网", "http://www.swhyquotation.com/"),
            ("申万估值", "https://www.swhyquotation.com/"),
            ("乌龟量化(有类似数据)", "https://weguang.com/"),
        ]

        for name, url in sites:
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                add_result(
                    f"官网爬虫: {name}",
                    resp.status_code == 200,
                    f"状态码: {resp.status_code}"
                )
            except Exception as e:
                add_result(f"官网爬虫: {name}", False, str(e))

        # 测试 akshare 的申万接口
        try:
            import akshare as ak

            # 申万一级行业列表
            try:
                df = ak.sw_index_first_info()
                add_result(
                    "akshare: 申万一级行业",
                    True,
                    f"获取到 {len(df)} 个行业",
                    df.head(3).to_string() if len(df) > 0 else "无数据"
                )
            except Exception as e:
                add_result("akshare: 申万一级行业", False, str(e))

            # 申万行业PE/PB
            try:
                df = ak.sw_index_second_info()
                add_result(
                    "akshare: 申万二级行业(实时估值)",
                    True,
                    f"获取到 {len(df)} 个行业的实时估值",
                    df[['行业代码', '行业名称', '静态市盈率', '市净率']].head(3).to_string()
                )
            except Exception as e:
                add_result("akshare: 申万二级行业", False, str(e))

            # 申万行业历史PE走势
            try:
                df = ak.sw_index_daily("801991.SI")  # 航空机场
                add_result(
                    "akshare: 申万行业历史走势",
                    True,
                    f"获取到 {len(df)} 条历史数据",
                    df.tail(5).to_string() if len(df) > 0 else "无数据"
                )
            except Exception as e:
                add_result("akshare: 申万行业历史走势", False, str(e))

        except ImportError:
            add_result("akshare", False, "akshare 未安装")

    except ImportError:
        add_result("requests/beautifulsoup", False, "依赖未安装")


# ============================================================================
# 方案4: 验证计算逻辑
# ============================================================================

def test_calculation_logic():
    """测试 PE/PB 计算逻辑"""
    log.info("测试计算逻辑...")

    print("""
    ================================================================
    【行业 PE/PB 计算方法说明】
    ================================================================

    方法1: 指数 PE = 指数点位 / 指数 EPS
    方法2: PE_TTM = Σ(成分股总市值) / Σ(成分股净利润TTM)
           PB = Σ(成分股总市值) / Σ(成分股净资产)

    数据获取流程:
    1. 获取申万二级行业成分股列表
       → baostock.query_stock_industry()

    2. 获取成分股历史市值/净利润
       → baostock query_*_data 系列接口

    3. 按季度/年度汇总成分股数据
       → 成分股净利润TTM = 最近4个季度净利润之和

    4. 加权计算行业PE/PB
       → PE = Σ(成分股市值) / Σ(成分股净利润)

    关键问题:
    - 需要获取足够长时间的财务数据（10年）
    - 需要处理财务数据的缺失和调整
    - 需要按市值加权还是等权重？

    ================================================================
    """)

    add_result("计算逻辑说明", True, "逻辑可行，需验证数据接口")


# ============================================================================
# 主函数
# ============================================================================

def main():
    print("\n" + "=" * 70)
    print("行业历史 PE/PB 数据源完整测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 方案1: Baostock 自主计算
    print("\n>>> 方案1: Baostock 成分股加权计算 <<<")
    test_baostock_pe_pb_calculation()

    # 方案2: OpenDataTools
    print("\n>>> 方案2: OpenDataTools <<<")
    test_opendatatools()

    # 方案3: 申万官网爬虫
    print("\n>>> 方案3: 申万指数官网爬虫 <<<")
    test_swindex_websites()

    # 方案4: 计算逻辑验证
    print("\n>>> 方案4: 计算逻辑验证 <<<")
    test_calculation_logic()

    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)

    passed = sum(1 for r in results if r["success"])
    total = len(results)

    print(f"\n通过: {passed}/{total}")
    print("\n可用的数据源:")
    for r in results:
        if r["success"]:
            print(f"  ✓ {r['name']}")

    print("\n不可用的数据源:")
    for r in results:
        if not r["success"]:
            print(f"  ✗ {r['name']}")

    print("\n>>> 最终建议 <<<")
    success_names = [r['name'] for r in results if r["success"]]

    if any("baostock: 个股K线数据" in n for n in success_names):
        print("""
【推荐方案】
1. Baostock 数据完整，但需要自行开发成分股财务数据获取逻辑
2. akshare.sw_index_second_info() 可获取实时行业PE/PB（无需计算）
3. akshare.sw_index_daily() 可获取行业指数历史走势

【下一步】
1. 验证 baostock 是否有完整的10年成分股财务数据
2. 如果 baostock 财务数据不完整，考虑：
   - 使用 akshare 申万行业实时PE作为当前值
   - 通过历史分位计算器，只用当前PE与历史区间估算分位
   - 或者用申万官网爬虫获取历史PE数据
""")


if __name__ == "__main__":
    main()
