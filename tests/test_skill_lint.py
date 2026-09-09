"""scripts/lint_skills.py 단위 테스트.

린터가 CI 게이트인 이상 린터 자신도 검증돼야 한다. 특히 baseline 로직은
"기존 부채는 통과시키되 신규 위반은 막는다"는 비대칭 동작이라, 어느 쪽이
깨져도 조용하다 — 신규를 못 막으면 게이트가 무의미해지고, 기존을 막으면
CI가 상시 빨간불이 된다. 양방향을 모두 단언한다.

`python3 -m unittest` 와 pytest 양쪽에서 동작.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

import lint_skills as ls  # noqa: E402


# description 도 검사 대상(Check 8·10)이므로, 이 픽스처는 "잘 쓰인 description"
# 의 본보기여야 한다 — 언제 쓰는지(trigger)와 언제 쓰지 않는지(negative)를 모두 담는다.
GOOD_SKILL = """---
name: good-skill
description: "Use this skill when the user asks to verify a target. Do NOT use it for unrelated reporting tasks."
---

# Good Skill

## Phase 1: Do the thing

Body.

## Phase 2: Report

Emit PASS or FAIL.

## Recommended next

Run `$other-skill`.
"""


def _write_skill(root: str, name: str, text: str) -> str:
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "SKILL.md")
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


class TestFrontmatter(unittest.TestCase):
    def test_parses_top_level_scalars(self):
        fm = ls.parse_frontmatter(GOOD_SKILL)
        self.assertEqual(fm["name"], "good-skill")
        self.assertEqual(set(fm), {"name", "description"})

    def test_missing_block_returns_none(self):
        self.assertIsNone(ls.parse_frontmatter("# No frontmatter\n\nbody"))

    def test_indented_keys_are_ignored(self):
        # 중첩 키를 최상위로 잘못 읽으면 필수 필드 검사가 통과해 버린다.
        text = "---\nname: x\nnested:\n  name: should-not-leak\n---\nbody"
        fm = ls.parse_frontmatter(text)
        self.assertEqual(fm["name"], "x")
        self.assertNotIn("should-not-leak", fm.values())


class TestChecks(unittest.TestCase):
    def test_well_formed_skill_has_no_failures(self):
        # 쓰기 범위 선언이 없어 Check 4 는 WARN 이 남는다(설계된 동작). failures 만 0.
        r = ls.lint_skill("good/SKILL.md", GOOD_SKILL)
        self.assertEqual(r.failures, [], f"unexpected failures: {r.failures}")
        self.assertEqual(r.verdict, "WARNINGS")

    def test_fully_compliant_skill(self):
        text = GOOD_SKILL.replace("Body.", "Body. Writes the result to `production/qa/result.md`.")
        r = ls.lint_skill("good/SKILL.md", text)
        self.assertEqual(r.failures, [])
        self.assertEqual(r.warnings, [])
        self.assertEqual(r.verdict, "COMPLIANT")

    def test_check1_missing_fields(self):
        text = "---\nname: x\n---\n\n## Phase 1\n\n## Phase 2\n\nPASS\n"
        r = ls.lint_skill("x/SKILL.md", text)
        self.assertTrue(any("Check 1" in f for f in r.failures))

    def test_check2_needs_two_phases(self):
        text = GOOD_SKILL.replace("## Phase 2: Report", "").replace("## Recommended next", "")
        r = ls.lint_skill("x/SKILL.md", text)
        self.assertTrue(any("Check 2" in f for f in r.failures))

    def test_check3_needs_verdict_keyword(self):
        text = GOOD_SKILL.replace("Emit PASS or FAIL.", "Emit something.")
        r = ls.lint_skill("x/SKILL.md", text)
        self.assertTrue(any("Check 3" in f for f in r.failures))

    def test_check4_missing_write_boundary_warns(self):
        r = ls.lint_skill("x/SKILL.md", GOOD_SKILL)
        self.assertTrue(any("Check 4" in w for w in r.warnings))
        self.assertFalse(any("Check 4" in f for f in r.failures))

    # Check 4 는 "쓰기 범위 선언" 검사다 (v0.8.0 A-2). 어느 경로에 쓰는지 밝히거나
    # read-only 임을 밝히면 통과. 허락을 구하는 문구는 범위를 말하지 않으므로 통과가 아니다.
    def test_check4_path_declaration_passes(self):
        for phrase in ("Writes: `production/qa/report.md`.",
                       "Write the ADR to `docs/architecture/adr-0001.md`.",
                       "**Output:** `design/gdd/[system].md`",
                       "`Documents/Lessons/INDEX.md` 를 작성한다.",
                       "결과를 `production/qa/smoke.md`에 저장한다.",
                       "## Output\n\nThe report."):
            r = ls.lint_skill("x/SKILL.md", GOOD_SKILL.replace("Body.", phrase))
            self.assertFalse(any("Check 4" in w for w in r.warnings), phrase)

    def test_check4_ask_language_alone_still_warns(self):
        for phrase in ("May I write this to the file?",
                       "Ask before writing.",
                       "Get approval before creating the file.",
                       # 동사 어간이 아닌 단어(product/production, creative-director)와
                       # 빈 백틱 경로(` / `)는 선언으로 치지 않는다.
                       "Production artifacts live under `production/`.",
                       "Spawn `creative-director` with gate AD-1 (`../../docs/director-gates.md`).",
                       "Hook `Update()` / `FixedUpdate()` — never write here."):
            r = ls.lint_skill("x/SKILL.md", GOOD_SKILL.replace("Body.", phrase))
            self.assertTrue(any("Check 4" in w for w in r.warnings), phrase)
            self.assertFalse(any("Check 4" in f for f in r.failures), phrase)

    def test_check4_read_only_declaration_passes(self):
        for phrase in ("Read-only: writes nothing.",
                       "This skill is read-only — no files are written.",
                       "This orchestrator does not write files directly.",
                       "이 스킬은 파일을 쓰지 않는다."):
            r = ls.lint_skill("x/SKILL.md", GOOD_SKILL.replace("Body.", phrase))
            self.assertFalse(any("Check 4" in w for w in r.warnings), phrase)
        # API 호출 종류를 나열한 "Read-only / metadata calls" 는 스킬에 대한 선언이 아니다.
        r = ls.lint_skill("x/SKILL.md", GOOD_SKILL.replace(
            "Body.", "- **Read-only / metadata calls** — fetching credit balance."))
        self.assertTrue(any("Check 4" in w for w in r.warnings))

    def test_check5_missing_handoff_warns(self):
        text = GOOD_SKILL.replace("## Recommended next\n\nRun `$other-skill`.\n", "")
        r = ls.lint_skill("x/SKILL.md", text)
        self.assertTrue(any("Check 5" in w for w in r.warnings))


class TestRoleChecks(unittest.TestCase):
    def test_role_requires_name_and_description(self):
        text = "---\nname: a\n---\nbody"
        r = ls.lint_role("roles/a.md", text)
        self.assertTrue(any("description" in f for f in r.failures))

    def test_complete_role_passes(self):
        text = "---\nname: a\ndescription: d\n---\nbody"
        r = ls.lint_role("roles/a.md", text)
        self.assertEqual(r.failures, [])


class TestBaseline(unittest.TestCase):
    """비대칭 동작 양방향 — 기존 부채는 통과, 신규 위반은 차단."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.skills = os.path.join(self.root, "skills")
        os.makedirs(self.skills)
        self.baseline = os.path.join(self.root, "baseline.json")

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, *args) -> int:
        return ls.main(list(args))

    def test_known_failure_is_tolerated_but_new_one_is_not(self):
        broken = "---\nname: broken\ndescription: d\n---\n\nbody with no phases\n"
        _write_skill(self.skills, "broken", broken)

        # baseline 없이는 실패
        self.assertEqual(self._run(self.skills, "--quiet"), 1)

        # baseline 을 뜨면 통과
        self.assertEqual(self._run(self.skills, "--write-baseline", self.baseline), 0)
        self.assertEqual(self._run(self.skills, "--quiet", "--baseline", self.baseline), 0)

        # 새 위반이 추가되면 다시 차단
        _write_skill(self.skills, "broken2", broken.replace("broken", "broken2"))
        self.assertEqual(self._run(self.skills, "--quiet", "--baseline", self.baseline), 1)

    def test_baselined_entry_that_gets_worse_is_blocked(self):
        """failure 목록이 달라지면 baseline 과 불일치 → 차단."""
        text = "---\nname: drift\ndescription: d\n---\n\n## Phase 1\n\n## Phase 2\n\nbody\n"
        _write_skill(self.skills, "drift", text)
        self.assertEqual(self._run(self.skills, "--write-baseline", self.baseline), 0)
        self.assertEqual(self._run(self.skills, "--quiet", "--baseline", self.baseline), 0)

        # 필수 필드를 하나 더 깨면 failure 목록이 늘어난다
        _write_skill(self.skills, "drift", text.replace("description: d\n", ""))
        self.assertEqual(self._run(self.skills, "--quiet", "--baseline", self.baseline), 1)

    def test_partial_run_does_not_report_unlinted_entries_as_stale(self):
        """회귀 테스트 — stale 판정이 `in seen` 가드를 잃으면 부분 린트에서 오보고한다."""
        broken = "---\nname: broken\ndescription: d\n---\n\nbody\n"
        _write_skill(self.skills, "broken", broken)
        _write_skill(self.skills, "other", broken.replace("broken", "other"))
        self._run(self.skills, "--write-baseline", self.baseline)

        with open(self.baseline, encoding="utf-8") as f:
            known = json.load(f)["known_failures"]
        self.assertEqual(set(known), {"broken", "other"})

        # 'broken' 하나만 린트 — 'other' 는 검사하지 않았을 뿐 고쳐진 게 아니다
        one = os.path.join(self.skills, "broken")
        buf, sys.stdout = sys.stdout, open(os.devnull, "w", encoding="utf-8")
        try:
            code = self._run(one, "--baseline", self.baseline)
        finally:
            sys.stdout.close()
            sys.stdout = buf
        self.assertEqual(code, 0)

    def test_missing_baseline_file_is_not_an_error(self):
        _write_skill(self.skills, "good", GOOD_SKILL)
        code = self._run(self.skills, "--quiet", "--baseline", os.path.join(self.root, "nope.json"))
        self.assertEqual(code, 0)


