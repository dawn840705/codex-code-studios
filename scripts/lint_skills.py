#!/usr/bin/env python3
"""Structural linter for codex-code-studios skills and role references.

This is the executable form of the static checks that `skills/skill-test/SKILL.md`
(Phase 2) runs. That skill is read and performed by an LLM, so it cannot run in
CI and does nothing unless a human invokes it. This script is the SSOT for the
*mechanical* checks; the skill keeps the qualitative evaluation on top.

Standard library only — no third-party dependencies.

Usage:
    python3 scripts/lint_skills.py skills/ skills/studio-orchestrator/references/roles/
    python3 scripts/lint_skills.py skills/gate-check      # single skill
    python3 scripts/lint_skills.py skills/ --strict       # warnings fail too
    python3 scripts/lint_skills.py skills/ --quiet        # summary line only

Baseline (how CI stays green while pre-existing debt is paid down):

    python3 scripts/lint_skills.py skills/ skills/studio-orchestrator/references/roles/ --write-baseline
    python3 scripts/lint_skills.py skills/ skills/studio-orchestrator/references/roles/ --baseline scripts/lint_baseline.json

Known failures recorded in the baseline are reported but do not fail the run.
Anything NOT in the baseline does — so a new skill with a broken frontmatter is
blocked immediately, which is the whole point of having this in CI. A baseline
entry that no longer fails is reported as fixed and should be deleted.

Exit codes:
    0  no un-baselined failures (warnings allowed unless --strict)
    1  at least one failure (or warning under --strict)
    2  bad invocation / nothing to lint
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

DEFAULT_BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lint_baseline.json")

_CONSOLE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CONSOLE_DIR not in sys.path:
    sys.path.insert(0, _CONSOLE_DIR)
from console_encoding import force_utf8  # noqa: E402

# --- frontmatter conventions -------------------------------------------------

SKILL_REQUIRED_FIELDS = ("name", "description")
ROLE_REQUIRED_FIELDS = ("name", "description")

VERDICT_KEYWORDS = (
    "PASS",
    "FAIL",
    "CONCERNS",
    "APPROVED",
    "BLOCKED",
    "COMPLETE",
    "READY",
    "COMPLIANT",
    "NON-COMPLIANT",
)

# write-scope declaration (Check 4)
#
# Until v0.7 this check rewarded ask-before-write wording ("May I write…?"),
# the opposite of the autonomy contract the repo is moving to
# (docs/design/v0.8.0-astra-autonomy-plan.md § 2.4, A-2). A skill now passes by
# saying *where* it writes — a write verb next to a backticked path, or an
# output/artifact heading — or by saying it is read-only. Asking permission
# declares nothing about scope, so it no longer counts.
#
# Verb stems are bounded to their conjugations on purpose: `produc\w*` matches
# "product"/"production" and `creat\w*` matches "creative-director", and both
# sit next to a path in a large part of the roster (13 false passes measured).
_WRITE_VERB = (
    r"(?:(?:writ(?:e|es|ing|ten)|creat(?:e|es|ed|ing)|sav(?:e|es|ed|ing)"
    r"|generat(?:e|es|ed|ing)|produc(?:e|es|ed|ing)|emit(?:s|ted|ting)?"
    r"|output(?:s|ted|ting)?|append(?:s|ed|ing)?|updat(?:e|es|ed|ing)"
    r"|overwrit(?:e|es|ing|ten)|record(?:s|ed|ing)?)\b|저장|생성|작성|기록)"
)
# A backticked token containing a slash and at least one word character:
# `a/b.md`, `production/`, `../../docs/x.md` — but not "` / `" or "`/`", which
# the roster produces from "`Update()` / `FixedUpdate()`" and "`game`/`product`".
_BACKTICK_PATH = r"`(?=[^`\s]*/)(?=[^`\s]*\w)[^`\s]+`"

WRITE_SCOPE_PATTERNS = (
    # verb → path: "write the report to `docs/x.md`", "Writes: `a/b/`", "결과를 `x/y.md`에 저장"
    re.compile(_WRITE_VERB + r"[^\n]{0,80}?" + _BACKTICK_PATH, re.I),
    # path → verb: "`a/b.md` — write", "`Documents/x.md` 를 작성"
    re.compile(_BACKTICK_PATH + r"[^\n]{0,40}?" + _WRITE_VERB, re.I),
    # an output / artifact section
    re.compile(r"^#{1,4}\s.*(output|artifact|deliverable|writes|산출물|출력|결과물)", re.I | re.M),
    # an explicit read-only statement *about the skill* — "Read-only / metadata
    # calls" (a list of API call kinds) must not count
    re.compile(
        r"(?:skill|mode|audit|orchestrator|command|this)\b[^.\n]{0,25}?\bread[- ]only"
        r"|does not (?:write|modify|create)"
        r"|writes? (?:nothing|no files)|no files are written"
        r"|파일을 (?:쓰지|수정하지|만들지) 않",
        re.I,
    ),
)

# next-step handoff (Check 5)
HANDOFF_PATTERNS = (
    re.compile(r"^#{1,4}\s.*(next step|follow[- ]?up|after this|recommended next)", re.I | re.M),
    re.compile(r"(recommended next|next step|follow[- ]?up)", re.I),
)

PHASE_HEADING = re.compile(r"^#{2,3}\s*(phase\s*\d+|step\s*\d+|\d+[\.\)])", re.I | re.M)
ANY_H2 = re.compile(r"^##\s+\S", re.M)

FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)

# --- description quality (Checks 8-10) ---------------------------------------
#
# `description` is not documentation. It is the routing instruction Codex reads
# when deciding whether to use a skill, and this repo ships a large public roster.
# A description that says only what a skill does, and not when to reach for it
# or when to reach past it, forces the model to infer. In operation, inference
# is a design failure: it shows up as a skill firing on the wrong task, or the
# right skill never firing at all, and nothing in this repo detects either.
#
# All three checks are WARNINGS, not failures. The existing roster will trip
# them broadly and fixing 130 files is not this change's job; the point is that
# a *new* skill lands with the defect visible. Run with --strict to see the
# backlog. Rationale: docs/design/v0.6.3-context-density-plan.md (A-2).

# Check 8 — "when NOT to use this". English and Korean.
NEGATIVE_CONDITION_PATTERNS = (
    re.compile(r"\bdo not\b|\bdon't\b|\bnot for\b|\bnever\b|\bavoid\b", re.I),
    re.compile(r"\binstead of\b|\brather than\b|\bas opposed to\b|\bnot when\b", re.I),
    re.compile(r"\bonly (?:for|when|if)\b|\bexcept\b", re.I),
    re.compile(r"않|아닌|아니라|제외|말 것|대신"),
)

# Check 10 — "when TO use this". A description with neither an explicit trigger
# clause nor a conditional is a capability blurb, not a routing rule.
TRIGGER_PATTERNS = (
    re.compile(r"\buse (?:this |it )?(?:skill |agent )?(?:for|when|whenever|any time|after|before)\b", re.I),
    re.compile(r"\b(?:trigger|invoke|reach for)(?:s|ed|ing)?\b", re.I),
    re.compile(r"\bwhen(?:ever)? the (?:user|caller|orchestrator)\b", re.I),
    re.compile(r"\b(?:run|call) (?:this|it) (?:at|after|before|when|during)\b", re.I),
    re.compile(r"할 때|하려면|경우에|요청(?:하|할)"),
)

# Check 9 — near-duplicate descriptions. Jaccard over content tokens.
#
# Measured against the full v0.6.2 roster (130 files, 8385 pairs):
#
#     max 0.438 · p99.9 0.216 · p99 0.121 · median 0.000
#
# The distribution is far tighter than intuition suggests, because these
# descriptions are long and Jaccard punishes length. The first guess at this
# constant was 0.60 and it never fired once — a check that cannot fire is worse
# than no check, because silence reads as "no confusables exist".
#
# 0.30 sits above p99.9 and selects exactly the pairs a human agrees are
# confusable: create-prd ~ design-system (0.44 — the product-track and
# game-track design docs, which is the pack-mixing failure Code Studios policy warns
# about), team-combat ~ team-polish (0.32), team-level ~ team-narrative (0.30).
#
# If this starts producing noise, change it here and record the new measurement
# in the commit message. Never inline it.
NEAR_DUPLICATE_THRESHOLD = 0.30

# Below this, two descriptions are too thin for a similarity score to mean
# anything, so Check 9 abstains rather than guessing.
SIMILARITY_MIN_TOKENS = 6

DESCRIPTION_STOPWORDS = frozenset(
    """a an and any are as at be by for from has have in into is it its of on or
    that the then this to use used uses using when with without you your which
    what while all can if not""".split()
)

WORD_RE = re.compile(r"[A-Za-z가-힣][A-Za-z0-9가-힣'-]*")


class Result:
    """Per-file lint outcome."""

    def __init__(self, path: str, kind: str):
        self.path = path
        self.kind = kind  # "skill" | "role"
        self.failures: list[str] = []
        self.warnings: list[str] = []
        self.description: str = ""  # kept for the cross-file Check 9 pass

    @property
    def verdict(self) -> str:
        if self.failures:
            return "NON-COMPLIANT"
        if self.warnings:
            return "WARNINGS"
        return "COMPLIANT"

    def issues(self) -> str:
        return "; ".join(self.failures + self.warnings)


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Extract top-level `key: value` pairs from the YAML frontmatter block.

    Deliberately naive — we only need presence and simple scalar values, and a
    YAML dependency is not worth it. Nested keys are ignored (they are indented,
    so the leading-character guard skips them).
    """
    m = FRONTMATTER.match(text)
    if not m:
        return None
    fields: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line[0].isspace() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def unquote(value: str) -> str:
    """Strip the surrounding quotes the frontmatter convention uses."""
    v = value.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    return v.replace('\\"', '"').strip()


