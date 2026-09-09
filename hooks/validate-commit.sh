#!/bin/bash
# Codex PreToolUse hook: validates git commit commands
# Receives JSON on stdin with tool_input.command
# Exit 0 = allow, Exit 2 = block
#
# Input schema (PreToolUse for Bash):
# { "tool_name": "Bash", "tool_input": { "command": "git commit -m ..." } }
#
# Layout-aware since v0.6.2. The path filters used to be ^design/gdd/,
# ^assets/data/, ^src/gameplay/ and ^src/ — none of which a Unity project ever
# matches (its files live under Assets/ and Documents/), so this hook passed
# silently on every Unity commit. Code checks now select files by EXTENSION,
# which is portable across every engine; document and data checks use the
# detected design/asset roots.

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/lib/hook-io.sh" ]; then
    # shellcheck source=lib/hook-io.sh
    . "$SCRIPT_DIR/lib/hook-io.sh"
fi

if [ -f "$SCRIPT_DIR/lib/detect-layout.sh" ]; then
    # shellcheck source=lib/detect-layout.sh
    . "$SCRIPT_DIR/lib/detect-layout.sh"
else
    # Degraded fallback: the pre-v0.6.2 hardcoded web layout.
    STUDIO_DESIGN_ROOTS="design/gdd"
    studio_path_has_ext() {
        case "$1" in
            *.gd|*.cs|*.cpp|*.c|*.h|*.hpp|*.rs|*.py|*.js|*.ts|*.tsx|*.jsx) return 0 ;;
        esac
        return 1
    }
    studio_asset_root_regex() { printf '(^|/)(assets)/'; }
fi

# Parse command -- use jq if available, fall back to grep
if command -v jq >/dev/null 2>&1; then
    COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
else
    COMMAND=$(echo "$INPUT" | grep -oE '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/"command"[[:space:]]*:[[:space:]]*"//;s/"$//')
fi

# Only commands that BEGIN with `git commit`. A prefixed form (`git add -A &&
# git commit`, `ENV=x git commit`, `git -C dir commit`) passes without a
# verdict. Widening this anchor is a separate decision: it would switch the
# JSON block on for every such commit at once.
if ! echo "$COMMAND" | grep -qE '^git[[:space:]]+commit'; then
    exit 0
fi

# Get staged files. --no-optional-locks: this hook runs *before* the commit, so
# refreshing the index here can leave a lock that makes the commit it is
# validating fail on unlink-denied mounts.
STAGED=$(git --no-optional-locks diff --cached --name-only 2>/dev/null)
if [ -z "$STAGED" ]; then
    exit 0
fi

WARNINGS=""

# Cap the per-file scans. A Unity commit can stage hundreds of files, and this
# hook runs inside a 15s PreToolUse timeout.
MAX_SCAN=200

# --- Design documents: required sections ---------------------------------
# Every existing design root is considered, not just design/gdd/. Outside the
# canonical design/gdd/ path the section check only applies to files that
# already look like a GDD (3+ of the required sections present) — otherwise
# every ordinary markdown note in a project's Documents/ folder would be
# nagged for a "Player Fantasy" heading it was never meant to have.
GDD_SECTIONS="Overview
Player Fantasy
Detailed
Formulas
Edge Cases
Dependencies
Tuning Knobs
Acceptance Criteria"

count_gdd_sections() {
    local file="$1" hits=0 section
    while IFS= read -r section; do
        [ -n "$section" ] || continue
        if grep -qi "$section" "$file" 2>/dev/null; then
            hits=$((hits + 1))
        fi
    done <<< "$GDD_SECTIONS"
    printf '%s' "$hits"
}

report_missing_sections() {
    local file="$1" section
    while IFS= read -r section; do
        [ -n "$section" ] || continue
        if ! grep -qi "$section" "$file" 2>/dev/null; then
            WARNINGS="$WARNINGS\nDESIGN: $file missing required section: $section"
        fi
    done <<< "$GDD_SECTIONS"
}

while IFS= read -r design_root; do
    [ -n "$design_root" ] || continue
    # A design root of "." would match the whole repository — refuse it.
    [ "$design_root" = "." ] && continue
    design_root="${design_root%/}"

    DESIGN_FILES=$(printf '%s\n' "$STAGED" | grep -E "^${design_root}/.*\.md$")
    [ -n "$DESIGN_FILES" ] || continue

    while IFS= read -r file; do
        [ -n "$file" ] || continue
        [ -f "$file" ] || continue

        if [ "$design_root" = "design/gdd" ]; then
            # Canonical GDD path — always enforced (pre-v0.6.2 behaviour).
            report_missing_sections "$file"
        elif [ "$(count_gdd_sections "$file")" -ge 3 ]; then
            # Looks like a GDD living somewhere else — enforce the remainder.
            report_missing_sections "$file"
        fi
    done <<< "$DESIGN_FILES"
