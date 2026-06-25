# 逆向周期行业投资分析系统

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

基于基本面-估值-股价背离的逆向投资策略分析工具，专注于周期性行业投资机会识别。

## 项目简介

本系统通过分析强周期行业的景气度、估值水平和股价走势之间的背离关系，识别逆向投资机会。系统覆盖10个典型周期行业，使用申万行业指数和公开数据源进行量化分析，为投资决策提供数据支持。

### 核心功能

- **多维度分析**：景气度、估值、价格三维度背离检测
- **智能评分**：逆向投资机会评分系统（0-100分）
- **信号判定**：自动生成买入/卖出/持有信号
- **风险预警**：识别潜在风险因素
- **历史回溯**：支持历史数据查询和对比分析
- **多样化输出**：控制台、Markdown报告、CSV/Excel导出

## 目标行业

系统覆盖10个强周期行业：

| 行业 | 申万代码 | 监控指标 |
|------|----------|----------|
| 航空机场 | 801991.SI | 旅客周转量、客座率、航油价格 |
| 生猪养殖 | 801017.SI | 能繁母猪存栏量、生猪价格、猪粮比 |
| 基础化工 | 801033.SI | 化工品价格指数、开工率、库存周期 |
| 煤炭 | 801951.SI | 秦皇岛煤价指数、港口库存、发电量 |
| 有色金属 | 801055.SI | LME铜价、库存变化、加工费 |
| 远洋航运 | 801992.SI | BDI指数、集装箱运价、新船订单 |
| 酒店旅游 | 801219.SI | 出游人数、酒店入住率、旅游收入 |
| 周期半导体 | 801081.SI | 全球半导体销售额、存储芯片价格 |
| 光伏上游 | 801735.SI | 硅料价格、组件价格、装机量 |
| 工程机械 | 801077.SI | 挖掘机销量、小松开工小时数、房地产新开工 |

## 安装

### 环境要求

- Python 3.8 或更高版本
- Windows / Linux / macOS

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd financial_reverse_analysis
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置检查**
```bash
python -m src.cli.main version
```

## 快速开始

### 1. 查看目标行业列表

```bash
python -m src.cli.main list-industries
```

### 2. 分析所有行业

```bash
# 基础分析（控制台输出）
python -m src.cli.main analyze --all

# 分析并保存到数据库
python -m src.cli.main analyze --all --save-db

# 分析并生成Markdown报告
python -m src.cli.main analyze --all --generate-report

# 同时保存数据库和生成报告
python -m src.cli.main analyze --all --save-db --generate-report
```

### 3. 分析指定行业

```bash
# 分析单个行业
python -m src.cli.main analyze --industry 航空机场

# 分析多个行业
python -m src.cli.main analyze --industry 航空机场 --industry 生猪养殖

# 分析并生成报告
python -m src.cli.main analyze --industry 航空机场 --generate-report
```

### 4. 查询历史记录

```bash
# 查询今天的记录
python -m src.cli.main history --date 2024-01-15

# 查询指定行业的历史记录
python -m src.cli.main history --industry 航空机场

# 查询买入信号
python -m src.cli.main history --signal buy

# 查询最新10条记录
python -m src.cli.main history --latest --limit 10
```

### 5. 导出分析结果

```bash
# 导出为CSV格式
python -m src.cli.main export --date 2024-01-15 --format csv

# 导出为Excel格式
python -m src.cli.main export --industry 航空机场 --format excel

# 导出为Markdown格式
python -m src.cli.main export --signal buy --format markdown

# 导出到指定文件
python -m src.cli.main export --latest --format csv --output ./data/results/analysis
```

## 项目结构

```
financial_reverse_analysis/
├── config/                 # 配置文件
│   ├── config.yaml        # 主配置文件
│   └── logger.py          # 日志配置
├── data/                   # 数据目录
│   ├── cache/             # 数据缓存
│   ├── results/           # 分析结果
│   └── results.db         # SQLite数据库
├── docs/                   # 文档目录
│   └── *.md               # 开发文档
├── reports/                # 生成的报告
├── src/                    # 源代码
│   ├── analysis/          # 分析引擎
│   │   ├── analysis_engine.py          # 分析引擎核心
│   │   ├── divergence_analyzer.py      # 背离分析器
│   │   ├── percentile_calculator.py    # 分位计算器
│   │   ├── reverse_scoring.py          # 逆向评分系统
│   │   ├── risk_filter.py              # 风险过滤
│   │   └── signal_judgment.py          # 信号判定
│   ├── cli/               # 命令行接口
│   │   └── main.py        # CLI主入口
│   ├── data/              # 数据采集
│   │   ├── collectors/    # 数据采集器
│   │   │   ├── akshare_collector.py     # Akshare数据源
│   │   │   ├── baostock_collector.py    # Baostock数据源
│   │   │   ├── base_collector.py        # 基础采集器
│   │   │   └── macro_collector.py       # 宏观数据采集
│   │   ├── collector_factory.py         # 采集器工厂
│   │   ├── data_cache.py                # 数据缓存
│   │   ├── industry_mapper.py           # 行业映射
│   │   └── industry_pe_pb_calculator.py # PE/PB计算器
│   └── output/            # 输出模块
│       ├── reporter.py                  # 报告生成器
│       ├── result_db.py                 # 数据库管理
│       └── result_exporter.py           # 结果导出器
├── tests/                  # 测试文件
├── requirements.txt        # 依赖清单
└── README.md              # 本文件
```

