#!/usr/bin/env python3
"""PAL Router — Phase-Aware LLM Router for cost-quality optimization.

Maps each pipeline phase to a model tier (frugal / standard / frontier)
and resolves the concrete model configuration.
"""

import json
import sys
from pathlib import Path

PIPELINES_DIR = Path(__file__).resolve().parent.parent / "data" / "pipelines"

# ── Model Tiers ──────────────────────────────────────────────────────

MODEL_TIERS = {
    "frugal": {
        "model_id": "claude-haiku-4-5-20251001",
        "max_tokens": 4096,
        "temperature": 0.3,
        "cost_multiplier": 1,
    },
    "standard": {
        "model_id": "claude-sonnet-4-6",
        "max_tokens": 8192,
        "temperature": 0.5,
        "cost_multiplier": 10,
    },
    "frontier": {
        "model_id": "claude-opus-4-6",
        "max_tokens": 16384,
        "temperature": 0.2,
        "cost_multiplier": 30,
    },
}

# ── Default Phase → Tier mapping ─────────────────────────────────────

DEFAULT_PHASE_TIERS = {
    0: "standard",   # Big Bang: spec 검증, 중간 추론
    1: "frugal",     # Research: 대량 검색
    2: "standard",   # Strategy: 전략 수립
    3: "frugal",     # Execution: 도구 실행
    4: "frontier",   # Evaluation: 정밀 판단
    5: "standard",   # Drift Check: 드리프트 계산
}

PHASE_NAMES = {
    0: "Big Bang",
    1: "Research",
    2: "Strategy",
    3: "Execution",
    4: "Evaluation",
    5: "Drift Check",
}


# ── Core functions ───────────────────────────────────────────────────

def get_tier_config(tier_name):
    """Return the configuration dict for a given tier name.

    Returns None if the tier name is unknown.
    """
    return MODEL_TIERS.get(tier_name)


def get_model_for_phase(phase, spec=None):
    """Determine the model tier and config for a given phase.

    If spec contains pipeline.model_tiers with an override for this phase,
    use that tier. Otherwise fall back to DEFAULT_PHASE_TIERS.

    Returns dict with: phase, phase_name, tier, model_id, max_tokens, temperature.
    """
    phase = int(phase)

    # Check spec override
    tier_name = None
    if spec is not None:
        overrides = spec.get("pipeline", {}).get("model_tiers", {})
        # model_tiers keys can be int or str
        tier_name = overrides.get(phase) or overrides.get(str(phase))

    # Fall back to default
    if tier_name is None:
        tier_name = DEFAULT_PHASE_TIERS.get(phase, "standard")

    # Validate tier
    config = get_tier_config(tier_name)
    if config is None:
        print(f"Unknown tier '{tier_name}' for phase {phase}, falling back to 'standard'", file=sys.stderr)
        tier_name = "standard"
        config = MODEL_TIERS["standard"]

    return {
        "phase": phase,
        "phase_name": PHASE_NAMES.get(phase, f"Phase {phase}"),
        "tier": tier_name,
        "model_id": config["model_id"],
        "max_tokens": config["max_tokens"],
        "temperature": config["temperature"],
    }


# ── Adaptive routing ─────────────────────────────────────────────────

ADAPTIVE_ROUTING_CONFIG = {
    # Promote to frontier when previous drift exceeds this threshold
    # Rationale: drift > 0.2 indicates evaluation found significant gaps
    "drift_threshold": 0.2,
    # Promote to frontier when research produced many sources
    # Rationale: >20 sources requires more careful strategy synthesis
    "source_count_threshold": 20,
}


def get_adaptive_model(phase, spec=None, prev_results=None):
    """Select model tier adaptively based on previous phase results.

    Falls back to get_model_for_phase() when prev_results is None.

    Args:
        phase: phase number
        spec: pipeline spec dict
        prev_results: dict with keys like prev_drift_score, research_source_count

    Returns:
        dict with phase, phase_name, tier, model_id, max_tokens, temperature
    """
    base = get_model_for_phase(phase, spec)

    if prev_results is None:
        return base

    # Phase 4 (Evaluation): promote to frontier if prior drift was high
    if phase == 4:
        prev_drift = prev_results.get("prev_drift_score", 0)
        if prev_drift > ADAPTIVE_ROUTING_CONFIG["drift_threshold"]:
            config = MODEL_TIERS["frontier"]
            base["tier"] = "frontier"
            base["model_id"] = config["model_id"]
            base["max_tokens"] = config["max_tokens"]
            base["temperature"] = config["temperature"]

    # Phase 2 (Strategy): promote to frontier if many research sources
    if phase == 2:
        source_count = prev_results.get("research_source_count", 0)
        if source_count > ADAPTIVE_ROUTING_CONFIG["source_count_threshold"]:
            config = MODEL_TIERS["frontier"]
            base["tier"] = "frontier"
            base["model_id"] = config["model_id"]
            base["max_tokens"] = config["max_tokens"]
            base["temperature"] = config["temperature"]

    return base


