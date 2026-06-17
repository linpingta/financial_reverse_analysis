# 逆向周期行业投资分析系统 开发计划 V1.0

## 一、项目概述

基于业务设计文档和技术设计文档，制定本开发计划。系统为本地 Python 程序，实现周期行业逆向投资分析。

---

## 二、开发阶段总览

```
阶段一：基础设施搭建（预计工作量：小）
阶段二：数据采集模块开发（预计工作量：中）
阶段三：核心分析引擎开发（预计工作量：中）
阶段四：输出与存储模块（预计工作量：小）
阶段五：CLI 整合与测试（预计工作量：中）
阶段六：真实验证与优化（预计工作量：持续）
```

---

## 三、详细开发计划

### 阶段一：基础设施搭建

| 序号 | 任务 | 说明 | 优先级 |
|------|------|------|--------|
| 1.1 | 创建项目目录结构 | 按技术设计创建所有文件夹 | P0 |
| 1.2 | 创建 `config.yaml` | 配置行业池、阈值、API参数 | P0 |
| 1.3 | 创建 `requirements.txt` | 依赖库清单 | P0 |
| 1.4 | 安装依赖并验证 | pip install -r requirements.txt | P0 |
| 1.5 | 配置日志模块 | loguru 配置 | P1 |

**产出**：`config.yaml`、`requirements.txt`、目录结构

---

### 阶段二：数据采集模块开发

#### 2.0 数据源方案（已验证）

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          数据源架构（已验证可用）                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  【行业实时PE/PB】                                                       │
│    接口: akshare.sw_index_second_info()                                 │
│    覆盖: 131个申万二级行业，含静态PE、TTM PE、PB、股息率                  │
│    状态: ✅ 已验证                                                       │
│                                                                         │
│  【行业历史价格】                                                        │
│    接口: baostock.query_history_k_data_plus()                          │
│    覆盖: 10年+ 日线数据，含收盘价、成交量、市值                           │
│    状态: ✅ 已验证                                                       │
│                                                                         │
│  【行业成分股】                                                          │
│    接口: baostock.query_stock_industry()                               │
│    覆盖: 5530只股票/84个行业分类                                        │
│    状态: ✅ 已验证                                                       │
│                                                                         │
│  【个股财务数据】                                                        │
│    接口: baostock.query_profit_data()                                   │
│    覆盖: 10年+ 利润表数据，含 epsTTM                                    │
│    状态: ✅ 已验证                                                       │
│                                                                         │
│  【宏观景气指标】                                                        │
│    接口: akshare.macro_china_pmi() / macro_china_cpi() 等              │
│    覆盖: PMI、CPI、PPI、M2、工业企业利润                                 │
│    状态: ✅ 已验证                                                       │
│                                                                         │
│  【申万行业列表】                                                        │
│    接口: akshare.sw_index_first_info() / sw_index_second_info()        │
│    覆盖: 31个申万一级行业、131个申万二级行业                             │
│    状态: ✅ 已验证                                                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 2.1 Baostock 数据采集器（主数据源）

**模块**: `src/data/collectors/baostock_collector.py`

```python
# 数据采集接口清单

# 1. 登录/登出
bs.login()
bs.logout()

# 2. 行业成分股列表
bs.query_stock_industry()
# 返回: 股票代码、名称、行业分类

# 3. 沪深300成分股
bs.query_hs300_stocks()
# 返回: 成分股列表

# 4. 个股历史K线（含调整因子）
bs.query_history_k_data_plus(
    code="sh.600519",
    fields="date,code,open,high,low,close,volume,amount",
    start_date="2014-01-01",
    end_date="2024-12-31",
    frequency="d"  # d=日线, w=周线, m=月线
)

# 5. 个股利润表
bs.query_profit_data(
    code="sh.600519",
    year="2024",
    quarter="4"  # 可选
)
# 返回字段: pubDate, statDate, code, roe, npMargins, gpMargin,
#          epsTTM(关键字段), netProfit, opProfit, revenue, totalAsset

# 6. 季频财务指标（包含更多字段）
bs.query_quarterly_fina_indicator(
    code="sh.600519",
    start_date="2014-01-01",
    end_date="2024-12-31"
)
```

