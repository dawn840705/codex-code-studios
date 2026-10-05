"""Run a Code Studios hook with a real Bash executable.

Windows reserves ``bash.exe`` for the WSL launcher, so a bare ``bash`` command
can miss an installed Git Bash before PATH is considered.  Resolve Git Bash
from the Git installation instead; use the normal PATH lookup elsewhere.
"""

from __future__ import annotations

import ntpath
import argparse
import json
import os
from pathlib import Path
import queue
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from typing import Callable, Mapping


def find_bash(
    platform: str = os.name,
    which: Callable[[str], str | None] = shutil.which,
    is_file: Callable[[str], bool] = os.path.isfile,
    environ: Mapping[str, str] = os.environ,
) -> str | None:
    if platform != "nt":
        return which("bash")

    candidates: list[str] = []
    git = which("git")
    if git:
        current = ntpath.dirname(git)
        while current and ntpath.dirname(current) != current:
            candidates.extend(
                (
                    ntpath.join(current, "bash.exe"),
                    ntpath.join(current, "bin", "bash.exe"),
                    ntpath.join(current, "usr", "bin", "bash.exe"),
                )
            )
            current = ntpath.dirname(current)

    for key in ("ProgramFiles", "ProgramW6432", "LOCALAPPDATA"):
        root = environ.get(key)
        if root:
            candidates.extend(
                (
                    ntpath.join(root, "Git", "bin", "bash.exe"),
                    ntpath.join(root, "Programs", "Git", "bin", "bash.exe"),
                )
            )

    seen: set[str] = set()
    for candidate in candidates:
        normalized = ntpath.normcase(candidate)
        if normalized not in seen and is_file(candidate):
            return candidate
        seen.add(normalized)
    return None


def read_input(timeout: float) -> bytes:
    """Bound EOF waiting; only the wrapper owns the caller's input pipe."""
    result: queue.Queue = queue.Queue()

    def read() -> None:
        try:
            # Buffered stdin holds a Python lock while blocked; a daemon thread
            # holding that lock can abort interpreter shutdown after timeout.
            chunks = []
            while chunk := os.read(sys.stdin.fileno(), 65536):
                chunks.append(chunk)
            result.put(b"".join(chunks))
        except (OSError, ValueError):
            result.put(b"")

    threading.Thread(target=read, daemon=True).start()
    try:
        return result.get(timeout=timeout)
    except queue.Empty:
        raise TimeoutError("hook input did not reach EOF") from None


def irrelevant_edit(script: str, payload: bytes) -> bool:
    """Skip only provably unrelated edits; asset layout stays shell-owned."""
    name = Path(script).name
    known = {"validate-assets.sh", "validate-skill-change.sh",
             "unity-meta-check.sh", "unity-animator-string-lint.sh"}
    if name not in known:
        return False
    if not payload.strip():
        return True
    try:
        data = json.loads(payload)
        tool = data.get("tool_input", {})
        paths = [tool.get("file_path", "")]
        command = tool.get("command", "")
        paths.extend(re.findall(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", command, re.M))
        paths.extend(re.findall(r"^\*\*\* Move to: (.+)$", command, re.M))
        paths = [p.replace("\\", "/") for p in paths if p]
    except (ValueError, AttributeError, TypeError):
        return False
    if not paths:
        return True
    if name == "validate-assets.sh":
        return False  # Any extension may have a naming or custom-root violation.
    if name == "validate-skill-change.sh":
        return not any(re.search(r"(?:^|/)skills/[^/]+/SKILL\.md$", p) for p in paths)
    if not (Path("Assets").is_dir() and Path("ProjectSettings").is_dir()):
        return True
    suffixes = (".cs",) if name == "unity-animator-string-lint.sh" else (
        ".cs", ".shader", ".asset", ".prefab", ".mat", ".controller")
    return not any(p.endswith(suffixes) for p in paths)


def terminate_tree(process: subprocess.Popen) -> None:
    """Kill this hook's descendants as well as its Bash process."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=1, check=False)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=1)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("usage: run-bash.py <bash arguments>", file=sys.stderr)
        return 2

    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=7)
    parser.add_argument("--stdin-timeout", type=float, default=1)
    parser.add_argument("bash_args", nargs=argparse.REMAINDER)
    # Keep the historic `-c ...` invocation working without parsing Bash flags.
    if args[0].startswith("--timeout") or args[0].startswith("--stdin-timeout"):
        options = parser.parse_args(args)
        args = options.bash_args
    else:
        options = parser.parse_args(["--", *args])
        args = options.bash_args[1:]
    if args and args[0] == "--":
        args = args[1:]
    if not args or options.timeout <= 0 or options.stdin_timeout <= 0:
        parser.error("positive timeouts and Bash arguments are required")
    deadline = time.monotonic() + options.timeout
    try:
        payload = read_input(min(options.stdin_timeout, options.timeout))
    except TimeoutError as exc:
        print(f"Code Studios: {exc}; validation did not run.", file=sys.stderr)
        return 124
    if irrelevant_edit(args[0], payload):
        return 0

    bash = find_bash()
    if not bash:
        print("Code Studios: Bash not found; install Git for Windows or Bash.", file=sys.stderr)
        return 127
    process = None
    incomplete = False
    previous = {}
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    try:
        process = subprocess.Popen(
            [bash, *args], stdin=subprocess.PIPE,
            start_new_session=os.name != "nt",
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )
        for signum in (signal.SIGTERM, signal.SIGINT):
            previous[signum] = signal.signal(signum, interrupted)
        process.communicate(input=payload, timeout=max(0.001, deadline - time.monotonic()))
        return process.returncode
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        incomplete = True
        print("Code Studios: hook interrupted or timed out; validation incomplete.", file=sys.stderr)
        return 124
    except OSError as exc:
        print(f"Code Studios: failed to start Bash: {exc}", file=sys.stderr)
        return 127
    finally:
        if process is not None and (incomplete or process.poll() is None):
            terminate_tree(process)
        for signum, handler in previous.items():
            signal.signal(signum, handler)


if __name__ == "__main__":
    raise SystemExit(main())
