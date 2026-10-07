#!/usr/bin/env bash
# Compatibility entry point; the registered commit hook is native Python.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for cmd in python python3 py; do
    if command -v "$cmd" >/dev/null 2>&1; then
        exec "$cmd" "$SCRIPT_DIR/pre-commit.py"
    fi
done
echo "BLOCKED: Python not found; commit validation did not run." >&2
exit 2
