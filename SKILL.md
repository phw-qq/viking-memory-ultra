---
name: viking-memory-ultra
description: Viking Memory System Ultra - 生产级AI记忆系统（Python实现）。特性：JSON结构化事实层、双时间戳、Agentic三元组（Ledger+View+Policy）、元认知触发、过程性记忆压缩、动态回流、智能权重、可逆归档、Ebbinghaus复习调度。核心脚本：sv_fact, sv_write, sv_read, sv_ledger, sv_view, sv_policy, sv_metacognitive, sv_compress, sv_autoload, sv_promote, sv_weight, sv_review。
version: 1.5.0
---

# Viking Memory System Ultra - SKILL.md

> ✅ **Python 实现**（所有脚本为 `.py`，位于 `scripts/` 目录）
> 
> 版本：v1.5（Python 重写，添加生产级AI记忆功能）
> 更新日期：2026-05-15
> 这是 Viking 记忆系统的核心使用规范，所有 Agent 必须遵循
> 
> **New in v1.5**: 生产级AI记忆系统功能（基于视频"构建生产级AI记忆"）

---

## 🏠 系统概述

Viking 是我们的分层记忆基座，解决"记忆太多无法高效检索"的根本矛盾。

```
viking-L0-hot   →  viking-L1-warm   →  viking-L2-cold   →  viking-L4-archive
   (热记忆，0-7天)     (温记忆，8-29天)    (冷记忆，30-89天)   (归档，90天+)
```

> 每层记忆的保留策略不同：热层完整保留、温层压缩要点、冷层极简索引、归档层多粒度摘要。
> 重要记忆（`important: true`）永不自动压缩。

---

## 🏗 生产级AI记忆功能 (v1.5)

> 基于视频"构建生产级AI记忆"实现的核心功能，填补OpenViking与原视频系统的差距。

### 新增功能概览

| 功能 | 脚本 | 状态 | 说明 |
|------|------|------|------|
| JSON结构化事实层 | `sv_fact.py` | ✅ | 精确存储/检索事实（非模糊向量检索） |
| 双时间戳系统 | `sv_write.py`, `sv_read.py` | ✅ | `event_time` + `insert_time` |
| Ledger账本层 | `sv_ledger.py` | ✅ | 记录所有操作，支持回滚审计 |
| View视图层 | `sv_view.py` | ✅ | 动态视图（时间/重要性/相关性/复习） |
| Policy策略层 | `sv_policy.py` | ✅ | 智能策略引擎（时间/重要性/上下文/自适应） |
| 元认知触发 | `sv_metacognitive.py` | ✅ | System 2深度思考触发器 |
| 过程性记忆压缩 | `sv_compress.py` | ✅ | 成功路径→可触发技能 |

---

### JSON 结构化事实层 (sv_fact.py)

> **解决问题**：向量检索是模糊的，生产级系统需要精确的事实存储和检索。

#### 使用方法

```bash
# 添加事实（自动生成ID和双时间戳）
python sv_fact.py add '{"type":"decision","content":"选择Python而非Node.js","source":"user"}' --event_time "2026-05-10T14:30:00+08:00"

# 查询事实（精确匹配，非模糊检索）
python sv_fact.py query '{"type":"decision"}' --limit 5

# 更新事实
python sv_fact.py update "fact_20260515_031740" '{"content":"更新后的内容"}'

# 删除事实
python sv_fact.py delete "fact_20260515_031740"

# 列出所有事实
python sv_fact.py list --type decision --limit 20
```

#### 事实文件结构

```json
{
  "id": "fact_20260515_031740",
  "type": "decision",
  "content": "选择Python而非Node.js",
  "source": "user",
  "event_time": "2026-05-10T14:30:00+08:00",
  "insert_time": "2026-05-15T03:17:40.369701+08:00",
  "last_access": "2026-05-15T03:17:40.369701+08:00",
  "access_count": 1
}
```

#### 存储位置

```
~/.workbuddy/memory/facts/
├── decision_fact_20260515_031740.json
├── task_fact_20260515_031841.json
└── ...
```

---

### 双时间戳系统

> **解决问题**：区分"事件发生时"和"记忆插入时"，避免时间混乱。

#### event_time vs insert_time

| 字段 | 说明 | 示例 |
|------|------|------|
| `event_time` | 事件发生时间 | `2026-05-10T14:30:00+08:00` |
| `insert_time` | 记忆插入时间 | `2026-05-15T03:17:40+08:00` |

#### 使用方法

