#!/usr/bin/env python3
"""Pipeline Schema — Phase 간 JSON 핸드오프 스키마 정의, 생성, 검증, 직렬화."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PIPELINES_DIR = Path(__file__).resolve().parent.parent / "data" / "pipelines"

# ── Schemas ─────────────────────────────────────────────────────────

HANDOFF_SCHEMA = {
    "required": ["version", "from_phase", "to_phase", "session_id", "timestamp", "status"],
    "optional": ["output_file", "summary"],
    "defaults": {
        "version": "1.0",
        "status": "success",
        "output_file": None,
        "summary": {},
    },
}

RESEARCH_SCHEMA = {
    "required": ["version", "session_id", "topic", "completed_at", "sources", "findings"],
    "optional": ["loop_summary", "open_gaps", "notebook_id"],
    "defaults": {
        "version": "1.0",
        "loop_summary": {
            "total_iterations": 0,
            "total_queries": 0,
            "total_sources": 0,
            "covered_topics": [],
        },
        "sources": [],
        "findings": [],
        "open_gaps": [],
        "notebook_id": None,
    },
}

STRATEGY_SCHEMA = {
    "required": ["version", "session_id", "created_at", "approach", "tasks"],
    "optional": ["constraints_applied", "estimated_cost"],
    "defaults": {
        "version": "1.0",
        "approach": "Double Diamond",
        "tasks": [],
        "constraints_applied": [],
        "estimated_cost": None,
    },
}

EXECUTION_SCHEMA = {
    "required": ["version", "session_id", "completed_at", "artifacts", "tasks_completed", "tasks_failed"],
    "optional": ["total_cost"],
    "defaults": {
        "version": "1.0",
        "artifacts": [],
        "tasks_completed": 0,
        "tasks_failed": 0,
        "total_cost": None,
    },
}

VALIDATION_SCHEMA = {
    "required": ["version", "session_id", "completed_at", "passed", "drift_score"],
    "optional": ["stage1_mechanical", "stage2_semantic", "stage3_consensus", "action", "feedback"],
    "defaults": {
        "version": "1.0",
        "passed": False,
        "drift_score": 1.0,
        "stage1_mechanical": {"passed": False, "checks": []},
        "stage2_semantic": {"passed": False, "spec_alignment": 0.0, "notes": []},
        "stage3_consensus": {
            "passed": False,
            "advocate": "",
            "critic": "",
            "judge": "",
            "drift_score": 1.0,
        },
        "action": "pending",
        "feedback": [],
    },
}

_SCHEMAS = {
    "research": RESEARCH_SCHEMA,
    "strategy": STRATEGY_SCHEMA,
    "execution": EXECUTION_SCHEMA,
    "validation": VALIDATION_SCHEMA,
    "handoff": HANDOFF_SCHEMA,
}

_FILENAMES = {
    "research": "research.json",
    "strategy": "strategy.json",
    "execution": "execution.json",
    "validation": "validation.json",
}


# ── Create functions ────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def create_research(session_id, topic) -> dict:
    """Create a blank research output (Phase 1)."""
    return {
        "version": "1.0",
        "session_id": session_id,
        "topic": topic,
        "completed_at": _now_iso(),
        "loop_summary": {
            "total_iterations": 0,
            "total_queries": 0,
            "total_sources": 0,
            "covered_topics": [],
        },
        "sources": [],
        "findings": [],
        "open_gaps": [],
        "notebook_id": None,
    }


def create_strategy(session_id) -> dict:
    """Create a blank strategy output (Phase 2)."""
    return {
        "version": "1.0",
        "session_id": session_id,
        "created_at": _now_iso(),
        "approach": "Double Diamond",
        "tasks": [],
        "constraints_applied": [],
        "estimated_cost": None,
    }


def create_execution(session_id) -> dict:
    """Create a blank execution output (Phase 3)."""
    return {
        "version": "1.0",
        "session_id": session_id,
        "completed_at": _now_iso(),
        "artifacts": [],
        "tasks_completed": 0,
        "tasks_failed": 0,
        "total_cost": None,
    }


def create_validation(session_id) -> dict:
    """Create a blank validation output (Phase 4)."""
    return {
        "version": "1.0",
        "session_id": session_id,
        "completed_at": _now_iso(),
        "passed": False,
        "drift_score": 1.0,
        "stage1_mechanical": {"passed": False, "checks": []},
        "stage2_semantic": {"passed": False, "spec_alignment": 0.0, "notes": []},
        "stage3_consensus": {
            "passed": False,
            "advocate": "",
            "critic": "",
            "judge": "",
            "drift_score": 1.0,
        },
        "action": "pending",
        "feedback": [],
    }


def create_handoff(from_phase, to_phase, session_id, status="success",
                    output_file=None, summary=None) -> dict:
    """Create a handoff record between Phases."""
    return {
        "version": "1.0",
        "from_phase": from_phase,
        "to_phase": to_phase,
        "session_id": session_id,
        "timestamp": _now_iso(),
        "status": status,
        "output_file": output_file,
        "summary": summary or {},
    }


# ── Validate functions ──────────────────────────────────────────────

def _validate_against_schema(data, schema, name) -> dict:
    """Generic validator: check required fields."""
    missing = []
    for field in schema["required"]:
        if field not in data or data[field] is None:
            missing.append(field)

    return {
        "valid": len(missing) == 0,
        "schema": name,
        "missing": missing,
    }


def validate_research(data) -> dict:
    """Validate a research output."""
    return _validate_against_schema(data, RESEARCH_SCHEMA, "research")


def validate_strategy(data) -> dict:
    """Validate a strategy output."""
    return _validate_against_schema(data, STRATEGY_SCHEMA, "strategy")


def validate_execution(data) -> dict:
    """Validate an execution output."""
    return _validate_against_schema(data, EXECUTION_SCHEMA, "execution")


def validate_validation(data) -> dict:
    """Validate a validation output."""
    return _validate_against_schema(data, VALIDATION_SCHEMA, "validation")


def validate_handoff(data) -> dict:
    """Validate a handoff record."""
    result = _validate_against_schema(data, HANDOFF_SCHEMA, "handoff")
    # Extra check: from_phase < to_phase
    fp = data.get("from_phase")
    tp = data.get("to_phase")
    if isinstance(fp, int) and isinstance(tp, int) and fp >= tp:
        result["valid"] = False
        result.setdefault("errors", []).append(
            f"from_phase ({fp}) must be less than to_phase ({tp})"
        )
    return result


# ── Save / Load ─────────────────────────────────────────────────────

def _get_pipeline_dir(session_id) -> Path:
    pipeline_dir = PIPELINES_DIR / session_id
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    return pipeline_dir


def save_phase_output(data, phase_name, session_id) -> Path:
    """Save a Phase output JSON to data/pipelines/{session_id}/{phase_name}.json."""
    if phase_name == "handoff":
        fp = data.get("from_phase", "?")
        tp = data.get("to_phase", "?")
        filename = f"handoff_{fp}_to_{tp}.json"
    elif phase_name in _FILENAMES:
        filename = _FILENAMES[phase_name]
    else:
        filename = f"{phase_name}.json"

    pipeline_dir = _get_pipeline_dir(session_id)
    path = pipeline_dir / filename
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def load_phase_output(phase_name, session_id) -> dict:
    """Load a Phase output JSON from data/pipelines/{session_id}/{phase_name}.json."""
    if phase_name in _FILENAMES:
        filename = _FILENAMES[phase_name]
    else:
        filename = f"{phase_name}.json"

    path = _get_pipeline_dir(session_id) / filename
    if not path.exists():
        raise FileNotFoundError(f"Phase output not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Phase output corrupted: {path}: {exc}") from exc


# ── CLI ─────────────────────────────────────────────────────────────

def _parse_cli(argv) -> None:
    """Minimal CLI dispatcher."""
    if len(argv) < 2:
        _usage()
        sys.exit(1)

    cmd = argv[1]

    if cmd == "create":
        if len(argv) < 4:
            print("Usage: pipeline_schema.py create <phase_name> <session_id> [extra_args]",
                  file=sys.stderr)
            sys.exit(1)
        phase_name = argv[2]
        session_id = argv[3]
        data = _dispatch_create(phase_name, session_id, argv[4:])
        print(json.dumps(data, indent=2, ensure_ascii=False))

    elif cmd == "validate":
        if len(argv) < 4:
            print("Usage: pipeline_schema.py validate <phase_name> <session_id>",
                  file=sys.stderr)
            sys.exit(1)
        phase_name = argv[2]
        session_id = argv[3]
        data = load_phase_output(phase_name, session_id)
        result = _dispatch_validate(phase_name, data)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "save":
        if len(argv) < 4:
            print("Usage: pipeline_schema.py save <phase_name> <session_id> < data.json",
                  file=sys.stderr)
            sys.exit(1)
        phase_name = argv[2]
        session_id = argv[3]
        raw = sys.stdin.read()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON input: {exc}", file=sys.stderr)
            sys.exit(1)
        path = save_phase_output(data, phase_name, session_id)
        print(f"Saved: {path}")

    elif cmd == "load":
        if len(argv) < 4:
            print("Usage: pipeline_schema.py load <phase_name> <session_id>",
                  file=sys.stderr)
            sys.exit(1)
        phase_name = argv[2]
        session_id = argv[3]
        data = load_phase_output(phase_name, session_id)
        print(json.dumps(data, indent=2, ensure_ascii=False))

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        _usage()
        sys.exit(1)


def _dispatch_create(phase_name, session_id, extra_args) -> dict:
    if phase_name == "research":
        topic = extra_args[0] if extra_args else "untitled"
        return create_research(session_id, topic)
    elif phase_name == "strategy":
        return create_strategy(session_id)
    elif phase_name == "execution":
        return create_execution(session_id)
    elif phase_name == "validation":
        return create_validation(session_id)
    elif phase_name == "handoff":
        if len(extra_args) < 2:
            print("Usage: pipeline_schema.py create handoff <session_id> <from> <to>",
                  file=sys.stderr)
            sys.exit(1)
        return create_handoff(int(extra_args[0]), int(extra_args[1]), session_id)
    else:
        print(f"Unknown phase: {phase_name}", file=sys.stderr)
        sys.exit(1)


def _dispatch_validate(phase_name, data) -> dict:
    validators = {
        "research": validate_research,
        "strategy": validate_strategy,
        "execution": validate_execution,
        "validation": validate_validation,
        "handoff": validate_handoff,
    }
    fn = validators.get(phase_name)
    if fn is None:
        print(f"Unknown phase: {phase_name}", file=sys.stderr)
        sys.exit(1)
    return fn(data)


def _usage() -> None:
    print(
        "Usage: pipeline_schema.py <command> [args]\n\n"
        "Commands:\n"
        "  create <phase> <session_id> [args]   Create blank phase output\n"
        "  validate <phase> <session_id>        Validate saved phase output\n"
        "  save <phase> <session_id>            Save phase output from stdin\n"
        "  load <phase> <session_id>            Load and print phase output\n\n"
        "Phases: research, strategy, execution, validation, handoff",
        file=sys.stderr,
    )


if __name__ == "__main__":
    _parse_cli(sys.argv)