## 核心模块说明

### 1. 数据采集层 (`src/data/`)

- **Baostock采集器**：主要数据源，提供行业历史价格、成分股数据
- **Akshare采集器**：辅助数据源，提供申万行业实时估值数据
- **宏观数据采集**：PMI、CPI、PPI等宏观经济指标
- **数据缓存**：自动缓存机制，减少重复请求

### 2. 分析引擎层 (`src/analysis/`)

#### 背离检测
- **价格-估值背离**：PE/PB分位与股价分位的偏离
- **景气-估值背离**：行业景气度与估值水平的背离
- **多周期确认**：通过时间窗口确认背离有效性

#### 逆向评分系统
- **景气度权重**：30分
- **估值优势权重**：30分
- **价格位置权重**：20分
- **背离强度权重**：20分

评分等级：
- **A级**：80-100分（强买入机会）
- **B级**：60-79分（中等机会）
- **C级**：40-59分（一般机会）
- **D级**：0-39分（无机会）

#### 信号判定
- **买入信号**：景气高+估值低+价格低 + 背离确认
- **卖出信号**：景气低+估值高+价格高 + 背离确认
- **持有信号**：其他情况

### 3. 输出层 (`src/output/`)

- **数据库存储**：SQLite持久化分析结果
- **报告生成**：Markdown格式详细报告
- **数据导出**：CSV、Excel格式导出
- **历史查询**：支持多维度历史数据检索

## 配置说明

主配置文件：`config/config.yaml`

### 关键配置项

```yaml
# 分析参数
analysis:
  percentile:
    low_threshold: 20      # 低分位阈值
    high_threshold: 80     # 高分位阈值
  divergence:
    price_window: 12       # 价格观察窗口（周）
    valuation_window: 12   # 估值观察窗口（周）
    confirm_weeks: 4       # 确认周期（周）

# 数据参数
data_params:
  history_years: 10        # 历史数据年限
  update_frequency: "weekly"  # 更新频率
  cache:
    enabled: true
    expire_hours: 24       # 缓存过期时间

# 输出配置
output:
  report_dir: "reports"    # 报告目录
  database: "data/results.db"  # 数据库路径
```

## 数据源说明

### 主要数据源

1. **Baostock**（免费、无限制）
   - 行业历史价格数据（10年+）
   - 成分股信息
   - 个股财务数据

2. **Akshare**（免费、无限制）
   - 申万行业实时估值（PE、PB、股息率）
   - 宏观经济指标（PMI、CPI、PPI、M2）

### 数据更新频率

- **实时数据**：每日更新
- **历史数据**：按需获取，自动缓存24小时
- **宏观数据**：月度更新

## 输出示例

### 控制台输出

```
开始分析 10 个行业...
================================================================================

[1/10] 正在分析: 航空机场
--------------------------------------------------------------------------------
  → 采集行业数据...
  → 执行分析引擎...

航空机场 - 核心指标
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ 指标           ┃ 数值          ┃ 分位   ┃
┠────────────────┼────────────────┼────────┨
│ PE估值         │ 25.3          │ 15%    │
│ PB估值         │ 1.2           │ 20%    │
└────────────────┴────────────────┴────────┘

信号判定: [buy] 买入
操作建议: 景气度上升+估值处于历史低位，建议分批建仓

逆向评分: 75 分
评级: B级

风险提示:
  • 行业整体景气度仍处于较低水平
  • 需关注宏观经济下行风险
```

### Markdown报告

系统会生成包含以下内容的详细报告：
- 核心指标表格
- 背离分析详情
- 评分明细
- 风险提示
- 操作建议

## 开发文档

详细的开发文档请参见 `docs/` 目录：

- `development_plan_v1.0.md` - 开发计划
- `technical_design_v1.0.md` - 技术设计文档
- `phase*_code_review.md` - 各阶段代码审查
- `phase*_completion_summary.md` - 阶段完成总结

## 测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_cli.py

# 生成覆盖率报告
pytest --cov=src tests/
```

## 常见问题

### Q: 数据采集失败怎么办？

A: 检查网络连接，确认数据源可访问。系统会自动重试，失败的数据会跳过并记录日志。

### Q: 如何更新行业配置？

A: 编辑 `config/config.yaml` 文件中的 `industries.target_industries` 部分。

### Q: 分析结果保存在哪里？

A:
- 数据库：`data/results.db`
- 报告：`reports/` 目录
- 导出文件：`data/results/` 目录

### Q: 如何调整分析参数？

A: 修改 `config/config.yaml` 中的 `analysis` 部分参数，然后重新运行分析。

## 技术栈

- **Python 3.8+**：核心语言
- **Click**：命令行界面框架
- **Rich**：终端富文本输出
- **Pandas**：数据处理
- **Baostock**：证券数据接口
- **Akshare**：金融数据接口
- **SQLite**：本地数据存储
- **Loguru**：日志管理
- **Pydantic**：数据验证

## 许可证

MIT License

## 免责声明

本系统仅供学习和研究使用，不构成任何投资建议。投资有风险，决策需谨慎。使用者应根据自身情况独立判断，系统开发者不承担任何因使用本系统而产生的投资损失责任。

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。

---

**版本**: 1.0.0  
**更新日期**: 2024