"""Tests for evaluation_engine module."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from evaluation_engine import (
    DRIFT_THRESHOLD,
    advocate,
    critic,
    determine_action,
    judge,
    run_evaluation,
    run_stage0,
    run_stage1,
    run_stage2,
    run_stage3,
    show_validation,
)


# ── Fixtures ────────────────────────────────────────────────────────


def _make_spec(deliverables=None, success_criteria=None, target="test target"):
    return {
        "version": "1.0",
        "goal": {
            "deliverables": deliverables or [],
            "success_criteria": success_criteria or [],
            "deadline": None,
            "cost_limit": None,
        },
        "domain": {
            "target": target,
            "constraints": [],
            "references": [],
        },
        "pipeline": {
            "active_phases": [0, 1, 2, 3, 4, 5],
            "tools": [],
            "model_tiers": {},
        },
    }


def _make_execution(artifacts=None, tasks_completed=0, tasks_failed=0, smoke_test=None):
    return {
        "version": "1.0",
        "session_id": "ses_test",
        "completed_at": "2026-01-01T00:00:00+00:00",
        "artifacts": artifacts or [],
        "tasks_completed": tasks_completed,
        "tasks_failed": tasks_failed,
        "total_cost": None,
        "smoke_test": smoke_test,
    }


def _skipped_smoke_test():
    """서버 없는 프로젝트에서의 스킵된 smoke test 결과."""
    return {
        "passed": True,
        "server_started": False,
        "port": None,
        "endpoints": [],
        "error": "start_command not configured — skipped",
    }


def _make_artifact(task_id="t1", tool="claude", status="done", output="test output"):
    result = {
        "task_id": task_id,
        "tool": tool,
        "status": status,
    }
    if status == "done":
        result["artifact"] = {"type": "text", "task_id": task_id, "tool": tool, "output": output}
    else:
        result["error"] = "failed"
    return result


# ── Stage 0: Runtime ──────────────────────────────────────────────


class TestRunStage0:
    def test_no_smoke_test_fails(self):
        execution = _make_execution(tasks_completed=1)
        result = run_stage0(execution)

        assert result["passed"] is False
        assert any("미실행" in c["detail"] for c in result["checks"])

    def test_smoke_test_none_fails(self):
        execution = _make_execution(tasks_completed=1)
        execution["smoke_test"] = None
        result = run_stage0(execution)

        assert result["passed"] is False

    def test_smoke_test_skipped_passes(self):
        execution = _make_execution(tasks_completed=1)
        execution["smoke_test"] = {
            "passed": True,
            "server_started": False,
            "port": None,
            "endpoints": [],
            "error": "start_command not configured — skipped",
        }
        result = run_stage0(execution)

        assert result["passed"] is True
        assert any("스킵" in c["detail"] for c in result["checks"])

    def test_smoke_test_all_pass(self):
        execution = _make_execution(tasks_completed=1)
        execution["smoke_test"] = {
            "passed": True,
            "server_started": True,
            "port": 8080,
            "endpoints": [
                {"path": "/health", "method": "GET", "status_code": 200, "passed": True, "error": None},
                {"path": "/api", "method": "GET", "status_code": 200, "passed": True, "error": None},
            ],
            "error": None,
        }
        result = run_stage0(execution)

        assert result["passed"] is True
        assert len(result["checks"]) == 3  # server_started + 2 endpoints

    def test_smoke_test_server_fail(self):
        execution = _make_execution(tasks_completed=1)
        execution["smoke_test"] = {
            "passed": False,
            "server_started": False,
            "port": 8080,
            "endpoints": [],
            "error": "Server did not respond within 30s",
        }
        result = run_stage0(execution)

        assert result["passed"] is False
        server_check = [c for c in result["checks"] if c["name"] == "server_started"]
        assert server_check[0]["passed"] is False

    def test_smoke_test_endpoint_5xx(self):
        execution = _make_execution(tasks_completed=1)
        execution["smoke_test"] = {
            "passed": False,
            "server_started": True,
            "port": 8080,
            "endpoints": [
                {"path": "/health", "method": "GET", "status_code": 200, "passed": True, "error": None},
                {"path": "/api", "method": "GET", "status_code": 500, "passed": False, "error": "HTTP 500"},
            ],
            "error": None,
        }
        result = run_stage0(execution)

        assert result["passed"] is False
        endpoint_checks = [c for c in result["checks"] if c["name"].startswith("endpoint:")]
        assert len(endpoint_checks) == 2
        passed_eps = [c for c in endpoint_checks if c["passed"]]
        failed_eps = [c for c in endpoint_checks if not c["passed"]]
        assert len(passed_eps) == 1
        assert len(failed_eps) == 1


# ── Stage 1: Mechanical ────────────────────────────────────────────


class TestRunStage1:
    def test_all_pass(self):
        spec = _make_spec(success_criteria=["3개 이상의 산출물"])
        execution = _make_execution(
            artifacts=[_make_artifact("t1"), _make_artifact("t2"), _make_artifact("t3")],
            tasks_completed=3,
            tasks_failed=0,
        )
        result = run_stage1(spec, execution)

        assert result["passed"] is True
        assert len(result["checks"]) >= 2

    def test_no_artifacts_fails(self):
        spec = _make_spec(success_criteria=["1개 이상"])
        execution = _make_execution(artifacts=[], tasks_completed=0, tasks_failed=0)
        result = run_stage1(spec, execution)

        assert result["passed"] is False
        has_artifact_check = [c for c in result["checks"] if c["name"] == "has_artifacts"]
        assert has_artifact_check[0]["passed"] is False

    def test_low_success_rate_fails(self):
        spec = _make_spec()
        execution = _make_execution(
            artifacts=[_make_artifact("t1"), _make_artifact("t2", status="failed")],
            tasks_completed=1,
            tasks_failed=4,
        )
        result = run_stage1(spec, execution)

        rate_check = [c for c in result["checks"] if c["name"] == "task_success_rate"]
        assert rate_check[0]["passed"] is False

    def test_quantitative_threshold_met(self):
        spec = _make_spec(success_criteria=["2개 이상의 결과물"])
        execution = _make_execution(
            artifacts=[_make_artifact("t1"), _make_artifact("t2")],
            tasks_completed=2,
            tasks_failed=0,
        )
        result = run_stage1(spec, execution)

        quant_checks = [c for c in result["checks"] if c["name"].startswith("quantitative")]
        assert len(quant_checks) == 1
        assert quant_checks[0]["passed"] is True

    def test_quantitative_threshold_not_met(self):
        spec = _make_spec(success_criteria=["10개 이상의 소스"])
        execution = _make_execution(
            artifacts=[_make_artifact("t1")],
            tasks_completed=1,
            tasks_failed=0,
        )
        result = run_stage1(spec, execution)

        quant_checks = [c for c in result["checks"] if c["name"].startswith("quantitative")]
        assert quant_checks[0]["passed"] is False

    def test_no_quantitative_criteria_skipped(self):
        spec = _make_spec(success_criteria=["모든 작업 완료"])
        execution = _make_execution(
            artifacts=[_make_artifact("t1")],
            tasks_completed=1,
            tasks_failed=0,
        )
        result = run_stage1(spec, execution)

        quant_checks = [c for c in result["checks"] if c["name"].startswith("quantitative")]
        assert len(quant_checks) == 0

    def test_empty_checks_fails(self):
        spec = _make_spec()
        execution = _make_execution()
        result = run_stage1(spec, execution)

        # has_artifacts check will fail (no artifacts)
        assert result["passed"] is False


# ── Stage 2: Semantic ──────────────────────────────────────────────


class TestRunStage2:
    def test_full_alignment(self):
        spec = _make_spec(deliverables=["code output", "image result"])
        execution = _make_execution(
            artifacts=[
                _make_artifact("t1", output="code output here"),
                _make_artifact("t2", output="image result generated"),
            ],
            tasks_completed=2,
            tasks_failed=0,
        )
        result = run_stage2(spec, execution)

        assert result["passed"] is True
        assert result["spec_alignment"] >= 0.7

    def test_partial_alignment(self):
        spec = _make_spec(deliverables=["code output", "video render"])
        execution = _make_execution(
            artifacts=[_make_artifact("t1", output="code output done")],
            tasks_completed=1,
            tasks_failed=0,
        )
        result = run_stage2(spec, execution)

        assert result["spec_alignment"] < 1.0
        matched = [n for n in result["notes"] if "매칭" in n and "미매칭" not in n]
        unmatched = [n for n in result["notes"] if "미매칭" in n]
        assert len(matched) == 1
        assert len(unmatched) == 1

    def test_no_deliverables(self):
        spec = _make_spec(deliverables=[])
        execution = _make_execution(
            artifacts=[_make_artifact("t1")],
            tasks_completed=1,
            tasks_failed=0,
        )
        result = run_stage2(spec, execution)

        assert "deliverables 미정의" in result["notes"]

    def test_no_tasks(self):
        spec = _make_spec(deliverables=["something"])
        execution = _make_execution(artifacts=[], tasks_completed=0, tasks_failed=0)
        result = run_stage2(spec, execution)

        assert result["spec_alignment"] < 0.7
        assert "실행된 작업 없음" in result["notes"]

    def test_all_tasks_failed(self):
        spec = _make_spec(deliverables=["output"])
        execution = _make_execution(
            artifacts=[_make_artifact("t1", status="failed")],
            tasks_completed=0,
            tasks_failed=1,
        )
        result = run_stage2(spec, execution)

        assert result["passed"] is False


# ── Stage 3: Consensus ─────────────────────────────────────────────


class TestAdvocate:
    def test_with_passed_checks(self):
        stage1 = {"passed": True, "checks": [{"name": "x", "passed": True, "detail": "ok"}]}
        stage2 = {"passed": True, "spec_alignment": 0.9, "notes": []}
        execution = _make_execution(
            artifacts=[_make_artifact("t1")],
            tasks_completed=1,
            tasks_failed=0,
        )
        result = advocate(_make_spec(), execution, stage1, stage2)

        assert "옹호:" in result
        assert "통과" in result

    def test_no_positives(self):
        stage1 = {"passed": False, "checks": []}
        stage2 = {"passed": False, "spec_alignment": 0.1, "notes": []}
        execution = _make_execution()
        result = advocate(_make_spec(), execution, stage1, stage2)

        assert "특별한 성과 없음" in result


class TestCritic:
    def test_with_failures(self):
        stage1 = {"passed": False, "checks": [{"name": "x", "passed": False, "detail": "bad"}]}
        stage2 = {"passed": False, "spec_alignment": 0.3, "notes": ["deliverable 미매칭: something"]}
        execution = _make_execution(tasks_completed=0, tasks_failed=2)
        result = critic(_make_spec(), execution, stage1, stage2)

        assert "비판:" in result
        assert "실패" in result

    def test_no_issues(self):
        stage1 = {"passed": True, "checks": [{"name": "x", "passed": True, "detail": "ok"}]}
        stage2 = {"passed": True, "spec_alignment": 0.9, "notes": []}
        execution = _make_execution(tasks_completed=1, tasks_failed=0)
        result = critic(_make_spec(), execution, stage1, stage2)

        assert "특별한 문제점 없음" in result


class TestJudge:
    def test_low_drift(self):
        stage1 = {"passed": True, "checks": [
            {"name": "a", "passed": True, "detail": "ok"},
            {"name": "b", "passed": True, "detail": "ok"},
        ]}
        stage2 = {"passed": True, "spec_alignment": 0.9, "notes": []}
        result = judge("옹호: good", "비판: 없음", None, stage1, stage2)

        assert result["passed"] is True
        assert result["drift_score"] <= DRIFT_THRESHOLD

    def test_high_drift(self):
        stage1 = {"passed": False, "checks": [
            {"name": "a", "passed": False, "detail": "bad"},
        ]}
        stage2 = {"passed": False, "spec_alignment": 0.1, "notes": []}
        result = judge("옹호: 없음", "비판: bad", None, stage1, stage2)

        assert result["passed"] is False
        assert result["drift_score"] > DRIFT_THRESHOLD

    def test_drift_clamped_0_to_1(self):
        stage1 = {"passed": False, "checks": [{"name": "a", "passed": False, "detail": "x"}]}
        stage2 = {"passed": False, "spec_alignment": 0.0, "notes": []}
        result = judge("a", "b", None, stage1, stage2)

        assert 0.0 <= result["drift_score"] <= 1.0

    def test_empty_checks_default(self):
        stage1 = {"passed": False, "checks": []}
        stage2 = {"passed": False, "spec_alignment": 0.5, "notes": []}
        result = judge("a", "b", None, stage1, stage2)

        assert "drift_score" in result

    def test_stage0_full_fail_adds_penalty(self):
        stage0 = {"passed": False, "checks": [
            {"name": "server_started", "passed": False, "detail": "서버 기동 실패"},
        ]}
        stage1 = {"passed": True, "checks": [
            {"name": "a", "passed": True, "detail": "ok"},
        ]}
        stage2 = {"passed": True, "spec_alignment": 0.9, "notes": []}
        result_with = judge("a", "b", stage0, stage1, stage2)
        result_without = judge("a", "b", None, stage1, stage2)

        assert result_with["drift_score"] > result_without["drift_score"]
        assert result_with["drift_score"] >= result_without["drift_score"] + 0.4  # ~0.5 penalty

    def test_stage0_partial_fail_adds_proportional_penalty(self):
        stage0 = {"passed": False, "checks": [
            {"name": "ep1", "passed": True, "detail": "OK"},
            {"name": "ep2", "passed": False, "detail": "HTTP 500"},
        ]}
        stage1 = {"passed": True, "checks": [
            {"name": "a", "passed": True, "detail": "ok"},
        ]}
        stage2 = {"passed": True, "spec_alignment": 0.9, "notes": []}
        result = judge("a", "b", stage0, stage1, stage2)

        # 50% fail ratio × 0.3 = 0.15 penalty
        result_no_s0 = judge("a", "b", None, stage1, stage2)
        assert result["drift_score"] > result_no_s0["drift_score"]

    def test_stage0_pass_no_penalty(self):
        stage0 = {"passed": True, "checks": [
            {"name": "ep1", "passed": True, "detail": "OK"},
        ]}
        stage1 = {"passed": True, "checks": [
            {"name": "a", "passed": True, "detail": "ok"},
        ]}
        stage2 = {"passed": True, "spec_alignment": 0.9, "notes": []}
        result_with = judge("a", "b", stage0, stage1, stage2)
        result_without = judge("a", "b", None, stage1, stage2)

        assert result_with["drift_score"] == result_without["drift_score"]


class TestRunStage3:
    def test_full_pipeline(self):
        spec = _make_spec(success_criteria=["2개 이상"], deliverables=["code"])
        execution = _make_execution(
            artifacts=[_make_artifact("t1", output="code"), _make_artifact("t2", output="code")],
            tasks_completed=2,
            tasks_failed=0,
        )
        stage0 = run_stage0(execution)
        stage1 = run_stage1(spec, execution)
        stage2 = run_stage2(spec, execution)
        result = run_stage3(spec, execution, stage0, stage1, stage2)

        assert "advocate" in result
        assert "critic" in result
        assert "judge" in result
        assert "drift_score" in result


# ── determine_action ────────────────────────────────────────────────


class TestDetermineAction:
    def test_pass(self):
        assert determine_action(0.1) == "pass"
        assert determine_action(0.3) == "pass"

    def test_restart(self):
        assert determine_action(0.31) == "restart"
        assert determine_action(0.9) == "restart"

    def test_boundary(self):
        assert determine_action(DRIFT_THRESHOLD) == "pass"
        assert determine_action(DRIFT_THRESHOLD + 0.01) == "restart"


# ── run_evaluation (integration) ────────────────────────────────────


class TestRunEvaluation:
    def _setup_data(self, tmp_path, session_id, spec, execution):
        from pipeline_schema import save_phase_output
        from pipeline_spec import save_spec

        save_spec(spec, session_id)
        save_phase_output(execution, "execution", session_id)

    def test_full_pass(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("pipeline_spec.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("evaluation_engine.PIPELINES_DIR", tmp_path)

        spec = _make_spec(
            deliverables=["code output"],
            success_criteria=["2개 이상의 산출물"],
        )
        execution = _make_execution(
            artifacts=[
                _make_artifact("t1", output="code output v1"),
                _make_artifact("t2", output="code output v2"),
            ],
            tasks_completed=2,
            tasks_failed=0,
            smoke_test=_skipped_smoke_test(),
        )
        self._setup_data(tmp_path, "ses_eval", spec, execution)

        validation = run_evaluation("ses_eval")

        assert validation["passed"] is True
        assert validation["drift_score"] <= DRIFT_THRESHOLD
        assert validation["action"] == "pass"
        assert validation["stage0_runtime"]["passed"] is True
        assert validation["stage1_mechanical"]["passed"] is True
        assert validation["stage2_semantic"]["passed"] is True
        assert validation["stage3_consensus"]["passed"] is True

    def test_full_fail(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("pipeline_spec.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("evaluation_engine.PIPELINES_DIR", tmp_path)

        spec = _make_spec(
            deliverables=["video render", "audio mix"],
            success_criteria=["10개 이상의 결과물"],
        )
        execution = _make_execution(
            artifacts=[_make_artifact("t1", status="failed")],
            tasks_completed=0,
            tasks_failed=1,
        )
        self._setup_data(tmp_path, "ses_fail", spec, execution)

        validation = run_evaluation("ses_fail")

        assert validation["passed"] is False
        assert validation["drift_score"] > DRIFT_THRESHOLD
        assert validation["action"] == "restart"

    def test_saves_validation_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("pipeline_spec.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("evaluation_engine.PIPELINES_DIR", tmp_path)

        spec = _make_spec(deliverables=["output"], success_criteria=["1개"])
        execution = _make_execution(
            artifacts=[_make_artifact("t1", output="output data")],
            tasks_completed=1,
            tasks_failed=0,
            smoke_test=_skipped_smoke_test(),
        )
        self._setup_data(tmp_path, "ses_save", spec, execution)

        run_evaluation("ses_save")

        path = tmp_path / "ses_save" / "validation.json"
        assert path.exists()

        data = json.loads(path.read_text(encoding="utf-8"))
        assert "drift_score" in data
        assert "stage1_mechanical" in data

    def test_feedback_collected(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("pipeline_spec.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("evaluation_engine.PIPELINES_DIR", tmp_path)

        spec = _make_spec(
            deliverables=["nonexistent thing"],
            success_criteria=["100개 이상"],
        )
        execution = _make_execution(
            artifacts=[_make_artifact("t1")],
            tasks_completed=1,
            tasks_failed=0,
        )
        self._setup_data(tmp_path, "ses_fb", spec, execution)

        validation = run_evaluation("ses_fb")

        assert len(validation["feedback"]) > 0

    def test_validates_against_schema(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("pipeline_spec.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("evaluation_engine.PIPELINES_DIR", tmp_path)

        from pipeline_schema import validate_validation

        spec = _make_spec(deliverables=["code"], success_criteria=["1개"])
        execution = _make_execution(
            artifacts=[_make_artifact("t1", output="code here")],
            tasks_completed=1,
            tasks_failed=0,
            smoke_test=_skipped_smoke_test(),
        )
        self._setup_data(tmp_path, "ses_schema", spec, execution)

        validation = run_evaluation("ses_schema")
        result = validate_validation(validation)

        assert result["valid"]
        assert result["missing"] == []


# ── show_validation ─────────────────────────────────────────────────


class TestShowValidation:
    def test_prints_summary(self, capsys):
        validation = {
            "session_id": "ses_show",
            "passed": True,
            "drift_score": 0.15,
            "action": "pass",
            "stage1_mechanical": {
                "passed": True,
                "checks": [{"name": "has_artifacts", "passed": True, "detail": "2개"}],
            },
            "stage2_semantic": {
                "passed": True,
                "spec_alignment": 0.9,
                "notes": ["작업 완료율: 100%"],
            },
            "stage3_consensus": {
                "passed": True,
                "advocate": "옹호: good",
                "critic": "비판: 없음",
                "judge": "판정: drift 0.15 <= 0.3, 통과",
                "drift_score": 0.15,
            },
            "feedback": [],
        }
        show_validation(validation)

        captured = capsys.readouterr()
        assert "ses_show" in captured.out
        assert "0.15" in captured.out
        assert "PASS" in captured.out

    def test_prints_feedback(self, capsys):
        validation = {
            "session_id": "ses_fb",
            "passed": False,
            "drift_score": 0.8,
            "action": "restart",
            "stage1_mechanical": {"passed": False, "checks": []},
            "stage2_semantic": {"passed": False, "spec_alignment": 0.2, "notes": []},
            "stage3_consensus": {
                "passed": False,
                "advocate": "",
                "critic": "",
                "judge": "",
                "drift_score": 0.8,
            },
            "feedback": ["[Stage1] bad check", "[Stage2] unmatched"],
        }
        show_validation(validation)

        captured = capsys.readouterr()
        assert "Feedback:" in captured.out
        assert "[Stage1] bad check" in captured.out


# ── CLI ─────────────────────────────────────────────────────────────


class TestCli:
    def test_full_command(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("pipeline_spec.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("evaluation_engine.PIPELINES_DIR", tmp_path)

        from evaluation_engine import _parse_cli
        from pipeline_schema import save_phase_output
        from pipeline_spec import save_spec

        spec = _make_spec(deliverables=["code"], success_criteria=["1개"])
        execution = _make_execution(
            artifacts=[_make_artifact("t1", output="code data")],
            tasks_completed=1,
            tasks_failed=0,
        )
        save_spec(spec, "ses_cli")
        save_phase_output(execution, "execution", "ses_cli")

        _parse_cli(["evaluation_engine.py", "full", "ses_cli"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert "drift_score" in data
        assert data["session_id"] == "ses_cli"

    def test_check_alias(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("pipeline_spec.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("evaluation_engine.PIPELINES_DIR", tmp_path)

        from evaluation_engine import _parse_cli
        from pipeline_schema import save_phase_output
        from pipeline_spec import save_spec

        spec = _make_spec(deliverables=["out"], success_criteria=["1개"])
        execution = _make_execution(
            artifacts=[_make_artifact("t1", output="out")],
            tasks_completed=1,
            tasks_failed=0,
        )
        save_spec(spec, "ses_check")
        save_phase_output(execution, "execution", "ses_check")

        _parse_cli(["evaluation_engine.py", "check", "ses_check"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert "drift_score" in data

    def test_stage1_command(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("pipeline_spec.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("evaluation_engine.PIPELINES_DIR", tmp_path)

        from evaluation_engine import _parse_cli
        from pipeline_schema import save_phase_output
        from pipeline_spec import save_spec

        spec = _make_spec(success_criteria=["2개"])
        execution = _make_execution(
            artifacts=[_make_artifact("t1"), _make_artifact("t2")],
            tasks_completed=2,
            tasks_failed=0,
        )
        save_spec(spec, "ses_s1")
        save_phase_output(execution, "execution", "ses_s1")

        _parse_cli(["evaluation_engine.py", "stage1", "ses_s1"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert "passed" in data
        assert "checks" in data

    def test_stage2_command(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("pipeline_spec.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("evaluation_engine.PIPELINES_DIR", tmp_path)

        from evaluation_engine import _parse_cli
        from pipeline_schema import save_phase_output
        from pipeline_spec import save_spec

        spec = _make_spec(deliverables=["test"])
        execution = _make_execution(
            artifacts=[_make_artifact("t1", output="test done")],
            tasks_completed=1,
            tasks_failed=0,
        )
        save_spec(spec, "ses_s2")
        save_phase_output(execution, "execution", "ses_s2")

        _parse_cli(["evaluation_engine.py", "stage2", "ses_s2"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert "spec_alignment" in data

    def test_stage3_command(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("pipeline_spec.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("evaluation_engine.PIPELINES_DIR", tmp_path)

        from evaluation_engine import _parse_cli
        from pipeline_schema import save_phase_output
        from pipeline_spec import save_spec

        spec = _make_spec(deliverables=["data"], success_criteria=["1개"])
        execution = _make_execution(
            artifacts=[_make_artifact("t1", output="data output")],
            tasks_completed=1,
            tasks_failed=0,
        )
        save_spec(spec, "ses_s3")
        save_phase_output(execution, "execution", "ses_s3")

        _parse_cli(["evaluation_engine.py", "stage3", "ses_s3"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert "drift_score" in data
        assert "advocate" in data

    def test_show_command(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("pipeline_spec.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("evaluation_engine.PIPELINES_DIR", tmp_path)

        from evaluation_engine import _parse_cli
        from pipeline_schema import save_phase_output
        from pipeline_spec import save_spec

        spec = _make_spec(deliverables=["code"], success_criteria=["1개"])
        execution = _make_execution(
            artifacts=[_make_artifact("t1", output="code")],
            tasks_completed=1,
            tasks_failed=0,
        )
        save_spec(spec, "ses_show")
        save_phase_output(execution, "execution", "ses_show")

        run_evaluation("ses_show")
        capsys.readouterr()

        _parse_cli(["evaluation_engine.py", "show", "ses_show"])
        captured = capsys.readouterr()

        assert "ses_show" in captured.out
        assert "Drift Score" in captured.out

    def test_unknown_command_exits(self):
        from evaluation_engine import _parse_cli

        with pytest.raises(SystemExit):
            _parse_cli(["evaluation_engine.py", "bogus"])

    def test_no_args_exits(self):
        from evaluation_engine import _parse_cli

        with pytest.raises(SystemExit):
            _parse_cli(["evaluation_engine.py"])

    def test_full_missing_session_exits(self):
        from evaluation_engine import _parse_cli

        with pytest.raises(SystemExit):
            _parse_cli(["evaluation_engine.py", "full"])

    def test_stage1_missing_session_exits(self):
        from evaluation_engine import _parse_cli

        with pytest.raises(SystemExit):
            _parse_cli(["evaluation_engine.py", "stage1"])

    def test_stage2_missing_session_exits(self):
        from evaluation_engine import _parse_cli

        with pytest.raises(SystemExit):
            _parse_cli(["evaluation_engine.py", "stage2"])

    def test_stage3_missing_session_exits(self):
        from evaluation_engine import _parse_cli

        with pytest.raises(SystemExit):
            _parse_cli(["evaluation_engine.py", "stage3"])

    def test_show_missing_session_exits(self):
        from evaluation_engine import _parse_cli

        with pytest.raises(SystemExit):
            _parse_cli(["evaluation_engine.py", "show"])
