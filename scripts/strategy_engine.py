#!/usr/bin/env python3
"""Strategy Engine — Double Diamond (Diverge → Converge) 전략 수립."""

import json
import sys
from pathlib import Path

PIPELINES_DIR = Path(__file__).resolve().parent.parent / "data" / "pipelines"

# ── Tool mapping keywords ────────────────────────────────────────────

_TOOL_KEYWORDS = {
    "dall-e": ["image", "thumbnail", "visual", "picture", "illustration", "그림", "썸네일", "이미지"],
    "flux": ["video", "animation", "motion", "영상", "애니메이션", "동영상"],
    "notebooklm": ["document", "report", "summary", "분석", "보고서", "요약", "문서"],
    "claude": ["code", "script", "automation", "write", "코드", "스크립트", "자동화", "작성"],
    "web_search": ["search", "research", "find", "검색", "조사", "탐색"],
}

_DEFAULT_TOOL = "claude"


# ── Diverge ──────────────────────────────────────────────────────────

def _diverge(findings):
    """Findings → task candidates. 각 finding에서 1개의 task candidate를 생성."""
    candidates = []
    for i, finding in enumerate(findings):
        candidate = {
            "id": f"task_{i + 1}",
            "title": _extract_title(finding),
            "description": finding,
            "tool": _map_tool(finding),
            "priority": "medium",
            "source_findings": [i],
        }
        candidates.append(candidate)
    return candidates


def _extract_title(finding):
    """Finding 텍스트에서 짧은 제목을 추출."""
    text = finding.strip()
    # 첫 문장 또는 50자까지
    for sep in [".", "。", "\n"]:
        idx = text.find(sep)
        if 0 < idx <= 80:
            return text[:idx]
    if len(text) > 50:
        return text[:50] + "..."
    return text


def _map_tool(text):
    """텍스트 내 키워드로 최적 도구를 매핑."""
    lower = text.lower()
    for tool, keywords in _TOOL_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                return tool
    return _DEFAULT_TOOL


# ── Converge ─────────────────────────────────────────────────────────

def _converge(candidates, constraints=None, allowed_tools=None):
    """제약 조건으로 candidates를 필터링하고 우선순위를 조정."""
    if not candidates:
        return []

    filtered = list(candidates)

    # 허용된 도구로 필터링
    if allowed_tools:
        allowed_set = set(allowed_tools)
        filtered = [c for c in filtered if c["tool"] in allowed_set]

    # 제약 조건 텍스트에 매칭되는 task에 priority 상향
    if constraints:
        for task in filtered:
            desc_lower = task["description"].lower()
            for constraint in constraints:
                if constraint.lower() in desc_lower:
                    task["priority"] = "high"
                    break

    # 우선순위 정렬: high → medium → low
    priority_order = {"high": 0, "medium": 1, "low": 2}
    filtered.sort(key=lambda t: priority_order.get(t["priority"], 1))

    return filtered


# ── Generate ─────────────────────────────────────────────────────────

def generate_strategy(research_data, spec_data=None):
    """research.json → strategy.json 변환 (Double Diamond).

    Args:
        research_data: Phase 1 research output dict
        spec_data: Pipeline Spec dict (optional, for constraints/tools)

    Returns:
        strategy dict ready for validate_strategy / save_phase_output
    """
    from pipeline_schema import create_strategy

    session_id = research_data.get("session_id", "unknown")
    findings = research_data.get("findings", [])

    if not findings:
        print("경고: findings가 비어있습니다. 빈 전략을 생성합니다.", file=sys.stderr)

    # Phase 1: Diverge — findings → candidates
    candidates = _diverge(findings)

    # Extract constraints and tools from spec
    constraints = []
    allowed_tools = None
    if spec_data:
        domain = spec_data.get("domain", {})
        constraints = domain.get("constraints", [])
        pipeline = spec_data.get("pipeline", {})
        spec_tools = pipeline.get("tools", [])
        if spec_tools:
            allowed_tools = spec_tools

    # Phase 2: Converge — filter + prioritize
    tasks = _converge(candidates, constraints=constraints, allowed_tools=allowed_tools)

    # Build strategy
    strategy = create_strategy(session_id)
    strategy["tasks"] = tasks
    strategy["constraints_applied"] = constraints

    return strategy


# ── Show ─────────────────────────────────────────────────────────────

def show_strategy(strategy):
    """전략 요약을 사람이 읽을 수 있는 형태로 출력."""
    print(f"Session: {strategy.get('session_id', '?')}")
    print(f"Approach: {strategy.get('approach', '?')}")
    print(f"Tasks: {len(strategy.get('tasks', []))}")

    constraints = strategy.get("constraints_applied", [])
    if constraints:
        print(f"Constraints: {', '.join(constraints)}")

    cost = strategy.get("estimated_cost")
    if cost is not None:
        print(f"Estimated cost: {cost}")

    print()
    for task in strategy.get("tasks", []):
        priority_mark = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task["priority"], "⚪")
        print(f"  {priority_mark} [{task['id']}] {task['title']}")
        print(f"     Tool: {task['tool']} | Priority: {task['priority']}")


# ── CLI ──────────────────────────────────────────────────────────────

def _load_research(session_id):
    """Load research.json for a session."""
    from pipeline_schema import load_phase_output
    return load_phase_output("research", session_id)


def _load_spec_safe(session_id):
    """Load spec.json if available, else return None."""
    from pipeline_spec import load_spec
    try:
        return load_spec(session_id)
    except FileNotFoundError:
        return None


def _parse_cli(argv):
    """Minimal CLI dispatcher."""
    if len(argv) < 2:
        _usage()
        sys.exit(1)

    cmd = argv[1]

    if cmd == "generate":
        if len(argv) < 3:
            print("Usage: strategy_engine.py generate <session_id>", file=sys.stderr)
            sys.exit(1)
        session_id = argv[2]
        research = _load_research(session_id)
        spec = _load_spec_safe(session_id)
        strategy = generate_strategy(research, spec_data=spec)
        print(json.dumps(strategy, indent=2, ensure_ascii=False))

    elif cmd == "validate":
        if len(argv) < 3:
            print("Usage: strategy_engine.py validate <session_id>", file=sys.stderr)
            sys.exit(1)
        from pipeline_schema import load_phase_output, validate_strategy
        session_id = argv[2]
        data = load_phase_output("strategy", session_id)
        result = validate_strategy(data)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "show":
        if len(argv) < 3:
            print("Usage: strategy_engine.py show <session_id>", file=sys.stderr)
            sys.exit(1)
        from pipeline_schema import load_phase_output
        session_id = argv[2]
        data = load_phase_output("strategy", session_id)
        show_strategy(data)

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        _usage()
        sys.exit(1)


def _usage():
    print(
        "Usage: strategy_engine.py <command> [args]\n\n"
        "Commands:\n"
        "  generate <session_id>   Generate strategy from research\n"
        "  validate <session_id>   Validate saved strategy\n"
        "  show <session_id>       Show strategy summary",
        file=sys.stderr,
    )


if __name__ == "__main__":
    _parse_cli(sys.argv)
