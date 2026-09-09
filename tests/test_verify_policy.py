"""scripts/verify_policy.py 단위 테스트.

이 게이트는 "완료됐다"가 아니라 "우리가 말한 방식대로 했다"를 판정한다.
정책 게이트가 조용히 망가지면 unsafe-success 가 다시 exit 0 으로 기록되는데,
그 상태는 정상 통과와 기록상 구별되지 않는다 — 그래서 발동해야 할 때
발동하는지와, 발동하지 말아야 할 때 잠자코 있는지를 양방향으로 단언한다.

이 파일은 P2 가 찾는 skip 마커를 픽스처로 담고 있으므로 P2 대상에서 제외한다
(게이트 자신의 테스트가 게이트에 걸리는 구조를 피한다).
policy-allow-file: skip-marker

`python3 -m unittest` 와 pytest 양쪽에서 동작.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

import verify_policy as vp  # noqa: E402


def git(root: str, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True,
                   encoding="utf-8", errors="replace")


def write(root: str, relpath: str, content: str = "") -> str:
    path = os.path.join(root, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


class RepoCase(unittest.TestCase):
    """git 저장소 하나를 세우고 커밋 하나를 남긴 상태에서 시작."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        git(self.root, "init", "-q")
        git(self.root, "config", "user.email", "t@example.com")
        git(self.root, "config", "user.name", "t")
        write(self.root, "tests/sample_test.py", "def test_a():\n    assert True\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "init")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_all(self, story: str | None = None) -> int:
        return vp.verdict(vp.run_checks(self.root, story, None))


COMPLETE_STORY = """# Story 001: Damage calculator

> **Epic**: combat
> **Status**: Complete
> **Type**: Logic

## Acceptance Criteria

- [x] damage is computed

## Test Evidence

**Required evidence**:
- `{evidence}`
"""

TEMPLATE_STORY = """# Story 001

> **Status**: Complete

## Test Evidence

- Logic: `tests/unit/[system]/[story-slug]_test.[ext]` — must exist and pass
- `production/qa/evidence/real-evidence.md`
"""


class TestP1StoryEvidence(RepoCase):
    def test_complete_story_with_missing_evidence_aborts(self):
        story = "production/epics/core/story-001.md"
        write(self.root, story, COMPLETE_STORY.format(evidence="tests/unit/nope_test.py"))
        self.assertEqual(self.run_all(story), vp.EXIT_ABORT)

    def test_complete_story_with_present_evidence_passes(self):
        write(self.root, "tests/unit/damage_test.py", "def test_d():\n    assert True\n")
        story = "production/epics/core/story-001.md"
        write(self.root, story, COMPLETE_STORY.format(evidence="tests/unit/damage_test.py"))
        findings = vp.check_p1_story_evidence(self.root, story)
        self.assertEqual(findings, [])

    def test_incomplete_story_is_not_policed(self):
        """진행 중 스토리에 증거가 없는 것은 위반이 아니라 정상이다."""
        story = "production/epics/core/story-001.md"
        write(self.root, story,
              COMPLETE_STORY.format(evidence="tests/unit/nope_test.py")
              .replace("**Status**: Complete", "**Status**: In Progress"))
        self.assertEqual(vp.check_p1_story_evidence(self.root, story), [])

    def test_unfilled_template_placeholders_are_skipped(self):
        """갓 생성된 스토리의 [system] 자리표시자까지 잡으면 전량 오탐이 된다."""
        write(self.root, "production/qa/evidence/real-evidence.md", "# evidence\n")
        story = "production/epics/core/story-001.md"
        write(self.root, story, TEMPLATE_STORY)
        findings = vp.check_p1_story_evidence(self.root, story)
        self.assertEqual([f.detail for f in findings], [])

    def test_not_yet_created_marker_aborts(self):
        story = "production/epics/core/story-001.md"
        write(self.root, story,
              "# Story\n\n> **Status**: Complete\n\n"
              "## Test Evidence\n\n**Status**: [ ] Not yet created\n")
        findings = vp.check_p1_story_evidence(self.root, story)
        self.assertTrue(any("Not yet created" in f.detail for f in findings))

    def test_missing_evidence_section_aborts(self):
        story = "production/epics/core/story-001.md"
        write(self.root, story, "# Story\n\n> **Status**: Complete\n\n## Dependencies\n\nNone\n")
        findings = vp.check_p1_story_evidence(self.root, story)
        self.assertEqual(len(findings), 1)
        self.assertIn("no Test Evidence section", findings[0].detail)

    def test_missing_story_file_cannot_judge(self):
        with self.assertRaises(vp.GitUnavailable):
            vp.check_p1_story_evidence(self.root, "production/epics/core/ghost.md")


class TestP2SkipMarkers(RepoCase):
    def test_added_pytest_skip_aborts(self):
        write(self.root, "tests/sample_test.py",
              "import pytest\n\n@pytest.mark.skip\ndef test_a():\n    assert True\n")
        self.assertEqual(self.run_all(), vp.EXIT_ABORT)

    def test_pre_existing_skip_is_not_flagged(self):
        """이미 skip 이던 파일을 스쳐 지나갔다고 위반이 되면 안 된다."""
        write(self.root, "tests/legacy_test.py",
              "import pytest\n\n@pytest.mark.skip\ndef test_old():\n    pass\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "legacy")
        write(self.root, "tests/legacy_test.py",
              "import pytest\n\n@pytest.mark.skip\ndef test_old():\n    pass\n\n"
              "# a harmless comment\n")
        findings = vp.check_p2_skip_markers(self.root, None)
        self.assertEqual(findings, [])

    def test_recognises_other_ecosystems(self):
        for name, line in (
            ("jest", "  it.skip('x', () => {});"),
            ("nunit", "  [Ignore(\"flaky\")]"),
            ("go", "\tt.Skip(\"wip\")"),
            ("rust", "#[ignore]"),
            ("unittest", "@unittest.skip('wip')"),
        ):
            with self.subTest(name):
                self.assertTrue(
                    any(p.search(line) for p in vp.SKIP_MARKER_PATTERNS),
                    f"{name} skip marker not recognised: {line}",
                )

    def test_diff_header_is_not_read_as_an_added_line(self):
        diff = "--- a/x.py\n+++ b/x.py\n@@ -0,0 +1 @@\n+real addition\n"
        self.assertEqual(vp.added_lines(diff), [("x.py", "real addition")])

    def test_prose_naming_a_marker_is_not_a_skipped_test(self):
        """첫 실행에서 story-done/SKILL.md 가 걸렸다 — 설명문은 위반이 아니다."""
        write(self.root, "docs/guide.md",
              "P2 catches a diff that adds `@pytest.mark.skip` to a test.\n")
        git(self.root, "add", "-A")
        self.assertEqual(vp.check_p2_skip_markers(self.root, None), [])

    def test_opt_out_marker_exempts_a_code_file(self):
        write(self.root, "tests/fixtures_test.py",
              "# policy-allow-file: skip-marker\n"
              "SAMPLE = '@pytest.mark.skip'\n")
        git(self.root, "add", "-A")
        self.assertEqual(vp.check_p2_skip_markers(self.root, None), [])

    def test_opt_out_is_greppable(self):
        """탈출구가 보이지 않으면 감사가 불가능하다."""
        self.assertIn("policy-allow-file", vp.POLICY_OPT_OUT)

    def test_code_file_without_opt_out_is_still_judged(self):
        """면제가 너무 넓어지면 P2 자체가 무력해진다 — 반대 방향도 단언."""
        write(self.root, "tests/real_test.py",
              "import pytest\n\n@pytest.mark.skip\ndef test_a():\n    pass\n")
        git(self.root, "add", "-A")
        self.assertTrue(vp.check_p2_skip_markers(self.root, None))


class TestP3TrackMixing(RepoCase):
    def test_both_tracks_present_warns(self):
        write(self.root, "design/gdd/combat.md", "# Combat\n")
        write(self.root, "product/prd/prd-login.md", "# Login\n")
        self.assertEqual(self.run_all(), vp.EXIT_WARNING)

    def test_single_track_is_clean(self):
        write(self.root, "design/gdd/combat.md", "# Combat\n")
        self.assertEqual(vp.check_p3_track_mixing(self.root), [])

    def test_empty_directories_do_not_count(self):
        os.makedirs(os.path.join(self.root, "design/gdd"))
        os.makedirs(os.path.join(self.root, "product/prd"))
        self.assertEqual(vp.check_p3_track_mixing(self.root), [])

    # --- declared track vs artifacts: the asymmetric case, undetectable before
    # production/track.txt existed ------------------------------------------

    def test_product_track_with_gdd_artifacts_warns(self):
        """The misrouting this check used to miss entirely: only design/gdd/ present."""
        write(self.root, "production/track.txt", "product\n")
        write(self.root, "design/gdd/game-concept.md", "# Concept\n")
        findings = vp.check_p3_track_mixing(self.root)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].check, "P3")
        self.assertIn("design/gdd", findings[0].path)
        self.assertEqual(self.run_all(), vp.EXIT_WARNING)

    def test_game_track_with_prd_artifacts_warns(self):
        write(self.root, "production/track.txt", "game\n")
        write(self.root, "product/prd/prd-login.md", "# Login\n")
        findings = vp.check_p3_track_mixing(self.root)
        self.assertEqual(len(findings), 1)
        self.assertIn("product/prd", findings[0].path)

    def test_declared_track_matching_its_artifacts_is_clean(self):
        write(self.root, "production/track.txt", "product\n")
        write(self.root, "product/prd/prd-login.md", "# Login\n")
        self.assertEqual(vp.check_p3_track_mixing(self.root), [])

    def test_track_alias_web_counts_as_product(self):
        write(self.root, "production/track.txt", "web\n")
        write(self.root, "design/gdd/combat.md", "# Combat\n")
        self.assertEqual(len(vp.check_p3_track_mixing(self.root)), 1)

    def test_unparseable_track_file_falls_back_to_symmetric_check(self):
        write(self.root, "production/track.txt", "banana\n")
        write(self.root, "design/gdd/combat.md", "# Combat\n")
        self.assertEqual(vp.check_p3_track_mixing(self.root), [])


