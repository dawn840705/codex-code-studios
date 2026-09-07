#!/bin/bash
# UserPromptSubmit: observation only, opt-in per project. No executor calls.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if command -v python3 >/dev/null 2>&1; then
    python3 "${SCRIPT_DIR}/../scripts/reasoning_effort.py" hook
else
    echo 'reasoning-effort: observation unavailable (python3 missing)' >&2
fi
exit 0
