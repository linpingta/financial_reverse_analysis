# phase-gate.py 使用说明

`phase-gate.py` 是 `phase-gated-dev` skill 的状态机脚本，负责：

1. **解析开发计划文档**：从 markdown 中识别出所有 phase
2. **持久化状态**：写到 `.state/state.json`，跨会话保留
3. **强制阶段顺序**：phase N-1 不通过就不让开 phase N
4. **记录历史**：所有操作写到 `.state/history.log`

## 安装

无需安装。仅依赖 Python 3.7+（仅使用了标准库）。

## 命令清单

| 命令 | 作用 |
|------|------|
| `init <plan_path>` | 从计划文档解析出 phases，初始化状态 |
| `status` | 显示当前 phase 进度状态 |
| `start <N>` | 开始 phase N（自动校验前置 phase 已通过） |
| `review <N> --pass` | 标记 phase N review 通过 |
| `review <N> --issues "..."` | 标记 phase N review 发现问题（分号分隔多个） |
| `reset <N>` | 重置 phase N 状态（重新开发） |
| `skip <N>` | 跳过 phase N |
| `list` | 列出所有 phases 的当前状态 |

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 一般错误（参数错误、解析失败等） |
| 2 | **被硬卡点拒绝**（如：phase N-1 未通过就 start phase N） |

AI 可以根据退出码决定下一步行为。

## 状态文件位置

默认在 `<skill 目录>/.state/`：

```
<skill 目录>/
└── .state/
    ├── state.json   # 当前所有 phase 的状态
    └── history.log  # 操作历史（JSONL 格式）
```

可以用 `--skill-dir` 参数指定其他位置：

```bash
python phase-gate.py --skill-dir /path/to/skill status
```

## state.json 结构

```json
{
  "plan_file": "绝对路径/development_plan_v1.0.md",
  "created_at": "2026-06-27T15:43:52",
  "phases": [
    {
      "num": 1,
      "title": "基础设施搭建",
      "status": "pending | in_progress | completed | skipped",
      "started_at": "2026-06-27T15:43:58",
      "completed_at": null,
      "review_rounds": 1,
      "last_review_issues": ["问题1", "问题2"]
    }
  ]
}
```

## 使用示例

### 第一次使用

```bash
# 1. 初始化（解析计划文档）
python scripts/phase-gate.py init ./development_plan_v1.0.md

# 输出:
# ✅ 已从 development_plan_v1.0.md 解析出 6 个 phase:
#    1. 基础设施搭建
#    2. 数据采集模块开发
#    ...

# 2. 查看状态
python scripts/phase-gate.py status

# 3. 开始 phase 1
python scripts/phase-gate.py start 1

# 4. AI 完成开发后，标记 review 通过
python scripts/phase-gate.py review 1 --pass

# 5. 开始下一 phase
python scripts/phase-gate.py start 2
```

### review 发现问题需要修复

```bash
# 标记 review 发现 2 个问题
python scripts/phase-gate.py review 1 --issues "config 模块缺单元测试;日志路径不存在"

# AI 根据 issues 修复 → 自动重新 review → 再次调用 review --pass 或 --issues

# 修复 5 轮还没通过 → 脚本会提示停下让用户决策
```

### 重做已通过的 phase

```bash
# 重置 phase 3，重新开发
python scripts/phase-gate.py reset 3

# 重新启动
python scripts/phase-gate.py start 3
```

### 跳过 phase

```bash
# 跳过 phase 4（标记为已跳过，不影响后续 phase 启动）
python scripts/phase-gate.py skip 4
```

## 在 Trae / AI 工作流中的调用方式

AI 助手应该这样调用（用相对路径，从 skill 目录运行）：

```bash
cd <skill 目录>
python scripts/phase-gate.py status
python scripts/phase-gate.py start 1
python scripts/phase-gate.py review 1 --pass
```

**重要**：
- AI 在每次"开始新动作"前必须先调 `status` 确认当前状态
- AI 严禁自己编辑 `.state/state.json`（用户会从 history.log 发现越权）
- AI 严禁跳过 `phase-gate.py` 直接开发（脚本是唯一的 state-changer）

## 测试用例

```bash
# 测试 1：基本流程
python scripts/phase-gate.py init /path/to/test_plan.md
python scripts/phase-gate.py start 1
python scripts/phase-gate.py start 2          # 应该被拒绝（exit 2）
python scripts/phase-gate.py review 1 --pass
python scripts/phase-gate.py start 2          # 现在可以通过

# 测试 2：reset
python scripts/phase-gate.py reset 1
python scripts/phase-gate.py status           # 应该看到 phase 1 回到 pending

# 测试 3：skip
python scripts/phase-gate.py skip 3           # 跳过 phase 3
python scripts/phase-gate.py start 4          # phase 4 可以直接开始（跳过 phase 3 不阻塞）
```