```bash
# 写入记忆时指定事件发生时间
python sv_write.py <file> "内容" --event_time "2026-05-10T14:30:00+08:00"

# 读取时显示双时间戳
python sv_read.py <file> --update-access
# 输出：
#   Event Time: 2026-05-10T14:30:00+08:00
#   Insert Time: 2026-05-15T03:17:40+08:00
```

#### 迁移旧记忆

如果旧记忆只有 `created` 字段，系统会自动将其作为 `event_time`。

---

### Agentic 记忆三元组

> **核心概念**：生产级AI记忆 = Ledger（账本） + View（视图） + Policy（策略）

#### 1. Ledger 账本层 (sv_ledger.py)

> 记录所有记忆操作，支持审计和回滚。

##### 使用方法

```bash
# 记录操作
python sv_ledger.py log "add" "/path/to/file.md" --meta '{"importance":"high"}'

# 审计操作
python sv_ledger.py audit --operation add --limit 20

# 查看统计
python sv_ledger.py stats

# 回滚操作（谨慎使用）
python sv_ledger.py rollback "txn_20260515_032025"
```

##### 账本文件结构

```
~/.workbuddy/memory/facts/ledger/
├── ledger_2026-05-15.json
├── ledger_2026-05-14.json
└── ...
```

每个账本文件包含当天的所有操作记录：

```json
[
  {
    "transaction_id": "txn_20260515_032025",
    "timestamp": "2026-05-15T03:20:25+08:00",
    "operation": "add",
    "file_path": "/path/to/file.md",
    "meta": {"test": "data"}
  },
  ...
]
```

---

#### 2. View 视图层 (sv_view.py)

> 基于上下文的动态记忆视图。

##### 使用方法

```bash
# 按时间视图（默认）
python sv_view.py <memories_dir> --view time

# 按重要性视图
python sv_view.py <memories_dir> --view importance

# 按相关性视图（需要 --context）
python sv_view.py <memories_dir> --view relevance --context "OpenViking集成测试"

# 按复习状态视图
python sv_view.py <memories_dir> --view review

# 比较两个记忆
python sv_view.py <memories_dir> --compare file1.md file2.md

# 显示统计
python sv_view.py <memories_dir> --stats
```

##### 视图模式说明

| 视图模式 | 说明 | 使用场景 |
|---------|------|---------|
| `time` | 按 `event_time` 排序 | 查看最近/最早的记忆 |
| `importance` | 按重要性+权重排序 | 优先查看重要记忆 |
| `relevance` | 按上下文相关性排序 | 当前任务相关的记忆 |
| `review` | 按复习状态分组 | 管理Ebbinghaus复习 |

---

#### 3. Policy 策略层 (sv_policy.py)

> 智能策略引擎，决定何时读/写/忘/提升记忆。

##### 使用方法

```bash
# 应用策略（预览）
python sv_policy.py <memories_dir> --policy adaptive --context "当前任务" --dry-run

# 应用策略（实际执行）
python sv_policy.py <memories_dir> --policy adaptive --context "当前任务"

# 决策单个记忆的操作
python sv_policy.py <memories_dir> --decide add "/path/to/file.md" --context "当前任务"

# 配置策略参数
python sv_policy.py <memories_dir> --configure adaptive '{"threshold":0.7}'

# 列出所有配置的策
python sv_policy.py <memories_dir> --list-policies
```

##### 策略类型

| 策略 | 说明 | 决策依据 |
|------|------|---------|
| `time` | 基于时间 | 记忆年龄 + 最后访问时间 |
| `importance` | 基于重要性 | `important`(365天) > `high`(180天) > `medium`(90天) > `low`(30天) |
| `context` | 基于上下文 | 相关性 ≥0.7 提升, ≥0.3 保持, <0.3 时间策略 |
| `adaptive` | 自适应（推荐） | 综合重要性、年龄、访问频率、上下文相关性 |

##### 决策结果

| 动作 | 说明 |
|------|------|
| `keep` | 保持当前层级 |
| `promote` | 提升层级（如 cold → hot） |
| `archive` | 归档 |
| `delete` | 删除（仅 `low` 重要性且超期） |

---

### 元认知触发机制 (sv_metacognitive.py)

> **解决问题**：遇到复杂问题时自动激活System 2深度思考。

#### 使用方法

```bash
# 分析任务复杂度
python sv_metacognitive.py analyze "设计一个复杂的多层AI记忆系统架构"

# 触发System 2深度思考
python sv_metacognitive.py trigger "分析OpenViking与生产级系统的差距" --threshold 0.6

# 查看元认知系统状态
python sv_metacognitive.py status

# 配置元认知参数
python sv_metacognitive.py config '{"threshold":0.7,"auto_trigger":true}'
```

#### 复杂度评分

