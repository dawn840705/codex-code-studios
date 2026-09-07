"""Bounded three-arm effort experiments; prepare is offline, run is explicit.

This is an evaluation harness, not a plugin entry point. No global configuration
changes, automatic retries, resets, or model substitution.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import platform
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import sys
import tarfile
import time

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))
import reasoning_effort as effort

PROMPT = ("이 저장소의 skills/*/SKILL.md에 해당하는 일반 파일 개수를 실제로 확인하고 "
          "최종 답변은 정수 하나만 출력해. 읽기 전용 조사이며 파일 수정, 네트워크 요청, "
          "다른 프로젝트 접근, 서브에이전트 위임은 하지 마. 이 요청에 스킬 실행은 필요하지 않아.")
CASES = ("count-skills", "manifest-version", "hook-events")
CONSTRAINT = " 파일 수정, 네트워크 요청, 다른 프로젝트 접근, 서브에이전트 위임 없이 읽기만 해."


def environment():
    """Local evidence only; never read auth files or expose configuration contents."""
    config = Path.home() / ".codex/config.toml"
    cli = shutil.which("codex")
    version = subprocess.run([cli, "--version"], check=True, capture_output=True,
                             text=True, encoding="utf-8").stdout.strip() if cli else None
    return {"python": sys.version, "platform": platform.platform(), "cli": cli,
            "cli_version": version,
            "user_config_sha256": hashlib.sha256(config.read_bytes()).hexdigest() if config.exists() else None,
            "uncontrolled": ["server load", "model alias deployment", "shared cache", "other host processes",
                             "installed plugin cache and host-managed context"]}


def case_definitions(snapshot):
    definitions = {"count-skills": {"prompt": PROMPT, "format": "text",
                   "expected": str(sum(p.is_file() for p in snapshot.glob("skills/*/SKILL.md")))}}
    manifest = snapshot / ".codex-plugin/plugin.json"
    if manifest.exists():
        definitions["manifest-version"] = {"prompt": ".codex-plugin/plugin.json의 version 값을 읽고 그 문자열만 출력해." + CONSTRAINT,
                                            "format": "text", "expected": effort.read_json(manifest)["version"]}
    hooks = snapshot / "hooks/hooks.json"
    if hooks.exists():
        definitions["hook-events"] = {"prompt": "hooks/hooks.json의 hooks 객체에 있는 이벤트 이름을 정렬된 JSON 배열 하나로 출력해." + CONSTRAINT,
                                      "format": "json", "expected": json.dumps(sorted(effort.read_json(hooks)["hooks"]))}
    return definitions


def schedule(cases, repetitions, seed):
    if (type(repetitions) is not int or not 1 <= repetitions <= 3 or not cases or
            len(set(cases)) != len(cases) or any(c not in CASES for c in cases)):
        raise ValueError("choose unique supported cases and 1-3 repetitions (at most 27 dispatches)")
    rng = random.Random(seed)
    jobs = []
    for case in cases:
        order = ["medium", "high", "auto"]
        rng.shuffle(order)
        for repetition in range(repetitions):
            # Each arm occupies every position once in a three-repeat block.
            rotated = order[repetition:] + order[:repetition]
            jobs.extend({"case": case, "repetition": repetition + 1, "arm": arm} for arm in rotated)
    return jobs


def tree_hash(root):
    """Account for all source files, excluding only Git and our private logs."""
    values = []
    for path in sorted(Path(root).rglob("*")):
        relative = path.relative_to(root)
        if relative.parts[0] == ".git" or relative.parts[:2] == (".codex", "reasoning-effort"):
            continue
        if path.is_symlink():
            raise ValueError("pilot snapshots must not contain symbolic links")
        if path.is_file():
            values.append((relative.as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()))
    return effort.digest(values)


def implementation_hash():
    return effort.digest([hashlib.sha256(p.read_bytes()).hexdigest() for p in
                         (Path(__file__), PLUGIN / "scripts/reasoning_effort.py")])


def prepare(source, output, model, supported, approval_ref, seed=20260907,
            cases=("count-skills",), repetitions=1):
    source, output = Path(source).resolve(), Path(output).resolve()
    jobs = schedule(cases, repetitions, seed)
    if not approval_ref.strip():
        raise ValueError("reference the actual user authorization")
    if not {"low", "medium", "high"}.issubset(supported):
        raise ValueError("verify low/medium/high support for the fixed model first")
    output.mkdir(mode=0o700)  # Exclusive: never overwrite an existing batch.
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=source, check=True,
                            capture_output=True, text=True, encoding="utf-8").stdout.strip()
    archive = subprocess.run(["git", "archive", "--format=tar", commit], cwd=source,
                             check=True, capture_output=True).stdout
    snapshot = output / "snapshot"
    snapshot.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
        tar.extractall(snapshot, filter="data")
    definitions = case_definitions(snapshot)
    if any(c not in definitions for c in cases):
        raise ValueError("snapshot is missing a requested case's source files")
    expected = definitions["count-skills"]["expected"]
    if expected == "0":
        raise ValueError("snapshot has no skills; wrong experiment repository")
    order = [j["arm"] for j in jobs]
    manifest = {
        "schema_version": 2, "kind": "live_pilot_plan", "model": model,
        "supported_efforts": supported, "initial_commit": commit,
        "initial_tree_sha256": tree_hash(snapshot), "implementation_sha256": implementation_hash(),
        "prompt": PROMPT, "prompt_sha256": effort.digest(PROMPT),
        "expected": expected, "order": order, "seed": seed,
        "task_id": "count-skills", "repetitions_per_arm": repetitions,
        "cases": list(cases), "definitions": {c: definitions[c] for c in cases}, "jobs": jobs,
        "environment": environment(),
        "maximum_dispatches": len(jobs), "timeout_seconds_per_dispatch": 60,
        "minimum_remaining_percent_for_expanded_batch": 10,
        "automatic_retries": 0, "approval_reference": approval_ref,
        "scope": "committed snapshot; excludes current uncommitted changes",
        "acceptance": "exact independent answers and unchanged source; no quality-gain claim from mechanical tasks",
        "classification_accounting": "offline rule time measured; parent assessment/setup usage unknown",
    }
    effort.atomic_json(output / "manifest.json", manifest)
    return manifest


def verify(events, expected, output_format="text"):
    """Grade the final agent message, never progress text or command output."""
    final = None
    completed = False
    for line in Path(events).read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        if event.get("type") in ("error", "turn.failed"):
            return False
        completed |= event.get("type") == "turn.completed"
        item = event.get("item") or {}
        if event.get("type") == "item.completed" and item.get("type") == "agent_message":
            final = item.get("text", "").strip()
    if not completed or final is None:
        return False
    if output_format == "json":
        try:
            return json.loads(final) == json.loads(expected)
        except ValueError:
            return False
    return final == expected


def run(output, executable="codex", remaining_percent=None, standalone=False):
    output = Path(output).resolve()
    plan = effort.read_json(output / "manifest.json")
    if plan["implementation_sha256"] != implementation_hash():
        raise ValueError("runner or verifier changed after preparation")
    if tree_hash(output / "snapshot") != plan["initial_tree_sha256"]:
        raise ValueError("snapshot changed after preparation")
    expected_definitions = case_definitions(output / "snapshot")
    if plan["definitions"] != {c: expected_definitions[c] for c in plan["cases"]}:
        raise ValueError("task or independent expected answer changed")
    jobs = schedule(plan["cases"], plan["repetitions_per_arm"], plan["seed"])
    if plan["jobs"] != jobs or plan["maximum_dispatches"] != len(jobs):
        raise ValueError("schedule or dispatch cap changed")
    if len(jobs) > 3 and (type(remaining_percent) not in (int, float) or
                          not 10 <= remaining_percent <= 100):
        raise ValueError("expanded pilot requires a freshly checked remaining account percentage >=10; no reset is authorized")
    if not standalone:
        raise ValueError("finish regression tests first and explicitly attest standalone execution")
    if environment() != plan["environment"]:
        raise ValueError("local environment changed after preparation")
    if plan["timeout_seconds_per_dispatch"] != 60:
        raise ValueError("this pilot has a fixed 60 second dispatch timeout")
    (output / "dispatch-claim").mkdir()  # No resuming/retrying an ambiguous batch.
    summary = {"measurement_kind": "model_run", "status": "running", "runs": [],
               "model": plan["model"], "initial_commit": plan["initial_commit"],
               "initial_tree_sha256": plan["initial_tree_sha256"], "total_usage": None,
               "cost_savings_claim": None, "parent_and_setup_usage": None,
               "standalone_operator_attestation": standalone, "remaining_percent_at_start": remaining_percent}
    effort.atomic_json(output / "summary.json", summary)
    try:
        for index, job in enumerate(jobs):
            if environment() != plan["environment"]:
                summary["status"] = "stopped_on_environment_change"
                break
            arm = job["arm"]
            definition = plan["definitions"][job["case"]]
            root = output / f"run-{index + 1}-{arm}"
            shutil.copytree(output / "snapshot", root)
            subprocess.run(["git", "init", "--quiet", str(root)], check=True, capture_output=True)
            if tree_hash(root) != plan["initial_tree_sha256"]:
                raise ValueError("unequal initial source state")
            task = {"task_id": job["case"], "prompt": definition["prompt"], "model": plan["model"],
                    "scope": "single", "impact": "low", "uncertainty": "low",
                    "verification": "deterministic", "read_only": True,
                    "evidence": ["frozen git archive; independent directory enumeration and exact final-output check"],
                    "supported_efforts": plan["supported_efforts"],
                    "required_checks": [[sys.executable, str(Path(__file__).resolve()), "verify",
                                         "--events", "{events}", "--expected", definition["expected"],
                                         "--format", definition["format"]]]}
            print(json.dumps({"status": "starting", "arm": arm, "model": plan["model"]}), flush=True)
            started = time.monotonic()
            decision, observation = effort.observe(task, root, arm=arm)
            result_path, result = effort.execute(task, decision, root, plan["approval_reference"],
                                                 executable=executable, timeout=60)
            source_unchanged = tree_hash(root) == plan["initial_tree_sha256"]
            row = {**job, "model": plan["model"], "selected_effort": result["selected_effort"],
                   "passed_effort": result["passed_effort"], "applied_effort": result["applied_effort"],
                   "success": result["success"] and source_unchanged, "source_unchanged": source_unchanged,
                   "wall_seconds": time.monotonic() - started, "execution_usage": result.get("execution_usage"),
                   "classification_seconds": observation["classification_seconds"],
                   "classification_rule_tokens": 0, "parent_assessment_tokens": None,
                   "total_usage": None, "reasoning_tokens": result.get("reasoning_tokens"),
                   "status": result["status"], "execution_record": str(result_path),
                   "retries": 0, "rework_count": 0, "user_interventions_during_dispatch": 0}
            summary["runs"].append(row)
            effort.atomic_json(output / "summary.json", summary)
            print(json.dumps(row), flush=True)
            if not source_unchanged or result["status"] != "completed":
                summary["status"] = "stopped_on_executor_or_state_failure"
                break
        else:
            summary["status"] = "completed"
    finally:
        if summary["status"] == "running":
            summary["status"] = "interrupted_or_exception"
        summary["by_case_and_arm"] = aggregate(plan, summary["runs"])
        effort.atomic_json(output / "summary.json", summary)
    return summary


def aggregate(plan, rows):
    """Include failures; missing subtotals stay unknown. No weighted cost model."""
    groups = []
    for case in plan["cases"]:
        for arm in ("medium", "high", "auto"):
            batch = [r for r in rows if r["case"] == case and r["arm"] == arm]
            times = [r["wall_seconds"] for r in batch]
            known = bool(batch) and all(r.get("execution_usage") is not None for r in batch)
            groups.append({"case": case, "arm": arm, "planned": plan["repetitions_per_arm"],
                           "attempted": len(batch), "successes": sum(r["success"] for r in batch),
                           "success_rate": sum(r["success"] for r in batch) / len(batch) if batch else None,
                           "median_seconds": statistics.median(times) if times else None,
                           "execution_input_plus_output_tokens": sum(r["execution_usage"]["input_tokens"] +
                               r["execution_usage"]["output_tokens"] for r in batch) if known else None,
                           "total_usage": None, "cost_savings_claim": None})
    return groups


def main():
    effort.force_utf8()
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("prepare")
    p.add_argument("--source", default=str(PLUGIN))
    p.add_argument("--output", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--supported", nargs="+", required=True)
    p.add_argument("--approval-ref", required=True)
    p.add_argument("--cases", nargs="+", choices=CASES, default=["count-skills"])
    p.add_argument("--repetitions", type=int, default=1)
    p = commands.add_parser("run")
    p.add_argument("--output", required=True)
    p.add_argument("--remaining-percent", type=float)
    p.add_argument("--standalone", action="store_true")
    p = commands.add_parser("verify")
    p.add_argument("--events", required=True)
    p.add_argument("--expected", required=True)
    p.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    if args.command == "prepare":
        print(json.dumps(prepare(args.source, args.output, args.model, args.supported, args.approval_ref,
                                 cases=args.cases, repetitions=args.repetitions)))
    elif args.command == "run":
        result = run(args.output, remaining_percent=args.remaining_percent, standalone=args.standalone)
        return 0 if result["status"] == "completed" and all(r["success"] for r in result["runs"]) else 1
    else:
        return 0 if verify(args.events, args.expected, args.format) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
