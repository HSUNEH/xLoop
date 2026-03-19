#!/usr/bin/env python3
"""Pipeline Spec — define, validate, and persist Pipeline Spec JSON."""

import json
import sys
from pathlib import Path

PIPELINES_DIR = Path(__file__).resolve().parent.parent / "data" / "pipelines"

# ── Schema ──────────────────────────────────────────────────────────

SPEC_SCHEMA = {
    "required": {
        "goal": {
            "deliverables": {"type": "list", "description": "최종 산출물 목록"},
            "success_criteria": {"type": "list", "description": "성공 기준 (정량 최소 1개 필수)"},
        },
        "domain": {
            "target": {"type": "str", "description": "대상 (예: 채널, 사이트, 주제)"},
        },
    },
    "optional": {
        "goal": {
            "deadline": {"type": "str", "description": "마감 기한"},
            "cost_limit": {"type": "str", "description": "비용 한도"},
        },
        "domain": {
            "constraints": {"type": "list", "description": "제약 조건"},
            "references": {"type": "list", "description": "참고 자료"},
        },
        "pipeline": {
            "active_phases": {"type": "list", "description": "활성 Phase 목록"},
            "tools": {"type": "list", "description": "사용 도구 목록"},
            "model_tiers": {"type": "dict", "description": "Phase별 모델 티어"},
        },
    },
}


# ── Core functions ──────────────────────────────────────────────────

def create_spec() -> dict:
    """Create an empty Pipeline Spec with all fields initialized."""
    return {
        "version": "1.0",
        "goal": {
            "deliverables": [],
            "success_criteria": [],
            "deadline": None,
            "cost_limit": None,
        },
        "domain": {
            "target": None,
            "constraints": [],
            "references": [],
        },
        "pipeline": {
            "active_phases": [0, 1, 2, 3, 4, 5],
            "tools": [],
            "model_tiers": {},
        },
    }


def validate_spec(spec: dict) -> dict:
    """Validate a spec and return {valid, missing, ambiguity, warnings}."""
    missing = []
    warnings = []

    # Check required fields
    goal = spec.get("goal", {})
    domain = spec.get("domain", {})

    if not goal.get("deliverables"):
        missing.append("goal.deliverables")
    if not goal.get("success_criteria"):
        missing.append("goal.success_criteria")
    if not domain.get("target"):
        missing.append("domain.target")

    # Check success_criteria has at least one quantitative criterion
    has_quantitative = False
    for criterion in goal.get("success_criteria", []):
        if _is_quantitative(criterion):
            has_quantitative = True
            break

    if goal.get("success_criteria") and not has_quantitative:
        warnings.append("success_criteria에 정량 기준이 없습니다. 최소 1개의 측정 가능한 기준을 추가하세요.")

    ambiguity = calculate_ambiguity(spec)
    valid = len(missing) == 0 and has_quantitative and ambiguity <= 0.2

    return {
        "valid": valid,
        "missing": missing,
        "ambiguity": ambiguity,
        "has_quantitative_criteria": has_quantitative,
        "warnings": warnings,
    }


def _is_quantitative(criterion: str) -> bool:
    """Check if a success criterion contains quantitative measure."""
    import re
    # Numbers, units, comparison operators
    return bool(re.search(r'\d+', criterion))


def calculate_ambiguity(spec: dict) -> float:
    """Calculate ambiguity score (0.0 = clear, 1.0 = ambiguous).

    Weights: goal clarity 40%, constraint clarity 30%, success criteria 30%.
    """
    goal = spec.get("goal", {})
    domain = spec.get("domain", {})

    # Goal clarity (40%): deliverables + target
    goal_score = 1.0
    deliverables = goal.get("deliverables", [])
    target = domain.get("target")
    if deliverables and target:
        goal_score = 0.0
    elif deliverables or target:
        goal_score = 0.5

    # Constraint clarity (30%): constraints + references
    constraint_score = 1.0
    constraints = domain.get("constraints", [])
    references = domain.get("references", [])
    if constraints and references:
        constraint_score = 0.0
    elif constraints or references:
        constraint_score = 0.5

    # Success criteria (30%): existence + quantitative
    criteria_score = 1.0
    criteria = goal.get("success_criteria", [])
    if criteria:
        has_quant = any(_is_quantitative(c) for c in criteria)
        if has_quant and len(criteria) >= 2:
            criteria_score = 0.0
        elif has_quant or len(criteria) >= 2:
            criteria_score = 0.3
        else:
            criteria_score = 0.5

    return round(goal_score * 0.4 + constraint_score * 0.3 + criteria_score * 0.3, 2)


def save_spec(spec: dict, session_id: str) -> Path:
    """Save a Pipeline Spec to data/pipelines/{session_id}/spec.json."""
    spec_dir = _get_pipeline_dir(session_id)
    path = spec_dir / "spec.json"
    path.write_text(
        json.dumps(spec, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def load_spec(session_id: str) -> dict:
    """Load a Pipeline Spec from data/pipelines/{session_id}/spec.json."""
    path = _get_pipeline_dir(session_id) / "spec.json"
    if not path.exists():
        raise FileNotFoundError(f"Spec not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Spec file is corrupted: {path}: {exc}") from exc


def _get_pipeline_dir(session_id: str) -> Path:
    """Return the pipeline directory for a session, creating it if needed."""
    pipeline_dir = PIPELINES_DIR / session_id
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    return pipeline_dir


# ── CLI ──────────────────────────────────────────────────────────────

def _parse_cli(argv: list[str]) -> None:
    """Minimal CLI dispatcher — no external deps."""
    if len(argv) < 2:
        _usage()
        sys.exit(1)

    cmd = argv[1]

    if cmd == "create":
        spec = create_spec()
        print(json.dumps(spec, indent=2, ensure_ascii=False))

    elif cmd == "validate":
        if len(argv) < 3:
            print("Usage: pipeline_spec.py validate <session_id>", file=sys.stderr)
            sys.exit(1)
        spec = load_spec(argv[2])
        result = validate_spec(spec)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "load":
        if len(argv) < 3:
            print("Usage: pipeline_spec.py load <session_id>", file=sys.stderr)
            sys.exit(1)
        spec = load_spec(argv[2])
        print(json.dumps(spec, indent=2, ensure_ascii=False))

    elif cmd == "save":
        if len(argv) < 3:
            print("Usage: pipeline_spec.py save <session_id> < spec.json", file=sys.stderr)
            sys.exit(1)
        raw = sys.stdin.read()
        try:
            spec = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON input: {exc}", file=sys.stderr)
            sys.exit(1)
        path = save_spec(spec, argv[2])
        print(f"Spec saved: {path}")

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        _usage()
        sys.exit(1)


def _usage() -> None:
    print(
        "Usage: pipeline_spec.py <command> [args]\n\n"
        "Commands:\n"
        "  create                   Create an empty spec (stdout)\n"
        "  validate <session_id>    Validate a saved spec\n"
        "  load <session_id>        Load and print a spec\n"
        "  save <session_id>        Save spec from stdin",
        file=sys.stderr,
    )


if __name__ == "__main__":
    _parse_cli(sys.argv)
