"""决策溯源链模板（spec 4.5, 10.1）.

用于 save_decision_log 的 trace_chain 字段，由宿主 AI 填充后传入。
"""

DECISION_TRACE_TEMPLATE = """决策溯源链:
1. 输入数据: {inputs}
2. 判断逻辑: {reasoning}
3. 建议结论: {recommendation}
4. 置信度: {confidence}
5. 相关 Session: {related_session_ids}
"""
