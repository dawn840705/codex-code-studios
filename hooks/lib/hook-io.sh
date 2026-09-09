#!/usr/bin/env bash
# Shared Codex hook input/output helpers. Source this file; do not execute it.

studio__json_escape() {
    awk 'BEGIN { ORS="" }
        {
            gsub(/\\/, "\\\\");
            gsub(/\"/, "\\\"");
            gsub(/\r/, "\\r");
            gsub(/\t/, "\\t");
            if (NR > 1) printf "\\n";
            printf "%s", $0;
        }'
}

studio_emit_system_message() {
    studio__message=$(printf '%s' "$1" | studio__json_escape)
    printf '{"systemMessage":"%s"}\n' "$studio__message"
}

studio_emit_additional_context() {
    studio__message=$(printf '%s' "$1" | studio__json_escape)
    printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"%s"}}\n' "$studio__message"
}

# studio_extract_session_id <input-json> — the session id Codex puts on every
# hook payload, or nothing when the payload has none.
studio_extract_session_id() {
    if command -v jq >/dev/null 2>&1; then
        printf '%s' "$1" | jq -r '.session_id // empty' 2>/dev/null
    elif command -v python3 >/dev/null 2>&1; then
        printf '%s' "$1" | python3 -c \
            'import json,sys; print(json.load(sys.stdin).get("session_id", "") or "")' \
            2>/dev/null
    else
        printf '%s' "$1" \
            | grep -oE '"session_id"[[:space:]]*:[[:space:]]*"[^"]*"' \
            | head -1 \
            | sed -E 's/.*"session_id"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/'
    fi
}

studio_extract_changed_paths() {
    studio__input=$1
    studio__file=""
    studio__command=""

    if command -v jq >/dev/null 2>&1; then
        studio__file=$(printf '%s' "$studio__input" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
        studio__command=$(printf '%s' "$studio__input" | jq -r '.tool_input.command // empty' 2>/dev/null)
    elif command -v python3 >/dev/null 2>&1; then
        studio__file=$(printf '%s' "$studio__input" | python3 -c \
            'import json,sys; print(json.load(sys.stdin).get("tool_input", {}).get("file_path", ""))' \
            2>/dev/null)
        studio__command=$(printf '%s' "$studio__input" | python3 -c \
            'import json,sys; print(json.load(sys.stdin).get("tool_input", {}).get("command", ""))' \
            2>/dev/null)
    else
        studio__file=$(printf '%s' "$studio__input" \
            | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' \
            | head -1 \
            | sed -E 's/.*"file_path"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/')
        studio__command=$(printf '%s' "$studio__input" \
            | grep -oE '"command"[[:space:]]*:[[:space:]]*"[^"]*"' \
            | head -1 \
            | sed -E 's/.*"command"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/')
    fi

    {
        [ -n "$studio__file" ] && printf '%s\n' "$studio__file"
        if [ -n "$studio__command" ]; then
            printf '%s\n' "$studio__command" | sed -nE \
                -e 's/^\*\*\* (Add|Update|Delete) File: (.*)$/\2/p' \
                -e 's/^\*\*\* Move to: (.*)$/\1/p'
        fi
    } | sed 's|\\|/|g' | awk 'NF && !seen[$0]++'
}
