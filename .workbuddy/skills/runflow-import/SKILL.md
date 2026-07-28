---
name: runflow-import
description: Use when 用户想导入训练数据、上传文件、同步记录、手动录入跑步活动
version: 1.0.0
allowed-tools: [import_file, import_manual]
inputs:
  - name: file_path
    type: string
    required: false
    description: FIT/GPX/CSV/TCX/XML 文件路径或批量目录
  - name: manual_data
    type: object
    required: false
    description: 手动录入数据（date/distance/duration/heart_rate/source）
  - name: force
    type: boolean
    required: false
    default: false
    description: 是否强制重新导入（覆盖去重检测）
outputs:
  - name: session_id
    type: string
    description: 导入成功的会话 ID
  - name: status
    type: enum
    values: [imported, skipped, error]
    description: 导入状态
  - name: reason
    type: string
    description: 跳过/失败原因
error_handling:
  - parse_failed: "提示手动录入（import_manual）"
  - duplicate_hash: "询问是否 --force 覆盖"
  - cross_platform_duplicate: "询问是否 --force 覆盖"
  - unsupported_format: "明确告知仅支持 .fit .gpx .csv .tcx .xml"
compatibility:
  mcp_server: ">=0.1.1"
  python: ">=3.12"
  platforms: [trae, claude-code, cursor, windsurf, continue]
---

# 训练数据导入流程

## Overview

跑步数据导入助手，负责将 FIT/GPX/CSV/TCX/XML 文件或手动录入数据转化为结构化 Session 并存储。核心流程：解析文件 → SHA256 去重 → 计算指标 → 存储 Parquet。

## When to Use

- 用户说"导入"/"上传"/"同步"/"录入"
- 用户提供 FIT/GPX/CSV/TCX/XML 文件路径
- 用户要求手动录入跑步数据
- 用户需要批量导入多个文件

## Workflow

### 1. 确定数据源

询问用户提供以下之一：
- 文件路径（FIT/GPX/CSV/TCX/XML）
- 批量文件目录
- 手动录入（日期/距离/时长/心率/来源）

### 2. 调用导入 Tool

- 文件源：调用 `import_file(file_path, force)` —— 支持单文件或循环批量
- 手动录入：调用 `import_manual(manual_data, force)`

### 3. 处理去重结果

- `imported=true`：展示 session_id + 关键指标（距离/时长/VDOT/TSS）
- `skipped=true`：告知用户重复原因（duplicate_hash / cross_platform_duplicate），询问是否 `--force` 重新导入
- `error`：给出明确错误原因（格式错误/不支持类型）

### 4. 批量导入汇总

循环调用 `import_file`，最后汇总：
```
导入完成：成功 N，跳过 M（重复），失败 K
```

## Quick Reference

| 步骤 | Tool | 降级方案 |
|------|------|----------|
| 文件导入 | `import_file` | 解析失败 → 手动录入 |
| 手动录入 | `import_manual` | 数据校验失败 → 提示修正 |
| 去重检测 | Tool 内部自动 | 重复 → 询问 --force |
| 批量导入 | 循环 `import_file` | 逐文件报告状态 |

## Common Mistakes

- **重复导入不提示 --force**：skipped=true 时必须告知用户可加 force 覆盖
- **手动录入未校验合理性**：距离/时长必须 >0，心率 30-260
- **批量导入无汇总**：必须给出成功/跳过/失败计数
- **不支持的文件类型**：仅支持 .fit .gpx .csv .tcx .xml

## 约束规则

> 规则统一收敛至根目录 [AGENTS.md](../../../AGENTS.md)，本节仅列与本 Skill 直接相关的条目。

- 遵循 `AGENTS.md §6 数据安全规则`：文件本地解析，不上传外部服务
- 遵循 `AGENTS.md §2 交互协议`：去重冲突必须用户确认
- SHA256 去重 + 跨平台去重（时间±5min + 距离±2% + 时长±30s）
- 导入失败必须给明确原因，不可只报 "导入失败"