def description_tokens(description: str) -> set[str]:
    """Content tokens of a description, for the Check 9 similarity score."""
    return {
        w.lower()
        for w in WORD_RE.findall(description)
        if w.lower() not in DESCRIPTION_STOPWORDS and len(w) > 1
    }


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def check_description_quality(r: Result, description: str) -> None:
    """Checks 8 and 10 — the two halves of a routing rule.

    Both are warnings. An empty description is already a failure elsewhere
    (Check 1 for skills, `empty description` for agents), so skip it here
    rather than reporting the same defect three times.
    """
    r.description = description
    if not description:
        return

    if not any(p.search(description) for p in NEGATIVE_CONDITION_PATTERNS):
        r.warnings.append(
            "Check 8: description says when to use but never when NOT to — "
            "the model has to infer the boundary"
        )

    if not any(p.search(description) for p in TRIGGER_PATTERNS):
        r.warnings.append(
            "Check 10: description has no explicit trigger clause "
            "(\"Use when…\", \"Trigger whenever…\") — it describes, it does not route"
        )


def flag_near_duplicates(results: list[Result]) -> None:
    """Check 9 — cross-file pass over every description in the run.

    Runs after all files are linted because confusability is a property of the
    roster, not of one file. Each pair is reported on both sides: whichever
    file the author is editing should see it.
    """
    scored = [
        (r, description_tokens(r.description))
        for r in results
        if len(description_tokens(r.description)) >= SIMILARITY_MIN_TOKENS
    ]
    for i, (ra, ta) in enumerate(scored):
        for rb, tb in scored[i + 1:]:
            score = jaccard(ta, tb)
            if score < NEAR_DUPLICATE_THRESHOLD:
                continue
            for mine, other in ((ra, rb), (rb, ra)):
                mine.warnings.append(
                    f"Check 9: description {score:.2f} similar to "
                    f"{label(other.path, other.kind)} — the model must guess between them"
                )


