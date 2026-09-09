"""Tests for hooks/lib/detect-layout.sh and the three hooks that consume it.

The bug these cover: every path-sensitive hook hardcoded a lowercase web layout
(src/, assets/, design/gdd/). Unity forces Assets/ + ProjectSettings/ and keeps
code under Assets/**/*.cs, so on a real Unity project detect-gaps.sh reported
"NEW PROJECT" (and skipped checks 1-5 entirely), validate-commit.sh matched
nothing on every commit, and validate-assets.sh skipped every file — while its
lowercase-only naming rule sat there waiting to fire on PascalCase the moment
the path filter was fixed.

Both directions are asserted throughout: Unity projects must now be handled,
and generic/web projects must behave exactly as they did before.
"""

import json
import os
import shutil
import subprocess

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS = os.path.join(REPO, "hooks")
LIB = os.path.join(HOOKS, "lib", "detect-layout.sh")

DETECT_GAPS = os.path.join(HOOKS, "detect-gaps.sh")
VALIDATE_COMMIT = os.path.join(HOOKS, "validate-commit.sh")
VALIDATE_ASSETS = os.path.join(HOOKS, "validate-assets.sh")
PRE_COMPACT = os.path.join(HOOKS, "pre-compact.sh")
SESSION_START = os.path.join(HOOKS, "session-start.sh")
SKILL_CHANGE = os.path.join(HOOKS, "validate-skill-change.sh")
ANIMATOR_LINT = os.path.join(HOOKS, "unity-animator-string-lint.sh")

COMMIT_EVENT = json.dumps(
    {"tool_name": "Bash", "tool_input": {"command": 'git commit -m "test"'}}
)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def write(root, relpath, content=""):
    path = os.path.join(root, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


def run_hook(script, cwd, stdin="", env=None):
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run(
        ["bash", script],
        cwd=str(cwd),
        input=stdin,
        capture_output=True,
        text=True,
        # 훅은 UTF-8 로 찍는다(⚠️ 등). text=True 만 주면 locale.getencoding()
        # 을 타서 한국어 Windows 에서 디코딩하다 죽는다 — PYTHONIOENCODING 으로는
        # 안 고쳐지는 별개의 실패다 (tests/test_console_encoding.py 참조).
        encoding="utf-8",
        errors="replace",
        env=full_env,
    )


def probe(cwd, snippet, env=None, prelude=""):
    """Source the helper in `cwd` and run a shell snippet against it."""
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run(
        ["bash", "-c", f'{prelude}\n. "{LIB}"\n{snippet}'],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=full_env,
    )


# Shadows the `command` builtin so the helper believes jq is absent, which is
# the only way to exercise the grep fallback on a machine that has jq.
NO_JQ = (
    'command() { if [ "$1" = "-v" ] && [ "$2" = "jq" ]; then return 1; fi; '
    'builtin command "$@"; }'
)


def write_event(file_path):
    return json.dumps({"tool_name": "Write", "tool_input": {"file_path": file_path}})


def patch_event(*paths):
    command = "*** Begin Patch\n" + "\n".join(
        f"*** Update File: {path}" for path in paths
    ) + "\n*** End Patch"
    return json.dumps({"tool_name": "apply_patch", "tool_input": {"command": command}})


def hook_text(result):
    """Return model-visible hook context for advisory or blocking outcomes."""
    if result.stdout.strip():
        payload = json.loads(result.stdout)
        if "systemMessage" in payload:
            return payload["systemMessage"]
        return payload.get("hookSpecificOutput", {}).get("additionalContext", "")
    return result.stderr


def git_init(root):
    subprocess.run(["git", "init", "-q"], cwd=str(root), check=True,
                   capture_output=True, encoding="utf-8", errors="replace")
    for key, value in (("user.email", "t@example.com"), ("user.name", "t")):
        subprocess.run(["git", "config", key, value], cwd=str(root), check=True,
                       capture_output=True, encoding="utf-8", errors="replace")


def git_add_all(root):
    subprocess.run(["git", "add", "-A"], cwd=str(root), check=True,
                   capture_output=True, encoding="utf-8", errors="replace")


# --------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------

@pytest.fixture
def unity(tmp_path):
    """A mature Unity project: 60 scripts, 80 design docs, no src/ or design/gdd/."""
    root = tmp_path / "unity"
    os.makedirs(root / "ProjectSettings")
    for i in range(60):
        write(root, f"Assets/02.Scripts/Gameplay/Behaviour{i}.cs",
              f"public class Behaviour{i} {{}}\n")
    for i in range(80):
        write(root, f"Documents/Specs/Spec{i}.md", f"# Spec {i}\n")
    # Library/ holds tens of thousands of generated files in a real project.
    write(root, "Library/ScriptAssemblies/Generated.cs", "// generated\n")
    return root


@pytest.fixture
def web(tmp_path):
    """The layout every hook assumed before v0.6.2."""
    root = tmp_path / "web"
    for i in range(6):
        write(root, f"src/gameplay/combat/mod{i}.ts", f"export const a{i} = 1;\n")
    write(root, "design/gdd/combat-system.md", "# Combat\n")
    write(root, "assets/data/items.json", '{"ok": true}\n')
    return root


@pytest.fixture
def empty(tmp_path):
    root = tmp_path / "empty"
    os.makedirs(root)
    return root


# --------------------------------------------------------------------------
# detect-layout.sh — engine detection and layout resolution
# --------------------------------------------------------------------------

def test_helper_detects_unity(unity):
    out = probe(unity, 'echo "$STUDIO_ENGINE"').stdout.strip()
    assert out == "unity"


def test_helper_detects_generic_for_web(web):
    out = probe(web, 'echo "$STUDIO_ENGINE"').stdout.strip()
    assert out == "generic"


def test_helper_detects_godot(tmp_path):
    root = tmp_path / "g"
    write(root, "project.godot", "")
    assert probe(root, 'echo "$STUDIO_ENGINE"').stdout.strip() == "godot"


def test_helper_detects_unreal(tmp_path):
    root = tmp_path / "u"
    write(root, "MyGame.uproject", "{}")
    assert probe(root, 'echo "$STUDIO_ENGINE"').stdout.strip() == "unreal"


def test_helper_detects_gamemaker(tmp_path):
    root = tmp_path / "gm"
    write(root, "MyGame.yyp", "{}")
    assert probe(root, 'echo "$STUDIO_ENGINE"').stdout.strip() == "gamemaker"


def test_unity_source_count_excludes_library(unity):
    """Library/ and Temp/ are generated — counting them would also blow the
    SessionStart timeout on a real project."""
    assert probe(unity, "studio_count_sources").stdout.strip() == "60"


def test_unity_design_root_is_documents(unity):
    out = probe(unity, 'echo "$STUDIO_DESIGN_ROOTS"').stdout.strip()
    assert out == "Documents"
    assert probe(unity, "studio_count_design_docs").stdout.strip() == "80"


def test_design_roots_keep_every_existing_candidate(unity):
    """A Unity project can carry both its own Documents/ and a template gdd tree."""
    write(unity, "design/gdd/combat-system.md", "# Combat\n")
    roots = probe(unity, 'echo "$STUDIO_DESIGN_ROOTS"').stdout.split()
    assert set(roots) == {"design/gdd", "Documents"}


def test_design_roots_fall_back_to_canonical_path_when_none_exist(empty):
    assert probe(empty, 'echo "$STUDIO_DESIGN_ROOTS"').stdout.strip() == "design/gdd"


def test_generic_layout_unchanged(web):
    """src/ stays the primary root; assets/, snake and design/gdd are as before."""
    out = probe(web, 'echo "$STUDIO_ASSET_ROOTS|$STUDIO_ASSET_NAMING|'
                     '$STUDIO_DESIGN_ROOTS"').stdout.strip()
    assert out == "assets|snake|design/gdd"
    roots = probe(web, 'echo "$STUDIO_SRC_ROOTS"').stdout.split()
    assert roots[0] == "src"


def test_generic_monorepo_roots_are_additive(tmp_path):
    """packages/ counts, but only because it exists — src/ alone is unaffected."""
    root = tmp_path / "mono"
    write(root, "packages/api/index.ts", "export const a = 1;\n")
    write(root, "src/main.ts", "export const b = 2;\n")
    assert probe(root, "studio_count_sources").stdout.strip() == "2"


def test_naming_convention_is_per_engine(unity, web):
    assert probe(unity, 'echo "$STUDIO_ASSET_NAMING"').stdout.strip() == "pascal"
    assert probe(web, 'echo "$STUDIO_ASSET_NAMING"').stdout.strip() == "snake"


def test_find_subdir_handles_unity_nesting(unity):
    """Unity nests as Assets/02.Scripts/Gameplay/ — a fixed src/gameplay never resolves."""
    out = probe(unity, "studio_find_subdir Gameplay gameplay").stdout.strip()
    assert out == "Assets/02.Scripts/Gameplay"


def test_source_globs_are_not_shell_expanded(tmp_path):
    """An unquoted "-name *.cs" string would be glob-expanded against $PWD
    before find ever saw it, silently narrowing the search to one file."""
    root = tmp_path / "u"
    os.makedirs(root / "ProjectSettings")
    write(root, "Assets/A.cs", "")
    write(root, "Assets/B.cs", "")
    # A .cs file in the project root is what would poison the glob.
    write(root, "Decoy.cs", "")
    assert probe(root, "studio_count_sources").stdout.strip() == "2"


def test_naming_violation_pascal_allows_unity_conventions(unity):
    for name in ("PlayerController.cs", "CARD_MaxHP.asset", "Monster_Base.prefab"):
        result = probe(unity, f'studio_naming_violation "{name}"')
        assert result.stdout == "", f"{name} should be accepted under PascalCase"


def test_naming_violation_pascal_still_rejects_spaces_and_hyphens(unity):
    assert "whitespace" in probe(unity, 'studio_naming_violation "Bad Name.png"').stdout
    assert "hyphen" in probe(unity, 'studio_naming_violation "my-texture.png"').stdout


def test_naming_violation_snake_unchanged(web):
    assert "lowercase" in probe(web, 'studio_naming_violation "Hero.png"').stdout
    assert probe(web, 'studio_naming_violation "hero_idle.png"').stdout == ""


# --- overrides ------------------------------------------------------------

def test_env_override_wins(web):
    out = probe(web, 'echo "$STUDIO_ENGINE|$STUDIO_ASSET_NAMING|$STUDIO_LAYOUT_SOURCE"',
                env={"STUDIO_ENGINE": "unity", "STUDIO_ASSET_NAMING": "any"})
    assert out.stdout.strip() == "unity|any|env"


def test_env_override_of_design_roots_is_colon_separated(unity):
    write(unity, "Docs/Readme.md", "# hi\n")
    out = probe(unity, 'echo "$STUDIO_DESIGN_ROOTS"',
                env={"STUDIO_DESIGN_ROOTS": "Docs:Documents"})
    assert out.stdout.split() == ["Docs", "Documents"]


def test_codex_config_file_overrides_detection(unity):
    write(unity, ".codex/studio-layout.json",
          json.dumps({"assetNaming": "any", "designRoots": ["Documents"]}))
    out = probe(unity, 'echo "$STUDIO_ASSET_NAMING|$STUDIO_LAYOUT_SOURCE"')
    assert out.stdout.strip().startswith("any|")


def test_codex_config_wins_over_legacy_config(unity):
    write(unity, ".codex/studio-layout.json", '{"assetNaming": "any"}')
    write(unity, ".claude/studio-layout.json", '{"assetNaming": "snake"}')
    assert probe(unity, 'echo "$STUDIO_ASSET_NAMING"').stdout.strip() == "any"


@pytest.mark.skipif(shutil.which("jq") is None, reason="array config needs jq")
def test_settings_json_layout_block_is_read(unity):
    write(unity, ".claude/settings.json",
          json.dumps({"studio": {"layout": {"srcRoots": ["Assets/02.Scripts"]}}}))
    assert probe(unity, 'echo "$STUDIO_SRC_ROOTS"').stdout.strip() == "Assets/02.Scripts"


def test_string_config_values_are_readable_without_jq(unity):
    """No jq means the grep fallback, which understands scalars only."""
    write(unity, ".claude/studio-layout.json",
          '{\n  "assetNaming": "snake",\n  "designRoots": "Docs"\n}')
    write(unity, "Docs/Readme.md", "# hi\n")
    out = probe(unity, 'echo "$STUDIO_ASSET_NAMING|$STUDIO_DESIGN_ROOTS"', prelude=NO_JQ)
    assert out.stdout.strip() == "snake|Docs"


def test_array_config_without_jq_degrades_to_detection(unity):
    """An unreadable array must fall through to detection, never to garbage."""
    write(unity, ".claude/studio-layout.json", '{"designRoots": ["Docs"]}')
    out = probe(unity, 'echo "$STUDIO_DESIGN_ROOTS"', prelude=NO_JQ)
    assert out.stdout.strip() == "Documents"


def test_invalid_naming_value_falls_back_to_engine_default(unity):
    write(unity, ".claude/studio-layout.json", json.dumps({"assetNaming": "bogus"}))
    assert probe(unity, 'echo "$STUDIO_ASSET_NAMING"').stdout.strip() == "pascal"


def test_helper_is_idempotent_when_sourced_twice(web):
    result = probe(web, f'. "{LIB}"\necho "$STUDIO_ENGINE"')
    assert result.returncode == 0
    assert result.stdout.strip() == "generic"


def test_helper_is_silent_without_debug(web):
    result = probe(web, "true")
    assert result.stdout == ""
    assert result.stderr == ""


# --------------------------------------------------------------------------
# detect-gaps.sh
# --------------------------------------------------------------------------

def test_unity_project_is_not_reported_as_new(unity):
    """The headline bug: 60 scripts and 80 docs read as a fresh start."""
    result = run_hook(DETECT_GAPS, unity)
    assert result.returncode == 0
    assert "NEW PROJECT" not in result.stdout


def test_empty_project_is_still_reported_as_new(empty):
    result = run_hook(DETECT_GAPS, empty)
    assert "NEW PROJECT" in result.stdout


def test_bare_engine_scaffold_is_not_new(tmp_path):
    """Unity scaffolding only exists because someone created the project."""
    root = tmp_path / "bare"
    os.makedirs(root / "Assets")
    os.makedirs(root / "ProjectSettings")
    assert "NEW PROJECT" not in run_hook(DETECT_GAPS, root).stdout


def test_web_project_with_code_is_not_new(web):
    assert "NEW PROJECT" not in run_hook(DETECT_GAPS, web).stdout


def test_production_artifacts_rule_out_fresh(empty):
    """Nothing creates production/ by accident — this repo itself is the case
    that has no src/ at all yet is obviously not a fresh start."""
    write(empty, "production/session-logs/2026-07-31.md", "# log\n")
    assert "NEW PROJECT" not in run_hook(DETECT_GAPS, empty).stdout


def test_empty_production_directory_does_not_count(empty):
    os.makedirs(empty / "production")
    assert "NEW PROJECT" in run_hook(DETECT_GAPS, empty).stdout


def test_stack_signal_without_a_source_root_is_not_new(empty):
    """A web app that keeps its code in pages/ counts 0 sources under the known
    roots and was told to run $start every session. detect-project-type.sh
    still reads react out of package.json; its verdict, not the source count,
    decides whether the project is fresh."""
    write(empty, "package.json", '{"dependencies": {"react": "18"}}\n')
    write(empty, "pages/index.tsx", "export default () => null;\n")
    assert "NEW PROJECT" not in run_hook(DETECT_GAPS, empty).stdout


def test_track_file_alone_rules_out_fresh(empty):
    write(empty, "production/track.txt", "product\n")
    assert "NEW PROJECT" not in run_hook(DETECT_GAPS, empty).stdout


def test_unity_gap_checks_actually_run(unity):
    """Checks 1-5 were unreachable behind the fresh-project early exit."""
    shutil.rmtree(unity / "Documents")
    for i in range(6):
        write(unity, f"Assets/02.Scripts/Gameplay/Combat/C{i}.cs", "class C {}\n")
    write(unity, "Assets/02.Scripts/Core/Boot.cs", "class Boot {}\n")

    out = run_hook(DETECT_GAPS, unity).stdout
    assert "Substantial codebase" in out
    assert "Assets/02.Scripts/Gameplay/Combat/" in out
    assert "no architecture docs directory" in out


def test_web_gap_checks_unchanged(web):
    os.remove(web / "design" / "gdd" / "combat-system.md")
    write(web, "src/core/boot.ts", "export const boot = 1;\n")
    out = run_hook(DETECT_GAPS, web).stdout
    assert "src/gameplay/combat/" in out
    assert "no architecture docs directory" in out


def test_design_doc_presence_silences_the_gameplay_check(web):
    """design/gdd/combat-system.md covers src/gameplay/combat/."""
    out = run_hook(DETECT_GAPS, web).stdout
    assert "GAP" not in out


# --------------------------------------------------------------------------
# Check 5: production planning roots are overridable like every other root
# --------------------------------------------------------------------------
# lib/detect-layout.sh lets a project redeclare srcRoots / designRoots /
# assetRoots, but the production path was hardcoded inside Check 5 — so a
# project that keeps its plans elsewhere got the same false alarm every
# session with no way to turn it off, even while the same helper counted its
# design docs correctly.

@pytest.fixture
def big_codebase(tmp_path):
    """>100 source files — the threshold Check 5 fires above."""
    root = tmp_path / "big"
    for i in range(110):
        write(root, f"src/mod{i}.ts", f"export const a{i} = {i};\n")
    write(root, "design/gdd/combat-system.md", "# Combat\n")
    return root


PRODUCTION_GAP = "no production planning found"


def test_production_gap_fires_without_planning_docs(big_codebase):
    out = run_hook(DETECT_GAPS, big_codebase).stdout
    assert PRODUCTION_GAP in out
    # 어디를 봤는지 말해줘야 사용자가 끄는 법을 알 수 있다.
    assert "production/sprints" in out


def test_default_production_roots_still_silence_the_check(big_codebase):
    """기존 동작 회귀 방어 — 템플릿 경로는 그대로 통해야 한다."""
    os.makedirs(big_codebase / "production" / "sprints")
    out = run_hook(DETECT_GAPS, big_codebase).stdout
    assert PRODUCTION_GAP not in out


def test_production_roots_override_via_config(big_codebase):
    """계획을 Documents/ 에 두는 프로젝트가 경고를 끌 수 있다.

    콜론 구분 문자열로 쓴다 — jq 없는 환경에서는 배열 형식을 못 읽는다
    (lib/detect-layout.sh 헤더에 명시된 제약).
    """
    write(big_codebase, "Documents/Plan.md", "# Plan\n")
    write(big_codebase, ".claude/studio-layout.json",
          '{"productionRoots": "Documents"}\n')
    out = run_hook(DETECT_GAPS, big_codebase).stdout
    assert PRODUCTION_GAP not in out


def test_production_roots_override_via_env(big_codebase):
    write(big_codebase, "Documents/Plan.md", "# Plan\n")
    out = run_hook(DETECT_GAPS, big_codebase,
                   env={"STUDIO_PRODUCTION_ROOTS": "Documents"}).stdout
    assert PRODUCTION_GAP not in out


def test_production_roots_override_does_not_silence_a_missing_directory(big_codebase):
    """override 는 경고를 끄는 스위치가 아니라 볼 곳을 바꾸는 것이다."""
    out = run_hook(DETECT_GAPS, big_codebase,
                   env={"STUDIO_PRODUCTION_ROOTS": "Documents"}).stdout
    assert PRODUCTION_GAP in out
    assert "Documents" in out


def test_meta_sidecars_do_not_inflate_the_system_file_count(unity):
    """Every Unity asset has a .meta twin — counting both halves the threshold."""
    shutil.rmtree(unity / "Documents")
    for i in range(3):
        write(unity, f"Assets/02.Scripts/Gameplay/Cover/C{i}.cs", "class C {}\n")
        write(unity, f"Assets/02.Scripts/Gameplay/Cover/C{i}.cs.meta", "guid: x\n")
    out = run_hook(DETECT_GAPS, unity).stdout
    assert "Cover/" not in out, "3 scripts + 3 .meta must not read as 6 files"


def test_design_docs_are_found_in_nested_directories(unity):
    """Design roots are rarely flat — Documents/Specs/CoverSystem.md counts."""
    for i in range(6):
        write(unity, f"Assets/02.Scripts/Gameplay/Cover/C{i}.cs", "class C {}\n")
    write(unity, "Documents/Specs/CoverSystem.md", "# Cover\n")
    assert "Cover/" not in run_hook(DETECT_GAPS, unity).stdout


def test_design_doc_lookup_is_case_insensitive(unity):
    assert probe(unity, 'studio_design_doc_exists Cover && echo hit').stdout.strip() == ""
    write(unity, "Documents/cover-system.md", "# Cover\n")
    assert probe(unity, 'studio_design_doc_exists Cover && echo hit').stdout.strip() == "hit"


def test_adr_directory_satisfies_the_architecture_check(unity):
    write(unity, "Assets/02.Scripts/Core/Boot.cs", "class Boot {}\n")
    for i in range(3):
        write(unity, f"design/adr/adr-00{i}.md", f"# ADR {i}\n")
    out = run_hook(DETECT_GAPS, unity).stdout
    assert "architecture docs" not in out


def test_detect_gaps_survives_a_missing_helper(unity, tmp_path):
    """A broken install must not fail the session."""
    staged = tmp_path / "hooks_copy"
    os.makedirs(staged)
    shutil.copy(DETECT_GAPS, staged / "detect-gaps.sh")
    result = run_hook(str(staged / "detect-gaps.sh"), unity)
    assert result.returncode == 0
    assert "detect-layout.sh not found" in result.stdout


# --------------------------------------------------------------------------
# validate-commit.sh
# --------------------------------------------------------------------------

# The hardcoded-value scan is gated on production/track.txt == game: balance
# values belong in data files on a game, while `duration = 300` is ordinary
# product code. Fixtures that expect the warning declare the track.

def test_commit_hook_fires_on_unity_sources(unity):
    git_init(unity)
    write(unity, "production/track.txt", "game\n")
    write(unity, "Assets/02.Scripts/PlayerController.cs",
          "public class PlayerController {\n    // TODO: refactor\n    int health = 100;\n}\n")
    git_add_all(unity)

    result = run_hook(VALIDATE_COMMIT, unity, stdin=COMMIT_EVENT)
    assert result.returncode == 0
    assert "hardcoded gameplay values" in hook_text(result)
    assert "PlayerController.cs" in hook_text(result)


def test_commit_hook_still_fires_on_web_sources(web):
    git_init(web)
    write(web, "production/track.txt", "game\n")
    write(web, "src/gameplay/combat.ts", "// FIXME broken\nexport const damage = 12;\n")
    git_add_all(web)

    result = run_hook(VALIDATE_COMMIT, web, stdin=COMMIT_EVENT)
    assert "hardcoded gameplay values" in hook_text(result)
    assert "src/gameplay/combat.ts" in hook_text(result)


@pytest.mark.parametrize("track", ["product", None], ids=["product", "no-track-file"])
def test_commit_hook_skips_the_hardcoded_scan_off_the_game_track(web, track):
    """`duration = 300` on the product track is a timeout, not a balance value."""
    git_init(web)
    if track:
        write(web, "production/track.txt", track + "\n")
    write(web, "src/api/client.ts", "export const duration = 300;\n")
    git_add_all(web)

    result = run_hook(VALIDATE_COMMIT, web, stdin=COMMIT_EVENT)
    assert result.returncode == 0
    assert "hardcoded gameplay values" not in hook_text(result)


def test_commit_hook_no_longer_nags_about_todo_owner_tags(unity):
    """The TODO(name) style opinion is gone on every track."""
    git_init(unity)
    write(unity, "production/track.txt", "game\n")
    write(unity, "Assets/02.Scripts/Todo.cs",
          "public class Todo {\n    // TODO: later\n}\n")
    git_add_all(unity)
    result = run_hook(VALIDATE_COMMIT, unity, stdin=COMMIT_EVENT)
    assert result.returncode == 0
    assert "TODO/FIXME" not in hook_text(result)


def test_commit_hook_blocks_invalid_json_under_unity_assets(unity):
    git_init(unity)
    write(unity, "Assets/Resources/cards.json", '{"a":')
    git_add_all(unity)

    result = run_hook(VALIDATE_COMMIT, unity, stdin=COMMIT_EVENT)
    assert result.returncode == 2
    assert "not valid JSON" in result.stderr


def test_commit_hook_blocks_invalid_json_in_web_layout(web):
    git_init(web)
    write(web, "assets/data/broken.json", '{"a":')
    git_add_all(web)
    assert run_hook(VALIDATE_COMMIT, web, stdin=COMMIT_EVENT).returncode == 2


def test_commit_hook_enforces_gdd_sections_in_canonical_path(web):
    git_init(web)
    git_add_all(web)
    result = run_hook(VALIDATE_COMMIT, web, stdin=COMMIT_EVENT)
    assert "missing required section: Player Fantasy" in hook_text(result)


def test_commit_hook_ignores_ordinary_docs_outside_the_gdd_path(unity):
    """Documents/ is a general doc tree — not every note owes a Player Fantasy."""
    git_init(unity)
    write(unity, "Documents/Meeting.md", "# Standup\n\nWe talked about things.\n")
    git_add_all(unity)
    assert "missing required section" not in run_hook(
        VALIDATE_COMMIT, unity, stdin=COMMIT_EVENT).stderr


def test_commit_hook_enforces_sections_on_gdd_shaped_docs_anywhere(unity):
    """Three sections present means someone was writing a GDD — finish it."""
    git_init(unity)
    write(unity, "Documents/Specs/CombatSpec.md",
          "# Combat\n\n## Overview\nx\n\n## Dependencies\ny\n\n## Formulas\nz\n")
    git_add_all(unity)
    result = run_hook(VALIDATE_COMMIT, unity, stdin=COMMIT_EVENT)
    assert "missing required section: Player Fantasy" in hook_text(result)


def test_commit_hook_ignores_non_commit_commands(unity):
    git_init(unity)
    write(unity, "Assets/02.Scripts/Bad.cs", "// TODO: x\nint damage = 5;\n")
    git_add_all(unity)
    event = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git status"}})
    result = run_hook(VALIDATE_COMMIT, unity, stdin=event)
    assert result.returncode == 0
    assert result.stderr == ""


def test_commit_hook_produces_valid_codex_json(unity):
    git_init(unity)
    write(unity, "production/track.txt", "game\n")
    write(unity, "Assets/02.Scripts/Noisy.cs", "// TODO: x\nint damage = 5;\n")
    git_add_all(unity)
    result = run_hook(VALIDATE_COMMIT, unity, stdin=COMMIT_EVENT)
    payload = json.loads(result.stdout)
    assert "hardcoded gameplay values" in payload["systemMessage"]


# --------------------------------------------------------------------------
# validate-assets.sh
# --------------------------------------------------------------------------

@pytest.mark.parametrize("name", [
    "Assets/Art/PlayerController.cs",
    "Assets/Data/CARD_MaxHP.asset",
    "Assets/Prefabs/Monster_Base.prefab",
])
def test_unity_pascal_names_are_accepted(unity, name):
    """Fixing the path match alone would have warned on every one of these."""
    result = run_hook(VALIDATE_ASSETS, unity, stdin=write_event(name))
    assert result.returncode == 0
    assert result.stderr == ""


@pytest.mark.parametrize("name,reason", [
    ("Assets/Art/Bad Name.png", "whitespace"),
    ("Assets/Art/my-texture.png", "hyphen"),
])
def test_unity_still_rejects_spaces_and_hyphens(unity, name, reason):
    result = run_hook(VALIDATE_ASSETS, unity, stdin=write_event(name))
    assert result.returncode == 0
    assert reason in hook_text(result)


def test_web_naming_rule_unchanged(web):
    result = run_hook(VALIDATE_ASSETS, web, stdin=write_event("assets/Sprites/Hero.png"))
    assert "must be lowercase with underscores" in hook_text(result)
    assert run_hook(VALIDATE_ASSETS, web,
                    stdin=write_event("assets/sprites/hero.png")).stderr == ""


def test_files_outside_asset_roots_are_skipped(unity):
    assert run_hook(VALIDATE_ASSETS, unity, stdin=write_event("src/foo.ts")).stderr == ""


def test_meta_sidecars_are_skipped(unity):
    event = write_event("Assets/Art/Bad Name.png.meta")
    assert run_hook(VALIDATE_ASSETS, unity, stdin=event).stderr == ""


def test_invalid_json_blocks_under_unity_assets(unity):
    write(unity, "Assets/Resources/cards.json", '{"a":')
    result = run_hook(VALIDATE_ASSETS, unity, stdin=write_event("Assets/Resources/cards.json"))
    assert result.returncode == 2
    assert "not valid JSON" in result.stderr


def test_invalid_json_blocks_in_web_layout(web):
    write(web, "assets/data/bad.json", '{"a":')
    result = run_hook(VALIDATE_ASSETS, web, stdin=write_event("assets/data/bad.json"))
    assert result.returncode == 2


def test_blocking_exit_is_2_not_1(web):
    """Regression guard for the v0.6.3 fix.

    Until v0.6.3 this hook exited 1 on invalid JSON while printing
    "ERRORS (Blocking)". The Codex migration preserves exit 2 as the blocking
    path and returns model-visible JSON context for advisory results. Because
    this is a PostToolUse hook the write has already landed, a blocking result
    must make the failed tool result explicit.
    """
    write(web, "assets/data/broken.json", "{ not json")
    result = run_hook(VALIDATE_ASSETS, web, stdin=write_event("assets/data/broken.json"))
    assert result.returncode == 2, (
        "invalid JSON must exit 2 so Codex treats the tool result as blocked"
    )
    assert "1" != str(result.returncode)


def test_naming_violations_never_block(web):
    """The other half of the contract: style opinions stay advisory (exit 0)."""
    result = run_hook(VALIDATE_ASSETS, web, stdin=write_event("assets/Sprites/Hero.png"))
    assert result.returncode == 0
    assert "must be lowercase with underscores" in hook_text(result)


def test_valid_json_passes(web):
    result = run_hook(VALIDATE_ASSETS, web, stdin=write_event("assets/data/items.json"))
    assert result.returncode == 0


def test_empty_file_path_is_skipped(unity):
    event = json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}})
    result = run_hook(VALIDATE_ASSETS, unity, stdin=event)
    assert result.returncode == 0
    assert result.stderr == ""


def test_assets_hook_survives_a_missing_helper(tmp_path):
    """An incomplete installation must not fail the tool call."""
    staged = tmp_path / "hooks_copy"
    os.makedirs(staged)
    shutil.copy(VALIDATE_ASSETS, staged / "validate-assets.sh")
    project = tmp_path / "proj"
    write(project, "assets/data/items.json", "{}")

    result = run_hook(str(staged / "validate-assets.sh"), project,
                      stdin=write_event("assets/Sprites/Hero.png"))
    assert result.returncode == 0
    assert result.stdout == ""


# --------------------------------------------------------------------------
# the two Unity hooks that already worked — guard against regression
# --------------------------------------------------------------------------

def test_unity_meta_check_still_flags_missing_meta(unity):
    write(unity, "Assets/02.Scripts/New.cs", "public class New {}\n")
    result = run_hook(os.path.join(HOOKS, "unity-meta-check.sh"), unity,
                      stdin=write_event("Assets/02.Scripts/New.cs"))
    assert result.returncode == 0
    assert "Missing Unity sidecar" in hook_text(result)


def test_unity_meta_check_still_skips_non_unity_projects(web):
    result = run_hook(os.path.join(HOOKS, "unity-meta-check.sh"), web,
                      stdin=write_event("src/foo.cs"))
    assert result.returncode == 0
    assert result.stderr == ""


