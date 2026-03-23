#!/usr/bin/env python3
"""Tests for _io_utils — atomic writes, advisory locks, .bak backup/recovery."""

import json
import os
import sys

import pytest

# Ensure scripts/ is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from _io_utils import (
    _atomic_write_json,
    _locked_file,
    _rotate_backups,
    load_json_with_recovery,
    locked_write_json,
    save_json_with_backup,
)


# ── _atomic_write_json ──────────────────────────────────────────────

def test_atomic_write_creates_file(tmp_path):
    path = tmp_path / "data.json"
    _atomic_write_json(path, {"key": "value"})
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data == {"key": "value"}


def test_atomic_write_overwrites_existing(tmp_path):
    path = tmp_path / "data.json"
    _atomic_write_json(path, {"v": 1})
    _atomic_write_json(path, {"v": 2})
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["v"] == 2


def test_atomic_write_preserves_unicode(tmp_path):
    path = tmp_path / "data.json"
    _atomic_write_json(path, {"한글": "테스트"})
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["한글"] == "테스트"


def test_atomic_write_no_leftover_tmp_on_success(tmp_path):
    path = tmp_path / "data.json"
    _atomic_write_json(path, {"ok": True})
    tmp_files = list(tmp_path.glob("*.tmp"))
    assert len(tmp_files) == 0


def test_atomic_write_creates_parent_dirs(tmp_path):
    path = tmp_path / "sub" / "dir" / "data.json"
    _atomic_write_json(path, {"nested": True})
    assert path.exists()


# ── _locked_file ────────────────────────────────────────────────────

def test_locked_file_context_manager(tmp_path):
    path = tmp_path / "data.json"
    _atomic_write_json(path, {"x": 1})
    with _locked_file(path):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["x"] == 1


def test_locked_write_json(tmp_path):
    path = tmp_path / "data.json"
    locked_write_json(path, {"locked": True})
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["locked"] is True


# ── .bak rotation ───────────────────────────────────────────────────

def test_rotate_backups_creates_bak1(tmp_path):
    path = tmp_path / "data.json"
    path.write_text('{"v": 1}', encoding="utf-8")
    _rotate_backups(path)
    bak1 = path.with_suffix(".bak.1")
    assert bak1.exists()
    assert json.loads(bak1.read_text(encoding="utf-8"))["v"] == 1


def test_rotate_backups_shifts_existing(tmp_path):
    path = tmp_path / "data.json"
    # Create initial file and first backup
    path.write_text('{"v": 1}', encoding="utf-8")
    _rotate_backups(path)
    # Overwrite and rotate again
    path.write_text('{"v": 2}', encoding="utf-8")
    _rotate_backups(path)
    bak1 = path.with_suffix(".bak.1")
    bak2 = path.with_suffix(".bak.2")
    assert json.loads(bak1.read_text(encoding="utf-8"))["v"] == 2
    assert json.loads(bak2.read_text(encoding="utf-8"))["v"] == 1


def test_rotate_backups_max_three(tmp_path):
    path = tmp_path / "data.json"
    for i in range(5):
        path.write_text(json.dumps({"v": i}), encoding="utf-8")
        _rotate_backups(path)
    # Only .bak.1, .bak.2, .bak.3 should exist
    assert path.with_suffix(".bak.1").exists()
    assert path.with_suffix(".bak.2").exists()
    assert path.with_suffix(".bak.3").exists()
    assert not path.with_suffix(".bak.4").exists()


# ── save_json_with_backup ───────────────────────────────────────────

def test_save_json_with_backup(tmp_path):
    path = tmp_path / "data.json"
    save_json_with_backup(path, {"v": 1})
    assert json.loads(path.read_text(encoding="utf-8"))["v"] == 1
    save_json_with_backup(path, {"v": 2})
    assert json.loads(path.read_text(encoding="utf-8"))["v"] == 2
    bak1 = path.with_suffix(".bak.1")
    assert json.loads(bak1.read_text(encoding="utf-8"))["v"] == 1


# ── load_json_with_recovery ─────────────────────────────────────────

def test_load_json_with_recovery_normal(tmp_path):
    path = tmp_path / "data.json"
    _atomic_write_json(path, {"ok": True})
    data = load_json_with_recovery(path)
    assert data["ok"] is True


def test_load_json_with_recovery_from_backup(tmp_path):
    path = tmp_path / "data.json"
    # Create a good backup
    bak1 = path.with_suffix(".bak.1")
    bak1.write_text('{"recovered": true}', encoding="utf-8")
    # Write corrupted main file
    path.write_text("{corrupted", encoding="utf-8")
    data = load_json_with_recovery(path)
    assert data["recovered"] is True
    # Main file should now be restored
    assert json.loads(path.read_text(encoding="utf-8"))["recovered"] is True


def test_load_json_with_recovery_no_file(tmp_path):
    path = tmp_path / "nonexistent.json"
    with pytest.raises(FileNotFoundError):
        load_json_with_recovery(path)


def test_load_json_with_recovery_all_corrupted(tmp_path):
    path = tmp_path / "data.json"
    path.write_text("{bad", encoding="utf-8")
    path.with_suffix(".bak.1").write_text("{bad1", encoding="utf-8")
    path.with_suffix(".bak.2").write_text("{bad2", encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        load_json_with_recovery(path)


# ── validate_handoff backtrack support ──────────────────────────────

def test_validate_handoff_forward_ok():
    from pipeline_schema import validate_handoff

    data = {
        "version": "1.0",
        "from_phase": 1,
        "to_phase": 2,
        "session_id": "test",
        "timestamp": "2026-01-01T00:00:00",
        "status": "success",
    }
    result = validate_handoff(data)
    assert result["valid"] is True


def test_validate_handoff_forward_rejects_backward():
    from pipeline_schema import validate_handoff

    data = {
        "version": "1.0",
        "from_phase": 3,
        "to_phase": 2,
        "session_id": "test",
        "timestamp": "2026-01-01T00:00:00",
        "status": "success",
    }
    result = validate_handoff(data)
    assert result["valid"] is False


def test_validate_handoff_backtrack_ok():
    from pipeline_schema import validate_handoff

    data = {
        "version": "1.0",
        "from_phase": 5,
        "to_phase": 2,
        "session_id": "test",
        "timestamp": "2026-01-01T00:00:00",
        "status": "success",
        "type": "backtrack",
    }
    result = validate_handoff(data)
    assert result["valid"] is True


def test_validate_handoff_backtrack_rejects_forward():
    from pipeline_schema import validate_handoff

    data = {
        "version": "1.0",
        "from_phase": 2,
        "to_phase": 5,
        "session_id": "test",
        "timestamp": "2026-01-01T00:00:00",
        "status": "success",
        "type": "backtrack",
    }
    result = validate_handoff(data)
    assert result["valid"] is False


def test_validate_handoff_default_is_forward():
    from pipeline_schema import validate_handoff

    # No "type" field — should default to forward behavior
    data = {
        "version": "1.0",
        "from_phase": 3,
        "to_phase": 1,
        "session_id": "test",
        "timestamp": "2026-01-01T00:00:00",
        "status": "success",
    }
    result = validate_handoff(data)
    assert result["valid"] is False
