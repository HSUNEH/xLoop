"""Tests for web_search module."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from web_search import parse_args, print_json_results, print_results


class TestParseArgs:
    def test_basic_query(self):
        query, count, json_output, time_filter = parse_args(["prog", "AI", "agents"])
        assert query == "AI agents"
        assert count == 10
        assert json_output is False
        assert time_filter is None

    def test_count_flag(self):
        query, count, json_output, time_filter = parse_args(["prog", "test", "--count", "5"])
        assert query == "test"
        assert count == 5

    def test_json_flag(self):
        query, count, json_output, time_filter = parse_args(["prog", "test", "--json"])
        assert query == "test"
        assert json_output is True

    def test_json_with_count(self):
        query, count, json_output, time_filter = parse_args(
            ["prog", "AI", "framework", "--json", "--count", "3"]
        )
        assert query == "AI framework"
        assert count == 3
        assert json_output is True

    def test_no_query_exits(self):
        try:
            parse_args(["prog"])
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code == 1

    def test_invalid_count_exits(self):
        try:
            parse_args(["prog", "test", "--count", "abc"])
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code == 1

    def test_time_flag_day(self):
        query, count, json_output, time_filter = parse_args(["prog", "test", "--time", "d"])
        assert time_filter == "d"

    def test_time_flag_week(self):
        query, count, json_output, time_filter = parse_args(["prog", "test", "--time", "w"])
        assert time_filter == "w"

    def test_time_flag_month(self):
        query, count, json_output, time_filter = parse_args(["prog", "test", "--time", "m"])
        assert time_filter == "m"

    def test_time_flag_year(self):
        query, count, json_output, time_filter = parse_args(["prog", "test", "--time", "y"])
        assert time_filter == "y"

    def test_time_flag_invalid_exits(self):
        try:
            parse_args(["prog", "test", "--time", "x"])
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code == 1

    def test_time_with_other_flags(self):
        query, count, json_output, time_filter = parse_args(
            ["prog", "AI", "--count", "5", "--time", "w", "--json"]
        )
        assert query == "AI"
        assert count == 5
        assert time_filter == "w"
        assert json_output is True


class TestPrintResults:
    def test_print_format(self, capsys):
        results = [
            {
                "title": "Test Article",
                "url": "https://example.com/article",
                "snippet": "This is a test snippet.",
                "source": "example.com",
            },
        ]
        print_results(results)
        captured = capsys.readouterr()
        assert "Test Article" in captured.out
        assert "example.com" in captured.out
        assert "https://example.com/article" in captured.out
        assert "This is a test snippet." in captured.out

    def test_print_empty_snippet(self, capsys):
        results = [
            {
                "title": "No Snippet",
                "url": "https://example.com",
                "snippet": "",
                "source": "example.com",
            },
        ]
        print_results(results)
        captured = capsys.readouterr()
        assert "No Snippet" in captured.out


class TestPrintJsonResults:
    def test_json_output_format(self, capsys):
        results = [
            {
                "title": "Test Article",
                "url": "https://example.com/article",
                "snippet": "Test snippet",
                "source": "example.com",
            },
            {
                "title": "Another Article",
                "url": "https://other.com/page",
                "snippet": "Another snippet",
                "source": "other.com",
            },
        ]
        print_json_results(results)
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert len(parsed) == 2
        assert parsed[0]["title"] == "Test Article"
        assert parsed[0]["url"] == "https://example.com/article"
        assert parsed[1]["source"] == "other.com"

    def test_json_output_empty(self, capsys):
        print_json_results([])
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed == []
