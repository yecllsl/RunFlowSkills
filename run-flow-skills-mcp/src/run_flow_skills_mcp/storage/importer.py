"""文件导入解析器 - FIT/GPX/CSV/TCX/XML（spec FR-IMPORT-01/02/03, M-1 评审修正）.

GPX/TCX 用标准库 xml.etree，无新依赖（M-1 决策）。
FIT 用 fitparse 库。
"""
from __future__ import annotations

import csv
import hashlib
import math
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.constants import SUPPORTED_IMPORT_EXT
from run_flow_skills_mcp.models import Session, SourceType


class ImportParseError(Exception):
    """文件解析错误."""


def compute_file_hash(path: Path) -> str:
    """计算文件 SHA256 哈希."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_gpx_time(time_str: str) -> datetime:
    """解析 GPX/TCX 时间格式 ISO 8601 UTC."""
    # 2026-07-25T06:00:00Z
    if time_str.endswith("Z"):
        time_str = time_str[:-1] + "+00:00"
    return datetime.fromisoformat(time_str)


def parse_gpx(path: Path, source: SourceType = "garmin") -> Session:
    """解析 GPX 文件（M-1 评审修正）.

    GPX 1.1 格式：trk > trkseg > trkpt (lat, lon, ele, time)
    """
    try:
        tree = ET.parse(path)
    except ET.ParseError as e:
        raise ImportParseError(f"GPX 解析失败: {e}") from e

    root = tree.getroot()
    # 处理命名空间
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    # 提取所有 trkpt
    points = root.findall(f".//{ns}trkpt")
    if not points:
        raise ImportParseError("GPX 无轨迹点")

    # 提取时间和位置
    times: list[datetime] = []
    elevations: list[float] = []
    lat_lon: list[tuple[float, float]] = []

    for pt in points:
        lat = float(pt.get("lat", "0"))
        lon = float(pt.get("lon", "0"))
        lat_lon.append((lat, lon))

        time_elem = pt.find(f"{ns}time")
        if time_elem is not None and time_elem.text:
            times.append(_parse_gpx_time(time_elem.text))

        ele_elem = pt.find(f"{ns}ele")
        if ele_elem is not None and ele_elem.text:
            elevations.append(float(ele_elem.text))

    if not times:
        # 无时间戳，用文件修改时间
        activity_date = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        duration_s = 0
    else:
        activity_date = times[0]
        duration_s = int((times[-1] - times[0]).total_seconds()) if len(times) > 1 else 0

    # 计算距离（Haversine）
    distance_m = _calc_track_distance(lat_lon)

    # 累计爬升
    elevation_gain = _calc_elevation_gain(elevations) if elevations else None

    avg_pace = duration_s / (distance_m / 1000) if distance_m > 0 else 0.0

    session_id = _generate_id_from_date(activity_date)
    return Session(
        session_id=session_id,
        activity_date=activity_date,
        distance_m=distance_m if distance_m > 0 else 1.0,
        duration_s=max(duration_s, 1),
        avg_pace_s_per_km=avg_pace if avg_pace > 0 else 1.0,
        elevation_gain_m=elevation_gain,
        source=source,
        raw_file_hash=compute_file_hash(path),
        raw_file_path=path.name,
    )


def _calc_track_distance(points: list[tuple[float, float]]) -> float:
    """Haversine 距离计算（米）."""
    if len(points) < 2:
        return 0.0
    total = 0.0
    for i in range(1, len(points)):
        lat1, lon1 = points[i - 1]
        lat2, lon2 = points[i]
        # Haversine 公式
        r = 6371000.0  # 地球半径（米）
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = (
            math.sin(dphi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        total += r * c
    return total


def _calc_elevation_gain(elevations: list[float]) -> float:
    """累计爬升（仅正向差值累加）."""
    gain = 0.0
    for i in range(1, len(elevations)):
        diff = elevations[i] - elevations[i - 1]
        if diff > 0:
            gain += diff
    return gain


def _generate_id_from_date(dt: datetime) -> str:
    """根据日期生成临时 session_id（实际应由 service 层重写）."""
    date_str = dt.strftime("%Y%m%d")
    return f"sess_{date_str}_001"


def parse_fit(path: Path, source: SourceType = "garmin") -> Session:
    """解析 FIT 文件（用 fitparse）."""
    try:
        from fitparse import FitFile
    except ImportError as e:
        raise ImportParseError("fitparse 未安装") from e

    try:
        fitfile = FitFile(str(path))
        # 提取关键信息
        activity_date: Optional[datetime] = None
        total_distance = 0.0
        total_timer_time = 0
        avg_hr: Optional[int] = None
        max_hr: Optional[int] = None

        for record in fitfile.get_messages():
            for field in record:
                if field.name == "total_distance":
                    total_distance = float(field.value or 0)
                elif field.name == "total_timer_time":
                    total_timer_time = int(field.value or 0)
                elif field.name == "avg_heart_rate":
                    avg_hr = int(field.value) if field.value else None
                elif field.name == "max_heart_rate":
                    max_hr = int(field.value) if field.value else None
                elif field.name == "time_created":
                    activity_date = field.value

        if activity_date is None:
            activity_date = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)

        distance_m = total_distance
        duration_s = max(total_timer_time, 1)
        avg_pace = duration_s / (distance_m / 1000) if distance_m > 0 else 0.0

        return Session(
            session_id=_generate_id_from_date(activity_date),
            activity_date=activity_date,
            distance_m=distance_m if distance_m > 0 else 1.0,
            duration_s=duration_s,
            avg_pace_s_per_km=avg_pace if avg_pace > 0 else 1.0,
            avg_hr=avg_hr,
            max_hr=max_hr,
            source=source,
            raw_file_hash=compute_file_hash(path),
            raw_file_path=path.name,
        )
    except (OSError, ValueError, KeyError, RuntimeError) as e:
        raise ImportParseError(f"FIT 解析失败: {e}") from e


def parse_csv(path: Path, source: SourceType = "garmin") -> Session:
    """解析 Garmin Connect CSV 导出."""
    try:
        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader, None)
            if row is None:
                raise ImportParseError("CSV 无数据行")

            # Garmin CSV 字段：Activity Date, Distance, Duration, Avg HR, Max HR
            activity_date = datetime.fromisoformat(row.get("Activity Date", ""))
            distance_m = float(row.get("Distance", 0)) * 1000  # km → m
            duration_s = int(float(row.get("Duration", 0)))
            avg_hr = int(row["Avg HR"]) if row.get("Avg HR") else None
            max_hr = int(row["Max HR"]) if row.get("Max HR") else None

            avg_pace = duration_s / (distance_m / 1000) if distance_m > 0 else 0.0

            return Session(
                session_id=_generate_id_from_date(activity_date),
                activity_date=activity_date,
                distance_m=distance_m if distance_m > 0 else 1.0,
                duration_s=max(duration_s, 1),
                avg_pace_s_per_km=avg_pace if avg_pace > 0 else 1.0,
                avg_hr=avg_hr,
                max_hr=max_hr,
                source=source,
                raw_file_hash=compute_file_hash(path),
                raw_file_path=path.name,
            )
    except (ValueError, KeyError) as e:
        raise ImportParseError(f"CSV 解析失败: {e}") from e


def parse_tcx(path: Path, source: SourceType = "garmin") -> Session:
    """解析 TCX 文件（XML）."""
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        # TCX 命名空间
        ns = "{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}"

        activity = root.find(f".//{ns}Activity")
        if activity is None:
            raise ImportParseError("TCX 无 Activity 节点")

        # 提取时间、距离、时长、心率
        id_elem = activity.find(f"{ns}Id")
        activity_date = (
            _parse_gpx_time(id_elem.text)
            if id_elem is not None and id_elem.text
            else datetime.now(timezone.utc)
        )

        distance_elem = activity.find(f".//{ns}DistanceMeters")
        distance_m = float(distance_elem.text) if distance_elem is not None else 0.0

        time_elem = activity.find(f".//{ns}TotalTimeSeconds")
        duration_s = int(float(time_elem.text)) if time_elem is not None else 0

        avg_hr_elem = activity.find(f".//{ns}AverageHeartRateBpm/{ns}Value")
        avg_hr = int(avg_hr_elem.text) if avg_hr_elem is not None else None

        avg_pace = duration_s / (distance_m / 1000) if distance_m > 0 else 0.0

        return Session(
            session_id=_generate_id_from_date(activity_date),
            activity_date=activity_date,
            distance_m=distance_m if distance_m > 0 else 1.0,
            duration_s=max(duration_s, 1),
            avg_pace_s_per_km=avg_pace if avg_pace > 0 else 1.0,
            avg_hr=avg_hr,
            source=source,
            raw_file_hash=compute_file_hash(path),
            raw_file_path=path.name,
        )
    except (ET.ParseError, ValueError) as e:
        raise ImportParseError(f"TCX 解析失败: {e}") from e


def parse_xml(path: Path, source: SourceType = "apple") -> Session:
    """解析 Apple Health XML 导出."""
    # ponytail: Apple Health XML 格式复杂，MVP 仅支持简化版单活动
    # 升级路径：v0.2.0 完整支持 Apple Health 多活动
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        # Apple Health: Record type="HKQuantityTypeIdentifierDistanceWalkingRunning"
        record = root.find(".//Record")
        if record is None:
            raise ImportParseError("Apple Health XML 无 Record")

        activity_date = _parse_gpx_time(record.get("startDate", ""))
        distance_m = float(record.get("value", "0"))
        # Apple Health 不直接提供时长，用 endDate - startDate
        end_date = _parse_gpx_time(record.get("endDate", activity_date.isoformat()))
        duration_s = int((end_date - activity_date).total_seconds())

        avg_pace = duration_s / (distance_m / 1000) if distance_m > 0 else 0.0

        return Session(
            session_id=_generate_id_from_date(activity_date),
            activity_date=activity_date,
            distance_m=distance_m if distance_m > 0 else 1.0,
            duration_s=max(duration_s, 1),
            avg_pace_s_per_km=avg_pace if avg_pace > 0 else 1.0,
            source=source,
            raw_file_hash=compute_file_hash(path),
            raw_file_path=path.name,
        )
    except (ET.ParseError, ValueError) as e:
        raise ImportParseError(f"Apple Health XML 解析失败: {e}") from e


def parse_file(path: Path, source: Optional[SourceType] = None) -> Session:
    """根据文件扩展名分发到对应解析器（spec FR-IMPORT-01）.

    Args:
        path: 文件路径
        source: 可选数据源覆盖，None 时使用各 parser 的默认值

    Returns:
        解析后的 Session（含 raw_file_hash、raw_file_path）

    Raises:
        ImportParseError: 扩展名不支持或解析失败
    """
    ext = path.suffix.lower()
    if ext not in SUPPORTED_IMPORT_EXT:
        raise ImportParseError(
            f"不支持的文件扩展名: {ext}，支持: {', '.join(SUPPORTED_IMPORT_EXT)}"
        )

    parser_map: dict[str, Callable[..., Session]] = {
        ".fit": parse_fit,
        ".gpx": parse_gpx,
        ".csv": parse_csv,
        ".tcx": parse_tcx,
        ".xml": parse_xml,
    }

    parser = parser_map[ext]
    if source is not None:
        return parser(path, source=source)
    return parser(path)
