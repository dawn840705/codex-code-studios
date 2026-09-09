#!/usr/bin/env bash
# Shared project-layout detection for codex-code-studios hooks.
#
# WHY THIS FILE EXISTS
#   Hooks used to hardcode a lowercase web layout (src/, assets/, design/gdd/).
#   Unity forces Assets/ + ProjectSettings/ and keeps code under Assets/**/*.cs,
#   so every one of those hooks either silently skipped or misfired on Unity
#   projects. The same engine test was also copy-pasted per hook, which is how
#   they drifted apart in the first place. Detection lives here now — one place.
#
# USAGE
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   # shellcheck source=lib/detect-layout.sh
#   [ -f "$SCRIPT_DIR/lib/detect-layout.sh" ] && . "$SCRIPT_DIR/lib/detect-layout.sh"
#
#   Always guard the source with -f. A hook must never die because the helper
#   is missing; every consumer keeps a hardcoded fallback for that case.
#
# CONTRACT
#   Sourced, never executed. Never exits, never writes to stdout/stderr
#   (except when STUDIO_LAYOUT_DEBUG=1). Detection runs against $PWD, which for
#   Codex hooks is the user's project root — not the plugin root.
#
# EXPORTED VARIABLES
#   STUDIO_ENGINE        unity | godot | unreal | gamemaker | generic
#   STUDIO_SRC_ROOTS     newline-separated dirs holding first-party source
#   STUDIO_SRC_EXTS      space-separated extensions, no dot (e.g. "cs")
#   STUDIO_DESIGN_ROOTS  newline-separated dirs holding design/spec markdown
#   STUDIO_ASSET_ROOTS   newline-separated dirs holding art/data assets
#   STUDIO_PRODUCTION_ROOTS  newline-separated dirs holding sprint/milestone plans
#   STUDIO_ASSET_NAMING  pascal | snake | any  — file-naming convention to enforce
#   STUDIO_LAYOUT_SOURCE detected | config | env  — where the layout came from
#
# EXPORTED FUNCTIONS
#   studio_find_sources [max]      print source file paths (optionally capped)
#   studio_count_sources           print the source file count
#   studio_find_design_docs        print design .md paths across design roots
#   studio_count_design_docs       print the design .md count across design roots
#   studio_design_doc_exists <n>   exit 0 if <n>.md or <n>-system.md exists
#   studio_find_subdir <name...>   print source subdirs matching any given name
#   studio_is_engine_project       exit 0 if an engine project was detected
#   studio_src_ext_regex           print an extension alternation, e.g. "cs|gd"
#   studio_path_has_ext <path>     exit 0 if the path ends in a known source ext
#   studio_asset_root_regex        print an anchored asset-path regex
#   studio_naming_violation <name> print a reason if the file name breaks convention
#   studio_production_planning_exists  exit 0 if any production root exists
#
# OVERRIDES (highest priority first)
#   1. environment: STUDIO_ENGINE / STUDIO_SRC_ROOTS / STUDIO_SRC_EXTS /
#      STUDIO_DESIGN_ROOTS / STUDIO_ASSET_ROOTS / STUDIO_ASSET_NAMING /
#      STUDIO_PRODUCTION_ROOTS
#      (colon-separated for the list-valued ones)
#   2. .codex/studio-layout.json    — dedicated Codex project config
#   3. .claude/studio-layout.json   — legacy transition fallback
#   4. .claude/settings.json        — legacy transition fallback
#   Keys: engine, srcRoots, srcExtensions, designRoots, assetRoots, assetNaming,
#   productionRoots.
#   List values accept a JSON array or a colon-separated string. Without jq
#   installed only the string form is readable; arrays fall back to detection.
#   That jq caveat matters most for productionRoots: a project that moves its
#   planning docs and writes the override as an array will silently keep the
#   default on a machine without jq. Use the colon-separated string form to be
#   portable:  "productionRoots": "Documents/Plan:Documents/Queue"
#
# Cross-platform: Windows Git Bash compatible — grep -E only, never grep -P.

# Idempotent: sourcing twice in one process is a no-op.
if [ -n "${STUDIO_LAYOUT_LOADED:-}" ]; then
    return 0 2>/dev/null || exit 0
fi
STUDIO_LAYOUT_LOADED=1

studio__debug() {
    if [ "${STUDIO_LAYOUT_DEBUG:-0}" = "1" ]; then
        echo "[detect-layout] $*" >&2
    fi
    return 0
}

# --- config reading -------------------------------------------------------

