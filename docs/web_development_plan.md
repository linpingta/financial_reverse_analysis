# Web界面开发计划

## 一、项目概述

为逆向周期行业投资分析系统开发Web界面，让用户通过浏览器快速访问所有功能。

### 技术栈确认

| 技术项 | 选择 | 说明 |
|--------|------|------|
| Web框架 | Flask | 轻量级、易集成 |
| 异步方案 | 后台线程 | 简单实现，开发阶段适用 |
| 实时推送 | Flask-SocketIO | WebSocket支持，实时进度显示 |
| 用户认证 | 无 | 不需要登录功能 |
| 前端风格 | Tailwind CSS | 现代化UI设计 |

---

## 二、开发阶段总览

```
阶段一：基础架构搭建（预计工作量：小）
阶段二：API接口开发（预计工作量：中）
阶段三：前端页面开发（预计工作量：中）
阶段四：数据可视化（预计工作量：中）
阶段五：集成测试与优化（预计工作量：小）
```

---

## 三、详细开发计划

### 阶段一：基础架构搭建

| 序号 | 任务 | 说明 | 优先级 |
|------|------|------|--------|
| 1.1 | 创建Web目录结构 | `src/web/` 及子目录 | P0 |
| 1.2 | Flask应用初始化 | `app.py` 主应用 | P0 |
| 1.3 | 配置文件扩展 | Web配置参数 | P0 |
| 1.4 | 依赖库安装 | Flask、Flask-SocketIO、Tailwind | P0 |
| 1.5 | SocketIO集成 | WebSocket支持 | P0 |
| 1.6 | 基础路由框架 | 主路由和API路由 | P0 |

**产出**：
- Flask应用骨架
- 目录结构完整
- WebSocket支持
- 基础路由框架

---

### 阶段二：API接口开发

| 序号 | 任务 | API路径 | 优先级 |
|------|------|---------|--------|
| 2.1 | 分析启动接口 | `POST /api/analyze` | P0 |
| 2.2 | 分析进度接口 | `GET /api/analyze/status` | P0 |
| 2.3 | 分析结果接口 | `GET /api/analyze/result` | P0 |
| 2.4 | 历史查询接口 | `GET /api/history` | P0 |
| 2.5 | 历史详情接口 | `GET /api/history/<id>` | P0 |
| 2.6 | 导出生成接口 | `POST /api/export` | P0 |
| 2.7 | 文件下载接口 | `GET /api/export/download/<filename>` | P0 |
| 2.8 | 统计数据接口 | `GET /api/stats` | P1 |
| 2.9 | 行业详情接口 | `GET /api/industry/<name>` | P1 |
| 2.10 | 系统状态接口 | `GET /api/system` | P1 |
| 2.11 | 行业列表接口 | `GET /api/industries` | P0 |

**产出**：
- 完整的RESTful API
- 异步任务管理
- 实时进度推送

---

### 阶段三：前端页面开发

#### 3.1 基础组件

| 序号 | 任务 | 文件 | 优先级 |
|------|------|------|--------|
| 3.1.1 | 基础模板 | `base.html` | P0 |
| 3.1.2 | 导航栏组件 | 导航栏 | P0 |
| 3.1.3 | Tailwind配置 | Tailwind CSS | P0 |
| 3.1.4 | API调用模块 | `api.js` | P0 |
| 3.1.5 | WebSocket连接 | Socket.IO客户端 | P0 |

#### 3.2 页面开发

| 序号 | 任务 | 页面 | 优先级 |
|------|------|------|--------|
| 3.2.1 | Dashboard首页 | `index.html` | P0 |
| 3.2.2 | 行业分析页 | `analysis.html` | P0 |
| 3.2.3 | 历史记录页 | `history.html` | P0 |
| 3.2.4 | 数据导出页 | `export.html` | P1 |
| 3.2.5 | 行业详情页 | `industry_detail.html` | P1 |
| 3.2.6 | 系统配置页 | `settings.html` | P2 |

**产出**：
- 完整的前端页面
- Tailwind现代UI
- 响应式布局
- WebSocket实时通信

---

### 阶段四：数据可视化

