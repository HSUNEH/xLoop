#!/usr/bin/env python3
"""Evaluation Engine — 3-Stage Validation: Mechanical → Semantic → Consensus (B+C Drift)."""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PIPELINES_DIR = Path(__file__).resolve().parent.parent / "data" / "pipelines"

DRIFT_THRESHOLD = 0.3


# ── Helpers ─────────────────────────────────────────────────────────

def _now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ── Stage 1: Mechanical Verification ────────────────────────────────

def run_stage1(spec, execution):
    """Stage 1: success_criteria의 정량 기준 자동 체크.

    Returns:
        dict: {"passed": bool, "checks": list}
    """
    checks = []
    criteria = spec.get("goal", {}).get("success_criteria", [])

    artifacts = execution.get("artifacts", [])
    tasks_completed = execution.get("tasks_completed", 0)
    tasks_failed = execution.get("tasks_failed", 0)
    total_tasks = tasks_completed + tasks_failed

    # Check 1: Execution has artifacts
    checks.append({
        "name": "has_artifacts",
        "passed": len(artifacts) > 0,
        "detail": f"산출물 {len(artifacts)}개",
    })

    # Check 2: Task success rate >= 80%
    if total_tasks > 0:
        success_rate = tasks_completed / total_tasks
        checks.append({
            "name": "task_success_rate",
            "passed": success_rate >= 0.8,
            "detail": f"성공률 {success_rate:.0%} ({tasks_completed}/{total_tasks})",
        })

    # Check 3: Quantitative criteria from spec
    for criterion in criteria:
        check = _check_quantitative(criterion, execution)
        if check is not None:
            checks.append(check)

    passed = all(c["passed"] for c in checks) if checks else False

    return {"passed": passed, "checks": checks}


def _check_quantitative(criterion, execution):
    """Extract numbers from criterion and check against execution metrics."""
    numbers = re.findall(r'\d+', criterion)
    if not numbers:
        return None

    threshold = int(numbers[0])

    artifacts_count = len(execution.get("artifacts", []))
    completed = execution.get("tasks_completed", 0)

    passed = artifacts_count >= threshold or completed >= threshold

    return {
        "name": f"quantitative: {criterion[:50]}",
        "passed": passed,
        "detail": f"기준={threshold}, 산출물={artifacts_count}, 완료={completed}",
    }


# ── Stage 2: Semantic Verification ──────────────────────────────────

def run_stage2(spec, execution):
    """Stage 2: spec과 execution의 정성적 정합성 평가.

    Returns:
        dict: {"passed": bool, "spec_alignment": float, "notes": list}
    """
    notes = []
    scores = []

    deliverables = spec.get("goal", {}).get("deliverables", [])
    artifacts = execution.get("artifacts", [])

    # Deliverable coverage
    if deliverables:
        artifact_texts = " ".join(
            str(a.get("artifact", {}).get("output", "") if isinstance(a.get("artifact"), dict) else a.get("artifact", ""))
            + " " + str(a.get("task_id", ""))
            for a in artifacts
        ).lower()

        covered = 0
        for d in deliverables:
            words = [w for w in d.lower().split() if len(w) > 2]
            if any(w in artifact_texts for w in words):
                covered += 1
                notes.append(f"deliverable 매칭: {d[:50]}")
            else:
                notes.append(f"deliverable 미매칭: {d[:50]}")

        coverage = covered / len(deliverables)
        scores.append(coverage)
    else:
        notes.append("deliverables 미정의")
        scores.append(0.5)

    # Task completion quality
    tasks_completed = execution.get("tasks_completed", 0)
    tasks_failed = execution.get("tasks_failed", 0)
    total = tasks_completed + tasks_failed

    if total > 0:
        completion_score = tasks_completed / total
        scores.append(completion_score)
        notes.append(f"작업 완료율: {completion_score:.0%}")
    else:
        scores.append(0.0)
        notes.append("실행된 작업 없음")

    spec_alignment = sum(scores) / len(scores) if scores else 0.0
    spec_alignment = round(spec_alignment, 2)

    passed = spec_alignment >= 0.7

    return {"passed": passed, "spec_alignment": spec_alignment, "notes": notes}


# ── Stage 3: Consensus Verification (B+C) ──────────────────────────

def advocate(spec, execution, stage1, stage2):
    """옹호자: execution이 spec을 충족한다는 주장을 구성."""
    points = []

    passed_checks = [c for c in stage1.get("checks", []) if c["passed"]]
    if passed_checks:
        points.append(f"기계적 검증 {len(passed_checks)}개 항목 통과")

    alignment = stage2.get("spec_alignment", 0)
    if alignment >= 0.7:
        points.append(f"spec 정합성 {alignment:.0%}로 양호")

    completed = execution.get("tasks_completed", 0)
    if completed > 0:
        points.append(f"{completed}개 작업 성공적 완료")

    artifacts = execution.get("artifacts", [])
    done_artifacts = [a for a in artifacts if a.get("status") == "done"]
    if done_artifacts:
        tools_used = set(a.get("tool", "") for a in done_artifacts)
        points.append(f"도구 {len(tools_used)}종 활용하여 산출물 {len(done_artifacts)}개 생성")

    if not points:
        points.append("특별한 성과 없음")

    return "옹호: " + "; ".join(points)


