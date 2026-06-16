# 逆向周期行业投资分析系统 技术设计文档 V1.0

## 文档基础信息
| 项目 | 内容 |
| ---- | ---- |
| 文档名称 | 逆向周期行业投资分析系统 技术设计文档 |
| 版本 | V1.0 |
| 关联业务文档 | financial_reverse_analysis_1.0.md |
| 程序形态 | Python本地单机分析程序 |
| 分析范围 | 10个强周期性行业 |

---

## 一、系统架构总览

### 1.1 整体架构图
```
┌─────────────────────────────────────────────────────────────┐
│                      Presentation Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ CLI 命令行  │  │ 分析报告    │  │ CSV/Excel 导出      │ │
│  │ 交互界面    │  │ Markdown    │  │ 模块                │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                    │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │ 背离分析引擎     │  │ 逆向信号判定器   │  │ 风控过滤器 │ │
│  │ DivergenceEngine │  │ SignalJudge      │  │ RiskFilter │ │
│  └──────────────────┘  └──────────────────┘  └────────────┘ │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │ 分位计算器       │  │ 逆向评分计算器   │  │ 报告生成器 │ │
│  │ PercentileCalc   │  │ ScoreCalculator  │  │ Reporter   │ │
│  └──────────────────┘  └──────────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Data Access Layer                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │ Akshare  │  │ Tushare  │  │ 统计局API│  │ Web爬虫     │ │
│  │ 数据接口  │  │ 数据接口  │  │ 数据接口  │  │ 数据接口    │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Storage Layer                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ SQLite: 每次运行输出结果存储                           │  │
│  │ (不存储原始历史数据，仅存储分析结论)                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块依赖关系
```
config.yaml          # 配置文件（行业池、阈值参数）
       │
       ▼
┌─────────────────┐
│   Main CLI      │  ← 用户入口
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ DataCollector   │────▶│ PercentileCalc  │
│ 数据采集模块     │     │ 分位计算模块     │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│ DivergenceEngine │◀────│  原始数据        │
│ 背离分析引擎     │     │                 │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ RiskFilter       │────▶│ SignalJudge     │
│ 风控过滤器       │     │ 信号判定器       │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│ ScoreCalculator  │◀────│ 风控后行业列表   │
│ 逆向评分计算器   │     │                 │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│ Reporter        │
│ 报告生成器       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ResultExporter  │  → Markdown / CSV
│ 结果导出器       │
└─────────────────┘
```

---

## 二、技术选型

### 2.1 核心依赖库
| 用途 | 库名 | 版本 | 说明 |
|------|------|------|------|
| 数据获取 | akshare | >=1.12.0 | 行业指数、PE/PB、宏观数据 |
| 数据获取 | tushare | >=1.4.0 | 免费版数据补充 |
| 数据处理 | pandas | >=2.0.0 | 数据分析核心 |
| 数据处理 | numpy | >=1.24.0 | 数值计算 |
| 时间序列 | pandas | datetime | 日期处理 |
| HTTP请求 | requests | >=2.28.0 | API调用、爬虫 |
| HTML解析 | beautifulsoup4 | >=4.11.0 | 网页爬虫 |
| 配置文件 | pyyaml | >=6.0 | 配置文件读写 |
| 数据库 | sqlite3 | 内置 | 结果存储 |
| 日志 | loguru | >=0.7.0 | 日志记录 |
| CLI界面 | click | >=8.0.0 | 命令行交互 |

### 2.2 项目结构
```
financial_reverse_analysis/
├── config.yaml                 # 全局配置文件
├── requirements.txt            # Python依赖
├── main.py                     # 程序入口 CLI
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py         # 配置加载
│   ├── data/
│   │   ├── __init__.py
│   │   ├── collector.py        # 数据采集统一入口
│   │   ├── akshare_adapter.py # Akshare适配器
│   │   ├── tushare_adapter.py  # Tushare适配器
│   │   ├── nbs_scraper.py      # 国家统计局爬虫
│   │   └── industry_scraper.py # 行业协会爬虫
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── percentile.py       # 分位计算
│   │   ├── divergence.py       # 背离分析
│   │   ├── signal.py           # 信号判定
│   │   ├── risk_filter.py      # 风控过滤
│   │   └── scorer.py           # 逆向评分
│   ├── output/
│   │   ├── __init__.py
│   │   ├── reporter.py         # 报告生成
│   │   └── exporter.py         # 导出器(CSV/MD)
│   └── storage/
│       ├── __init__.py
│       └── result_db.py        # SQLite结果存储
├── data/
│   └── results/                 # 分析结果输出目录
├── logs/                        # 日志目录
└── tests/                       # 单元测试
```

---

## 三、数据采集层设计

### 3.1 数据采集策略
```
数据源选择优先级（按数据质量排序）：
1. Akshare（主力数据源，免费、稳定）
2. Tushare 免费版（补充行业估值、机构持仓）
3. 国家统计局 API（宏观景气指标）
4. 行业协会网页（细分行业数据）
```

### 3.2 各数据类型获取方案

#### 3.2.1 行业指数价格数据
```python
# 方案：使用 akshare 行业板块指数
# 接口：akshare.get_industry_index_daily()
# 频率：周频（取每周最后一个交易日）

