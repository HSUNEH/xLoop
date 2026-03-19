#!/usr/bin/env python3
"""Loop engine — manage research loop state within sessions."""

import json
import sys
from datetime import datetime
from pathlib import Path

SESSIONS_DIR = Path(__file__).resolve().parent.parent / "data" / "sessions"


def _get_sessions_dir() -> Path:
    """Return the sessions directory, creating it if needed."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    return SESSIONS_DIR


def _now_iso() -> str:
    """Return current time as ISO-8601 string (no microseconds)."""
    return datetime.now().replace(microsecond=0).isoformat()


def _load_session(session_id: str) -> dict:
    """Load a session from its JSON file."""
    path = _get_sessions_dir() / f"{session_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Session not found: {session_id}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Session file is corrupted: {path}: {exc}") from exc


def _save_session(session: dict) -> None:
    """Write a session dict to its JSON file."""
    path = _get_sessions_dir() / f"{session['id']}.json"
    path.write_text(
        json.dumps(session, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def start_loop(session_id: str, initial_query: str, max_iterations: int = 3) -> dict:
    """Initialize loop state on a session. Returns the loop dict."""
    session = _load_session(session_id)

    if "loop" in session and session["loop"] is not None:
        raise ValueError(f"Session {session_id} already has a loop")

    loop = {
        "status": "running",
        "max_iterations": max_iterations,
        "current_iteration": 0,
        "initial_query": initial_query,
        "iterations": [],
        "covered_topics": [],
        "all_queries": [initial_query],
    }

    session["loop"] = loop
    session["updated_at"] = _now_iso()
    _save_session(session)
    return loop


def get_loop_state(session_id: str) -> dict:
    """Return the current loop state for a session."""
    session = _load_session(session_id)

    if "loop" not in session or session["loop"] is None:
        raise ValueError(f"Session {session_id} has no loop")

    return session["loop"]


def _require_running_loop(session: dict) -> dict:
    """Return the loop dict, raising if missing or not running."""
    loop = session.get("loop")
    if loop is None:
        raise ValueError(f"Session {session['id']} has no loop")
    if loop["status"] != "running":
        raise ValueError(f"Loop in session {session['id']} is not running (status: {loop['status']})")
    return loop


def add_iteration(
    session_id: str,
    queries: list[str],
    sources_added: int,
    findings: list[str],
    gaps: list[str],
) -> dict:
    """Record one loop iteration's results. Returns updated loop dict."""
    session = _load_session(session_id)
    loop = _require_running_loop(session)

    loop["current_iteration"] += 1
    iteration = {
        "number": loop["current_iteration"],
        "queries": queries,
        "sources_added": sources_added,
        "findings": findings,
        "gaps": gaps,
        "timestamp": _now_iso(),
    }
    loop["iterations"].append(iteration)
    loop["all_queries"].extend(queries)
    loop["covered_topics"].extend(findings)

    session["updated_at"] = _now_iso()
    _save_session(session)
    return loop


def check_termination(session_id: str) -> dict:
    """Check whether the loop should terminate. Returns {should_terminate, reason}."""
    session = _load_session(session_id)

    if session.get("loop") is None:
        raise ValueError(f"Session {session_id} has no loop")

    loop = session["loop"]

    # Condition 1: max iterations reached
    if loop["current_iteration"] >= loop["max_iterations"]:
        return {
            "should_terminate": True,
            "reason": f"Max iterations reached ({loop['max_iterations']})",
        }

    # Condition 2: no gaps in the last iteration
    if loop["iterations"]:
        last_gaps = loop["iterations"][-1].get("gaps", [])
        if len(last_gaps) == 0:
            return {
                "should_terminate": True,
                "reason": "No gaps found in the last iteration",
            }

    return {
        "should_terminate": False,
        "reason": f"Gaps remain, {loop['max_iterations'] - loop['current_iteration']} iterations left",
    }


def get_unused_queries(session_id: str, candidate_queries: list[str]) -> list[str]:
    """Filter out queries that have already been used in this loop."""
    session = _load_session(session_id)

    if session.get("loop") is None:
        raise ValueError(f"Session {session_id} has no loop")

    used = set(session["loop"]["all_queries"])
    return [q for q in candidate_queries if q not in used]


def end_loop(session_id: str) -> dict:
    """End the loop and mark it as completed. Returns updated loop dict."""
    session = _load_session(session_id)

    if session.get("loop") is None:
        raise ValueError(f"Session {session_id} has no loop")

    session["loop"]["status"] = "completed"
    session["updated_at"] = _now_iso()
    _save_session(session)
    return session["loop"]


