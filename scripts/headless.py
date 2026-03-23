#!/usr/bin/env python3
"""Headless execution utilities — auto source selection, retry, logging, alerts."""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PIPELINES_DIR = Path(__file__).resolve().parent.parent / "data" / "pipelines"
SCRIPTS_DIR = Path(__file__).resolve().parent

# ── Source mapping ──────────────────────────────────────────────────

SOURCE_MAP = {
    "youtube": {"script": "yt_search.py", "label": "YouTube 검색"},
    "web": {"script": "web_search.py", "label": "웹 검색"},
    "arxiv": {"script": "arxiv_search.py", "label": "arXiv 검색"},
    "community": {"script": "community_search.py", "label": "커뮤니티 검색"},
}

# Constraint keywords → preferred sources
_CONSTRAINT_PRIORITY = {
    "학술": ["arxiv", "web"],
    "논문": ["arxiv", "web"],
    "영상": ["youtube", "web"],
    "비디오": ["youtube", "web"],
    "커뮤니티": ["community", "web"],
    "reddit": ["community", "web"],
}


# ── Core functions ──────────────────────────────────────────────────

def select_sources(spec) -> list:
    """Select search sources based on spec's pipeline.tools and domain.constraints.

    Returns list of dicts: [{"name": "youtube", "script": "yt_search.py", "label": "..."}]
    """
    tools = spec.get("pipeline", {}).get("tools", [])
    constraints = spec.get("domain", {}).get("constraints", [])

    # If tools explicitly specified, use those
    if tools:
        selected = []
        for tool in tools:
            tool_lower = tool.lower()
            if tool_lower in SOURCE_MAP:
                entry = SOURCE_MAP[tool_lower]
                selected.append({"name": tool_lower, **entry})
        if selected:
            return selected

    # Check constraints for priority hints
    constraint_text = " ".join(constraints).lower()
    for keyword, preferred in _CONSTRAINT_PRIORITY.items():
        if keyword in constraint_text:
            return [
                {"name": name, **SOURCE_MAP[name]}
                for name in preferred
                if name in SOURCE_MAP
            ]

    # Default: all sources
    return [
        {"name": name, **info}
        for name, info in SOURCE_MAP.items()
    ]


def retry_with_skip(fn, args=None, kwargs=None, max_retries=2, timeout=30):
    """Execute fn with retry. Returns result on success, None on final failure.

    Args:
        fn: callable to execute
        args: positional args tuple
        kwargs: keyword args dict
        max_retries: number of retries after first failure
        timeout: not enforced on fn itself (caller should set subprocess timeout)

    Returns:
        fn result on success, None on final failure
    """
    args = args or ()
    kwargs = kwargs or {}
    last_error = None
    elapsed = 0

    for attempt in range(1 + max_retries):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_error = exc
            if attempt < max_retries:
                delay = min(2 ** attempt, timeout - elapsed)
                if delay <= 0:
                    break
                time.sleep(delay)
                elapsed += delay

    # All retries exhausted
    print(
        f"retry_with_skip: {fn.__name__} failed after {1 + max_retries} attempts: {last_error}",
        file=sys.stderr,
    )
    return None


def log_progress(session_id, phase, message, level="info") -> Path:
    """Append a structured log line to data/pipelines/{session_id}/progress.log.

    Format: [ISO-8601] [LEVEL] [phase] message
    Also writes a parallel JSON Lines entry to progress.jsonl.
    """
    pipeline_dir = PIPELINES_DIR / session_id
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    log_path = pipeline_dir / "progress.log"

    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    line = f"[{timestamp}] [{level.upper()}] [{phase}] {message}\n"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)

    # Parallel JSON Lines log
    log_progress_structured(session_id, phase, message, level=level)

    return log_path


def log_progress_structured(session_id, phase, message, level="info",
                            duration_ms=None, error=None):
    """Append a JSON Lines entry to data/pipelines/{session_id}/progress.jsonl."""
    pipeline_dir = PIPELINES_DIR / session_id
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = pipeline_dir / "progress.jsonl"

    entry = {
        "ts": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "session_id": session_id,
        "phase": phase,
        "level": level,
        "msg": message,
    }
    if duration_ms is not None:
        entry["duration_ms"] = duration_ms
    if error is not None:
        entry["error"] = error

    with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def phase_timer():
    """Return a timer dict. Call phase_timer_end() to get elapsed ms."""
    return {"start": time.monotonic()}


def phase_timer_end(timer):
    """Return elapsed milliseconds since phase_timer() was called."""
    return round((time.monotonic() - timer["start"]) * 1000)


def summarize_logs(session_id):
    """Summarize progress.jsonl: count errors, warnings, and phases.

    Returns a dict with totals and per-phase breakdown.
    """
    jsonl_path = PIPELINES_DIR / session_id / "progress.jsonl"
    if not jsonl_path.exists():
        return {"session_id": session_id, "total": 0, "errors": 0, "warnings": 0, "phases": {}}

    total = 0
    errors = 0
    warnings = 0
    phases = {}

    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        total += 1
        level = entry.get("level", "info")
        if level == "error":
            errors += 1
        elif level == "warning":
            warnings += 1

        phase = entry.get("phase", "unknown")
        if phase not in phases:
            phases[phase] = {"count": 0, "errors": 0, "warnings": 0}
        phases[phase]["count"] += 1
        if level == "error":
            phases[phase]["errors"] += 1
        elif level == "warning":
            phases[phase]["warnings"] += 1

    return {
        "session_id": session_id,
        "total": total,
        "errors": errors,
        "warnings": warnings,
        "phases": phases,
    }


def generate_dashboard(session_id):
    """Generate dashboard data for a pipeline session.

    Returns dict with phase statuses, costs, drift scores, errors.
    """
    pipeline_dir = PIPELINES_DIR / session_id
    if not pipeline_dir.exists():
        return {"session_id": session_id, "phases": [], "total_cost": 0, "errors": 0, "warnings": 0}

    # Cost data
    cost_log_path = pipeline_dir / "cost_log.json"
    cost_records = []
    total_cost = 0
    if cost_log_path.exists():
        try:
            cost_records = json.loads(cost_log_path.read_text(encoding="utf-8"))
            total_cost = sum(r.get("cost", 0) for r in cost_records)
        except (json.JSONDecodeError, ValueError):
            pass

    # Phase cost breakdown
    phase_costs = {}
    for r in cost_records:
        p = r.get("phase", -1)
        phase_costs[p] = phase_costs.get(p, 0) + r.get("cost", 0)

    # Drift trend from validation_history
    drift_trend = []
    history_path = pipeline_dir / "validation_history.json"
    if history_path.exists():
        try:
            records = json.loads(history_path.read_text(encoding="utf-8"))
            drift_trend = [r.get("drift_score", 1.0) for r in records]
        except (json.JSONDecodeError, ValueError):
            pass

    # Log summary
    log_summary = summarize_logs(session_id)

    return {
        "session_id": session_id,
        "total_cost": total_cost,
        "phase_costs": phase_costs,
        "drift_trend": drift_trend,
        "errors": log_summary.get("errors", 0),
        "warnings": log_summary.get("warnings", 0),
        "log_entries": log_summary.get("total", 0),
    }


def generate_summary(session_id):
    """Generate a pipeline execution summary and save to summary.json.

    Returns the summary dict.
    """
    from _io_utils import _atomic_write_json

    dashboard = generate_dashboard(session_id)
    pipeline_dir = PIPELINES_DIR / session_id

    # Backtrack count from drift_log
    backtrack_count = 0
    drift_log_path = pipeline_dir / "drift_log.json"
    if drift_log_path.exists():
        try:
            drift_records = json.loads(drift_log_path.read_text(encoding="utf-8"))
            backtrack_count = sum(1 for r in drift_records if r.get("action") == "backtrack")
        except (json.JSONDecodeError, ValueError):
            pass

    summary = {
        "session_id": session_id,
        "completed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "total_cost": dashboard["total_cost"],
        "phase_costs": dashboard["phase_costs"],
        "drift_trend": dashboard["drift_trend"],
        "backtrack_count": backtrack_count,
        "errors": dashboard["errors"],
        "warnings": dashboard["warnings"],
        "log_entries": dashboard["log_entries"],
    }

    pipeline_dir.mkdir(parents=True, exist_ok=True)
    summary_path = pipeline_dir / "summary.json"
    _atomic_write_json(summary_path, summary)

    return summary