# 行业指数代码映射（预设10个行业）
INDUSTRY_INDEX_MAP = {
    "航空机场": "881001",      # 航空机场指数
    "生猪养殖": "801012",      # 农林牧渔指数
    "基础化工": "801032",      # 化工指数
    "煤炭": "801022",          # 煤炭指数
    "有色金属": "801005",      # 有色金属指数
    "远洋航运": "801014",      # 港口航运指数
    "酒店旅游": "801010",      # 旅游酒店指数
    "周期半导体": "801081",    # 半导体指数
    "光伏上游": "801023",      # 电力设备指数
    "工程机械": "801018",      # 机械设备指数
}
```

#### 3.2.2 行业估值数据 (PE/PB)
```python
# 方案1：Akshare - 行业估值接口
akshare.getIndustryPeHistogram(symbol="801001")

# 方案2：Tushare 免费版 - 行业估值
tushare.industry_pe()

# 数据存储：当日PE_TTM、PB_LF 数值
# 历史序列：拉取近10年用于分位计算
```

#### 3.2.3 行业景气度指标
```python
# 方案：多数据源组合

# 1. 国家统计局 API（推荐）
# 网址：http://www.stats.gov.cn/
# 接口：季度GDP、PMI、工业企业利润
URL_GDP = "http://www.stats.gov.cn/english/PressRelease/"
URL_PMI = "http://www.stats.gov.cn/english/PressRelease/"

# 2. Akshare 宏观指标（辅助）
akshare.macro_china_pmi()           # PMI
akshare.macro_china_industrial_profit()  # 工业企业利润

# 3. 行业协会数据（补充，具体URL待确认）
# - 中国民航局：旅客周转量、货邮运输量
# - 中国钢铁工业协会：粗钢产量、价格指数
# - 中国汽车工业协会：汽车产销数据

# 景气指标定义（按行业）
INDUSTRY_BENCHMARKS = {
    "航空机场": ["旅客周转量同比", "客座率", "航油成本"],
    "生猪养殖": ["能繁母猪存栏量", "生猪价格", "猪粮比"],
    "基础化工": ["化工品价格指数", "开工率", "库存周期"],
    "煤炭": ["秦皇岛煤价指数", "港口库存", "发电量增速"],
    "有色金属": ["LME铜价", "库存变化", "加工费"],
    "远洋航运": ["BDI指数", "集装箱运价", "新船订单"],
    "酒店旅游": ["出游人数", "酒店入住率", "旅游收入"],
    "周期半导体": ["全球半导体销售额", "存储芯片价格"],
    "光伏上游": ["硅料价格", "组件价格", "装机量"],
    "工程机械": ["挖掘机销量", "小松开工小时数", "房地产新开工"],
}
```

#### 3.2.4 机构持仓数据
```python
# 方案：Tushare 免费版
# 接口：tushare.fund_holdings()（基金重仓）
#       tushare.hsgt_top10()（北向资金）

# 注意：Tushare 免费版数据范围有限
# 可能需要降级为：使用行业指数成交量/换手率作为情绪代理指标
```

### 3.3 数据采集失败降级策略
```python
# 降级优先级
PRIMARY_SOURCE = "akshare"
FALLBACK_SOURCE = "tushare"
FINAL_FALLBACK = "manual_input"  # 人工输入或跳过

# 错误处理
class DataSourceError(Exception):
    """数据源不可用异常"""
    pass

def get_data_with_fallback(source_type: str, **kwargs):
    """带降级的数据获取"""
    try:
        return primary_fetch(source_type, **kwargs)
    except DataSourceError:
        try:
            return fallback_fetch(source_type, **kwargs)
        except DataSourceError:
            log.warning(f"数据源{source_type}不可用，尝试降级...")
            return None
```

---

## 四、业务分析层设计

### 4.1 分位计算模块 (PercentileCalc)
```python
class PercentileCalculator:
    """近10年历史分位计算器"""

    def __init__(self, lookback_years: int = 10):
        self.lookback_years = lookback_years

    def calculate(self, series: pd.Series, current_value: float) -> float:
        """
        计算当前值在历史序列中的百分位
        返回: 0~100 的分位值
        """
        # 剔除空值和异常值
        valid_series = series.dropna()
        if len(valid_series) == 0:
            return 50.0  # 默认中性

        # 计算百分位
        percentile = (valid_series <= current_value).sum() / len(valid_series) * 100
        return min(100.0, max(0.0, percentile))

    def batch_calculate(self, df: pd.DataFrame, columns: list) -> pd.DataFrame:
        """批量计算多列分位"""
        result = df.copy()
        for col in columns:
            result[f"{col}_pct"] = result.apply(
                lambda row: self.calculate(df[col], row[col]), axis=1
            )
        return result
```

### 4.2 背离分析模块 (DivergenceEngine)
```python
class DivergenceEngine:
    """基本面-价格背离检测引擎"""

    def detect(self, industry_data: dict) -> dict:
        """
        检测背离类型和强度
        返回背离分析结果
        """
        signal_data = industry_data

        # 核心背离计算
        price_vs_prosperity = signal_data['price_pct'] - signal_data['prosperity_pct']
        valuation_vs_price = signal_data['valuation_pct'] - signal_data['price_pct']

        # 背离类型判定
        divergence_type = None
        divergence_strength = 0

        # 逆向买点背离：基本面跌，股价不跟跌
        if (signal_data['prosperity_pct'] <= 20 and
            signal_data['price_pct'] > signal_data['prosperity_pct'] + 10):
            divergence_type = "buy_divergence"
            divergence_strength = min(100, price_vs_prosperity * 2)

        # 逆向卖点背离：基本面涨，股价不跟涨
        elif (signal_data['prosperity_pct'] >= 80 and
              signal_data['price_pct'] < signal_data['prosperity_pct'] - 10):
            divergence_type = "sell_divergence"
            divergence_strength = min(100, abs(price_vs_prosperity) * 2)

        return {
            "type": divergence_type,
            "strength": divergence_strength,
            "price_vs_prosperity": price_vs_prosperity,
            "valuation_vs_price": valuation_vs_price
        }
```

### 4.3 信号判定模块 (SignalJudge)
```python
class SignalJudge:
    """逆向买卖信号判定器"""

    # 判定阈值（从配置读取）
    BUY_THRESHOLD = {"prosperity": 20, "valuation": 25, "divergence": 10}
    SELL_THRESHOLD = {"prosperity": 80}
    NEUTRAL_RANGE = (20, 80)

    def judge(self, analysis_result: dict) -> str:
        """
        判定信号类型
        返回: "buy_signal" / "sell_signal" / "neutral" / "risk_sell"
        """
        p = analysis_result['prosperity_pct']
        v = analysis_result['valuation_pct']
        d = analysis_result['divergence']

        # 卖出风险信号（任意2条触发）
        sell_conditions = [
            p >= self.SELL_THRESHOLD['prosperity'],
            d['type'] == 'sell_divergence',
            analysis_result['valuation_declining'],
        ]
        if sum(sell_conditions) >= 2:
            return "risk_sell"

        # 逆向买入信号（全部条件满足）
        buy_conditions = [
            p <= self.BUY_THRESHOLD['prosperity'],
            v <= self.BUY_THRESHOLD['valuation'],
            d['type'] == 'buy_divergence',
            analysis_result['margin_improving'],  # 边际改善
        ]
        if all(buy_conditions):
            return "buy_signal"

        # 观望区间
        return "neutral"