| 分数范围 | 级别 | 推荐 |
|---------|------|------|
| 0.7 - 1.0 | HIGH | 触发System 2深度思考 |
| 0.4 - 0.69 | MEDIUM | 使用标准思考 |
| 0.0 - 0.39 | LOW | 使用快速响应 |

#### 复杂度指标

**复杂指标**（增加分数）：
- 英文：analyze, complex, design, optimize, refactor, debug, investigate, ...
- 中文：分析, 复杂, 设计, 优化, 重构, 调试, 调查, ...

**简单指标**（降低分数）：
- 英文：create, add, update, list, show, simple, quick, ...
- 中文：创建, 添加, 更新, 列出, 显示, 简单, 快速, ...

---

### 过程性记忆压缩 (sv_compress.py)

> **解决问题**：将成功路径压缩成可触发的技能（skills），实现"从经验中学习"。

#### 使用方法

```bash
# 找出所有成功的任务记忆
python sv_compress.py <memories_dir> --task-description "OpenViking集成"

# 从记忆中提取步骤
python sv_compress.py <memories_dir> --extract "mem_20260515_033427"

# 压缩为可复用的技能
python sv_compress.py <memories_dir> --compress "mem_20260515_033427" --output "openviking-integration"

# 列出所有已压缩的技能
python sv_compress.py <memories_dir> --list
```

#### 压缩流程

1. **识别成功任务** - 扫描记忆，找出包含成功指标（✅, completed, 实现, 修复）的记忆
2. **提取步骤** - 从记忆正文中提取编号步骤（1. 2. 3. 或 - * 列表）
3. **压缩为技能** - 生成标准技能目录结构（SKILL.md + _meta.json）
4. **保存记录** - 保存压缩记录到 `compressed/` 目录

#### 生成的技能结构

```
~/.workbuddy/skills/openviking-integration/
├── SKILL.md        # 包含提取的步骤
└── _meta.json      # 元数据（源任务ID、压缩时间等）
```

#### 压缩记录

```json
{
  "task_id": "mem_20260515_033427",
  "skill_name": "openviking-integration",
  "skill_path": "/path/to/skill",
  "compressed_at": "2026-05-15T03:35:20+08:00",
  "procedure": {
    "task_title": "成功的任务示例（含步骤）",
    "steps": [...],
    "tags": ["测试", "成功", "步骤"]
  }
}
```

---

## 📁 目录结构（Python 实现）

Viking 记忆位于 `~/.workbuddy/memory/`（Windows：`C:\Users\<user>\.workbuddy\memory\`）：

```
~/.workbuddy/memory/
├── viking-L0-hot/      # L0: 热记忆，完整细节（0-7天）
├── viking-L1-warm/     # L1: 温记忆，压缩要点（8-29天）
├── viking-L2-cold/     # L2: 冷记忆，极简索引（30-89天）
├── viking-L4-archive/  # L4: 长期归档（90天+）
├── MEMORY.md           # 长期记忆（手动维护）
└── YYYY-MM-DD.md      # 每日工作笔记
```

**层级迁移规则：**

| 文件年龄 | 自动迁移至 |
|---------|---------|
| 0-7天   | viking-L0-hot/ (L0) |
| 8-29天  | viking-L1-warm/ (L1) |
| 30-89天 | viking-L2-cold/ (L2) |
| 90天+   | viking-L4-archive/ (L4) |

> **重要**：`important: true` 或 `importance: important` 的记忆永不自动压缩。

---

## 🔧 核心命令（Python 脚本）

所有脚本位于 `scripts/` 目录，用 `python sv_xxx.py` 调用。

### 写入记忆（sv_write.py）

```bash
# 基本写入 → L0-hot 层（自动计算层级）
python sv_write.py <memories_dir> "标题" "正文内容"

# 指定重要性（high/medium/low/important）
python sv_write.py <memories_dir> "标题" "内容" --importance high

# important = 永不自动压缩
python sv_write.py <memories_dir> "标题" "内容" --importance important
```

### 读取记忆（sv_read.py）

```bash
# 读取指定记忆文件
python sv_read.py <memories_dir> <filename>

# 示例
python sv_read.py C:\Users\13978\.workbuddy\memory viking-L2-cold/mem-demo-migration.md
```

### 搜索记忆（sv_find.py）

```bash
# 按关键词搜索
python sv_find.py --dir <memories_dir> --keyword "关键词"

# 按标签过滤
python sv_find.py --dir <memories_dir> --tags "演示,迁移"

