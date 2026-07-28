---
trigger: model_decision
description: "用户询问跑步训练、导入数据、分析负荷、制定计划、复盘训练、教练建议、统计分布时使用"
---

# RunFlowSkills 技能清单

本项目提供 6 个跑步数据分析技能，通过 MCP Tool 暴露：

- /runflow-analyze: runflow-analyze
- /runflow-coach: runflow-coach
- /runflow-import: runflow-import
- /runflow-plan: runflow-plan
- /runflow-review: runflow-review
- /runflow-stats: runflow-stats

## 使用方式

直接用自然语言描述需求，AI 会自动匹配对应技能：
- "导入今天的跑步文件" → runflow-import
- "分析最近 30 天的训练" → runflow-analyze
- "帮我制定全马破 4 的 12 周计划" → runflow-plan
- "复盘本周训练" → runflow-review
- "今天能跑间歇吗？" → runflow-coach
- "按周统计跑量" → runflow-stats