#!/usr/bin/env bash
# Codex PostToolUse hook: advise on direct Unity Animator string access.

set +e
[ -d "Assets" ] && [ -d "ProjectSettings" ] || exit 0

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -f "$SCRIPT_DIR/lib/hook-io.sh" ] || exit 0
# shellcheck source=lib/hook-io.sh
. "$SCRIPT_DIR/lib/hook-io.sh"

# <animator-ish receiver>.<Setter|Getter>("...") — first arg a literal string.
#
# 판단 축은 원래 수신자의 **타입**이 Animator 인가인데, bash 정규식은 타입을 모른다.
# 그래서 이름 휴리스틱을 쓴다 — 식별자에 `anim` 이 들어가면 Animator 로 본다.
# 이전 패턴은 수신자를 `animator` 로 못박아 뒀고 앞의 `\b` 때문에 밑줄·접두사가
# 붙은 이름에는 경계가 생기지 않아, 실제 프로젝트가 쓰는 5변형 중 1개만 잡았다
# (`_anim` · `_animator` · `playerAnimator` · `playerAnim` 이 전부 통과했다).
#
# 넓히면 오탐이 따라오므로 두 가지로 막는다:
#   - 첫 인자가 `"_` 로 시작하면 제외 = 셰이더 프로퍼티 관례.
#     `animMaterial.SetFloat("_BaseColor")` 같은 Material 호출을 살려준다.
#   - 수신자에 `anim` 이 없으면 애초에 안 잡힌다.
#     `EditorPrefs.SetBool(...)`, `serializedObject.SetBool("m_...")` 가 여기 해당.
#
# `GetComponent<Animator>()` 는 이름이 아니라 타입이 그 자리에 드러난 형태라
# 오탐 여지가 없어 함께 잡는다. 해시 접근(`SetBool(hash, ...)`)과 권장 해법인
# `Animator.StringToHash("...")` 는 따옴표·메서드가 달라 걸리지 않는다.
ANIM_STR_PAT='(\b[A-Za-z0-9_]*[Aa]nim[A-Za-z0-9_]*|GetComponent<Animator>\(\))\.(SetBool|SetInteger|SetFloat|SetTrigger|ResetTrigger|GetBool|GetInteger|GetFloat)\("[^_"]'
PATHS=$(studio_extract_changed_paths "$INPUT")
WARNINGS=""

# Findings per file are capped: the advice is one line, the evidence needs
# only enough to locate it.
MAX_FINDINGS=5

while IFS= read -r FILE_PATH; do
    case "$FILE_PATH" in
        *.cs) ;;
        *) continue ;;
    esac
    [ -f "$FILE_PATH" ] || continue

    if command -v rg >/dev/null 2>&1; then
        FINDINGS=$(rg -n --no-heading "$ANIM_STR_PAT" "$FILE_PATH" 2>/dev/null || true)
    else
        FINDINGS=$(grep -nE "$ANIM_STR_PAT" "$FILE_PATH" 2>/dev/null || true)
    fi

    if [ -n "$FINDINGS" ]; then
        TOTAL=$(printf '%s\n' "$FINDINGS" | grep -c .)
        SHOWN=$(printf '%s\n' "$FINDINGS" | head -n "$MAX_FINDINGS")
        if [ "$TOTAL" -gt "$MAX_FINDINGS" ]; then
            SHOWN="$SHOWN
... and $((TOTAL - MAX_FINDINGS)) more"
        fi
        WARNINGS="$WARNINGS
Unity Animator string access in $FILE_PATH:
$SHOWN
Cache parameters with Animator.StringToHash and pass the integer hash."
    fi
done <<< "$PATHS"

[ -n "$WARNINGS" ] && studio_emit_additional_context "$WARNINGS"
exit 0