| 序号 | 任务 | 图表类型 | 优先级 |
|------|------|----------|--------|
| 4.1 | 信号统计饼图 | Plotly Pie Chart | P0 |
| 4.2 | 评分分布图 | Plotly Scatter | P0 |
| 4.3 | 分位数趋势图 | Plotly Line Chart | P0 |
| 4.4 | 行业对比柱状图 | Plotly Bar Chart | P0 |
| 4.5 | 背离分析组合图 | Plotly Mixed Chart | P1 |
| 4.6 | 历史走势面积图 | Plotly Area Chart | P1 |

**产出**：
- 交互式图表组件
- 数据可视化模块
- 图表配置选项

---

### 阶段五：集成测试与优化

| 序号 | 任务 | 说明 | 优先级 |
|------|------|------|--------|
| 5.1 | API测试 | 所有接口功能测试 | P0 |
| 5.2 | 页面功能测试 | 所有页面交互测试 | P0 |
| 5.3 | WebSocket测试 | 实时推送测试 | P0 |
| 5.4 | 性能优化 | 响应速度优化 | P1 |
| 5.5 | 错误处理完善 | 异常处理机制 | P0 |
| 5.6 | UI细节优化 | Tailwind样式调整 | P1 |
| 5.7 | 浏览器兼容性测试 | Chrome/Edge/Firefox | P1 |
| 5.8 | 使用文档编写 | Web界面使用指南 | P1 |

**产出**：
- 测试通过的完整系统
- 用户使用文档
- 性能优化完成

---

## 四、文件结构

```
src/web/
├── __init__.py
├── app.py                    # Flask主应用 + SocketIO
├── config.py                 # Web配置
├── routes/                   # 路由模块
│   ├── __init__.py
│   ├── main.py               # 主页面路由
│   ├── api.py                # API路由
│   └── industry.py           # 行业相关路由
├── templates/                # HTML模板
│   ├── base.html             # 基础模板（Tailwind）
│   ├── index.html            # 首页
│   ├── analysis.html         # 分析页
│   ├── history.html          # 历史页
│   ├── export.html           # 导出页
│   ├── industry_detail.html  # 行业详情页
│   └── settings.html         # 配置页
├── static/                   # 静态文件
│   ├── css/
│   │   └── custom.css        # 自定义Tailwind样式
│   ├── js/
│   │   ├── main.js           # 主脚本
│   │   ├── api.js            # API调用
│   │   ├── socket.js         # WebSocket连接
│   │   ├── charts.js         # 图表脚本
│   │   └── analysis.js       # 分析页脚本
│   └── img/                  # 图片资源
├── utils/                    # 工具函数
│   ├── __init__.py
│   ├── task_manager.py       # 异步任务管理
│   ├── helpers.py            # 辅助函数
│   └── validators.py         # 数据验证
└── tests/                    # Web测试
    ├── test_api.py           # API测试
    └── test_routes.py        # 路由测试
```

---

## 五、核心功能设计

### 5.1 Dashboard首页

**功能模块**：
- 系统状态卡片（总记录数、买入机会、卖出预警、平均评分）
- 信号分布饼图（买入/卖出/持有比例）
- 最新分析结果表格（最近10条）
- 快速操作按钮（一键分析、查看报告、导出数据）
- 行业评分排行（Top 5机会行业）

**数据来源**：
- `ResultDB.query_latest(10)`
- `ResultDB.get_statistics()`
- 系统配置信息

### 5.2 行业分析页

**功能模块**：
- 分析模式选择（全量/指定行业）
- 行业选择器（多选框）
- 保存选项（数据库/报告）
- 实时进度条（WebSocket推送）
- 结果实时更新表格
- 分析状态显示

**异步任务流程**：
1. 用户提交分析请求
2. 后台线程启动分析任务
3. WebSocket实时推送进度
4. 分析完成后推送结果

### 5.3 历史记录页

**功能模块**：
- 多维度筛选（日期、行业、信号）
- 分页表格展示
- 详情弹窗查看
- 数据可视化（趋势图）
- 批量导出选择

### 5.4 数据导出页

**功能模块**：
- 导出格式选择（CSV/Excel/Markdown）
- 筛选条件设置
- 数据预览表格
- 文件下载
- 导出历史记录

