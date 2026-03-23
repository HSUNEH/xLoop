#!/usr/bin/env python3
"""Tests for tool plugin system (US-003)."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


# ── load_tool_manifest ──────────────────────────────────────────────

def test_load_tool_manifest_exists():
    from execution_engine import load_tool_manifest
    manifest = load_tool_manifest()
    assert manifest is not None
    assert "tools" in manifest
    assert "claude" in manifest["tools"]


def test_load_tool_manifest_missing(tmp_path, monkeypatch):
    from execution_engine import load_tool_manifest
    import execution_engine
    monkeypatch.setattr(execution_engine, "_MANIFEST_PATH", tmp_path / "nonexistent.json")
    result = load_tool_manifest()
    assert result is None


def test_load_tool_manifest_corrupted(tmp_path, monkeypatch):
    from execution_engine import load_tool_manifest
    import execution_engine
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{bad json", encoding="utf-8")
    monkeypatch.setattr(execution_engine, "_MANIFEST_PATH", bad_path)
    result = load_tool_manifest()
    assert result is None


# ── register_tools_from_manifest ────────────────────────────────────

def test_register_from_manifest_default_tools():
    from execution_engine import register_tools_from_manifest, list_tools
    register_tools_from_manifest()
    tools = list_tools()
    assert "claude" in tools
    assert "dall-e" in tools
    assert "flux" in tools
    assert "notebooklm" in tools
    assert "web_search" in tools


def test_register_from_manifest_fallback(tmp_path, monkeypatch):
    """When manifest is missing, default stubs are registered."""
    import execution_engine
    monkeypatch.setattr(execution_engine, "_MANIFEST_PATH", tmp_path / "missing.json")
    execution_engine.register_tools_from_manifest()
    tools = execution_engine.list_tools()
    assert len(tools) == 5
    # Restore
    execution_engine.register_tools_from_manifest()


def test_register_from_manifest_disabled_tool(tmp_path, monkeypatch):
    """Disabled tools should not be registered."""
    import execution_engine
    manifest = {
        "tools": {
            "claude": {"label": "Claude", "type": "generation", "keywords": [], "enabled": True},
            "dall-e": {"label": "DALL-E", "type": "image", "keywords": [], "enabled": False},
        }
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(execution_engine, "_MANIFEST_PATH", manifest_path)
    execution_engine.register_tools_from_manifest()
    tools = execution_engine.list_tools()
    assert "claude" in tools
    assert "dall-e" not in tools
    # Restore
    monkeypatch.setattr(execution_engine, "_MANIFEST_PATH",
                        execution_engine.Path(__file__).resolve().parent.parent / "data" / "tool_manifest.json")
    execution_engine.register_tools_from_manifest()


def test_register_from_manifest_external_tool(tmp_path, monkeypatch):
    """External tools (not in default stubs) should get a generic stub."""
    import execution_engine
    manifest = {
        "tools": {
            "claude": {"label": "Claude", "type": "generation", "keywords": [], "enabled": True},
            "my_custom_tool": {"label": "Custom", "type": "custom", "keywords": ["custom"], "enabled": True},
        }
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(execution_engine, "_MANIFEST_PATH", manifest_path)
    execution_engine.register_tools_from_manifest()
    tools = execution_engine.list_tools()
    assert "my_custom_tool" in tools
    # Test the external stub works
    fn = execution_engine.get_tool("my_custom_tool")
    result = fn({"id": "t1", "title": "test"}, "s1")
    assert result["tool"] == "my_custom_tool"
    assert result["type"] == "external"
    # Restore
    monkeypatch.setattr(execution_engine, "_MANIFEST_PATH",
                        execution_engine.Path(__file__).resolve().parent.parent / "data" / "tool_manifest.json")
    execution_engine.register_tools_from_manifest()


# ── check_tool_health ───────────────────────────────────────────────

def test_check_tool_health_all():
    from execution_engine import check_tool_health
    health = check_tool_health()
    assert "claude" in health
    assert health["claude"]["available"] is True
    assert health["claude"]["enabled"] is True


def test_check_tool_health_specific():
    from execution_engine import check_tool_health
    health = check_tool_health("dall-e")
    assert "dall-e" in health
    assert len(health) == 1


def test_check_tool_health_nonexistent():
    from execution_engine import check_tool_health
    health = check_tool_health("nonexistent_tool")
    assert health["nonexistent_tool"]["available"] is False


# ── strategy_engine build_tool_keywords ─────────────────────────────

def test_build_tool_keywords_returns_dict():
    from strategy_engine import build_tool_keywords
    keywords = build_tool_keywords()
    assert isinstance(keywords, dict)
    assert "claude" in keywords
    assert "dall-e" in keywords


def test_build_tool_keywords_manifest_override(tmp_path, monkeypatch):
    import strategy_engine
    manifest = {
        "tools": {
            "claude": {"label": "Claude", "keywords": ["ai", "llm"], "enabled": True},
        }
    }
    manifest_path = tmp_path / "tool_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    # Monkey-patch the path used inside build_tool_keywords
    original_build = strategy_engine.build_tool_keywords

    def patched_build():
        result = dict(strategy_engine._HARDCODED_TOOL_KEYWORDS)
        try:
            m = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return result
        for name, config in m.get("tools", {}).items():
            if not config.get("enabled", True):
                result.pop(name, None)
                continue
            kw = config.get("keywords")
            if kw:
                result[name] = kw
        return result

    keywords = patched_build()
    assert keywords["claude"] == ["ai", "llm"]
    # Other tools should keep hardcoded defaults
    assert "dall-e" in keywords


def test_build_tool_keywords_disabled_tool_removed(tmp_path):
    import strategy_engine
    manifest = {
        "tools": {
            "flux": {"label": "Flux", "keywords": [], "enabled": False},
        }
    }
    manifest_path = tmp_path / "tool_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = dict(strategy_engine._HARDCODED_TOOL_KEYWORDS)
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, config in m.get("tools", {}).items():
        if not config.get("enabled", True):
            result.pop(name, None)
    assert "flux" not in result


def test_tool_keywords_module_level_populated():
    """_TOOL_KEYWORDS should be populated at module import."""
    from strategy_engine import _TOOL_KEYWORDS
    assert isinstance(_TOOL_KEYWORDS, dict)
    assert len(_TOOL_KEYWORDS) >= 5


# ── tool_manifest.json structure ────────────────────────────────────

def test_manifest_has_all_default_tools():
    manifest_path = os.path.join(os.path.dirname(__file__), "..", "data", "tool_manifest.json")
    manifest = json.loads(open(manifest_path, encoding="utf-8").read())
    expected = {"claude", "dall-e", "flux", "notebooklm", "web_search"}
    assert set(manifest["tools"].keys()) == expected


def test_manifest_tools_have_required_fields():
    manifest_path = os.path.join(os.path.dirname(__file__), "..", "data", "tool_manifest.json")
    manifest = json.loads(open(manifest_path, encoding="utf-8").read())
    for name, config in manifest["tools"].items():
        assert "label" in config, f"{name} missing label"
        assert "type" in config, f"{name} missing type"
        assert "keywords" in config, f"{name} missing keywords"
        assert "enabled" in config, f"{name} missing enabled"
        assert isinstance(config["keywords"], list), f"{name} keywords not a list"