def lint_skill(path: str, text: str) -> Result:
    r = Result(path, "skill")
    fm = parse_frontmatter(text)
    body = FRONTMATTER.sub("", text, count=1)

    # Check 1 — required frontmatter fields
    if fm is None:
        r.failures.append("Check 1: no YAML frontmatter block")
        fm = {}
    else:
        missing = [f for f in SKILL_REQUIRED_FIELDS if f not in fm]
        if missing:
            r.failures.append("Check 1: missing " + ", ".join(missing))

    # Check 2 — >= 2 numbered phase headings (fall back to any 2 H2 headings)
    phases = len(PHASE_HEADING.findall(body))
    if phases < 2:
        h2 = len(ANY_H2.findall(body))
        if h2 < 2:
            r.failures.append(f"Check 2: only {max(phases, h2)} phase-like heading(s), need 2")
        phases = max(phases, h2)

    # Check 3 — verdict keywords
    if not any(k in body for k in VERDICT_KEYWORDS):
        r.failures.append("Check 3: no verdict keyword")

    # Check 4 — declare the write scope. Codex skills do not declare tool
    # allowlists in frontmatter, so this remains an advisory content check.
    if not any(p.search(body) for p in WRITE_SCOPE_PATTERNS):
        r.warnings.append(
            "Check 4: no write-scope declaration (name the paths written, or say read-only)"
        )

    # Check 5 — next-step handoff
    if not any(p.search(body) for p in HANDOFF_PATTERNS):
        r.warnings.append("Check 5: no next-step handoff")

    # Checks 8 & 10 — description as a routing rule (Check 9 runs cross-file)
    check_description_quality(r, unquote(fm.get("description", "")))

    return r


