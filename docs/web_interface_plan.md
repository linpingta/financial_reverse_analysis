# Web界面交互模块开发计划

## 一、项目概述

为逆向周期行业投资分析系统开发一个Web界面，让用户可以通过浏览器快速访问所有功能，无需使用命令行。

---

## 二、现有系统功能分析

### 2.1 CLI功能清单

| 命令 | 功能 | 输入参数 | 输出 |
|------|------|---------|------|
| `analyze` | 分析行业投资机会 | --all, --industry, --save-db, --generate-report | 分析结果、评分、信号 |
| `history` | 查询历史记录 | --date, --industry, --signal, --latest, --limit | 历史记录表格 |
| `export` | 导出分析结果 | --date, --industry, --signal, --format, --output | CSV/Excel/Markdown文件 |
| `list_industries` | 列出目标行业 | 无 | 行业列表 |
| `version` | 显示版本信息 | 无 | 版本信息 |

### 2.2 核心模块

- **数据采集层**: `src/data/` - Baostock、Akshare数据源
- **分析引擎层**: `src/analysis/` - 分位计算、背离分析、信号判定
- **输出层**: `src/output/` - 数据库存储、报告生成、数据导出
- **CLI层**: `src/cli/` - 命令行接口

---

## 三、Web界面设计方案

### 3.1 技术栈选择

#### 后端框架
- **Flask** (推荐)
  - 优点: 轻量级、易上手、适合数据分析项目、Python原生
  - 缺点: 功能相对简单，需要手动配置较多组件
  
- **FastAPI** (备选)
  - 优点: 自动API文档、异步支持、类型安全
  - 缺点: 相对较新，学习曲线稍陡

**推荐选择**: Flask（与现有系统架构兼容性好，开发速度快）

#### 前端框架
- **Bootstrap 5** (推荐)
  - 优点: 成熟稳定、组件丰富、响应式设计、中文友好
  - 缺点: 样式相对传统
  
- **Tailwind CSS + Alpine.js** (备选)
  - 优点: 现代化、灵活、轻量
  - 缺点: 需要更多自定义工作

**推荐选择**: Bootstrap 5（快速开发，UI组件现成）

#### 数据可视化
- **Plotly** (推荐)
  - 优点: Python原生、交互式图表、支持多种图表类型
  - 缺点: 文件较大
  
- **Chart.js** (备选)
  - 优点: 轻量、美观、JavaScript原生
  - 缺点: 需要前后端数据传递

**推荐选择**: Plotly（与Python后端无缝集成）

#### 其他组件
- **Flask-RESTful**: RESTful API支持
- **Flask-CORS**: 跨域支持
- **Flask-SocketIO**: 实时数据推送（可选）
- **Waitress/Gunicorn**: 生产服务器

### 3.2 页面结构设计

```
Web界面结构
├── 首页 (Dashboard)
│   ├── 系统概览
│   ├── 最新分析结果
│   ├── 信号统计
│   └── 快速操作入口
│
├── 行业分析页面 (Analysis)
│   ├── 全量分析
│   ├── 单行业分析
│   ├── 分析进度显示
│   └── 结果实时展示
│
├── 历史记录页面 (History)
│   ├── 记录查询
│   ├── 数据筛选
│   ├── 结果表格展示
│   └── 详情查看
│
├── 数据导出页面 (Export)
│   ├── 格式选择
│   ├── 筛选条件
│   ├── 导出预览
│   └── 文件下载
│
├── 行业详情页面 (Industry Detail)
│   ├── 历史走势图
│   ├── 估值分位图
│   ├── 背离分析图
│   └── 详细数据表
│
└── 系统配置页面 (Settings)
    ├── 行业管理
    ├── 参数配置
    ├── 数据源状态
    └── 系统信息
```

### 3.3 功能模块设计

#### 3.3.1 Dashboard（首页）

