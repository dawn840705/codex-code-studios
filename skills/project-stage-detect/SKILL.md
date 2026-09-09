---
name: project-stage-detect
description: "Automatically analyze project state, detect stage, identify gaps, and recommend next steps based on existing artifacts. Use when user asks 'where are we in development', 'what stage are we in', 'full project audit'."
# Read-only diagnostic skill — no specialist agent delegation needed
---

# Project Stage Detection

This skill scans your project to determine its current development stage, completeness
of artifacts, and gaps that need attention. It's especially useful when:
- Starting with an existing project
- Onboarding to a codebase
- Checking what's missing before a milestone
- Understanding "where are we?"

Writes: `production/project-stage-report.md` (the stage report) — no other file is touched.

---

## Workflow

### 0. Run the Deterministic Phase Gate

Before any model-side scanning, run (Bash):

```bash
python3 ../../scripts/check_phase.py \
  --catalog ../../docs/workflow-catalog.yaml --json
```

This returns the track (game/product), current phase, per-step completion
verdicts, the current blocker, and any **dependency violations** (a completed
step whose required dependency was skipped). These verdicts are deterministic —
carry them into the report unchanged; do not re-derive completion by globbing
(`../../docs/deterministic-gates.md`). Name the gate in the report:
`check_phase.py → exit N`.

- `EXIT: 2` — surface each violation as a top-priority gap.
- `EXIT: 3` — the gate produced no verdict (say so explicitly); fall back to
  model-side classification below and mark Stage Confidence as CONCERNS at best.

The scans below add what the gate cannot see: content quality, code volume,
and gaps that need human judgment.

### 1. Scan Key Directories

Analyze project structure and content:

**Design Documentation** (`design/`):
- Count GDD files in `design/gdd/*.md`
- Check for game-concept.md, game-pillars.md, systems-index.md
- If systems-index.md exists, count total systems vs. designed systems
- Analyze completeness (Overview, Detailed Design, Edge Cases, etc.)
- Count narrative docs in `design/narrative/`
- Count level designs in `design/levels/`

**Source Code** (`src/`):
- Count source files (language-agnostic)
- Identify major systems (directories with 5+ files)
- Check for core/, gameplay/, ai/, networking/, ui/ directories
- Estimate lines of code (rough scale)

**Production Artifacts** (`production/`):
- Check for active sprint plans
- Look for milestone definitions
- Find roadmap documents

**Prototypes** (`prototypes/`):
- Count prototype directories
- Check for READMEs (documented vs undocumented)
- Assess if prototypes are archived or active

**Architecture Docs** (`docs/architecture/`):
- Count ADRs (Architecture Decision Records)
- Check for overview/index documents

**Tests** (`tests/`):
- Count test files
- Estimate test coverage (rough heuristic)

### 2. Classify Project Stage

**Normal path:** the stage is the `phase` field from check_phase.py (Step 0) —
it already applied stage.txt-first, artifact-inference-second, for the right
track. Report it with `Stage Confidence: PASS` and name the gate.

**Fallback (gate exit 3 only):** check `production/stage.txt` first —
if it exists, use its value (explicit override from `$gate-check`). Otherwise,
auto-detect using these heuristics (check from most-advanced backward):

| Stage | Indicators |
|-------|-----------|
| **Concept** | No game concept doc, brainstorming phase |
| **Systems Design** | Game concept exists, systems index missing or incomplete |
| **Technical Setup** | Systems index exists, engine not configured |
| **Pre-Production** | Engine configured, `src/` has <10 source files |
| **Production** | `src/` has 10+ source files, active development |
| **Polish** | Explicit only (set by `$gate-check` Production → Polish gate) |
| **Release** | Explicit only (set by `$gate-check` Polish → Release gate) |

### 3. Gap Identification

**DO NOT** just list missing files. Pair each gap with the question it raises and the
recommended skill. Answer the question yourself when the repository can (git log, READMEs,
`AGENTS.md`); leave the rest as questions in the report — they do not block the write.

- "Combat code (`src/gameplay/combat/`) but no `design/gdd/combat-system.md`. Prototyped first? → `$reverse-document design src/gameplay/combat`"
- "15 ADRs but no architecture overview → `$reverse-document architecture`"
- "No sprint plans in `production/`. Tracked elsewhere (Jira, Trello)? → `$sprint-plan`"
- "Game concept but no systems index → `$map-systems`"
- "3 prototypes with no READMEs. Experiments, or do they need documentation?"

### 4. Generate Stage Report

Use template: `../../docs/templates/project-stage-report.md`

**Report structure**:
```markdown
# Project Stage Analysis

**Date**: [date]
**Stage**: [Concept/Systems Design/Technical Setup/Pre-Production/Production/Polish/Release]
**Stage Confidence**: [PASS — clearly detected / CONCERNS — ambiguous signals / FAIL — critical gaps block progress]

## Completeness Overview
- Design: [X%] ([N] docs, [gaps])
- Code: [X%] ([N] files, [systems])
- Architecture: [X%] ([N] ADRs, [gaps])
- Production: [X%] ([status])
- Tests: [X%] ([coverage estimate])

## Gaps Identified
1. [Gap description + clarifying question]
2. [Gap description + clarifying question]

## Recommended Next Steps
[Priority-ordered list based on stage and role]
```

### 5. Role-Filtered Recommendations (Optional)

If user provided a role argument (e.g., `$project-stage-detect programmer`):

**Programmer**:
- Focus on architecture docs, test coverage, missing ADRs
- Code-to-docs gaps

**Designer**:
- Focus on GDD completeness, missing design sections
- Prototype documentation

**Producer**:
- Focus on sprint plans, milestone tracking, roadmap
- Cross-team coordination docs

**General** (no role):
- Holistic view of all gaps
- Highest-priority items across domains

### 6. Write the Report

Write the full analysis to `production/project-stage-report.md`. Then report:

```
Stage: [stage] (check_phase.py → exit N) · Confidence: [PASS/CONCERNS/FAIL]
Gaps: 1. [Gap 1 + question] 2. [Gap 2 + question]
Next: [Priority 1] · [Priority 2] · [Priority 3]
Written: production/project-stage-report.md — revert: git checkout -- production/project-stage-report.md
```

---

## Example Usage

```bash
# General project analysis
$project-stage-detect

# Programmer-focused analysis
$project-stage-detect programmer

# Designer-focused analysis
$project-stage-detect designer
```

---

## Follow-Up Actions

After generating the report, suggest relevant next steps:

- **Concept exists but no systems index?** → `$map-systems` to decompose into systems
- **Missing design docs?** → `$reverse-document design src/[system]`
- **Missing architecture docs?** → `$architecture-decision` or `$reverse-document architecture`
- **Prototypes need documentation?** → `$reverse-document concept prototypes/[name]`
- **No sprint plan?** → `$sprint-plan`
- **Approaching milestone?** → `$milestone-review`

---

## Collaborative Protocol

1. **Gate first**: the stage comes from `check_phase.py`'s exit code, not from a guess.
2. **Gaps as questions**: each gap carries its question and the skill that closes it; open questions ride in the report, never block it.
3. **Write and report**: the report is a `production/` artifact (R) — write it, name the path and the revert command.
4. **Never run the recommended skills yourself**: this is a diagnostic; the user picks the next step.
