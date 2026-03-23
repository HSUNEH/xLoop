#!/usr/bin/env python3
"""Tests for phase routing flexibility (US-004)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


# ── should_run_phase ────────────────────────────────────────────────

def test_should_run_phase_always_runs_phase0():
    from pipeline_spec import should_run_phase
    spec = {"pipeline": {"active_phases": [0, 1, 2, 3, 4, 5]}}
    assert should_run_phase(0, spec) is True


def test_should_run_phase_skips_inactive():
    from pipeline_spec import should_run_phase
    spec = {"pipeline": {"active_phases": [0, 1, 4, 5]}}
    assert should_run_phase(2, spec) is False
    assert should_run_phase(3, spec) is False


def test_should_run_phase_precondition_research():
    from pipeline_spec import should_run_phase
    spec = {"pipeline": {"active_phases": [0, 1, 2, 3, 4, 5]}}
    # Phase 2 requires research findings
    assert should_run_phase(2, spec, {"research_findings_count": 0}) is False
    assert should_run_phase(2, spec, {"research_findings_count": 5}) is True


def test_should_run_phase_precondition_strategy():
    from pipeline_spec import should_run_phase
    spec = {"pipeline": {"active_phases": [0, 1, 2, 3, 4, 5]}}
    assert should_run_phase(3, spec, {"strategy_tasks_count": 0}) is False
    assert should_run_phase(3, spec, {"strategy_tasks_count": 3}) is True


def test_should_run_phase_precondition_execution():
    from pipeline_spec import should_run_phase
    spec = {"pipeline": {"active_phases": [0, 1, 2, 3, 4, 5]}}
    assert should_run_phase(4, spec, {"execution_artifacts_count": 0}) is False
    assert should_run_phase(4, spec, {"execution_artifacts_count": 2}) is True


def test_should_run_phase_default_active_phases():
    from pipeline_spec import should_run_phase
    spec = {}  # No active_phases → defaults to [0,1,2,3,4,5]
    assert should_run_phase(1, spec) is True


# ── get_adaptive_model ──────────────────────────────────────────────

def test_adaptive_model_no_prev_results():
    from pal_router import get_adaptive_model
    result = get_adaptive_model(1)
    assert result["tier"] == "frugal"  # Phase 1 default


def test_adaptive_model_phase4_high_drift():
    from pal_router import get_adaptive_model
    result = get_adaptive_model(4, prev_results={"prev_drift_score": 0.5})
    assert result["tier"] == "frontier"


def test_adaptive_model_phase4_low_drift():
    from pal_router import get_adaptive_model
    result = get_adaptive_model(4, prev_results={"prev_drift_score": 0.1})
    assert result["tier"] == "frontier"  # Phase 4 default is frontier


def test_adaptive_model_phase2_many_sources():
    from pal_router import get_adaptive_model
    result = get_adaptive_model(2, prev_results={"research_source_count": 25})
    assert result["tier"] == "frontier"


def test_adaptive_model_phase2_few_sources():
    from pal_router import get_adaptive_model
    result = get_adaptive_model(2, prev_results={"research_source_count": 5})
    assert result["tier"] == "standard"  # Phase 2 default


def test_adaptive_routing_config_exists():
    from pal_router import ADAPTIVE_ROUTING_CONFIG
    assert "drift_threshold" in ADAPTIVE_ROUTING_CONFIG
    assert "source_count_threshold" in ADAPTIVE_ROUTING_CONFIG
    assert ADAPTIVE_ROUTING_CONFIG["drift_threshold"] == 0.2
    assert ADAPTIVE_ROUTING_CONFIG["source_count_threshold"] == 20


# ── decide_backtrack_target ─────────────────────────────────────────

def test_backtrack_target_stage0():
    from drift_checker import decide_backtrack_target
    assert decide_backtrack_target({"feedback": ["[Stage0] smoke test failed"]}) == 3


def test_backtrack_target_stage1():
    from drift_checker import decide_backtrack_target
    assert decide_backtrack_target({"feedback": ["[Stage1] artifact count low"]}) == 3


def test_backtrack_target_stage2():
    from drift_checker import decide_backtrack_target
    assert decide_backtrack_target({"feedback": ["[Stage2] semantic mismatch"]}) == 2


def test_backtrack_target_default():
    from drift_checker import decide_backtrack_target
    assert decide_backtrack_target({"feedback": ["generic issue"]}) == 2


def test_backtrack_target_empty_feedback():
    from drift_checker import decide_backtrack_target
    assert decide_backtrack_target({}) == 2


# ── create_backtrack_handoff ────────────────────────────────────────

def test_create_backtrack_handoff_basic():
    from drift_checker import create_backtrack_handoff
    handoff = create_backtrack_handoff(5, 2, "test_session")
    assert handoff["type"] == "backtrack"
    assert handoff["from_phase"] == 5
    assert handoff["to_phase"] == 2
    assert handoff["session_id"] == "test_session"
    assert handoff["status"] == "backtrack"
    assert "timestamp" in handoff


def test_create_backtrack_handoff_with_drift_info():
    from drift_checker import create_backtrack_handoff
    drift_info = {"feedback": ["[Stage0] crash", "[Stage1] incomplete"]}
    handoff = create_backtrack_handoff(5, 3, "s1", drift_info=drift_info)
    assert "[Stage0]" in handoff["reason"]
    assert handoff["to_phase"] == 3


def test_create_backtrack_handoff_validates():
    """Backtrack handoff should pass validate_handoff."""
    from drift_checker import create_backtrack_handoff
    from pipeline_schema import validate_handoff
    handoff = create_backtrack_handoff(5, 2, "s1")
    result = validate_handoff(handoff)
    assert result["valid"] is True