def critic(spec, execution, stage1, stage2):
    """비판자: execution의 미충족/문제점을 지적."""
    points = []

    failed_checks = [c for c in stage1.get("checks", []) if not c["passed"]]
    if failed_checks:
        points.append(f"기계적 검증 {len(failed_checks)}개 항목 실패")

    alignment = stage2.get("spec_alignment", 0)
    if alignment < 0.7:
        points.append(f"spec 정합성 {alignment:.0%}로 미흡")

    unmatched = [n for n in stage2.get("notes", []) if "미매칭" in n]
    if unmatched:
        points.append(f"deliverable {len(unmatched)}개 미충족")

    failed = execution.get("tasks_failed", 0)
    if failed > 0:
        points.append(f"{failed}개 작업 실패")

    if not points:
        points.append("특별한 문제점 없음")

    return "비판: " + "; ".join(points)


def judge(advocate_text, critic_text, stage1, stage2):
    """판사: 양쪽 의견을 종합하여 drift_score 산출.

    Returns:
        dict: stage3_consensus structure
    """
    scores = []

    # Stage 1 contribution (40%)
    total_checks = stage1.get("checks", [])
    if total_checks:
        passed_ratio = sum(1 for c in total_checks if c["passed"]) / len(total_checks)
        scores.append(("stage1", 0.4, 1.0 - passed_ratio))
    else:
        scores.append(("stage1", 0.4, 0.5))

    # Stage 2 contribution (60%)
    alignment = stage2.get("spec_alignment", 0.0)
    scores.append(("stage2", 0.6, 1.0 - alignment))

    drift_score = sum(weight * score for _, weight, score in scores)
    drift_score = round(min(1.0, max(0.0, drift_score)), 2)

    if drift_score <= DRIFT_THRESHOLD:
        judge_text = f"판정: drift {drift_score} <= {DRIFT_THRESHOLD}, 통과"
    else:
        judge_text = f"판정: drift {drift_score} > {DRIFT_THRESHOLD}, 재검토 필요"

    passed = drift_score <= DRIFT_THRESHOLD

    return {
        "passed": passed,
        "advocate": advocate_text,
        "critic": critic_text,
        "judge": judge_text,
        "drift_score": drift_score,
    }


def run_stage3(spec, execution, stage1, stage2):
    """Stage 3 합의 검증 실행."""
    advocate_text = advocate(spec, execution, stage1, stage2)
    critic_text = critic(spec, execution, stage1, stage2)
    return judge(advocate_text, critic_text, stage1, stage2)


# ── Determine Action ────────────────────────────────────────────────

def determine_action(drift_score):
    """drift_score에 따른 다음 행동 결정.

    - drift <= 0.3: "pass"
    - drift > 0.3: "restart" (Phase 0 복귀)
    """
    if drift_score <= DRIFT_THRESHOLD:
        return "pass"
    return "restart"


# ── Full Evaluation ─────────────────────────────────────────────────

def run_evaluation(session_id):
    """spec.json + execution.json → 3단계 검증 → validation.json 저장.

    Returns:
        dict: validation output (VALIDATION_SCHEMA)
    """
    from pipeline_schema import (
        create_validation,
        save_phase_output,
        validate_validation,
    )
    from pipeline_spec import load_spec

    from pipeline_schema import load_phase_output

    # Load inputs
    spec = load_spec(session_id)
    execution = load_phase_output("execution", session_id)

    # Stage 1: Mechanical
    stage1 = run_stage1(spec, execution)

    # Stage 2: Semantic
    stage2 = run_stage2(spec, execution)

    # Stage 3: Consensus
    stage3 = run_stage3(spec, execution, stage1, stage2)

    # Build validation output
    validation = create_validation(session_id)
    validation["completed_at"] = _now_iso()
    validation["stage1_mechanical"] = stage1
    validation["stage2_semantic"] = stage2
    validation["stage3_consensus"] = stage3
    validation["drift_score"] = stage3["drift_score"]
    validation["passed"] = stage3["passed"]
    validation["action"] = determine_action(stage3["drift_score"])

    # Collect feedback
    feedback = []
    for check in stage1.get("checks", []):
        if not check["passed"]:
            feedback.append(f"[Stage1] {check['name']}: {check['detail']}")
    for note in stage2.get("notes", []):
        if "미매칭" in note or "실행된 작업 없음" in note:
            feedback.append(f"[Stage2] {note}")
    validation["feedback"] = feedback

    # Validate against schema
    schema_result = validate_validation(validation)
    if not schema_result["valid"]:
        print(f"검증 스키마 오류: {schema_result['missing']}", file=sys.stderr)

    # Save
    save_phase_output(validation, "validation", session_id)

    return validation