#### 2.2 Akshare 数据采集器（辅助数据源）

**模块**: `src/data/collectors/akshare_collector.py`

```python
# 数据采集接口清单

# 1. 申万二级行业实时估值（核心接口）
ak.sw_index_second_info()
# 返回: 行业代码、行业名称、静态PE、TTM PE、PB、市净率、股息率、市值
# 用途: 获取当前行业PE/PB分位

# 2. 申万一级行业列表
ak.sw_index_first_info()
# 返回: 申万一级行业代码和名称

# 3. 申万行业历史日线
ak.sw_index_daily(indicator="801991.SI")
# 返回: 申万行业指数历史数据

# 4. 宏观PMI数据
ak.macro_china_pmi()
# 返回: 制造业PMI、非制造业PMI

# 5. 宏观CPI/PPI
ak.macro_china_cpi()
ak.macro_china_ppi()

# 6. 货币供应量
ak.macro_china_money_supply()

# 7. 工业企业利润
ak.macro_china_industrial_enterprise_profit()
```

#### 2.3 行业PE/PB计算器（核心模块）

**模块**: `src/data/industry_pe_pb_calculator.py`

由于申万只提供实时PE/PB，需要自行计算历史分位：

```python
"""
行业历史 PE/PB 计算方法

方法1: 基于成分股财务数据加权计算
  PE_TTM = Σ(成分股市值) / Σ(成分股净利润TTM)
  PB = Σ(成分股市值) / Σ(成分股净资产)

方法2: 指数点位 / 指数EPS
  PE = 指数点位 / 指数EPS
  (需要申万提供指数EPS历史数据，或自行计算)

推荐实现路径:
1. 使用 akshare.sw_index_second_info() 获取当前PE/PB
2. 使用 akshare.sw_index_daily() 获取行业指数历史点位
3. 使用 baostock 成分股财务数据估算历史PE分位

简化方案（满足基本需求）:
1. 获取申万行业当前PE/PB（实时）
2. 获取行业指数历史点位
3. 通过点位变化估算估值分位
"""

class IndustryPEPBHistoryCalculator:
    """行业历史PE/PB计算器"""

    def get_current_pe_pb(self, sw_index_code: str) -> dict:
        """获取当前PE/PB（来自申万实时数据）"""
        pass

    def get_industry_index_history(self, sw_index_code: str) -> pd.DataFrame:
        """获取行业指数历史点位"""
        pass

    def calculate_percentile(self, sw_index_code: str) -> dict:
        """计算PE/PB分位"""
        pass
```

#### 2.4 模块文件结构

```
src/data/
├── __init__.py
├── collectors/
│   ├── __init__.py
│   ├── base_collector.py      # 基类，定义统一接口
│   ├── baostock_collector.py  # Baostock 数据采集器
│   ├── akshare_collector.py   # Akshare 数据采集器
│   └── macro_collector.py     # 宏观数据采集器
├── industry_pe_pb_calculator.py  # 行业PE/PB计算器
├── industry_mapper.py         # 行业映射（业务→申万→Baostock）
├── data_cache.py              # 数据缓存（避免重复请求）
└── collector_factory.py        # 采集器工厂
```

#### 2.5 统一数据接口

**模块**: `src/data/collector_factory.py`

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import pandas as pd

@dataclass
class IndustryData:
    """行业数据结构"""
    name: str                    # 业务行业名称
    sw_code: str                 # 申万行业代码
    baostock_code: str           # Baostock 行业代码

    # 当前数据
    current_price: Optional[float] = None
    current_pe: Optional[float] = None
    current_pb: Optional[float] = None
    pe_percentile: Optional[float] = None  # PE历史分位
    pb_percentile: Optional[float] = None  # PB历史分位

    # 历史数据
    price_history: Optional[pd.DataFrame] = None
    pe_history: Optional[pd.DataFrame] = None

    # 元数据
    update_time: Optional[datetime] = None

