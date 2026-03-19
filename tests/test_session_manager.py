"""Tests for session_manager module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from session_manager import (
    add_question,
    add_search,
    add_source,
    close_session,
    create_session,
    list_sessions,
    load_session,
    save_session,
    set_notebook,
    show_session,
)


class TestCreateSession:
    def test_creates_session_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        session = create_session("AI agents")
        assert session["topic"] == "AI agents"
        assert session["status"] == "active"
        assert session["id"].startswith("ses_")
        assert (tmp_path / f"{session['id']}.json").exists()

    def test_session_has_empty_lists(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        session = create_session("test topic")
        assert session["searches"] == []
        assert session["sources"] == []
        assert session["questions"] == []
        assert session["notebook_id"] is None


class TestLoadSession:
    def test_load_existing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        original = create_session("load test")
        loaded = load_session(original["id"])
        assert loaded["id"] == original["id"]
        assert loaded["topic"] == "load test"

    def test_load_missing_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        try:
            load_session("ses_nonexistent")
            assert False, "Expected FileNotFoundError"
        except FileNotFoundError:
            pass

    def test_load_corrupted_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        bad_path = tmp_path / "ses_bad.json"
        bad_path.write_text("{invalid json", encoding="utf-8")
        try:
            load_session("ses_bad")
            assert False, "Expected ValueError"
        except ValueError as exc:
            assert "corrupted" in str(exc)


class TestSaveSession:
    def test_overwrites_existing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        session = create_session("save test")
        session["topic"] = "updated topic"
        save_session(session)
        reloaded = load_session(session["id"])
        assert reloaded["topic"] == "updated topic"


class TestListSessions:
    def test_list_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        assert list_sessions() == []

    def test_list_all(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        create_session("topic A")
        create_session("topic B")
        sessions = list_sessions()
        assert len(sessions) == 2

    def test_list_filter_by_status(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        s1 = create_session("active one")
        s2 = create_session("to close")
        close_session(s2["id"])
        active = list_sessions(status="active")
        closed = list_sessions(status="closed")
        assert len(active) == 1
        assert active[0]["id"] == s1["id"]
        assert len(closed) == 1
        assert closed[0]["id"] == s2["id"]

    def test_list_ignores_corrupted(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        create_session("good")
        (tmp_path / "ses_bad.json").write_text("not json", encoding="utf-8")
        sessions = list_sessions()
        assert len(sessions) == 1


class TestAddSearch:
    def test_appends_search(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        session = create_session("search test")
        add_search(session["id"], {
            "source": "youtube",
            "query": "AI agents",
            "count": 10,
            "results_count": 8,
        })
        reloaded = load_session(session["id"])
        assert len(reloaded["searches"]) == 1
        assert reloaded["searches"][0]["source"] == "youtube"
        assert "timestamp" in reloaded["searches"][0]


class TestAddSource:
    def test_appends_source(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        session = create_session("source test")
        add_source(session["id"], {
            "url": "https://youtube.com/watch?v=abc",
            "title": "AI Tutorial",
            "source_type": "youtube",
        })
        reloaded = load_session(session["id"])
        assert len(reloaded["sources"]) == 1
        assert reloaded["sources"][0]["url"] == "https://youtube.com/watch?v=abc"
        assert "added_at" in reloaded["sources"][0]


class TestSetNotebook:
    def test_links_notebook(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        session = create_session("notebook test")
        set_notebook(session["id"], "nb-123", "https://notebooklm.google.com/nb-123")
        reloaded = load_session(session["id"])
        assert reloaded["notebook_id"] == "nb-123"
        assert reloaded["notebook_url"] == "https://notebooklm.google.com/nb-123"

    def test_links_without_url(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        session = create_session("notebook test 2")
        set_notebook(session["id"], "nb-456")
        reloaded = load_session(session["id"])
        assert reloaded["notebook_id"] == "nb-456"
        assert reloaded["notebook_url"] is None


class TestAddQuestion:
    def test_appends_question(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        session = create_session("question test")
        add_question(session["id"], {
            "question": "What are the main frameworks?",
            "conversation_id": "conv-123",
        })
        reloaded = load_session(session["id"])
        assert len(reloaded["questions"]) == 1
        assert reloaded["questions"][0]["question"] == "What are the main frameworks?"
        assert "timestamp" in reloaded["questions"][0]


class TestCloseSession:
    def test_closes_session(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        session = create_session("close test")
        assert session["status"] == "active"
        close_session(session["id"])
        reloaded = load_session(session["id"])
        assert reloaded["status"] == "closed"


class TestShowSession:
    def test_show_output(self, tmp_path, monkeypatch):
        monkeypatch.setattr("session_manager.SESSIONS_DIR", tmp_path)
        session = create_session("show test")
        add_source(session["id"], {
            "url": "https://example.com",
            "title": "Example",
            "source_type": "web",
        })
        output = show_session(session["id"])
        assert "show test" in output
        assert "Example" in output
        assert "Sources (1)" in output
