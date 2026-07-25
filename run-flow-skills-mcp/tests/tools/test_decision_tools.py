"""get_decision_trace / save_decision_log tool 测试（spec FR-COACH-02/03, 6.2, 10.1）."""
from pathlib import Path

import pytest

from run_flow_skills_mcp.tools import _deps
from run_flow_skills_mcp.tools.get_decision_trace import get_decision_trace
from run_flow_skills_mcp.tools.save_decision_log import save_decision_log


@pytest.fixture(autouse=True)
def reset_cache():
    yield
    _deps.reset_services_cache()


def test_save_decision_log_returns_prompt_and_id(tmp_path: Path):
    """save_decision_log 返回 prompt + decision_id + saved=True."""
    _deps.reset_services_cache()
    result = save_decision_log(
        decision_type="coach",
        inputs={"hrv": 38, "tsb": -5},
        reasoning="HRV 偏低 + TSB 负值，建议降级训练",
        recommendation="E 区间 30 分钟，配速 5'40\"-6'00\"/km",
        confidence=0.75,
        trace_chain=["HRV=38", "baseline=45", "rule:HRV偏离>10%", "TSB=-5"],
        _data_dir=tmp_path,
    )
    assert result["saved"] is True
    assert result["decision_id"].startswith("dec_")
    assert "prompt" in result
    # prompt 应已填充 DECISION_TRACE_TEMPLATE
    assert "{recommendation}" not in result["prompt"]


def test_save_decision_log_invalid_confidence_returns_error(tmp_path: Path):
    """confidence 越界返回 error + prompt."""
    _deps.reset_services_cache()
    result = save_decision_log(
        decision_type="coach",
        inputs={"hrv": 38},
        reasoning="test",
        recommendation="test",
        confidence=1.5,  # 越界
        trace_chain=["a"],
        _data_dir=tmp_path,
    )
    assert result["saved"] is False
    assert "error" in result
    assert "prompt" in result


def test_get_decision_trace_found(tmp_path: Path):
    """保存后可查询."""
    _deps.reset_services_cache()
    saved = save_decision_log(
        decision_type="coach",
        inputs={"hrv": 38},
        reasoning="test",
        recommendation="test",
        confidence=0.7,
        trace_chain=["a", "b"],
        _data_dir=tmp_path,
    )
    result = get_decision_trace(saved["decision_id"], _data_dir=tmp_path)
    assert result["found"] is True
    assert result["decision_id"] == saved["decision_id"]
    assert "trace" in result
    assert "prompt" in result


def test_get_decision_trace_not_found(tmp_path: Path):
    """不存在的 decision_id 返回 found=False + prompt."""
    _deps.reset_services_cache()
    result = get_decision_trace("dec_20260101_999", _data_dir=tmp_path)
    assert result["found"] is False
    assert "prompt" in result
