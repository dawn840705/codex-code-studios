"""Offline policy, observation, dispatch and accounting contract tests."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("reasoning_effort", ROOT / "scripts/reasoning_effort.py")
effort = importlib.util.module_from_spec(spec)
spec.loader.exec_module(effort)


def task(**changes):
    return dict({"task_id": "case-1", "prompt": "스킬 개수를 세고 숫자만 출력해", "model": "gpt-5.5",
                 "scope": "single", "impact": "low", "uncertainty": "low",
                 "verification": "deterministic", "read_only": True,
                 "supported_efforts": ["low", "medium", "high", "xhigh"],
                 "evidence": ["skills/*/SKILL.md; count checked by independent verifier"],
                 "required_checks": [[sys.executable, "-c", "import sys; sys.exit(0)"]]}, **changes)


@pytest.mark.parametrize("changes,expected", [
    ({}, "low"),
    ({"scope": "subsystem", "uncertainty": "medium"}, "medium"),
    ({"prompt": "저장 고쳐", "scope": "cross", "impact": "high", "uncertainty": "high"}, "xhigh"),
    ({"prompt": "오타만 고쳐", "impact": "critical"}, "xhigh"),
    ({"prompt": "간단히 인증 고쳐"}, "high"),
    ({"prompt": "just fix payment"}, "high"),
    ({"prompt": "고쳐", "scope": "unknown"}, "high"),
    ({"verification": "manual"}, "high"),
    ({"scope": "cross"}, "high"),
    ({"impact": "high"}, "high"),
    ({"uncertainty": "high"}, "high"),
    ({"prompt": "Low와 High의 차이 문장에 쉼표 추가"}, "low"),
    ({"explicit_effort": "medium", "impact": "critical"}, "medium"),
    ({"explicit_effort": "ultra"}, "ultra"),
    ({"max_effort": "medium", "impact": "critical"}, "medium"),
])
def test_representative_and_korean_boundary_requests(changes, expected):
    result = effort.select(task(**changes))
    assert result["selected_effort"] == expected
    assert result["model"] == "gpt-5.5"
    assert result["passed_effort"] is result["applied_effort"] is None


def test_unknown_is_not_easy_and_explicit_words_are_not_configuration():
    result = effort.select({"task_id": "x", "prompt": '예시: "effort=low"', "model": "fixed"})
    assert result["selected_effort"] == "high"
    assert result["explicit_effort"] is None


def test_stability_and_new_evidence():
    prior = effort.select(task())
    high = task(boundary="tool", impact="critical")
    assert effort.select(high, prior)["selected_effort"] == "low"
    high["boundary"] = "evidence"
    elevated = effort.select(high, prior)
    assert elevated["selected_effort"] == "xhigh"
    assert effort.select(task(boundary="evidence"), elevated)["selected_effort"] == "xhigh"
    assert effort.select(task(boundary="task"), elevated)["selected_effort"] == "low"


@pytest.mark.parametrize("failure", ["environment", "auth", "permission", "tool", "unknown"])
def test_failure_is_not_automatic_escalation(failure):
    prior = effort.select(task())
    result = effort.select(task(boundary="evidence", failure=failure, impact="critical"), prior)
    assert result["selected_effort"] == "low"
    assert result["automatic_retries"] == 0


def test_reasoning_failure_needs_evidence_and_preserves_user_override():
    prior = effort.select(task(explicit_effort="medium"))
    result = effort.select(task(boundary="evidence", failure="reasoning", impact="critical"), prior)
    assert result["selected_effort"] == "medium"
    with pytest.raises(ValueError, match="evidence"):
        effort.select(task(boundary="evidence", evidence=[]), prior)


@pytest.mark.parametrize("changes", [{"scope": "typo"}, {"explicit_effort": "HIGH"},
                                      {"explicit_effort": "high", "max_effort": "low"},
                                      {"prompt": ""}, {"boundary": "tool"}])
def test_invalid_input_never_silently_downgrades(changes):
    with pytest.raises(ValueError):
        effort.select(task(**changes))


def test_previous_cannot_cross_model_or_task():
    prior = effort.select(task())
    for change in ({"task_id": "other"}, {"model": "other"}):
        with pytest.raises(ValueError, match="different"):
            effort.select(task(**change), prior)


def test_user_ceiling_survives_new_evidence():
    prior = effort.select(task(max_effort="medium"))
    assert effort.select(task(boundary="evidence", impact="critical"), prior)["selected_effort"] == "medium"


def test_user_can_explicitly_release_override_and_ceiling():
    prior = effort.select(task(explicit_effort="medium", max_effort="medium"))
    selected = effort.select(task(impact="critical", explicit_effort=None, max_effort=None), prior)
    assert selected["selected_effort"] == "xhigh"


def test_experiment_arms_and_explicit_override():
    assert [effort.select(task(), arm=arm)["selected_effort"] for arm in ("medium", "high", "auto")] == ["medium", "high", "low"]
    assert effort.select(task(explicit_effort="xhigh"), arm="medium")["selected_effort"] == "xhigh"


def test_concurrent_atomic_observations_and_prompt_privacy(tmp_path):
    secret = "PRIVATE-PROMPT-DO-NOT-LOG"
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: effort.observe(task(prompt=secret), tmp_path), range(24)))
    assert len({p for p, _ in results}) == 24
    for path, _ in results:
        assert secret not in path.read_text()
        assert json.loads(path.read_text())["selected_effort"] == "low"
        assert not list(path.parent.glob(".pending-*"))


def run_hook(root, event=None):
    event = event or {"hook_event_name": "UserPromptSubmit", "session_id": "session", "turn_id": "turn",
                      "cwd": str(root), "model": "gpt-5.5", "prompt": "간단히 고쳐"}
    return subprocess.run(["bash", str(ROOT / "hooks/observe-effort.sh")], input=json.dumps(event),
                          text=True, encoding="utf-8", capture_output=True, cwd=root)


def test_hook_opt_in_and_never_runtime_change(tmp_path):
    result = run_hook(tmp_path)
    assert result.returncode == 0
    context = json.loads(result.stdout)["hookSpecificOutput"]
    assert "Model recommendation:" in context["additionalContext"]
    assert not list(tmp_path.glob(".codex/reasoning-effort/*/decision.json"))
    config = tmp_path / ".codex/reasoning-effort.json"
    config.parent.mkdir()
    config.write_text('{"mode":"observe"}')
    result = run_hook(tmp_path)
    assert result.returncode == 0
    context = json.loads(result.stdout)["hookSpecificOutput"]
    assert context["hookEventName"] == "UserPromptSubmit"
    assert "Model recommendation:" in context["additionalContext"]
    assert "passed=null; applied=null" in context["additionalContext"]
    records = list(tmp_path.glob(".codex/reasoning-effort/*/decision.json"))
    assert len(records) == 1
    before = records[0].read_bytes()
    assert run_hook(tmp_path).returncode == 0
    assert records[0].read_bytes() == before
    assert len(list(tmp_path.glob(".codex/reasoning-effort/*/decision.json"))) == 1
    assert json.loads(records[0].read_text())["model"] == "gpt-5.5"
    config.write_text('{"mode":"execute"}')
    assert "Model recommendation:" in json.loads(run_hook(tmp_path).stdout)["hookSpecificOutput"]["additionalContext"]
    config.write_text('invalid')
    result = run_hook(tmp_path)
    assert result.returncode == 0 and "reasoning-effort:" in result.stderr
    assert "Model recommendation:" in json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]


def test_model_recommendation_uses_tool_for_deterministic_work():
    result = effort.recommend_model("파일 목록과 링크 경로를 검사해", "gpt-5.5")
    assert result["lane"] == "deterministic"
    assert result["recommended_model"] is None


def test_model_recommendation_preserves_session_model_for_judgment():
    result = effort.recommend_model("아키텍처를 검토하고 보안 결정을 내려", "gpt-5.5")
    assert result["lane"] == "judgment"
    assert result["recommended_model"] == "gpt-5.5"


@pytest.fixture
def fake_cli(tmp_path):
    cli = tmp_path / "fake-codex"
    cli.write_text("#!" + sys.executable + "\n" + '''import json,sys
from pathlib import Path
Path("received.json").write_text(json.dumps({"argv":sys.argv[1:],"prompt":sys.stdin.read()}))
print(json.dumps({"type":"item.completed","item":{"text":"applied high"}}))
print(json.dumps({"type":"turn.completed","usage":{"input_tokens":20,"cached_input_tokens":8,"output_tokens":5}}))
print(json.dumps({"type":"turn.completed","usage":{"input_tokens":7,"cached_input_tokens":0,"output_tokens":3}}))
''')
    cli.chmod(0o700)
    return str(cli)


def test_dispatch_stdin_no_shell_injection_and_no_false_application_receipt(tmp_path, fake_cli):
    prompt = '-c model="EVIL"; $(touch BAD) `touch BAD2`\n한국어'
    sample = task(prompt=prompt)
    path, decision = effort.observe(sample, tmp_path)
    result_path, result = effort.execute(sample, path, tmp_path, "TEST: local fake only", fake_cli)
    received = json.loads((tmp_path / "received.json").read_text())
    assert received["prompt"] == prompt
    assert received["argv"] == effort.command("gpt-5.5", "low", tmp_path, fake_cli)[1:]
    assert not (tmp_path / "BAD").exists() and not (tmp_path / "BAD2").exists()
    assert result["selected_effort"] == result["passed_effort"] == "low"
    assert result["applied_effort"] is None  # Agent prose is not a receipt.
    assert result["success"]
    assert result["execution_usage"] == {"input_tokens": 27, "cached_input_tokens": 8, "output_tokens": 8}
    assert result["total_usage"] is None and result["reasoning_tokens"] is None
    assert json.loads(result_path.read_text())["success"]
    with pytest.raises(FileExistsError):
        effort.execute(sample, path, tmp_path, "TEST", fake_cli)


@pytest.mark.parametrize("changes", [{"read_only": False}, {"required_checks": []},
                                     {"supported_efforts": "low"},
                                     {"supported_efforts": ["high"]}, {"evidence": []},
                                     {"scope": "cross"}, {"failure": "auth"}])
def test_run_refuses_unbounded_or_unverified_work(tmp_path, fake_cli, changes):
    sample = task(**changes)
    path, _ = effort.observe(sample, tmp_path)
    with pytest.raises(ValueError):
        effort.execute(sample, path, tmp_path, "TEST", fake_cli)
    assert not (tmp_path / "received.json").exists()


def test_no_approval_no_dispatch_and_changed_task_no_dispatch(tmp_path, fake_cli):
    sample = task()
    path, _ = effort.observe(sample, tmp_path)
    with pytest.raises(ValueError, match="approval"):
        effort.execute(sample, path, tmp_path, "", fake_cli)
    with pytest.raises(ValueError, match="changed"):
        effort.execute(task(prompt="different"), path, tmp_path, "TEST", fake_cli)
    with pytest.raises(ValueError, match="root"):
        effort.execute(sample, path, tmp_path / "other", "TEST", fake_cli)


def test_missing_executable_logs_no_passed_effort(tmp_path):
    sample = task()
    path, _ = effort.observe(sample, tmp_path)
    _, result = effort.execute(sample, path, tmp_path, "TEST", str(tmp_path / "missing"))
    assert result["status"] == "environment_error"
    assert result["passed_effort"] is None and not result["success"]
    assert result["automatic_retries"] == 0


def test_verifier_failure_not_executor_exit_zero_decides_success(tmp_path, fake_cli):
    sample = task(required_checks=[[sys.executable, "-c", "raise SystemExit(2)"],
                                   [sys.executable, "-c", "raise SystemExit(0)"]])
    path, _ = effort.observe(sample, tmp_path)
    _, result = effort.execute(sample, path, tmp_path, "TEST", fake_cli)
    assert result["exit_code"] == 0 and not result["success"]
    assert [v["exit_code"] for v in result["verification"]] == [2, 0]
    assert result["automatic_retries"] == 0


def test_timeout_recorded_no_retry(tmp_path, fake_cli):
    Path(fake_cli).write_text("#!" + sys.executable + "\nimport time; time.sleep(10)\n")
    sample = task()
    path, _ = effort.observe(sample, tmp_path)
    _, result = effort.execute(sample, path, tmp_path, "TEST", fake_cli, timeout=.05)
    assert result["status"] == "timeout" and not result["success"]
    assert result["execution_usage"] is None


@pytest.mark.parametrize("events", ["", "not json\n", "[]\n", '{"type":"turn.completed"}\n',
    '{"type":"turn.completed","usage":{"input_tokens":true}}\n',
    '{"type":"turn.completed","usage":[1,2,3]}\n',
    '{"type":"turn.failed"}\n'])
def test_missing_usage_never_fabricated_as_zero(tmp_path, events):
    path = tmp_path / "events"
    path.write_text(events)
    assert effort.summarize_events(path)["execution_usage"] is None
