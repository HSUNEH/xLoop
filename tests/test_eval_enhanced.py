#!/usr/bin/env python3
"""Tests for enhanced evaluation engine (US-005)."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from evaluation_engine import (
    SEMANTIC_MATCH_WEIGHTS,
    _artifact_completeness,
    _keyword_match,
    _semantic_match_score,
    _tool_type_match,
    cross_validate_findings,
    save_validation_history,
    show_trend,
)


# ── SEMANTIC_MATCH_WEIGHTS ──────────────────────────────────────────

def test_weights_sum_to_one():
    total = sum(SEMANTIC_MATCH_WEIGHTS.values())
    assert abs(total - 1.0) < 1e-9


def test_weights_keys():
    assert set(SEMANTIC_MATCH_WEIGHTS.keys()) == {"keyword", "tool_type", "completeness"}


# ── _keyword_match ──────────────────────────────────────────────────

def test_keyword_match_full():
    artifacts = [{"artifact": {"output": "image thumbnail visual"}, "task_id": "t1"}]
    score = _keyword_match("image thumbnail", artifacts)
    assert score >= 0.5


def test_keyword_match_none():
    artifacts = [{"artifact": {"output": "code script"}, "task_id": "t1"}]
    score = _keyword_match("image thumbnail visual", artifacts)
    assert score == 0.0


def test_keyword_match_empty_deliverable():
    score = _keyword_match("", [])
    assert score == 0.0


# ── _tool_type_match ────────────────────────────────────────────────

def test_tool_type_match_image():
    artifacts = [{"tool": "dall-e", "status": "done"}]
    score = _tool_type_match("이미지 생성", artifacts)
    assert score >= 0.5


def test_tool_type_match_no_hint():
    artifacts = [{"tool": "claude", "status": "done"}]
    score = _tool_type_match("general task", artifacts)
    assert score == 1.0  # No specific tool expected


# ── _artifact_completeness ──────────────────────────────────────────

def test_completeness_all_done():
    artifacts = [{"status": "done"}, {"status": "done"}]
    assert _artifact_completeness(artifacts) == 1.0


def test_completeness_partial():
    artifacts = [{"status": "done"}, {"status": "failed"}]
    assert _artifact_completeness(artifacts) == 0.5


def test_completeness_empty():
    assert _artifact_completeness([]) == 0.0


# ── _semantic_match_score ───────────────────────────────────────────

def test_semantic_match_score_range():
    artifacts = [{"artifact": {"output": "test"}, "tool": "claude", "status": "done", "task_id": "t1"}]
    score = _semantic_match_score("test output", artifacts)
    assert 0.0 <= score <= 1.0


# ── cross_validate_findings ─────────────────────────────────────────

def test_cross_validate_empty():
    result = cross_validate_findings({})
    assert result["findings"] == []
    assert result["avg_confidence"] == 0.0


def test_cross_validate_single_source():
    data = {
        "findings": ["machine learning is important"],
        "sources": [{"type": "web", "content": "machine learning advances"}],
    }
    result = cross_validate_findings(data)
    assert len(result["findings"]) == 1
    assert result["findings"][0]["confidence"] >= 0.5


def test_cross_validate_multi_source():
    data = {
        "findings": ["deep learning trends"],
        "sources": [
            {"type": "web", "content": "deep learning trends in 2026"},
            {"type": "arxiv", "content": "deep learning paper"},
            {"type": "youtube", "content": "unrelated cooking video"},
        ],
    }
    result = cross_validate_findings(data)
    f = result["findings"][0]
    assert len(f["source_types"]) >= 2  # web and arxiv should match
    assert f["confidence"] > 0.0


def test_cross_validate_no_match():
    data = {
        "findings": ["quantum computing breakthrough"],
        "sources": [{"type": "web", "content": "cooking recipe"}],
    }
    result = cross_validate_findings(data)
    assert result["findings"][0]["confidence"] == 0.0


# ── save_validation_history / show_trend ────────────────────────────

def test_save_validation_history(tmp_path, monkeypatch):
    import evaluation_engine
    monkeypatch.setattr(evaluation_engine, "PIPELINES_DIR", tmp_path)

    validation = {"drift_score": 0.5, "passed": False, "action": "backtrack",
                   "stage2_semantic": {"spec_alignment": 0.4}}
    save_validation_history("s1", validation)

    history_path = tmp_path / "s1" / "validation_history.json"
    assert history_path.exists()
    records = json.loads(history_path.read_text(encoding="utf-8"))
    assert len(records) == 1
    assert records[0]["drift_score"] == 0.5


def test_save_validation_history_appends(tmp_path, monkeypatch):
    import evaluation_engine
    monkeypatch.setattr(evaluation_engine, "PIPELINES_DIR", tmp_path)

    save_validation_history("s1", {"drift_score": 0.8, "passed": False, "action": "restart"})
    save_validation_history("s1", {"drift_score": 0.3, "passed": False, "action": "backtrack"})
    save_validation_history("s1", {"drift_score": 0.0, "passed": True, "action": "complete"})

    records = json.loads((tmp_path / "s1" / "validation_history.json").read_text(encoding="utf-8"))
    assert len(records) == 3


def test_show_trend_improving(tmp_path, monkeypatch):
    import evaluation_engine
    monkeypatch.setattr(evaluation_engine, "PIPELINES_DIR", tmp_path)

    save_validation_history("s1", {"drift_score": 0.8, "passed": False, "action": "restart"})
    save_validation_history("s1", {"drift_score": 0.3, "passed": False, "action": "backtrack"})
    save_validation_history("s1", {"drift_score": 0.0, "passed": True, "action": "complete"})

    trend = show_trend("s1")
    assert trend["evaluations"] == 3
    assert trend["trend"] == "improving"
    assert trend["drift_scores"] == [0.8, 0.3, 0.0]


def test_show_trend_degrading(tmp_path, monkeypatch):
    import evaluation_engine
    monkeypatch.setattr(evaluation_engine, "PIPELINES_DIR", tmp_path)

    save_validation_history("s1", {"drift_score": 0.1, "passed": False, "action": "backtrack"})
    save_validation_history("s1", {"drift_score": 0.5, "passed": False, "action": "backtrack"})

    trend = show_trend("s1")
    assert trend["trend"] == "degrading"


def test_show_trend_none(tmp_path, monkeypatch):
    import evaluation_engine
    monkeypatch.setattr(evaluation_engine, "PIPELINES_DIR", tmp_path)

    trend = show_trend("nonexistent")
    assert trend["trend"] == "none"
    assert trend["evaluations"] == 0