**功能点**:
- 系统状态概览（数据源连接状态、数据库状态）
- 最新分析结果摘要（最近10条）
- 信号统计图表（买入/卖出/持有比例）
- 快速操作按钮（一键分析、查看报告、导出数据）
- 行业评分排行（Top 5机会行业）

**数据来源**:
- `ResultDB.query_latest(10)`
- `ResultDB.get_statistics()`
- 系统配置信息

#### 3.3.2 Analysis（行业分析）

**功能点**:
- 选择分析模式（全量/指定行业）
- 行业选择器（多选框）
- 分析参数配置（可选）
- 实时进度显示（进度条）
- 结果实时更新（AJAX）
- 保存选项（数据库/报告）

**API接口**:
- `POST /api/analyze` - 启动分析
- `GET /api/analyze/status` - 查询进度
- `GET /api/analyze/result` - 获取结果

#### 3.3.3 History（历史记录）

**功能点**:
- 多维度筛选（日期、行业、信号）
- 分页表格展示
- 详情弹窗查看
- 数据可视化（趋势图）
- 批量操作选择

**API接口**:
- `GET /api/history` - 查询历史记录
- `GET /api/history/<id>` - 查询详情
- `GET /api/history/stats` - 统计数据

#### 3.3.4 Export（数据导出）

**功能点**:
- 导出格式选择（CSV/Excel/Markdown）
- 筛选条件设置
- 数据预览表格
- 文件下载
- 导出历史记录

**API接口**:
- `POST /api/export` - 生成导出文件
- `GET /api/export/download/<filename>` - 下载文件

#### 3.3.5 Industry Detail（行业详情）

**功能点**:
- 行业历史走势图（价格、PE、PB）
- 分位数趋势图（10年历史）
- 背离分析可视化
- 关键指标对比
- 操作建议详情

**API接口**:
- `GET /api/industry/<name>` - 行业详情
- `GET /api/industry/<name>/history` - 历史数据
- `GET /api/industry/<name>/chart` - 图表数据

---

## 四、开发阶段规划

### 阶段一：基础架构搭建（预计1-2天）

| 序号 | 任务 | 文件 | 优先级 |
|------|------|------|--------|
| 1.1 | Flask应用初始化 | `src/web/app.py` | P0 |
| 1.2 | 目录结构创建 | `src/web/` | P0 |
| 1.3 | 配置文件扩展 | `config/config.yaml` | P0 |
| 1.4 | 依赖库安装 | `requirements.txt` | P0 |
| 1.5 | 基础路由设置 | `src/web/routes/` | P0 |
| 1.6 | 模板目录创建 | `src/web/templates/` | P0 |
| 1.7 | 静态文件目录 | `src/web/static/` | P0 |

**产出**:
- Flask应用骨架
- 基础路由框架
- 目录结构完整

### 阶段二：API接口开发（预计2-3天）

| 序号 | 任务 | API路径 | 优先级 |
|------|------|---------|--------|
| 2.1 | 分析接口 | `/api/analyze` | P0 |
| 2.2 | 历史查询接口 | `/api/history` | P0 |
| 2.3 | 导出接口 | `/api/export` | P0 |
| 2.4 | 行业详情接口 | `/api/industry` | P0 |
| 2.5 | 统计数据接口 | `/api/stats` | P1 |
| 2.6 | 系统状态接口 | `/api/system` | P1 |
| 2.7 | 配置管理接口 | `/api/config` | P2 |

**产出**:
- RESTful API完整
- API文档（Swagger）
- 接口测试通过

### 阶段三：前端页面开发（预计3-4天）

| 序号 | 任务 | 页面 | 优先级 |
|------|------|------|--------|
| 3.1 | 首页Dashboard | `index.html` | P0 |
| 3.2 | 行业分析页 | `analysis.html` | P0 |
| 3.3 | 历史记录页 | `history.html` | P0 |
| 3.4 | 数据导出页 | `export.html` | P1 |
| 3.5 | 行业详情页 | `industry_detail.html` | P1 |
| 3.6 | 系统配置页 | `settings.html` | P2 |
| 3.7 | 导航栏和布局 | `base.html` | P0 |

