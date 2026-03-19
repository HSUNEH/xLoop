"""Tests for notebooklm_ask module."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from notebooklm_ask import parse_args, print_json_result, print_text_result


class TestParseArgs:
    def test_basic_usage(self):
        result = parse_args(["prog", "nb-123", "What is AI?"])
        assert result["notebook_id"] == "nb-123"
        assert result["question"] == "What is AI?"
        assert result["conversation_id"] is None
        assert result["json_output"] is False

    def test_multi_word_question(self):
        result = parse_args(["prog", "nb-123", "What", "is", "machine", "learning?"])
        assert result["question"] == "What is machine learning?"

    def test_conversation_id(self):
        result = parse_args(
            ["prog", "nb-123", "Follow up?", "--conversation-id", "conv-456"]
        )
        assert result["notebook_id"] == "nb-123"
        assert result["question"] == "Follow up?"
        assert result["conversation_id"] == "conv-456"

    def test_json_flag(self):
        result = parse_args(["prog", "nb-123", "Question?", "--json"])
        assert result["json_output"] is True

    def test_all_flags(self):
        result = parse_args(
            [
                "prog",
                "nb-123",
                "Question?",
                "--conversation-id",
                "conv-456",
                "--json",
            ]
        )
        assert result["notebook_id"] == "nb-123"
        assert result["question"] == "Question?"
        assert result["conversation_id"] == "conv-456"
        assert result["json_output"] is True

    def test_missing_args_exits(self):
        try:
            parse_args(["prog"])
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code == 1

    def test_only_notebook_id_exits(self):
        try:
            parse_args(["prog", "nb-123"])
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code == 1


class TestPrintJsonResult:
    def test_json_output_format(self, capsys):
        data = {
            "answer": "AI is artificial intelligence.",
            "conversation_id": "conv-123",
            "turn_number": 1,
            "references": [
                {"citation_number": 1, "cited_text": "Source text here"},
            ],
        }
        print_json_result(data)
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["answer"] == "AI is artificial intelligence."
        assert result["conversation_id"] == "conv-123"
        assert result["turn_number"] == 1
        assert len(result["references"]) == 1
        assert result["references"][0]["citation_number"] == 1

    def test_json_empty_references(self, capsys):
        data = {
            "answer": "Answer text",
            "conversation_id": "conv-456",
            "turn_number": 1,
            "references": [],
        }
        print_json_result(data)
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["references"] == []


class TestPrintTextResult:
    def test_text_output_with_references(self, capsys):
        data = {
            "answer": "The answer is 42.",
            "conversation_id": "conv-789",
            "turn_number": 1,
            "references": [
                {"citation_number": 1, "cited_text": "Relevant source passage"},
            ],
        }
        print_text_result(data)
        captured = capsys.readouterr()
        assert "The answer is 42." in captured.out
        assert "[1]" in captured.out
        assert "Relevant source passage" in captured.out
        assert "conv-789" in captured.err

    def test_text_output_no_references(self, capsys):
        data = {
            "answer": "Simple answer.",
            "conversation_id": "conv-000",
            "turn_number": 1,
            "references": [],
        }
        print_text_result(data)
        captured = capsys.readouterr()
        assert "Simple answer." in captured.out
        assert "References" not in captured.out

    def test_long_citation_truncated(self, capsys):
        long_text = "A" * 200
        data = {
            "answer": "Answer.",
            "conversation_id": "conv-111",
            "turn_number": 1,
            "references": [
                {"citation_number": 1, "cited_text": long_text},
            ],
        }
        print_text_result(data)
        captured = capsys.readouterr()
        assert "..." in captured.out