def test_animator_lint_still_flags_string_access(unity):
    write(unity, "Assets/02.Scripts/Anim.cs",
          'void Update() { animator.SetBool("IsRunning", true); }\n')
    result = run_hook(os.path.join(HOOKS, "unity-animator-string-lint.sh"), unity,
                      stdin=write_event("Assets/02.Scripts/Anim.cs"))
    assert result.returncode == 0
    assert "Unity Animator string access" in hook_text(result)


def test_animator_lint_caps_findings_per_file(unity):
    """Five lines locate the problem; the rest is a count."""
    calls = "".join('void F%d() { animator.SetBool("P%d", true); }\n' % (i, i)
                    for i in range(8))
    write(unity, "Assets/02.Scripts/Anim.cs", calls)
    text = hook_text(run_hook(ANIMATOR_LINT, unity,
                              stdin=write_event("Assets/02.Scripts/Anim.cs")))
    assert text.count("animator.SetBool") == 5
    assert "... and 3 more" in text


# 이 훅이 강제하는 규칙은 「Animator 파라미터는 해시로 접근」이다. 그런데 패턴이
# 수신자 이름을 `animator` 로 못박아 둬서, 실제 프로젝트가 쓰는 이름 5변형 중
# 1개만 잡았다 — 훅이 조용했던 건 잘 잡아서가 아니라 잡을 게 없어서였다.
# 넓히는 쪽과 오탐을 늘리지 않는 쪽을 양방향으로 건다.

