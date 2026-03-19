"""Tests for headless module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from headless import (
    log_progress,
    retry_with_skip,
    select_sources,
    send_alert,
)


# ── select_sources ──────────────────────────────────────────────────


class TestSelectSources:
    def test_default_returns_all_sources(self):
        spec = {}
        sources = select_sources(spec)
        names = [s["name"] for s in sources]
        assert "youtube" in names
        assert "web" in names
        assert "arxiv" in names
        assert "community" in names

    def test_explicit_tools_filters(self):
        spec = {"pipeline": {"tools": ["youtube", "arxiv"]}}
        sources = select_sources(spec)
        names = [s["name"] for s in sources]
        assert names == ["youtube", "arxiv"]

    def test_unknown_tool_ignored(self):
        spec = {"pipeline": {"tools": ["youtube", "unknown_tool"]}}
        sources = select_sources(spec)
        names = [s["name"] for s in sources]
        assert names == ["youtube"]

    def test_constraint_academic_prefers_arxiv(self):
        spec = {"domain": {"constraints": ["학술 논문 중심"]}}
        sources = select_sources(spec)
        names = [s["name"] for s in sources]
        assert names[0] == "arxiv"

    def test_constraint_video_prefers_youtube(self):
        spec = {"domain": {"constraints": ["영상 콘텐츠 위주"]}}
        sources = select_sources(spec)
        names = [s["name"] for s in sources]
        assert names[0] == "youtube"

    def test_tools_take_precedence_over_constraints(self):
        spec = {
            "pipeline": {"tools": ["web"]},
            "domain": {"constraints": ["학술 논문"]},
        }
        sources = select_sources(spec)
        names = [s["name"] for s in sources]
        assert names == ["web"]

    def test_source_has_script_field(self):
        spec = {}
        sources = select_sources(spec)
        for s in sources:
            assert "script" in s
            assert s["script"].endswith(".py")


# ── retry_with_skip ─────────────────────────────────────────────────


class TestRetryWithSkip:
    def test_success_first_try(self):
        def ok():
            return 42
        assert retry_with_skip(ok) == 42

    def test_success_after_retry(self):
        call_count = {"n": 0}
        def fail_then_ok():
            call_count["n"] += 1
            if call_count["n"] < 2:
                raise RuntimeError("fail")
            return "ok"
        result = retry_with_skip(fail_then_ok, max_retries=2, timeout=1)
        assert result == "ok"

    def test_returns_none_on_all_failures(self):
        def always_fail():
            raise RuntimeError("always")
        result = retry_with_skip(always_fail, max_retries=1, timeout=1)
        assert result is None

    def test_passes_args_and_kwargs(self):
        def add(a, b, extra=0):
            return a + b + extra
        result = retry_with_skip(add, args=(1, 2), kwargs={"extra": 10})
        assert result == 13

    def test_zero_retries_tries_once(self):
        call_count = {"n": 0}
        def counter():
            call_count["n"] += 1
            raise RuntimeError("fail")
        retry_with_skip(counter, max_retries=0, timeout=1)
        assert call_count["n"] == 1


# ── log_progress ────────────────────────────────────────────────────


class TestLogProgress:
    def test_creates_log_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)
        path = log_progress("ses_001", "research", "Starting search")
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "[INFO]" in content
        assert "[research]" in content
        assert "Starting search" in content

    def test_appends_to_existing_log(self, tmp_path, monkeypatch):
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)
        log_progress("ses_001", "research", "First line")
        log_progress("ses_001", "research", "Second line")
        path = tmp_path / "ses_001" / "progress.log"
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2

    def test_custom_level(self, tmp_path, monkeypatch):
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)
        log_progress("ses_001", "eval", "Drift detected", level="warning")
        path = tmp_path / "ses_001" / "progress.log"
        assert "[WARNING]" in path.read_text(encoding="utf-8")

    def test_creates_session_directory(self, tmp_path, monkeypatch):
        monkeypatch.setattr("headless.PIPELINES_DIR", tmp_path)
        log_progress("new_session", "phase0", "Init")
        assert (tmp_path / "new_session").is_dir()


# ── send_alert ──────────────────────────────────────────────────────


class TestSendAlert:
    def test_does_not_raise_without_webhook(self):
        # Should silently succeed (or fail gracefully)
        send_alert("Test", "Body")

    def test_does_not_raise_with_invalid_webhook(self, monkeypatch):
        monkeypatch.setenv("XLOOP_WEBHOOK_URL", "http://invalid.local/webhook")
        send_alert("Test", "Body")
