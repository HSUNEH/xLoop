#!/usr/bin/env python3
"""Drift Checker — Phase 5: drift_score 기반 파이프라인 흐름 제어.

drift == 0       → "complete"  (통과, 파이프라인 종료)
0 < drift ≤ 0.3  → "backtrack" (Phase 2 전략 재수립)
drift > 0.3      → "restart"   (Phase 0 복귀 + 알림)
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PIPELINES_DIR = Path(__file__).resolve().parent.parent / "data" / "pipelines"

DRIFT_THRESHOLD = 0.3


# ── Helpers ─────────────────────────────────────────────────────────

def _now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _get_pipeline_dir(session_id):
    return PIPELINES_DIR / session_id


# ── Core functions ──────────────────────────────────────────────────

def check_drift(session_id):
    """validation.json에서 drift_score와 관련 정보를 읽는다.

    Returns:
        dict: {"drift_score": float, "passed": bool, "action": str, "session_id": str}
    """
    from pipeline_schema import load_phase_output

    validation = load_phase_output("validation", session_id)

    return {
        "session_id": session_id,
        "drift_score": validation.get("drift_score", 1.0),
        "passed": validation.get("passed", False),
        "action": validation.get("action", "pending"),
        "feedback": validation.get("feedback", []),
    }


def decide_action(drift_score):
    """drift_score에 따른 행동 결정.

    Returns:
        str: "complete" | "backtrack" | "restart"
    """
    if drift_score == 0.0:
        return "complete"
    if drift_score <= DRIFT_THRESHOLD:
        return "backtrack"
    return "restart"


def _log_drift(session_id, drift_score, action, reason=""):
    """drift_log.json에 드리프트 기록을 추가한다."""
    pipeline_dir = _get_pipeline_dir(session_id)
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    log_path = pipeline_dir / "drift_log.json"

    records = []
    if log_path.exists():
        try:
            records = json.loads(log_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            records = []

    records.append({
        "timestamp": _now_iso(),
        "drift_score": drift_score,
        "action": action,
        "reason": reason,
    })

    log_path.write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return log_path


def execute_backtrack(session_id):
    """Phase 2로 백트래킹: strategy.json 삭제 → Phase 2 재트리거.

    Returns:
        dict: {"action": "backtrack", "deleted": str|None, "session_id": str}
    """
    pipeline_dir = _get_pipeline_dir(session_id)
    strategy_path = pipeline_dir / "strategy.json"

    deleted = None
    if strategy_path.exists():
        strategy_path.unlink()
        deleted = str(strategy_path)

    return {
        "action": "backtrack",
        "session_id": session_id,
        "deleted": deleted,
        "message": "Phase 2 (Strategy) 재수립 필요",
    }


def execute_restart(session_id, webhook_url=None):
    """Phase 0로 복귀: spec 관련 파일 정리 + 알림 발송.

    Returns:
        dict: {"action": "restart", "session_id": str, "alerted": bool}
    """
    from headless import send_alert

    # 알림 발송
    send_alert(
        "드리프트 감지 — Phase 0 복귀",
        f"세션 {session_id}: drift > {DRIFT_THRESHOLD}, spec 재정의 필요",
        webhook_url=webhook_url,
    )

    return {
        "action": "restart",
        "session_id": session_id,
        "alerted": True,
        "message": f"Phase 0 (Big Bang) 복귀 필요 — drift > {DRIFT_THRESHOLD}",
    }


def run_drift_check(session_id, webhook_url=None):
    """전체 드리프트 검사 흐름: check → decide → execute.

    Returns:
        dict: {"drift_score": float, "action": str, "result": dict}

    Exit codes (for CLI):
        0 = complete
        1 = restart (Phase 0)
        2 = backtrack (Phase 2)
    """
    from headless import log_progress

    # 1. Check
    drift_info = check_drift(session_id)
    drift_score = drift_info["drift_score"]

    # 2. Decide
    action = decide_action(drift_score)

    # 3. Log
    _log_drift(session_id, drift_score, action,
               reason=f"feedback: {drift_info.get('feedback', [])}")

    log_progress(session_id, "phase5",
                 f"drift={drift_score}, action={action}", level="info")

    # 4. Execute
    if action == "complete":
        result = {
            "action": "complete",
            "session_id": session_id,
            "message": "드리프트 0 — 파이프라인 완료",
        }
        log_progress(session_id, "phase5", "파이프라인 완료", level="info")

    elif action == "backtrack":
        result = execute_backtrack(session_id)
        log_progress(session_id, "phase5",
                     "백트래킹: Phase 2로 복귀", level="warning")

    else:  # restart
        result = execute_restart(session_id, webhook_url=webhook_url)
        log_progress(session_id, "phase5",
                     "Phase 0 복귀 — 알림 발송", level="error")

    return {
        "drift_score": drift_score,
        "action": action,
        "result": result,
    }


# ── CLI ─────────────────────────────────────────────────────────────

def _parse_cli(argv):
    """Minimal CLI dispatcher."""
    if len(argv) < 2:
        _usage()
        sys.exit(1)

    cmd = argv[1]

    if cmd == "check":
        if len(argv) < 3:
            print("Usage: drift_checker.py check <session_id>", file=sys.stderr)
            sys.exit(1)
        session_id = argv[2]
        info = check_drift(session_id)
        print(json.dumps(info, indent=2, ensure_ascii=False))

    elif cmd == "decide":
        if len(argv) < 3:
            print("Usage: drift_checker.py decide <drift_score>", file=sys.stderr)
            sys.exit(1)
        try:
            score = float(argv[2])
        except ValueError:
            print(f"Invalid drift_score: {argv[2]}", file=sys.stderr)
            sys.exit(1)
        action = decide_action(score)
        print(json.dumps({"drift_score": score, "action": action},
                         indent=2, ensure_ascii=False))

    elif cmd == "run":
        if len(argv) < 3:
            print("Usage: drift_checker.py run <session_id> [--webhook URL]",
                  file=sys.stderr)
            sys.exit(1)
        session_id = argv[2]
        webhook = None
        if "--webhook" in argv:
            idx = argv.index("--webhook")
            if idx + 1 < len(argv):
                webhook = argv[idx + 1]

        output = run_drift_check(session_id, webhook_url=webhook)
        print(json.dumps(output, indent=2, ensure_ascii=False))

        # Exit code mapping
        action = output["action"]
        if action == "restart":
            sys.exit(1)
        elif action == "backtrack":
            sys.exit(2)
        # complete → exit 0

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        _usage()
        sys.exit(1)


def _usage():
    print(
        "Usage: drift_checker.py <command> [args]\n\n"
        "Commands:\n"
        "  check <session_id>                 Read drift_score from validation.json\n"
        "  decide <drift_score>               Decide action for given score\n"
        "  run <session_id> [--webhook URL]   Full drift check + execute action",
        file=sys.stderr,
    )


if __name__ == "__main__":
    _parse_cli(sys.argv)
