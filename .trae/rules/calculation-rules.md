---
name: calculation-rules
scope: runflow-analyze, runflow-plan, runflow-coach
---

# 计算规则

1. VDOT 计算必须使用 Powers 方法，距离 <1500m 时标记为 "estimated" 并降低置信度
2. TSS = 时长(秒) × IF² × 100，IF 基于乳酸阈值心率或配速
3. CTL = 42 天 EWMA，ATL = 7 天 EWMA，TSB = CTL - ATL
4. 配速格式统一 M'SS"/km（如 5'40"/km），时长统一 HH:MM:SS
5. 心率区间基于个人最大心率或乳酸阈值心率，不可使用通用公式默认值（如 220-年龄）。默认值见 constants.py（DEFAULT_MAX_HR / DEFAULT_LTHR），用户可经 Web `/settings` 页覆盖 `data/config.json`；计算器读取顺序：config.json → constants.py 默认值
6. 配速区间基于个人 VDOT：E=59-74%, M=75-84%, T=88-100%, I=95-100%, R=100-110%
7. EWMA 计算：当日值 × α + 昨日 EWMA × (1-α)，α = 2/(N+1)，N 为窗口天数
8. HRV 指标：RMSSD（主）、SDNN、pNN50，基线 = 7 天滚动均值
