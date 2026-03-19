"""Tests for drift_checker module."""

import json
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from drift_checker import (
    DRIFT_THRESHOLD,
    _log_drift,
    check_drift,
    decide_action,
    execute_backtrack,
    execute_restart,
    run_drift_check,
)


# ── Fixtures ────────────────────────────────────────────────────────


def _make_validation(drift_score=0.1, passed=True, action="pass", feedback=None):
    return {
        "version": "1.0",
        "session_id": "ses_test",
        "completed_at": "2026-01-01T00:00:00+00:00",
        "passed": passed,
        "drift_score": drift_score,
        "action": action,
        "stage1_mechanical": {"passed": True, "checks": []},
        "stage2_semantic": {"passed": True, "spec_alignment": 0.9, "notes": []},
        "stage3_consensus": {
            "passed": True,
            "advocate": "ok",
            "critic": "ok",
            "judge": "ok",
            "drift_score": drift_score,
        },
        "feedback": feedback or [],
    }


def _setup_validation(tmp_path, session_id, validation):
    """Save validation.json to tmp_path/{session_id}/."""
    from pipeline_schema import save_phase_output

    save_phase_output(validation, "validation", session_id)


def _setup_strategy(tmp_path, session_id):
    """Create a dummy strategy.json."""
    from pipeline_schema import create_strategy, save_phase_output

    strategy = create_strategy(session_id)
    save_phase_output(strategy, "strategy", session_id)


# ── check_drift ─────────────────────────────────────────────────────