```

### 4.4 风控过滤器 (RiskFilter)
```python
class RiskFilter:
    """价值陷阱风控过滤器"""

    # 夕阳行业黑名单
    SUNSET_INDUSTRIES = [
        # "部分行业可配置"
    ]

    # 产能过剩信号阈值
    OVERCAPACITY_SIGNALS = [
        "产能利用率 < 70% 持续2年",
        "行业大规模亏损 > 3年无修复",
    ]

    def filter(self, industry_name: str, industry_data: dict) -> tuple[bool, str]:
        """
        风控校验
        返回: (通过校验, 风险原因)
        """
        # 1. 检查夕阳行业
        if industry_name in self.SUNSET_INDUSTRIES:
            return False, "夕阳行业，需求永久性萎缩"

        # 2. 检查产能过剩
        if industry_data.get('capacity_utilization', 100) < 70:
            if industry_data.get('loss_years', 0) > 3:
                return False, "产能过剩，长期亏损无修复预期"

        # 3. 检查政策风险
        if industry_data.get('policy_risk', False):
            return False, "面临永久性政策压制"

        return True, "通过风控"
```

### 4.5 逆向评分计算器 (ScoreCalculator)
```python
class ScoreCalculator:
    """逆向投资价值综合评分（0~100）"""

    def calculate(self, analysis_result: dict) -> dict:
        """
        计算综合逆向得分
        """
        score = 0
        details = {}

        # 1. 背离强度得分（最高40分）
        divergence_score = min(40, analysis_result['divergence']['strength'] * 0.4)
        score += divergence_score
        details['divergence_score'] = divergence_score

        # 2. 基本面极值得分（最高30分）
        if analysis_result['prosperity_pct'] <= 10:
            prosperity_score = 30
        elif analysis_result['prosperity_pct'] <= 20:
            prosperity_score = 20
        else:
            prosperity_score = 0
        score += prosperity_score
        details['prosperity_score'] = prosperity_score

        # 3. 估值安全边际得分（最高20分）
        if analysis_result['valuation_pct'] <= 15:
            valuation_score = 20
        elif analysis_result['valuation_pct'] <= 25:
            valuation_score = 10
        else:
            valuation_score = 0
        score += valuation_score
        details['valuation_score'] = valuation_score

        # 4. 边际改善得分（最高10分）
        if analysis_result.get('margin_improving'):
            score += 10
            details['margin_score'] = 10
        else:
            details['margin_score'] = 0

        return {
            "total_score": min(100, score),
            "details": details,
            "level": self._score_to_level(score)
        }

    def _score_to_level(self, score: float) -> str:
        if score >= 60:
            return "高确定性机会"
        elif score >= 30:
            return "观察区间"
        else:
            return "无逆向价值"
```

---

## 五、输出层设计

### 5.1 报告生成器 (Reporter)
```python
class Reporter:
    """行业分析报告生成器"""

    def generate(self, industry_name: str, result: dict) -> str:
        """生成 Markdown 格式分析报告"""
        template = f"""
# {industry_name} 逆向投资分析报告

## 一、核心指标
| 指标 | 数值 | 历史分位 |
|------|------|----------|
| 景气度 | {result['prosperity']} | {result['prosperity_pct']}% |
| 估值(PE) | {result['pe']} | {result['valuation_pct']}% |
| 价格 | {result['price']} | {result['price_pct']}% |

## 二、背离分析
- 背离类型: {result['divergence']['type']}
- 背离强度: {result['divergence']['strength']}
- 核心逻辑: {result['divergence_text']}

## 三、信号判定
- **判定结果**: {result['signal']}
- **逆向评分**: {result['score']['total_score']}分（{result['score']['level']}）

## 四、风险提示
{result['risk_warnings']}

## 五、操作建议
{result['recommendation']}
"""
        return template