ANIMATOR_RECEIVERS = [
    ("_anim", '_anim.SetBool("IsRunning", true);'),
    ("_animator", '_animator.SetTrigger("Attack");'),
    ("playerAnimator", 'playerAnimator.SetFloat("Speed", 1f);'),
    ("playerAnim", 'playerAnim.SetInteger("State", 2);'),
    ("animator", 'animator.SetBool("IsRunning", true);'),
    ("GetComponent<Animator>()", 'GetComponent<Animator>().SetTrigger("Hit");'),
]


@pytest.mark.parametrize("name,call", ANIMATOR_RECEIVERS,
                         ids=[n for n, _ in ANIMATOR_RECEIVERS])
def test_animator_lint_catches_every_receiver_name(unity, name, call):
    write(unity, "Assets/02.Scripts/Anim.cs", "void Update() { %s }\n" % call)
    result = run_hook(os.path.join(HOOKS, "unity-animator-string-lint.sh"), unity,
                      stdin=write_event("Assets/02.Scripts/Anim.cs"))
    assert result.returncode == 0
    assert "Unity Animator string access" in hook_text(result), (
        "수신자 이름이 %s 이면 린트가 놓친다. 이름을 `animator` 로 못박은 회귀." % name
    )


NON_ANIMATOR_CALLS = [
    # Material 셰이더 프로퍼티 — 첫 인자가 `"_` 로 시작한다.
    ("material", 'mat.SetFloat("_BaseColor", 1f);'),
    # 수신자에 anim 이 들어가도 셰이더 프로퍼티면 통과해야 한다.
    ("anim-named-material", 'animMaterial.SetFloat("_Glow", 1f);'),
    # 에디터 설정 저장.
    ("editor-prefs", 'EditorPrefs.SetBool("MyPref", true);'),
    # SerializedObject 계열 — StarDiver KoreanFontBaker.cs:332 형태.
    ("serialized-property", 'serializedFontAsset.SetBool("m_IsMultiAtlasTextures", true);'),
    # 이 훅이 권장하는 해법 자체를 잡으면 안 된다.
    ("hash-access", 'animator.SetBool(IsRunningHash, true);'),
    ("string-to-hash", 'int h = Animator.StringToHash("IsRunning");'),
]


