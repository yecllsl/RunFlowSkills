"""tools 公共依赖工厂（spec 10.2）.

所有 tool 函数通过 get_services() 获取 service 实例，
测试可通过 monkeypatch 替换或传 _data_dir 参数隔离。

单例缓存：同一进程内多次调用只创建一次 services（按 data_dir 区分）。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.constants import DATA_DIR as _DEFAULT_DATA_DIR
from run_flow_skills_mcp.services.analysis_service import AnalysisService
from run_flow_skills_mcp.services.coach_service import CoachService
from run_flow_skills_mcp.services.import_service import ImportService
from run_flow_skills_mcp.services.plan_service import PlanService
from run_flow_skills_mcp.services.review_service import ReviewService
from run_flow_skills_mcp.services.stats_service import StatsService
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


@dataclass
class Services:
    """所有 service 实例的容器.

    后两个 store 字段供 Plan 3 Web 层复用，避免跨 Plan 修改本类。
    """

    import_service: ImportService
    analysis_service: AnalysisService
    plan_service: PlanService
    review_service: ReviewService
    coach_service: CoachService
    stats_service: StatsService
    parquet_store: ParquetStore  # 供 Plan 3 Web 层读取 session 列表
    json_store: JsonStore  # 供 Plan 3 Web 层读写 config.json


_cache: dict[str, Services] = {}


def get_services(data_dir: Optional[Path] = None) -> Services:
    """获取 services 单例（按 data_dir 缓存）.

    Args:
        data_dir: 数据目录；为 None 时使用 constants.DATA_DIR 默认值

    Returns:
        Services 容器（同一 data_dir 仅创建一次）
    """
    key = str(data_dir or _DEFAULT_DATA_DIR)
    if key in _cache:
        return _cache[key]

    actual_dir = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
    actual_dir.mkdir(parents=True, exist_ok=True)

    parquet_store = ParquetStore(actual_dir)
    json_store = JsonStore(actual_dir)

    services = Services(
        import_service=ImportService(parquet_store, json_store),
        analysis_service=AnalysisService(parquet_store, json_store),
        plan_service=PlanService(parquet_store, json_store),
        review_service=ReviewService(parquet_store, json_store),
        coach_service=CoachService(parquet_store, json_store),
        stats_service=StatsService(parquet_store, json_store),
        parquet_store=parquet_store,
        json_store=json_store,
    )
    _cache[key] = services
    return services


def reset_services_cache() -> None:
    """重置单例缓存（测试隔离用）."""
    _cache.clear()
