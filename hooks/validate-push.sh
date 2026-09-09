#!/bin/bash
# Codex PreToolUse hook: warns on git push to a protected branch
# Advisory only: emits a systemMessage and always exits 0. It never blocks.
# Only commands that BEGIN with `git push` are inspected — a prefixed form
# (`git add -A && git push`, `ENV=x git push`) passes without a verdict.
#
# Input schema (PreToolUse for Bash):
# { "tool_name": "Bash", "tool_input": { "command": "git push origin main" } }

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/lib/hook-io.sh" ]; then
    # shellcheck source=lib/hook-io.sh
    . "$SCRIPT_DIR/lib/hook-io.sh"
fi

# Parse command -- use jq if available, fall back to grep
if command -v jq >/dev/null 2>&1; then
    COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
else
    COMMAND=$(echo "$INPUT" | grep -oE '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/"command"[[:space:]]*:[[:space:]]*"//;s/"$//')
fi

# Only commands that begin with `git push`
if ! echo "$COMMAND" | grep -qE '^git[[:space:]]+push'; then
    exit 0
fi

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
MATCHED_BRANCH=""

# Check if pushing to a protected branch
for branch in develop main master; do
    if [ "$CURRENT_BRANCH" = "$branch" ]; then
        MATCHED_BRANCH="$branch"
        break
    fi
    # Also check if pushing to a protected branch explicitly (quote branch name for safety)
    if echo "$COMMAND" | grep -qE "[[:space:]]${branch}([[:space:]]|$)"; then
        MATCHED_BRANCH="$branch"
        break
    fi
done

if [ -n "$MATCHED_BRANCH" ]; then
    MESSAGE="Push to protected branch '$MATCHED_BRANCH' detected. Ensure the build and unit tests pass and no S1/S2 bugs remain before pushing."
    if command -v studio_emit_system_message >/dev/null 2>&1; then
        studio_emit_system_message "$MESSAGE"
    fi
    # Allow the push; the message above is the whole verdict.
fi

exit 0