def send_alert(title, body, webhook_url=None):
    """Send alert via macOS notification and/or webhook. Never raises.

    Args:
        title: alert title
        body: alert body
        webhook_url: Slack/Discord webhook URL (falls back to XLOOP_WEBHOOK_URL env var)
    """
    import subprocess

    # macOS local notification (disabled by default — set XLOOP_NOTIFY=1 to enable)
    if os.environ.get("XLOOP_NOTIFY"):
        try:
            subprocess.run(
                ["osascript", "-e",
                 f'display notification "{body}" with title "xLoop: {title}"'],
                timeout=5,
                capture_output=True,
            )
        except Exception:
            pass

    # Webhook notification
    url = webhook_url or os.environ.get("XLOOP_WEBHOOK_URL", "")
    if url:
        payload = json.dumps({"text": f"**{title}**\n{body}"})
        try:
            subprocess.run(
                ["curl", "-s", "-X", "POST",
                 "-H", "Content-Type: application/json",
                 "-d", payload, url],
                timeout=10,
                capture_output=True,
            )
        except Exception:
            pass


# ── CLI ─────────────────────────────────────────────────────────────

def _parse_cli(argv) -> None:
    if len(argv) < 2:
        _usage()
        sys.exit(1)

    cmd = argv[1]

    if cmd == "select-sources":
        if len(argv) < 3:
            print("Usage: headless.py select-sources <session_id>", file=sys.stderr)
            sys.exit(1)
        session_id = argv[2]
        spec = _load_spec(session_id)
        sources = select_sources(spec)
        for s in sources:
            print(f"  {s['name']}: {s['label']} ({s['script']})")

    elif cmd == "log":
        if len(argv) < 5:
            print("Usage: headless.py log <session_id> <phase> <message>", file=sys.stderr)
            sys.exit(1)
        session_id = argv[2]
        phase = argv[3]
        message = " ".join(argv[4:])
        level = "info"
        if "--level" in argv:
            idx = argv.index("--level")
            if idx + 1 < len(argv):
                level = argv[idx + 1]
                message = " ".join(
                    a for i, a in enumerate(argv[4:], 4)
                    if i != idx and i != idx + 1
                )
        path = log_progress(session_id, phase, message, level=level)
        print(f"Logged to {path}")

    elif cmd == "alert":
        if len(argv) < 4:
            print("Usage: headless.py alert <title> <body> [--webhook URL]", file=sys.stderr)
            sys.exit(1)
        title = argv[2]
        body = argv[3]
        webhook = None
        if "--webhook" in argv:
            idx = argv.index("--webhook")
            if idx + 1 < len(argv):
                webhook = argv[idx + 1]
        send_alert(title, body, webhook_url=webhook)
        print("Alert sent.")

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        _usage()
        sys.exit(1)


def _load_spec(session_id) -> dict:
    """Load spec.json for a session (lazy import to avoid circular deps)."""
    spec_path = PIPELINES_DIR / session_id / "spec.json"
    if not spec_path.exists():
        print(f"spec.json not found for session {session_id}", file=sys.stderr)
        return {}
    return json.loads(spec_path.read_text(encoding="utf-8"))


def _usage() -> None:
    print(
        "Usage: headless.py <command> [args]\n\n"
        "Commands:\n"
        "  select-sources <session_id>        Show auto-selected sources\n"
        "  log <session_id> <phase> <message>  Log progress\n"
        "  alert <title> <body> [--webhook URL]  Send alert",
        file=sys.stderr,
    )


if __name__ == "__main__":
    _parse_cli(sys.argv)