# studio__json_get <file> <jq-path> <leaf-key>
# Reads a scalar or array value. jq when available, grep fallback otherwise.
studio__json_get() {
    studio__jg_file="$1"
    studio__jg_path="$2"
    studio__jg_leaf="$3"
    studio__jg_value=""

    [ -f "$studio__jg_file" ] || return 1

    if command -v jq >/dev/null 2>&1; then
        studio__jg_value=$(jq -r "($studio__jg_path) // empty | if type == \"array\" then join(\":\") else tostring end" \
                              "$studio__jg_file" 2>/dev/null)
    else
        studio__jg_value=$(grep -oE "\"$studio__jg_leaf\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" "$studio__jg_file" 2>/dev/null \
                           | head -1 \
                           | sed -E "s/.*:[[:space:]]*\"([^\"]*)\"/\1/")
    fi

    if [ -z "$studio__jg_value" ] || [ "$studio__jg_value" = "null" ]; then
        return 1
    fi
    printf '%s' "$studio__jg_value"
}

# studio__config_get <leaf-key> — Codex file first, then legacy fallbacks.
studio__config_get() {
    studio__cg_value=""
    if studio__cg_value=$(studio__json_get ".codex/studio-layout.json" ".$1" "$1"); then
        printf '%s' "$studio__cg_value"
        return 0
    fi
    if studio__cg_value=$(studio__json_get ".claude/studio-layout.json" ".$1" "$1"); then
        printf '%s' "$studio__cg_value"
        return 0
    fi
    if studio__cg_value=$(studio__json_get ".claude/settings.json" ".studio.layout.$1" "$1"); then
        printf '%s' "$studio__cg_value"
        return 0
    fi
    return 1
}

studio__colon_to_lines() {
    printf '%s' "$1" | tr ':' '\n' | grep -vE '^[[:space:]]*$'
}

# Keeps only the candidates that exist as directories. Reads stdin.
studio__existing_dirs() {
    while IFS= read -r studio__ed_dir; do
        [ -n "$studio__ed_dir" ] || continue
        if [ -d "$studio__ed_dir" ]; then
            printf '%s\n' "$studio__ed_dir"
        fi
    done
}

# --- engine detection -----------------------------------------------------
# Mirrors section 1 of hooks/detect-project-type.sh. Keep the two in sync;
# this one is the more specific (it names the engine, not just "game").

