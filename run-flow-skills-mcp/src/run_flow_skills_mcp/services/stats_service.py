"""统计与导出编排服务（spec FR-STATS-01/02, 7.6）.

编排 storage 多维聚合 + 导出。
导出前必须用户确认（interaction-rules.md 第 5 条）——
本 service 仅执行导出，确认由调用方（Skill/Web）处理。
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


class StatsService:
    """统计与导出编排服务."""

    def __init__(self, parquet_store: ParquetStore, json_store: JsonStore) -> None:
        self.parquet_store = parquet_store
        self.json_store = json_store

    def get_statistics(
        self,
        dimension: str,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict:
        """按维度分组统计.

        Args:
            dimension: 分组维度，支持
                by_source / by_week / by_month / by_year / by_pace_zone / by_distance_range
            date_from / date_to: 可选日期过滤（YYYY-MM-DD）

        Returns:
            {groups: [{key, count, total_distance_km, ...}], dimension}
            无效 dimension 或无数据时 groups 为空列表。
        """
        sessions = self.parquet_store.query_sessions(date_from=date_from, date_to=date_to)
        if not sessions:
            return {"groups": [], "dimension": dimension}

        metrics = self.parquet_store.query_metrics([s.session_id for s in sessions])
        metrics_map = {m.session_id: m for m in metrics}

        groups: dict[str, list] = defaultdict(list)

        for s in sessions:
            m = metrics_map.get(s.session_id)
            if dimension == "by_source":
                key = s.source
            elif dimension == "by_week":
                iso_week = s.activity_date.isocalendar()
                key = f"{iso_week.year}-W{iso_week.week:02d}"
            elif dimension == "by_month":
                key = s.activity_date.strftime("%Y-%m")
            elif dimension == "by_year":
                key = str(s.activity_date.year)
            elif dimension == "by_pace_zone":
                key = m.pace_zone if m and m.pace_zone else "unknown"
            elif dimension == "by_distance_range":
                km = s.distance_m / 1000
                if km < 5:
                    key = "<5k"
                elif km < 10:
                    key = "5-10k"
                elif km < 21:
                    key = "10-21k"
                elif km < 42:
                    key = "21-42k"
                else:
                    key = ">=42k"
            else:
                # 未知维度直接返回空，避免误聚合
                return {"groups": [], "dimension": dimension}
            groups[key].append((s, m))

        result_groups = []
        for key, items in groups.items():
            total_distance = sum(s.distance_m for s, _ in items) / 1000.0
            total_duration = sum(s.duration_s for s, _ in items)
            avg_pace = total_duration / total_distance if total_distance > 0 else 0
            total_tss = sum(m.tss for _, m in items if m and m.tss)
            vdots = [m.vdot for _, m in items if m and m.vdot]
            avg_vdot = sum(vdots) / len(vdots) if vdots else None

            result_groups.append(
                {
                    "key": key,
                    "count": len(items),
                    "total_distance_km": round(total_distance, 2),
                    "total_duration_s": total_duration,
                    "avg_pace_s_per_km": round(avg_pace, 2),
                    "total_tss": round(total_tss, 2),
                    "avg_vdot": round(avg_vdot, 2) if avg_vdot else None,
                }
            )

        return {"groups": result_groups, "dimension": dimension}

    def export_data(
        self,
        export_format: str,
        filters: dict | None = None,
        include_ai_logs: bool = False,
    ) -> dict:
        """导出数据为 CSV/JSON/Parquet/MD.

        Args:
            export_format: csv / json / parquet / md
            filters: 可选 {date_from, date_to, source}
            include_ai_logs: 是否合并决策日志到导出数据

        Returns:
            {file_path, rows_count, format}；不支持的格式返回 error 字段。
        """
        filters = filters or {}
        sessions = self.parquet_store.query_sessions(
            date_from=filters.get("date_from"),
            date_to=filters.get("date_to"),
            source=filters.get("source"),
        )
        metrics = self.parquet_store.query_metrics([s.session_id for s in sessions])
        metrics_map = {m.session_id: m for m in metrics}

        rows: list[dict] = []
        for s in sessions:
            m = metrics_map.get(s.session_id)
            rows.append(
                {
                    "session_id": s.session_id,
                    "activity_date": s.activity_date.isoformat(),
                    "distance_m": s.distance_m,
                    "duration_s": s.duration_s,
                    "avg_pace_s_per_km": s.avg_pace_s_per_km,
                    "avg_hr": s.avg_hr,
                    "source": s.source,
                    "vdot": m.vdot if m else None,
                    "tss": m.tss if m else None,
                    "pace_zone": m.pace_zone if m else None,
                }
            )

        if include_ai_logs:
            decisions = self.json_store.query_decisions(
                date_from=filters.get("date_from"),
                date_to=filters.get("date_to"),
            )
            for d in decisions:
                rows.append(
                    {
                        "type": "decision_log",
                        "decision_id": d.decision_id,
                        "timestamp": d.timestamp.isoformat(),
                        "decision_type": d.decision_type,
                        "reasoning": d.reasoning,
                        "recommendation": d.recommendation,
                        "confidence": d.confidence,
                    }
                )

        # 导出目录：data/exports/
        export_dir = self.parquet_store.data_dir / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        file_path = export_dir / f"export_{timestamp}.{export_format}"

        if export_format == "csv":
            self._write_csv(file_path, rows)
        elif export_format == "json":
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(rows, f, ensure_ascii=False, indent=2, default=str)
        elif export_format == "parquet":
            import polars as pl

            df = pl.DataFrame(rows) if rows else pl.DataFrame()
            df.write_parquet(file_path)
        elif export_format == "md":
            self._write_markdown(file_path, rows)
        else:
            return {
                "file_path": "",
                "rows_count": 0,
                "format": export_format,
                "error": f"不支持的格式: {export_format}",
            }

        return {
            "file_path": str(file_path),
            "rows_count": len(rows),
            "format": export_format,
        }

    def _write_csv(self, path: Path, rows: list[dict]) -> None:
        """写 CSV（取所有字段并集作为表头）."""
        if not rows:
            path.write_text("", encoding="utf-8")
            return
        # 统一字段（取并集，保留首次出现顺序）
        fieldnames: list[str] = []
        for r in rows:
            for k in r.keys():
                if k not in fieldnames:
                    fieldnames.append(k)
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

    def _write_markdown(self, path: Path, rows: list[dict]) -> None:
        """写 Markdown 表格（以首行字段为表头）."""
        if not rows:
            path.write_text("# 导出报告\n\n无数据\n", encoding="utf-8")
            return
        fieldnames = list(rows[0].keys())
        lines = ["# 训练数据导出报告", "", f"共 {len(rows)} 条记录", ""]
        lines.append("| " + " | ".join(fieldnames) + " |")
        lines.append("| " + " | ".join("---" for _ in fieldnames) + " |")
        for r in rows:
            lines.append("| " + " | ".join(str(r.get(f, "")) for f in fieldnames) + " |")
        path.write_text("\n".join(lines), encoding="utf-8")
