"""Tests for strategy_engine module."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from strategy_engine import (
    _converge,
    _diverge,
    _extract_title,
    _map_tool,
    generate_strategy,
    show_strategy,
)


# ── _map_tool ────────────────────────────────────────────────────────


class TestMapTool:
    def test_image_keywords(self):
        assert _map_tool("generate thumbnail image") == "dall-e"
        assert _map_tool("썸네일 생성") == "dall-e"

    def test_video_keywords(self):
        assert _map_tool("create animation video") == "flux"
        assert _map_tool("영상 제작") == "flux"

    def test_document_keywords(self):
        assert _map_tool("write a summary report") == "notebooklm"
        assert _map_tool("보고서 작성") == "notebooklm"

    def test_code_keywords(self):
        assert _map_tool("write code script") == "claude"
        assert _map_tool("코드 자동화") == "claude"

    def test_search_keywords(self):
        assert _map_tool("search for research papers") == "web_search"
        assert _map_tool("검색 및 조사") == "web_search"

    def test_default_tool(self):
        assert _map_tool("do something unspecified") == "claude"
        assert _map_tool("") == "claude"


# ── _extract_title ───────────────────────────────────────────────────


class TestExtractTitle:
    def test_short_text(self):
        assert _extract_title("Short finding") == "Short finding"

    def test_sentence_ending_with_period(self):
        assert _extract_title("First sentence. Second sentence.") == "First sentence"

    def test_long_text_truncated(self):
        long_text = "A" * 100
        result = _extract_title(long_text)
        assert len(result) == 53  # 50 + "..."
        assert result.endswith("...")

    def test_empty_text(self):
        assert _extract_title("") == ""

    def test_strips_whitespace(self):
        assert _extract_title("  padded text  ") == "padded text"


# ── _diverge ─────────────────────────────────────────────────────────


class TestDiverge:
    def test_creates_candidates_from_findings(self):
        findings = ["Image generation is key", "Video editing needed"]
        candidates = _diverge(findings)

        assert len(candidates) == 2
        assert candidates[0]["id"] == "task_1"
        assert candidates[1]["id"] == "task_2"
        assert candidates[0]["description"] == "Image generation is key"
        assert candidates[1]["description"] == "Video editing needed"

    def test_maps_tools_automatically(self):
        findings = ["Create thumbnail images", "Write summary report"]
        candidates = _diverge(findings)

        assert candidates[0]["tool"] == "dall-e"
        assert candidates[1]["tool"] == "notebooklm"

    def test_default_priority_is_medium(self):
        candidates = _diverge(["some finding"])
        assert candidates[0]["priority"] == "medium"

    def test_source_findings_indexed(self):
        findings = ["a", "b", "c"]
        candidates = _diverge(findings)

        assert candidates[0]["source_findings"] == [0]
        assert candidates[1]["source_findings"] == [1]
        assert candidates[2]["source_findings"] == [2]

    def test_empty_findings(self):
        assert _diverge([]) == []


# ── _converge ────────────────────────────────────────────────────────


class TestConverge:
    def test_no_constraints_returns_all(self):
        candidates = [
            {"id": "t1", "description": "task A", "tool": "claude", "priority": "medium"},
            {"id": "t2", "description": "task B", "tool": "dall-e", "priority": "medium"},
        ]
        result = _converge(candidates)
        assert len(result) == 2

    def test_filters_by_allowed_tools(self):
        candidates = [
            {"id": "t1", "description": "task A", "tool": "claude", "priority": "medium"},
            {"id": "t2", "description": "task B", "tool": "dall-e", "priority": "medium"},
            {"id": "t3", "description": "task C", "tool": "flux", "priority": "medium"},
        ]
        result = _converge(candidates, allowed_tools=["claude", "dall-e"])

        assert len(result) == 2
        tools = [t["tool"] for t in result]
        assert "flux" not in tools

    def test_constraints_boost_priority(self):
        candidates = [
            {"id": "t1", "description": "한국어 콘텐츠 작성", "tool": "claude", "priority": "medium"},
            {"id": "t2", "description": "English content", "tool": "claude", "priority": "medium"},
        ]
        result = _converge(candidates, constraints=["한국어"])

        # t1 should be boosted to high
        assert result[0]["id"] == "t1"
        assert result[0]["priority"] == "high"
        assert result[1]["priority"] == "medium"

    def test_sorted_by_priority(self):
        candidates = [
            {"id": "t1", "description": "low", "tool": "claude", "priority": "low"},
            {"id": "t2", "description": "high", "tool": "claude", "priority": "high"},
            {"id": "t3", "description": "medium", "tool": "claude", "priority": "medium"},
        ]
        result = _converge(candidates)

        assert result[0]["priority"] == "high"
        assert result[1]["priority"] == "medium"
        assert result[2]["priority"] == "low"

    def test_empty_candidates(self):
        assert _converge([]) == []

    def test_combined_constraints_and_tools(self):
        candidates = [
            {"id": "t1", "description": "이미지 생성", "tool": "dall-e", "priority": "medium"},
            {"id": "t2", "description": "이미지 분석", "tool": "claude", "priority": "medium"},
            {"id": "t3", "description": "영상 제작", "tool": "flux", "priority": "medium"},
        ]
        result = _converge(
            candidates,
            constraints=["이미지"],
            allowed_tools=["dall-e", "claude"],
        )

        assert len(result) == 2
        # Both match "이미지" constraint → both high
        assert result[0]["priority"] == "high"
        assert result[1]["priority"] == "high"


# ── generate_strategy ────────────────────────────────────────────────


class TestGenerateStrategy:
    def test_generates_from_research(self):
        research = {
            "session_id": "ses_test",
            "findings": [
                "Create thumbnail images for videos",
                "Write a summary report on findings",
            ],
        }
        strategy = generate_strategy(research)

        assert strategy["session_id"] == "ses_test"
        assert strategy["approach"] == "Double Diamond"
        assert len(strategy["tasks"]) == 2
        assert strategy["constraints_applied"] == []
        assert "created_at" in strategy

    def test_applies_spec_constraints(self):
        research = {
            "session_id": "ses_test",
            "findings": ["한국어 콘텐츠 작성", "English writing"],
        }
        spec = {
            "domain": {"constraints": ["한국어"]},
            "pipeline": {"tools": []},
        }
        strategy = generate_strategy(research, spec_data=spec)

        assert strategy["constraints_applied"] == ["한국어"]
        # 한국어 task should be high priority
        korean_task = [t for t in strategy["tasks"] if "한국어" in t["description"]][0]
        assert korean_task["priority"] == "high"

    def test_applies_spec_tool_filter(self):
        research = {
            "session_id": "ses_test",
            "findings": [
                "Create thumbnail images",
                "Write code automation",
                "Make a video",
            ],
        }
        spec = {
            "domain": {"constraints": []},
            "pipeline": {"tools": ["dall-e", "claude"]},
        }
        strategy = generate_strategy(research, spec_data=spec)

        tools = [t["tool"] for t in strategy["tasks"]]
        assert "flux" not in tools
        assert len(strategy["tasks"]) == 2

    def test_empty_findings(self):
        research = {"session_id": "ses_empty", "findings": []}
        strategy = generate_strategy(research)

        assert strategy["tasks"] == []
        assert strategy["session_id"] == "ses_empty"

    def test_no_spec(self):
        research = {
            "session_id": "ses_test",
            "findings": ["some finding"],
        }
        strategy = generate_strategy(research, spec_data=None)

        assert len(strategy["tasks"]) == 1

    def test_validates_with_schema(self):
        from pipeline_schema import validate_strategy

        research = {
            "session_id": "ses_valid",
            "findings": ["task one", "task two"],
        }
        strategy = generate_strategy(research)
        result = validate_strategy(strategy)

        assert result["valid"]
        assert result["missing"] == []


# ── show_strategy ────────────────────────────────────────────────────


class TestShowStrategy:
    def test_prints_summary(self, capsys):
        strategy = {
            "session_id": "ses_show",
            "approach": "Double Diamond",
            "tasks": [
                {"id": "task_1", "title": "Do thing", "tool": "claude", "priority": "high"},
            ],
            "constraints_applied": ["한국어"],
            "estimated_cost": None,
        }
        show_strategy(strategy)

        captured = capsys.readouterr()
        assert "ses_show" in captured.out
        assert "Double Diamond" in captured.out
        assert "Tasks: 1" in captured.out
        assert "한국어" in captured.out
        assert "task_1" in captured.out

    def test_prints_without_constraints(self, capsys):
        strategy = {
            "session_id": "ses_no_const",
            "approach": "Double Diamond",
            "tasks": [],
            "constraints_applied": [],
            "estimated_cost": None,
        }
        show_strategy(strategy)

        captured = capsys.readouterr()
        assert "Tasks: 0" in captured.out
        assert "Constraints" not in captured.out

    def test_prints_estimated_cost(self, capsys):
        strategy = {
            "session_id": "ses_cost",
            "approach": "Double Diamond",
            "tasks": [],
            "constraints_applied": [],
            "estimated_cost": "$5.00",
        }
        show_strategy(strategy)

        captured = capsys.readouterr()
        assert "$5.00" in captured.out


# ── CLI ──────────────────────────────────────────────────────────────


class TestCli:
    def test_generate_command(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("strategy_engine.PIPELINES_DIR", tmp_path)

        from pipeline_schema import create_research, save_phase_output
        from strategy_engine import _parse_cli

        research = create_research("ses_cli", "test topic")
        research["findings"] = ["Create images for report"]
        save_phase_output(research, "research", "ses_cli")

        _parse_cli(["strategy_engine.py", "generate", "ses_cli"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert data["session_id"] == "ses_cli"
        assert len(data["tasks"]) == 1

    def test_validate_command(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("strategy_engine.PIPELINES_DIR", tmp_path)

        from pipeline_schema import create_strategy, save_phase_output
        from strategy_engine import _parse_cli

        strategy = create_strategy("ses_cli_val")
        save_phase_output(strategy, "strategy", "ses_cli_val")

        _parse_cli(["strategy_engine.py", "validate", "ses_cli_val"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert data["valid"]

    def test_show_command(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", tmp_path)
        monkeypatch.setattr("strategy_engine.PIPELINES_DIR", tmp_path)

        from pipeline_schema import create_strategy, save_phase_output
        from strategy_engine import _parse_cli

        strategy = create_strategy("ses_cli_show")
        strategy["tasks"] = [
            {"id": "task_1", "title": "Test", "tool": "claude", "priority": "medium"},
        ]
        save_phase_output(strategy, "strategy", "ses_cli_show")

        _parse_cli(["strategy_engine.py", "show", "ses_cli_show"])
        captured = capsys.readouterr()

        assert "ses_cli_show" in captured.out
        assert "task_1" in captured.out

    def test_unknown_command_exits(self):
        from strategy_engine import _parse_cli

        with pytest.raises(SystemExit):
            _parse_cli(["strategy_engine.py", "bogus"])

    def test_no_args_exits(self):
        from strategy_engine import _parse_cli

        with pytest.raises(SystemExit):
            _parse_cli(["strategy_engine.py"])

    def test_generate_missing_session_exits(self):
        from strategy_engine import _parse_cli

        with pytest.raises(SystemExit):
            _parse_cli(["strategy_engine.py", "generate"])
