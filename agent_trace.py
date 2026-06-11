"""
Agent Trace recorder used to produce auditable, step-by-step evidence of the
generation pipeline (Gemma 4 Function Calling -> Tool Call Parser -> Validator
-> Self-Correction -> Asset Grounding -> Preview -> Export -> Report).

Kept intentionally tiny: a dict-backed recorder with start/end/add_step/to_list,
so it can be dropped into the existing _run_generation flow without changing
its control structure.
"""
from __future__ import annotations

import time
from datetime import datetime

# Recommended status values (UI may render any string, these are just the
# ones the rest of the pipeline is expected to use).
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_SUCCESS = "success"
STATUS_WARNING = "warning"
STATUS_ERROR = "error"
STATUS_SKIPPED = "skipped"


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="milliseconds")


class TraceRecorder:
    """Records ordered pipeline steps with timing for the Agent Trace panel."""

    def __init__(self) -> None:
        self._steps: dict[str, dict] = {}
        self._order: list[str] = []
        self._t0: dict[str, float] = {}

    def start(self, step_id: str, title: str, message: str = "", metadata: dict | None = None) -> dict:
        if step_id not in self._steps:
            self._order.append(step_id)
        self._t0[step_id] = time.monotonic()
        step = {
            "step_id": step_id,
            "title": title,
            "status": STATUS_RUNNING,
            "message": message,
            "started_at": _now_iso(),
            "ended_at": None,
            "duration_ms": 0,
            "metadata": dict(metadata or {}),
        }
        self._steps[step_id] = step
        return step

    def end(self, step_id: str, status: str = STATUS_SUCCESS, message: str | None = None,
            metadata: dict | None = None) -> dict:
        step = self._steps.get(step_id) or self.start(step_id, step_id)
        step["ended_at"] = _now_iso()
        t0 = self._t0.get(step_id)
        step["duration_ms"] = int((time.monotonic() - t0) * 1000) if t0 is not None else 0
        step["status"] = status
        if message is not None:
            step["message"] = message
        if metadata:
            step["metadata"].update(metadata)
        return step

    def add_step(self, step_id: str, title: str, status: str = STATUS_SKIPPED,
                  message: str = "", metadata: dict | None = None, duration_ms: int = 0) -> dict:
        """Add a fully-formed step in one call (e.g. for skipped/static steps)."""
        if step_id not in self._steps:
            self._order.append(step_id)
        now = _now_iso()
        step = {
            "step_id": step_id,
            "title": title,
            "status": status,
            "message": message,
            "started_at": now,
            "ended_at": now,
            "duration_ms": duration_ms,
            "metadata": dict(metadata or {}),
        }
        self._steps[step_id] = step
        return step

    def to_list(self) -> list[dict]:
        return [dict(self._steps[step_id]) for step_id in self._order]
