"""Tests for yt_search module."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from yt_search import (
    filter_videos,
    format_date,
    format_duration,
    format_subscribers,
    format_views,
    get_cutoff_date,
    parse_args,
    print_json_results,
)


class TestParseArgs:
    def test_basic_query(self):
        query, count, months, json_output, filters = parse_args(["prog", "AI", "agents"])
        assert query == "AI agents"
        assert count == 20
        assert months == 6
        assert json_output is False
        assert filters["min_views"] == 0

    def test_count_flag(self):
        query, count, months, json_output, filters = parse_args(["prog", "test", "--count", "5"])
        assert query == "test"
        assert count == 5

    def test_months_flag(self):
        query, count, months, json_output, filters = parse_args(["prog", "test", "--months", "3"])
        assert query == "test"
        assert months == 3

    def test_no_date_filter(self):
        query, count, months, json_output, filters = parse_args(["prog", "test", "--no-date-filter"])
        assert query == "test"
        assert months == 0

    def test_json_flag(self):
        query, count, months, json_output, filters = parse_args(["prog", "test", "--json"])
        assert query == "test"
        assert json_output is True

    def test_json_with_other_flags(self):
        query, count, months, json_output, filters = parse_args(
            ["prog", "AI", "tutorial", "--json", "--count", "5", "--months", "3"]
        )
        assert query == "AI tutorial"
        assert count == 5
        assert months == 3
        assert json_output is True

    def test_no_query_exits(self):
        try:
            parse_args(["prog"])
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code == 1

    def test_min_views_flag(self):
        query, count, months, json_output, filters = parse_args(
            ["prog", "test", "--min-views", "1000"]
        )
        assert filters["min_views"] == 1000

    def test_min_duration_flag(self):
        query, count, months, json_output, filters = parse_args(
            ["prog", "test", "--min-duration", "5"]
        )
        assert filters["min_duration"] == 5

    def test_max_duration_flag(self):
        query, count, months, json_output, filters = parse_args(
            ["prog", "test", "--max-duration", "30"]
        )
        assert filters["max_duration"] == 30

    def test_channel_flag(self):
        query, count, months, json_output, filters = parse_args(
            ["prog", "test", "--channel", "3Blue1Brown"]
        )
        assert filters["channels"] == ["3Blue1Brown"]

    def test_multiple_channels(self):
        query, count, months, json_output, filters = parse_args(
            ["prog", "test", "--channel", "A", "--channel", "B"]
        )
        assert filters["channels"] == ["A", "B"]

    def test_exclude_channel_flag(self):
        query, count, months, json_output, filters = parse_args(
            ["prog", "test", "--exclude-channel", "SpamBot"]
        )
        assert filters["exclude_channels"] == ["SpamBot"]

    def test_all_filters_combined(self):
        query, count, months, json_output, filters = parse_args(
            ["prog", "AI", "--min-views", "500", "--min-duration", "3",
             "--max-duration", "60", "--channel", "DeepMind", "--exclude-channel", "Spam"]
        )
        assert query == "AI"
        assert filters["min_views"] == 500
        assert filters["min_duration"] == 3
        assert filters["max_duration"] == 60
        assert filters["channels"] == ["DeepMind"]
        assert filters["exclude_channels"] == ["Spam"]


class TestFilterVideos:
    SAMPLE_VIDEOS = [
        {"title": "Short Low", "view_count": 100, "duration": 120, "channel": "Alpha"},
        {"title": "Long Popular", "view_count": 50000, "duration": 3600, "channel": "Beta"},
        {"title": "Medium Mid", "view_count": 5000, "duration": 600, "channel": "Alpha"},
        {"title": "No Stats", "channel": "Gamma"},
    ]

    def _default_filters(self, **overrides):
        f = {
            "min_views": 0, "min_duration": 0, "max_duration": 0,
            "channels": [], "exclude_channels": [],
        }
        f.update(overrides)
        return f

    def test_no_filters(self):
        result = filter_videos(self.SAMPLE_VIDEOS, self._default_filters())
        assert len(result) == 4

    def test_min_views(self):
        result = filter_videos(self.SAMPLE_VIDEOS, self._default_filters(min_views=1000))
        assert len(result) == 3  # 50000, 5000, and No Stats (None passes)
        titles = [v["title"] for v in result]
        assert "Short Low" not in titles

    def test_min_duration(self):
        result = filter_videos(self.SAMPLE_VIDEOS, self._default_filters(min_duration=5))
        # 5 min = 300s. 120s filtered out, 3600s and 600s pass, No Stats (None) passes
        assert len(result) == 3
        titles = [v["title"] for v in result]
        assert "Short Low" not in titles

    def test_max_duration(self):
        result = filter_videos(self.SAMPLE_VIDEOS, self._default_filters(max_duration=15))
        # 15 min = 900s. 3600s filtered out, 120s and 600s pass, No Stats (None) passes
        assert len(result) == 3
        titles = [v["title"] for v in result]
        assert "Long Popular" not in titles

    def test_channel_include(self):
        result = filter_videos(self.SAMPLE_VIDEOS, self._default_filters(channels=["Alpha"]))
        assert len(result) == 2
        assert all(v["channel"] == "Alpha" for v in result)

    def test_channel_case_insensitive(self):
        result = filter_videos(self.SAMPLE_VIDEOS, self._default_filters(channels=["alpha"]))
        assert len(result) == 2

    def test_exclude_channel(self):
        result = filter_videos(
            self.SAMPLE_VIDEOS, self._default_filters(exclude_channels=["Beta"])
        )
        assert len(result) == 3
        titles = [v["title"] for v in result]
        assert "Long Popular" not in titles

    def test_combined_filters(self):
        result = filter_videos(
            self.SAMPLE_VIDEOS,
            self._default_filters(min_views=1000, max_duration=15),
        )
        # min_views=1000: removes Short Low (100). max_duration=15min=900s: removes Long Popular (3600s)
        # Remaining: Medium Mid (5000 views, 600s) + No Stats (None passes both)
        assert len(result) == 2

    def test_none_view_count_passes(self):
        result = filter_videos(
            [{"title": "No Views", "duration": 300}],
            self._default_filters(min_views=1000),
        )
        assert len(result) == 1

    def test_none_duration_passes(self):
        result = filter_videos(
            [{"title": "No Duration", "view_count": 5000}],
            self._default_filters(min_duration=5),
        )
        assert len(result) == 1


class TestFormatSubscribers:
    def test_none(self):
        assert format_subscribers(None) == "N/A"

    def test_millions(self):
        assert format_subscribers(1_500_000) == "1.5M"

    def test_thousands(self):
        assert format_subscribers(45_200) == "45.2K"

    def test_small(self):
        assert format_subscribers(500) == "500"


class TestFormatViews:
    def test_none(self):
        assert format_views(None) == "N/A"

    def test_with_commas(self):
        assert format_views(1234567) == "1,234,567"


class TestFormatDuration:
    def test_duration_string(self):
        assert format_duration({"duration_string": "5:30"}) == "5:30"

    def test_duration_seconds(self):
        assert format_duration({"duration": 150}) == "2:30"

    def test_duration_hours(self):
        assert format_duration({"duration": 3661}) == "1:01:01"

    def test_no_duration(self):
        assert format_duration({}) == "N/A"


class TestFormatDate:
    def test_valid_date(self):
        assert format_date("20260115") == "Jan 15, 2026"

    def test_invalid_date(self):
        assert format_date("abc") == "N/A"

    def test_none(self):
        assert format_date(None) == "N/A"


class TestGetCutoffDate:
    def test_zero_months(self):
        assert get_cutoff_date(0) is None

    def test_positive_months(self):
        result = get_cutoff_date(6)
        assert result is not None
        assert len(result) == 8


class TestPrintJsonResults:
    def test_json_output_format(self, capsys):
        videos = [
            {
                "id": "abc123",
                "title": "Test Video",
                "channel": "Test Channel",
                "view_count": 1000,
                "upload_date": "20260115",
            },
            {
                "id": "def456",
                "title": "Another Video",
                "uploader": "Another Channel",
                "view_count": None,
                "upload_date": "",
            },
        ]
        print_json_results(videos)
        captured = capsys.readouterr()
        results = json.loads(captured.out)
        assert len(results) == 2
        assert results[0]["url"] == "https://youtube.com/watch?v=abc123"
        assert results[0]["title"] == "Test Video"
        assert results[0]["channel"] == "Test Channel"
        assert results[0]["views"] == 1000
        assert results[0]["date"] == "Jan 15, 2026"
        assert results[1]["url"] == "https://youtube.com/watch?v=def456"
        assert results[1]["channel"] == "Another Channel"
        assert results[1]["views"] is None
        assert results[1]["date"] == "N/A"

    def test_json_output_empty(self, capsys):
        print_json_results([])
        captured = capsys.readouterr()
        results = json.loads(captured.out)
        assert results == []

    def test_json_output_no_id(self, capsys):
        videos = [{"title": "No ID Video"}]
        print_json_results(videos)
        captured = capsys.readouterr()
        results = json.loads(captured.out)
        assert results[0]["url"] is None
