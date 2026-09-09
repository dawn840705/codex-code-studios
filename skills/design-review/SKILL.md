---
name: design-review
description: "Reviews a game design document for completeness, internal consistency, implementability, and adherence to project design standards. Run this before handing a design document to programmers."
---

> **Track check — this skill is game-framed.** Resolve `production/track.txt` (or the
> session's `PROJECT_TYPE` line) before Phase 0.
>
> - **`game`** — run as written.
> - **`product`** (web / mobile / service) — substitute as you read: player becomes user,
>   game becomes product, GDD becomes PRD (`design/gdd/` → `product/prd/`), engine becomes
>   the stack pinned in `.codex/studio/technical-preferences.md`. You are reviewing a PRD, not a GDD. The completeness check maps onto the PRD template's sections; "implementable" means an engineer can build it from the doc alone, and every success metric must be measurable.
> - **Unresolved** — ask once which track this is, write the answer to `production/track.txt`,
>   then continue. A greenfield project has no signal either way; do not infer one from the
>   repository contents.

## Phase 0: Parse Arguments

Extract `--depth [full|lean|solo]` if present. Default is `full` when no flag is given.

**Note**: `--depth` controls the *analysis depth* of this skill (how many specialist agents are spawned). It is independent of the global review mode in `production/review-mode.txt`, which controls director gate spawning. These are two different concepts — `--depth` is about how thoroughly *this* skill analyses the document.

- **`full`**: Complete review — all phases + specialist agent delegation (Phase 3b)
- **`lean`**: All phases, no specialist agents — faster, single-session analysis
- **`solo`**: Phases 1-4 only, no delegation, no Phase 5 next-step prompt — use when called from within another skill

---

## Phase 1: Load Documents

Read the target design document in full. Read AGENTS.md to understand project context and standards. Read related design documents referenced or implied by the target doc (check `design/gdd/` for related systems).

**Dependency graph validation:** For every system listed in the Dependencies section, use Glob to check whether its GDD file exists in `design/gdd/`. Flag any that don't exist yet — these are broken references that downstream authors will hit.

**Lore/narrative alignment:** If `design/gdd/game-concept.md` or any file in `design/narrative/` exists, read it. Note any mechanical choices in this GDD that contradict established world rules, tone, or design pillars. Pass this context to `game-designer` in Phase 3b.

**Prior review check:** Check whether `design/gdd/reviews/[doc-name]-review-log.md` exists. If it does, read the most recent entry — note what verdict was given and what blocking items were listed. This session is a re-review; track whether prior items were addressed.

---

## Phase 2: Completeness Check

Evaluate against the Design Document Standard checklist:

- [ ] Has Overview section (one-paragraph summary)
- [ ] Has Player Fantasy section (intended feeling)
- [ ] Has Detailed Rules section (unambiguous mechanics)
- [ ] Has Formulas section (all math defined with variables)
- [ ] Has Edge Cases section (unusual situations handled)
- [ ] Has Dependencies section (other systems listed)
- [ ] Has Tuning Knobs section (configurable values identified)
- [ ] Has Acceptance Criteria section (testable success conditions)

---

## Phase 3: Consistency and Implementability

**Internal consistency:**
- Do the formulas produce values that match the described behavior?
- Do edge cases contradict the main rules?
- Are dependencies bidirectional (does the other system know about this one)?

**Implementability:**
- Are the rules precise enough for a programmer to implement without guessing?
- Are there any "hand-wave" sections where details are missing?
- Are performance implications considered?

**Cross-system consistency:**
- Does this conflict with any existing mechanic?
- Does this create unintended interactions with other systems?
- Is this consistent with the game's established tone and pillars?

---

## Phase 3b: Adversarial Specialist Review (full mode only)

**Skip this phase in `lean` or `solo` mode.**

**This phase is MANDATORY in full mode.** Do not skip it.

**Before spawning any agents**, print this notice:
> "Full review: spawning specialist agents in parallel. This typically takes 8–15 minutes. Use `--review lean` for faster single-session analysis."

### Step 1 — Identify all domains the GDD touches

Read the GDD and identify every domain present. A GDD can touch multiple domains simultaneously — be thorough. Common signals:

| If the GDD contains... | Spawn these agents |
|------------------------|-------------------|
| Costs, prices, drops, rewards, economy | `economy-designer` |
| Combat stats, damage, health, DPS | `game-designer`, `systems-designer` |
| AI behaviour, pathfinding, targeting | `ai-programmer` |
| Level layout, spawning, wave structure | `level-designer` |
| Player progression, XP, unlocks | `economy-designer`, `game-designer` |
| UI, HUD, menus, player-facing displays | `ux-designer`, `ui-programmer` |
| Dialogue, quests, story, lore | `narrative-director` |
| Animation, feel, timing, juice | `gameplay-programmer` |
| Multiplayer, sync, replication | `network-programmer` |
| Audio cues, music triggers | `audio-director` |
| Performance, draw calls, memory | `performance-analyst` |
| Engine-specific patterns or APIs | Primary engine specialist (from `.codex/studio/technical-preferences.md`) |
| Acceptance criteria, test coverage | `qa-lead` |
| Data schema, resource structure | `systems-designer` |
| Any gameplay system | `game-designer` (always) |

**Always spawn `game-designer` and `systems-designer` as a baseline minimum.** Every GDD touches their domain.

### Step 2 — Spawn all relevant specialists in parallel

**CRITICAL: Task in this skill spawns a SUBAGENT — a separate independent Codex subagent
with its own context window. It is NOT task tracking. Do NOT simulate specialist
perspectives internally. Do NOT reason through domain views yourself. You MUST issue
actual Codex subagent calls. A simulated review is not a specialist review.**

Issue all Codex subagent calls simultaneously. Do NOT spawn one at a time.

**Prompt each specialist adversarially:**
> "Here is the GDD for [system] and the main review's structural findings so far.
> Your job is NOT to validate this design — your job is to find problems.
> Challenge the design choices from your domain expertise. What is wrong,
> underspecified, likely to cause problems, or missing entirely?
> Be specific and critical. Disagreement with the main review is welcome."

**Additional instructions per agent type:**

- **`game-designer`**: Anchor your review to the Player Fantasy stated in Section B of this GDD. Does this design actually deliver that fantasy? Would a player feel the intended experience? Flag any rules that serve implementability but undermine the stated feeling.

- **`systems-designer`**: For every formula in the GDD, plug in boundary values (minimum and maximum plausible inputs). Report whether any outputs go degenerate — negative values, division by zero, infinity, or nonsensical results at the extremes.

- **`qa-lead`**: Review every acceptance criterion. Flag any that are not independently testable — phrases like "feels balanced", "works correctly", "performs well" are not ACs. Suggest concrete rewrites for any that fail this test.

### Step 3 — Senior lead review

After all specialists respond, spawn `creative-director` as the **senior reviewer**:
- Provide: the GDD, all specialist findings, any disagreements between them
- Ask: "Synthesise these findings. What are the most important issues? Do you agree with the specialists? What is your overall verdict on this design?"
- The creative-director's synthesis becomes the **final verdict** in Phase 4.

### Step 4 — Surface disagreements

If specialists disagree with each other or with the creative-director, do NOT silently pick one view. Present the disagreement explicitly in Phase 4; the creative-director synthesis sets the verdict, and the dissent stays on record for the user.

Mark every finding with its source: `[game-designer]`, `[economy-designer]`, `[creative-director]` etc.

---

## Phase 4: Output Review

```
## Design Review: [Document Title]
Specialists consulted: [list agents spawned]
Re-review: [Yes — prior verdict was X on YYYY-MM-DD / No — first review]

### Completeness: [X/8 sections present]
[List missing sections]

### Dependency Graph
[List each declared dependency and whether its GDD file exists on disk]
- ✓ enemy-definition-data.md — exists
- ✗ loot-system.md — NOT FOUND (file does not exist yet)

### Required Before Implementation
[Numbered list — blocking issues only. Each item tagged with source agent.]

### Recommended Revisions
[Numbered list — important but not blocking. Source-tagged.]

### Specialist Disagreements
[Any cases where agents disagreed with each other or with the main review.
Present both sides — do not silently resolve.]

### Nice-to-Have
[Minor improvements, low priority.]

### Senior Verdict [creative-director]
[Creative director's synthesis and overall assessment.]

### Scope Signal
Estimate implementation scope based on: dependency count, formula count,
systems touched, and whether new ADRs are required.
- **S** — single system, no formulas, no new ADRs, <3 dependencies
- **M** — moderate complexity, 1-2 formulas, 3-6 dependencies
- **L** — multi-system integration, 3+ formulas, may require new ADR
- **XL** — cross-cutting concern, 5+ dependencies, multiple new ADRs likely
Label clearly: "Rough scope signal: M (producer should verify before sprint planning)"

### Verdict: [APPROVED / NEEDS REVISION / MAJOR REVISION NEEDED]
```

This skill is read-only — no files are written during Phase 4.

---

## Phase 5: Next Steps

Close with a report; the verdict decides what happens next.

**If APPROVED** (first-pass, no revision needed): go straight to the systems-index update and the review log below.

**If NEEDS REVISION or MAJOR REVISION NEEDED — revise now:**

Work through every blocking item that has a defect ticket (the finding cites the section and the evidence). Where a fix needs a design decision you cannot resolve from the GDD and existing docs alone, do not guess and do not stop: add it to the GDD's Open Questions marked `[확인 필요]` and leave that item open. Record each fix in a summary table (blocker → fix applied) and report the GDD path with its revert command (`git checkout -- <path>`).

A revised GDD is not Approved by this run: the systems index gets `In Review`, and the recommended next step is a fresh `$design-review [doc-path]` in a new session (a full re-review runs 5 agents and needs clean context — note current context usage and recommend `/clear` above ~50%). Marking the revisions Approved without re-review is the user's call; say so in the report.

**Systems index update (always):**

Update `design/gdd/systems-index.md` to mark [system] as `Approved` (verdict APPROVED) or `In Review` (any other verdict). Report the path and the revert command.

**Review log (always):**

Append the review summary to `design/gdd/reviews/[doc-name]-review-log.md` — a revision history so future re-reviews can track what changed. Report the path.

Entry format:
```
## Review — [YYYY-MM-DD] — Verdict: [APPROVED / NEEDS REVISION / MAJOR REVISION NEEDED]
Scope signal: [S/M/L/XL]
Specialists: [list]
Blocking items: [count] | Recommended: [count]
Summary: [2-3 sentence summary of key findings from creative-director verdict]
Prior verdict resolved: [Yes / No / First review]
```

---

**Recommended next — always after all file writes complete:**

Check project state and close with one recommended next step plus the alternatives that apply:

Before building the list, read:
- `design/gdd/systems-index.md` — find any system with Status: In Review or NEEDS REVISION (other than the one just reviewed)
- Count `.md` files in `design/gdd/` (excluding game-concept.md, systems-index.md) to determine if `$review-all-gdds` is worth offering (≥2 GDDs)
- Find the next system with Status: Not Started in design order

Build the list dynamically — only include steps that are genuinely next:
- `[_] Run $design-review [other-gdd-path] — [system name] is still [In Review / NEEDS REVISION]` (include if another GDD needs review)
- `[_] Run $consistency-check — verify this GDD's values don't conflict with existing GDDs` (always include if ≥1 other GDD exists)
- `[_] Run $review-all-gdds — holistic design-theory review across all designed systems` (include if ≥2 GDDs exist)
- `[_] Run $design-system [next-system] — next in design order` (always include, name the actual system)
- `[_] Stop here`

Put the most pipeline-advancing step first as `Recommended next`; list the others under it. End the report with the paths written and their revert commands.
