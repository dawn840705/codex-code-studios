#!/usr/bin/env python3
"""Policy compliance gate — the axis `$story-done` was missing.

Every gate in this plugin judges the same question: *did the work get done?*
`$story-done` verifies acceptance criteria, `$smoke-check` runs the suite,
`check_phase.py` checks artifacts exist. All of them are the **completion** axis.

None of them asks the second question: *was it done the way we said?* A story
that reaches `Status: Complete` by skipping the failing test, or by writing its
artifacts outside the documented tree, records exactly the same `exit 0` as one
that did the work properly. `Code Studios policy` has a "Don't do this" section, but it is
prose — no script has ever read it, so nothing has ever enforced it.

That failure mode has a name: **unsafe-success**. It is worse than a plain
failure, because a plain failure is visible and gets fixed, while an unsafe
success is indistinguishable from a real one in every record we keep — and the
next session's agent reads those records as the normal way to work.

This script is the policy axis. It is deliberately *independent* of the
completion axis: run both, report both, and let a completion PASS sit next to a
policy FAIL without either one overwriting the other.

    Task completion  : PASS  (AC 7/7)
    Policy compliance: FAIL  (verify_policy.py -> exit 2, P2)

Checks
------
    P1  story is Complete but its declared test evidence does not exist   ABORT
    P2  the diff *adds* a test-skip marker                                ABORT
    P3  design artifacts contradict production/track.txt, or both tracks'
        artifacts exist with no declared track                             WARN
    P4  new files under design/ or production/ break the path convention  WARN

P1 and P2 abort because both are mechanical and unambiguous: a file is there or
it is not; a skip marker was added or it was not. P3 and P4 warn because both
have legitimate exceptions (a genuinely hybrid project; a deliberate new
directory), and a gate that fires wrongly gets disabled wholesale — which costs
more than the check ever earned. Promote them once the false-positive rate is
known, not before.

Exit codes — the contract in docs/deterministic-gates.md:

    0  compliant — no policy violation found
    1  warning   — a soft violation (P3/P4); a human decides
    2  abort     — a hard violation (P1/P2); do not mark the work done
    3  cannot judge — not a git repo, or the diff could not be produced

Exit 3 is not a pass. A gate that could not run has produced no verdict.

Standard library only.

Usage:
    python3 scripts/verify_policy.py                          # repo-wide, vs HEAD
    python3 scripts/verify_policy.py --story production/epics/core/story-001-x.md
    python3 scripts/verify_policy.py --base <story-start-commit>  # everything since
    python3 scripts/verify_policy.py --self-test              # built-in smoke test

Without --base the diff is the working tree plus the index against HEAD — the
shape of a story in progress, and *empty right after a commit*. A story that
commits mid-way therefore hides its committed half from P2 and P4. Pass the
commit the story started from (or the branch fork point) as --base: the diff
then runs from merge-base(<base>, HEAD) to the working tree, so committed,
staged and unstaged work are all judged. Callers that do not know the commit
can use `--base $(git merge-base HEAD main)`.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gate_report import build as build_report, emit as emit_report  # noqa: E402
from check_phase import read_track_file  # noqa: E402  (one reader for production/track.txt)
from console_encoding import force_utf8  # noqa: E402

# --- exit codes (docs/deterministic-gates.md) --------------------------------

EXIT_COMPLIANT = 0
EXIT_WARNING = 1
EXIT_ABORT = 2
EXIT_CANNOT_JUDGE = 3

WARN = "WARNING"
ABORT = "ABORT"

# --- P1: story completion vs declared evidence -------------------------------

# `> **Status**: Complete` in the story header block.
STORY_STATUS_RE = re.compile(r"^\s*>?\s*\*\*Status\*\*\s*:\s*(.+?)\s*$", re.M)
COMPLETE_STATUSES = ("complete", "done", "closed")

# The "## Test Evidence" section and the backticked paths inside it.
TEST_EVIDENCE_SECTION_RE = re.compile(
    r"^##\s*Test Evidence\s*$(.*?)(?=^##\s|\Z)", re.M | re.S
)
BACKTICK_PATH_RE = re.compile(r"`([^`\n]+)`")

# An unfilled template still carries its placeholders. Judging those would flag
# every freshly generated story, so a path containing one is skipped, not failed.
PLACEHOLDER_RE = re.compile(r"[\[\]<>]")

# `**Status**: [ ] Not yet created` inside the evidence section.
EVIDENCE_NOT_CREATED_RE = re.compile(r"not yet created", re.I)

# --- P2: skip markers introduced by the diff ---------------------------------
#
# Only *added* lines are judged (diff lines starting with a single '+'). A story
# that merely touches a file which already had a skip marker is not the failure
# this check is looking for.
SKIP_MARKER_PATTERNS = (
    re.compile(r"@pytest\.mark\.(skip|xfail)"),
    re.compile(r"\bpytest\.skip\s*\("),
    re.compile(r"\bunittest\.skip"),
    re.compile(r"\.(skip|only)\s*\("),          # jest / vitest / mocha
    re.compile(r"\bxit\s*\(|\bxdescribe\s*\("),  # jasmine / jest
    re.compile(r"\[\s*Ignore\s*[\]\(]"),         # NUnit / MSTest
    re.compile(r"\bt\.Skip\s*\("),               # Go
    re.compile(r"#\s*\[ignore\]"),               # Rust
)

# P2 judges only files that can hold an executable test. Prose that *names* a
# skip marker is documentation, not a skipped test — the first run of this gate
# flagged `skills/story-done/SKILL.md` for explaining what P2 catches, which is
# exactly the kind of false positive that gets a gate switched off entirely.
CODE_EXTENSIONS = (
    ".py", ".js", ".jsx", ".mjs", ".ts", ".tsx", ".go", ".rs", ".cs", ".java",
    ".kt", ".kts", ".rb", ".php", ".swift", ".m", ".mm", ".cpp", ".cc", ".c",
    ".h", ".hpp", ".gd", ".lua", ".dart", ".scala", ".ex", ".exs",
)

# File-level opt-out. Deliberately greppable — `git grep -l "policy-allow-file"`
# lists every exemption in the repo, so the escape hatch stays auditable rather
# than becoming invisible. The intended user is the test suite *for this gate*,
# which must carry skip markers as fixtures to prove the check works.
POLICY_OPT_OUT = "policy-allow-file: skip-marker"

# --- P3: track mixing --------------------------------------------------------
#
# Code Studios policy: a game project does not get a frontend-engineer, a web app does not
# get a level-designer. Runtime spawns are invisible to a script, but the
# artifacts those agents leave behind are not.
GAME_TRACK_GLOB = ("design/gdd", ".md")
PRODUCT_TRACK_GLOB = ("product/prd", ".md")

# --- P4: path conventions (Code Studios policy "File conventions the plugin expects") ---

# Derived from three sources, and a path must be in one of them to be listed:
# the artifact globs in docs/workflow-catalog.yaml, the tree in
# docs/directory-structure.md, and the output paths the skills and hooks in
# this plugin actually write. A path the plugin itself declares as a canonical
# location must not warn here — a gate that fires on its own conventions is the
# false-positive case this file's docstring says gets gates disabled wholesale.
CONVENTION_PREFIXES = (
    "design/gdd/",
    "design/adr/",
    "design/art/",
    "design/assets/",
    "design/ux/",
    "design/archive/",
    "design/narrative/",
    "design/ui/",
    "design/registry/",
    "design/levels/",
    "design/live-ops/",
    "design/quick-specs/",
    "design/balance/",
    "design/concepts/",
    "design/community/",
    "product/prd/",
    "production/sprints/",
    "production/milestones/",
    "production/bugs/",
    "production/epics/",
    "production/stories/",
    "production/qa/",
    "production/playtests/",
    "production/marketing/",
    "production/session-state/",
    "production/session-logs/",
    "production/retrospectives/",
    "production/releases/",
    "production/localization/",
    "production/security/",
    "production/gate-checks/",
    "production/onboarding/",
    "production/hotfixes/",
    "production/risk-register/",
)
CONVENTION_FILES = (
    "design/architecture.md",
    "design/accessibility-requirements.md",
    "production/review-mode.txt",
    "production/human-actions.md",
    "production/track.txt",
    "production/stage.txt",
)
# Only these two roots are policed. Everything else in a user project is the
# user's business, and a linter with an opinion about `src/` would be wrong more
# often than right.
POLICED_ROOTS = ("design/", "production/")


class Finding:
    def __init__(self, check: str, severity: str, path: str, detail: str):
        self.check = check
        self.severity = severity
        self.path = path
        self.detail = detail

    def __str__(self) -> str:
        return f"{self.check} [{self.severity}] {self.path}: {self.detail}"


# --- git helpers -------------------------------------------------------------


class GitUnavailable(Exception):
    """Raised when no verdict can be produced — maps to exit 3."""


def _git(root: str, *args: str) -> str:
    # --no-optional-locks: `git diff` refreshes the stat cache, which writes
    # .git/index.lock. On a filesystem where unlink is denied (FUSE bridges,
    # some network mounts) that lock cannot be removed and every later commit
    # in the repo fails — git reports the cleanup failure as a warning and
    # still exits 0, so the poisoning is silent. Read-only judgement has no
    # business touching the index.
    try:
        proc = subprocess.run(
            ["git", "--no-optional-locks", *args],
            cwd=root,
            capture_output=True,
            text=True,
            # 한국어 저장소의 diff 는 UTF-8 이다. text=True 만 주면
            # locale.getencoding() (한국어 Windows 에서 cp949) 로 디코딩하다
            # 리더 스레드가 죽고 stdout 이 None 이 된다 — 게이트가 판정 대신
            # AttributeError 로 무너진다. 판정을 인코딩에 걸지 않는다.
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, FileNotFoundError) as exc:  # git not installed
        raise GitUnavailable(f"git could not be run: {exc}") from exc
    if proc.returncode != 0:
        raise GitUnavailable(
            f"git {' '.join(args)} failed ({proc.returncode}): {proc.stderr.strip()}"
        )
    return proc.stdout


def diff_anchor(root: str, base: str | None) -> str:
    """The commit the judged diff starts from.

    Without --base that is HEAD: the working tree plus the index, which is what
    a story in progress looks like — and which is empty right after a commit.
    With --base it is merge-base(base, HEAD), so the diff to the working tree
    covers everything since the story started: committed, staged and unstaged.
    A ref git cannot resolve is no verdict (GitUnavailable → exit 3).
    """
    if not os.path.isdir(os.path.join(root, ".git")):
        raise GitUnavailable(f"not a git repository: {root}")
    if not base:
        return "HEAD"
    anchor = _git(root, "merge-base", base, "HEAD").strip()
    if not anchor:
        raise GitUnavailable(f"no common ancestor between {base} and HEAD")
    return anchor


def diff_text(root: str, base: str | None) -> str:
    """Unified diff of the work under judgement (see diff_anchor)."""
    return _git(root, "diff", "--unified=0", diff_anchor(root, base))


def added_lines(diff: str) -> list[tuple[str, str]]:
    """[(path, added_line)] — only real additions, never the +++ header."""
    out: list[tuple[str, str]] = []
    current = ""
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+") and current:
            out.append((current, line[1:]))
    return out


def added_files(root: str, base: str | None) -> list[str]:
    out = _git(root, "diff", "--name-only", "--diff-filter=A", diff_anchor(root, base))
    return [p for p in out.splitlines() if p.strip()]


# --- checks ------------------------------------------------------------------


def check_p1_story_evidence(root: str, story_path: str) -> list[Finding]:
    """A story cannot be Complete while the evidence it declares is absent."""
    findings: list[Finding] = []
    abs_story = story_path if os.path.isabs(story_path) else os.path.join(root, story_path)
    if not os.path.isfile(abs_story):
        raise GitUnavailable(f"story file not found: {story_path}")

    with open(abs_story, encoding="utf-8") as fh:
        text = fh.read()

    statuses = [m.group(1).strip().lower() for m in STORY_STATUS_RE.finditer(text)]
    if not statuses or not any(
        s.startswith(done) for s in statuses[:1] for done in COMPLETE_STATUSES
    ):
        return findings  # not claiming completion — nothing to police

    section = TEST_EVIDENCE_SECTION_RE.search(text)
    if not section:
        findings.append(
            Finding("P1", ABORT, story_path,
                    "Status is Complete but the story has no Test Evidence section")
        )
        return findings

    body = section.group(1)
    if EVIDENCE_NOT_CREATED_RE.search(body):
        findings.append(
            Finding("P1", ABORT, story_path,
                    "Status is Complete but Test Evidence still reads 'Not yet created'")
        )

    for raw in BACKTICK_PATH_RE.findall(body):
        candidate = raw.strip()
        if PLACEHOLDER_RE.search(candidate):
            continue  # unfilled template placeholder
        if "/" not in candidate:
            continue  # prose in backticks, not a path
        if not os.path.exists(os.path.join(root, candidate)):
            findings.append(
                Finding("P1", ABORT, story_path,
                        f"declared evidence does not exist: {candidate}")
            )
    return findings


def p2_judges(root: str, path: str) -> bool:
    """Is this a file where a skip marker would actually skip a test?"""
    if not path.endswith(CODE_EXTENSIONS):
        return False
    full = os.path.join(root, path)
    if os.path.isfile(full):
        try:
            with open(full, encoding="utf-8", errors="replace") as fh:
                if POLICY_OPT_OUT in fh.read():
                    return False
        except OSError:
            pass
    return True


def check_p2_skip_markers(root: str, base: str | None) -> list[Finding]:
    """A test made to pass by not running is not a test that passed."""
    findings: list[Finding] = []
    judged: dict[str, bool] = {}
    for path, line in added_lines(diff_text(root, base)):
        if path not in judged:
            judged[path] = p2_judges(root, path)
        if not judged[path]:
            continue
        for pattern in SKIP_MARKER_PATTERNS:
            if pattern.search(line):
                findings.append(
                    Finding("P2", ABORT, path,
                            f"diff adds a test-skip marker: {line.strip()[:90]}")
                )
                break
    return findings


def check_p3_track_mixing(root: str) -> list[Finding]:
    """Design artifacts that contradict the track, or that leave it undecidable.

    Two shapes, and the first one only became checkable when production/track.txt
    arrived. Before that the declared track existed nowhere on disk, so a product
    project misrouted into `$brainstorm` or `$design-system` — writing design/gdd/
    and nothing else — was indistinguishable from a game project doing its job, and
    this check could only fire on the symmetric case where both roots were present.
    With the track declared, one root plus a contradicting declaration is no longer
    a guess: the project says one thing and its artifacts say another.
    """
    def has(spec: tuple[str, str]) -> bool:
        directory, suffix = spec
        full = os.path.join(root, directory)
        if not os.path.isdir(full):
            return False
        return any(n.endswith(suffix) for n in os.listdir(full))

    game, product = has(GAME_TRACK_GLOB), has(PRODUCT_TRACK_GLOB)
    track = read_track_file(root)

    if track == "product" and game:
        return [
            Finding("P3", WARN, "design/gdd",
                    "production/track.txt declares `product` but design/gdd/*.md "
                    "exists — a game-track skill wrote here. Check what produced it "
                    "(/brainstorm and /design-system are game-framed) and move the "
                    "content to product/prd/, or correct track.txt")
        ]
    if track == "game" and product:
        return [
            Finding("P3", WARN, "product/prd",
                    "production/track.txt declares `game` but product/prd/*.md "
                    "exists — a product-track skill wrote here. Move the content to "
                    "design/gdd/, or correct track.txt")
        ]
    if game and product:
        return [
            Finding("P3", WARN, ".",
                    "both design/gdd/*.md (game track) and product/prd/*.md "
                    "(product track) exist, and production/track.txt does not say "
                    "which is intended — write `game` or `product` to that file so "
                    "this is decidable. Code Studios policy says not to mix packs")
        ]
    return []


def check_p4_path_conventions(root: str, base: str | None) -> list[Finding]:
    """New files under design/ and production/ must land where we said."""
    findings: list[Finding] = []
    for path in added_files(root, base):
        if not path.startswith(POLICED_ROOTS):
            continue
        if path in CONVENTION_FILES:
            continue
        if path.startswith(CONVENTION_PREFIXES):
            continue
        findings.append(
            Finding("P4", WARN, path,
                    "new file outside the documented layout "
                    "(Code Studios policy 'File conventions the plugin expects')")
        )
    return findings


# --- driver ------------------------------------------------------------------


def run_checks(root: str, story: str | None, base: str | None) -> list[Finding]:
    findings: list[Finding] = []
    if story:
        findings += check_p1_story_evidence(root, story)
    findings += check_p2_skip_markers(root, base)
    findings += check_p3_track_mixing(root)
    findings += check_p4_path_conventions(root, base)
    return findings


def verdict(findings: list[Finding]) -> int:
    if any(f.severity == ABORT for f in findings):
        return EXIT_ABORT
    if findings:
        return EXIT_WARNING
    return EXIT_COMPLIANT


def report(findings: list[Finding], code: int, quiet: bool) -> None:
    if not quiet:
        for f in findings:
            print(f)
        if findings:
            print()
    label = {
        EXIT_COMPLIANT: "COMPLIANT",
        EXIT_WARNING: "WARNING",
        EXIT_ABORT: "ABORT",
    }[code]
    aborts = sum(1 for f in findings if f.severity == ABORT)
    warns = len(findings) - aborts
    print(
        f"verify_policy: {label} — {aborts} abort, {warns} warning "
        f"(exit {code})"
    )


def self_test() -> int:
    """Built-in smoke test: each check fires, and a clean tree stays clean."""
    import tempfile

    def git(root, *a):
        subprocess.run(["git", *a], cwd=root, check=True, capture_output=True)

    failures = []

    def expect(name, got, want):
        mark = "ok  " if got == want else "FAIL"
        if got != want:
            failures.append(f"{name}: got {got}, want {want}")
        print(f"  [{mark}] {name}: exit {got} (want {want})")

    with tempfile.TemporaryDirectory() as d:
        git(d, "init", "-q")
        git(d, "config", "user.email", "t@example.com")
        git(d, "config", "user.name", "t")
        os.makedirs(os.path.join(d, "tests"))
        with open(os.path.join(d, "tests", "t_test.py"), "w") as f:
            f.write("def test_a():\n    assert True\n")
        git(d, "add", "-A")
        git(d, "commit", "-qm", "init")

        print("verify_policy --self-test")
        expect("clean tree", verdict(run_checks(d, None, None)), EXIT_COMPLIANT)

        # P2 — add a skip marker
        with open(os.path.join(d, "tests", "t_test.py"), "w") as f:
            f.write("import pytest\n\n@pytest.mark.skip\ndef test_a():\n    assert True\n")
        expect("P2 skip marker", verdict(run_checks(d, None, None)), EXIT_ABORT)
        git(d, "checkout", "--", ".")

        # P1 — Complete story, missing evidence
        os.makedirs(os.path.join(d, "production", "epics", "core"), exist_ok=True)
        story = "production/epics/core/story-001-x.md"
        with open(os.path.join(d, story), "w") as f:
            f.write("# Story 001\n\n> **Status**: Complete\n\n"
                    "## Test Evidence\n\n- `tests/unit/nope_test.py`\n")
        expect("P1 missing evidence", verdict(run_checks(d, story, None)), EXIT_ABORT)

        # --base — off-convention file already committed: invisible vs HEAD,
        # visible from the story-start commit
        start = subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, check=True,
                               capture_output=True, encoding="utf-8").stdout.strip()
        os.makedirs(os.path.join(d, "design"), exist_ok=True)
        with open(os.path.join(d, "design", "stray.md"), "w") as f:
            f.write("x\n")
        git(d, "add", "-A")
        git(d, "commit", "-qm", "mid-story")
        expect("P4 committed, no --base", verdict(run_checks(d, None, None)), EXIT_COMPLIANT)
        expect("P4 committed, --base", verdict(run_checks(d, None, start)), EXIT_WARNING)

        # P3 — both tracks present
        os.makedirs(os.path.join(d, "design", "gdd"), exist_ok=True)
        os.makedirs(os.path.join(d, "product", "prd"), exist_ok=True)
        open(os.path.join(d, "design", "gdd", "combat.md"), "w").close()
        open(os.path.join(d, "product", "prd", "prd-login.md"), "w").close()
        expect("P3 track mixing", verdict(run_checks(d, None, None)), EXIT_WARNING)

        # exit 3 — not a repo
        with tempfile.TemporaryDirectory() as plain:
            try:
                run_checks(plain, None, None)
                expect("P0 non-repo", EXIT_COMPLIANT, EXIT_CANNOT_JUDGE)
            except GitUnavailable:
                expect("P0 non-repo", EXIT_CANNOT_JUDGE, EXIT_CANNOT_JUDGE)

    if failures:
        print("\nself-test FAILED:\n  " + "\n  ".join(failures))
        return 1
    print("\nself-test passed")
    return 0


def main(argv: list[str]) -> int:
    force_utf8()  # 판정이 콘솔 코드페이지에 좌우되지 않게 (console_encoding 참조)
    ap = argparse.ArgumentParser(
        description="Policy compliance gate — the axis completion checks miss"
    )
    ap.add_argument("--story", help="story file to judge for P1")
    ap.add_argument(
        "--base",
        help="commit the story started from (or its branch fork point); judges "
             "everything since merge-base(BASE, HEAD) including staged and "
             "unstaged work. Default: HEAD only — blind right after a commit",
    )
    ap.add_argument("--project-root", default=".", help="repository root")
    ap.add_argument("--quiet", action="store_true", help="summary line only")
    ap.add_argument("--json", action="store_true", dest="as_json",
                    help="emit the shared gate report (scripts/gate_report.py)")
    ap.add_argument("--self-test", action="store_true", help="run the built-in smoke test")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    root = os.path.abspath(args.project_root)
    try:
        findings = run_checks(root, args.story, args.base)
    except GitUnavailable as exc:
        if args.as_json:
            emit_report(build_report(
                "verify_policy", EXIT_CANNOT_JUDGE, reason=str(exc),
            ))
        else:
            print(f"verify_policy: CANNOT JUDGE — {exc} (exit {EXIT_CANNOT_JUDGE})",
                  file=sys.stderr)
            print("A gate that could not run has produced no verdict. "
                  "Do not read this as a pass.", file=sys.stderr)
        return EXIT_CANNOT_JUDGE

    code = verdict(findings)
    if args.as_json:
        aborts = sum(1 for f in findings if f.severity == ABORT)
        emit_report(build_report(
            "verify_policy", code,
            reason=f"{aborts} abort, {len(findings) - aborts} warning",
            evidence=[
                {"id": f.check, "severity": f.severity,
                 "source": f.path, "detail": f.detail}
                for f in findings
            ],
        ))
        return code
    report(findings, code, args.quiet)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