def lint_role(path: str, text: str) -> Result:
    r = Result(path, "role")
    fm = parse_frontmatter(text)
    if fm is None:
        r.failures.append("no YAML frontmatter block")
        return r
    missing = [f for f in ROLE_REQUIRED_FIELDS if f not in fm]
    if missing:
        r.failures.append("missing " + ", ".join(missing))
    if not fm.get("description", "").strip():
        r.failures.append("empty description")

    # Role references are selected by the studio orchestrator from description.
    check_description_quality(r, unquote(fm.get("description", "")))
    return r


# Compatibility alias for older imports while downstream tooling migrates.
lint_agent = lint_role


def collect(targets: list[str]) -> list[tuple[str, str]]:
    """Resolve CLI targets to (path, kind) pairs."""
    found: list[tuple[str, str]] = []
    for t in targets:
        t = t.rstrip("/")
        if os.path.isfile(t):
            kind = "role" if os.path.basename(os.path.dirname(t)) in {"agents", "roles"} else "skill"
            found.append((t, kind))
            continue
        if not os.path.isdir(t):
            print(f"lint_skills: no such path: {t}", file=sys.stderr)
            continue
        base = os.path.basename(t)
        if base in {"agents", "roles"}:
            for name in sorted(os.listdir(t)):
                if name.endswith(".md"):
                    found.append((os.path.join(t, name), "role"))
        else:
            # a skills/ root, or a single skill directory
            skill_md = os.path.join(t, "SKILL.md")
            if os.path.isfile(skill_md):
                found.append((skill_md, "skill"))
            else:
                for name in sorted(os.listdir(t)):
                    cand = os.path.join(t, name, "SKILL.md")
                    if os.path.isfile(cand):
                        found.append((cand, "skill"))
    return found


def label(path: str, kind: str) -> str:
    if kind == "skill":
        return os.path.basename(os.path.dirname(path))
    return os.path.splitext(os.path.basename(path))[0]


def load_baseline(path: str) -> dict[str, list[str]]:
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("known_failures", {})


