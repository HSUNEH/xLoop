"""Tests for loop_engine module."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from session_manager import create_session, load_session


# ── Phase 1-1: start_loop, get_loop_state ──────────────────────────


class TestStartLoop:
    def test_initializes_loop_state(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import start_loop

        session = create_session("AI agents")
        result = start_loop(session["id"], "AI agent frameworks")

        assert result["status"] == "running"
        assert result["initial_query"] == "AI agent frameworks"
        assert result["max_iterations"] == 3
        assert result["current_iteration"] == 0
        assert result["iterations"] == []
        assert result["covered_topics"] == []
        assert result["all_queries"] == ["AI agent frameworks"]

    def test_custom_max_iterations(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import start_loop

        session = create_session("custom max")
        result = start_loop(session["id"], "query", max_iterations=5)

        assert result["max_iterations"] == 5

    def test_persists_to_session_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import start_loop

        session = create_session("persist test")
        start_loop(session["id"], "persistence query")

        reloaded = load_session(session["id"])
        assert "loop" in reloaded
        assert reloaded["loop"]["status"] == "running"
        assert reloaded["loop"]["initial_query"] == "persistence query"

    def test_raises_if_session_not_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import start_loop

        with pytest.raises(FileNotFoundError):
            start_loop("ses_nonexistent", "query")

    def test_raises_if_loop_already_exists(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import start_loop

        session = create_session("duplicate test")
        start_loop(session["id"], "first query")

        with pytest.raises(ValueError, match="already has"):
            start_loop(session["id"], "second query")


class TestGetLoopState:
    def test_returns_loop_state(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import get_loop_state, start_loop

        session = create_session("state test")
        start_loop(session["id"], "state query")

        state = get_loop_state(session["id"])
        assert state["status"] == "running"
        assert state["initial_query"] == "state query"

    def test_raises_if_no_loop(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import get_loop_state

        session = create_session("no loop")

        with pytest.raises(ValueError, match="no loop"):
            get_loop_state(session["id"])

    def test_raises_if_session_not_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import get_loop_state

        with pytest.raises(FileNotFoundError):
            get_loop_state("ses_nonexistent")


# ── Phase 1-2: add_iteration, check_termination ───────────────────


class TestAddIteration:
    def test_records_iteration(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import add_iteration, start_loop

        session = create_session("iteration test")
        start_loop(session["id"], "initial query")

        result = add_iteration(
            session["id"],
            queries=["query A", "query B"],
            sources_added=3,
            findings=["finding 1", "finding 2"],
            gaps=["gap 1"],
        )

        assert result["current_iteration"] == 1
        assert len(result["iterations"]) == 1
        iteration = result["iterations"][0]
        assert iteration["number"] == 1
        assert iteration["queries"] == ["query A", "query B"]
        assert iteration["sources_added"] == 3
        assert iteration["findings"] == ["finding 1", "finding 2"]
        assert iteration["gaps"] == ["gap 1"]
        assert "timestamp" in iteration

    def test_accumulates_queries(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import add_iteration, start_loop

        session = create_session("accumulate test")
        start_loop(session["id"], "initial")

        add_iteration(session["id"], queries=["q1"], sources_added=1, findings=[], gaps=["gap"])
        result = add_iteration(session["id"], queries=["q2", "q3"], sources_added=2, findings=[], gaps=[])

        assert result["current_iteration"] == 2
        assert result["all_queries"] == ["initial", "q1", "q2", "q3"]

    def test_updates_covered_topics(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import add_iteration, start_loop

        session = create_session("topics test")
        start_loop(session["id"], "initial")

        add_iteration(
            session["id"],
            queries=["q1"],
            sources_added=1,
            findings=["topic A covered"],
            gaps=["gap X"],
        )

        reloaded = load_session(session["id"])
        assert "topic A covered" in reloaded["loop"]["covered_topics"]

    def test_persists_to_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import add_iteration, start_loop

        session = create_session("persist iter")
        start_loop(session["id"], "initial")
        add_iteration(session["id"], queries=["q1"], sources_added=1, findings=["f1"], gaps=[])

        reloaded = load_session(session["id"])
        assert len(reloaded["loop"]["iterations"]) == 1
        assert reloaded["loop"]["current_iteration"] == 1

    def test_raises_if_no_loop(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import add_iteration

        session = create_session("no loop iter")

        with pytest.raises(ValueError, match="no loop"):
            add_iteration(session["id"], queries=[], sources_added=0, findings=[], gaps=[])

    def test_raises_if_loop_completed(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import add_iteration, end_loop, start_loop

        session = create_session("completed loop")
        start_loop(session["id"], "initial")
        end_loop(session["id"])

        with pytest.raises(ValueError, match="not running"):
            add_iteration(session["id"], queries=[], sources_added=0, findings=[], gaps=[])


class TestCheckTermination:
    def test_continue_when_gaps_remain(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import add_iteration, check_termination, start_loop

        session = create_session("continue test")
        start_loop(session["id"], "initial", max_iterations=3)
        add_iteration(session["id"], queries=["q1"], sources_added=1, findings=["f1"], gaps=["gap1"])

        result = check_termination(session["id"])
        assert result["should_terminate"] is False
        assert "gaps" in result["reason"].lower()

    def test_terminate_when_max_iterations_reached(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import add_iteration, check_termination, start_loop

        session = create_session("max iter test")
        start_loop(session["id"], "initial", max_iterations=2)
        add_iteration(session["id"], queries=["q1"], sources_added=1, findings=["f1"], gaps=["gap1"])
        add_iteration(session["id"], queries=["q2"], sources_added=1, findings=["f2"], gaps=["gap2"])

        result = check_termination(session["id"])
        assert result["should_terminate"] is True
        assert "max" in result["reason"].lower()

    def test_terminate_when_no_gaps(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import add_iteration, check_termination, start_loop

        session = create_session("no gaps test")
        start_loop(session["id"], "initial", max_iterations=5)
        add_iteration(session["id"], queries=["q1"], sources_added=1, findings=["f1"], gaps=[])

        result = check_termination(session["id"])
        assert result["should_terminate"] is True
        assert "gap" in result["reason"].lower() or "no" in result["reason"].lower()

    def test_raises_if_no_loop(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import check_termination

        session = create_session("no loop check")

        with pytest.raises(ValueError, match="no loop"):
            check_termination(session["id"])


# ── Phase 1-3: get_unused_queries, end_loop ────────────────────────


class TestGetUnusedQueries:
    def test_filters_used_queries(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import add_iteration, get_unused_queries, start_loop

        session = create_session("filter test")
        start_loop(session["id"], "initial query")
        add_iteration(session["id"], queries=["q1", "q2"], sources_added=1, findings=[], gaps=["gap"])

        unused = get_unused_queries(session["id"], ["q1", "q3", "q4"])
        assert unused == ["q3", "q4"]

    def test_returns_all_if_none_used(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import get_unused_queries, start_loop

        session = create_session("all unused")
        start_loop(session["id"], "initial")

        unused = get_unused_queries(session["id"], ["new1", "new2"])
        assert unused == ["new1", "new2"]

    def test_returns_empty_if_all_used(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import get_unused_queries, start_loop

        session = create_session("all used")
        start_loop(session["id"], "initial")

        unused = get_unused_queries(session["id"], ["initial"])
        assert unused == []

    def test_raises_if_no_loop(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import get_unused_queries

        session = create_session("no loop filter")

        with pytest.raises(ValueError, match="no loop"):
            get_unused_queries(session["id"], ["q1"])


class TestEndLoop:
    def test_marks_loop_completed(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import end_loop, start_loop

        session = create_session("end test")
        start_loop(session["id"], "initial")

        result = end_loop(session["id"])
        assert result["status"] == "completed"

    def test_persists_completed_status(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import end_loop, start_loop

        session = create_session("persist end")
        start_loop(session["id"], "initial")
        end_loop(session["id"])

        reloaded = load_session(session["id"])
        assert reloaded["loop"]["status"] == "completed"

    def test_raises_if_no_loop(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import end_loop

        session = create_session("no loop end")

        with pytest.raises(ValueError, match="no loop"):
            end_loop(session["id"])


# ── Phase 1-4: CLI 파싱 ───────────────────────────────────────────


class TestCli:
    def test_start_command(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import _parse_cli

        session = create_session("cli start")
        _parse_cli(["loop_engine.py", "start", session["id"], "test query"])

        captured = capsys.readouterr()
        assert "running" in captured.out.lower() or "started" in captured.out.lower()

        reloaded = load_session(session["id"])
        assert reloaded["loop"]["initial_query"] == "test query"

    def test_start_with_max_iterations(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import _parse_cli

        session = create_session("cli max iter")
        _parse_cli(["loop_engine.py", "start", session["id"], "query", "--max-iterations", "5"])

        reloaded = load_session(session["id"])
        assert reloaded["loop"]["max_iterations"] == 5

    def test_status_command(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import _parse_cli, start_loop

        session = create_session("cli status")
        start_loop(session["id"], "status query")

        _parse_cli(["loop_engine.py", "status", session["id"]])
        captured = capsys.readouterr()
        assert "running" in captured.out.lower()

    def test_status_json_flag(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import _parse_cli, start_loop

        session = create_session("cli json status")
        start_loop(session["id"], "json query")

        _parse_cli(["loop_engine.py", "status", session["id"], "--json"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["status"] == "running"

    def test_add_iteration_command(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import _parse_cli, start_loop

        session = create_session("cli add iter")
        start_loop(session["id"], "initial")

        _parse_cli([
            "loop_engine.py", "add-iteration", session["id"],
            "--queries-json", '["q1", "q2"]',
            "--sources-added", "3",
            "--findings-json", '["finding1"]',
            "--gaps-json", '["gap1"]',
        ])
        captured = capsys.readouterr()
        assert "iteration" in captured.out.lower() or "added" in captured.out.lower()

        reloaded = load_session(session["id"])
        assert reloaded["loop"]["current_iteration"] == 1

    def test_check_command(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import _parse_cli, add_iteration, start_loop

        session = create_session("cli check")
        start_loop(session["id"], "initial")
        add_iteration(session["id"], queries=["q1"], sources_added=1, findings=["f1"], gaps=[])

        _parse_cli(["loop_engine.py", "check", session["id"]])
        captured = capsys.readouterr()
        assert "terminate" in captured.out.lower() or "yes" in captured.out.lower()

    def test_filter_queries_command(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import _parse_cli, start_loop

        session = create_session("cli filter")
        start_loop(session["id"], "initial")

        _parse_cli([
            "loop_engine.py", "filter-queries", session["id"],
            "--candidates-json", '["initial", "new query"]',
        ])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data == ["new query"]

    def test_end_command(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import _parse_cli, start_loop

        session = create_session("cli end")
        start_loop(session["id"], "initial")

        _parse_cli(["loop_engine.py", "end", session["id"]])
        captured = capsys.readouterr()
        assert "completed" in captured.out.lower() or "ended" in captured.out.lower()

    def test_unknown_command_exits(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import _parse_cli

        with pytest.raises(SystemExit):
            _parse_cli(["loop_engine.py", "bogus"])

    def test_no_args_exits(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("loop_engine.SESSIONS_DIR", tmp_path)
        from loop_engine import _parse_cli

        with pytest.raises(SystemExit):
            _parse_cli(["loop_engine.py"])
