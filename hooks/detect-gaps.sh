#!/bin/bash
# Hook: detect-gaps.sh
# Event: SessionStart
# Purpose: Detect missing documentation when code/prototypes exist
# Cross-platform: Windows Git Bash compatible (uses grep -E, not -P)
#
# Layout-aware since v0.6.2: source roots, design roots and the engine test all
# come from hooks/lib/detect-layout.sh. Before that this hook assumed src/ +
# design/gdd/, so a mature Unity project (Assets/**/*.cs, Documents/*.md) was
# reported as "NEW PROJECT" and checks 1-5 never ran at all.

# Exit on error for debugging (but don't fail the session)
set +e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Checking for Documentation Gaps ==="

if [ ! -f "$SCRIPT_DIR/lib/detect-layout.sh" ]; then
  echo "   (skipped: hooks/lib/detect-layout.sh not found — plugin install looks incomplete)"
  echo "==================================="
  exit 0
fi

# shellcheck source=lib/detect-layout.sh
. "$SCRIPT_DIR/lib/detect-layout.sh"

# Human-readable root lists for the suggestion messages. Prefer a root that
# actually exists so the suggested command names a real path.
PRIMARY_SRC_ROOT=""
while IFS= read -r candidate; do
  [ -n "$candidate" ] || continue
  if [ -d "$candidate" ]; then
    PRIMARY_SRC_ROOT="$candidate"
    break
  fi
done <<< "$STUDIO_SRC_ROOTS"
[ -n "$PRIMARY_SRC_ROOT" ] || PRIMARY_SRC_ROOT=$(printf '%s\n' "$STUDIO_SRC_ROOTS" | head -1)
PRIMARY_DESIGN_ROOT=$(printf '%s\n' "$STUDIO_DESIGN_ROOTS" | head -1)
DESIGN_ROOT_LIST=$(printf '%s' "$STUDIO_DESIGN_ROOTS" | tr '\n' ' ')

# --- Check 0: Fresh project detection (suggests \$start) ---
FRESH_PROJECT=true

# An engine project is never fresh — Unity/Godot/Unreal/GameMaker all require
# scaffolding that does not exist before someone deliberately created it.
if studio_is_engine_project; then
  FRESH_PROJECT=false
fi

# Check if engine is configured
if [ -f ".codex/studio/technical-preferences.md" ]; then
  ENGINE_LINE=$(grep -E "^\- \*\*Engine\*\*:" .codex/studio/technical-preferences.md 2>/dev/null)
  if [ -n "$ENGINE_LINE" ] && ! echo "$ENGINE_LINE" | grep -q "TO BE CONFIGURED" 2>/dev/null; then
    FRESH_PROJECT=false
  fi
fi

# Check if a game concept exists in any design root
if studio_design_doc_exists "game-concept" || studio_design_doc_exists "product-concept"; then
  FRESH_PROJECT=false
fi

# Check if source code exists
SRC_FILES=$(studio_count_sources)
if [ "$SRC_FILES" -gt 0 ]; then
  FRESH_PROJECT=false
fi

# The domain detector's verdict rules out "fresh" too. production/track.txt or
# a stack signal (package.json naming react, pubspec.yaml, go.mod, …) means a
# stack was already chosen, even when nothing lives under a known source root
# — a web app that keeps its code in pages/ and components/ counts 0 sources
# and used to be told to run $start every session. Reuse the detector rather
# than re-deriving its heuristics here; only `unknown` leaves this flag alone.
if [ -f "$SCRIPT_DIR/detect-project-type.sh" ]; then
  PROJECT_TYPE=$(bash "$SCRIPT_DIR/detect-project-type.sh" 2>/dev/null \
                 | sed -n 's/^PROJECT_TYPE=//p' | head -1)
  case "${PROJECT_TYPE%+ai}" in
    ""|unknown) ;;
    *) FRESH_PROJECT=false ;;
  esac
fi

# A body of design docs also rules out "fresh", even when none of them is
# named game-concept.md — projects that predate this template name it whatever
# they like.
DESIGN_FILES=$(studio_count_design_docs)
if [ "$DESIGN_FILES" -ge 3 ]; then
  FRESH_PROJECT=false
fi

# Production artifacts are layout-independent evidence that work has started:
# sprints, milestones, bugs, session logs. Nothing creates production/ by
# accident.
if [ -d "production" ] && [ -n "$(find production -mindepth 1 -print -quit 2>/dev/null)" ]; then
  FRESH_PROJECT=false
fi

if [ "$FRESH_PROJECT" = true ]; then
  echo ""
  echo "🚀 NEW PROJECT: No engine configured, no game concept, no source code, no production/track.txt."
  echo "   This looks like a fresh start! Run: \$start"
  echo ""
  echo "💡 To get a comprehensive project analysis, run: \$project-stage-detect"
  echo "==================================="
  exit 0
fi

# --- Check 1: Substantial codebase but sparse design docs ---
if [ "$SRC_FILES" -gt 50 ] && [ "$DESIGN_FILES" -lt 5 ]; then
  echo "⚠️  GAP: Substantial codebase ($SRC_FILES source files) but sparse design docs ($DESIGN_FILES files in: $DESIGN_ROOT_LIST)"
  echo "    Suggested action: \$reverse-document design $PRIMARY_SRC_ROOT/[system]"
  echo "    Or run: \$project-stage-detect to get full analysis"
fi