class DataCollector:
    """统一数据采集入口"""

    def __init__(self, config: dict):
        self.config = config
        self.baostock = BaostockCollector()
        self.akshare = AkshareCollector()
        self.macro = MacroCollector()

    def collect_industry(self, industry_name: str) -> IndustryData:
        """采集指定行业的完整数据"""
        pass

    def collect_all_industries(self) -> list[IndustryData]:
        """采集所有目标行业数据"""
        pass

    def collect_macro(self) -> dict:
        """采集宏观数据"""
        pass
```

#### 2.6 任务清单（修订）

| 序号 | 任务 | 接口/方法 | 优先级 |
|------|------|----------|--------|
| 2.1 | Baostock采集器基类 | `base_collector.py` | P0 |
| 2.2 | Baostock行情数据 | `query_history_k_data_plus()` | P0 |
| 2.3 | Baostock成分股 | `query_stock_industry()` | P0 |
| 2.4 | Baostock财务数据 | `query_profit_data()` | P0 |
| 2.5 | Akshare申万实时估值 | `sw_index_second_info()` | P0 |
| 2.6 | Akshare宏观数据 | `macro_china_*` | P1 |
| 2.7 | 行业PE/PB计算器 | `industry_pe_pb_calculator.py` | P0 |
| 2.8 | 行业映射表 | `industry_mapper.py` | P0 |
| 2.9 | 数据缓存机制 | `data_cache.py` | P1 |
| 2.10 | 统一采集入口 | `collector_factory.py` | P0 |

**注**: Tushare 适配器已降级为P2（免费版数据有限）

**待确认**: 无需用户提供额外数据

---

#### 2.7 数据采集流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                      数据采集主流程                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 初始化                                                       │
│     ├── 加载 config.yaml                                        │
│     ├── 登录 Baostock                                           │
│     └── 初始化 Akshare                                          │
│                                                                 │
│  2. 获取行业列表                                                 │
│     └── 读取配置的 10 个目标行业                                  │
│                                                                 │
│  3. 批量采集行业数据（每个行业）                                  │
│     ┌─────────────────────────────────────────────────────────┐ │
│     │ 3.1 获取申万实时PE/PB                                    │ │
│     │     └── akshare.sw_index_second_info()                 │ │
│     │                                                         │ │
│     │ 3.2 获取行业指数历史点位                                  │ │
│     │     └── akshare.sw_index_daily()                       │ │
│     │                                                         │ │
│     │ 3.3 计算PE/PB分位                                        │ │
│     │     └── 基于历史数据计算                                  │ │
│     │                                                         │ │
│     │ 3.4 获取成分股列表（备用）                                │ │
│     │     └── baostock.query_stock_industry()                │ │
│     │                                                         │ │
│     │ 3.5 获取个股财务数据（备用）                              │ │
│     │     └── baostock.query_profit_data()                   │ │
│     └─────────────────────────────────────────────────────────┘ │
│                                                                 │
│  4. 采集宏观数据                                                 │
│     └── akshare.macro_china_pmi/cpi/ppi()                     │
│                                                                 │
│  5. 缓存数据                                                     │
│     └── 保存到本地缓存，避免重复请求                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 2.8 错误处理与降级策略

```python
# 错误处理策略
ERROR_STRATEGY = {
    # 网络错误：重试3次，间隔2秒
    "NetworkError": {"retry": 3, "interval": 2, "fallback": None},

    # 数据为空：使用备源
    "DataEmpty": {"retry": 1, "fallback": "alternative_source"},

    # API限流：等待后重试
    "RateLimit": {"retry": 5, "interval": 60, "fallback": None},

    # 未知错误：跳过并记录
    "Unknown": {"retry": 0, "fallback": None, "log": True},
}

