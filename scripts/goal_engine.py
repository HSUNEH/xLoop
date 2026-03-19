#!/usr/bin/env python3
"""Goal engine — manage goal definition loop for Phase 0 (Big Bang)."""

import json
import sys
from datetime import datetime
from pathlib import Path

PIPELINES_DIR = Path(__file__).resolve().parent.parent / "data" / "pipelines"


def _now_iso() -> str:
    """Return current time as ISO-8601 string (no microseconds)."""
    return datetime.now().replace(microsecond=0).isoformat()


def _get_pipeline_dir(session_id: str) -> Path:
    """Return the pipeline directory for a session, creating it if needed."""
    pipeline_dir = PIPELINES_DIR / session_id
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    return pipeline_dir


def _load_goal_state(session_id: str) -> dict:
    """Load goal loop state from goal_state.json."""
    path = _get_pipeline_dir(session_id) / "goal_state.json"
    if not path.exists():
        raise FileNotFoundError(f"Goal state not found: {session_id}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Goal state file is corrupted: {path}: {exc}") from exc


def _save_goal_state(session_id: str, state: dict) -> None:
    """Save goal loop state to goal_state.json."""
    path = _get_pipeline_dir(session_id) / "goal_state.json"
    path.write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# ── Core functions ──────────────────────────────────────────────────

