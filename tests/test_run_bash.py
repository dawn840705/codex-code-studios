import importlib.util
import ntpath
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from unittest.mock import Mock

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "hooks" / "run-bash.py"
spec = importlib.util.spec_from_file_location("run_bash", RUNNER)
run_bash = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_bash)


def test_windows_resolves_git_bash_instead_of_wsl_launcher():
    git = r"C:\Program Files\Git\cmd\git.exe"
    expected = r"C:\Program Files\Git\bin\bash.exe"

    def which(name):
        return git if name == "git" else r"C:\Windows\System32\bash.exe"

    assert run_bash.find_bash(
        platform="nt",
        which=which,
        is_file=lambda path: ntpath.normcase(path) == ntpath.normcase(expected),
        environ={},
    ) == expected


def test_windows_does_not_fall_back_to_wsl_launcher():
    assert run_bash.find_bash(
        platform="nt",
        which=lambda name: r"C:\Windows\System32\bash.exe" if name == "bash" else None,
        is_file=lambda path: False,
        environ={},
    ) is None


def test_runner_forwards_output_and_exit_code():
    success = subprocess.run(
        [sys.executable, RUNNER, "-c", "printf okay"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    failure = subprocess.run([sys.executable, RUNNER, "-c", "exit 7"])
    assert success.returncode == 0 and success.stdout == "okay"
    assert failure.returncode == 7


def test_runner_closes_private_stdin_and_preserves_payload():
    payload = '{"text":"한글\\nfeedback"}'
    result = subprocess.run([sys.executable, RUNNER, "-c", "cat"],
                            input=payload, capture_output=True, text=True,
                            encoding="utf-8", timeout=11)
    assert result.returncode == 0
    assert result.stdout == payload


def test_open_input_pipe_times_out_before_starting_bash(tmp_path):
    marker = tmp_path / "should-not-exist"
    process = subprocess.Popen(
        [sys.executable, RUNNER, "--stdin-timeout", "0.1", "--timeout", "0.5",
         "--", "-c", 'touch "$1"', "hook", str(marker)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        assert process.wait(timeout=3) == 124
        assert b"input did not reach EOF" in process.stderr.read()
        assert not marker.exists()
    finally:
        process.stdin.close()
        if process.poll() is None:
            process.kill()
        process.wait()


def test_timeout_terminates_descendants(tmp_path):
    pidfile = tmp_path / "child.pid"
    result = subprocess.run(
        [sys.executable, RUNNER, "--timeout", "5", "--", "-c",
         'sleep 30 & echo $! > "$1"; wait', "hook", pidfile.as_posix()],
        input=b"", capture_output=True, timeout=9)
    assert result.returncode == 124
    assert b"validation incomplete" in result.stderr
    assert pidfile.exists(), "the descendant must actually have started"
    # Git Bash's $! is a POSIX PID, not a Windows PID. Native Windows tree
    # cleanup is checked separately below; Linux exposes descendant liveness.
    if sys.platform.startswith("linux"):
        pid = int(pidfile.read_text())
        status = Path(f"/proc/{pid}/status")
        deadline = time.monotonic() + 1
        while status.exists() and "State:\tZ" not in status.read_text():
            if time.monotonic() >= deadline:
                os.kill(pid, signal.SIGKILL)
                pytest.fail("hook descendant survived timeout")
            time.sleep(0.01)


def test_windows_cleanup_targets_only_own_process_tree(monkeypatch):
    process = Mock(pid=12345)
    call = Mock()
    monkeypatch.setattr(run_bash.os, "name", "nt")
    monkeypatch.setattr(run_bash.subprocess, "run", call)
    run_bash.terminate_tree(process)
    assert call.call_args.args[0] == ["taskkill", "/PID", "12345", "/T", "/F"]
    assert call.call_args.kwargs["timeout"] == 1
    process.wait.assert_called_once_with(timeout=1)


@pytest.mark.parametrize("tool_input", [
    {"file_path": "docs/readme.md"},
    {"command": "*** Begin Patch\n*** Update File: docs/readme.md\n*** End Patch"},
])
def test_unrelated_edits_do_not_resolve_or_launch_bash(monkeypatch, tool_input):
    monkeypatch.setattr(run_bash, "read_input", lambda timeout: json.dumps(
        {"tool_input": tool_input}).encode())
    monkeypatch.setattr(run_bash, "find_bash", lambda: pytest.fail("Bash started"))
    assert run_bash.main(["validate-skill-change.sh"]) == 0
    assert run_bash.main(["unity-meta-check.sh"]) == 0
    assert run_bash.main(["unity-animator-string-lint.sh"]) == 0


def test_relevant_multi_file_and_move_paths_are_not_skipped(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "Assets").mkdir()
    (tmp_path / "ProjectSettings").mkdir()
    payload = json.dumps({"tool_input": {"command":
        "*** Update File: docs/readme.md\n*** Move to: skills/example/SKILL.md\n"
        "*** Add File: Assets/Player.cs\n*** Delete File: Assets/Card.asset"}}).encode()
    for name in ("validate-skill-change.sh", "unity-meta-check.sh",
                 "unity-animator-string-lint.sh", "validate-assets.sh"):
        assert not run_bash.irrelevant_edit(name, payload)
    assert not run_bash.irrelevant_edit("validate-assets.sh", json.dumps(
        {"tool_input": {"file_path": "custom-root/BAD-NAME.png"}}).encode())
    assert not run_bash.irrelevant_edit("validate-assets.sh", b"broken json")
    assert run_bash.irrelevant_edit("validate-assets.sh", b" \n")


def test_explicit_timeout_invocation_passes_input_to_hook(tmp_path):
    script = tmp_path / "read-input.sh"
    script.write_text("#!/usr/bin/env bash\ncat\n", encoding="utf-8")
    payload = b'{"hook_event_name":"SessionStart"}'
    result = subprocess.run([sys.executable, RUNNER, "--timeout", "7", str(script)],
                            input=payload, capture_output=True, timeout=11)
    assert result.returncode == 0
    assert result.stdout == payload


def test_every_registered_shell_hook_has_cleanup_margin():
    manifest = json.loads((ROOT / "hooks/hooks.json").read_text())
    hooks = [hook for groups in manifest["hooks"].values() for group in groups
             for hook in group["hooks"] if "run-bash.py" in hook["command"]]
    assert hooks
    for hook in hooks:
        budget = float(hook["command"].split("--timeout ", 1)[1].split()[0])
        assert budget > 0
        assert hook["timeout"] - budget >= 3


def test_combined_edit_hook_keeps_all_feedback_and_json_failure(tmp_path):
    (tmp_path / "Assets").mkdir()
    (tmp_path / "ProjectSettings").mkdir()
    (tmp_path / "Assets/Player.cs").write_text('animator.SetBool("Moving", true);')
    payload = json.dumps({"tool_input": {"command":
        "*** Update File: Assets/Player.cs\n*** Update File: skills/example/SKILL.md"}})
    result = subprocess.run([sys.executable, ROOT / "hooks/post-edit.py"],
                            input=payload, text=True, encoding="utf-8",
                            capture_output=True, cwd=tmp_path, timeout=31)
    assert result.returncode == 0, result.stderr
    context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "skill modified" in context
    assert "Missing Unity sidecar" in context
    assert "Animator string access" in context
    (tmp_path / "Assets/Broken.json").write_text("{broken")
    result = subprocess.run([sys.executable, ROOT / "hooks/post-edit.py"],
                            input=json.dumps({"tool_input": {"file_path": "Assets/Broken.json"}}),
                            text=True, encoding="utf-8", capture_output=True, cwd=tmp_path, timeout=31)
    assert result.returncode == 2
    assert "not valid JSON" in result.stderr


def test_edit_manifest_has_one_handler_and_no_automatic_agent_logs():
    hooks = json.loads((ROOT / "hooks/hooks.json").read_text())["hooks"]
    assert len(hooks["PostToolUse"][0]["hooks"]) == 1
    assert "post-edit.py" in hooks["PostToolUse"][0]["hooks"][0]["command"]
    assert not {"SessionEnd", "SubagentStart", "SubagentStop"} & hooks.keys()


def test_unrelated_commands_do_not_start_bash(monkeypatch):
    monkeypatch.setattr(run_bash, "read_input", lambda timeout: b'{"tool_input":{"command":"git status"}}')
    monkeypatch.setattr(run_bash, "find_bash", lambda: pytest.fail("Bash started"))
    assert run_bash.main(["validate-commit.sh"]) == 0
    assert run_bash.main(["validate-push.sh"]) == 0


def test_native_edit_layout_overrides_and_no_child_process(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("post_edit", ROOT / "hooks/post-edit.py")
    edit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(edit)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".codex").mkdir()
    (tmp_path / ".codex/studio-layout.json").write_text(json.dumps(
        {"engine": "unity", "assetRoots": ["custom-root"], "assetNaming": "any"}))
    assert edit.asset_layout() == (["custom-root"], "any", False)
    monkeypatch.setenv("STUDIO_ASSET_ROOTS", "other:assets")
    monkeypatch.setenv("STUDIO_ASSET_NAMING", "snake")
    assert edit.asset_layout() == (["other", "assets"], "snake", False)
    monkeypatch.setattr(edit.runner, "read_input", lambda timeout: b'{"tool_input":{"file_path":"docs/readme.md"}}')
    monkeypatch.setattr(edit.runner, "find_bash", lambda: pytest.fail("Bash started"))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("child process started"))
    assert edit.main() == 0