@pytest.mark.parametrize("name,call", NON_ANIMATOR_CALLS,
                         ids=[n for n, _ in NON_ANIMATOR_CALLS])
def test_animator_lint_does_not_flag_non_animator_calls(unity, name, call):
    write(unity, "Assets/02.Scripts/Other.cs", "void Update() { %s }\n" % call)
    result = run_hook(os.path.join(HOOKS, "unity-animator-string-lint.sh"), unity,
                      stdin=write_event("Assets/02.Scripts/Other.cs"))
    assert result.returncode == 0
    assert "Unity Animator string access" not in hook_text(result), (
        "%s 는 Animator 호출이 아닌데 잡혔다 — 넓히면서 오탐이 늘었다." % name
    )


# --------------------------------------------------------------------------
# pre-compact.sh — capped, layout-aware, no nag for a missing state file
# --------------------------------------------------------------------------

def test_pre_compact_caps_the_file_list(web):
    git_init(web)
    for i in range(40):
        write(web, f"scratch/n{i}.txt", "x\n")
    text = hook_text(run_hook(PRE_COMPACT, web, stdin="{}"))
    listed = [ln for ln in text.splitlines() if ln.startswith("  - ")]
    assert len(listed) == 30
    # 8 fixture files + 40 scratch files, 30 shown.
    assert "... and 18 more" in text