**产出**:
- 完整的前端页面
- 响应式布局
- 用户交互功能

### 阶段四：数据可视化（预计2-3天）

| 序号 | 任务 | 图表类型 | 优先级 |
|------|------|----------|--------|
| 4.1 | 分位数趋势图 | Plotly折线图 | P0 |
| 4.2 | 信号统计图 | Plotly饼图 | P0 |
| 4.3 | 行业对比图 | Plotly柱状图 | P0 |
| 4.4 | 背离分析图 | Plotly组合图 | P1 |
| 4.5 | 评分分布图 | Plotly散点图 | P1 |
| 4.6 | 历史走势图 | Plotly面积图 | P1 |

**产出**:
- 交互式图表
- 数据可视化组件
- 图表配置选项

### 阶段五：集成测试与优化（预计1-2天）

| 序号 | 任务 | 说明 | 优先级 |
|------|------|------|--------|
| 5.1 | 功能测试 | 所有页面功能测试 | P0 |
| 5.2 | 性能优化 | 响应速度优化 | P1 |
| 5.3 | 错误处理 | 异常处理完善 | P0 |
| 5.4 | UI优化 | 界面美化 | P1 |
| 5.5 | 文档编写 | 使用文档 | P1 |
| 5.6 | 部署配置 | 生产环境配置 | P2 |

**产出**:
- 测试通过的完整系统
- 用户使用文档
- 部署指南

---

## 五、文件结构设计

```
src/web/
├── __init__.py
├── app.py                    # Flask主应用
├── config.py                 # Web配置
├── routes/                   # 路由模块
│   ├── __init__.py
│   ├── main.py               # 主页面路由
│   ├── api.py                # API路由
│   └── industry.py           # 行业相关路由
├── templates/                # HTML模板
│   ├── base.html             # 基础模板
│   ├── index.html            # 首页
│   ├── analysis.html         # 分析页
│   ├── history.html          # 历史页
│   ├── export.html           # 导出页
│   ├── industry_detail.html  # 行业详情页
│   └── settings.html         # 配置页
├── static/                   # 静态文件
│   ├── css/
│   │   ├── main.css          # 主样式
│   │   └── custom.css        # 自定义样式
│   ├── js/
│   │   ├── main.js           # 主脚本
│   │   ├── analysis.js       # 分析页脚本
│   │   ├── charts.js         # 图表脚本
│   │   └── api.js            # API调用脚本
│   └── img/                  # 图片资源
├── utils/                    # 工具函数
│   ├── __init__.py
│   ├── helpers.py            # 辅助函数
│   └── validators.py         # 数据验证
└── tests/                    # Web测试
    ├── test_api.py           # API测试
    └── test_routes.py        # 路由测试
```

---

## 六、API接口设计

### 6.1 分析相关API

```python
# 启动分析
POST /api/analyze
Request:
{
    "mode": "all" | "selected",
    "industries": ["航空机场", "生猪养殖"],  # mode=selected时必填
    "save_db": true,
    "generate_report": true
}
Response:
{
    "task_id": "abc123",
    "status": "running",
    "progress": 0
}

# 查询分析进度
GET /api/analyze/status?task_id=abc123
Response:
{
    "task_id": "abc123",
    "status": "running" | "completed" | "failed",
    "progress": 50,
    "current_industry": "生猪养殖",
    "total": 10,
    "completed": 5
}

# 获取分析结果
GET /api/analyze/result?task_id=abc123
Response:
{
    "task_id": "abc123",
    "results": [
        {
            "industry": "航空机场",
            "signal": "buy",
            "score": 85.0,
            "pe_percentile": 15.5,
            "pb_percentile": 18.2,
            ...
        }
    ]
}
```