class TestCheckDrift:
    def test_reads_drift_score(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("drift_checker.PIPELINES_DIR", tmp_path)

        validation = _make_validation(drift_score=0.25, passed=True, action="pass")
        _setup_validation(tmp_path, "ses_check", validation)

        result = check_drift("ses_check")

        assert result["drift_score"] == 0.25
        assert result["passed"] is True
        assert result["session_id"] == "ses_check"

    def test_defaults_on_missing_fields(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("drift_checker.PIPELINES_DIR", tmp_path)

        # Minimal validation without optional fields
        minimal = {"version": "1.0", "session_id": "ses_min", "completed_at": "x"}
        pipeline_dir = tmp_path / "ses_min"
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        (pipeline_dir / "validation.json").write_text(
            json.dumps(minimal, ensure_ascii=False), encoding="utf-8"
        )

        result = check_drift("ses_min")

        assert result["drift_score"] == 1.0  # default
        assert result["passed"] is False  # default

    def test_missing_validation_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("drift_checker.PIPELINES_DIR", tmp_path)

        with pytest.raises(FileNotFoundError):
            check_drift("ses_nonexistent")


# ── decide_action ───────────────────────────────────────────────────


class TestDecideAction:
    def test_complete_on_zero(self):
        assert decide_action(0.0) == "complete"

    def test_backtrack_on_low(self):
        assert decide_action(0.1) == "backtrack"
        assert decide_action(0.2) == "backtrack"
        assert decide_action(0.3) == "backtrack"

    def test_restart_on_high(self):
        assert decide_action(0.31) == "restart"
        assert decide_action(0.5) == "restart"
        assert decide_action(1.0) == "restart"

    def test_boundary(self):
        assert decide_action(DRIFT_THRESHOLD) == "backtrack"
        assert decide_action(DRIFT_THRESHOLD + 0.01) == "restart"

    def test_exact_zero(self):
        assert decide_action(0.0) == "complete"
        assert decide_action(0.001) == "backtrack"


# ── _log_drift ──────────────────────────────────────────────────────


class TestLogDrift:
    def test_creates_log_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("drift_checker.PIPELINES_DIR", tmp_path)

        path = _log_drift("ses_log", 0.2, "backtrack", reason="test")

        assert path.exists()
        records = json.loads(path.read_text(encoding="utf-8"))
        assert len(records) == 1
        assert records[0]["drift_score"] == 0.2
        assert records[0]["action"] == "backtrack"

    def test_appends_to_existing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("drift_checker.PIPELINES_DIR", tmp_path)

        _log_drift("ses_append", 0.1, "backtrack")
        _log_drift("ses_append", 0.5, "restart")

        log_path = tmp_path / "ses_append" / "drift_log.json"
        records = json.loads(log_path.read_text(encoding="utf-8"))
        assert len(records) == 2

    def test_handles_corrupt_log(self, tmp_path, monkeypatch):
        monkeypatch.setattr("drift_checker.PIPELINES_DIR", tmp_path)

        pipeline_dir = tmp_path / "ses_corrupt"
        pipeline_dir.mkdir(parents=True)
        (pipeline_dir / "drift_log.json").write_text("not json", encoding="utf-8")

        path = _log_drift("ses_corrupt", 0.4, "restart")

        records = json.loads(path.read_text(encoding="utf-8"))
        assert len(records) == 1


# ── execute_backtrack ───────────────────────────────────────────────


class TestExecuteBacktrack:
    def test_deletes_strategy(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("drift_checker.PIPELINES_DIR", tmp_path)

        _setup_strategy(tmp_path, "ses_bt")

        result = execute_backtrack("ses_bt")

        assert result["action"] == "backtrack"
        assert result["deleted"] is not None
        assert not (tmp_path / "ses_bt" / "strategy.json").exists()

    def test_no_strategy_to_delete(self, tmp_path, monkeypatch):
        monkeypatch.setattr("drift_checker.PIPELINES_DIR", tmp_path)

        result = execute_backtrack("ses_no_strat")

        assert result["action"] == "backtrack"
        assert result["deleted"] is None


# ── execute_restart ─────────────────────────────────────────────────


class TestExecuteRestart:
    def test_sends_alert(self, tmp_path, monkeypatch):
        monkeypatch.setattr("drift_checker.PIPELINES_DIR", tmp_path)

        alerts = []

        def mock_send_alert(title, body, webhook_url=None):
            alerts.append({"title": title, "body": body, "webhook_url": webhook_url})

        monkeypatch.setattr("headless.send_alert", mock_send_alert)

        result = execute_restart("ses_restart")

        assert result["action"] == "restart"
        assert result["alerted"] is True
        assert len(alerts) == 1
        assert "Phase 0" in alerts[0]["title"]

    def test_passes_webhook(self, tmp_path, monkeypatch):
        monkeypatch.setattr("drift_checker.PIPELINES_DIR", tmp_path)

        alerts = []

        def mock_send_alert(title, body, webhook_url=None):
            alerts.append({"webhook_url": webhook_url})

        monkeypatch.setattr("headless.send_alert", mock_send_alert)

        execute_restart("ses_wh", webhook_url="https://hooks.example.com/test")

        assert alerts[0]["webhook_url"] == "https://hooks.example.com/test"


# ── run_drift_check ─────────────────────────────────────────────────


class TestRunDriftCheck:
    def _setup(self, tmp_path, monkeypatch, session_id, drift_score, **kwargs):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("drift_checker.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

        # Mock send_alert to avoid macOS notifications during tests
        monkeypatch.setattr(
            "headless.send_alert",
            lambda title, body, webhook_url=None: None,
        )

        validation = _make_validation(drift_score=drift_score, **kwargs)
        _setup_validation(tmp_path, session_id, validation)

    def test_complete_on_zero(self, tmp_path, monkeypatch):
        self._setup(tmp_path, monkeypatch, "ses_zero", 0.0)

        result = run_drift_check("ses_zero")

        assert result["action"] == "complete"
        assert result["drift_score"] == 0.0

    def test_backtrack_on_low(self, tmp_path, monkeypatch):
        self._setup(tmp_path, monkeypatch, "ses_low", 0.2)

        # Create strategy.json so backtrack can delete it
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        _setup_strategy(tmp_path, "ses_low")

        result = run_drift_check("ses_low")

        assert result["action"] == "backtrack"
        assert not (tmp_path / "ses_low" / "strategy.json").exists()

    def test_restart_on_high(self, tmp_path, monkeypatch):
        self._setup(tmp_path, monkeypatch, "ses_high", 0.5, passed=False, action="restart")

        result = run_drift_check("ses_high")

        assert result["action"] == "restart"
        assert result["drift_score"] == 0.5

    def test_logs_drift(self, tmp_path, monkeypatch):
        self._setup(tmp_path, monkeypatch, "ses_logged", 0.15)

        run_drift_check("ses_logged")

        log_path = tmp_path / "ses_logged" / "drift_log.json"
        assert log_path.exists()
        records = json.loads(log_path.read_text(encoding="utf-8"))
        assert len(records) == 1
        assert records[0]["action"] == "backtrack"

    def test_progress_logged(self, tmp_path, monkeypatch):
        self._setup(tmp_path, monkeypatch, "ses_prog", 0.0)

        run_drift_check("ses_prog")

        progress_path = tmp_path / "ses_prog" / "progress.log"
        assert progress_path.exists()
        content = progress_path.read_text(encoding="utf-8")
        assert "phase5" in content


# ── CLI ─────────────────────────────────────────────────────────────


class TestCli:
    def test_check_command(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("drift_checker.PIPELINES_DIR", tmp_path)

        validation = _make_validation(drift_score=0.15)
        _setup_validation(tmp_path, "ses_cli_check", validation)

        from drift_checker import _parse_cli

        _parse_cli(["drift_checker.py", "check", "ses_cli_check"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert data["drift_score"] == 0.15
        assert data["session_id"] == "ses_cli_check"

    def test_decide_command(self, capsys):
        from drift_checker import _parse_cli

        _parse_cli(["drift_checker.py", "decide", "0.2"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert data["action"] == "backtrack"

    def test_decide_zero(self, capsys):
        from drift_checker import _parse_cli

        _parse_cli(["drift_checker.py", "decide", "0.0"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert data["action"] == "complete"

    def test_decide_high(self, capsys):
        from drift_checker import _parse_cli

        _parse_cli(["drift_checker.py", "decide", "0.8"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert data["action"] == "restart"

    def test_run_complete(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("drift_checker.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr(
            "headless.send_alert",
            lambda title, body, webhook_url=None: None,
        )

        validation = _make_validation(drift_score=0.0)
        _setup_validation(tmp_path, "ses_cli_run", validation)

        from drift_checker import _parse_cli

        _parse_cli(["drift_checker.py", "run", "ses_cli_run"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert data["action"] == "complete"

    def test_run_restart_exits_1(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("drift_checker.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr(
            "headless.send_alert",
            lambda title, body, webhook_url=None: None,
        )

        validation = _make_validation(drift_score=0.5, passed=False, action="restart")
        _setup_validation(tmp_path, "ses_cli_restart", validation)

        from drift_checker import _parse_cli

        with pytest.raises(SystemExit) as exc_info:
            _parse_cli(["drift_checker.py", "run", "ses_cli_restart"])

        assert exc_info.value.code == 1

    def test_run_backtrack_exits_2(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("drift_checker.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr(
            "headless.send_alert",
            lambda title, body, webhook_url=None: None,
        )

        validation = _make_validation(drift_score=0.2)
        _setup_validation(tmp_path, "ses_cli_bt", validation)

        from drift_checker import _parse_cli

        with pytest.raises(SystemExit) as exc_info:
            _parse_cli(["drift_checker.py", "run", "ses_cli_bt"])

        assert exc_info.value.code == 2

    def test_unknown_command_exits(self):
        from drift_checker import _parse_cli

        with pytest.raises(SystemExit):
            _parse_cli(["drift_checker.py", "bogus"])

    def test_no_args_exits(self):
        from drift_checker import _parse_cli

        with pytest.raises(SystemExit):
            _parse_cli(["drift_checker.py"])

    def test_check_missing_session_exits(self):
        from drift_checker import _parse_cli

        with pytest.raises(SystemExit):
            _parse_cli(["drift_checker.py", "check"])

    def test_decide_missing_score_exits(self):
        from drift_checker import _parse_cli

        with pytest.raises(SystemExit):
            _parse_cli(["drift_checker.py", "decide"])

    def test_decide_invalid_score_exits(self):
        from drift_checker import _parse_cli

        with pytest.raises(SystemExit):
            _parse_cli(["drift_checker.py", "decide", "abc"])

    def test_run_missing_session_exits(self):
        from drift_checker import _parse_cli

        with pytest.raises(SystemExit):
            _parse_cli(["drift_checker.py", "run"])
