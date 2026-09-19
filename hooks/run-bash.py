"""Run a Code Studios hook with a real Bash executable.

Windows reserves ``bash.exe`` for the WSL launcher, so a bare ``bash`` command
can miss an installed Git Bash before PATH is considered.  Resolve Git Bash
from the Git installation instead; use the normal PATH lookup elsewhere.
"""

from __future__ import annotations

import ntpath
import os
import shutil
import subprocess
import sys
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


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("usage: run-bash.py <bash arguments>", file=sys.stderr)
        return 2

    bash = find_bash()
    if not bash:
        print("Code Studios: Bash not found; install Git for Windows or Bash.", file=sys.stderr)
        return 127
    try:
        return subprocess.run([bash, *args], check=False).returncode
    except OSError as exc:
        print(f"Code Studios: failed to start Bash: {exc}", file=sys.stderr)
        return 127


if __name__ == "__main__":
    raise SystemExit(main())