# ── CLI ──────────────────────────────────────────────────────────────


def _parse_cli(argv: list[str]) -> None:
    """Minimal CLI dispatcher — no external deps."""
    if len(argv) < 2:
        _usage()
        sys.exit(1)

    cmd = argv[1]

    if cmd == "start":
        if len(argv) < 4:
            print("Usage: loop_engine.py start <session_id> <initial_query> [--max-iterations N]", file=sys.stderr)
            sys.exit(1)
        session_id = argv[2]
        initial_query = argv[3]
        max_iter = 3
        if "--max-iterations" in argv:
            idx = argv.index("--max-iterations")
            if idx + 1 < len(argv):
                max_iter = int(argv[idx + 1])
        result = start_loop(session_id, initial_query, max_iterations=max_iter)
        print(f"Loop started: {result['status']}")
        print(f"Query: {result['initial_query']}")
        print(f"Max iterations: {result['max_iterations']}")

    elif cmd == "status":
        if len(argv) < 3:
            print("Usage: loop_engine.py status <session_id> [--json]", file=sys.stderr)
            sys.exit(1)
        state = get_loop_state(argv[2])
        if "--json" in argv:
            print(json.dumps(state, indent=2, ensure_ascii=False))
        else:
            print(f"Status: {state['status']}")
            print(f"Iteration: {state['current_iteration']}/{state['max_iterations']}")
            print(f"Initial query: {state['initial_query']}")
            print(f"Total queries: {len(state['all_queries'])}")
            print(f"Topics covered: {len(state['covered_topics'])}")

    elif cmd == "add-iteration":
        if len(argv) < 3:
            print("Usage: loop_engine.py add-iteration <session_id> --queries-json '...' --sources-added N --findings-json '...' --gaps-json '...'", file=sys.stderr)
            sys.exit(1)
        session_id = argv[2]
        kv = _parse_kv_args(argv[3:])
        queries = json.loads(kv.get("queries-json", "[]"))
        sources_added = int(kv.get("sources-added", "0"))
        findings = json.loads(kv.get("findings-json", "[]"))
        gaps = json.loads(kv.get("gaps-json", "[]"))
        result = add_iteration(session_id, queries=queries, sources_added=sources_added, findings=findings, gaps=gaps)
        print(f"Iteration {result['current_iteration']} added.")

    elif cmd == "check":
        if len(argv) < 3:
            print("Usage: loop_engine.py check <session_id>", file=sys.stderr)
            sys.exit(1)
        result = check_termination(argv[2])
        terminate = "Yes" if result["should_terminate"] else "No"
        print(f"Should terminate: {terminate}")
        print(f"Reason: {result['reason']}")

    elif cmd == "filter-queries":
        if len(argv) < 3:
            print("Usage: loop_engine.py filter-queries <session_id> --candidates-json '...'", file=sys.stderr)
            sys.exit(1)
        kv = _parse_kv_args(argv[3:])
        candidates = json.loads(kv.get("candidates-json", "[]"))
        unused = get_unused_queries(argv[2], candidates)
        print(json.dumps(unused, ensure_ascii=False))

    elif cmd == "end":
        if len(argv) < 3:
            print("Usage: loop_engine.py end <session_id>", file=sys.stderr)
            sys.exit(1)
        result = end_loop(argv[2])
        print(f"Loop completed. Status: {result['status']}")

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        _usage()
        sys.exit(1)


def _parse_kv_args(argv: list[str]) -> dict:
    """Parse --key value pairs from argv."""
    result: dict = {}
    i = 0
    while i < len(argv):
        if argv[i].startswith("--") and i + 1 < len(argv):
            key = argv[i][2:]
            result[key] = argv[i + 1]
            i += 2
        else:
            i += 1
    return result


def _usage() -> None:
    print(
        "Usage: loop_engine.py <command> [args]\n\n"
        "Commands:\n"
        "  start <session_id> <query> [--max-iterations N]  Start a loop\n"
        "  status <session_id> [--json]                     Show loop status\n"
        "  add-iteration <session_id> ...                   Record an iteration\n"
        "  check <session_id>                               Check termination\n"
        "  filter-queries <session_id> --candidates-json ..  Filter used queries\n"
        "  end <session_id>                                 End the loop",
        file=sys.stderr,
    )


if __name__ == "__main__":
    _parse_cli(sys.argv)
