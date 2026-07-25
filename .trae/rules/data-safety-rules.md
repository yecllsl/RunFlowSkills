---
name: data-safety-rules
scope: runflow-import, runflow-stats, runflow-coach
---

# 数据安全规则

1. 所有数据仅存储在本地 data/ 目录，禁止上传任何外部服务
2. 导出数据前需用户确认
3. 不记录用户姓名、身份证号、手机号等个人身份信息（PII）；年龄/体重/性别/身高/心率等训练参数不属 PII，存于 `data/config.json` 用于计算
4. FIT/GPX/CSV/TCX/XML 文件解析在本地完成，不调用外部 API
5. Web 可视化仅绑定 127.0.0.1，JS 库本地化（HTMX/Alpine/ECharts 无 CDN）
6. 原始文件 SHA256 哈希存储用于去重，原始文件路径可选保留
7. 导出含 AI 决策日志时二次确认（含敏感训练分析）
8. 不记录 IP 地址、设备指纹等环境信息