def estimate_cost(phases=None, spec=None):
    """Estimate relative cost for given phases.

    Returns dict with: phases (list of phase details), total_cost, breakdown.
    Cost is relative: frugal=1x, standard=10x, frontier=30x.
    """
    if phases is None:
        phases = [0, 1, 2, 3, 4, 5]

    breakdown = []
    total = 0

    for phase in phases:
        route = get_model_for_phase(phase, spec)
        tier_config = MODEL_TIERS[route["tier"]]
        cost = tier_config["cost_multiplier"]
        total += cost
        breakdown.append({
            "phase": phase,
            "phase_name": route["phase_name"],
            "tier": route["tier"],
            "cost": cost,
        })

    return {
        "phases": breakdown,
        "total_cost": total,
        "unit": "relative (frugal=1x)",
    }


# ── Cost tracking ────────────────────────────────────────────────────

def track_cost(session_id, phase, tier):
    """Record a cost event to cost_log.json using relative cost units.

    Cost = tier cost_multiplier (reuses MODEL_TIERS values: frugal=1, standard=10, frontier=30).
    """
    from _io_utils import _atomic_write_json

    config = MODEL_TIERS.get(tier, MODEL_TIERS["standard"])
    cost = config["cost_multiplier"]

    pipeline_dir = PIPELINES_DIR / session_id
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    log_path = pipeline_dir / "cost_log.json"

    records = []
    if log_path.exists():
        try:
            records = json.loads(log_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            records = []

    from datetime import datetime, timezone
    entry = {
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "phase": phase,
        "phase_name": PHASE_NAMES.get(phase, f"Phase {phase}"),
        "tier": tier,
        "cost": cost,
    }
    records.append(entry)
    _atomic_write_json(log_path, records)

    return {"recorded": True, "cost": cost, "total": sum(r["cost"] for r in records)}


def check_budget(session_id, cost_limit):
    """Check if accumulated cost is approaching or exceeding budget.

    Args:
        session_id: pipeline session ID
        cost_limit: budget limit in relative cost units

    Returns:
        dict: {"total_cost": int, "limit": int, "percent": float, "warning": bool, "exceeded": bool}
    """
    pipeline_dir = PIPELINES_DIR / session_id
    log_path = pipeline_dir / "cost_log.json"

    total = 0
    if log_path.exists():
        try:
            records = json.loads(log_path.read_text(encoding="utf-8"))
            total = sum(r.get("cost", 0) for r in records)
        except (json.JSONDecodeError, ValueError):
            pass

    limit = int(cost_limit) if cost_limit else 0
    if limit <= 0:
        return {"total_cost": total, "limit": 0, "percent": 0.0, "warning": False, "exceeded": False}

    percent = round(total / limit * 100, 1)
    warning = percent >= 80
    exceeded = percent >= 100

    if warning and not exceeded:
        print(f"[COST WARNING] {percent}% of budget used ({total}/{limit})", file=sys.stderr)
    elif exceeded:
        print(f"[COST EXCEEDED] {percent}% of budget ({total}/{limit})", file=sys.stderr)

    return {"total_cost": total, "limit": limit, "percent": percent, "warning": warning, "exceeded": exceeded}


def _load_spec_for_session(session_id):
    """Load spec from pipelines directory. Returns None if not found."""
    spec_path = PIPELINES_DIR / session_id / "spec.json"
    if not spec_path.exists():
        return None
    try:
        return json.loads(spec_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


# ── CLI ──────────────────────────────────────────────────────────────

def _parse_cli(argv):
    """Minimal CLI dispatcher — no external deps."""
    if len(argv) < 2:
        _usage()
        sys.exit(1)

    cmd = argv[1]

    if cmd == "route":
        if len(argv) < 3:
            print("Usage: pal_router.py route <phase_num> [--session <session_id>]", file=sys.stderr)
            sys.exit(1)
        try:
            phase = int(argv[2])
        except ValueError:
            print(f"Error: phase must be integer, got '{argv[2]}'", file=sys.stderr)
            sys.exit(1)
        spec = None
        if "--session" in argv:
            idx = argv.index("--session")
            if idx + 1 < len(argv):
                spec = _load_spec_for_session(argv[idx + 1])
        result = get_model_for_phase(phase, spec)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "estimate":
        spec = None
        phases = None
        if "--session" in argv:
            idx = argv.index("--session")
            if idx + 1 < len(argv):
                spec = _load_spec_for_session(argv[idx + 1])
        if "--phases" in argv:
            idx = argv.index("--phases")
            if idx + 1 < len(argv):
                phases = [int(p) for p in argv[idx + 1].split(",")]
        result = estimate_cost(phases, spec)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "config":
        if len(argv) < 3:
            # Show all tiers
            print(json.dumps(MODEL_TIERS, indent=2, ensure_ascii=False))
        else:
            tier_name = argv[2]
            config = get_tier_config(tier_name)
            if config is None:
                print(f"Unknown tier: {tier_name}", file=sys.stderr)
                sys.exit(1)
            print(json.dumps(config, indent=2, ensure_ascii=False))

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        _usage()
        sys.exit(1)


def _usage():
    print(
        "Usage: pal_router.py <command> [args]\n\n"
        "Commands:\n"
        "  route <phase_num> [--session <id>]   Get model for a phase\n"
        "  estimate [--phases 0,1,2] [--session <id>]  Estimate cost\n"
        "  config [tier_name]                   Show tier configuration",
        file=sys.stderr,
    )


if __name__ == "__main__":
    _parse_cli(sys.argv)