# --- Check 2: Prototypes without documentation ---
if [ -d "prototypes" ]; then
  PROTOTYPE_DIRS=$(find prototypes -mindepth 1 -maxdepth 1 -type d 2>/dev/null)
  UNDOCUMENTED_PROTOS=()

  if [ -n "$PROTOTYPE_DIRS" ]; then
    while IFS= read -r proto_dir; do
      # Normalize path separators for Windows
      proto_dir=$(echo "$proto_dir" | sed 's|\\|/|g')

      # Check for README.md or CONCEPT.md
      if [ ! -f "${proto_dir}/README.md" ] && [ ! -f "${proto_dir}/CONCEPT.md" ]; then
        proto_name=$(basename "$proto_dir")
        UNDOCUMENTED_PROTOS+=("$proto_name")
      fi
    done <<< "$PROTOTYPE_DIRS"

    if [ ${#UNDOCUMENTED_PROTOS[@]} -gt 0 ]; then
      echo "⚠️  GAP: ${#UNDOCUMENTED_PROTOS[@]} undocumented prototype(s) found:"
      for proto in "${UNDOCUMENTED_PROTOS[@]}"; do
        echo "    - prototypes/$proto/ (no README or CONCEPT doc)"
      done
      echo "    Suggested action: \$reverse-document concept prototypes/[name]"
    fi
  fi
fi

# --- Check 3: Core systems without architecture docs ---
# Matched by directory name rather than a fixed src/core path: Unity nests
# these as Assets/02.Scripts/Core/, Unreal as Source/<Game>/Core/.
CORE_DIRS=$(studio_find_subdir core engine Core Engine)
if [ -n "$CORE_DIRS" ]; then
  ADR_COUNT=0
  ADR_ROOT=""
  for candidate in "docs/architecture" "design/adr" "design/architecture"; do
    if [ -d "$candidate" ]; then
      [ -z "$ADR_ROOT" ] && ADR_ROOT="$candidate"
      n=$(find "$candidate" -type f -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
      ADR_COUNT=$((ADR_COUNT + n))
    fi
  done

  if [ -z "$ADR_ROOT" ]; then
    echo "⚠️  GAP: Core engine/systems exist but no architecture docs directory (looked for docs/architecture/, design/adr/)"
    echo "    Suggested action: Create design/adr/ and run \$architecture-decision"
  elif [ "$ADR_COUNT" -lt 3 ]; then
    FIRST_CORE=$(printf '%s\n' "$CORE_DIRS" | head -1)
    echo "⚠️  GAP: Core systems exist but only $ADR_COUNT ADR(s) documented in $ADR_ROOT/"
    echo "    Suggested action: \$reverse-document architecture $FIRST_CORE"
  fi
fi

# --- Check 4: Gameplay systems without design docs ---
GAMEPLAY_DIRS=$(studio_find_subdir gameplay Gameplay systems Systems)
if [ -n "$GAMEPLAY_DIRS" ]; then
  while IFS= read -r gameplay_root; do
    [ -n "$gameplay_root" ] || continue

    GAMEPLAY_SYSTEMS=$(find "$gameplay_root" -mindepth 1 -maxdepth 1 -type d 2>/dev/null)
    [ -n "$GAMEPLAY_SYSTEMS" ] || continue

    while IFS= read -r system_dir; do
      system_dir=$(echo "$system_dir" | sed 's|\\|/|g')
      system_name=$(basename "$system_dir")
      # .meta sidecars are not content — counting them doubles every Unity
      # directory and halves the effective 5-file threshold.
      file_count=$(find "$system_dir" -type f ! -name '*.meta' 2>/dev/null | wc -l)
      file_count=$(echo "$file_count" | tr -d ' ')

      # If system has 5+ files, check for a corresponding design doc
      if [ "$file_count" -ge 5 ]; then
        # Directory names are matched case-insensitively against doc names:
        # Unity's Combat/ should find design/gdd/combat-system.md.
        system_slug=$(echo "$system_name" | tr '[:upper:]' '[:lower:]')

        if ! studio_design_doc_exists "$system_name" && ! studio_design_doc_exists "$system_slug"; then
          echo "⚠️  GAP: Gameplay system '$system_dir/' ($file_count files) has no design doc"
          echo "    Expected: $PRIMARY_DESIGN_ROOT/${system_slug}-system.md or $PRIMARY_DESIGN_ROOT/${system_slug}.md"
          echo "    Suggested action: \$reverse-document design $system_dir"
        fi
      fi
    done <<< "$GAMEPLAY_SYSTEMS"
  done <<< "$GAMEPLAY_DIRS"
fi

# --- Check 5: Production planning ---
# The roots come from detect-layout.sh so a project that keeps its plans
# somewhere else can say so, the same way it already can for src/design/asset
# roots. They used to be hardcoded here, which made this the one check a
# project could not silence: a project whose planning lives in Documents/ got
# the warning every session while the same helper counted its design docs
# correctly.
PRODUCTION_ROOT_LIST=$(printf '%s' "$STUDIO_PRODUCTION_ROOTS" | tr '\n' ' ')
if [ "$SRC_FILES" -gt 100 ]; then
  # For projects with substantial code, check for production planning
  if ! studio_production_planning_exists; then
    echo "⚠️  GAP: Large codebase ($SRC_FILES files) but no production planning found"
    echo "    Looked in: $PRODUCTION_ROOT_LIST"
    echo "    Suggested action: \$sprint-plan, or set \"productionRoots\" in .codex/studio-layout.json"
  fi
fi

# --- Summary ---
echo ""
echo "💡 To get a comprehensive project analysis, run: \$project-stage-detect"
echo "==================================="

exit 0
