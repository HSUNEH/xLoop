"""Tests for pipeline_spec module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from pipeline_spec import (
    SPEC_SCHEMA,
    calculate_ambiguity,
    create_spec,
    load_spec,
    save_spec,
    validate_spec,
)


class TestCreateSpec:
    def test_creates_empty_spec(self):
        spec = create_spec()
        assert spec["version"] == "1.0"
        assert spec["goal"]["deliverables"] == []
        assert spec["goal"]["success_criteria"] == []
        assert spec["goal"]["deadline"] is None
        assert spec["goal"]["cost_limit"] is None
        assert spec["domain"]["target"] is None
        assert spec["domain"]["constraints"] == []
        assert spec["domain"]["references"] == []
        assert spec["pipeline"]["active_phases"] == [0, 1, 2, 3, 4, 5]
        assert spec["pipeline"]["tools"] == []
        assert spec["pipeline"]["model_tiers"] == {}

    def test_spec_has_all_schema_fields(self):
        spec = create_spec()
        for section in SPEC_SCHEMA["required"]:
            assert section in spec
        for section in SPEC_SCHEMA["optional"]:
            assert section in spec


class TestValidateSpec:
    def test_empty_spec_invalid(self):
        spec = create_spec()
        result = validate_spec(spec)
        assert not result["valid"]
        assert "goal.deliverables" in result["missing"]
        assert "goal.success_criteria" in result["missing"]
        assert "domain.target" in result["missing"]

    def test_complete_spec_valid(self):
        spec = create_spec()
        spec["goal"]["deliverables"] = ["썸네일 3개"]
        spec["goal"]["success_criteria"] = ["파일 3개", "1280x720 해상도"]
        spec["domain"]["target"] = "youtube.com/c/MrBeast"
        spec["domain"]["constraints"] = ["한국어만"]
        spec["domain"]["references"] = ["피식대학 레이아웃"]
        result = validate_spec(spec)
        assert result["valid"]
        assert result["missing"] == []
        assert result["has_quantitative_criteria"]

    def test_qualitative_only_warns(self):
        spec = create_spec()
        spec["goal"]["deliverables"] = ["보고서"]
        spec["goal"]["success_criteria"] = ["깔끔한 디자인", "전문적 느낌"]
        spec["domain"]["target"] = "AI agents"
        result = validate_spec(spec)
        assert not result["valid"]
        assert not result["has_quantitative_criteria"]
        assert len(result["warnings"]) > 0

    def test_partial_missing(self):
        spec = create_spec()
        spec["goal"]["deliverables"] = ["보고서"]
        result = validate_spec(spec)
        assert not result["valid"]
        assert "goal.success_criteria" in result["missing"]
        assert "domain.target" in result["missing"]
        assert "goal.deliverables" not in result["missing"]


class TestCalculateAmbiguity:
    def test_empty_spec_max_ambiguity(self):
        spec = create_spec()
        assert calculate_ambiguity(spec) == 1.0

    def test_full_spec_zero_ambiguity(self):
        spec = create_spec()
        spec["goal"]["deliverables"] = ["썸네일 3개"]
        spec["goal"]["success_criteria"] = ["파일 3개", "1280x720"]
        spec["domain"]["target"] = "MrBeast"
        spec["domain"]["constraints"] = ["한국어"]
        spec["domain"]["references"] = ["피식대학"]
        assert calculate_ambiguity(spec) == 0.0

    def test_partial_spec_mid_ambiguity(self):
        spec = create_spec()
        spec["goal"]["deliverables"] = ["보고서"]
        spec["domain"]["target"] = "AI agents"
        ambiguity = calculate_ambiguity(spec)
        assert 0.0 < ambiguity < 1.0

    def test_deliverables_only_partial(self):
        spec = create_spec()
        spec["goal"]["deliverables"] = ["보고서"]
        # target is None → goal_score = 0.5
        ambiguity = calculate_ambiguity(spec)
        assert ambiguity > 0.0

    def test_weights_sum_to_one(self):
        # goal 40% + constraint 30% + criteria 30% = 100%
        spec = create_spec()
        # All zero scores
        spec["goal"]["deliverables"] = ["X"]
        spec["goal"]["success_criteria"] = ["파일 3개", "크기 1MB"]
        spec["domain"]["target"] = "Y"
        spec["domain"]["constraints"] = ["A"]
        spec["domain"]["references"] = ["B"]
        assert calculate_ambiguity(spec) == 0.0


class TestSaveLoadSpec:
    def test_save_and_load(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_spec.PIPELINES_DIR", tmp_path)
        spec = create_spec()
        spec["goal"]["deliverables"] = ["테스트"]
        save_spec(spec, "test_session")
        loaded = load_spec("test_session")
        assert loaded == spec

    def test_save_creates_directory(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_spec.PIPELINES_DIR", tmp_path)
        spec = create_spec()
        save_spec(spec, "new_session")
        assert (tmp_path / "new_session" / "spec.json").exists()

    def test_load_missing_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_spec.PIPELINES_DIR", tmp_path)
        try:
            load_spec("nonexistent")
            assert False, "Expected FileNotFoundError"
        except FileNotFoundError:
            pass

    def test_load_corrupted_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_spec.PIPELINES_DIR", tmp_path)
        bad_dir = tmp_path / "bad_session"
        bad_dir.mkdir()
        (bad_dir / "spec.json").write_text("{invalid", encoding="utf-8")
        try:
            load_spec("bad_session")
            assert False, "Expected ValueError"
        except ValueError as exc:
            assert "corrupted" in str(exc)

    def test_unicode_preserved(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline_spec.PIPELINES_DIR", tmp_path)
        spec = create_spec()
        spec["goal"]["deliverables"] = ["한국어 썸네일"]
        spec["domain"]["target"] = "피식대학"
        save_spec(spec, "unicode_test")
        raw = (tmp_path / "unicode_test" / "spec.json").read_text(encoding="utf-8")
        assert "한국어 썸네일" in raw
        assert "피식대학" in raw