class TestExitCodes(unittest.TestCase):
    def test_nothing_to_lint_returns_2(self):
        with tempfile.TemporaryDirectory() as d:
            empty = os.path.join(d, "empty")
            os.makedirs(empty)
            self.assertEqual(ls.main([empty, "--quiet"]), 2)

    def test_strict_turns_warnings_into_failure(self):
        with tempfile.TemporaryDirectory() as d:
            skills = os.path.join(d, "skills")
            os.makedirs(skills)
            _write_skill(skills, "warner", GOOD_SKILL)  # Check 4: no write-scope declaration → WARN
            self.assertEqual(ls.main([skills, "--quiet"]), 0)
            self.assertEqual(ls.main([skills, "--quiet", "--strict"]), 1)


class TestDescriptionQuality(unittest.TestCase):
    """Checks 8·9·10 — description 은 문서가 아니라 라우팅 지시문이다.

    셋 다 WARNING 이므로 실패로 승격되지 않는지도 함께 단언한다. 경고가
    조용히 실패가 되면 기존 130개 파일이 전부 CI 를 막는다.
    """

    def _warn_text(self, description: str) -> str:
        r = ls.Result("x", "skill")
        ls.check_description_quality(r, description)
        return " ".join(r.warnings)

    # --- Check 8: when NOT to use --------------------------------------
    def test_missing_negative_condition_warns(self):
        self.assertIn("Check 8", self._warn_text(
            "Use this skill when the user asks for a sprint plan."))

    def test_english_negative_condition_satisfies_check_8(self):
        for phrase in ("Do NOT use for PDFs.", "instead of a Word document",
                       "never for style opinions", "Avoid for read-only tasks."):
            text = self._warn_text(f"Use when the user asks for X. {phrase}")
            self.assertNotIn("Check 8", text, phrase)

    def test_korean_negative_condition_satisfies_check_8(self):
        text = self._warn_text("문서를 만들 때 사용하세요. 스프레드시트에는 쓰지 않습니다.")
        self.assertNotIn("Check 8", text)

    # --- Check 10: when TO use -----------------------------------------
    def test_capability_blurb_without_trigger_warns(self):
        self.assertIn("Check 10", self._warn_text(
            "A helper that produces a nicely formatted report."))

    def test_trigger_clause_satisfies_check_10(self):
        for phrase in ("Use this skill when the user asks.",
                       "Trigger whenever a .pptx is involved.",
                       "Use for release readiness evaluation.",
                       "사용자가 요청할 때 실행합니다."):
            self.assertNotIn("Check 10", self._warn_text(phrase), phrase)

    def test_empty_description_is_not_double_reported(self):
        # 빈 description 은 Check 1 / empty description 이 이미 잡는다.
        r = ls.Result("x", "skill")
        ls.check_description_quality(r, "")
        self.assertEqual(r.warnings, [])

    # --- Check 9: near duplicates ---------------------------------------
    def _pair(self, da: str, db: str) -> list[ls.Result]:
        ra, rb = ls.Result("skills/a/SKILL.md", "skill"), ls.Result("skills/b/SKILL.md", "skill")
        ra.description, rb.description = da, db
        ls.flag_near_duplicates([ra, rb])
        return [ra, rb]

    def test_near_identical_descriptions_warn_on_both_sides(self):
        d = ("Use this skill when the user wants a combat balance review of "
             "damage formulas, hit rates and enemy scaling curves.")
        ra, rb = self._pair(d, d)
        self.assertTrue(any("Check 9" in w for w in ra.warnings))
        self.assertTrue(any("Check 9" in w for w in rb.warnings))

    def test_distinct_descriptions_do_not_warn(self):
        ra, rb = self._pair(
            "Use this skill when the user wants a combat balance review of damage formulas.",
            "Trigger whenever a PDF must be merged, split, rotated or watermarked.")
        self.assertFalse(any("Check 9" in w for w in ra.warnings + rb.warnings))

    def test_short_descriptions_abstain(self):
        # 토큰이 너무 적으면 유사도는 잡음이다 — 판정하지 않는다.
        ra, rb = self._pair("Do the thing.", "Do the thing.")
        self.assertFalse(any("Check 9" in w for w in ra.warnings + rb.warnings))

    def test_threshold_is_a_named_constant(self):
        # deterministic-gates.md "Adding a gate" 규칙 2.
        self.assertIsInstance(ls.NEAR_DUPLICATE_THRESHOLD, float)
        self.assertTrue(0.0 < ls.NEAR_DUPLICATE_THRESHOLD < 1.0)

    def test_threshold_can_actually_fire_on_the_real_roster(self):
        """0.60 은 한 번도 발동하지 않았다. 발동 못 하는 검사는 없느니만 못하다."""
        files = ls.collect([
            os.path.join(_ROOT, "skills"),
            os.path.join(_ROOT, "skills", "studio-orchestrator", "references", "roles"),
        ])
        results = []
        for path, kind in files:
            with open(path, encoding="utf-8") as f:
                text = f.read()
            results.append(ls.lint_skill(path, text) if kind == "skill"
                           else ls.lint_role(path, text))
        ls.flag_near_duplicates(results)
        fired = sum(1 for r in results for w in r.warnings if "Check 9" in w)
        self.assertGreater(fired, 0, "Check 9 never fires — threshold is too high")

    # --- 등급 ------------------------------------------------------------
    def test_description_checks_are_warnings_not_failures(self):
        r = ls.Result("x", "skill")
        ls.check_description_quality(r, "A helper that does helpful things nicely.")
        self.assertEqual(r.failures, [])
        self.assertTrue(r.warnings)


class TestUnquote(unittest.TestCase):
    def test_strips_matching_quotes(self):
        self.assertEqual(ls.unquote('"hello"'), "hello")
        self.assertEqual(ls.unquote("'hello'"), "hello")

    def test_leaves_bare_text(self):
        self.assertEqual(ls.unquote("hello"), "hello")

    def test_unescapes_inner_quotes(self):
        self.assertEqual(ls.unquote('"say \\"hi\\""'), 'say "hi"')


if __name__ == "__main__":
    unittest.main()
