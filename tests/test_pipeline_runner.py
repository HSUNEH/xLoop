"""Tests for pipeline_runner.sh — Phase 0→5 orchestrator."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
RUNNER_SH = SCRIPTS_DIR / "pipeline_runner.sh"

sys.path.insert(0, str(SCRIPTS_DIR))

from pipeline_spec import create_spec, save_spec  # noqa: E402


def _make_valid_spec():
    """Create a valid spec that passes validation."""
    spec = create_spec()
    spec["goal"]["deliverables"] = ["리서치 보고서"]
    spec["goal"]["success_criteria"] = ["파일 1개", "5000자 이상"]
    spec["domain"]["target"] = "AI agents"
    spec["domain"]["constraints"] = ["한국어"]
    spec["domain"]["references"] = ["참고 자료"]
    return spec


def _run_runner(session_id, pipelines_dir, extra_args=None, timeout=30):
    """Run pipeline_runner.sh via subprocess."""
    cmd = ["bash", str(RUNNER_SH), session_id]
    if extra_args:
        cmd.extend(extra_args)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(SCRIPTS_DIR.parent),
    )
    return result


def _setup_session(tmp_path, monkeypatch, session_id="test_run"):
    """Set up a valid session with spec.json in data/pipelines/."""
    pipelines_dir = tmp_path / "data" / "pipelines"
    pipelines_dir.mkdir(parents=True)

    # Monkeypatch PIPELINES_DIR for Python modules
    monkeypatch.setattr("pipeline_spec.PIPELINES_DIR", pipelines_dir)
    monkeypatch.setattr("pipeline_schema.PIPELINES_DIR", pipelines_dir)

    spec = _make_valid_spec()
    save_spec(spec, session_id)

    return pipelines_dir, spec


class TestRunnerWithSubprocess:
    """Integration tests that run pipeline_runner.sh via subprocess.

    These tests use the actual data/pipelines directory.
    """

    def _setup_real_session(self, session_id):
        """Set up a session in the real pipelines dir."""
        from pipeline_schema import PIPELINES_DIR

        session_dir = PIPELINES_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        spec = _make_valid_spec()
        spec_path = session_dir / "spec.json"
        spec_path.write_text(
            json.dumps(spec, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return session_dir

    def _cleanup_session(self, session_id):
        """Remove test session directory."""
        import shutil
        from pipeline_schema import PIPELINES_DIR

        session_dir = PIPELINES_DIR / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir)

    def test_full_pipeline_run(self):
        """Run full pipeline and verify all outputs are created."""
        session_id = "test_runner_full"
        try:
            session_dir = self._setup_real_session(session_id)
            result = _run_runner(session_id, None)

            assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"

            # Check output files
            assert (session_dir / "spec.json").exists()
            assert (session_dir / "runner.log").exists()
            assert (session_dir / "progress.log").exists()
            assert (session_dir / "handoff_0_to_1.json").exists()
            assert (session_dir / "research.json").exists()
            assert (session_dir / "handoff_1_to_2.json").exists()
            assert (session_dir / "strategy.json").exists()
            assert (session_dir / "handoff_2_to_3.json").exists()
            assert (session_dir / "execution.json").exists()
            assert (session_dir / "handoff_3_to_4.json").exists()
            assert (session_dir / "validation.json").exists()
            assert (session_dir / "handoff_4_to_5.json").exists()

            # Verify handoff contents
            h01 = json.loads((session_dir / "handoff_0_to_1.json").read_text())
            assert h01["from_phase"] == 0
            assert h01["to_phase"] == 1
            assert h01["session_id"] == session_id

            h12 = json.loads((session_dir / "handoff_1_to_2.json").read_text())
            assert h12["from_phase"] == 1
            assert h12["to_phase"] == 2

            # Verify phase outputs
            research = json.loads((session_dir / "research.json").read_text())
            assert research["session_id"] == session_id
            assert research["topic"] == "AI agents"

            strategy = json.loads((session_dir / "strategy.json").read_text())
            assert strategy["session_id"] == session_id

            execution = json.loads((session_dir / "execution.json").read_text())
            assert execution["session_id"] == session_id

            validation = json.loads((session_dir / "validation.json").read_text())
            assert validation["session_id"] == session_id
            assert validation["passed"] is True

            # Verify pipeline complete message
            assert "Pipeline complete" in result.stdout

        finally:
            self._cleanup_session(session_id)

    def test_missing_spec_fails(self):
        """Runner should fail if spec.json is missing."""
        session_id = "test_runner_nospec"
        try:
            from pipeline_schema import PIPELINES_DIR
            session_dir = PIPELINES_DIR / session_id
            session_dir.mkdir(parents=True, exist_ok=True)

            result = _run_runner(session_id, None)
            assert result.returncode != 0
            assert "spec.json not found" in result.stdout or "spec.json not found" in result.stderr
        finally:
            self._cleanup_session(session_id)

    def test_no_args_shows_usage(self):
        """Runner with no args should show usage."""
        result = subprocess.run(
            ["bash", str(RUNNER_SH)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode != 0
        assert "Usage" in result.stderr

    def test_unknown_option_fails(self):
        """Runner with unknown option should fail."""
        result = subprocess.run(
            ["bash", str(RUNNER_SH), "test_session", "--bad-option"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode != 0
        assert "Unknown option" in result.stderr

    def test_runner_log_created(self):
        """Runner should create runner.log with timestamps."""
        session_id = "test_runner_log"
        try:
            session_dir = self._setup_real_session(session_id)
            _run_runner(session_id, None)

            log_path = session_dir / "runner.log"
            assert log_path.exists()
            log_content = log_path.read_text()
            assert "Pipeline Runner Start" in log_content
            assert "Pipeline Complete" in log_content
            assert session_id in log_content

        finally:
            self._cleanup_session(session_id)

    def test_progress_log_created(self):
        """Runner should create progress.log via headless.py."""
        session_id = "test_runner_progress"
        try:
            session_dir = self._setup_real_session(session_id)
            _run_runner(session_id, None)

            progress_path = session_dir / "progress.log"
            assert progress_path.exists()
            content = progress_path.read_text()
            assert "phase0" in content
            assert "파이프라인 완료" in content

        finally:
            self._cleanup_session(session_id)

    def test_handoff_chain_valid(self):
        """All handoffs should be valid per pipeline_schema."""
        from pipeline_schema import validate_handoff

        session_id = "test_runner_handoffs"
        try:
            session_dir = self._setup_real_session(session_id)
            result = _run_runner(session_id, None)
            assert result.returncode == 0

            for from_p, to_p in [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]:
                path = session_dir / f"handoff_{from_p}_to_{to_p}.json"
                assert path.exists(), f"Missing handoff_{from_p}_to_{to_p}.json"
                data = json.loads(path.read_text())
                v = validate_handoff(data)
                assert v["valid"], f"Handoff {from_p}→{to_p} invalid: {v}"

        finally:
            self._cleanup_session(session_id)

    def test_drift_exceeds_threshold_exits_2(self):
        """When drift > 0.3, runner should exit with code 2."""
        session_id = "test_runner_drift"
        try:
            session_dir = self._setup_real_session(session_id)

            # Pre-create a validation.json with high drift
            validation = {
                "version": "1.0",
                "session_id": session_id,
                "completed_at": "2026-03-19T00:00:00+00:00",
                "passed": False,
                "drift_score": 0.8,
                "stage1_mechanical": {"passed": False, "checks": []},
                "stage2_semantic": {"passed": False, "spec_alignment": 0.2, "notes": []},
                "stage3_consensus": {
                    "passed": False, "advocate": "", "critic": "",
                    "judge": "", "drift_score": 0.8,
                },
                "action": "phase0_return",
                "feedback": [],
            }
            (session_dir / "validation.json").write_text(
                json.dumps(validation, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            result = _run_runner(session_id, None)
            assert result.returncode == 2, f"Expected exit 2, got {result.returncode}\nstdout:\n{result.stdout}"

            # Check drift_log.json was created
            drift_log = session_dir / "drift_log.json"
            assert drift_log.exists()
            records = json.loads(drift_log.read_text())
            assert len(records) >= 1
            assert records[-1]["drift_score"] == 0.8
            assert records[-1]["action"] == "phase0_return"

        finally:
            self._cleanup_session(session_id)

    def test_existing_research_reused(self):
        """If research.json already exists and is valid, it should be reused."""
        session_id = "test_runner_reuse"
        try:
            session_dir = self._setup_real_session(session_id)

            # Pre-create a valid research.json
            research = {
                "version": "1.0",
                "session_id": session_id,
                "topic": "pre-existing research",
                "completed_at": "2026-03-19T00:00:00+00:00",
                "loop_summary": {"total_iterations": 5, "total_queries": 20,
                                 "total_sources": 30, "covered_topics": ["topic1"]},
                "sources": [{"url": "https://example.com", "title": "Test"}],
                "findings": ["실제 리서치 결과"],
                "open_gaps": [],
                "notebook_id": None,
            }
            (session_dir / "research.json").write_text(
                json.dumps(research, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            result = _run_runner(session_id, None)
            assert result.returncode == 0

            # Verify the pre-existing research was kept
            loaded = json.loads((session_dir / "research.json").read_text())
            assert loaded["topic"] == "pre-existing research"
            assert loaded["findings"] == ["실제 리서치 결과"]

        finally:
            self._cleanup_session(session_id)


class TestRunnerUnitHelpers:
    """Unit tests for Python functions used by the runner."""

    def test_create_handoff_via_schema(self):
        from pipeline_schema import create_handoff, validate_handoff

        handoff = create_handoff(2, 3, "ses_test",
                                 output_file="strategy.json",
                                 summary={"tasks": 5})
        assert handoff["from_phase"] == 2
        assert handoff["to_phase"] == 3
        result = validate_handoff(handoff)
        assert result["valid"]

    def test_is_phase_active_all_default(self):
        """Default spec has all phases active."""
        spec = _make_valid_spec()
        active = spec.get("pipeline", {}).get("active_phases", [0, 1, 2, 3, 4, 5])
        for p in range(6):
            assert p in active

    def test_is_phase_active_subset(self):
        """Spec with subset of phases."""
        spec = _make_valid_spec()
        spec["pipeline"]["active_phases"] = [0, 1, 4, 5]
        active = spec["pipeline"]["active_phases"]
        assert 2 not in active
        assert 3 not in active
