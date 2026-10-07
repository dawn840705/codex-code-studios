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


def windows_job(process):
    """Own all descendants even when Git Bash reparents its Windows children."""
    import ctypes
    from ctypes import wintypes

    class Basic(ctypes.Structure):
        _fields_ = [("times", ctypes.c_int64 * 2), ("flags", wintypes.DWORD),
                    ("sizes", ctypes.c_size_t * 2), ("active", wintypes.DWORD),
                    ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD),
                    ("scheduling", wintypes.DWORD)]

    class Extended(ctypes.Structure):
        _fields_ = [("basic", Basic), ("io", ctypes.c_uint64 * 6),
                    ("memory", ctypes.c_size_t * 4)]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                              ctypes.c_void_p, wintypes.DWORD]
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    job = kernel.CreateJobObjectW(None, None)
    limits = Extended()
    limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())
    if not kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)) \
            or not kernel.AssignProcessToJobObject(job, int(process._handle)):
        error = ctypes.WinError(ctypes.get_last_error())
        kernel.CloseHandle(job)
        raise error
    resume = ctypes.WinDLL("ntdll").NtResumeProcess
    resume.argtypes = [wintypes.HANDLE]
    resume.restype = wintypes.LONG
    if resume(int(process._handle)) != 0:
        kernel.CloseHandle(job)
        raise OSError("could not resume hook process")
    return lambda: kernel.CloseHandle(job)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("usage: run-bash.py <bash arguments>", file=sys.stderr)
        return 2

    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=27)
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
    if Path(args[0]).name in ("validate-commit.sh", "validate-push.sh"):
        try:
            command = json.loads(payload).get("tool_input", {}).get("command", "")
            action = "commit" if Path(args[0]).name == "validate-commit.sh" else "push"
            if not re.search(r"^git\s+" + action, command):
                return 0
        except (ValueError, AttributeError, TypeError):
            pass  # Unknown input follows the existing shell validation path.
    if irrelevant_edit(args[0], payload):
        return 0

    bash = find_bash()
    if not bash:
        print("Code Studios: Bash not found; install Git for Windows or Bash.", file=sys.stderr)
        return 127
    process = None
    incomplete = False
    previous = {}
    close_job = None
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    try:
        process = subprocess.Popen(
            [bash, *args], stdin=subprocess.PIPE,
            start_new_session=os.name != "nt",
            creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP | 0x4) if os.name == "nt" else 0,
        )
        if os.name == "nt":
            close_job = windows_job(process)
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
        if close_job is not None:
            close_job()
        if process is not None and (incomplete or process.poll() is None):
            terminate_tree(process)
        for signum, handler in previous.items():
            signal.signal(signum, handler)


if __name__ == "__main__":
    raise SystemExit(main())