# 降级数据源映射
FALLBACK_MAP = {
    # 申万实时PE/PB
    "akshare_sw_pe_pb": ["baostock_self_calculation", "skip"],

    # Baostock K线
    "baostock_kline": ["akshare_sw_daily", "skip"],

    # 宏观数据
    "macro_pmi": ["skip", "manual"],
}
```

#### 2.9 缓存机制

```python
# 数据缓存设计
CACHE_CONFIG = {
    "enabled": True,
    "cache_dir": "data/cache",
    "expire_hours": 24,  # 日线数据缓存24小时

    # 缓存文件命名
    # data/cache/industry_pe_pb_YYYYMMDD.json
    # data/cache/macro_2024_06.json
}
```

---

**产出**：
- `src/data/collectors/baostock_collector.py`
- `src/data/collectors/akshare_collector.py`
- `src/data/industry_pe_pb_calculator.py`
- `src/data/industry_mapper.py`
- `src/data/data_cache.py`
- `src/data/collector_factory.py`

---

---

### 阶段三：核心分析引擎开发

#### 3.1 分位计算模块
| 序号 | 任务 | 说明 | 优先级 |
|------|------|------|--------|
| 3.1.1 | 分位计算器 | `PercentileCalculator` | P0 |
| 3.1.2 | 批量分位计算 | 多指标并行 | P0 |
| 3.1.3 | 边界处理 | 数据不足10年时的处理 | P1 |

#### 3.2 背离分析引擎
| 序号 | 任务 | 说明 | 优先级 |
|------|------|------|--------|
| 3.2.1 | 背离类型判定 | 买点/卖点/无背离 | P0 |
| 3.2.2 | 背离强度计算 | 分值量化 | P0 |
| 3.2.3 | 多维度背离检测 | 价格vs景气、估值vs价格 | P0 |

#### 3.3 信号判定器
| 序号 | 任务 | 说明 | 优先级 |
|------|------|------|--------|
| 3.3.1 | 买入信号判定 | 全部条件满足逻辑 | P0 |
| 3.3.2 | 卖出预警判定 | 任意2条触发逻辑 | P0 |
| 3.3.3 | 观望区间判定 | 中性判定 | P0 |

#### 3.4 风控过滤器
| 序号 | 任务 | 说明 | 优先级 |
|------|------|------|--------|
| 3.4.1 | 夕阳行业过滤 | 黑名单机制 | P0 |
| 3.4.2 | 产能过剩检测 | 产能利用率判断 | P1 |
| 3.4.3 | 政策风险检测 | 政策压制识别 | P2 |

#### 3.5 逆向评分计算
| 序号 | 任务 | 说明 | 优先级 |
|------|------|------|--------|
| 3.5.1 | 综合评分算法 | 0-100分 | P0 |
| 3.5.2 | 评分等级划分 | 三档：机会/观察/规避 | P0 |
| 3.5.3 | 得分明细 | 各维度贡献分展示 | P1 |

---

### 阶段四：输出与存储模块

| 序号 | 任务 | 说明 | 优先级 |
|------|------|------|--------|
| 4.1 | SQLite 结果存储 | `result_db.py` | P0 |
| 4.2 | Markdown 报告生成 | `Reporter` | P0 |
| 4.3 | CSV 导出功能 | `ResultExporter` | P1 |
| 4.4 | Excel 导出功能 | (可选) | P2 |

---

### 阶段五：CLI 整合与测试

| 序号 | 任务 | 说明 | 优先级 |
|------|------|------|--------|
| 5.1 | CLI 命令框架 | click 框架 | P0 |
| 5.2 | `analyze` 命令 | 全量/指定行业分析 | P0 |
| 5.3 | `history` 命令 | 历史记录查询 | P1 |
| 5.4 | `export` 命令 | 结果导出 | P1 |
| 5.5 | 单元测试 | pytest 测试用例 | P1 |

---

### 阶段六：真实验证与优化

| 序号 | 任务 | 说明 | 优先级 |
|------|------|------|--------|
| 6.1 | 全行业数据拉取测试 | 验证10个行业数据可用性 | P0 |
| 6.2 | 历史分位准确性验证 | 对标已知历史高低点 | P0 |
| 6.3 | 航空行业回测验证 | 对比2023年逆向买点案例 | P0 |
| 6.4 | 数据源优化 | 根据实际可用性调整 | P1 |
| 6.5 | 阈值参数调优 | 根据验证结果微调 | P2 |

---

## 四、优先级排序（P0 = 必须先行）

```
P0 任务（阻塞其他任务）:
├── 1.1 项目目录结构
├── 1.2 config.yaml 配置
├── 1.3 requirements.txt
├── 2.1.1 行业指数数据获取
├── 2.1.2 行业PE/PB获取
├── 2.4.1 数据采集统一入口
├── 3.1.1 分位计算器
├── 3.2.1 背离类型判定
├── 3.3.1 买入信号判定
├── 5.1 CLI 命令框架
└── 6.1 全行业数据测试

