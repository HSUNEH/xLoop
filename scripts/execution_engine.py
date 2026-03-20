#!/usr/bin/env python3
"""Execution Engine — Tool Registry + strategy.json 작업 실행 → execution.json 생성."""

import json
import socket
import subprocess
import sys
import time
import urllib.request
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


# ── Smoke Test ───────────────────────────────────────────────────────

_SMOKE_SERVER_TIMEOUT = 30  # 서버 기동 대기 (초)
_SMOKE_REQUEST_TIMEOUT = 10  # 엔드포인트 요청 타임아웃 (초)


def _find_free_port() -> int:
    """OS가 할당하는 사용 가능한 임시 포트를 반환한다."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _wait_for_server(port, timeout):
    """서버가 포트에서 응답할 때까지 대기한다. 성공하면 True."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def _check_endpoint(port, path, method="GET"):
    """단일 엔드포인트에 요청을 보내고 결과를 반환한다.

    Returns:
        dict: {path, method, status_code, passed, error}
    """
    url = f"http://127.0.0.1:{port}{path}"
    try:
        req = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(req, timeout=_SMOKE_REQUEST_TIMEOUT) as resp:
            return {
                "path": path,
                "method": method,
                "status_code": resp.status,
                "passed": resp.status < 500,
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        return {
            "path": path,
            "method": method,
            "status_code": exc.code,
            "passed": exc.code < 500,
            "error": None if exc.code < 500 else f"HTTP {exc.code}",
        }
    except Exception as exc:
        return {
            "path": path,
            "method": method,
            "status_code": None,
            "passed": False,
            "error": str(exc),
        }


def run_smoke_test(session_id, artifacts, strategy=None):
    """생성된 서비스를 임시 포트에서 기동하고 주요 엔드포인트를 테스트한다.

    Args:
        session_id: 파이프라인 세션 ID
        artifacts: execute_task() 결과 리스트
        strategy: strategy.json 데이터 (엔드포인트 목록 추출용)

    Returns:
        dict: {passed, server_started, port, endpoints, error}
              passed=True이면 모든 엔드포인트가 5xx 없이 응답.
              서버 기동 실패 시 passed=False, server_started=False.
    """
    from headless import log_progress

    log_progress(session_id, "smoke_test", "Smoke test 시작")

    # strategy에서 start_command와 endpoints 추출
    smoke_config = (strategy or {}).get("smoke_test", {})
    start_cmd = smoke_config.get("start_command")
    endpoints = smoke_config.get("endpoints", [])

    # start_command가 없으면 smoke test 스킵 (서버 없는 프로젝트)
    if not start_cmd:
        log_progress(session_id, "smoke_test", "start_command 미설정 — 스킵")
        return {
            "passed": True,
            "server_started": False,
            "port": None,
            "endpoints": [],
            "error": "start_command not configured — skipped",
        }

    # 기본 엔드포인트: 최소 health check
    if not endpoints:
        endpoints = [{"path": "/", "method": "GET"}]

    port = _find_free_port()
    # start_command 내 {port} 플레이스홀더 치환
    cmd_str = start_cmd.replace("{port}", str(port))

    # 서버 기동
    try:
        proc = subprocess.Popen(
            cmd_str.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as exc:
        log_progress(session_id, "smoke_test", f"서버 기동 실패: {exc}", level="error")
        return {
            "passed": False,
            "server_started": False,
            "port": port,
            "endpoints": [],
            "error": f"Server start failed: {exc}",
        }

    try:
        # 서버 응답 대기
        if not _wait_for_server(port, _SMOKE_SERVER_TIMEOUT):
            # 프로세스가 이미 종료했는지 확인 (런타임 에러)
            retcode = proc.poll()
            stderr_out = ""
            if retcode is not None:
                stderr_out = proc.stderr.read().decode("utf-8", errors="replace")[:500]
            log_progress(
                session_id, "smoke_test",
                f"서버 응답 타임아웃 (port={port}, retcode={retcode})",
                level="error",
            )
            return {
                "passed": False,
                "server_started": False,
                "port": port,
                "endpoints": [],
                "error": f"Server did not respond within {_SMOKE_SERVER_TIMEOUT}s. "
                         f"retcode={retcode}, stderr={stderr_out}",
            }

        log_progress(session_id, "smoke_test", f"서버 기동 완료 (port={port})")

        # 엔드포인트 테스트
        results = []
        for ep in endpoints:
            path = ep.get("path", "/")
            method = ep.get("method", "GET")
            result = _check_endpoint(port, path, method)
            results.append(result)

        all_passed = all(r["passed"] for r in results)
        passed_count = sum(1 for r in results if r["passed"])

        log_progress(
            session_id, "smoke_test",
            f"완료: {passed_count}/{len(results)} 통과, passed={all_passed}",
        )

        return {
            "passed": all_passed,
            "server_started": True,
            "port": port,
            "endpoints": results,
            "error": None,
        }

    finally:
        # 서버 프로세스 정리
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
            proc.wait(timeout=3)


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

    try:
        result = retry_with_skip(fn, args=(task, session_id), max_retries=2, timeout=30)
    except Exception as exc:
        log_progress(session_id, "execution", f"Exception: {task_id}: {exc}", level="error")
        return {
            "task_id": task_id,
            "tool": tool_name,
            "status": "failed",
            "error": str(exc),
        }

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

    # Smoke test
    smoke_result = run_smoke_test(session_id, artifacts, strategy=strategy)
    log_progress(session_id, "execution", f"Smoke test passed={smoke_result['passed']}")

    # Build execution output
    execution = create_execution(session_id)
    execution["completed_at"] = _now_iso()
    execution["artifacts"] = artifacts
    execution["tasks_completed"] = tasks_completed
    execution["tasks_failed"] = tasks_failed
    execution["smoke_test"] = smoke_result

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