### 5.5 行业详情页

**功能模块**：
- 行业历史走势图（价格、PE、PB）
- 分位数趋势图（10年历史）
- 背离分析可视化
- 关键指标对比
- 操作建议详情

---

## 六、API接口设计

### 6.1 分析相关API

```python
# 启动分析
POST /api/analyze
Request:
{
    "mode": "all" | "selected",
    "industries": ["航空机场", "生猪养殖"],
    "save_db": true,
    "generate_report": true
}
Response:
{
    "task_id": "abc123",
    "status": "pending"
}

# 查询分析进度（WebSocket推送）
WebSocket Event: progress_update
Data:
{
    "task_id": "abc123",
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
    "status": "completed",
    "results": [...]
}
```

### 6.2 历史记录API

```python
# 查询历史记录
GET /api/history?date=2024-01-15&industry=航空机场&signal=buy&page=1&limit=10
Response:
{
    "total": 50,
    "page": 1,
    "records": [...]
}

# 查询记录详情
GET /api/history/<id>
Response:
{
    "id": 1,
    "run_date": "2024-01-15",
    "industry": "航空机场",
    ...
}
```

### 6.3 导出API

```python
# 生成导出文件
POST /api/export
Request:
{
    "format": "csv" | "excel" | "markdown",
    "filters": {...}
}
Response:
{
    "filename": "export_20240115.csv",
    "download_url": "/api/export/download/export_20240115.csv"
}

# 下载文件
GET /api/export/download/<filename>
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
    "top_industries": [...]
}
```

---

## 七、异步任务管理

### 7.1 任务管理器设计

```python
# src/web/utils/task_manager.py

import uuid
from threading import Thread
from datetime import datetime

class TaskManager:
    """异步任务管理器"""
    
    def __init__(self):
        self.tasks = {}  # task_id -> task_info
        
    def create_task(self, func, *args, **kwargs):
        """创建异步任务"""
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {
            'status': 'pending',
            'progress': 0,
            'start_time': datetime.now(),
            'result': None
        }
        
        # 启动后台线程
        thread = Thread(target=self._run_task, args=(task_id, func, args, kwargs))
        thread.daemon = True
        thread.start()
        
        return task_id
    
    def _run_task(self, task_id, func, args, kwargs):
        """执行任务"""
        self.tasks[task_id]['status'] = 'running'
        try:
            result = func(*args, **kwargs)
            self.tasks[task_id]['status'] = 'completed'
            self.tasks[task_id]['result'] = result
        except Exception as e:
            self.tasks[task_id]['status'] = 'failed'
            self.tasks[task_id]['error'] = str(e)
    
    def get_task_status(self, task_id):
        """查询任务状态"""
        return self.tasks.get(task_id)
    
    def update_progress(self, task_id, progress, message=None):
        """更新任务进度"""
        if task_id in self.tasks:
            self.tasks[task_id]['progress'] = progress
            if message:
                self.tasks[task_id]['message'] = message
```

### 7.2 WebSocket实时推送

```python
# src/web/app.py

from flask_socketio import SocketIO, emit

socketio = SocketIO(app)

# WebSocket连接事件
@socketio.on('connect')
def handle_connect():
    emit('connected', {'data': 'Connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# 进度推送函数
def push_progress(task_id, progress, industry):
    socketio.emit('progress_update', {
        'task_id': task_id,
        'progress': progress,
        'current_industry': industry
    })
```

---

## 八、依赖库清单

需要在 `requirements.txt` 中添加：

```python
# Web框架
Flask>=2.3.0
Flask-SocketIO>=5.3.0

# 生产服务器
Waitress>=2.1.2

# 数据可视化
Plotly>=5.15.0

# Tailwind CSS（通过CDN引入，无需安装）
```

---

## 九、开发时间估算

| 阶段 | 工作量 | 预计时间 | 优先级 |
|------|--------|---------|--------|
| 阶段一：基础架构 | 小 | 1-2天 | P0 |
| 阶段二：API接口 | 中 | 2-3天 | P0 |
| 阶段三：前端页面 | 中 | 3-4天 | P0 |
| 阶段四：数据可视化 | 中 | 2-3天 | P1 |
| 阶段五：测试优化 | 小 | 1-2天 | P0 |
| **总计** | **中** | **9-14天** | - |

