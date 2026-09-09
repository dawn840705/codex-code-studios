---
name: skill-improve
description: "Improve a skill using a test-fix-retest loop. Runs static checks, proposes targeted fixes, rewrites the skill, re-tests, and keeps or reverts based on score change."
---

# Skill Improve

Runs an improvement loop on a single skill:
test → fix → retest → keep or revert.

---

## Phase 1: Parse Argument

Read the skill name from the first argument. If missing, output usage and stop:

```
Usage: $skill-improve [skill-name]
Example: $skill-improve tech-debt
```

Verify `../[name]/SKILL.md` exists. If not, stop with:
"Skill '[name]' not found."

---

## Phase 2: Baseline Test

Run `$skill-test static [name]` and record the baseline score:
- Count of FAILs
- Count of WARNs
- Which specific checks failed

Display to the user:
```
Static baseline:   [N] failures, [M] warnings
Failing: Check 1 (frontmatter), Check 3 (no verdict keyword)
```

If baseline is 0 FAILs and 0 WARNs, stop: "This skill already passes the
Codex-format structural and routing checks. No improvement is needed."

---

## Phase 3: Diagnose

Read the full skill file at `../[name]/SKILL.md`.

For each failing or warning **static** check, identify the exact gap:

- **Check 1 fail** → whether `name` or `description` is missing or invalid
- **Check 2 fail** → how many phases found vs. minimum required
- **Check 3 fail** → no verdict keywords anywhere in the skill body
- **Check 4 warn** → no explicit boundary for user-owned file writes
- **Check 5 warn** → no follow-up or next-step section at the end
- **Check 8/10 warn** → description lacks a negative boundary or explicit trigger
- **Check 9 warn** → description is too similar to another skill and needs a clearer boundary

Record the full combined diagnosis; it goes into the final report.

---

## Phase 4: Fix

Write a targeted fix for each failure and warning. Only change what is failing — do not
rewrite sections that are passing. Keep the before/after blocks for the report.

---

## Phase 5: Write and Retest

Write the improved skill to `../[name]/SKILL.md` (the file is git-tracked; the revert
path is `git checkout -- ../[name]/SKILL.md`).

Re-run `$skill-test static [name]` and record the new static score.

Display the comparison:
```
Static:   Before [N] failures, [M] warnings  →  After [N'] failures, [M'] warnings
Change: improved / no change / worse
```

---

## Phase 6: Verdict

Count the combined total: static FAILs + static WARNs.

**If the score improved (combined issue count is lower than baseline):**
Report: "Score improved. Changes kept." with the before/after blocks and the revert command.

**If combined score is the same or worse:**
Run `git checkout -- ../[name]/SKILL.md` yourself. Report: "Combined score did not
improve; reverted." with what changed and why it may not have helped.

---

## Phase 7: Next Steps

- Run `$skill-test static all` to find the next skill with failures.
- Run `$skill-improve [next-name]` to continue the loop on another skill.
- Run `$skill-test audit` to see overall coverage progress.