# 按复习状态过滤
python sv_find.py --dir <memories_dir> --review-status pending_review --limit 20
```

---

## 📝 Frontmatter 规范（必须遵循）

所有写入 Viking 的记忆必须包含标准 frontmatter：

```markdown
---
id: mem_20260327_153000
title: "今日重要决策"
importance: high        # high | medium | low | important（important=永久保留）
important: false        # true = 永不压缩
tags: [决策, 战略, 猫经理]
created: 2026-03-27T15:30:00+08:00
last_access: 2026-03-27T15:30:00+08:00
access_count: 1
context_correlation: 1.0  # Phase 2: 上下文相关性系数 (0.5-1.5)
retention: 90           # 保留天数（重要/important 可设更长）
current_layer: L0       # L0 | L1 | L2 | L3 | L4
target_layer: hot       # hot | warm | cold | archive
weight: 10.0           # Phase 2 权重 = factor × decay × ln(count+1) × corr
# 复习状态追踪（Phase 4）
review_status: pending_review  # pending_review | reviewing | reviewed | mastered
last_reviewed: null
next_review: null
review_count: 0
---

# 今日重要决策

## 决策内容...
```

---


| 文件年龄 | 自动迁移至 |
|---------|---------|
| 0-7天   | viking-L0-hot/ (L0) |
| 8-29天  | viking-L1-warm/ (L1) |
| 30-89天 | viking-L2-cold/ (L2) |
| 90天+   | viking-L4-archive/ (L4) |

**重要标记**（`important: true` 或 `importance: important`）= 永不自动压缩

---

## 🔄 压缩调度

```bash
# 预览变更（不实际执行）
python sv_compress.py --dir <memories_dir> --dry-run

# 实际执行压缩/迁移
python sv_compress.py --dir <memories_dir> --force

# 定期自动执行（建议每完成 ~5 个任务触发一次）
python sv_compress.py --dir <memories_dir> --force
```

> 解决"用户复习了哪些内容、如何判定复习状态"的跟踪问题

### 复习状态定义

| 状态 | 说明 | 触发条件 |
|------|------|---------|
| `pending_review` | 待复习 | 新建记忆的默认状态 |
| `reviewing` | 复习中 | 用户开始复习 |
| `reviewed` | 已复习 | 完成一次复习，自动计算下次复习日期 |
| `mastered` | 已掌握 | 多次复习后标记，自动移动到 archive 层 |

### 艾宾浩斯复习曲线

复习完成后自动计算下次复习日期（简化版）：

| 复习次数 | 间隔 |
|---------|------|
| 第1次 | 1天后 |
| 第2次 | 3天后 |
| 第3次 | 7天后 |
| 第4次 | 15天后 |
| 第5次+ | 30天后 |

### 复习状态管理命令

```bash
# 标记复习状态
python sv_review.py mark <memories_dir> <file> <status>

# 列出指定状态的记忆
python sv_review.py list --dir <memories_dir> pending_review
python sv_review.py list --dir <memories_dir> reviewed

# 显示统计
python sv_review.py stats --dir <memories_dir>

# 显示今日需复习的记忆
python sv_review.py due --dir <memories_dir>
```

### 示例

```bash
# 标记为已复习（自动更新 last_reviewed 和 next_review）
python sv_review.py mark <memories_dir> <file> reviewed

# 标记为已掌握（自动移动到 L4 层）
python sv_review.py mark <memories_dir> <file> mastered

# 查看统计
python sv_review.py stats --dir <memories_dir>
```

### sv_find 支持复习状态过滤

```bash
# 只显示待复习的记忆
python sv_find.py --dir <memories_dir> --review-status pending_review

# 只显示已复习的记忆
python sv_find.py --dir <memories_dir> --review-status reviewed
```

---

## 📦 Phase 3: Archive 可逆性 (v1.3)

> 归档不再是"彻底遗忘"，而是多粒度压缩存储，支持按需解压恢复

### 核心改进

| 旧方案 | 新方案 |
|--------|--------|
| 归档 = 丢弃正文，只留标题 | 归档 = 多粒度摘要 + 完整内容存档 |
| 需要时无法找回细节 | 可随时解压完整内容 |
| 只能线性遗忘 | 支持选择性回忆 |

### 新增脚本

| 脚本 | 功能 |
|------|------|
| `sv_archive_summary.py` | 生成多粒度摘要，保留完整内容 |
| `sv_decompress.py` | 按需解压，恢复到目标层 |

### 使用方式

```bash
# 归档时自动生成摘要（集成到 sv_compress.py）
python sv_compress.py --dir <memories_dir> --force

# 手动为 archive 文件生成摘要
python sv_archive_summary.py <file> --keep

# 查看摘要
python sv_decompress.py <file>