def start_goal_loop(session_id: str) -> dict:
    """Initialize goal definition loop. Returns the goal state dict."""
    pipeline_dir = _get_pipeline_dir(session_id)
    state_path = pipeline_dir / "goal_state.json"

    if state_path.exists():
        raise ValueError(f"Goal loop already exists for session {session_id}")

    state = {
        "session_id": session_id,
        "status": "running",
        "current_iteration": 0,
        "iterations": [],
        "started_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    _save_goal_state(session_id, state)
    return state


def add_goal_iteration(
    session_id: str,
    questions: list[str],
    responses: list[str],
    spec_updates: dict,
    ambiguity: float,
) -> dict:
    """Record one goal-definition iteration. Returns updated state."""
    state = _load_goal_state(session_id)

    if state["status"] != "running":
        raise ValueError(f"Goal loop is not running (status: {state['status']})")

    state["current_iteration"] += 1
    iteration = {
        "number": state["current_iteration"],
        "questions": questions,
        "responses": responses,
        "spec_updates": spec_updates,
        "ambiguity": ambiguity,
        "timestamp": _now_iso(),
    }
    state["iterations"].append(iteration)
    state["updated_at"] = _now_iso()

    _save_goal_state(session_id, state)
    return state


def check_goal_termination(session_id: str, spec: dict) -> dict:
    """Check if the goal loop should terminate.

    Termination: ambiguity <= 0.2 AND all required fields filled.
    Returns {should_terminate, reason, ambiguity}.
    """
    from scripts.pipeline_spec import validate_spec, calculate_ambiguity

    validation = validate_spec(spec)
    ambiguity = validation["ambiguity"]
    missing = validation["missing"]
    has_quant = validation["has_quantitative_criteria"]

    if missing:
        return {
            "should_terminate": False,
            "reason": f"필수 필드 미충족: {', '.join(missing)}",
            "ambiguity": ambiguity,
        }

    if not has_quant:
        return {
            "should_terminate": False,
            "reason": "success_criteria에 정량 기준이 없습니다",
            "ambiguity": ambiguity,
        }

    if ambiguity > 0.2:
        return {
            "should_terminate": False,
            "reason": f"모호성 {ambiguity} > 0.2 — 추가 구체화 필요",
            "ambiguity": ambiguity,
        }

    return {
        "should_terminate": True,
        "reason": f"모호성 {ambiguity} ≤ 0.2, 모든 필수 필드 충족",
        "ambiguity": ambiguity,
    }


def get_next_questions(spec: dict) -> list[str]:
    """Generate question candidates based on unfilled/ambiguous fields."""
    questions = []
    goal = spec.get("goal", {})
    domain = spec.get("domain", {})
    pipeline = spec.get("pipeline", {})

    # Goal questions
    if not goal.get("deliverables"):
        questions.append("최종 산출물은 무엇인가요? (예: 보고서, 썸네일 3개, 영상 스크립트)")
    if not goal.get("success_criteria"):
        questions.append("성공 기준은 무엇인가요? 정량적으로 측정 가능한 기준을 최소 1개 포함해주세요. (예: 파일 3개, 1280x720, 유사도 70%)")
    elif not any(_has_number(c) for c in goal.get("success_criteria", [])):
        questions.append("현재 성공 기준이 모두 정성적입니다. 측정 가능한 기준을 하나 추가해주세요. (예: 파일 개수, 해상도, 글자 수)")
    if not goal.get("deadline"):
        questions.append("마감 기한이 있나요? (예: 2026-03-25, 없음)")

    # Domain questions
    if not domain.get("target"):
        questions.append("대상/타겟은 무엇인가요? (예: youtube.com/c/MrBeast, AI 에이전트 논문)")
    if not domain.get("constraints"):
        questions.append("제약 조건이 있나요? (예: 한국어만, 비용 $10 이하, 특정 포맷)")
    if not domain.get("references"):
        questions.append("참고할 레퍼런스가 있나요? (예: 경쟁사 사이트, 스타일 가이드, 기존 작업)")

    # Pipeline questions
    if not pipeline.get("tools"):
        questions.append("사용할 도구/소스가 있나요? (예: YouTube, arXiv, 웹 검색, NotebookLM)")

    return questions


def _has_number(text: str) -> bool:
    """Check if text contains a number."""
    import re
    return bool(re.search(r'\d+', text))


def end_goal_loop(session_id: str) -> dict:
    """End the goal loop and mark it as completed."""
    state = _load_goal_state(session_id)

    if state["status"] != "running":
        raise ValueError(f"Goal loop is not running (status: {state['status']})")

    state["status"] = "completed"
    state["updated_at"] = _now_iso()
    _save_goal_state(session_id, state)
    return state


# ── CLI ──────────────────────────────────────────────────────────────

def _parse_cli(argv: list[str]) -> None:
    """Minimal CLI dispatcher — no external deps."""
    if len(argv) < 2:
        _usage()
        sys.exit(1)

    cmd = argv[1]

    if cmd == "start":
        if len(argv) < 3:
            print("Usage: goal_engine.py start <session_id>", file=sys.stderr)
            sys.exit(1)
        state = start_goal_loop(argv[2])
        print(f"Goal loop started for session: {state['session_id']}")
        print(f"Status: {state['status']}")

    elif cmd == "status":
        if len(argv) < 3:
            print("Usage: goal_engine.py status <session_id> [--json]", file=sys.stderr)
            sys.exit(1)
        state = _load_goal_state(argv[2])
        if "--json" in argv:
            print(json.dumps(state, indent=2, ensure_ascii=False))
        else:
            print(f"Session: {state['session_id']}")
            print(f"Status: {state['status']}")
            print(f"Iteration: {state['current_iteration']}")
            print(f"Started: {state['started_at']}")
            print(f"Updated: {state['updated_at']}")

    elif cmd == "add-iteration":
        if len(argv) < 3:
            print(
                "Usage: goal_engine.py add-iteration <session_id> "
                "--questions-json '...' --responses-json '...' "
                "--spec-updates-json '...' --ambiguity N",
                file=sys.stderr,
            )
            sys.exit(1)
        kv = _parse_kv_args(argv[3:])
        questions = json.loads(kv.get("questions-json", "[]"))
        responses = json.loads(kv.get("responses-json", "[]"))
        spec_updates = json.loads(kv.get("spec-updates-json", "{}"))
        ambiguity = float(kv.get("ambiguity", "1.0"))
        state = add_goal_iteration(
            argv[2],
            questions=questions,
            responses=responses,
            spec_updates=spec_updates,
            ambiguity=ambiguity,
        )
        print(f"Iteration {state['current_iteration']} added. Ambiguity: {ambiguity}")

    elif cmd == "check":
        if len(argv) < 3:
            print("Usage: goal_engine.py check <session_id>", file=sys.stderr)
            sys.exit(1)
        from scripts.pipeline_spec import load_spec
        spec = load_spec(argv[2])
        result = check_goal_termination(argv[2], spec)
        terminate = "Yes" if result["should_terminate"] else "No"
        print(f"Should terminate: {terminate}")
        print(f"Reason: {result['reason']}")
        print(f"Ambiguity: {result['ambiguity']}")

    elif cmd == "end":
        if len(argv) < 3:
            print("Usage: goal_engine.py end <session_id>", file=sys.stderr)
            sys.exit(1)
        state = end_goal_loop(argv[2])
        print(f"Goal loop completed. Status: {state['status']}")

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
        "Usage: goal_engine.py <command> [args]\n\n"
        "Commands:\n"
        "  start <session_id>                Start a goal loop\n"
        "  status <session_id> [--json]      Show goal loop status\n"
        "  add-iteration <session_id> ...    Record an iteration\n"
        "  check <session_id>                Check termination condition\n"
        "  end <session_id>                  End the goal loop",
        file=sys.stderr,
    )


if __name__ == "__main__":
    _parse_cli(sys.argv)
