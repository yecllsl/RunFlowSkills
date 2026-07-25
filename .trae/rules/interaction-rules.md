---
name: interaction-rules
scope: runflow-import, runflow-analyze, runflow-plan, runflow-review, runflow-coach, runflow-stats
---

# 交互规则

1. 命令格式：/import /analyze /plan /review /coach /stats
2. 自然语言关键词：导入/分析/计划/复盘/教练/统计
3. 每次操作结果必须给出明确反馈（成功/跳过/失败 + 原因）
4. 错误发生时提供降级方案而非直接报错：
   - FIT 解析失败 → 提示手动录入
   - 数据不足 → 降级为趋势外推并标注
   - AI 解读异常 → 提示重试 + 提供原始数据
5. 以下场景必须用户确认：
   - 训练计划生成后保存前
   - 数据导入去重检测到冲突时
   - AI 教练建议给出后是否采纳
   - 数据导出前
6. 命令未识别时提示可用命令清单
7. 批量操作（如导入 100 文件）展示进度
