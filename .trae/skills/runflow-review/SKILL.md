---
name: runflow-review
description: Use when 用户想复盘训练、生成总结、回顾本周/本月训练、导出报告
---

# 训练复盘流程

## Overview

训练复盘助手，负责聚合周期数据、对比历史、生成报告。核心流程：确定周期 → 聚合数据 → 对比 → AI 报告 → 可选导出。

## When to Use

- 用户说"复盘"/"总结"/"本周"/"本月"/"回顾"
- 用户想了解某段时间的训练表现
- 用户需要导出训练报告

## Workflow

### 1. 确定周期

默认本周，支持 week/month/season/year。

### 2. 聚合周期数据

调用 `get_period_summary(period, date_ref)`：
- 返回 total_distance / total_tss / avg_vdot / sessions_count
- 返回 vdot_trend / hrv_trend
- 返回 load_change（vs 上周期变化）

### 3. 对比历史

- 环比：vs 上周期（get_period_summary 已含 load_change）
- 同比：vs 去年同期（需调用两次 get_period_summary）

### 4. AI 生成报告

用 Tool 返回的 `prompt` 调用宿主 LLM 生成复盘报告：
- 跑量统计（总距离/训练次数）
- 负荷变化（CTL/ATL/TSB 趋势）
- VDOT 趋势（进步/停滞/退步）
- HRV 趋势（恢复状态）
- 伤病风险评估
- 下周建议

### 5. 可选导出

用户确认后调用 `export_data(format="md")` 导出 Markdown 报告。
**导出前必须用户确认**（data-safety-rules.md）。

### 6. 持久化决策

调用 `save_decision_log` 记录复盘结论。

## Quick Reference

| 步骤 | Tool | 说明 |
|------|------|------|
| 周期聚合 | `get_period_summary` | week/month/season/year |
| 导出报告 | `export_data` | md/csv/json/parquet |
| 决策记录 | `save_decision_log` | 记录复盘结论 |

## Common Mistakes

- **复盘笼统**：必须具体到数据（"本周跑量 45km，较上周 +5km"）
- **缺数据维度静默跳过**：必须明确标注 "HRV 数据缺失，未纳入分析"
- **导出前未确认**：export_data 前必须用户确认
- **同比/环比不明确**：必须标注时间窗口

## 约束规则

- 遵循 analysis-rules.md：复盘必须具体、附依据
- 遵循 data-safety-rules.md：导出前用户确认，含 AI 日志时二次确认
- 遵循 interaction-rules.md：错误时提供降级方案