### 6.2 历史记录API

```python
# 查询历史记录
GET /api/history?date=2024-01-15&industry=航空机场&signal=buy&limit=10
Response:
{
    "total": 50,
    "records": [
        {
            "id": 1,
            "run_date": "2024-01-15",
            "industry": "航空机场",
            "signal": "buy",
            "score_total": 85.0,
            ...
        }
    ]
}

# 查询记录详情
GET /api/history/<id>
Response:
{
    "id": 1,
    "run_date": "2024-01-15",
    "industry": "航空机场",
    "signal": "buy",
    "score_total": 85.0,
    "score_level": "A级",
    "divergence_type": "买点背离",
    "divergence_strength": 75.0,
    "risk_warnings": ["行业景气度较低"],
    "recommendation": "建议分批建仓",
    "raw_data": {...}
}
```

### 6.3 导出API

```python
# 生成导出文件
POST /api/export
Request:
{
    "format": "csv" | "excel" | "markdown",
    "filters": {
        "date": "2024-01-15",
        "industry": "航空机场",
        "signal": "buy"
    },
    "limit": 100
}
Response:
{
    "filename": "export_20240115_航空机场.csv",
    "download_url": "/api/export/download/export_20240115_航空机场.csv",
    "records_count": 10
}

# 下载文件
GET /api/export/download/<filename>
Response: 文件下载
```

### 6.4 统计数据API

```python
# 获取统计数据
GET /api/stats
Response:
{
    "total_records": 150,
    "buy_signals": 45,
    "sell_signals": 20,
    "hold_signals": 85,
    "avg_score": 62.5,
    "top_industries": [
        {"name": "生猪养殖", "avg_score": 85.0},
        {"name": "航空机场", "avg_score": 82.5}
    ],
    "last_update": "2024-01-15 10:30:00"
}
```

---

## 七、界面设计要点

### 7.1 首页（Dashboard）

**布局**:
```
┌─────────────────────────────────────────────────────────┐
│  逆向周期行业投资分析系统                    [分析] [历史] │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ 总记录数 │  │ 买入机会 │  │ 卖出预警 │  │ 平均评分 │ │
│  │   150    │  │    45    │  │    20    │  │   62.5   │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
│                                                           │
│  ┌─────────────────────────┐  ┌───────────────────────┐ │
│  │   信号分布饼图           │  │  最新分析结果表格     │ │
│  │                         │  │  行业 | 信号 | 评分   │ │
│  │                         │  │  ...                  │ │
│  └─────────────────────────┘  └───────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐│
│  │  快速操作                                            ││
│  │  [一键全量分析] [查看最新报告] [导出数据] [系统配置] ││
│  └─────────────────────────────────────────────────────┘│
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### 7.2 分析页面

**布局**:
```
┌─────────────────────────────────────────────────────────┐
│  行业投资机会分析                                         │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  分析模式:  ○ 全量分析  ● 指定行业                        │
│                                                           │
│  选择行业:                                                │
│  ☑ 航空机场  ☑ 生猪养殖  ☐ 基础化工  ☐ 煤炭             │
│  ☐ 有色金属  ☐ 远洋航运  ☐ 酒店旅游  ☐ 周期半导体       │
│  ☐ 光伏上游  ☐ 工程机械                                  │
│                                                           │
│  保存选项:                                                │
│  ☑ 保存到数据库  ☑ 生成Markdown报告                      │
│                                                           │
│  [开始分析]                                               │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐│
│  │  分析进度                                            ││
│  │  ████████████░░░░░░░░░░░░░░░░░░░░  60%              ││
│  │  正在分析: 生猪养殖 (已完成: 6/10)                   ││
│  └─────────────────────────────────────────────────────┘│
│                                                           │
│  ┌─────────────────────────────────────────────────────┐│
│  │  分析结果                                            ││
│  │  行业      | 信号 | 评分 | PE分位 | PB分位 | 建议   ││
│  │  航空机场  | buy  | 85.0 | 15.5%  | 18.2%  | 建仓   ││
│  │  生猪养殖  | buy  | 82.5 | 12.0%  | 15.0%  | 建仓   ││
│  └─────────────────────────────────────────────────────┘│
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### 7.3 历史记录页面