class TestP4PathConventions(RepoCase):
    def _commit_new(self, relpath: str) -> None:
        write(self.root, relpath, "x\n")
        git(self.root, "add", "-A")

    def test_conventional_paths_pass(self):
        for p in ("design/gdd/combat.md", "production/sprints/sprint-01.md",
                  "design/architecture.md", "production/epics/core/EPIC.md"):
            with self.subTest(p):
                write(self.root, p, "x\n")
        self.assertEqual(vp.check_p4_path_conventions(self.root, None), [])

    def test_off_convention_path_warns(self):
        write(self.root, "design/random-notes.md", "x\n")
        git(self.root, "add", "-A")
        findings = vp.check_p4_path_conventions(self.root, None)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].check, "P4")
        self.assertEqual(findings[0].severity, vp.WARN)

    def test_unpoliced_roots_are_left_alone(self):
        """src/ 에 대한 의견은 맞는 경우보다 틀리는 경우가 많다."""
        write(self.root, "src/whatever/thing.ts", "x\n")
        write(self.root, "notes.md", "x\n")
        git(self.root, "add", "-A")
        self.assertEqual(vp.check_p4_path_conventions(self.root, None), [])

    def test_paths_the_plugin_itself_writes_pass(self):
        """플러그인이 자기 스킬·훅의 산출물에 경고를 내면 게이트가 통째로 꺼진다.

        각 경로의 근거: CLAUDE.md 가 쓰라는 track.txt, gate-check 가 쓰는
        stage.txt, 훅(log-agent.sh 등)이 만드는 session-logs/, 카탈로그의
        accessibility-requirements.md, directory-structure.md 의 archive/
        narrative/ ui/, 그리고 스킬이 Output 으로 선언한 나머지.
        """
        for p in (
            "production/track.txt",
            "production/stage.txt",
            "production/session-logs/session-2026-01-01.md",
            "design/accessibility-requirements.md",
            "design/archive/old-gdd.md",
            "design/narrative/characters/hero.md",
            "design/ui/hud-flow.md",
            "design/registry/entities.yaml",
            "design/levels/forest-01.md",
            "design/live-ops/ethics-policy.md",
            "design/quick-specs/dash-2026-01-01.md",
            "design/balance/balance-check-combat-2026-01-01.md",
            "design/concepts/proto-a.md",
            "design/community/tone-guide.md",
            "production/releases/launch-checklist-2026-01-01.md",
            "production/localization/translator-brief-ko-2026-01-01.md",
            "production/security/security-audit-2026-01-01.md",
            "production/gate-checks/gate-check-production.md",
            "production/onboarding/onboard-artist-2026-01-01.md",
            "production/hotfixes/hotfix-2026-01-01-crash.md",
            "production/risk-register/risks.md",
        ):
            write(self.root, p, "x\n")
        git(self.root, "add", "-A")
        findings = vp.check_p4_path_conventions(self.root, None)
        self.assertEqual([f.path for f in findings], [])

    def test_stray_file_under_production_still_warns(self):
        """허용 목록이 넓어져도 루트 바로 아래 임의 파일은 여전히 규약 밖이다."""
        write(self.root, "production/notes.md", "x\n")
        write(self.root, "production/misc/thing.md", "x\n")
        git(self.root, "add", "-A")
        findings = vp.check_p4_path_conventions(self.root, None)
        self.assertEqual(sorted(f.path for f in findings),
                         ["production/misc/thing.md", "production/notes.md"])