def write_baseline(path: str, results: list[Result]) -> int:
    known = {
        label(r.path, r.kind): sorted(r.failures)
        for r in sorted(results, key=lambda x: x.path)
        if r.failures
    }
    payload = {
        "_comment": (
            "Pre-existing lint failures, recorded so CI blocks NEW violations without "
            "demanding the whole backlog be fixed first. Delete an entry once it is fixed "
            "— the linter reports stale entries."
        ),
        "known_failures": known,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"baseline written: {path} ({len(known)} known failures)")
    return 0


def main(argv: list[str]) -> int:
    force_utf8()  # 판정이 콘솔 코드페이지에 좌우되지 않게 (console_encoding 참조)
    ap = argparse.ArgumentParser(description="Structural linter for Code Studios skills and roles")
    ap.add_argument("targets", nargs="+", help="skills/, roles/, or a specific path")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    ap.add_argument("--quiet", action="store_true", help="print the summary line only")
    ap.add_argument(
        "--baseline",
        nargs="?",
        const=DEFAULT_BASELINE,
        help="ignore failures recorded in this baseline file (default: scripts/lint_baseline.json)",
    )
    ap.add_argument(
        "--write-baseline",
        nargs="?",
        const=DEFAULT_BASELINE,
        metavar="PATH",
        help="record current failures as the baseline and exit",
    )
    args = ap.parse_args(argv)

    files = collect(args.targets)
    if not files:
        print("lint_skills: nothing to lint", file=sys.stderr)
        return 2

    results = []
    for path, kind in files:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        results.append(lint_skill(path, text) if kind == "skill" else lint_role(path, text))

    # Check 9 is a property of the roster, not of any one file.
    flag_near_duplicates(results)

    if args.write_baseline:
        return write_baseline(args.write_baseline, results)

    baseline = load_baseline(args.baseline) if args.baseline else {}

    # Split failures into baselined (tolerated) and new (blocking).
    new_failures: list[Result] = []
    baselined: list[Result] = []
    for r in results:
        if not r.failures:
            continue
        known = baseline.get(label(r.path, r.kind))
        if known is not None and sorted(r.failures) == sorted(known):
            baselined.append(r)
        else:
            new_failures.append(r)

    warned = [r for r in results if r.warnings and not r.failures]

    # A baseline entry is stale only if we actually linted it this run AND it now
    # passes. Without the `in seen` guard a partial run (one skill, one dir) would
    # report every unlinted entry as fixed.
    seen = {label(r.path, r.kind) for r in results}
    failing_now = {label(r.path, r.kind) for r in baselined + new_failures}
    stale = sorted(k for k in baseline if k in seen and k not in failing_now)

    if not args.quiet:
        width = max(len(label(r.path, r.kind)) for r in results) + 2
        print(f"=== lint_skills: {len(results)} file(s) ===\n")
        for r in sorted(new_failures, key=lambda x: x.path):
            print(f"{label(r.path, r.kind):<{width}} NON-COMPLIANT  {r.issues()}")
        for r in sorted(warned, key=lambda x: x.path):
            print(f"{label(r.path, r.kind):<{width}} WARNINGS       {r.issues()}")
        for r in sorted(baselined, key=lambda x: x.path):
            print(f"{label(r.path, r.kind):<{width}} baselined      {r.issues()}")
        if stale:
            print("\nStale baseline entries (now passing — remove them):")
            for k in stale:
                print(f"  {k}")
        if new_failures or warned or baselined or stale:
            print()

    compliant = len(results) - len(new_failures) - len(baselined) - len(warned)
    summary = (
        f"Summary: {compliant} COMPLIANT, {len(warned)} WARNINGS, "
        f"{len(new_failures)} NON-COMPLIANT (of {len(results)})"
    )
    if baselined:
        summary += f" — {len(baselined)} baselined failure(s) tolerated"
    print(summary)

    if new_failures:
        return 1
    if args.strict and warned:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
