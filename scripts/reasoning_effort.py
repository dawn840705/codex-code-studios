#!/usr/bin/env python3
"""요청별 effort 관찰과 명시적으로 승인된 Codex CLI 실행.

Standard library only. No model routing, config writes, or automatic retries.
Task files and verifier argv are trusted operator input, never hook input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from console_encoding import force_utf8

POLICY_VERSION = "effort-v1-hypothesis"
EFFORTS = ("none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra")
SIGNALS = {
    "scope": ("single", "subsystem", "cross", "unknown"),
    "impact": ("low", "medium", "high", "critical", "unknown"),
    "uncertainty": ("low", "medium", "high", "unknown"),
    "verification": ("deterministic", "partial", "manual", "unknown"),
}
FAILURES = ("none", "reasoning", "environment", "permission", "auth", "tool", "unknown")
RISK_WORDS = re.compile(r"인증|권한|결제|마이그레이션|저장.*(?:깨|손상|삭제)|동시성|"
                        r"\b(?:auth|permission|payment|migration|concurrency|data loss)\b", re.I)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def atomic_json(path, value, exclusive=False):
    """Atomic visibility within a private run directory (no shared JSONL append)."""
    path = Path(path)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".pending-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if exclusive:
            try:
                os.link(name, path)
            except FileExistsError:
                pass
        else:
            os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def validate_task(task):
    if not isinstance(task, dict):
        raise ValueError("task must be an object")
    for key in ("task_id", "prompt", "model"):
        if not isinstance(task.get(key), str) or not task[key].strip():
            raise ValueError(f"nonempty {key} required")
    for key, choices in SIGNALS.items():
        if task.get(key, "unknown") not in choices:
            raise ValueError(f"invalid {key}")
    for key in ("explicit_effort", "max_effort"):
        if task.get(key) is not None and task[key] not in EFFORTS:
            raise ValueError(f"invalid {key}; never silently coerce a user's setting")
    if task.get("failure", "none") not in FAILURES:
        raise ValueError("invalid failure class")
    if task.get("boundary", "task") not in ("task", "tool", "evidence"):
        raise ValueError("invalid boundary")


def select(task, previous=None, arm="auto"):
    validate_task(task)
    if arm not in ("auto", "medium", "high"):
        raise ValueError("invalid experiment arm")
    signals = {key: task.get(key, "unknown") for key in SIGNALS}
    risk_word = bool(RISK_WORDS.search(task["prompt"]))
    explicit = task.get("explicit_effort")
    reason = "default_medium_hypothesis"
    candidate = "medium"
    if signals["impact"] == "critical" or (
        signals["uncertainty"] == "high" and
        (signals["scope"] == "cross" or signals["impact"] == "high")
    ):
        candidate, reason = "xhigh", "critical_or_uncertain_broad_change"
    elif (risk_word or "unknown" in signals.values() or
          signals["scope"] == "cross" or signals["impact"] == "high" or
          signals["uncertainty"] == "high" or signals["verification"] != "deterministic"):
        candidate, reason = "high", "risk_or_missing_evidence"
    elif signals == dict(scope="single", impact="low", uncertainty="low", verification="deterministic"):
        candidate, reason = "low", "bounded_verified_task"
    chosen = candidate
    boundary = task.get("boundary", "task")
    if previous is not None:
        if (previous["task_id"] != task["task_id"] or previous["model"] != task["model"] or
                previous["arm"] != arm or previous["policy_version"] != POLICY_VERSION):
            raise ValueError("previous decision belongs to a different task/model/arm/policy")
        prior = previous["selected_effort"]
        if boundary == "tool":
            chosen, reason = prior, "hold_until_task_boundary_or_material_evidence"
        elif boundary == "evidence":
            if not task.get("evidence"):
                raise ValueError("material evidence reference required")
            chosen = max((prior, candidate), key=EFFORTS.index)
            reason = "material_evidence_raise_only"
        if task.get("failure", "none") not in ("none", "reasoning"):
            chosen, reason = prior, "diagnose_non_reasoning_failure_without_escalation"
        if previous.get("explicit_effort") and "explicit_effort" not in task:
            explicit = previous["explicit_effort"]
    elif boundary != "task":
        raise ValueError("non-task boundary requires previous decision")
    if arm != "auto":
        chosen, reason = arm, "fixed_experiment_arm"
    if explicit:
        chosen, reason = explicit, "explicit_user_setting"
    ceiling = task.get("max_effort") if "max_effort" in task else (previous.get("max_effort") if previous else None)
    if ceiling and EFFORTS.index(chosen) > EFFORTS.index(ceiling):
        if explicit:
            raise ValueError("explicit effort conflicts with user ceiling")
        chosen, reason = ceiling, "user_ceiling"
    return {
        "schema_version": 1, "policy_version": POLICY_VERSION, "mode": "observe",
        "task_id": task["task_id"], "model": task["model"], "arm": arm,
        "prompt_sha256": digest(task["prompt"]), "task_sha256": digest(task),
        "signals": signals, "risk_word_signal": risk_word,
        "evidence_sha256": digest(task.get("evidence", [])),
        "explicit_effort": explicit, "max_effort": ceiling,
        "candidate_effort": candidate, "selected_effort": chosen, "reason": reason,
        "boundary": boundary, "failure": task.get("failure", "none"),
        "passed_effort": None, "applied_effort": None,
        "application_evidence": "not_executed",
        "parent_effort_changed": False,
        "automatic_retries": 0,
        "classification_rule_tokens": 0,
        "context_assessment_tokens": None,
        "total_usage": None,
    }


def observe(task, root, previous=None, arm="auto", idempotent=False):
    started = time.monotonic()
    record = select(task, previous, arm)
    record["classification_seconds"] = time.monotonic() - started
    record["created_at_unix"] = time.time()
    record["project_root"] = str(Path(root).resolve())
    key = digest([POLICY_VERSION, task, arm]) if idempotent else uuid.uuid4().hex
    run = Path(root) / ".codex" / "reasoning-effort" / key
    run.mkdir(parents=True, mode=0o700, exist_ok=idempotent)
    atomic_json(run / "decision.json", record, exclusive=idempotent)
    return run / "decision.json", read_json(run / "decision.json")


def command(model, effort, root, executable="codex"):
    if effort not in EFFORTS:
        raise ValueError("invalid effort")
    # No extra args escape hatch: keep rules, hooks, auth and user config loaded.
    return [executable, "exec", "--json", "--sandbox", "read-only",
            "-C", str(Path(root).resolve()), "-m", model,
            "-c", f'model_reasoning_effort="{effort}"', "-"]


def summarize_events(path):
    """CLI events are evidence of usage/completion, NOT applied effort."""
    totals = {k: 0 for k in ("input_tokens", "cached_input_tokens", "output_tokens")}
    complete = 0
    missing = False
    failed = False
    with Path(path).open(encoding="utf-8") as stream:
        for line in stream:
            try:
                event = json.loads(line)
            except (ValueError, TypeError):
                missing = True
                continue
            if not isinstance(event, dict):
                missing = True
                continue
            failed |= event.get("type") in ("turn.failed", "error")
            if event.get("type") == "turn.completed":
                complete += 1
                usage = event.get("usage") or {}
                if not isinstance(usage, dict):
                    missing = True
                    continue
                for key in totals:
                    value = usage.get(key)
                    if type(value) is int and value >= 0:
                        totals[key] += value
                    else:
                        missing = True
    return {"completed_turns": complete, "failed_event": failed,
            "execution_usage": totals if complete and not missing and not failed else None,
            "reasoning_tokens": None, "usage_scope": "CLI emitted turn.completed only"}


def execute(task, decision_path, root, approval_ref, executable="codex", timeout=120):
    """One operator-approved read-only run. Marker prevents duplicate dispatch."""
    validate_task(task)
    record = read_json(decision_path)
    if record["project_root"] != str(Path(root).resolve()):
        raise ValueError("decision belongs to a different project root")
    if record["task_sha256"] != digest(task):
        raise ValueError("task changed after observation; observe it again")
    if not approval_ref or not approval_ref.strip():
        raise ValueError("approval reference required; a reference does not grant approval")
    if (task.get("read_only") is not True or task.get("scope") != "single" or
        task.get("impact") != "low" or task.get("uncertainty") != "low" or
        task.get("verification") != "deterministic" or not task.get("evidence") or
        task.get("failure", "none") != "none" or record["risk_word_signal"]):
        raise ValueError("v1 execution requires bounded, evidenced, deterministic read-only work")
    supported = task.get("supported_efforts", [])
    if (not isinstance(supported, list) or any(v not in EFFORTS for v in supported) or
            record["selected_effort"] not in supported):
        raise ValueError("selected effort not in operator-verified model capabilities")
    checks = task.get("required_checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError("all required verifier argv lists must be provided")
    if any(not isinstance(c, list) or not c or any(not isinstance(v, str) or not v for v in c) for c in checks):
        raise ValueError("each verifier must be a nonempty argv list")
    if not 0 < timeout <= 3600:
        raise ValueError("timeout must be in (0, 3600]")
    run = Path(decision_path).parent
    # Exclusive creation is the dispatch claim. Never remove automatically after failure.
    (run / "execution").mkdir(mode=0o700)
    result = dict(record, mode="execute", approval_ref=approval_ref, status="starting",
                  passed_effort=None, application_evidence="not_launched",
                  verification=[], success=False, rework_count=None, user_interventions=None)
    result_path = run / "execution" / "result.json"
    atomic_json(result_path, result)
    start = time.monotonic()
    args = command(record["model"], record["selected_effort"], root, executable)
    result["argv"] = args
    try:
        with (run / "execution" / "events.jsonl").open("w", encoding="utf-8") as out, \
             (run / "execution" / "stderr.txt").open("w", encoding="utf-8") as err:
            child = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=out, stderr=err,
                                     text=True, encoding="utf-8", cwd=root,
                                     start_new_session=os.name != "nt")
            result.update(passed_effort=record["selected_effort"], status="running",
                          application_evidence="process_argv_only; runtime value unconfirmed")
            atomic_json(result_path, result)
            try:
                child.communicate(task["prompt"], timeout=timeout)
            except subprocess.TimeoutExpired:
                if os.name != "nt":
                    os.killpg(child.pid, signal.SIGKILL)
                else:
                    child.kill()
                child.communicate()
                result["status"] = "timeout"
            result["exit_code"] = child.returncode
        result.update(summarize_events(run / "execution" / "events.jsonl"))
        if result["status"] != "timeout":
            result["status"] = "completed" if child.returncode == 0 else "executor_failed"
        if child.returncode == 0 and result["completed_turns"] and not result["failed_event"]:
            for check in checks:
                check = [str((run / "execution" / "events.jsonl").resolve()) if v == "{events}" else v for v in check]
                check_start = time.monotonic()
                try:
                    checked = subprocess.run(check, cwd=root, capture_output=True, timeout=timeout)
                    verdict = {"argv": check, "exit_code": checked.returncode,
                               "stdout_sha256": hashlib.sha256(checked.stdout).hexdigest(),
                               "stderr_sha256": hashlib.sha256(checked.stderr).hexdigest()}
                except (OSError, subprocess.TimeoutExpired) as exc:
                    verdict = {"argv": check, "exit_code": None, "error_type": type(exc).__name__}
                verdict["seconds"] = time.monotonic() - check_start
                result["verification"].append(verdict)
            result["success"] = all(v["exit_code"] == 0 for v in result["verification"])
        if not result["success"]:
            result["next_action"] = "classify_failure_and_reassess; no automatic effort escalation or retry"
    except OSError as exc:
        result.update(status="environment_error", error_type=type(exc).__name__)
    finally:
        result["execution_and_verification_seconds"] = time.monotonic() - start
        # Assessment/context, parent/subagents, and external verifier model calls are unknown.
        # Never label the CLI subtotal or output tokens as total cost.
        atomic_json(result_path, result)
    return result_path, result


def hook():
    """Opt-in automatic observation. Never launch an executor from a prompt hook."""
    event = json.load(sys.stdin)
    if not isinstance(event, dict):
        raise ValueError("hook event must be an object")
    if event.get("hook_event_name") != "UserPromptSubmit":
        return
    root = Path(event["cwd"])
    policy_path = root / ".codex" / "reasoning-effort.json"
    if not policy_path.exists():
        return
    policy = read_json(policy_path)
    if not isinstance(policy, dict):
        raise ValueError("observation policy must be an object")
    if policy.get("mode") != "observe":
        return
    task = {"task_id": event["session_id"] + ":" + event["turn_id"],
            "prompt": event["prompt"], "model": event["model"]}
    path, record = observe(task, root, idempotent=True)
    message = (f"Effort observation: selected={record['selected_effort']}; passed=null; applied=null. "
               "Parent runtime unchanged. UI effort is not exposed by this hook; preserve explicit user settings. "
               f"Decision: {path}. After scope inspection, use {Path(__file__).resolve()} observe "
               "with evidence at a task boundary; do not reclassify after every tool call. "
               "No execution authorization is granted; keep every required safety and verification gate.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                             "additionalContext": message}}))


def main():
    force_utf8()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("hook")
    obs = sub.add_parser("observe")
    obs.add_argument("--task", required=True)
    obs.add_argument("--root", default=".")
    obs.add_argument("--previous")
    obs.add_argument("--arm", choices=("auto", "medium", "high"), default="auto")
    run = sub.add_parser("run")
    run.add_argument("--task", required=True)
    run.add_argument("--decision", required=True)
    run.add_argument("--root", default=".")
    run.add_argument("--approval-ref", required=True)
    run.add_argument("--execute", action="store_true", help="otherwise only print planned argv")
    run.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    try:
        if args.mode == "hook":
            hook()
            return 0
        task = read_json(args.task)
        if args.mode == "observe":
            path, result = observe(task, args.root, read_json(args.previous) if args.previous else None, args.arm)
        elif args.execute:
            path, result = execute(task, args.decision, args.root, args.approval_ref, timeout=args.timeout)
        else:
            record = read_json(args.decision)
            if record["task_sha256"] != digest(task):
                raise ValueError("task changed after observation")
            print(json.dumps({"planned_argv": command(record["model"], record["selected_effort"], args.root),
                              "passed_effort": None, "applied_effort": None}))
            return 0
        print(json.dumps({"record": str(path.resolve()), **result}, ensure_ascii=False))
        return 0 if args.mode == "observe" or result["success"] else 1
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"reasoning-effort: {type(exc).__name__}: {exc}", file=sys.stderr)
        # Advisory hook must not block ordinary user input on logger failure.
        return 0 if args.mode == "hook" else 2


if __name__ == "__main__":
    sys.exit(main())