```

### 5.2 结果导出器 (ResultExporter)
```python
class ResultExporter:
    """结果导出器"""

    def export_csv(self, results: list, output_path: str):
        """导出为CSV"""
        df = pd.DataFrame([self._to_row(r) for r in results])
        df.to_csv(output_path, index=False, encoding='utf-8-sig')

    def export_markdown(self, results: list, output_path: str):
        """导出为Markdown"""
        lines = ["# 周期行业逆向分析周报\n"]
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d')}\n")
        for r in results:
            lines.append(self._to_md_section(r))
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
```

---

## 六、数据存储设计

### 6.1 SQLite 结果存储
```sql
-- 每次运行的结果存储
CREATE TABLE IF NOT EXISTS analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date TEXT NOT NULL,           -- 运行日期
    industry TEXT NOT NULL,            -- 行业名称
    prosperity_pct REAL,              -- 景气分位
    valuation_pct REAL,               -- 估值分位
    price_pct REAL,                   -- 价格分位
    divergence_type TEXT,             -- 背离类型
    divergence_strength REAL,         -- 背离强度
    signal TEXT,                      -- 信号判定
    score_total REAL,                 -- 综合得分
    score_level TEXT,                 -- 得分等级
    risk_warnings TEXT,               -- 风险提示
    recommendation TEXT,              -- 操作建议
    raw_data_json TEXT,               -- 原始数据JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_run_date ON analysis_results(run_date);
CREATE INDEX idx_industry ON analysis_results(industry);
```

---

## 七、CLI 交互设计

### 7.1 命令行接口
```python
# main.py 命令设计
@click.group()
def cli():
    """逆向周期行业投资分析系统"""
    pass

@cli.command()
@click.option('--date', default=None, help='分析日期 YYYY-MM-DD')
@click.option('--industries', default=None, multiple=True, help='指定行业')
@click.option('--output-dir', default='./data/results', help='输出目录')
def analyze(date, industries, output_dir):
    """执行行业分析"""
    pass

@cli.command()
@click.option('--start-date', required=True)
@click.option('--end-date', required=True)
@click.option('--industry', required=True)
def history(start_date, end_date, industry):
    """查看行业历史分析记录"""
    pass

@cli.command()
@click.option('--format', type=click.Choice(['csv', 'markdown']), default='markdown')
def export(format):
    """导出最新分析结果"""
    pass
```

### 7.2 使用示例
```bash
# 全量分析所有行业
python main.py analyze

# 分析指定日期
python main.py analyze --date 2024-01-15

# 仅分析特定行业
python main.py analyze --industries 航空机场 --industries 生猪养殖

# 导出CSV
python main.py export --format csv

# 查看历史
python main.py history --start-date 2024-01-01 --end-date 2024-03-01 --industry 航空机场
```

---

## 八、关键数据源接口清单

| 数据类型 | 主要来源 | 接口函数 | 频率 | 覆盖年限 |
|---------|---------|---------|------|---------|
| 行业指数 | akshare | get_industry_index_daily() | 日 | 10年+ |
| 行业PE/PB | akshare | get_stock_pe_pb() | 周 | 10年 |
| 宏观PMI | akshare | macro_china_pmi() | 月 | 10年+ |
| 工业企业利润 | akshare | macro_industrial_profit() | 月 | 10年+ |
| 机构持仓 | tushare | fund_holdings() | 季 | 5年 |
| 北向资金 | tushare | hsgt_top10() | 日 | 5年 |
| 统计局GDP | 统计局API | requests.get() | 季 | 10年+ |

---

## 九、异常处理与容错

### 9.1 异常分类处理
```python
class DataError(Exception):
    """数据相关异常"""
    pass

class CalculationError(Exception):
    """计算异常"""
    pass

class NetworkError(Exception):
    """网络请求异常"""
    pass

# 全局异常处理
def global_exception_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except NetworkError as e:
            log.error(f"网络请求失败: {e}, 跳过该数据源")
            return None
        except DataError as e:
            log.error(f"数据异常: {e}, 使用替代数据")
            return get_backup_data()
        except CalculationError as e:
            log.error(f"计算异常: {e}")
            raise
    return wrapper
```

### 9.2 熔断降级策略
```python
# 连续失败N次后，临时跳过该数据源
CIRCUIT_BREAKER = {
    "failure_threshold": 3,
    "recovery_timeout": 300,  # 5分钟后重试
}
```

---

## 十、文档版本管理
| 版本 | 日期 | 修改内容 |
|------|------|---------|
| V1.0 | 2024-XX-XX | 初稿完成 |

---

## 附录A：待确认事项

1. [ ] 行业协会具体数据URL待用户提供
2. [ ] Tushare token 待配置
3. [ ] 行业指数代码映射表需根据实际可用数据调整
4. [ ] 机构持仓数据源是否充足，待测试