def test_pre_compact_scans_wip_markers_across_design_roots(unity):
    """The WIP scan globbed design/gdd/*.md; Unity keeps its docs in Documents/."""
    git_init(unity)
    write(unity, "Documents/Specs/Cover.md", "# Cover\n\nTODO: decide the peek rule\n")
    text = hook_text(run_hook(PRE_COMPACT, unity, stdin="{}"))
    assert "Documents/Specs/Cover.md:3:TODO" in text


def test_pre_compact_caps_wip_rows(web):
    git_init(web)
    write(web, "design/gdd/big.md", "".join(f"TODO {i}\n" for i in range(45)))
    text = hook_text(run_hook(PRE_COMPACT, web, stdin="{}"))
    assert text.count("design/gdd/big.md:") == 30
    assert "... and 15 more" in text


def test_pre_compact_does_not_nag_about_a_missing_state_file(web):
    git_init(web)
    text = hook_text(run_hook(PRE_COMPACT, web, stdin="{}"))
    assert "No active session state" not in text
    assert "Consider maintaining" not in text
    assert "=== END SESSION STATE ===" in text


# --------------------------------------------------------------------------
# validate-skill-change.sh — once per skill per session
# --------------------------------------------------------------------------

def skill_event(session_id, path="skills/foo/SKILL.md"):
    event = {"tool_name": "Write", "tool_input": {"file_path": path}}
    if session_id:
        event["session_id"] = session_id
    return json.dumps(event)


