---
name: runflow-stats
description: Use when 用户想查看统计、分布、导出数据、趋势汇总、按维度分组
---

# 训练统计与导出流程

## Overview

训练统计助手，按维度分组聚合数据并支持导出。核心流程：确定维度 → 查询统计 → 展示 → 可选导出。

## When to Use

- 用户说"统计"/"分布"/"导出"/"趋势"
- 用户想按来源/周/月/年/配速区间/距离范围分组
- 用户需要导出训练数据

## Workflow

### 1. 确定统计维度

支持维度：
- `by_source`：按数据来源（garmin/coros/apple/manual）
- `by_week`：按周
- `by_month`：按月
- `by_year`：按年
- `by_pace_zone`：按配速区间（E/M/T/I/R）
- `by_distance_range`：按距离范围（<5k/5-10k/10-21k/21-42k/>=42k）

### 2. 调用统计 Tool

调用 `get_statistics(dimension, date_from, date_to)`：
- 返回 groups（每组含 count/total_distance_km/total_duration_s/avg_pace/total_tss/avg_vdot）

### 3. 展示统计

以表格 + 简要文字展示，**不调 LLM**（统计是纯数据展示）。

### 4. 可选导出

用户要求导出时调用 `export_data(format, include_ai_logs)`：
- format：csv / json / parquet / md
- include_ai_logs：是否含 AI 决策日志（含时二次确认）
- **导出前必须用户确认**（data-safety-rules.md）

## Quick Reference

| 步骤 | Tool | 说明 |
|------|------|------|
| 分组统计 | `get_statistics` | 7 种维度 |
| 导出数据 | `export_data` | csv/json/parquet/md |

## Common Mistakes

- **导出前未确认**：export_data 前必须用户确认
- **全量导出未含 AI 日志**：询问是否包含 AI 决策记录
- **统计维度不合法**：仅支持 7 种维度，非法维度返回空
- **统计调 LLM**：统计是纯数据展示，不调 LLM

## 约束规则

- 遵循 data-safety-rules.md：导出前用户确认，含 AI 日志时二次确认
- 遵循 interaction-rules.md：批量操作展示进度
- 统计结果以表格展示，不调 LLM 生成解读