---

## 十、优先级排序（P0 = 必须先行）

```
P0 任务（阻塞其他任务）:
├── 1.1 Web目录结构
├── 1.2 Flask应用初始化
├── 1.4 依赖库安装
├── 1.5 SocketIO集成
├── 2.1 分析启动接口
├── 2.2 分析进度接口
├── 2.4 历史查询接口
├── 2.6 导出生成接口
├── 3.1.1 基础模板
├── 3.1.4 API调用模块
├── 3.1.5 WebSocket连接
├── 3.2.1 Dashboard首页
├── 3.2.2 行业分析页
├── 3.2.3 历史记录页
└── 5.1 API测试

P1 任务（核心功能）:
├── 2.8 统计数据接口
├── 2.9 行业详情接口
├── 3.2.4 数据导出页
├── 3.2.5 行业详情页
├── 4.1-4.4 数据可视化
├── 5.4 性能优化
└── 5.8 使用文档

P2 任务（增强功能）:
├── 3.2.6 系统配置页
├── 4.5-4.6 高级图表
└── 5.6 UI细节优化
```

---

## 十一、第一个可运行版本（MVP）检查清单

目标：能够通过浏览器访问系统并执行基本分析

**MVP 必须包含**：
- [ ] Flask应用运行正常
- [ ] WebSocket连接正常
- [ ] Dashboard首页显示
- [ ] 行业分析功能正常
- [ ] 实时进度显示正常
- [ ] 历史记录查询正常
- [ ] 至少一个行业分析成功

**MVP 不包含**：
- 数据导出页（可后续补充）
- 行业详情页（可后续补充）
- 系统配置页（可后续补充）
- 高级图表（可后续补充）

---

## 十二、风险点与应对

| 风险 | 可能性 | 影响 | 应对措施 |
|------|--------|------|---------|
| 分析任务耗时过长 | 高 | 中 | 异步任务+实时进度显示 |
| WebSocket连接不稳定 | 中 | 中 | 自动重连机制 |
| 数据源连接失败 | 中 | 高 | 错误提示+重试机制 |
| 浏览器兼容性 | 低 | 低 | Tailwind响应式设计 |
| 并发请求过多 | 低 | 中 | 任务队列+限流 |

---

## 十三、部署方案

### 13.1 本地开发环境

```bash
# 启动开发服务器（支持WebSocket）
python src/web/app.py

# 访问地址
http://localhost:5000
```

### 13.2 生产环境部署

**Windows服务器**：
```bash
# 使用Waitress（支持WebSocket）
waitress-serve --port=5000 src.web.app:app
```

---

## 十四、待确认事项

在开发前需确认：

| 序号 | 问题 | 状态 |
|------|------|------|
| 1 | Web框架选择 | ✅ 已确认：Flask |
| 2 | 异步任务方案 | ✅ 已确认：后台线程 |
| 3 | 实时推送需求 | ✅ 已确认：支持WebSocket |
| 4 | 用户认证需求 | ✅ 已确认：不需要 |
| 5 | 前端风格 | ✅ 已确认：Tailwind CSS |
| 6 | 是否按此计划开始开发？ | ⏸️ 待确认 |

---

## 十五、下一步行动

### 立即可开始的任务（P0）

1. **创建Web目录结构**
   ```bash
   mkdir src/web
   mkdir src/web/routes
   mkdir src/web/templates
   mkdir src/web/static
   mkdir src/web/static/css
   mkdir src/web/static/js
   mkdir src/web/static/img
   mkdir src/web/utils
   mkdir src/web/tests
   ```

2. **更新依赖库**
   - 在 `requirements.txt` 添加Flask、Flask-SocketIO、Plotly
   - 执行 `pip install -r requirements.txt`

3. **Flask应用初始化**
   - 创建 `src/web/app.py`
   - 配置SocketIO
   - 测试运行

---

**建议开发顺序**：
1. 先完成基础架构和首页（快速看到效果）
2. 然后开发API接口（核心功能）
3. 再完善前端页面（用户体验）
4. 最后添加数据可视化（增强展示）

**是否按此计划开始开发？**