def show_validation(validation):
    """검증 결과를 사람이 읽을 수 있는 형태로 출력."""
    print(f"Session: {validation.get('session_id', '?')}")
    print(f"Passed: {validation.get('passed', False)}")
    print(f"Drift Score: {validation.get('drift_score', '?')}")
    print(f"Action: {validation.get('action', '?')}")

    print()

    # Stage 1
    s1 = validation.get("stage1_mechanical", {})
    s1_mark = "PASS" if s1.get("passed") else "FAIL"
    print(f"Stage 1 (Mechanical): {s1_mark}")
    for check in s1.get("checks", []):
        mark = "OK" if check["passed"] else "FAIL"
        print(f"  [{mark}] {check['name']}: {check['detail']}")

    print()

    # Stage 2
    s2 = validation.get("stage2_semantic", {})
    s2_mark = "PASS" if s2.get("passed") else "FAIL"
    print(f"Stage 2 (Semantic): {s2_mark}")
    print(f"  Spec Alignment: {s2.get('spec_alignment', 0):.0%}")
    for note in s2.get("notes", []):
        print(f"  {note}")

    print()

    # Stage 3
    s3 = validation.get("stage3_consensus", {})
    s3_mark = "PASS" if s3.get("passed") else "FAIL"
    print(f"Stage 3 (Consensus): {s3_mark}")
    print(f"  {s3.get('advocate', '')}")
    print(f"  {s3.get('critic', '')}")
    print(f"  {s3.get('judge', '')}")

    # Feedback
    feedback = validation.get("feedback", [])
    if feedback:
        print()
        print("Feedback:")
        for f in feedback:
            print(f"  - {f}")


# ── CLI ─────────────────────────────────────────────────────────────

def _parse_cli(argv):
    """Minimal CLI dispatcher."""
    if len(argv) < 2:
        _usage()
        sys.exit(1)

    cmd = argv[1]

    if cmd in ("full", "check"):
        if len(argv) < 3:
            print(f"Usage: evaluation_engine.py {cmd} <session_id>", file=sys.stderr)
            sys.exit(1)
        session_id = argv[2]
        validation = run_evaluation(session_id)
        print(json.dumps(validation, indent=2, ensure_ascii=False))

    elif cmd == "stage1":
        if len(argv) < 3:
            print("Usage: evaluation_engine.py stage1 <session_id>", file=sys.stderr)
            sys.exit(1)
        from pipeline_schema import load_phase_output
        from pipeline_spec import load_spec

        session_id = argv[2]
        spec = load_spec(session_id)
        execution = load_phase_output("execution", session_id)
        result = run_stage1(spec, execution)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "stage2":
        if len(argv) < 3:
            print("Usage: evaluation_engine.py stage2 <session_id>", file=sys.stderr)
            sys.exit(1)
        from pipeline_schema import load_phase_output
        from pipeline_spec import load_spec

        session_id = argv[2]
        spec = load_spec(session_id)
        execution = load_phase_output("execution", session_id)
        result = run_stage2(spec, execution)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "stage3":
        if len(argv) < 3:
            print("Usage: evaluation_engine.py stage3 <session_id>", file=sys.stderr)
            sys.exit(1)
        from pipeline_schema import load_phase_output
        from pipeline_spec import load_spec

        session_id = argv[2]
        spec = load_spec(session_id)
        execution = load_phase_output("execution", session_id)
        stage1 = run_stage1(spec, execution)
        stage2 = run_stage2(spec, execution)
        result = run_stage3(spec, execution, stage1, stage2)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "show":
        if len(argv) < 3:
            print("Usage: evaluation_engine.py show <session_id>", file=sys.stderr)
            sys.exit(1)
        from pipeline_schema import load_phase_output

        session_id = argv[2]
        data = load_phase_output("validation", session_id)
        show_validation(data)

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        _usage()
        sys.exit(1)


def _usage():
    print(
        "Usage: evaluation_engine.py <command> [args]\n\n"
        "Commands:\n"
        "  full <session_id>     Run all 3 stages, save validation.json\n"
        "  check <session_id>    Alias for full\n"
        "  stage1 <session_id>   Run Stage 1 (mechanical) only\n"
        "  stage2 <session_id>   Run Stage 2 (semantic) only\n"
        "  stage3 <session_id>   Run Stage 3 (consensus) only\n"
        "  show <session_id>     Show saved validation summary",
        file=sys.stderr,
    )


if __name__ == "__main__":
    _parse_cli(sys.argv)
