#!/usr/bin/env bash
# Codex PostToolUse hook: remind the agent to validate changed plugin skills.
# Advisory only, once per skill per session. Always exits 0.

set +e
INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -f "$SCRIPT_DIR/lib/hook-io.sh" ] || exit 0
# shellcheck source=lib/hook-io.sh
. "$SCRIPT_DIR/lib/hook-io.sh"

PATHS=$(studio_extract_changed_paths "$INPUT")
[ -n "$PATHS" ] || exit 0

SKILLS=$(printf '%s\n' "$PATHS" \
    | sed -nE 's#(^|.*/)skills/([^/]+)/SKILL\.md$#\2#p' \
    | awk 'NF && !seen[$0]++')

[ -n "$SKILLS" ] || exit 0

# Once per skill per session. Editing one SKILL.md ten times used to inject
# the same reminder ten times. The session id on the hook payload keys a
# marker file listing the skills already announced; without an id (or a
# writable scratch dir) the hook falls back to announcing every time.
SESSION_ID=$(studio_extract_session_id "$INPUT")
if [ -n "$SESSION_ID" ]; then
    MARKER_DIR="${TMPDIR:-/tmp}/codex-code-studios"
    MARKER="$MARKER_DIR/skill-notified-$(printf '%s' "$SESSION_ID" | tr -c 'A-Za-z0-9._-' '_')"
    mkdir -p "$MARKER_DIR" 2>/dev/null
    if [ -f "$MARKER" ]; then
        SKILLS=$(printf '%s\n' "$SKILLS" | grep -vxF -f "$MARKER")
        [ -n "$SKILLS" ] || exit 0
    fi
    printf '%s\n' "$SKILLS" >> "$MARKER" 2>/dev/null
fi

NAMES=$(printf '%s' "$SKILLS" | tr '\n' ' ' | sed 's/[[:space:]]*$//')
studio_emit_additional_context "Code Studios skill modified: $NAMES. Run \$skill-test static for each changed skill and validate its SKILL.md with the Codex skill validator."

exit 0
