"""Tests for pal_router module."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from pal_router import (
    DEFAULT_PHASE_TIERS,
    MODEL_TIERS,
    estimate_cost,
    get_model_for_phase,
    get_tier_config,
)


class TestModelTiers:
    def test_three_tiers_defined(self):
        assert set(MODEL_TIERS.keys()) == {"frugal", "standard", "frontier"}

    def test_each_tier_has_required_fields(self):
        for tier_name, config in MODEL_TIERS.items():
            assert "model_id" in config, f"{tier_name} missing model_id"
            assert "max_tokens" in config, f"{tier_name} missing max_tokens"
            assert "temperature" in config, f"{tier_name} missing temperature"
            assert "cost_multiplier" in config, f"{tier_name} missing cost_multiplier"

    def test_cost_ordering(self):
        assert MODEL_TIERS["frugal"]["cost_multiplier"] < MODEL_TIERS["standard"]["cost_multiplier"]
        assert MODEL_TIERS["standard"]["cost_multiplier"] < MODEL_TIERS["frontier"]["cost_multiplier"]

    def test_cost_values(self):
        assert MODEL_TIERS["frugal"]["cost_multiplier"] == 1
        assert MODEL_TIERS["standard"]["cost_multiplier"] == 10
        assert MODEL_TIERS["frontier"]["cost_multiplier"] == 30


class TestDefaultPhaseTiers:
    def test_all_six_phases_mapped(self):
        for phase in range(6):
            assert phase in DEFAULT_PHASE_TIERS

    def test_default_mappings(self):
        assert DEFAULT_PHASE_TIERS[0] == "standard"
        assert DEFAULT_PHASE_TIERS[1] == "frugal"
        assert DEFAULT_PHASE_TIERS[2] == "standard"
        assert DEFAULT_PHASE_TIERS[3] == "frugal"
        assert DEFAULT_PHASE_TIERS[4] == "frontier"
        assert DEFAULT_PHASE_TIERS[5] == "standard"

    def test_all_tiers_are_valid(self):
        for phase, tier in DEFAULT_PHASE_TIERS.items():
            assert tier in MODEL_TIERS, f"Phase {phase} has invalid tier: {tier}"


class TestGetTierConfig:
    def test_valid_tier(self):
        config = get_tier_config("frugal")
        assert config is not None
        assert config["model_id"] == "claude-haiku-4-5-20251001"

    def test_all_tiers(self):
        for tier_name in MODEL_TIERS:
            config = get_tier_config(tier_name)
            assert config is not None
            assert config == MODEL_TIERS[tier_name]

    def test_unknown_tier_returns_none(self):
        assert get_tier_config("nonexistent") is None

    def test_empty_string_returns_none(self):
        assert get_tier_config("") is None


class TestGetModelForPhase:
    def test_default_routing(self):
        for phase in range(6):
            result = get_model_for_phase(phase)
            expected_tier = DEFAULT_PHASE_TIERS[phase]
            assert result["tier"] == expected_tier
            assert result["phase"] == phase
            assert result["model_id"] == MODEL_TIERS[expected_tier]["model_id"]

    def test_result_has_all_fields(self):
        result = get_model_for_phase(0)
        assert "phase" in result
        assert "phase_name" in result
        assert "tier" in result
        assert "model_id" in result
        assert "max_tokens" in result
        assert "temperature" in result

    def test_phase_name_included(self):
        result = get_model_for_phase(4)
        assert result["phase_name"] == "Evaluation"

    def test_spec_override_int_key(self):
        spec = {"pipeline": {"model_tiers": {1: "frontier"}}}
        result = get_model_for_phase(1, spec)
        assert result["tier"] == "frontier"
        assert result["model_id"] == MODEL_TIERS["frontier"]["model_id"]

    def test_spec_override_str_key(self):
        spec = {"pipeline": {"model_tiers": {"1": "frontier"}}}
        result = get_model_for_phase(1, spec)
        assert result["tier"] == "frontier"

    def test_spec_without_override_uses_default(self):
        spec = {"pipeline": {"model_tiers": {4: "standard"}}}
        result = get_model_for_phase(0, spec)
        assert result["tier"] == "standard"  # default for phase 0

    def test_spec_none_uses_default(self):
        result = get_model_for_phase(1, None)
        assert result["tier"] == "frugal"

    def test_empty_spec_uses_default(self):
        result = get_model_for_phase(1, {})
        assert result["tier"] == "frugal"

    def test_unknown_phase_defaults_to_standard(self):
        result = get_model_for_phase(99)
        assert result["tier"] == "standard"

    def test_phase_as_string(self):
        result = get_model_for_phase("4")
        assert result["phase"] == 4
        assert result["tier"] == "frontier"

    def test_invalid_tier_in_spec_falls_back(self, capsys):
        spec = {"pipeline": {"model_tiers": {0: "nonexistent_tier"}}}
        result = get_model_for_phase(0, spec)
        assert result["tier"] == "standard"
        captured = capsys.readouterr()
        assert "Unknown tier" in captured.err


class TestEstimateCost:
    def test_all_phases_default(self):
        result = estimate_cost()
        assert result["total_cost"] == 1 + 10 + 1 + 10 + 30 + 10  # frugal not for 0
        # Phase 0=standard(10), 1=frugal(1), 2=standard(10), 3=frugal(1), 4=frontier(30), 5=standard(10)
        assert result["total_cost"] == 62

    def test_subset_phases(self):
        result = estimate_cost(phases=[1, 3])
        assert result["total_cost"] == 2  # both frugal (1+1)

    def test_single_phase(self):
        result = estimate_cost(phases=[4])
        assert result["total_cost"] == 30  # frontier

    def test_breakdown_length(self):
        result = estimate_cost(phases=[0, 1, 2])
        assert len(result["phases"]) == 3

    def test_breakdown_fields(self):
        result = estimate_cost(phases=[0])
        entry = result["phases"][0]
        assert "phase" in entry
        assert "phase_name" in entry
        assert "tier" in entry
        assert "cost" in entry

    def test_with_spec_override(self):
        spec = {"pipeline": {"model_tiers": {1: "frontier"}}}
        result = estimate_cost(phases=[1], spec=spec)
        assert result["total_cost"] == 30  # overridden to frontier

    def test_unit_field(self):
        result = estimate_cost()
        assert "unit" in result

    def test_empty_phases(self):
        result = estimate_cost(phases=[])
        assert result["total_cost"] == 0
        assert result["phases"] == []


class TestLoadSpecForSession:
    def test_load_existing_spec(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pal_router.PIPELINES_DIR", tmp_path)
        session_dir = tmp_path / "test_session"
        session_dir.mkdir()
        spec = {"pipeline": {"model_tiers": {"4": "standard"}}}
        (session_dir / "spec.json").write_text(
            json.dumps(spec, ensure_ascii=False), encoding="utf-8"
        )
        from pal_router import _load_spec_for_session
        loaded = _load_spec_for_session("test_session")
        assert loaded == spec

    def test_missing_session_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pal_router.PIPELINES_DIR", tmp_path)
        from pal_router import _load_spec_for_session
        assert _load_spec_for_session("nonexistent") is None

    def test_corrupted_json_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pal_router.PIPELINES_DIR", tmp_path)
        session_dir = tmp_path / "bad_session"
        session_dir.mkdir()
        (session_dir / "spec.json").write_text("{invalid", encoding="utf-8")
        from pal_router import _load_spec_for_session
        assert _load_spec_for_session("bad_session") is None
