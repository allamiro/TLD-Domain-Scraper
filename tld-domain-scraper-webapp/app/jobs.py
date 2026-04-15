from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone

# In-memory job store  {job_id: dict}
# This is intentionally simple — no Redis/Celery needed for a single-worker app.
_jobs: dict[str, dict] = {}
_lock = threading.Lock()


def create_job(tlds: list[str]) -> str:
    job_id = str(uuid.uuid4())
    with _lock:
        _jobs[job_id] = {
            "id": job_id,
            "status": "pending",       # pending | running | done | error
            "tlds": tlds,
            "total_tlds": len(tlds),
            "tld_index": 0,            # which TLD we are on (0-based)
            "current_tld": None,
            "current_page": 0,
            "domains_found": 0,        # running total across all TLDs
            "domains_inserted": 0,
            "log": [],                 # last 200 log lines
            "started_at": None,
            "finished_at": None,
            "error": None,
        }
    return job_id


def get_job(job_id: str) -> dict | None:
    with _lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None


def update_job(job_id: str, **kwargs) -> None:
    with _lock:
        if job_id in _jobs:
            _jobs[job_id].update(kwargs)


def append_log(job_id: str, message: str) -> None:
    with _lock:
        if job_id in _jobs:
            ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
            _jobs[job_id]["log"].append(f"[{ts}] {message}")
            # Keep a rolling window so the response stays small
            _jobs[job_id]["log"] = _jobs[job_id]["log"][-200:]


def start_job(job_id: str) -> None:
    update_job(
        job_id,
        status="running",
        started_at=datetime.now(timezone.utc).isoformat(),
    )


def finish_job(job_id: str, inserted: int) -> None:
    update_job(
        job_id,
        status="done",
        domains_inserted=inserted,
        finished_at=datetime.now(timezone.utc).isoformat(),
    )


def fail_job(job_id: str, error: str) -> None:
    update_job(
        job_id,
        status="error",
        error=error,
        finished_at=datetime.now(timezone.utc).isoformat(),
    )