**布局**:
```
┌─────────────────────────────────────────────────────────┐
│  历史分析记录                                             │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  筛选条件:                                                │
│  日期范围: [2024-01-01] 至 [2024-01-31]                  │
│  行业:     [全部 ▼]                                      │
│  信号:     [全部 ▼]                                      │
│  [查询] [清空筛选]                                        │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐│
│  │  记录列表                                            ││
│  │  日期       | 行业     | 信号 | 评分 | 评级 | 操作   ││
│  │  2024-01-15 | 航空机场 | buy  | 85.0 | A级 | [详情] ││
│  │  2024-01-14 | 生猪养殖 | buy  | 82.5 | A级 | [详情] ││
│  │  ...                                                 ││
│  │                                                      ││
│  │  [上一页] 1 2 3 ... 10 [下一页]                     ││
│  └─────────────────────────────────────────────────────┘│
│                                                           │
│  ┌─────────────────────────────────────────────────────┐│
│  │  统计图表                                            ││
│  │  [评分趋势图] [信号分布图] [行业对比图]              ││
│  └─────────────────────────────────────────────────────┘│
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 八、技术实现要点

### 8.1 异步任务处理

由于行业分析可能耗时较长（10个行业约需5-10分钟），需要实现异步任务处理：

**方案一**: 后台线程（简单）
```python
from threading import Thread
import uuid

# 任务管理器
tasks = {}

def run_analysis_task(task_id, industries):
    # 执行分析
    tasks[task_id]['status'] = 'running'
    # ... 分析逻辑
    tasks[task_id]['status'] = 'completed'
    tasks[task_id]['results'] = results

# API路由
@app.route('/api/analyze', methods=['POST'])
def start_analyze():
    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'pending', 'progress': 0}
    
    # 启动后台线程
    thread = Thread(target=run_analysis_task, args=(task_id, industries))
    thread.start()
    
    return jsonify({'task_id': task_id})
```

**方案二**: Celery任务队列（推荐生产环境）
```python
from celery import Celery

celery = Celery('tasks', broker='redis://localhost:6379')

@celery.task
def analyze_industries(industries):
    # 执行分析
    return results
```

**推荐**: 开发阶段使用方案一，生产环境升级为方案二

### 8.2 数据缓存策略

为提高响应速度，实现数据缓存：

```python
from functools import lru_cache
from datetime import datetime, timedelta

# 内存缓存
cache_data = {}
cache_expire = {}

def get_cached_data(key, expire_minutes=30):
    if key in cache_data:
        if datetime.now() < cache_expire[key]:
            return cache_data[key]
    return None

def set_cached_data(key, data, expire_minutes=30):
    cache_data[key] = data
    cache_expire[key] = datetime.now() + timedelta(minutes=expire_minutes)
```

### 8.3 实时数据推送

使用Flask-SocketIO实现实时数据推送：

```python
from flask_socketio import SocketIO, emit

socketio = SocketIO(app)

@socketio.on('connect')
def handle_connect():
    emit('connected', {'data': 'Connected'})

# 分析进度推送
def update_progress(task_id, progress, industry):
    socketio.emit('progress_update', {
        'task_id': task_id,
        'progress': progress,
        'industry': industry
    })
```

---

## 九、依赖库清单

需要在 `requirements.txt` 中添加：

```python
# Web框架
Flask>=2.3.0
Flask-RESTful>=0.3.10
Flask-CORS>=4.0.0
Flask-SocketIO>=5.3.0  # 可选，用于实时推送

