#!/usr/bin/env python3
"""Tests for cost tracking and observability (US-006)."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


# ── track_cost ──────────────────────────────────────────────────────

def test_track_cost_basic(tmp_path, monkeypatch):
    import pal_router
    monkeypatch.setattr(pal_router, "PIPELINES_DIR", tmp_path)

    result = pal_router.track_cost("s1", 0, "standard")
    assert result["recorded"] is True
    assert result["cost"] == 10  # standard cost_multiplier
    assert result["total"] == 10


def test_track_cost_accumulates(tmp_path, monkeypatch):
    import pal_router
    monkeypatch.setattr(pal_router, "PIPELINES_DIR", tmp_path)

    pal_router.track_cost("s1", 0, "standard")  # 10
    pal_router.track_cost("s1", 1, "frugal")    # 1
    result = pal_router.track_cost("s1", 4, "frontier")  # 30
    assert result["total"] == 41


def test_track_cost_uses_model_tiers(tmp_path, monkeypatch):
    import pal_router
    monkeypatch.setattr(pal_router, "PIPELINES_DIR", tmp_path)

    r1 = pal_router.track_cost("s1", 1, "frugal")
    assert r1["cost"] == 1

    r2 = pal_router.track_cost("s1", 2, "standard")
    assert r2["cost"] == 10

    r3 = pal_router.track_cost("s1", 4, "frontier")
    assert r3["cost"] == 30


def test_track_cost_writes_log_file(tmp_path, monkeypatch):
    import pal_router
    monkeypatch.setattr(pal_router, "PIPELINES_DIR", tmp_path)

    pal_router.track_cost("s1", 0, "standard")
    log_path = tmp_path / "s1" / "cost_log.json"
    assert log_path.exists()
    records = json.loads(log_path.read_text(encoding="utf-8"))
    assert len(records) == 1
    assert records[0]["phase"] == 0
    assert records[0]["tier"] == "standard"
    assert "timestamp" in records[0]


# ── check_budget ────────────────────────────────────────────────────

def test_check_budget_no_cost(tmp_path, monkeypatch):
    import pal_router
    monkeypatch.setattr(pal_router, "PIPELINES_DIR", tmp_path)

    result = pal_router.check_budget("s1", 100)
    assert result["total_cost"] == 0
    assert result["warning"] is False
    assert result["exceeded"] is False


def test_check_budget_warning(tmp_path, monkeypatch):
    import pal_router
    monkeypatch.setattr(pal_router, "PIPELINES_DIR", tmp_path)

    # Budget 100, spend 85
    for _ in range(8):
        pal_router.track_cost("s1", 2, "standard")  # 8 * 10 = 80
    pal_router.track_cost("s1", 1, "frugal")  # +1 = 81
    # Not at 80% yet, spend more
    pal_router.track_cost("s1", 1, "frugal")  # +1 = 82
    pal_router.track_cost("s1", 1, "frugal")  # +1 = 83

    result = pal_router.check_budget("s1", 100)
    assert result["warning"] is True
    assert result["exceeded"] is False


def test_check_budget_exceeded(tmp_path, monkeypatch):
    import pal_router
    monkeypatch.setattr(pal_router, "PIPELINES_DIR", tmp_path)

    for _ in range(10):
        pal_router.track_cost("s1", 2, "standard")  # 10 * 10 = 100

    result = pal_router.check_budget("s1", 100)
    assert result["exceeded"] is True
    assert result["percent"] >= 100.0


def test_check_budget_no_limit(tmp_path, monkeypatch):
    import pal_router
    monkeypatch.setattr(pal_router, "PIPELINES_DIR", tmp_path)

    pal_router.track_cost("s1", 0, "standard")
    result = pal_router.check_budget("s1", 0)
    assert result["warning"] is False


# ── generate_dashboard ──────────────────────────────────────────────

def test_generate_dashboard_empty(tmp_path, monkeypatch):
    import headless
    monkeypatch.setattr(headless, "PIPELINES_DIR", tmp_path)

    result = headless.generate_dashboard("nonexistent")
    assert result["total_cost"] == 0
    assert result["errors"] == 0


def test_generate_dashboard_with_data(tmp_path, monkeypatch):
    import headless
    import pal_router
    monkeypatch.setattr(headless, "PIPELINES_DIR", tmp_path)
    monkeypatch.setattr(pal_router, "PIPELINES_DIR", tmp_path)

    # Add costs
    pal_router.track_cost("s1", 0, "standard")
    pal_router.track_cost("s1", 1, "frugal")

    # Add logs
    headless.log_progress_structured("s1", "research", "ok")
    headless.log_progress_structured("s1", "execution", "fail", level="error")

    result = headless.generate_dashboard("s1")
    assert result["total_cost"] == 11
    assert result["errors"] == 1
    assert result["log_entries"] == 2


# ── generate_summary ────────────────────────────────────────────────

def test_generate_summary(tmp_path, monkeypatch):
    import headless
    import pal_router
    monkeypatch.setattr(headless, "PIPELINES_DIR", tmp_path)
    monkeypatch.setattr(pal_router, "PIPELINES_DIR", tmp_path)

    pal_router.track_cost("s1", 0, "standard")
    headless.log_progress_structured("s1", "research", "done")

    summary = headless.generate_summary("s1")
    assert summary["session_id"] == "s1"
    assert summary["total_cost"] == 10
    assert "completed_at" in summary

    # Check file was saved
    summary_path = tmp_path / "s1" / "summary.json"
    assert summary_path.exists()
    saved = json.loads(summary_path.read_text(encoding="utf-8"))
    assert saved["total_cost"] == 10


def test_generate_summary_with_backtracks(tmp_path, monkeypatch):
    import headless
    monkeypatch.setattr(headless, "PIPELINES_DIR", tmp_path)

    session_dir = tmp_path / "s1"
    session_dir.mkdir()
    drift_log = [
        {"action": "backtrack", "drift_score": 0.2},
        {"action": "backtrack", "drift_score": 0.1},
        {"action": "complete", "drift_score": 0.0},
    ]
    (session_dir / "drift_log.json").write_text(json.dumps(drift_log), encoding="utf-8")

    summary = headless.generate_summary("s1")
    assert summary["backtrack_count"] == 2
