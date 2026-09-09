#!/bin/bash
# Codex SessionStart hook: load project context at session start
#
# Input schema (SessionStart): No stdin input

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Code Studios — Codex Session Context ==="

# Current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
if [ -n "$BRANCH" ]; then
    echo "Branch: $BRANCH"

    # Recent commits
    echo ""
    echo "Recent commits:"
    git log --oneline -5 2>/dev/null | while read -r line; do
        echo "  $line"
    done
fi

# Current sprint (find most recent sprint file)
LATEST_SPRINT=$(ls -t production/sprints/sprint-*.md 2>/dev/null | head -1)
if [ -n "$LATEST_SPRINT" ]; then
    echo ""
    echo "Active sprint: $(basename "$LATEST_SPRINT" .md)"
fi

# Current milestone
LATEST_MILESTONE=$(ls -t production/milestones/*.md 2>/dev/null | head -1)
if [ -n "$LATEST_MILESTONE" ]; then
    echo "Active milestone: $(basename "$LATEST_MILESTONE" .md)"
fi

# Open bug count
BUG_COUNT=0
for dir in tests/playtest production; do
    if [ -d "$dir" ]; then
        count=$(find "$dir" -name "BUG-*.md" 2>/dev/null | wc -l)
        BUG_COUNT=$((BUG_COUNT + count))
    fi
done
if [ "$BUG_COUNT" -gt 0 ]; then
    echo "Open bugs: $BUG_COUNT"
fi

# Code health quick check
if [ -d "src" ]; then
    TODO_COUNT=$(grep -r "TODO" src/ 2>/dev/null | wc -l)
    FIXME_COUNT=$(grep -r "FIXME" src/ 2>/dev/null | wc -l)
    if [ "$TODO_COUNT" -gt 0 ] || [ "$FIXME_COUNT" -gt 0 ]; then
        echo ""
        echo "Code health: ${TODO_COUNT} TODOs, ${FIXME_COUNT} FIXMEs in src/"
    fi
fi

# --- Human action queue (things only a person can do) ---
# Announce existence only. The file is a round-trip: a person may have written a
# result into it since the last session, and that result is usually the first
# task of this one. Silent when the file does not exist.
HUMAN_ACTIONS="production/human-actions.md"
if [ -f "$HUMAN_ACTIONS" ]; then
    echo ""
    echo "=== HUMAN ACTION QUEUE PRESENT ==="
    echo "File: $HUMAN_ACTIONS"
    echo "Read it before starting work. If a person has answered an item since the"
    echo "last session, that answer is this session's first task. Do not re-ask for"
    echo "something already recorded as done."
    echo "Rule: rules/work-records.md section 2"
fi

# --- Active session state recovery ---
STATE_FILE="production/session-state/active.md"
if [ -f "$STATE_FILE" ]; then
    echo ""
    echo "=== ACTIVE SESSION STATE DETECTED ==="
    echo "A previous session left state at: $STATE_FILE"
    echo "Read this file to recover context and continue where you left off."
    echo ""
    echo "Quick summary:"
    head -20 "$STATE_FILE" 2>/dev/null
    TOTAL_LINES=$(wc -l < "$STATE_FILE" 2>/dev/null)
    if [ "$TOTAL_LINES" -gt 20 ]; then
        echo "  ... ($TOTAL_LINES total lines — read the full file to continue)"
    fi
    echo "=== END SESSION STATE PREVIEW ==="
fi


# --- Self-loop quality rule (applies to every project using this plugin) ---
echo ""
echo "=== Self-Loop Rule (always active) ==="
echo "Deliverables with clear quality criteria are NOT one-shot. Iterate:"
echo "  plan -> execute -> score each criterion 1-10 (strict, evidence-cited) -> all >=8 ? done : fix lowest first"
echo "Guards: scores of 8+ require quoted evidence | max 5 iterations | stop+report after 2 stalled rounds."
echo "Full protocol: ${SCRIPT_DIR}/../rules/self-loop.md. Explicit run: \$self-loop"
echo "Scoring order: if a script can decide a criterion, its EXIT CODE sets the score — not your judgment."

# --- Route hint (call-count routing; applies to every project) ---
echo ""
echo "=== Route Hint (always active) ==="
echo "Pick a route BEFORE spawning: light = handle it yourself (0 agents) | standard = 1 specialist | heavy = fan-out + gates"
echo "Savings come from FEWER CALLS, not a cheaper model. Splitting is the last resort — measured: 7 chunks 610K tok vs 134K single call, equal quality."
echo "Tied between two routes? Take the lighter one. Full rule: ${SCRIPT_DIR}/../rules/route-hint.md"

# --- Autonomy contract (default is proceed; applies to every project) ---
echo ""
echo "=== Autonomy Contract (always active) ==="
echo "Default is proceed. Stop only for: R4/paid calls · unresolved track (ask once, write production/track.txt) · overturning a pinned decision"
echo "  · files outside write ownership · facts only a person can observe · items the user asked to review."
echo "Full rule: ${SCRIPT_DIR}/../rules/autonomy-contract.md"

# --- Lesson Ledger (교육용 노하우 원장) ---
# Announced only when it exists. Every project without one used to get a
# "not initialized" reminder every session; $lesson-log creates it on demand.
LESSON_DIR="Documents/Lessons"
if [ -d "$LESSON_DIR" ]; then
    LESSON_COUNT=$(find "$LESSON_DIR" -name "LES-*.md" 2>/dev/null | wc -l)
    LATEST_LESSON=$(ls -t "$LESSON_DIR"/LES-*.md 2>/dev/null | head -1)
    echo ""
    echo "Lesson Ledger: $LESSON_COUNT lessons recorded$([ -n "$LATEST_LESSON" ] && echo ", latest: $(basename "$LATEST_LESSON" .md)")"
    echo "  (교육 자료 원칙: 함정 반복/설계 구멍/뒤집힌 가정/도구 함정/기획 패턴 발생 시 \$lesson-log 로 기록)"
fi

echo "==================================="
exit 0
