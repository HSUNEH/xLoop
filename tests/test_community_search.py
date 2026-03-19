"""Tests for community_search module."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from community_search import parse_args, print_json_results, print_results


class TestParseArgs:
    def test_reddit_basic(self):
        opts = parse_args(["prog", "reddit", "AI", "agents"])
        assert opts["platform"] == "reddit"
        assert opts["query"] == "AI agents"
        assert opts["count"] == 10
        assert opts["subreddit"] is None
        assert opts["json_output"] is False

    def test_hn_basic(self):
        opts = parse_args(["prog", "hn", "LLM"])
        assert opts["platform"] == "hn"
        assert opts["query"] == "LLM"

    def test_all_platform(self):
        opts = parse_args(["prog", "all", "test"])
        assert opts["platform"] == "all"

    def test_count_flag(self):
        opts = parse_args(["prog", "reddit", "test", "--count", "5"])
        assert opts["count"] == 5

    def test_subreddit_flag(self):
        opts = parse_args(
            ["prog", "reddit", "test", "--subreddit", "MachineLearning"]
        )
        assert opts["subreddit"] == "MachineLearning"

    def test_json_flag(self):
        opts = parse_args(["prog", "hn", "test", "--json"])
        assert opts["json_output"] is True

    def test_all_flags(self):
        opts = parse_args(
            ["prog", "reddit", "AI", "--count", "3", "--subreddit", "AI", "--json"]
        )
        assert opts["platform"] == "reddit"
        assert opts["query"] == "AI"
        assert opts["count"] == 3
        assert opts["subreddit"] == "AI"
        assert opts["json_output"] is True

    def test_min_score_flag(self):
        opts = parse_args(["prog", "reddit", "test", "--min-score", "50"])
        assert opts["min_score"] == 50

    def test_min_score_default(self):
        opts = parse_args(["prog", "hn", "test"])
        assert opts["min_score"] == 0

    def test_time_flag(self):
        opts = parse_args(["prog", "reddit", "test", "--time", "m"])
        assert opts["time"] == "m"

    def test_time_default(self):
        opts = parse_args(["prog", "hn", "test"])
        assert opts["time"] == "year"

    def test_time_invalid_exits(self):
        try:
            parse_args(["prog", "hn", "test", "--time", "x"])
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code == 1

    def test_min_score_invalid_exits(self):
        try:
            parse_args(["prog", "reddit", "test", "--min-score", "abc"])
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code == 1

    def test_all_new_flags_combined(self):
        opts = parse_args(
            ["prog", "all", "AI", "--min-score", "100", "--time", "w", "--count", "5"]
        )
        assert opts["min_score"] == 100
        assert opts["time"] == "w"
        assert opts["count"] == 5

    def test_no_args_exits(self):
        try:
            parse_args(["prog"])
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code == 1

    def test_invalid_platform_exits(self):
        try:
            parse_args(["prog", "twitter", "test"])
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code == 1

    def test_no_query_exits(self):
        try:
            parse_args(["prog", "reddit"])
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code == 1

    def test_invalid_count_exits(self):
        try:
            parse_args(["prog", "hn", "test", "--count", "abc"])
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code == 1


class TestPrintResults:
    def test_reddit_format(self, capsys):
        results = [
            {
                "title": "AI agents discussion",
                "url": "https://reddit.com/r/AI/comments/abc123/test/",
                "subreddit": "AI",
                "score": 150,
                "comments": 42,
                "date": "Mar 01, 2026",
                "source": "reddit",
            },
        ]
        print_results(results)
        captured = capsys.readouterr()
        assert "[REDDIT]" in captured.out
        assert "AI agents discussion" in captured.out
        assert "r/AI" in captured.out
        assert "150" in captured.out
        assert "42 comments" in captured.out

    def test_hn_format(self, capsys):
        results = [
            {
                "title": "Show HN: New AI tool",
                "url": "https://example.com/tool",
                "points": 200,
                "comments": 85,
                "date": "Feb 15, 2026",
                "source": "hn",
            },
        ]
        print_results(results)
        captured = capsys.readouterr()
        assert "[HN]" in captured.out
        assert "Show HN: New AI tool" in captured.out
        assert "200" in captured.out
        assert "85 comments" in captured.out


class TestPrintJsonResults:
    def test_json_output(self, capsys):
        results = [
            {
                "title": "Test Post",
                "url": "https://reddit.com/r/test/comments/xyz/",
                "subreddit": "test",
                "score": 10,
                "comments": 5,
                "date": "Jan 01, 2026",
                "source": "reddit",
            },
        ]
        print_json_results(results)
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert len(parsed) == 1
        assert parsed[0]["title"] == "Test Post"
        assert parsed[0]["source"] == "reddit"

    def test_json_output_empty(self, capsys):
        print_json_results([])
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed == []
