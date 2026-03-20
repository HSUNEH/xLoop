"""Tests for execution_engine module."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from execution_engine import (
    _TOOL_REGISTRY,
    _check_endpoint,
    _find_free_port,
    _wait_for_server,
    execute_task,
    get_execution_status,
    get_tool,
    list_tools,
    register_tool,
    run_execution,
    run_smoke_test,
    show_execution,
)


# ── Tool Registry ────────────────────────────────────────────────────


class TestRegisterTool:
    def test_register_and_get(self):
        def my_tool(task, session_id):
            return {"ok": True}

        register_tool("test_tool", my_tool)
        assert get_tool("test_tool") is my_tool
        # Cleanup
        _TOOL_REGISTRY.pop("test_tool", None)

    def test_get_unknown_returns_none(self):
        assert get_tool("nonexistent_tool_xyz") is None

    def test_overwrite_existing(self):
        def fn_a(task, sid):
            return "a"

        def fn_b(task, sid):
            return "b"

        register_tool("overwrite_test", fn_a)
        register_tool("overwrite_test", fn_b)
        assert get_tool("overwrite_test") is fn_b
        _TOOL_REGISTRY.pop("overwrite_test", None)


class TestListTools:
    def test_default_tools_registered(self):
        tools = list_tools()
        assert "claude" in tools
        assert "dall-e" in tools
        assert "flux" in tools
        assert "notebooklm" in tools
        assert "web_search" in tools

    def test_sorted(self):
        tools = list_tools()
        assert tools == sorted(tools)


class TestDefaultStubs:
    def test_claude_stub(self):
        fn = get_tool("claude")
        result = fn({"id": "t1", "title": "Test"}, "ses_test")
        assert result["type"] == "text"
        assert result["task_id"] == "t1"
        assert result["tool"] == "claude"

    def test_dall_e_stub(self):
        fn = get_tool("dall-e")
        result = fn({"id": "t2", "title": "Image"}, "ses_test")
        assert result["type"] == "image"
        assert result["tool"] == "dall-e"

    def test_flux_stub(self):
        fn = get_tool("flux")
        result = fn({"id": "t3", "title": "Video"}, "ses_test")
        assert result["type"] == "video"

    def test_notebooklm_stub(self):
        fn = get_tool("notebooklm")
        result = fn({"id": "t4", "title": "Doc"}, "ses_test")
        assert result["type"] == "document"

    def test_web_search_stub(self):
        fn = get_tool("web_search")
        result = fn({"id": "t5", "title": "Search"}, "ses_test")
        assert result["type"] == "search_result"


# ── Smoke Test ───────────────────────────────────────────────────────


class TestFindFreePort:
    def test_returns_int(self):
        port = _find_free_port()
        assert isinstance(port, int)
        assert port > 0

    def test_returns_different_ports(self):
        ports = {_find_free_port() for _ in range(5)}
        assert len(ports) >= 2  # OS may reuse, but typically different


class TestRunSmokeTest:
    def test_no_start_command_skips(self, tmp_path, monkeypatch):
        monkeypatch.setattr("execution_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

        result = run_smoke_test("ses_smoke", [], strategy={})

        assert result["passed"] is True
        assert result["server_started"] is False
        assert "skipped" in result["error"]

    def test_no_strategy_skips(self, tmp_path, monkeypatch):
        monkeypatch.setattr("execution_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

        result = run_smoke_test("ses_smoke", [], strategy=None)

        assert result["passed"] is True
        assert result["server_started"] is False

    def test_bad_start_command_fails(self, tmp_path, monkeypatch):
        monkeypatch.setattr("execution_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

        strategy = {
            "smoke_test": {
                "start_command": "/nonexistent/binary/that/does/not/exist --port {port}",
                "endpoints": [{"path": "/", "method": "GET"}],
            }
        }
        result = run_smoke_test("ses_bad", [], strategy=strategy)

        assert result["passed"] is False
        assert result["server_started"] is False

    def test_server_timeout_fails(self, tmp_path, monkeypatch):
        monkeypatch.setattr("execution_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("execution_engine._SMOKE_SERVER_TIMEOUT", 1)

        # Use a command that runs but doesn't listen on the port
        strategy = {
            "smoke_test": {
                "start_command": "sleep 10",
                "endpoints": [{"path": "/", "method": "GET"}],
            }
        }
        result = run_smoke_test("ses_timeout", [], strategy=strategy)

        assert result["passed"] is False
        assert result["server_started"] is False
        assert "did not respond" in result["error"]

    def test_smoke_result_in_execution(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("execution_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

        from pipeline_schema import create_strategy, save_phase_output

        strategy = create_strategy("ses_smoke_exec")
        strategy["tasks"] = [{"id": "t1", "title": "Task", "tool": "claude", "priority": "medium"}]
        save_phase_output(strategy, "strategy", "ses_smoke_exec")

        execution = run_execution("ses_smoke_exec")

        assert "smoke_test" in execution
        assert execution["smoke_test"] is not None
        # No start_command in strategy → skipped
        assert execution["smoke_test"]["passed"] is True


# ── execute_task ─────────────────────────────────────────────────────


class TestExecuteTask:
    def test_success(self, tmp_path, monkeypatch):
        monkeypatch.setattr("execution_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

        task = {"id": "task_1", "tool": "claude", "title": "Write code"}
        result = execute_task(task, "ses_exec")

        assert result["status"] == "done"
        assert result["task_id"] == "task_1"
        assert result["tool"] == "claude"
        assert "artifact" in result

    def test_unknown_tool(self, tmp_path, monkeypatch):
        monkeypatch.setattr("execution_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

        task = {"id": "task_bad", "tool": "unknown_tool_xyz"}
        result = execute_task(task, "ses_exec")

        assert result["status"] == "failed"
        assert "Unknown tool" in result["error"]

    def test_tool_failure_returns_failed(self, tmp_path, monkeypatch):
        monkeypatch.setattr("execution_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

        def failing_tool(task, session_id):
            raise RuntimeError("boom")

        register_tool("failing_test", failing_tool)
        try:
            task = {"id": "task_fail", "tool": "failing_test"}
            result = execute_task(task, "ses_exec")

            assert result["status"] == "failed"
            assert "failed after retries" in result["error"]
        finally:
            _TOOL_REGISTRY.pop("failing_test", None)

    def test_default_tool_when_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("execution_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

        task = {"id": "task_no_tool"}
        result = execute_task(task, "ses_exec")

        # Defaults to "claude"
        assert result["tool"] == "claude"
        assert result["status"] == "done"


# ── run_execution ────────────────────────────────────────────────────


class TestRunExecution:
    def _setup_strategy(self, tmp_path, session_id, tasks):
        from pipeline_schema import create_strategy, save_phase_output

        strategy = create_strategy(session_id)
        strategy["tasks"] = tasks
        save_phase_output(strategy, "strategy", session_id)

    def test_full_run(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("execution_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

        tasks = [
            {"id": "task_1", "title": "Make image", "tool": "dall-e", "priority": "high"},
            {"id": "task_2", "title": "Write code", "tool": "claude", "priority": "medium"},
        ]
        self._setup_strategy(tmp_path, "ses_run", tasks)

        execution = run_execution("ses_run")

        assert execution["session_id"] == "ses_run"
        assert execution["tasks_completed"] == 2
        assert execution["tasks_failed"] == 0
        assert len(execution["artifacts"]) == 2
        assert execution["artifacts"][0]["status"] == "done"
        assert execution["artifacts"][1]["status"] == "done"

    def test_empty_tasks(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("execution_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

        self._setup_strategy(tmp_path, "ses_empty", [])

        execution = run_execution("ses_empty")

        assert execution["tasks_completed"] == 0
        assert execution["tasks_failed"] == 0
        assert execution["artifacts"] == []

    def test_partial_failure(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("execution_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

        tasks = [
            {"id": "task_ok", "title": "Good", "tool": "claude", "priority": "high"},
            {"id": "task_bad", "title": "Bad", "tool": "nonexistent_xyz", "priority": "low"},
        ]
        self._setup_strategy(tmp_path, "ses_partial", tasks)

        execution = run_execution("ses_partial")

        assert execution["tasks_completed"] == 1
        assert execution["tasks_failed"] == 1

    def test_saves_execution_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("execution_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

        self._setup_strategy(tmp_path, "ses_save", [
            {"id": "task_1", "title": "Task", "tool": "claude", "priority": "medium"},
        ])

        run_execution("ses_save")

        # Verify file was saved
        path = tmp_path / "ses_save" / "execution.json"
        assert path.exists()

        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["tasks_completed"] == 1

    def test_validates_against_schema(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("execution_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

        from pipeline_schema import validate_execution

        self._setup_strategy(tmp_path, "ses_valid", [
            {"id": "task_1", "title": "Task", "tool": "claude", "priority": "medium"},
        ])

        execution = run_execution("ses_valid")
        result = validate_execution(execution)

        assert result["valid"]
        assert result["missing"] == []


# ── get_execution_status ─────────────────────────────────────────────


class TestGetExecutionStatus:
    def test_success_status(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("execution_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

        from pipeline_schema import create_strategy, save_phase_output

        strategy = create_strategy("ses_status")
        strategy["tasks"] = [{"id": "t1", "title": "T", "tool": "claude", "priority": "medium"}]
        save_phase_output(strategy, "strategy", "ses_status")

        run_execution("ses_status")
        status = get_execution_status("ses_status")

        assert status["session_id"] == "ses_status"
        assert status["tasks_completed"] == 1
        assert status["tasks_failed"] == 0
        assert status["status"] == "success"

    def test_partial_status(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("execution_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

        from pipeline_schema import create_strategy, save_phase_output

        strategy = create_strategy("ses_part")
        strategy["tasks"] = [
            {"id": "t1", "title": "OK", "tool": "claude", "priority": "medium"},
            {"id": "t2", "title": "Bad", "tool": "no_such_tool", "priority": "low"},
        ]
        save_phase_output(strategy, "strategy", "ses_part")

        run_execution("ses_part")
        status = get_execution_status("ses_part")

        assert status["status"] == "partial"


# ── show_execution ───────────────────────────────────────────────────


class TestShowExecution:
    def test_prints_summary(self, capsys):
        execution = {
            "session_id": "ses_show",
            "tasks_completed": 2,
            "tasks_failed": 1,
            "total_cost": None,
            "artifacts": [
                {"task_id": "t1", "tool": "claude", "status": "done"},
                {"task_id": "t2", "tool": "dall-e", "status": "done"},
                {"task_id": "t3", "tool": "flux", "status": "failed", "error": "timeout"},
            ],
        }
        show_execution(execution)

        captured = capsys.readouterr()
        assert "ses_show" in captured.out
        assert "Completed: 2" in captured.out
        assert "Failed: 1" in captured.out
        assert "t1" in captured.out
        assert "timeout" in captured.out

    def test_prints_cost(self, capsys):
        execution = {
            "session_id": "ses_cost",
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_cost": "$3.50",
            "artifacts": [],
        }
        show_execution(execution)

        captured = capsys.readouterr()
        assert "$3.50" in captured.out

    def test_empty_artifacts(self, capsys):
        execution = {
            "session_id": "ses_empty",
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_cost": None,
            "artifacts": [],
        }
        show_execution(execution)

        captured = capsys.readouterr()
        assert "Completed: 0" in captured.out


# ── CLI ──────────────────────────────────────────────────────────────


class TestCli:
    def test_run_command(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("execution_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

        from execution_engine import _parse_cli
        from pipeline_schema import create_strategy, save_phase_output

        strategy = create_strategy("ses_cli")
        strategy["tasks"] = [{"id": "t1", "title": "Test", "tool": "claude", "priority": "medium"}]
        save_phase_output(strategy, "strategy", "ses_cli")

        _parse_cli(["execution_engine.py", "run", "ses_cli"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert data["session_id"] == "ses_cli"
        assert data["tasks_completed"] == 1

    def test_status_command(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("execution_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

        from execution_engine import _parse_cli
        from pipeline_schema import create_strategy, save_phase_output

        strategy = create_strategy("ses_cli_st")
        strategy["tasks"] = [{"id": "t1", "title": "Test", "tool": "claude", "priority": "medium"}]
        save_phase_output(strategy, "strategy", "ses_cli_st")

        run_execution("ses_cli_st")
        capsys.readouterr()  # Clear

        _parse_cli(["execution_engine.py", "status", "ses_cli_st"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert data["status"] == "success"

    def test_tools_command(self, capsys):
        from execution_engine import _parse_cli

        _parse_cli(["execution_engine.py", "tools"])
        captured = capsys.readouterr()

        assert "claude" in captured.out
        assert "dall-e" in captured.out

    def test_show_command(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("execution_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)

        from execution_engine import _parse_cli
        from pipeline_schema import create_strategy, save_phase_output

        strategy = create_strategy("ses_cli_sh")
        strategy["tasks"] = [{"id": "t1", "title": "Show", "tool": "claude", "priority": "medium"}]
        save_phase_output(strategy, "strategy", "ses_cli_sh")

        run_execution("ses_cli_sh")
        capsys.readouterr()  # Clear

        _parse_cli(["execution_engine.py", "show", "ses_cli_sh"])
        captured = capsys.readouterr()

        assert "ses_cli_sh" in captured.out
        assert "t1" in captured.out

    def test_unknown_command_exits(self):
        from execution_engine import _parse_cli

        with pytest.raises(SystemExit):
            _parse_cli(["execution_engine.py", "bogus"])

    def test_no_args_exits(self):
        from execution_engine import _parse_cli

        with pytest.raises(SystemExit):
            _parse_cli(["execution_engine.py"])

    def test_run_missing_session_exits(self):
        from execution_engine import _parse_cli

        with pytest.raises(SystemExit):
            _parse_cli(["execution_engine.py", "run"])
