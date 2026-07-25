"""constants.py 单元测试."""
from run_flow_skills_mcp.constants import (
    ATL_WINDOW_DAYS,
    CTL_WINDOW_DAYS,
    DEFAULT_GENDER,
    DEFAULT_LTHR,
    DEFAULT_MAX_HR,
    DEFAULT_RESTING_HR,
    DEDUP_DISTANCE_TOLERANCE_PCT,
    DEDUP_DURATION_TOLERANCE_S,
    DEDUP_TIME_TOLERANCE_S,
    HRV_BASELINE_DAYS,
    PACE_ZONE_FACTORS,
    SUPPORTED_IMPORT_EXT,
    VDOT_MIN_DISTANCE_M,
    format_duration,
    format_pace,
)


def test_default_hr_values():
    assert DEFAULT_MAX_HR == 190
    assert DEFAULT_LTHR == 165
    assert DEFAULT_RESTING_HR == 60


def test_default_gender_exists():
    """M-3 评审修正：DEFAULT_GENDER 必须存在."""
    assert DEFAULT_GENDER in ("male", "female")


def test_vdot_min_distance_constant():
    """VDOT_MIN_DISTANCE_M 应在 constants.py 中定义（评审修正）."""
    assert VDOT_MIN_DISTANCE_M == 1500.0


def test_ewma_windows():
    assert CTL_WINDOW_DAYS == 42
    assert ATL_WINDOW_DAYS == 7
    assert HRV_BASELINE_DAYS == 7


def test_pace_zone_factors_cover_all_zones():
    """E/M/T/I/R 五个区间都必须定义."""
    for zone in ("E", "M", "T", "I", "R"):
        assert zone in PACE_ZONE_FACTORS
        lo, hi = PACE_ZONE_FACTORS[zone]
        assert 0 < lo <= hi <= 1.1


def test_pace_zone_factors_values_match_spec():
    """spec 8.1.6: E=59-74%, M=75-84%, T=88-100%, I=95-100%, R=100-110%."""
    assert PACE_ZONE_FACTORS["E"] == (0.59, 0.74)
    assert PACE_ZONE_FACTORS["M"] == (0.75, 0.84)
    assert PACE_ZONE_FACTORS["T"] == (0.88, 1.00)
    assert PACE_ZONE_FACTORS["I"] == (0.95, 1.00)
    assert PACE_ZONE_FACTORS["R"] == (1.00, 1.10)


def test_dedup_tolerances():
    assert DEDUP_TIME_TOLERANCE_S == 300
    assert DEDUP_DISTANCE_TOLERANCE_PCT == 0.02
    assert DEDUP_DURATION_TOLERANCE_S == 30


def test_supported_import_ext_includes_gpx():
    """M-1 评审修正：GPX 必须在白名单."""
    assert ".gpx" in SUPPORTED_IMPORT_EXT
    assert set(SUPPORTED_IMPORT_EXT) == {".fit", ".gpx", ".csv", ".tcx", ".xml"}


def test_format_pace_normal():
    """5'40"/km 格式."""
    assert format_pace(340.0) == "5'40\"/km"
    assert format_pace(360.0) == "6'00\"/km"
    assert format_pace(361.0) == "6'01\"/km"


def test_format_pace_sub_minute():
    """3'05"/km."""
    assert format_pace(185.0) == "3'05\"/km"


def test_format_duration_normal():
    assert format_duration(3725) == "01:02:05"
    assert format_duration(60) == "00:01:00"
    assert format_duration(0) == "00:00:00"
