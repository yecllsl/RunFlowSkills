---
name: runflow-plan
description: Use when 用户想制定训练计划、生成课表、设定目标、备赛全马/半马/破4
version: 1.0.0
allowed-tools: [query_sessions, generate_plan, query_plan, save_decision_log]
inputs:
  - name: goal_type
    type: enum
    values: [full_marathon, half_marathon, 10k, 5k]
    required: true
    description: 比赛类型
  - name: goal_time
    type: string
    required: true
    description: 目标完赛时间（如 "4:00:00"）
  - name: race_date
    type: string
    required: true
    description: 比赛日期 YYYY-MM-DD
  - name: weeks
    type: integer
    required: true
    description: 训练周期周数
outputs:
  - name: plan_id
    type: string
    description: 计划 ID
  - name: phases
    type: array
    description: 周期化阶段（基础/进展/巅峰/减量）
  - name: pace_zones
    type: object
    description: E/M/T/I/R 配速区间（基于当前 VDOT）
  - name: target_vdot
    type: number
    description: 目标 VDOT（含误差范围）
  - name: plan_prompt
    type: string
    description: 传递给宿主 LLM 的计划解释提示词
error_handling:
  - no_data: "提示用户先导入训练记录"
  - vdot_unknown: "降级为通用 VDOT 并标注置信度低"
  - user_rejected: "不保存计划，记录到 DecisionLog"
compatibility:
  mcp_server: ">=0.1.1"
  python: ">=3.12"
  platforms: [trae, claude-code, cursor, windsurf, continue]
---

# 训练计划生成流程

## Overview

周期化训练计划生成助手，基于当前 VDOT 和目标生成结构化课表。核心流程：收集目标 → 评估能力 → 生成计划 → **用户确认** → 持久化。

## When to Use

- 用户说"计划"/"课表"/"目标"/"全马"/"破4"/"备赛"
- 用户想制定周期化训练方案
- 用户设定了比赛日期和目标成绩

## Workflow

### 1. 收集目标

必填参数：
- `goal_type`：full_marathon / half_marathon / 10k / 5k
- `goal_time`：目标完赛时间（如 "4:00:00"）
- `race_date`：比赛日期（YYYY-MM-DD）
- `weeks`：训练周期周数

### 2. 评估当前能力

调用 `query_sessions` 取近 90 天数据 → 计算当前 VDOT。
若无数据，提示用户先导入训练记录。

### 3. 生成计划

调用 `generate_plan(goal_type, goal_time, race_date, weeks, current_vdot)`：
- 返回结构化计划（phases 周期化阶段 + pace_zones 配速区间 + target_vdot）
- 返回 `plan_prompt`，用此 prompt 调用宿主 LLM 生成计划解释

### 4. 用户确认（强制）

展示完整计划 + AI 解释，**必须用户确认后才保存**。
未经确认不可保存计划。

### 5. 持久化决策

用户确认后调用 `save_decision_log` 记录计划生成决策（含 reasoning + trace_chain）。

### 6. 漏练自适应

后续 `query_plan` 自动计算 fidelity（执行忠实度），漏练检测 → 重新分配后续负荷（负荷守恒，不追加）。

## Quick Reference

| 步骤 | Tool | 说明 |
|------|------|------|
| 评估能力 | `query_sessions` | 取 90 天数据算 VDOT |
| 生成计划 | `generate_plan` | 结构化课表 + plan_prompt |
| 查询计划 | `query_plan` | 含 fidelity 忠实度 |
| 决策记录 | `save_decision_log` | 确认后记录 |

## Common Mistakes

- **未经确认直接保存**：计划必须用户确认后才持久化
- **漏练后追加负荷**：应重新分配，负荷守恒不追加
- **配速区间未基于个人 VDOT**：E/M/T/I/R 区间必须基于当前 VDOT
- **无数据生成计划**：当前 VDOT 未知时必须先导入数据

## 约束规则

> 规则统一收敛至根目录 [AGENTS.md](../../../AGENTS.md)，本节仅列与本 Skill 直接相关的条目。

- 遵循 `AGENTS.md §2 交互协议`：计划保存前必须用户确认
- 遵循 `AGENTS.md §3 计算规则`：配速区间基于 VDOT 比例
- 目标 VDOT 估算需标注误差范围
- 漏练自适应不追加负荷，只重新分配