P1 任务（核心功能）:
├── 2.2 Tushare 适配器
├── 2.3 统计局 API
├── 3.3.2 卖出预警判定
├── 3.4 风控过滤器
├── 3.5 逆向评分计算
├── 4.1 SQLite 存储
├── 4.2 Markdown 报告
└── 5.2 analyze 命令

P2 任务（增强功能）:
├── 2.2.3 机构持仓
├── 2.3.2 行业协会爬虫
├── 4.3 CSV 导出
└── 阶段六优化类任务
```

---

## 五、第一个可运行版本（MVP）检查清单

目标：能够运行 `python main.py analyze` 并输出10个行业的分析报告

**MVP 必须包含**：
- [ ] 项目结构搭建完成
- [ ] config.yaml 配置正确
- [ ] akshare 行业数据获取正常
- [ ] 分位计算功能正常
- [ ] 背离分析逻辑正确
- [ ] 买入/卖出/观望判定正确
- [ ] 输出 Markdown 报告
- [ ] 至少一个行业验证通过

**MVP 不包含**：
- Tushare（可后续补充）
- 统计局爬虫（可后续补充）
- SQLite 存储（可后续补充）
- CLI 完整功能（可后续补充）

---

## 六、风险点与应对

| 风险 | 可能性 | 影响 | 应对措施 |
|------|--------|------|---------|
| 数据源API不稳定 | 中 | 高 | 接入多个备源，实现熔断降级 |
| 行业指数代码映射错误 | 中 | 高 | 先用 akshare 默认指数，后续调整 |
| 行业景气指标难以量化 | 高 | 中 | 使用宏观代理指标（PMI等） |
| 10年历史数据不足 | 中 | 中 | 动态调整分位计算窗口 |
| Tushare 免费版数据有限 | 高 | 低 | 优先用 akshare，降级处理 |

---

## 七、待确认事项

在开发前需用户确认：

| 序号 | 问题 | 状态 |
|------|------|------|
| 1 | 是否提供 Tushare token？ | ✅ 已确认不需要（免费版权限有限） |
| 2 | 行业协会数据URL有哪些？ | ✅ 已确认不需要（使用申万行业即可） |
| 3 | 是否需要保留机构持仓功能？ | ✅ 已确认不需要 |
| 4 | 是否有特定行业优先开发需求？ | 待确认 |
| 5 | 数据存储路径偏好？ | 默认 `./data/results` |
| 6 | 阶段二详细设计是否确认？ | 待确认 |

---

## 八、版本规划

| 版本 | 目标 | 主要内容 |
|------|------|---------|
| V0.1 | MVP | 单一行业数据拉取 + 分位计算 + 背离判定 |
| V0.2 | 核心功能 | 10行业全量分析 + Markdown报告 |
| V0.3 | 完善功能 | SQLite存储 + CLI + 风控过滤 |
| V1.0 | 稳定版 | 全功能 + 验证优化 + 文档完善 |

---

**建议优先开发顺序**：
1. 先用 akshare 拉取 1 个行业（如航空机场）的数据，验证可行性
2. 完成分位计算和背离分析逻辑
3. 扩展到 10 个行业
4. 补充其他数据源

是否按此计划开始开发？
