---
name: runflow-coach
description: Use when 用户询问今天能不能跑、今天怎么练、感觉累、恢复状态、训练建议
version: 1.0.0
allowed-tools: [read_body_signals, calc_metrics, query_plan, save_decision_log, get_decision_trace]
inputs:
  - name: date
    type: string
    required: false
    description: 评估日期 YYYY-MM-DD，默认今日
  - name: user_question
    type: string
    required: true
    description: 用户的训练咨询问题
outputs:
  - name: readiness_level
    type: enum
    values: [green, yellow, red]
    description: 就绪状态
  - name: recommendation
    type: object
    description: 训练建议（类型/强度/时长/配速区间）
  - name: confidence
    type: number
    description: 置信度 0-1
  - name: trace_chain
    type: array
    description: 决策溯源链（输入数据 + 判断规则）
  - name: alternatives
    type: array
    description: 替代方案（至少 1 个）
  - name: coach_prompt
    type: string
    description: 传递给宿主 LLM 的建议生成提示词
error_handling:
  - insufficient_signals: "降级为 TSB 单指标决策并标注置信度低"
  - plan_conflict: "给调整建议并说明冲突原因"
  - confidence_low: "必须提示 '仅供参考，建议结合主观感受'"
compatibility:
  mcp_server: ">=0.1.1"
  python: ">=3.12"
  platforms: [trae, claude-code, cursor, windsurf, continue]
---

# AI 教练建议流程（差异化核心）

## Overview

AI 教练助手，综合身体信号、训练负荷、当前计划生成具体可执行的训练建议。核心流程：读身体信号 → 读负荷 → 读计划 → AI 综合判断 → 置信度门禁 → 用户反馈。

## When to Use

- 用户说"能不能跑"/"今天怎么练"/"感觉累"/"恢复"
- 用户询问今日训练建议
- 用户想了解身体就绪状态

## Workflow

### 1. 读取身体信号

调用 `read_body_signals(date=today)`：
- 返回 HRV / 静息心率 / 睡眠 / RPE / 基线偏离 / 就绪状态（green/yellow/red）
- readiness_level 由 Tool 内部综合 HRV + TSB + RPE 计算

### 2. 读取训练负荷

调用 `calc_metrics(date_from=<7天前日期>, date_to=<今日日期>)` 取 ATL，调用 `calc_metrics(date_from=<42天前日期>, date_to=<今日日期>)` 取 CTL/TSB。

> **注意**：`calc_metrics` 的入参是绝对日期（`YYYY-MM-DD`），不支持相对日期（如 `-7d`）。宿主 AI 需先计算具体日期后传入。

### 3. 读取当前计划

调用 `query_plan()`（无 plan_id 返回最新计划）→ 获取今日计划课表。

### 4. AI 综合判断

用 Tool 返回的 `coach_prompt` 调用宿主 LLM 生成建议：
- **类型 + 强度 + 时长 + 配速区间**（具体可执行）
- **决策溯源链**（输入数据 + 判断规则 + 置信度）
- **替代方案**（至少 1 个）

### 5. 置信度门禁

- `confidence ≥ 0.6`：直接给建议
- `confidence < 0.6`：必须提示 "仅供参考，建议结合主观感受"

### 6. 用户反馈

询问用户是否采纳：
- 采纳 → `save_decision_log` 记录 user_feedback=accepted
- 拒绝 → 记录 user_feedback=rejected
- 修改 → 记录修改内容

### 7. 历史查询（可选）

用户问"上次类似情况" → 调用 `get_decision_trace` 查询历史决策。

## Quick Reference

| 步骤 | Tool | 说明 |
|------|------|------|
| 身体信号 | `read_body_signals` | HRV/RPE/就绪状态 |
| 训练负荷 | `calc_metrics` | ATL(7d)/CTL(42d)/TSB |
| 当前计划 | `query_plan` | 今日课表 + fidelity |
| 决策记录 | `save_decision_log` | 含 user_feedback |
| 历史溯源 | `get_decision_trace` | 可选，查类似决策 |

## Common Mistakes

- **建议不具体**："轻松跑一会儿" 不合规，必须 "E 区间 30 分钟，配速 5'40"-6'00"/km"
- **单一指标决策**：必须综合 HRV + TSB + RPE
- **与计划冲突**：计划是休息日不可建议高强度；冲突时给调整建议
- **confidence < 0.6 未提示**：必须加 "仅供参考" 声明
- **未考虑昨日高强度**：24h 内有 T5 间歇 → 今日必须降级
- **无替代方案**：至少给 1 个替代

## 约束规则

> 规则统一收敛至根目录 [AGENTS.md](../../../AGENTS.md)，本节仅列与本 Skill 直接相关的条目。

- 遵循 `AGENTS.md §5 教练规则`：建议具体可执行 + 溯源链 + 替代方案
- 遵循 `AGENTS.md §3 计算规则`：配速区间基于个人 VDOT
- 遵循 `AGENTS.md §2 交互协议`：建议给出后必须询问采纳
- confidence ≥ 0.6 直接建议；< 0.6 标注 "仅供参考"
- 用户反馈必须记录到 DecisionLog