@pytest.fixture
def scratch_env(tmp_path):
    """Isolates the marker files the hook keeps under $TMPDIR."""
    scratch = tmp_path / "scratch"
    os.makedirs(scratch)
    return {"TMPDIR": str(scratch)}


def test_skill_notice_fires_once_per_session(empty, scratch_env):
    first = run_hook(SKILL_CHANGE, empty, stdin=skill_event("s1"), env=scratch_env)
    assert "skill modified: foo" in hook_text(first)
    assert "$skill-test static" in hook_text(first)
    second = run_hook(SKILL_CHANGE, empty, stdin=skill_event("s1"), env=scratch_env)
    assert second.returncode == 0
    assert second.stdout == ""


def test_skill_notice_fires_again_for_another_skill_or_session(empty, scratch_env):
    run_hook(SKILL_CHANGE, empty, stdin=skill_event("s1"), env=scratch_env)
    other = run_hook(SKILL_CHANGE, empty,
                     stdin=skill_event("s1", "skills/bar/SKILL.md"), env=scratch_env)
    assert "skill modified: bar" in hook_text(other)
    assert "foo" not in hook_text(other)
    new_session = run_hook(SKILL_CHANGE, empty, stdin=skill_event("s2"), env=scratch_env)
    assert "skill modified: foo" in hook_text(new_session)


def test_skill_notice_without_a_session_id_fires_every_time(empty, scratch_env):
    for _ in range(2):
        result = run_hook(SKILL_CHANGE, empty, stdin=skill_event(None), env=scratch_env)
        assert "skill modified: foo" in hook_text(result)


# --------------------------------------------------------------------------
# session-start.sh — rule summaries, no ledger nag
# --------------------------------------------------------------------------

def test_session_start_prints_the_autonomy_contract(empty):
    out = run_hook(SESSION_START, empty, stdin="{}").stdout
    assert "=== Autonomy Contract (always active) ===" in out
    assert "Default is proceed." in out
    assert "rules/autonomy-contract.md" in out


def test_session_start_is_silent_about_a_missing_lesson_ledger(empty):
    out = run_hook(SESSION_START, empty, stdin="{}").stdout
    assert "Lesson Ledger" not in out
    assert "not initialized" not in out
    write(empty, "Documents/Lessons/LES-001.md", "# Lesson\n")
    out = run_hook(SESSION_START, empty, stdin="{}").stdout
    assert "Lesson Ledger: 1 lessons recorded" in out


# --------------------------------------------------------------------------
# plugin manifest
# --------------------------------------------------------------------------

def test_post_tool_use_matcher_includes_codex_apply_patch():
    hook_config = os.path.join(REPO, "hooks", "hooks.json")
    with open(hook_config, encoding="utf-8") as fh:
        data = json.load(fh)
    matchers = [entry["matcher"] for entry in data["hooks"]["PostToolUse"]]
    assert all("apply_patch" in m for m in matchers), matchers


def test_apply_patch_paths_are_validated(web):
    result = run_hook(
        VALIDATE_ASSETS,
        web,
        stdin=patch_event("src/clean.ts", "assets/Sprites/Hero.png"),
    )
    assert result.returncode == 0
    assert "must be lowercase with underscores" in hook_text(result)


def test_every_layout_aware_hook_sources_the_helper():
    for script in (DETECT_GAPS, VALIDATE_COMMIT, VALIDATE_ASSETS, PRE_COMPACT):
        with open(script, encoding="utf-8") as fh:
            body = fh.read()
        assert "lib/detect-layout.sh" in body, script
        # The source must be guarded — a missing helper cannot kill a hook.
        assert '-f "$SCRIPT_DIR/lib/detect-layout.sh"' in body, script


def test_no_hook_uses_perl_grep():
    """Windows Git Bash ships grep without -P."""
    scripts = [os.path.join(HOOKS, n) for n in os.listdir(HOOKS) if n.endswith(".sh")]
    scripts.append(LIB)
    for path in scripts:
        with open(path, encoding="utf-8") as fh:
            code = [ln for ln in fh if not ln.lstrip().startswith("#")]
        for line in code:
            assert "grep -P" not in line, (path, line)
            assert "grep -qP" not in line, (path, line)