done <<< "$STUDIO_DESIGN_ROOTS"

# --- JSON data files: block invalid JSON ---------------------------------
# Matches the legacy assets/data/ path plus any JSON under the detected asset
# roots (Assets/ on Unity, Content/ on Unreal, assets/ on web).
ASSET_RE=$(studio_asset_root_regex)
DATA_FILES=$(printf '%s\n' "$STAGED" | grep -E "((^|/)assets/data/.*\.json$)|(${ASSET_RE}.*\.json$)")

if [ -n "$DATA_FILES" ]; then
    # Find a working Python command
    PYTHON_CMD=""
    for cmd in python python3 py; do
        if command -v "$cmd" >/dev/null 2>&1; then
            PYTHON_CMD="$cmd"
            break
        fi
    done

    while IFS= read -r file; do
        [ -n "$file" ] || continue
        if [ -f "$file" ]; then
            if [ -n "$PYTHON_CMD" ]; then
                if ! "$PYTHON_CMD" -m json.tool "$file" > /dev/null 2>&1; then
                    echo "BLOCKED: $file is not valid JSON" >&2
                    exit 2
                fi
            else
                echo "WARNING: Cannot validate JSON (python not found): $file" >&2
            fi
        fi
    done <<< "$DATA_FILES"
fi

# --- Source files: selected by extension, not by directory ---------------
CODE_FILES=""
CODE_COUNT=0
while IFS= read -r file; do
    [ -n "$file" ] || continue
    [ -f "$file" ] || continue
    if studio_path_has_ext "$file"; then
        CODE_FILES="$CODE_FILES$file
"
        CODE_COUNT=$((CODE_COUNT + 1))
    fi
done <<< "$STAGED"

# summarize_hits <label-line> <files...> — collapses per-file findings into one
# warning naming at most 5 files, so a large commit cannot bury the message.
summarize_hits() {
    local label="$1" files="$2" count shown
    count=$(printf '%s' "$files" | grep -c . 2>/dev/null)
    [ "$count" -gt 0 ] 2>/dev/null || return 0
    shown=$(printf '%s' "$files" | grep . | head -5 | tr '\n' ' ')
    WARNINGS="$WARNINGS\n$label ($count file(s)): $shown"
    if [ "$count" -gt 5 ]; then
        WARNINGS="$WARNINGS… and $((count - 5)) more"
    fi
}

# Hardcoded gameplay values are a game-track concern (balance belongs in data
# files). Product code carries `timeout duration = 300` or `rate = 100`
# legitimately and got this warning on every commit, so the scan runs only
# when production/track.txt says `game`. No file, or any other value, skips it.
# The TODO-owner-tag warning that used to sit beside it is gone: a style
# opinion, never a verdict.
TRACK=""
if [ -f "production/track.txt" ]; then
    TRACK=$(tr -d '[:space:]' < production/track.txt 2>/dev/null)
fi

if [ "$CODE_COUNT" -gt 0 ] && [ "$TRACK" = "game" ]; then
    SCANNED=0
    HARDCODED=""

    while IFS= read -r file; do
        [ -n "$file" ] || continue
        SCANNED=$((SCANNED + 1))
        if [ "$SCANNED" -gt "$MAX_SCAN" ]; then
            break
        fi

        # -q keeps the matches out of stdout; the old version leaked every
        # matching line into the hook's output.
        if grep -qE '(damage|health|speed|rate|chance|cost|duration)[[:space:]]*[:=][[:space:]]*[0-9]+' "$file" 2>/dev/null; then
            HARDCODED="$HARDCODED$file
"
        fi
    done <<< "$CODE_FILES"

    summarize_hits "CODE: may contain hardcoded gameplay values — use data files" "$HARDCODED"

    if [ "$CODE_COUNT" -gt "$MAX_SCAN" ]; then
        WARNINGS="$WARNINGS\nNOTE: scanned the first $MAX_SCAN of $CODE_COUNT staged source files (hook time budget)."
    fi
fi

# Return warnings as valid Codex hook JSON and allow the commit.
if [ -n "$WARNINGS" ]; then
    MESSAGE=$(printf '%b' "Commit validation warnings:$WARNINGS")
    if command -v studio_emit_system_message >/dev/null 2>&1; then
        studio_emit_system_message "$MESSAGE"
    fi
fi

exit 0
