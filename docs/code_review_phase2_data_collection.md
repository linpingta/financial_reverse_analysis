# 代码审查报告：阶段二 - 数据采集模块

**项目：** 逆向周期行业投资分析系统  
**审查阶段：** 阶段二：数据采集模块  
**审查日期：** 2026-06-19  
**审查人：** Code Review

---

## 一、总体评价

| 维度 | 评分 | 说明 |
|------|------|------|
| 架构设计 | 3/5 | 模块划分清晰，采集器模式使用得当 |
| 代码质量 | 3/5 | 重试机制完善，日志充分，但存在逻辑缺陷 |
| 量化逻辑 | 2/5 | **存在阻断性量化方法错误** |
| 可维护性 | 4/5 | 配置化程度高，注释清晰 |

**关键风险：** 估值分位计算方法错误可能导致错误的投资信号。

---

## 二、严重问题 (阻断性)

### 问题 1：估值分位计算方法错误

**文件：** `src/data/industry_pe_pb_calculator.py`  
**行号：** 130-140  
**严重程度：** 🔴 高

**当前实现：**
```python
def calculate_percentile(self, sw_index_code: str, current_value: Optional[float] = None, field: str = 'close'):
    # ...
    percentile = (history_values < current_value).sum() / len(history_values) * 100
```

**问题描述：**
使用"点位分位"替代"估值(PE/PB)分位"作为估值判断依据，这在金融逻辑上是根本性错误。

**为什么是错的：**

| 指数点位 | 估值(PE) | 说明 |
|---------|---------|------|
| 3000点 | 10倍 | 历史低位估值 |
| 3000点 | 50倍 | 盈利崩溃时的高估值假象 |
| 6000点 | 15倍 | 合理估值 |
| 6000点 | 80倍 | 盈利高峰时的表面低价 |

**结论：** 点位高低与估值高低没有必然对应关系。

**影响：** 导致错误的买入/卖出信号，直接影响策略有效性。

**修复建议：**
1. 优先方案：使用 akshare 提供的历史 PE/PB 数据（需确认接口可用性）
2. 备选方案：使用 PB 分位替代点位分位（PB 比 PE 更稳定）
3. 兜底方案：明确标注为"近似估算"，添加偏差警告和置信区间

---

### 问题 2：price_trend 和 valuation_trend 调用相同逻辑

**文件：** `src/data/collector_factory.py`  
**行号：** 202-207  
**严重程度：** 🟡 中

**当前实现：**
```python
price_trend = self._calculator.get_trend(mapping.sw_index_code, window=12)
valuation_trend = self._calculator.get_trend(mapping.sw_index_code, window=12)
```

**问题描述：**
两次调用完全相同的 `get_trend()` 方法，返回相同的结果，`valuation_trend` 无实际意义。

**影响：** 背离信号检测基于错误数据。

---

## 三、中等问题

### 问题 3：硬编码列索引

**文件：** `src/data/collectors/baostock_collector.py`  
**行号：** 265-267  
**严重程度：** 🟡 中

**当前实现：**
```python
stocks = df[df.iloc[:, 2].str.contains(industry_code, na=False)][df.columns[1]].tolist()
```

**问题：** 使用 `iloc[:, 2]` 和 `df.columns[1]` 硬编码列位置，依赖列顺序，代码脆弱。

**修复建议：**
```python
if '行业分类' in df.columns and '股票代码' in df.columns:
    mask = df['行业分类'].str.contains(industry_code, na=False)
    stocks = df.loc[mask, '股票代码'].tolist()
```

---

### 问题 4：batch_get_profit 数据重复未去重

**文件：** `src/data/collectors/baostock_collector.py`  
**行号：** 282-299  
**严重程度：** 🟡 中

**当前实现：**
```python
results[code] = pd.concat([results[code], df], ignore_index=True)
```

**问题：** concat 保留重复记录，没有去重逻辑。

**修复建议：**
```python
results[code] = pd.concat([results[code], df], ignore_index=True).drop_duplicates()
```

---

### 问题 5：is_connected 行为不一致

**文件：** `src/data/collectors/base_collector.py`  
**行号：** 85-87  
**严重程度：** 🟢 低

**当前实现：**
```python
def is_connected(self) -> bool:
    """检查是否已连接"""
    raise NotImplementedError
```

**问题：** 基类方法抛出异常而非返回 False，调用方必须用 try/catch 处理。

**修复建议：** 改为 `return False` 或将方法声明为 `@abstractmethod`。

---

### 问题 6：宏观数据缓存无上限

**文件：** `src/data/collectors/macro_collector.py`  
**行号：** 43  
**严重程度：** 🟢 低

**当前实现：**
```python
self._cache: Dict[str, pd.DataFrame] = {}
```

**问题：** 实例级缓存随时间积累，无容量限制。

**修复建议：** 使用 `functools.lru_cache` 或添加容量限制。

---

## 四、轻微问题

| # | 文件 | 问题 | 建议 |
|---|------|------|------|
| 7 | akshare_collector.py | `_safe_float` 外层 `pd.notna()` 冗余 | 移除外部检查 |
| 8 | data_cache.py | DataFrame 序列化丢失 dtype 信息 | 保存列类型元数据 |
| 9 | industry_pe_pb_calculator.py | `pct_change(periods=window)` 语义不清 | 明确 window 单位 |

---

## 五、问题汇总表

| 严重程度 | 数量 | 关键问题 |
|---------|------|---------|
| 🔴 高 | 1 | 估值分位计算方法错误 |
| 🟡 中 | 3 | trend重复调用、硬编码列索引、重复数据 |
| 🟢 低 | 5 | 其他优化项 |

---

## 六、修复优先级

### P0 - 必须修复（阻断性）
1. 修正 `calculate_percentile()` 分位计算逻辑
2. 修复 `collect_industry()` 中重复的 trend 调用

### P1 - 建议修复
3. 修复 `get_stocks_by_industry()` 硬编码列索引
4. 修复 `is_connected()` 异常行为
5. 优化 `batch_get_profit()` 去重逻辑

### P2 - 可选优化
6. 清理冗余检查
7. 添加缓存容量限制

---

## 七、代码亮点

- ✅ 重试机制完善（可配置次数和间隔）
- ✅ 内存+文件双层缓存，TTL 机制合理
- ✅ 日志记录充分（使用 loguru）
- ✅ 配置文件支持 + 默认映射 fallback
- ✅ 采集器模式统一接口

---

## 八、后续建议

1. **验证 akshare 接口可用性**：`sw_index_daily` 据反馈当前不可用，需确认
2. **补充单元测试**：关键计算方法缺乏测试覆盖
3. **添加数据质量检查**：获取数据后应验证字段完整性和数值合理性
