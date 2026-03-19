#!/usr/bin/env python3
"""Research session manager — create, load, save, and query sessions."""

import json
import sys
from datetime import datetime
from pathlib import Path

SESSIONS_DIR = Path(__file__).resolve().parent.parent / "data" / "sessions"


def get_sessions_dir() -> Path:
    """Return the sessions directory, creating it if needed."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    return SESSIONS_DIR


def _make_session_id() -> str:
    """Generate a unique session ID from the current timestamp."""
    base = datetime.now().strftime("ses_%Y%m%d_%H%M%S")
    sessions_dir = get_sessions_dir()
    if not (sessions_dir / f"{base}.json").exists():
        return base
    # Append a suffix if the base ID already exists
    for suffix in range(1, 100):
        candidate = f"{base}_{suffix}"
        if not (sessions_dir / f"{candidate}.json").exists():
            return candidate
    return base  # fallback (극히 드문 경우)


def _now_iso() -> str:
    """Return current time as ISO-8601 string (no microseconds)."""
    return datetime.now().replace(microsecond=0).isoformat()


def create_session(topic: str) -> dict:
    """Create a new session and save it to disk."""
    now = _now_iso()
    session = {
        "id": _make_session_id(),
        "topic": topic,
        "created_at": now,
        "updated_at": now,
        "status": "active",
        "notebook_id": None,
        "notebook_url": None,
        "searches": [],
        "sources": [],
        "questions": [],
    }
    save_session(session)
    return session


def load_session(session_id: str) -> dict:
    """Load a session from its JSON file."""
    path = get_sessions_dir() / f"{session_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Session not found: {session_id}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Session file is corrupted: {path}\n"
            f"Fix the JSON manually or delete the file to discard: {exc}"
        ) from exc


def save_session(session: dict) -> None:
    """Write a session dict to its JSON file."""
    path = get_sessions_dir() / f"{session['id']}.json"
    path.write_text(
        json.dumps(session, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def list_sessions(status: str | None = None) -> list[dict]:
    """List sessions, optionally filtered by status. Most recent first."""
    sessions = []
    for path in get_sessions_dir().glob("ses_*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if status is None or data.get("status") == status:
            sessions.append(data)
    sessions.sort(key=lambda s: s.get("updated_at", ""), reverse=True)
    return sessions


def add_search(session_id: str, search_info: dict) -> None:
    """Append a search record to the session."""
    session = load_session(session_id)
    search_info.setdefault("timestamp", _now_iso())
    session["searches"].append(search_info)
    session["updated_at"] = _now_iso()
    save_session(session)


def add_source(session_id: str, source_info: dict) -> None:
    """Append a source record to the session."""
    session = load_session(session_id)
    source_info.setdefault("added_at", _now_iso())
    session["sources"].append(source_info)
    session["updated_at"] = _now_iso()
    save_session(session)


def set_notebook(session_id: str, notebook_id: str, notebook_url: str | None = None) -> None:
    """Link a NotebookLM notebook to the session."""
    session = load_session(session_id)
    session["notebook_id"] = notebook_id
    if notebook_url is not None:
        session["notebook_url"] = notebook_url
    session["updated_at"] = _now_iso()
    save_session(session)


def add_question(session_id: str, question_info: dict) -> None:
    """Append a question record to the session."""
    session = load_session(session_id)
    question_info.setdefault("timestamp", _now_iso())
    session["questions"].append(question_info)
    session["updated_at"] = _now_iso()
    save_session(session)


def close_session(session_id: str) -> None:
    """Mark a session as closed."""
    session = load_session(session_id)
    session["status"] = "closed"
    session["updated_at"] = _now_iso()
    save_session(session)


def show_session(session_id: str) -> str:
    """Return a human-readable summary of a session."""
    s = load_session(session_id)
    lines = [
        f"Session: {s['id']}",
        f"Topic:   {s['topic']}",
        f"Status:  {s['status']}",
        f"Created: {s['created_at']}",
        f"Updated: {s['updated_at']}",
    ]
    if s.get("notebook_id"):
        lines.append(f"Notebook: {s['notebook_id']}")
    if s.get("notebook_url"):
        lines.append(f"URL:      {s['notebook_url']}")

    if s["searches"]:
        lines.append(f"\nSearches ({len(s['searches'])}):")
        for sr in s["searches"]:
            lines.append(
                f"  [{sr.get('source', '?')}] {sr.get('query', '')} "
                f"(results: {sr.get('results_count', '?')})"
            )

    if s["sources"]:
        lines.append(f"\nSources ({len(s['sources'])}):")
        for src in s["sources"]:
            lines.append(f"  [{src.get('source_type', '?')}] {src.get('title', src.get('url', '?'))}")

    if s["questions"]:
        lines.append(f"\nQuestions ({len(s['questions'])}):")
        for q in s["questions"]:
            lines.append(f"  - {q.get('question', '?')}")

    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────

def _parse_cli(argv: list[str]) -> None:
    """Minimal CLI dispatcher — no external deps."""
    if len(argv) < 2:
        _usage()
        sys.exit(1)

    cmd = argv[1]

    if cmd == "create":
        if len(argv) < 3:
            print("Usage: session_manager.py create <topic>", file=sys.stderr)
            sys.exit(1)
        topic = " ".join(argv[2:])
        session = create_session(topic)
        print(f"Created session: {session['id']}")
        print(f"Topic: {session['topic']}")

    elif cmd == "list":
        status = None
        if "--status" in argv:
            idx = argv.index("--status")
            if idx + 1 < len(argv):
                status = argv[idx + 1]
        sessions = list_sessions(status=status)
        if not sessions:
            print("No sessions found.")
            return
        print(f"{'ID':<25} {'Topic':<30} {'Status':<10} {'Sources':<8} {'Updated'}")
        print("-" * 90)
        for s in sessions:
            print(
                f"{s['id']:<25} {s['topic'][:28]:<30} {s['status']:<10} "
                f"{len(s.get('sources', [])):<8} {s.get('updated_at', '?')}"
            )

    elif cmd == "show":
        if len(argv) < 3:
            print("Usage: session_manager.py show <session_id>", file=sys.stderr)
            sys.exit(1)
        if "--json" in argv:
            print(json.dumps(load_session(argv[2]), indent=2, ensure_ascii=False))
        else:
            print(show_session(argv[2]))

    elif cmd == "add-search":
        if len(argv) < 3:
            print("Usage: session_manager.py add-search <session_id> --source X --query X --count N --results N", file=sys.stderr)
            sys.exit(1)
        info = _parse_kv_args(argv[3:], {"source", "query", "count", "results_count"})
        for int_key in ("count", "results_count"):
            if int_key in info:
                info[int_key] = int(info[int_key])
        add_search(argv[2], info)
        print("Search added.")

    elif cmd == "add-source":
        if len(argv) < 3:
            print("Usage: session_manager.py add-source <session_id> --url X --title X --type X", file=sys.stderr)
            sys.exit(1)
        info = _parse_kv_args(argv[3:], {"url", "title", "source_type"})
        # --type is an alias for source_type
        if "type" in info:
            info["source_type"] = info.pop("type")
        add_source(argv[2], info)
        print("Source added.")

    elif cmd == "set-notebook":
        if len(argv) < 4:
            print("Usage: session_manager.py set-notebook <session_id> <notebook_id> [notebook_url]", file=sys.stderr)
            sys.exit(1)
        url = argv[4] if len(argv) > 4 else None
        set_notebook(argv[2], argv[3], url)
        print("Notebook linked.")

    elif cmd == "add-question":
        if len(argv) < 3:
            print("Usage: session_manager.py add-question <session_id> --question X [--conversation-id X]", file=sys.stderr)
            sys.exit(1)
        info = _parse_kv_args(argv[3:], {"question", "conversation_id"})
        # --conversation-id → conversation_id
        if "conversation-id" in info:
            info["conversation_id"] = info.pop("conversation-id")
        add_question(argv[2], info)
        print("Question added.")

    elif cmd == "close":
        if len(argv) < 3:
            print("Usage: session_manager.py close <session_id>", file=sys.stderr)
            sys.exit(1)
        close_session(argv[2])
        print(f"Session {argv[2]} closed.")

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        _usage()
        sys.exit(1)


def _parse_kv_args(argv: list[str], known_keys: set[str]) -> dict:
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
        "Usage: session_manager.py <command> [args]\n\n"
        "Commands:\n"
        "  create <topic>          Create a new session\n"
        "  list [--status X]       List sessions\n"
        "  show <id> [--json]      Show session details\n"
        "  add-search <id> ...     Add a search record\n"
        "  add-source <id> ...     Add a source record\n"
        "  set-notebook <id> <nb>  Link a notebook\n"
        "  add-question <id> ...   Add a question record\n"
        "  close <id>              Close a session",
        file=sys.stderr,
    )


if __name__ == "__main__":
    _parse_cli(sys.argv)
