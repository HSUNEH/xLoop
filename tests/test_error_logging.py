#!/usr/bin/env python3
"""Tests for structured error handling and logging (US-002)."""

import json
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from _io_utils import _handle_error, make_error


# ── make_error ──────────────────────────────────────────────────────

def test_make_error_basic():
    err = make_error("E101", "Session not found")
    assert err["error_code"] == "E101"
    assert err["message"] == "Session not found"
    assert err["phase"] is None
    assert err["recoverable"] is False
    assert err["context"] == {}
    assert "timestamp" in err


def test_make_error_with_phase():
    err = make_error("E301", "Tool failed", phase=3)
    assert err["phase"] == 3


def test_make_error_recoverable():
    err = make_error("E201", "Timeout", recoverable=True)
    assert err["recoverable"] is True


def test_make_error_with_context():
    err = make_error("E401", "Low alignment", context={"score": 0.3})
    assert err["context"]["score"] == 0.3


def test_make_error_code_format():
    """Error codes should follow Exxx pattern."""
    err = make_error("E501", "Drift too high")
    assert err["error_code"].startswith("E")
    assert len(err["error_code"]) == 4


# ── _handle_error ───────────────────────────────────────────────────

def test_handle_error_stderr(capsys):
    err = make_error("E101", "Session corrupt", phase=1)
    _handle_error(err)
    captured = capsys.readouterr()
    assert "[E101]" in captured.err
    assert "Session corrupt" in captured.err
    assert "[Phase 1]" in captured.err


def test_handle_error_writes_jsonl(tmp_path):
    log_path = tmp_path / "progress.jsonl"
    err = make_error("E301", "Execution failed", phase=3)
    _handle_error(err, log_path=log_path)
    assert log_path.exists()
    entry = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert entry["error_code"] == "E301"
    assert entry["level"] == "error"
    assert entry["phase"] == 3


def test_handle_error_appends_to_jsonl(tmp_path):
    log_path = tmp_path / "progress.jsonl"
    _handle_error(make_error("E101", "Error 1"), log_path=log_path)
    _handle_error(make_error("E102", "Error 2"), log_path=log_path)
    lines = log_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2


def test_handle_error_no_log_path(capsys):
    """Should still print to stderr even without log_path."""
    err = make_error("E201", "Search failed")
    _handle_error(err)
    captured = capsys.readouterr()
    assert "[E201]" in captured.err


# ── headless.py logging ─────────────────────────────────────────────

def test_log_progress_structured(tmp_path, monkeypatch):
    from headless import log_progress_structured, PIPELINES_DIR
    monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

    log_progress_structured("test_session", "research", "Found 5 sources")
    jsonl_path = tmp_path / "test_session" / "progress.jsonl"
    assert jsonl_path.exists()
    entry = json.loads(jsonl_path.read_text(encoding="utf-8").strip())
    assert entry["session_id"] == "test_session"
    assert entry["phase"] == "research"
    assert entry["msg"] == "Found 5 sources"
    assert entry["level"] == "info"


def test_log_progress_structured_with_duration(tmp_path, monkeypatch):
    from headless import log_progress_structured
    monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

    log_progress_structured("s1", "execution", "Task done", duration_ms=1500)
    entry = json.loads((tmp_path / "s1" / "progress.jsonl").read_text(encoding="utf-8").strip())
    assert entry["duration_ms"] == 1500


def test_log_progress_structured_with_error(tmp_path, monkeypatch):
    from headless import log_progress_structured
    monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

    err = {"error_code": "E301", "message": "Tool timeout"}
    log_progress_structured("s1", "execution", "Failed", level="error", error=err)
    entry = json.loads((tmp_path / "s1" / "progress.jsonl").read_text(encoding="utf-8").strip())
    assert entry["level"] == "error"
    assert entry["error"]["error_code"] == "E301"


# ── phase_timer ─────────────────────────────────────────────────────

def test_phase_timer():
    from headless import phase_timer, phase_timer_end

    t = phase_timer()
    time.sleep(0.01)
    elapsed = phase_timer_end(t)
    assert elapsed >= 10  # at least 10ms
    assert isinstance(elapsed, int)


# ── summarize_logs ──────────────────────────────────────────────────

def test_summarize_logs_empty(tmp_path, monkeypatch):
    from headless import summarize_logs
    monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

    result = summarize_logs("nonexistent")
    assert result["total"] == 0
    assert result["errors"] == 0


def test_summarize_logs_with_entries(tmp_path, monkeypatch):
    from headless import summarize_logs
    monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

    session_dir = tmp_path / "s1"
    session_dir.mkdir()
    jsonl = session_dir / "progress.jsonl"

    entries = [
        {"ts": "2026-01-01T00:00:00", "level": "info", "phase": "research", "msg": "ok"},
        {"ts": "2026-01-01T00:01:00", "level": "error", "phase": "execution", "msg": "fail"},
        {"ts": "2026-01-01T00:02:00", "level": "warning", "phase": "research", "msg": "slow"},
        {"ts": "2026-01-01T00:03:00", "level": "info", "phase": "execution", "msg": "retry ok"},
    ]
    jsonl.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in entries) + "\n")

    result = summarize_logs("s1")
    assert result["total"] == 4
    assert result["errors"] == 1
    assert result["warnings"] == 1
    assert result["phases"]["research"]["count"] == 2
    assert result["phases"]["research"]["warnings"] == 1
    assert result["phases"]["execution"]["errors"] == 1


# ── log_progress writes both .log and .jsonl ────────────────────────

def test_log_progress_dual_output(tmp_path, monkeypatch):
    from headless import log_progress
    monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

    log_progress("s1", "strategy", "Building task list")
    log_path = tmp_path / "s1" / "progress.log"
    jsonl_path = tmp_path / "s1" / "progress.jsonl"
    assert log_path.exists()
    assert jsonl_path.exists()
    assert "Building task list" in log_path.read_text(encoding="utf-8")
    entry = json.loads(jsonl_path.read_text(encoding="utf-8").strip())
    assert entry["msg"] == "Building task list"