class TestBaseRef(RepoCase):
    """--base: 커밋 직후에도 스토리가 한 일이 보여야 한다.

    기본 기준(HEAD)은 작업 트리+인덱스만 보므로 스토리 중간에 커밋하면 P2·P4 가
    조용히 exit 0 을 낸다. --base <스토리 시작 커밋> 은 그 맹점을 닫는다.
    """

    def _head(self) -> str:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root, check=True,
                              capture_output=True, encoding="utf-8").stdout.strip()

    def test_committed_off_convention_file_is_seen_only_with_base(self):
        start = self._head()
        write(self.root, "design/random-notes.md", "x\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "mid-story")
        self.assertEqual(vp.check_p4_path_conventions(self.root, None), [])
        findings = vp.check_p4_path_conventions(self.root, start)
        self.assertEqual([f.path for f in findings], ["design/random-notes.md"])

    def test_committed_skip_marker_is_seen_only_with_base(self):
        start = self._head()
        write(self.root, "tests/sample_test.py",
              "import pytest\n\n@pytest.mark.skip\ndef test_a():\n    assert True\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "mid-story")
        self.assertEqual(vp.check_p2_skip_markers(self.root, None), [])
        self.assertEqual(vp.verdict(vp.run_checks(self.root, None, start)), vp.EXIT_ABORT)

    def test_base_covers_committed_and_uncommitted_work_together(self):
        """커밋한 절반과 아직 스테이징만 한 절반이 한 판정에 같이 들어와야 한다."""
        start = self._head()
        write(self.root, "design/committed.md", "x\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "half")
        write(self.root, "design/staged.md", "x\n")
        git(self.root, "add", "-A")
        findings = vp.check_p4_path_conventions(self.root, start)
        self.assertEqual(sorted(f.path for f in findings),
                         ["design/committed.md", "design/staged.md"])

    def test_base_equal_to_head_matches_the_default(self):
        write(self.root, "design/stray.md", "x\n")
        git(self.root, "add", "-A")
        self.assertEqual(
            [f.path for f in vp.check_p4_path_conventions(self.root, "HEAD")],
            [f.path for f in vp.check_p4_path_conventions(self.root, None)],
        )

    def test_unresolvable_base_cannot_judge(self):
        """모르는 ref 를 통과로 읽으면 안 된다 — exit 3 이다."""
        with self.assertRaises(vp.GitUnavailable):
            vp.run_checks(self.root, None, "no-such-ref")
        self.assertEqual(vp.main(["--project-root", self.root, "--base", "no-such-ref"]),
                         vp.EXIT_CANNOT_JUDGE)


class TestVerdictContract(RepoCase):
    """docs/deterministic-gates.md 의 4코드 계약."""

    def test_clean_repo_is_compliant(self):
        self.assertEqual(self.run_all(), vp.EXIT_COMPLIANT)

    def test_abort_outranks_warning(self):
        findings = [
            vp.Finding("P4", vp.WARN, "design/x.md", "off convention"),
            vp.Finding("P2", vp.ABORT, "tests/y.py", "skip marker"),
        ]
        self.assertEqual(vp.verdict(findings), vp.EXIT_ABORT)

    def test_warning_only_is_exit_1(self):
        self.assertEqual(
            vp.verdict([vp.Finding("P3", vp.WARN, ".", "mixed")]), vp.EXIT_WARNING
        )

    def test_non_repo_exits_3_not_0(self):
        """판정하지 못한 게이트를 통과로 읽는 것이 이 계약의 핵심 금지사항."""
        with tempfile.TemporaryDirectory() as plain:
            self.assertEqual(vp.main(["--project-root", plain]), vp.EXIT_CANNOT_JUDGE)

    def test_p1_p2_are_abort_and_p3_p4_are_warning(self):
        """등급 배정이 조용히 바뀌면 게이트의 성격이 바뀐다 — 고정한다."""
        write(self.root, "tests/sample_test.py",
              "import pytest\n\n@pytest.mark.skip\ndef test_a():\n    pass\n")
        write(self.root, "design/gdd/a.md", "x\n")
        write(self.root, "product/prd/b.md", "x\n")
        write(self.root, "design/stray.md", "x\n")
        git(self.root, "add", "-A")
        by_check = {f.check: f.severity for f in vp.run_checks(self.root, None, None)}
        self.assertEqual(by_check.get("P2"), vp.ABORT)
        self.assertEqual(by_check.get("P3"), vp.WARN)
        self.assertEqual(by_check.get("P4"), vp.WARN)


class TestSelfTest(unittest.TestCase):
    def test_built_in_self_test_passes(self):
        self.assertEqual(vp.self_test(), 0)


class TestRealRepoIsClean(unittest.TestCase):
    def test_this_repository_passes_its_own_gate(self):
        """플러그인 자신이 자기 정책을 어기고 있으면 게이트를 낼 자격이 없다."""
        self.assertEqual(vp.main(["--project-root", _ROOT, "--quiet"]),
                         vp.EXIT_COMPLIANT)


if __name__ == "__main__":
    unittest.main()
