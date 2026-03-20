"""Tests for pipeline_schema module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from pipeline_schema import (
    create_execution,
    create_handoff,
    create_research,
    create_strategy,
    create_validation,
    load_phase_output,
    save_phase_output,
    validate_execution,
    validate_handoff,
    validate_research,
    validate_strategy,
    validate_validation,
)


class TestCreateResearch:
    def test_creates_blank_research(self):
        data = create_research("ses_001", "AI agents")
        assert data["version"] == "1.0"
        assert data["session_id"] == "ses_001"
        assert data["topic"] == "AI agents"
        assert data["sources"] == []
        assert data["findings"] == []
        assert data["open_gaps"] == []
        assert data["notebook_id"] is None

    def test_has_loop_summary(self):
        data = create_research("ses_001", "test")
        summary = data["loop_summary"]
        assert summary["total_iterations"] == 0
        assert summary["total_queries"] == 0
        assert summary["total_sources"] == 0
        assert summary["covered_topics"] == []

    def test_completed_at_is_iso(self):
        data = create_research("ses_001", "test")
        assert "T" in data["completed_at"]


class TestCreateStrategy:
    def test_creates_blank_strategy(self):
        data = create_strategy("ses_001")
        assert data["version"] == "1.0"
        assert data["session_id"] == "ses_001"
        assert data["approach"] == "Double Diamond"
        assert data["tasks"] == []
        assert data["constraints_applied"] == []
        assert data["estimated_cost"] is None

    def test_created_at_is_iso(self):
        data = create_strategy("ses_001")
        assert "T" in data["created_at"]


class TestCreateExecution:
    def test_creates_blank_execution(self):
        data = create_execution("ses_001")
        assert data["version"] == "1.0"
        assert data["session_id"] == "ses_001"
        assert data["artifacts"] == []
        assert data["tasks_completed"] == 0
        assert data["tasks_failed"] == 0
        assert data["total_cost"] is None

    def test_has_smoke_test_field(self):
        data = create_execution("ses_001")
        assert "smoke_test" in data
        assert data["smoke_test"] is None


class TestCreateValidation:
    def test_creates_blank_validation(self):
        data = create_validation("ses_001")
        assert data["version"] == "1.0"
        assert data["session_id"] == "ses_001"
        assert data["passed"] is False
        assert data["drift_score"] == 1.0
        assert data["action"] == "pending"
        assert data["feedback"] == []

    def test_has_three_stages(self):
        data = create_validation("ses_001")
        assert "stage1_mechanical" in data
        assert "stage2_semantic" in data
        assert "stage3_consensus" in data
        assert data["stage1_mechanical"]["passed"] is False
        assert data["stage2_semantic"]["spec_alignment"] == 0.0
        assert data["stage3_consensus"]["drift_score"] == 1.0

    def test_stage0_runtime_in_schema(self):
        from pipeline_schema import VALIDATION_SCHEMA
        assert "stage0_runtime" in VALIDATION_SCHEMA["optional"]
        assert VALIDATION_SCHEMA["defaults"]["stage0_runtime"] is None

    def test_smoke_test_in_execution_schema(self):
        from pipeline_schema import EXECUTION_SCHEMA
        assert "smoke_test" in EXECUTION_SCHEMA["optional"]
        assert EXECUTION_SCHEMA["defaults"]["smoke_test"] is None


class TestCreateHandoff:
    def test_creates_handoff(self):
        data = create_handoff(0, 1, "ses_001")
        assert data["version"] == "1.0"
        assert data["from_phase"] == 0
        assert data["to_phase"] == 1
        assert data["session_id"] == "ses_001"
        assert data["status"] == "success"
        assert data["output_file"] is None
        assert data["summary"] == {}

    def test_custom_status_and_summary(self):
        data = create_handoff(1, 2, "ses_001", status="partial",
                              output_file="research.json",
                              summary={"sources": 15})
        assert data["status"] == "partial"
        assert data["output_file"] == "research.json"
        assert data["summary"]["sources"] == 15


class TestValidateResearch:
    def test_valid_research(self):
        data = create_research("ses_001", "AI agents")
        result = validate_research(data)
        assert result["valid"]
        assert result["missing"] == []

    def test_missing_required(self):
        data = {"version": "1.0", "session_id": "ses_001"}
        result = validate_research(data)
        assert not result["valid"]
        assert "topic" in result["missing"]
        assert "sources" in result["missing"]
        assert "findings" in result["missing"]


class TestValidateStrategy:
    def test_valid_strategy(self):
        data = create_strategy("ses_001")
        result = validate_strategy(data)
        assert result["valid"]

    def test_missing_required(self):
        data = {"version": "1.0"}
        result = validate_strategy(data)
        assert not result["valid"]
        assert "session_id" in result["missing"]
        assert "tasks" in result["missing"]


class TestValidateExecution:
    def test_valid_execution(self):
        data = create_execution("ses_001")
        result = validate_execution(data)
        assert result["valid"]

    def test_missing_required(self):
        data = {}
        result = validate_execution(data)
        assert not result["valid"]
        assert "version" in result["missing"]


class TestValidateValidation:
    def test_valid_validation(self):
        data = create_validation("ses_001")
        result = validate_validation(data)
        assert result["valid"]

    def test_missing_required(self):
        data = {"version": "1.0", "session_id": "ses_001"}
        result = validate_validation(data)
        assert not result["valid"]
        assert "completed_at" in result["missing"]


class TestValidateHandoff:
    def test_valid_handoff(self):
        data = create_handoff(0, 1, "ses_001")
        result = validate_handoff(data)
        assert result["valid"]

    def test_invalid_phase_order(self):
        data = create_handoff(2, 1, "ses_001")
        # Manually set wrong order
        data["from_phase"] = 2
        data["to_phase"] = 1
        result = validate_handoff(data)
        assert not result["valid"]
        assert "errors" in result

    def test_missing_required(self):
        data = {"version": "1.0"}
        result = validate_handoff(data)
        assert not result["valid"]
        assert "from_phase" in result["missing"]


class TestSaveLoadPhaseOutput:
    def test_save_and_load_research(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        data = create_research("ses_001", "AI agents")
        data["findings"] = ["LLM은 추론 가능"]
        save_phase_output(data, "research", "ses_001")
        loaded = load_phase_output("research", "ses_001")
        assert loaded == data

    def test_save_and_load_strategy(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        data = create_strategy("ses_001")
        save_phase_output(data, "strategy", "ses_001")
        loaded = load_phase_output("strategy", "ses_001")
        assert loaded == data

    def test_save_and_load_execution(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        data = create_execution("ses_001")
        save_phase_output(data, "execution", "ses_001")
        loaded = load_phase_output("execution", "ses_001")
        assert loaded == data

    def test_save_and_load_validation(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        data = create_validation("ses_001")
        save_phase_output(data, "validation", "ses_001")
        loaded = load_phase_output("validation", "ses_001")
        assert loaded == data

    def test_save_handoff_filename(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        data = create_handoff(1, 2, "ses_001")
        path = save_phase_output(data, "handoff", "ses_001")
        assert path.name == "handoff_1_to_2.json"

    def test_load_missing_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        try:
            load_phase_output("research", "nonexistent")
            assert False, "Expected FileNotFoundError"
        except FileNotFoundError:
            pass

    def test_load_corrupted_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        bad_dir = tmp_path / "bad_session"
        bad_dir.mkdir()
        (bad_dir / "research.json").write_text("{invalid", encoding="utf-8")
        try:
            load_phase_output("research", "bad_session")
            assert False, "Expected ValueError"
        except ValueError as exc:
            assert "corrupted" in str(exc).lower()

    def test_unicode_preserved(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        data = create_research("ses_001", "한국어 주제")
        data["findings"] = ["한글 발견"]
        save_phase_output(data, "research", "ses_001")
        raw = (tmp_path / "ses_001" / "research.json").read_text(encoding="utf-8")
        assert "한국어 주제" in raw
        assert "한글 발견" in raw
