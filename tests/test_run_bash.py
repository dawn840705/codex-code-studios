import importlib.util
import ntpath
from pathlib import Path
import subprocess
import sys


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
