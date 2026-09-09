---
name: playtest-report
description: "Generates a structured playtest report template or analyzes existing playtest notes into a structured format. Use this to standardize playtest feedback collection and analysis."
---

## Phase 1: Parse Arguments

Resolve the review mode (once, store for all gate spawns this run):
1. If `--review [full|lean|solo]` was passed → use that
2. Else read `production/review-mode.txt` → use that value
3. Else → default to `lean`

See `../../docs/director-gates.md` for the full check pattern.

Determine the mode:

- `new` → generate a blank playtest report template
- `analyze [path]` → read raw notes and fill in the template with structured findings

---

## Phase 2A: New Template Mode

Generate this template and output it to the user:

```markdown
# Playtest Report

## Session Info
- **Date**: [Date]
- **Build**: [Version/Commit]
- **Duration**: [Time played]
- **Tester**: [Name/ID]
- **Platform**: [PC/Console/Mobile]
- **Input Method**: [KB+M / Gamepad / Touch]
- **Session Type**: [First time / Returning / Targeted test]

## Test Focus
[What specific features or flows were being tested]

## First Impressions (First 5 minutes)
- **Understood the goal?** [Yes/No/Partially]
- **Understood the controls?** [Yes/No/Partially]
- **Emotional response**: [Engaged/Confused/Bored/Frustrated/Excited]
- **Notes**: [Observations]

## Gameplay Flow
### What worked well
- [Observation 1]

### Pain points
- [Issue 1 -- Severity: High/Medium/Low]

### Confusion points
- [Where the player was confused and why]

### Moments of delight
- [What surprised or pleased the player]

## Bugs Encountered
| # | Description | Severity | Reproducible |
|---|-------------|----------|-------------|

## Feature-Specific Feedback
### [Feature 1]
- **Understood purpose?** [Yes/No]
- **Found engaging?** [Yes/No]
- **Suggestions**: [Tester suggestions]

## Quantitative Data (if available)
- **Deaths**: [Count and locations]
- **Time per area**: [Breakdown]
- **Items used**: [What and when]
- **Features discovered vs missed**: [List]

## Overall Assessment
- **Would play again?** [Yes/No/Maybe]
- **Difficulty**: [Too Easy / Just Right / Too Hard]
- **Pacing**: [Too Slow / Good / Too Fast]
- **Session length preference**: [Shorter / Good / Longer]

## Top 3 Priorities from this session
1. [Most important finding]
2. [Second priority]
3. [Third priority]
```

---

## Phase 2B: Analyze Mode

Read the raw notes at the provided path (no path and no `production/qa/playtests/*.raw.md` → K2, Verdict: **BLOCKED**). Cross-reference with existing design documents. Fill in the template above with structured findings. Flag any playtest observations that conflict with design intent.

Session facts the notes do not carry (what the tester did, felt, or said) are K3 — only a
human observed them. Mark each `[DEFERRED: needs observer]`, keep going, and list the
questions once in the final report.

---

## Phase 3: Action Routing

Categorize all findings into four buckets:

- **Design changes needed** — fun issues, player confusion, broken mechanics, observations that conflict with the GDD's intended experience
- **Balance adjustments** — numbers feel wrong, difficulty too spiked or too flat
- **Bug reports** — clear implementation defects that are reproducible
- **Polish items** — not blocking progress, but friction or feel issues for later

Present the categorized list, then route:

- **Design changes:** "Run `$propagate-design-change [path]` on the affected design document to find downstream impacts before making changes."
- **Balance adjustments:** "Run `$balance-check [system]` to verify the full balance picture before tuning values."
- **Bugs:** "Use `$bug-report` to formally track these."
- **Polish items:** "Add to the polish backlog in `production/` when the team reaches that phase."

---

## Phase 3b: Creative Director Player Experience Review

**Review mode check** — apply before spawning CD-PLAYTEST:
- `solo` → skip. Note: "CD-PLAYTEST skipped — Solo mode." Proceed to Phase 4 (save the report).
- `lean` → skip (not a PHASE-GATE). Note: "CD-PLAYTEST skipped — Lean mode." Proceed to Phase 4 (save the report).
- `full` → spawn as normal.

After categorising findings, spawn `creative-director` as a Codex subagent using gate **CD-PLAYTEST** (`../../docs/director-gates.md`).

Pass: the structured report content, game pillars and core fantasy (from `design/gdd/game-concept.md`), the specific hypothesis being tested.

Fold the creative director's assessment into the report. If CONCERNS or REJECT, add a `## Creative Director Assessment` section capturing the verdict and feedback. If APPROVE, note the approval in the report. The verdict is advisory; it does not stop the save.

---

## Phase 4: Save Report

Write the report to `production/qa/playtests/playtest-[date]-[tester].md` (create the
directory if needed). Report the path, the revert command (`git checkout -- <path>`), and
any `[DEFERRED: needs observer]` questions.

---

## Phase 5: Next Steps

Verdict: **COMPLETE** — playtest report generated.

- Act on the highest-priority finding category first.
- After addressing design changes: re-run `$design-review` on the updated GDD.
- After fixing bugs: re-run `$bug-triage` to update priorities.
