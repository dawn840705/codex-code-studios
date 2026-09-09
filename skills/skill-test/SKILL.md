---
name: skill-test
description: "Validate Code Studios skill and role files with the repository's executable Codex-format linter. Use when a SKILL.md or orchestrator role guide changes, before release, or when the user requests a plugin compliance audit. Do not use as a behavioral test for an unrelated consumer project."
---

# Skill Test

Use the executable linter as the source of truth. Do not reproduce its verdict by
manually scanning files when Python is available.

Read-only: writes nothing — the linter and pytest only read `skills/`, `tests/`, and `scripts/lint_baseline.json`.

## Phase 1: Select scope

- `static all` or no argument: all skills plus all orchestrator role guides.
- `static NAME`: only `../NAME/SKILL.md`.
- `audit`: full roster, frontmatter, duplicate-description warnings, and counts.

If the named skill does not exist, report `BLOCKED` and the missing path.

## Phase 2: Run the Codex-format linter

For the full roster, run from this skill directory or resolve the paths to the
same plugin root:

```bash
python3 ../../scripts/lint_skills.py \
  .. \
  ../studio-orchestrator/references/roles \
  --baseline ../../scripts/lint_baseline.json
```

For one skill:

```bash
python3 ../../scripts/lint_skills.py ../NAME \
  --baseline ../../scripts/lint_baseline.json
```

Exit `0` means no new structural failure. Exit `1` means at least one new
failure; warnings and explicitly baselined debt remain visible. Exit `2` means
the invocation or target is invalid.

The linter requires Codex skill frontmatter fields `name` and `description`,
checks body structure and verdict/handoff conventions, requires a write-scope
declaration (Check 4: the paths the skill writes, or an explicit read-only
statement — "May I write…?" wording declares no scope and does not count), and
evaluates routing description quality. Role references require `name` and
`description` only; Claude-only fields such as `model`, `tools`, and `maxTurns`
must not return.

## Phase 3: Verify manifest counts

For `audit` and `static all`, also run:

```bash
pytest -q ../../tests/test_manifest_sync.py ../../tests/test_skill_lint.py
```

Confirm that `.codex-plugin/plugin.json` advertises the filesystem count and
that every `docs/agent-packs.yaml` role exists under the orchestrator references.

## Phase 4: Report

Report:

- files checked;
- new failures, warnings, and baselined failures separately;
- manifest/roster test result;
- exact next file to fix.

Return `COMPLIANT` only when the linter exits 0 and required tests pass. Return
`NON-COMPLIANT` for a new failure and `BLOCKED` when required tooling is missing.

## Recommended next

Use `$skill-improve NAME` for one failing skill. If only routing-description
warnings remain, batch those separately rather than mixing them with a structural fix.
