"""Tests for arxiv_search module."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from arxiv_search import parse_args, print_json_results, print_results


class TestParseArgs:
    def test_basic_query(self):
        query, count, sort, json_output = parse_args(["prog", "transformer", "attention"])
        assert query == "transformer attention"
        assert count == 10
        assert sort == "relevance"
        assert json_output is False

    def test_count_flag(self):
        query, count, sort, json_output = parse_args(["prog", "test", "--count", "5"])
        assert query == "test"
        assert count == 5

    def test_sort_relevance(self):
        query, count, sort, json_output = parse_args(
            ["prog", "test", "--sort", "relevance"]
        )
        assert sort == "relevance"

    def test_sort_date(self):
        query, count, sort, json_output = parse_args(
            ["prog", "test", "--sort", "date"]
        )
        assert sort == "date"

    def test_invalid_sort_exits(self):
        try:
            parse_args(["prog", "test", "--sort", "popularity"])
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code == 1

    def test_json_flag(self):
        query, count, sort, json_output = parse_args(["prog", "test", "--json"])
        assert json_output is True

    def test_all_flags(self):
        query, count, sort, json_output = parse_args(
            ["prog", "LLM", "agents", "--count", "3", "--sort", "date", "--json"]
        )
        assert query == "LLM agents"
        assert count == 3
        assert sort == "date"
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


class TestPrintResults:
    def test_print_format(self, capsys):
        results = [
            {
                "title": "Attention Is All You Need",
                "url": "https://arxiv.org/abs/1706.03762",
                "pdf_url": "https://arxiv.org/pdf/1706.03762",
                "authors": "Vaswani et al.",
                "abstract": "The dominant sequence transduction models...",
                "date": "Jun 12, 2017",
                "categories": "cs.CL, cs.LG",
            },
        ]
        print_results(results)
        captured = capsys.readouterr()
        assert "Attention Is All You Need" in captured.out
        assert "Vaswani et al." in captured.out
        assert "Jun 12, 2017" in captured.out
        assert "cs.CL" in captured.out
        assert "https://arxiv.org/pdf/1706.03762" in captured.out


class TestPrintJsonResults:
    def test_json_output_format(self, capsys):
        results = [
            {
                "title": "Test Paper",
                "url": "https://arxiv.org/abs/0000.00000",
                "pdf_url": "https://arxiv.org/pdf/0000.00000",
                "authors": "Author A, Author B",
                "abstract": "Test abstract.",
                "date": "Jan 01, 2026",
                "categories": "cs.AI",
            },
        ]
        print_json_results(results)
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert len(parsed) == 1
        assert parsed[0]["title"] == "Test Paper"
        assert parsed[0]["pdf_url"] == "https://arxiv.org/pdf/0000.00000"

    def test_json_output_empty(self, capsys):
        print_json_results([])
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed == []
