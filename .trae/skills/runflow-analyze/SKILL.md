---
name: runflow-analyze
description: Use when 用户想分析训练数据、查看负荷、VDOT趋势、HRV、疲劳度、心率漂移
---

# 训练数据分析流程

## Overview

训练数据分析助手，负责聚合区间指标、趋势分析、疲劳评估，并用 AI 生成数据驱动的解读。核心流程：确定范围 → 并行查询 → AI 解读 → 可选持久化。

## When to Use

- 用户说"分析"/"负荷"/"VDOT"/"HRV"/"疲劳"/"心率漂移"
- 用户想了解近期训练状态
- 用户需要数据支撑做训练决策

## Workflow

### 1. 确定分析范围

默认 30 天，支持 7/30/90/365 天或自定义日期范围。

### 2. 并行调用分析 Tool

- `calc_metrics(date_from, date_to)`：返回 VDOT 趋势 / TSS 累计 / CTL / ATL / TSB / 心率区间分布
- `get_trends(days, metric)`：返回时间序列（metric 可选 vdot/load/hrv）
- `analyze_fatigue(days)`：返回综合疲劳度（HRV + TSB + RPE）

### 3. AI 解读

用 Tool 返回的 `prompt` 调用宿主 LLM 生成解读：
- 必须具体到数据（"CTL 65 较上周 +3" 而非 "负荷上升"）
- 必须附数据依据
- 必须列风险因子
- 必须标注误差范围（禁止伪精确）
- 数据不足时必须降级标注

### 4. 可选持久化

用户确认后调用 `save_decision_log` 持久化分析结论。

## Quick Reference

| 步骤 | Tool | 说明 |
|------|------|------|
| 指标聚合 | `calc_metrics` | CTL/ATL/TSB/VDOT 趋势 |
| 趋势查询 | `get_trends` | vdot/load/hrv 时序 |
| 疲劳评估 | `analyze_fatigue` | 综合疲劳度 + 评分 |
| 决策记录 | `save_decision_log` | 可选，用户确认后 |

## Common Mistakes

- **笼统结论**："训练不错"/"负荷合理" 不合规，必须具体到数据
- **静默外推**：数据不足时必须标注 "基于 7 天数据，置信度低"
- **伪精确**："全马 3:59:30" 不合规，必须给区间 "3:55:00–4:05:00"
- **跨配速段混合**：心率漂移必须基于相同配速段

## 约束规则

- 遵循 analysis-rules.md：分析必须具体、附依据、标注误差
- 遵循 calculation-rules.md：VDOT 用 Powers 方法，TSS/CTL/ATL 公式正确
- 趋势判断必须明确时间窗口（vs 上周 / vs 去年同期）
