#!/usr/bin/env python3
"""
Structured JSON-lines logger for MCP tool calls.

Logs every tools/call request to data/logs/mcp-requests-YYYY-MM-DD.jsonl
with: timestamp, tool_name, query, filters, result_count, latency_ms, error.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class RequestLogger:
    """Structured JSON-lines logger for MCP tool calls."""

    def __init__(self, log_dir: str = "./data/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_path(self) -> Path:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.log_dir / f"mcp-requests-{date_str}.jsonl"

    def log_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result_count: Optional[int],
        latency_ms: float,
        error: Optional[str] = None,
    ):
        """Log a single tool call to the daily JSONL file."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool_name": tool_name,
            "query": arguments.get("query"),
            "filters": {
                k: v for k, v in arguments.items()
                if k not in ("query", "limit")
            } or None,
            "limit": arguments.get("limit"),
            "result_count": result_count,
            "latency_ms": round(latency_ms, 2),
            "error": error,
        }

        log_path = self._get_log_path()
        try:
            with open(log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except OSError:
            pass  # Don't let logging failures break the server
