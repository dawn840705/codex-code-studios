#!/bin/bash
# Codex PreCompact hook: return session state as JSON before context compression.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -f "$SCRIPT_DIR/lib/hook-io.sh" ] || exit 0
# shellcheck source=lib/hook-io.sh
. "$SCRIPT_DIR/lib/hook-io.sh"

if [ -f "$SCRIPT_DIR/lib/detect-layout.sh" ]; then
    # shellcheck source=lib/detect-layout.sh
    . "$SCRIPT_DIR/lib/detect-layout.sh"
else
    # Degraded fallback: the pre-v0.6.2 hardcoded web layout.
    STUDIO_DESIGN_ROOTS="design/gdd"
    studio_find_design_docs() { find design/gdd -type f -name '*.md' 2>/dev/null; }
fi

# Every list this hook injects is capped. A Unity project can have hundreds of
# untracked files and a Documents/ tree full of TODO markers; the point of the
# dump is the recovery pointer, not an inventory.
MAX_LIST_LINES=30

# print_capped <heading> <newline-separated list> — "  - item" lines, at most
# MAX_LIST_LINES of them, then a count of what was left out.
print_capped() {
    local heading="$1" list="$2" total
    [ -n "$list" ] || return 0
    total=$(printf '%s\n' "$list" | grep -c .)
    echo "$heading"
    printf '%s\n' "$list" | grep . | head -n "$MAX_LIST_LINES" \
        | while IFS= read -r item; do echo "  - $item"; done
    if [ "$total" -gt "$MAX_LIST_LINES" ]; then
        echo "  ... and $((total - MAX_LIST_LINES)) more"
    fi
}

build_message() {

echo "=== SESSION STATE BEFORE COMPACTION ==="
echo "Timestamp: $(date)"

# --- Active session state file ---
STATE_FILE="production/session-state/active.md"
if [ -f "$STATE_FILE" ]; then
    echo ""
    echo "## Active Session State (from $STATE_FILE)"
    STATE_LINES=$(wc -l < "$STATE_FILE" 2>/dev/null | tr -d ' ')
    if [ "$STATE_LINES" -gt 100 ] 2>/dev/null; then
        head -n 100 "$STATE_FILE"
        echo "... (truncated — $STATE_LINES total lines, showing first 100)"
    else
        cat "$STATE_FILE"
    fi
fi

# --- Files modified this session (unstaged + staged + untracked) ---
echo ""
echo "## Files Modified (git working tree)"

# --no-optional-locks: these are read-only queries; without the flag `git diff`
# writes .git/index.lock, which is unremovable on unlink-denied mounts and
# blocks every later commit.
CHANGED=$(git --no-optional-locks diff --name-only 2>/dev/null)
STAGED=$(git --no-optional-locks diff --staged --name-only 2>/dev/null)
UNTRACKED=$(git --no-optional-locks ls-files --others --exclude-standard 2>/dev/null)

print_capped "Unstaged changes:" "$CHANGED"
print_capped "Staged changes:" "$STAGED"
print_capped "New untracked files:" "$UNTRACKED"
if [ -z "$CHANGED" ] && [ -z "$STAGED" ] && [ -z "$UNTRACKED" ]; then
    echo "  (no uncommitted changes)"
fi

# --- Work-in-progress design docs ---
# Roots come from detect-layout.sh: design/gdd on the web layout, Documents/
# and friends on Unity. This used to glob design/gdd/*.md only.
echo ""
echo "## Design Docs — Work In Progress"

DESIGN_ROOT_LIST=$(printf '%s' "$STUDIO_DESIGN_ROOTS" | tr '\n' ' ')
WIP=""
while IFS= read -r f; do
    [ -n "$f" ] || continue
    HITS=$(grep -nHE "TODO|WIP|PLACEHOLDER|\[TO BE|\[TBD\]" "$f" 2>/dev/null)
    [ -n "$HITS" ] || continue
    WIP="$WIP$HITS
"
done <<EOF
$(studio_find_design_docs)
EOF

if [ -n "$WIP" ]; then
    WIP_TOTAL=$(printf '%s' "$WIP" | grep -c .)
    printf '%s' "$WIP" | grep . | head -n "$MAX_LIST_LINES" \
        | while IFS= read -r line; do echo "  $line"; done
    if [ "$WIP_TOTAL" -gt "$MAX_LIST_LINES" ]; then
        echo "  ... and $((WIP_TOTAL - MAX_LIST_LINES)) more"
    fi
else
    echo "  (no WIP markers found in: $DESIGN_ROOT_LIST)"
fi

# --- Log compaction event ---
SESSION_LOG_DIR="production/session-logs"
mkdir -p "$SESSION_LOG_DIR" 2>/dev/null
echo "Context compaction occurred at $(date)." \
    >> "$SESSION_LOG_DIR/compaction-log.txt" 2>/dev/null

echo ""
echo "## Recovery Instructions"
if [ -f "$STATE_FILE" ]; then
    echo "After compaction, read $STATE_FILE to recover full working context."
fi
echo "Read any files listed above that are being actively worked on."
echo "=== END SESSION STATE ==="
}

MESSAGE=$(build_message)
studio_emit_system_message "$MESSAGE"

exit 0
