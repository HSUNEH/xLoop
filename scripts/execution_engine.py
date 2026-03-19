#!/usr/bin/env python3
"""Execution Engine — Tool Registry + strategy.json 작업 실행 → execution.json 생성."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PIPELINES_DIR = Path(__file__).resolve().parent.parent / "data" / "pipelines"

# ── Tool Registry ────────────────────────────────────────────────────

_TOOL_REGISTRY = {}


def register_tool(name, fn):
    """Register a tool execution function.

    fn signature: fn(task, session_id) -> dict (artifact)
    """
    _TOOL_REGISTRY[name] = fn


def get_tool(name):
    """Look up a registered tool by name. Returns None if not found."""
    return _TOOL_REGISTRY.get(name)


def list_tools():
    """Return sorted list of registered tool names."""
    return sorted(_TOOL_REGISTRY.keys())


# ── Default tool stubs ───────────────────────────────────────────────

def _stub_claude(task, session_id):
    """Stub: Claude code/script generation."""
    return {
        "type": "text",
        "task_id": task["id"],
        "tool": "claude",
        "output": f"[stub] Claude output for: {task.get('title', task['id'])}",
    }


def _stub_dall_e(task, session_id):
    """Stub: DALL-E image generation."""
    return {
        "type": "image",
        "task_id": task["id"],
        "tool": "dall-e",
        "output": f"[stub] DALL-E image for: {task.get('title', task['id'])}",
    }


def _stub_flux(task, session_id):
    """Stub: Flux video generation."""
    return {
        "type": "video",
        "task_id": task["id"],
        "tool": "flux",
        "output": f"[stub] Flux video for: {task.get('title', task['id'])}",
    }


def _stub_notebooklm(task, session_id):
    """Stub: NotebookLM document generation."""
    return {
        "type": "document",
        "task_id": task["id"],
        "tool": "notebooklm",
        "output": f"[stub] NotebookLM doc for: {task.get('title', task['id'])}",
    }


def _stub_web_search(task, session_id):
    """Stub: Web search execution."""
    return {
        "type": "search_result",
        "task_id": task["id"],
        "tool": "web_search",
        "output": f"[stub] Web search for: {task.get('title', task['id'])}",
    }


def _register_defaults():
    """Register all default tool stubs."""
    register_tool("claude", _stub_claude)
    register_tool("dall-e", _stub_dall_e)
    register_tool("flux", _stub_flux)
    register_tool("notebooklm", _stub_notebooklm)
    register_tool("web_search", _stub_web_search)


# Auto-register on import
_register_defaults()


# ── Helpers ──────────────────────────────────────────────────────────

def _now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ── Core functions ───────────────────────────────────────────────────

def execute_task(task, session_id):
    """Execute a single task using the Tool Registry.

    Args:
        task: dict with at least {id, tool} keys
        session_id: pipeline session ID

    Returns:
        dict: {task_id, tool, status, artifact|error}
    """
    from headless import log_progress, retry_with_skip

    task_id = task["id"]
    tool_name = task.get("tool", "claude")
    fn = get_tool(tool_name)

    if fn is None:
        log_progress(session_id, "execution", f"Unknown tool: {tool_name} for {task_id}", level="error")
        return {
            "task_id": task_id,
            "tool": tool_name,
            "status": "failed",
            "error": f"Unknown tool: {tool_name}",
        }

    log_progress(session_id, "execution", f"Running {task_id} with {tool_name}")

    result = retry_with_skip(fn, args=(task, session_id), max_retries=2, timeout=30)

    if result is None:
        log_progress(session_id, "execution", f"Failed: {task_id}", level="error")
        return {
            "task_id": task_id,
            "tool": tool_name,
            "status": "failed",
            "error": f"Tool {tool_name} failed after retries",
        }

    log_progress(session_id, "execution", f"Done: {task_id}")
    return {
        "task_id": task_id,
        "tool": tool_name,
        "status": "done",
        "artifact": result,
    }


def run_execution(session_id):
    """Load strategy.json, execute all tasks, save execution.json.

    Returns:
        dict: execution output (EXECUTION_SCHEMA)
    """
    from headless import log_progress
    from pipeline_schema import (
        create_execution,
        load_phase_output,
        save_phase_output,
        validate_execution,
    )

    log_progress(session_id, "execution", "Phase 3 시작")

    # Load strategy
    strategy = load_phase_output("strategy", session_id)
    tasks = strategy.get("tasks", [])

    if not tasks:
        print("경고: strategy에 작업이 없습니다.", file=sys.stderr)

    # Execute tasks
    artifacts = []
    tasks_completed = 0
    tasks_failed = 0

    for task in tasks:
        result = execute_task(task, session_id)
        artifacts.append(result)

        if result["status"] == "done":
            tasks_completed += 1
        else:
            tasks_failed += 1

    # Build execution output
    execution = create_execution(session_id)
    execution["completed_at"] = _now_iso()
    execution["artifacts"] = artifacts
    execution["tasks_completed"] = tasks_completed
    execution["tasks_failed"] = tasks_failed

    # Validate
    validation = validate_execution(execution)
    if not validation["valid"]:
        print(f"검증 실패: {validation['missing']}", file=sys.stderr)

    # Save
    save_phase_output(execution, "execution", session_id)
    log_progress(session_id, "execution", f"Phase 3 완료: {tasks_completed} done, {tasks_failed} failed")

    return execution


def get_execution_status(session_id):
    """Load execution.json and return status summary.

    Returns:
        dict: {session_id, tasks_completed, tasks_failed, total, status}
    """
    from pipeline_schema import load_phase_output

    execution = load_phase_output("execution", session_id)
    total = execution["tasks_completed"] + execution["tasks_failed"]
    all_done = execution["tasks_failed"] == 0 and total > 0

    return {
        "session_id": session_id,
        "tasks_completed": execution["tasks_completed"],
        "tasks_failed": execution["tasks_failed"],
        "total": total,
        "status": "success" if all_done else "partial",
        "completed_at": execution.get("completed_at"),
    }


def show_execution(execution):
    """Print execution summary in human-readable format."""
    print(f"Session: {execution.get('session_id', '?')}")
    print(f"Completed: {execution.get('tasks_completed', 0)}")
    print(f"Failed: {execution.get('tasks_failed', 0)}")

    cost = execution.get("total_cost")
    if cost is not None:
        print(f"Total cost: {cost}")

    print()
    for item in execution.get("artifacts", []):
        status_mark = {"done": "✅", "failed": "❌"}.get(item.get("status"), "⚪")
        print(f"  {status_mark} [{item.get('task_id', '?')}] {item.get('tool', '?')}: {item.get('status', '?')}")
        if item.get("error"):
            print(f"     Error: {item['error']}")


# ── CLI ──────────────────────────────────────────────────────────────

def _parse_cli(argv):
    """Minimal CLI dispatcher."""
    if len(argv) < 2:
        _usage()
        sys.exit(1)

    cmd = argv[1]

    if cmd == "run":
        if len(argv) < 3:
            print("Usage: execution_engine.py run <session_id>", file=sys.stderr)
            sys.exit(1)
        session_id = argv[2]
        execution = run_execution(session_id)
        print(json.dumps(execution, indent=2, ensure_ascii=False))

    elif cmd == "status":
        if len(argv) < 3:
            print("Usage: execution_engine.py status <session_id>", file=sys.stderr)
            sys.exit(1)
        session_id = argv[2]
        status = get_execution_status(session_id)
        print(json.dumps(status, indent=2, ensure_ascii=False))

    elif cmd == "tools":
        tools = list_tools()
        for tool in tools:
            print(f"  {tool}")

    elif cmd == "show":
        if len(argv) < 3:
            print("Usage: execution_engine.py show <session_id>", file=sys.stderr)
            sys.exit(1)
        from pipeline_schema import load_phase_output

        session_id = argv[2]
        data = load_phase_output("execution", session_id)
        show_execution(data)

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        _usage()
        sys.exit(1)


def _usage():
    print(
        "Usage: execution_engine.py <command> [args]\n\n"
        "Commands:\n"
        "  run <session_id>      Execute strategy tasks\n"
        "  status <session_id>   Show execution status\n"
        "  tools                 List registered tools\n"
        "  show <session_id>     Show execution summary",
        file=sys.stderr,
    )


if __name__ == "__main__":
    _parse_cli(sys.argv)