studio__detect_engine() {
    if [ -d "Assets" ] && [ -d "ProjectSettings" ]; then
        printf 'unity'; return 0
    fi
    if [ -f "project.godot" ]; then
        printf 'godot'; return 0
    fi
    if ls ./*.uproject >/dev/null 2>&1; then
        printf 'unreal'; return 0
    fi
    if ls ./*.yyp >/dev/null 2>&1; then
        printf 'gamemaker'; return 0
    fi
    printf 'generic'
    return 0
}

STUDIO_LAYOUT_SOURCE="detected"

if [ -n "${STUDIO_ENGINE:-}" ]; then
    STUDIO_LAYOUT_SOURCE="env"
elif STUDIO_ENGINE=$(studio__config_get "engine"); then
    STUDIO_LAYOUT_SOURCE="config"
else
    STUDIO_ENGINE=$(studio__detect_engine)
fi

# --- per-engine defaults --------------------------------------------------
# Design-root candidates are ordered but NOT exclusive: every candidate that
# exists is kept, because a Unity project commonly carries both a Documents/
# tree of its own and a design/gdd/ tree copied from the template.

case "$STUDIO_ENGINE" in
    unity)
        studio__def_src_roots="Assets"
        studio__def_src_exts="cs"
        studio__def_asset_roots="Assets"
        # Unity file names must match the C# class name, so PascalCase is the
        # convention — lowercase-with-underscores can never be enforced here.
        studio__def_asset_naming="pascal"
        studio__design_candidates="design/gdd
Documents
Docs
docs/design
docs/gdd
product/prd"
        ;;
    godot)
        studio__def_src_roots="."
        studio__def_src_exts="gd cs"
        studio__def_asset_roots="assets
Assets"
        studio__def_asset_naming="snake"
        studio__design_candidates="design/gdd
docs/design
docs/gdd
Documents
product/prd"
        ;;
    unreal)
        studio__def_src_roots="Source
Plugins"
        studio__def_src_exts="cpp h hpp"
        studio__def_asset_roots="Content"
        studio__def_asset_naming="pascal"
        studio__design_candidates="design/gdd
Documents
Docs
docs/design
product/prd"
        ;;
    gamemaker)
        studio__def_src_roots="scripts
objects"
        studio__def_src_exts="gml"
        studio__def_asset_roots="sprites
sounds
assets"
        studio__def_asset_naming="snake"
        studio__design_candidates="design/gdd
docs/design
Documents
product/prd"
        ;;
    *)
        # generic — the pre-existing web/app layout. src/ stays first so its
        # behaviour is unchanged; lib/app/packages are additive and only take
        # effect when they exist (monorepos, which detect-project-type.sh
        # already scans one level into).
        studio__def_src_roots="src
lib
app
packages"
        studio__def_src_exts="gd cs cpp c h hpp rs py js ts tsx jsx go java kt swift"
        studio__def_asset_roots="assets"
        studio__def_asset_naming="snake"
        studio__design_candidates="design/gdd
product/prd
docs/design
docs/gdd"
        ;;
esac

# --- resolve each setting: env > config > default -------------------------

# studio__resolve_list <env-value> <config-leaf> <default-newline-separated>
studio__resolve_list() {
    if [ -n "$1" ]; then
        studio__colon_to_lines "$1"
        return 0
    fi
    if studio__rl_cfg=$(studio__config_get "$2"); then
        studio__colon_to_lines "$studio__rl_cfg"
        return 0
    fi
    printf '%s\n' "$3"
}

# 엔진과 무관한 기본값. 템플릿이 만드는 경로다.
studio__def_production_roots="production/sprints
production/milestones"

STUDIO_SRC_ROOTS=$(studio__resolve_list "${STUDIO_SRC_ROOTS:-}" "srcRoots" "$studio__def_src_roots")
STUDIO_ASSET_ROOTS=$(studio__resolve_list "${STUDIO_ASSET_ROOTS:-}" "assetRoots" "$studio__def_asset_roots")

if [ -n "${STUDIO_SRC_EXTS:-}" ]; then
    STUDIO_SRC_EXTS=$(printf '%s' "$STUDIO_SRC_EXTS" | tr ':' ' ')
elif studio__tmp=$(studio__config_get "srcExtensions"); then
    STUDIO_SRC_EXTS=$(printf '%s' "$studio__tmp" | tr ':' ' ')
else
    STUDIO_SRC_EXTS="$studio__def_src_exts"
fi

if [ -z "${STUDIO_ASSET_NAMING:-}" ]; then
    if studio__tmp=$(studio__config_get "assetNaming"); then
        STUDIO_ASSET_NAMING="$studio__tmp"
    else
        STUDIO_ASSET_NAMING="$studio__def_asset_naming"
    fi
fi

case "$STUDIO_ASSET_NAMING" in
    pascal|snake|any) ;;
    *) STUDIO_ASSET_NAMING="$studio__def_asset_naming" ;;
esac

# Design roots: keep every candidate that actually exists. If none do, fall
# back to the canonical template path so downstream "0 design docs" messages
# still have a path to name.
if [ -n "${STUDIO_DESIGN_ROOTS:-}" ]; then
    STUDIO_DESIGN_ROOTS=$(studio__colon_to_lines "$STUDIO_DESIGN_ROOTS" | studio__existing_dirs)
elif studio__tmp=$(studio__config_get "designRoots"); then
    STUDIO_DESIGN_ROOTS=$(studio__colon_to_lines "$studio__tmp" | studio__existing_dirs)
else
    STUDIO_DESIGN_ROOTS=$(printf '%s\n' "$studio__design_candidates" | studio__existing_dirs)
fi
[ -n "$STUDIO_DESIGN_ROOTS" ] || STUDIO_DESIGN_ROOTS="design/gdd"

# Production planning roots. Engine-independent: where a project keeps its
# sprint / milestone / work-queue documents is a workflow choice, not an
# engine one. This used to be hardcoded inside detect-gaps.sh Check 5, which
# meant a project that keeps its plans anywhere else had no way to silence a
# false alarm it got every session — the one layout question left outside the
# override system that every other root already went through.
#
# Unlike design roots these are NOT filtered to existing dirs: Check 5 asks
# precisely whether any of them exists, so filtering would answer the question
# before it was asked.
STUDIO_PRODUCTION_ROOTS=$(studio__resolve_list \
    "${STUDIO_PRODUCTION_ROOTS:-}" "productionRoots" "$studio__def_production_roots")
[ -n "$STUDIO_PRODUCTION_ROOTS" ] || STUDIO_PRODUCTION_ROOTS="$studio__def_production_roots"

export STUDIO_ENGINE STUDIO_SRC_ROOTS STUDIO_SRC_EXTS STUDIO_DESIGN_ROOTS
export STUDIO_ASSET_ROOTS STUDIO_ASSET_NAMING STUDIO_LAYOUT_SOURCE
export STUDIO_PRODUCTION_ROOTS

studio__debug "engine=$STUDIO_ENGINE source=$STUDIO_LAYOUT_SOURCE naming=$STUDIO_ASSET_NAMING"
studio__debug "src_roots=$(printf '%s' "$STUDIO_SRC_ROOTS" | tr '\n' ',')"
studio__debug "design_roots=$(printf '%s' "$STUDIO_DESIGN_ROOTS" | tr '\n' ',')"

# --- find argument arrays -------------------------------------------------
# Built as arrays, never as strings: an unquoted "-name *.cs" string would be
# glob-expanded by the shell against $PWD before find ever sees it.

# Directories that are never first-party source. Unity's Library/ and Temp/
# alone hold tens of thousands of files — walking them would blow the hook
# timeout on any real project.
studio__prune_names=(.git node_modules Library Temp Logs UserSettings obj bin \
                     .godot Binaries Intermediate DerivedDataCache Saved \
                     Build build dist out .venv venv __pycache__ .next)

studio__PRUNE=()
for studio__p in "${studio__prune_names[@]}"; do
    if [ ${#studio__PRUNE[@]} -eq 0 ]; then
        studio__PRUNE=(-name "$studio__p")
    else
        studio__PRUNE+=(-o -name "$studio__p")
    fi
done

studio__SRC_NAMES=()
for studio__e in $STUDIO_SRC_EXTS; do
    if [ ${#studio__SRC_NAMES[@]} -eq 0 ]; then
        studio__SRC_NAMES=(-name "*.$studio__e")
    else
        studio__SRC_NAMES+=(-o -name "*.$studio__e")
    fi
done

# --- helper functions -----------------------------------------------------

studio_is_engine_project() {
    [ "$STUDIO_ENGINE" != "generic" ]
}

studio_src_ext_regex() {
    printf '%s' "$STUDIO_SRC_EXTS" | tr -s ' ' '\n' | grep -vE '^$' | tr '\n' '|' | sed 's/|$//'
}

studio_path_has_ext() {
    for studio__phe_ext in $STUDIO_SRC_EXTS; do
        case "$1" in
            *".$studio__phe_ext") return 0 ;;
        esac
    done
    return 1
}

# studio_find_sources [max] — source file paths under every source root.
studio_find_sources() {
    studio__fs_max="${1:-0}"
    [ ${#studio__SRC_NAMES[@]} -gt 0 ] || return 0

    while IFS= read -r studio__fs_root; do
        [ -n "$studio__fs_root" ] || continue
        [ -d "$studio__fs_root" ] || continue
        if [ "$studio__fs_max" -gt 0 ] 2>/dev/null; then
            find "$studio__fs_root" \( "${studio__PRUNE[@]}" \) -prune -o \
                 -type f \( "${studio__SRC_NAMES[@]}" \) -print 2>/dev/null | head -n "$studio__fs_max"
        else
            find "$studio__fs_root" \( "${studio__PRUNE[@]}" \) -prune -o \
                 -type f \( "${studio__SRC_NAMES[@]}" \) -print 2>/dev/null
        fi
    done <<EOF
$STUDIO_SRC_ROOTS
EOF
}

studio_count_sources() {
    studio_find_sources | wc -l | tr -d ' '
}

# studio_find_design_docs — every .md under every existing design root, pruned
# like the source walk. pre-compact.sh scans these for WIP markers.
studio_find_design_docs() {
    while IFS= read -r studio__fdd_root; do
        [ -n "$studio__fdd_root" ] || continue
        [ -d "$studio__fdd_root" ] || continue
        find "$studio__fdd_root" \( "${studio__PRUNE[@]}" \) -prune -o \
             -type f -name '*.md' -print 2>/dev/null
    done <<EOF
$STUDIO_DESIGN_ROOTS
EOF
}

studio_count_design_docs() {
    studio_find_design_docs | wc -l | tr -d ' '
}

# studio_design_doc_exists <basename-without-extension>
# Searches every design root recursively, case-insensitively, for <name>.md and
# its -system / _system / system variants. Recursive because design roots are
# rarely flat (Documents/Specs/CoverSystem.md); case-insensitive because the
# name usually arrives from a directory whose casing follows the engine's
# convention, not the document's.
studio_design_doc_exists() {
    studio__dde_name="$1"
    [ -n "$studio__dde_name" ] || return 1

    while IFS= read -r studio__dde_root; do
        [ -n "$studio__dde_root" ] || continue
        [ -d "$studio__dde_root" ] || continue
        studio__dde_hit=$(find "$studio__dde_root" \( "${studio__PRUNE[@]}" \) -prune -o -type f \
            \( -iname "${studio__dde_name}.md" \
               -o -iname "${studio__dde_name}-system.md" \
               -o -iname "${studio__dde_name}_system.md" \
               -o -iname "${studio__dde_name}system.md" \) -print 2>/dev/null | head -1)
        [ -n "$studio__dde_hit" ] && return 0
    done <<EOF
$STUDIO_DESIGN_ROOTS
EOF
    return 1
}

# studio_production_planning_exists — exit 0 if any production root is a
# directory. Check 5 of detect-gaps.sh asks this and nothing more.
studio_production_planning_exists() {
    while IFS= read -r studio__ppe_root; do
        [ -n "$studio__ppe_root" ] || continue
        [ -d "$studio__ppe_root" ] && return 0
    done <<EOF
$STUDIO_PRODUCTION_ROOTS
EOF
    return 1
}

# studio_find_subdir <name> [name...] — directories under the source roots
# whose basename matches any given name (case-sensitive, depth <= 3).
# Unity projects nest scripts under Assets/02.Scripts/Gameplay/, so a fixed
# "src/gameplay" path would never resolve.
studio_find_subdir() {
    [ $# -gt 0 ] || return 0

    studio__fsd_names=()
    for studio__fsd_n in "$@"; do
        if [ ${#studio__fsd_names[@]} -eq 0 ]; then
            studio__fsd_names=(-name "$studio__fsd_n")
        else
            studio__fsd_names+=(-o -name "$studio__fsd_n")
        fi
    done

    while IFS= read -r studio__fsd_root; do
        [ -n "$studio__fsd_root" ] || continue
        [ -d "$studio__fsd_root" ] || continue
        find "$studio__fsd_root" -maxdepth 3 \( "${studio__PRUNE[@]}" \) -prune -o \
             -type d \( "${studio__fsd_names[@]}" \) -print 2>/dev/null
    done <<EOF
$STUDIO_SRC_ROOTS
EOF
}

# studio_asset_root_regex — anchored alternation for matching asset paths,
# e.g. "(^|/)(Assets)/". Case-sensitive on purpose: Unity's Assets/ and the
# web layout's assets/ are different conventions carrying different naming
# rules, so matching case-insensitively would apply the wrong one.
studio_asset_root_regex() {
    studio__arr_alt=""
    while IFS= read -r studio__arr_root; do
        [ -n "$studio__arr_root" ] || continue
        studio__arr_root="${studio__arr_root%/}"
        if [ -z "$studio__arr_alt" ]; then
            studio__arr_alt="$studio__arr_root"
        else
            studio__arr_alt="$studio__arr_alt|$studio__arr_root"
        fi
    done <<EOF
$STUDIO_ASSET_ROOTS
EOF
    [ -n "$studio__arr_alt" ] || studio__arr_alt="assets"
    printf '(^|/)(%s)/' "$studio__arr_alt"
}

# studio_naming_violation <filename> — prints a reason, or nothing if the name
# is fine. Exit code mirrors that: 0 = violation found, 1 = clean.
studio_naming_violation() {
    case "$STUDIO_ASSET_NAMING" in
        any)
            return 1
            ;;
        pascal)
            # PascalCase engines (Unity, Unreal): uppercase and underscores are
            # normal — PlayerController.cs, CARD_MaxHP.asset. Only whitespace
            # and hyphens are genuinely hostile (they break C# class-name
            # matching and asset-path handling).
            if printf '%s' "$1" | grep -qE '[[:space:]]'; then
                printf 'contains whitespace — use PascalCase without spaces'
                return 0
            fi
            if printf '%s' "$1" | grep -qE '-'; then
                printf 'contains a hyphen — use PascalCase or underscores'
                return 0
            fi
            return 1
            ;;
        snake|*)
            if printf '%s' "$1" | grep -qE '[A-Z[:space:]-]'; then
                printf 'must be lowercase with underscores'
                return 0
            fi
            return 1
            ;;
    esac
}
