"""
Health monitor — periodic health checks, metrics, and alerting.
"""

import json
import time
from pathlib import Path
from datetime import datetime

from loguru import logger

from mcp_cli.core.config import get_mcp_home


class HealthMonitor:
    """Monitors MCP server health and stores metrics."""

    def __init__(self):
        self._metrics_db = get_mcp_home() / "cache" / "health" / "metrics.jsonl"
        self._metrics_db.parent.mkdir(parents=True, exist_ok=True)

    async def record_health(self, server_id: str, health: dict) -> None:
        """Record a health check result to the metrics store."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "server_id": server_id,
            "status": health.get("status", "unknown"),
            "latency_ms": health.get("latency_ms", 0),
            "error": health.get("error"),
        }
        try:
            with open(self._metrics_db, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.warning(f"[health] Failed to record metric: {e}")

    def get_recent_metrics(self, server_id: str | None = None, limit: int = 100) -> list[dict]:
        """Retrieve recent health metrics."""
        if not self._metrics_db.exists():
            return []

        entries = []
        try:
            with open(self._metrics_db, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if server_id and entry.get("server_id") != server_id:
                            continue
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.warning(f"[health] Failed to read metrics: {e}")

        return entries[-limit:]

    def get_summary(self, server_id: str) -> dict:
        """Get health summary for a server."""
        metrics = self.get_recent_metrics(server_id, limit=50)
        if not metrics:
            return {"server_id": server_id, "status": "unknown", "avg_latency_ms": 0, "uptime": 0}

        healthy_count = sum(1 for m in metrics if m.get("status") == "healthy")
        total_count = len(metrics)
        latencies = [m.get("latency_ms", 0) for m in metrics if m.get("latency_ms")]

        return {
            "server_id": server_id,
            "status": "healthy" if healthy_count == total_count else "degraded" if healthy_count > 0 else "down",
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "uptime": healthy_count / total_count if total_count > 0 else 0,
            "samples": total_count,
            "healthy_samples": healthy_count,
        }

    def get_all_summaries(self) -> list[dict]:
        """Get health summaries for all servers."""
        if not self._metrics_db.exists():
            return []

        server_ids = set()
        try:
            with open(self._metrics_db, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        sid = entry.get("server_id")
                        if sid:
                            server_ids.add(sid)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

        return [self.get_summary(sid) for sid in sorted(server_ids)]