# 生产服务器
Waitress>=2.1.2  # Windows推荐
# Gunicorn>=21.2.0  # Linux推荐

# 数据可视化
Plotly>=5.15.0

# 异步任务（可选）
# Celery>=5.3.0
# Redis>=4.5.0  # Celery依赖

# API文档（可选）
Flask-Swagger>=0.2.14
Flask-APIDoc>=1.1.0
```

---

## 十、开发时间估算

| 阶段 | 工作量 | 预计时间 | 优先级 |
|------|--------|---------|--------|
| 阶段一：基础架构 | 小 | 1-2天 | P0 |
| 阶段二：API接口 | 中 | 2-3天 | P0 |
| 阶段三：前端页面 | 中 | 3-4天 | P0 |
| 阶段四：数据可视化 | 中 | 2-3天 | P1 |
| 阶段五：测试优化 | 小 | 1-2天 | P0 |
| **总计** | **中** | **9-14天** | - |

---

## 十一、部署方案

### 11.1 本地开发环境

```bash
# 启动开发服务器
python src/web/app.py

# 访问地址
http://localhost:5000
```

### 11.2 生产环境部署

**Windows服务器**:
```bash
# 使用Waitress
waitress-serve --port=5000 src.web.app:app
```

**Linux服务器**:
```bash
# 使用Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 src.web.app:app
```

**Docker部署**（可选）:
```dockerfile
FROM python:3.8
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "src.web.app:app"]
```

---

## 十二、风险与应对

| 风险 | 可能性 | 影响 | 应对措施 |
|------|--------|------|---------|
| 分析任务耗时过长 | 高 | 中 | 实现异步任务+进度显示 |
| 数据源连接失败 | 中 | 高 | 错误提示+重试机制 |
| 并发请求过多 | 低 | 中 | 任务队列+限流机制 |
| 浏览器兼容性 | 低 | 低 | 使用Bootstrap响应式设计 |
| 数据可视化性能 | 中 | 中 | 数据缓存+分页加载 |

---

## 十三、下一步行动

### 13.1 立即可开始的任务（P0）

1. **创建Web目录结构**
   - 创建 `src/web/` 目录
   - 创建子目录：routes, templates, static, utils

2. **安装依赖库**
   - 更新 `requirements.txt`
   - 执行 `pip install -r requirements.txt`

3. **Flask应用初始化**
   - 创建 `src/web/app.py`
   - 配置基础路由
   - 测试运行

4. **首页开发**
   - 创建 `templates/index.html`
   - 实现Dashboard基础功能
   - 集成现有数据查询

### 13.2 需要确认的事项

在开始开发前，需要确认：

1. **Web框架选择**: Flask 还是 FastAPI？
2. **异步任务方案**: 后台线程 还是 Celery？
3. **实时推送需求**: 是否需要实时进度显示？
4. **部署环境**: 本地开发 还是 生产服务器？
5. **用户认证**: 是否需要登录功能？
6. **界面风格**: Bootstrap传统风格 还是 Tailwind现代风格？

---

## 十四、总结

本Web界面开发计划覆盖了从基础架构到完整功能的所有开发阶段，预计需要9-14天完成。核心功能包括：

✅ **Dashboard首页** - 系统概览和快速操作
✅ **行业分析** - 全量/指定行业分析
✅ **历史记录** - 多维度查询和可视化
✅ **数据导出** - 多格式导出和下载
✅ **行业详情** - 详细数据和图表展示

技术栈选择：
- **后端**: Flask（轻量级、易集成）
- **前端**: Bootstrap 5（快速开发、响应式）
- **可视化**: Plotly（交互式图表）
- **异步**: 后台线程（开发阶段）

---

**建议开发顺序**:
1. 先完成基础架构和首页（快速看到效果）
2. 然后开发API接口（核心功能）
3. 再完善前端页面（用户体验）
4. 最后添加数据可视化（增强展示）

**是否按此计划开始开发？**