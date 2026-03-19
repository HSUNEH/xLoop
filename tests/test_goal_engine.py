"""Tests for goal_engine module."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from goal_engine import (
    _load_goal_state,
    add_goal_iteration,
    check_goal_termination,
    end_goal_loop,
    get_next_questions,
    start_goal_loop,
)
from pipeline_spec import create_spec


class TestStartGoalLoop:
    def test_initializes_state(self, tmp_path, monkeypatch):
        monkeypatch.setattr("goal_engine.PIPELINES_DIR", tmp_path)
        state = start_goal_loop("ses_001")
        assert state["session_id"] == "ses_001"
        assert state["status"] == "running"
        assert state["current_iteration"] == 0
        assert state["iterations"] == []

    def test_persists_to_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("goal_engine.PIPELINES_DIR", tmp_path)
        start_goal_loop("ses_002")
        state_path = tmp_path / "ses_002" / "goal_state.json"
        assert state_path.exists()
        data = json.loads(state_path.read_text())
        assert data["session_id"] == "ses_002"

    def test_raises_if_already_exists(self, tmp_path, monkeypatch):
        monkeypatch.setattr("goal_engine.PIPELINES_DIR", tmp_path)
        start_goal_loop("ses_003")
        try:
            start_goal_loop("ses_003")
            assert False, "Expected ValueError"
        except ValueError as exc:
            assert "already exists" in str(exc)


class TestAddGoalIteration:
    def test_records_iteration(self, tmp_path, monkeypatch):
        monkeypatch.setattr("goal_engine.PIPELINES_DIR", tmp_path)
        start_goal_loop("ses_010")
        state = add_goal_iteration(
            "ses_010",
            questions=["목표는?"],
            responses=["썸네일 3개"],
            spec_updates={"goal.deliverables": ["썸네일 3개"]},
            ambiguity=0.7,
        )
        assert state["current_iteration"] == 1
        assert len(state["iterations"]) == 1
        assert state["iterations"][0]["ambiguity"] == 0.7

    def test_accumulates_iterations(self, tmp_path, monkeypatch):
        monkeypatch.setattr("goal_engine.PIPELINES_DIR", tmp_path)
        start_goal_loop("ses_011")
        add_goal_iteration("ses_011", ["q1"], ["r1"], {}, 0.8)
        state = add_goal_iteration("ses_011", ["q2"], ["r2"], {}, 0.4)
        assert state["current_iteration"] == 2
        assert len(state["iterations"]) == 2

    def test_raises_if_not_running(self, tmp_path, monkeypatch):
        monkeypatch.setattr("goal_engine.PIPELINES_DIR", tmp_path)
        start_goal_loop("ses_012")
        end_goal_loop("ses_012")
        try:
            add_goal_iteration("ses_012", ["q"], ["r"], {}, 0.5)
            assert False, "Expected ValueError"
        except ValueError as exc:
            assert "not running" in str(exc)

    def test_raises_if_no_loop(self, tmp_path, monkeypatch):
        monkeypatch.setattr("goal_engine.PIPELINES_DIR", tmp_path)
        try:
            add_goal_iteration("nonexistent", ["q"], ["r"], {}, 0.5)
            assert False, "Expected FileNotFoundError"
        except FileNotFoundError:
            pass


class TestCheckGoalTermination:
    def test_should_not_terminate_missing_fields(self, tmp_path, monkeypatch):
        monkeypatch.setattr("goal_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("pipeline_spec.PIPELINES_DIR", tmp_path)
        spec = create_spec()
        result = check_goal_termination("ses_020", spec)
        assert not result["should_terminate"]
        assert "필수 필드" in result["reason"]

    def test_should_not_terminate_no_quantitative(self, tmp_path, monkeypatch):
        monkeypatch.setattr("goal_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("pipeline_spec.PIPELINES_DIR", tmp_path)
        spec = create_spec()
        spec["goal"]["deliverables"] = ["보고서"]
        spec["goal"]["success_criteria"] = ["깔끔한 디자인"]
        spec["domain"]["target"] = "AI"
        result = check_goal_termination("ses_021", spec)
        assert not result["should_terminate"]
        assert "정량 기준" in result["reason"]

    def test_should_not_terminate_high_ambiguity(self, tmp_path, monkeypatch):
        monkeypatch.setattr("goal_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("pipeline_spec.PIPELINES_DIR", tmp_path)
        spec = create_spec()
        spec["goal"]["deliverables"] = ["보고서"]
        spec["goal"]["success_criteria"] = ["5000자 이상"]
        spec["domain"]["target"] = "AI"
        # No constraints/references → high ambiguity
        result = check_goal_termination("ses_022", spec)
        assert not result["should_terminate"]
        assert "모호성" in result["reason"]

    def test_should_terminate_complete(self, tmp_path, monkeypatch):
        monkeypatch.setattr("goal_engine.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("pipeline_spec.PIPELINES_DIR", tmp_path)
        spec = create_spec()
        spec["goal"]["deliverables"] = ["썸네일 3개"]
        spec["goal"]["success_criteria"] = ["파일 3개", "1280x720"]
        spec["domain"]["target"] = "MrBeast"
        spec["domain"]["constraints"] = ["한국어"]
        spec["domain"]["references"] = ["피식대학"]
        result = check_goal_termination("ses_023", spec)
        assert result["should_terminate"]
        assert result["ambiguity"] <= 0.2


class TestGetNextQuestions:
    def test_empty_spec_many_questions(self):
        spec = create_spec()
        questions = get_next_questions(spec)
        assert len(questions) >= 4
        assert any("산출물" in q for q in questions)
        assert any("성공 기준" in q for q in questions)
        assert any("대상" in q or "타겟" in q for q in questions)

    def test_partial_spec_fewer_questions(self):
        spec = create_spec()
        spec["goal"]["deliverables"] = ["보고서"]
        spec["goal"]["success_criteria"] = ["파일 3개"]
        spec["domain"]["target"] = "AI"
        questions = get_next_questions(spec)
        assert not any("산출물" in q for q in questions)
        assert not any("대상" in q or "타겟" in q for q in questions)

    def test_qualitative_only_asks_for_quantitative(self):
        spec = create_spec()
        spec["goal"]["deliverables"] = ["보고서"]
        spec["goal"]["success_criteria"] = ["깔끔한 디자인"]
        questions = get_next_questions(spec)
        assert any("정량" in q or "측정" in q for q in questions)

    def test_full_spec_no_questions(self):
        spec = create_spec()
        spec["goal"]["deliverables"] = ["보고서"]
        spec["goal"]["success_criteria"] = ["5000자 이상"]
        spec["goal"]["deadline"] = "2026-03-25"
        spec["domain"]["target"] = "AI"
        spec["domain"]["constraints"] = ["한국어"]
        spec["domain"]["references"] = ["참고1"]
        spec["pipeline"]["tools"] = ["Web"]
        questions = get_next_questions(spec)
        assert len(questions) == 0


class TestEndGoalLoop:
    def test_marks_completed(self, tmp_path, monkeypatch):
        monkeypatch.setattr("goal_engine.PIPELINES_DIR", tmp_path)
        start_goal_loop("ses_030")
        state = end_goal_loop("ses_030")
        assert state["status"] == "completed"

    def test_persists_status(self, tmp_path, monkeypatch):
        monkeypatch.setattr("goal_engine.PIPELINES_DIR", tmp_path)
        start_goal_loop("ses_031")
        end_goal_loop("ses_031")
        loaded = _load_goal_state("ses_031")
        assert loaded["status"] == "completed"

    def test_raises_if_not_running(self, tmp_path, monkeypatch):
        monkeypatch.setattr("goal_engine.PIPELINES_DIR", tmp_path)
        start_goal_loop("ses_032")
        end_goal_loop("ses_032")
        try:
            end_goal_loop("ses_032")
            assert False, "Expected ValueError"
        except ValueError as exc:
            assert "not running" in str(exc)

    def test_raises_if_no_loop(self, tmp_path, monkeypatch):
        monkeypatch.setattr("goal_engine.PIPELINES_DIR", tmp_path)
        try:
            end_goal_loop("nonexistent")
            assert False, "Expected FileNotFoundError"
        except FileNotFoundError:
            pass