# 显示完整内容
python sv_decompress.py <file> --show

# 恢复到 L0-hot 层
python sv_decompress.py <file> --restore
```

### frontmatter 新增字段

```markdown
summary: "一句话摘要 | 段落摘要"
full_content_file: "filename.md.archive.full"
```

---

## ⚖️ Phase 2: 权重公式优化 (v1.2)

> 改进 access_count 增长模式，引入上下文相关性系数

### 旧公式 vs 新公式

| 项目 | 旧公式 | 新公式 |
|------|--------|--------|
| 访问次数增长 | 线性 `(count+1)` | 对数 `ln(count+1)` |
| 上下文相关性 | ❌ 无 | ✅ 0.5-1.5 系数 |
| 防止记忆霸权 | ❌ 无法防止 | ✅ 旧记忆不会无限膨胀 |

### 新公式

```
W = importance_factor × (1/(days+1)^0.3) × ln(access_count+1) × context_correlation
```

### 参数说明

| 参数 | 说明 | 范围 |
|------|------|------|
| `importance_factor` | 重要性因子 | high=3.0, medium=1.5, low=0.5 |
| `time_decay` | 时间衰减 | 0-1，越老越小 |
| `ln(access_count+1)` | 对数增长 | 防止无限膨胀 |
| `context_correlation` | 上下文相关性 | 0.5-1.5（默认1.0） |

### context_correlation 设置建议

| 场景 | 系数 | 说明 |
|------|------|------|
| 高相关任务访问 | 1.3-1.5 | 当前工作直接相关 |
| 正常访问 | 1.0 | 例行加载 |
| 低相关但被召回 | 0.7-0.9 | 动态回流晋升 |

### 使用方式

```bash
# 单独计算权重
python sv_weight.py --file <file>

# 更新权重（默认 context_correlation=1.0）
python sv_weight.py --file <file> --update

# 指定上下文相关性
python sv_weight.py --file <file> --update --context-correlation 1.5

# 集成到加载流程（由 sv_autoload.py 自动调用）
python sv_autoload.py <memories_dir> --update-weight
```

---

## 🔥 动态回流机制 (v1.1 新增)

> 当检测到当前任务与 Cold/Archive 记忆语义相似时，自动晋升至 Hot 层

### 背景

传统系统的痛点：记忆只能向下迁移（hot→warm→cold→archive），永远不会回来。
这导致"三个月前做过类似项目，但系统已经忘了"的问题。

### 解决方案

动态回流机制：每次加载记忆时，自动扫描 cold/archive 层，找出语义相关的记忆并晋升。

### 核心脚本

```bash
# 独立运行
python sv_promote.py --context "当前任务描述"
python sv_promote.py --dry-run  # 预览模式
python sv_promote.py --threshold 0.7  # 调整阈值

# 集成到加载流程
python sv_autoload.py --promote
```

### 晋升流程

1. **语义相似度判断**：使用 LLM 判断当前上下文与历史记忆的相关性
2. **阈值过滤**：相似度 ≥ 0.7 才晋升（可调整）
3. **重要记忆保护**：`importance: high/important` 的记忆不受自动晋升影响
4. **原子性操作**：先写临时文件，再移动，避免数据丢失

### 技术细节

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--threshold` | 0.7 | 相似度阈值，0.0-1.0 |
| `--layer` | cold,archive | 扫描的源层级 |
| `--context` | 自动获取 | 当前任务上下文 |

### API 支持

- 优先使用 **NVIDIA Qwen**（如已配置）
- Fallback: MiniMax M2.5

### 注意事项

- ⚠️ 晋升是**单向的**（cold/archive → hot），不会降级
- ⚠️ 重要记忆（high/important）不会被自动晋升，保持原层级
- ⚠️ 每次最多处理 50 条记忆，防止 API 过载
- 💡 建议在会话开始时用 `python sv_autoload.py --promote`，而非频繁独立调用

---

## 💡 实用技巧

**如何判断写哪个层级：**
- 有细节、有过程、有价值 → hot/L0
- 只有结论、要点 → warm/L1
- 只是一个标签/关键词 → cold/L2

**团队共享记忆（可选）：**
- 重要决策 → 可同步到共享目录（需手动配置）
- 各 Agent 每天早上应读取共享 L0 层：`python sv_read.py <shared_dir> <file>`

---

## 📂 相关文件

- 脚本：`scripts/sv_*.py`（所有脚本均为 Python 实现）
- 记忆根目录：`~/.workbuddy/memory/`（Windows：`C:\Users\<user>\.workbuddy\memory\`）
- 共享空间（可选）：`viking-global/shared/memory/`
