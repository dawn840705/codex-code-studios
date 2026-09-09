---
name: map-systems
description: "Decompose a game concept into individual systems, map dependencies, prioritize design order, and create the systems index."
---

When this skill is invoked:

## Parse Arguments

Two modes:

- **No argument**: `$map-systems` — Run the full decomposition workflow (Phases 1-5)
  to create or update the systems index.
- **`next`**: `$map-systems next` — Pick the highest-priority undesigned system
  from the index and hand off to `$design-system` (Phase 6).

Also resolve the review mode (once, store for all gate spawns this run):
1. If `--review [full|lean|solo]` was passed → use that
2. Else read `production/review-mode.txt` → use that value
3. Else → default to `lean`

See `../../docs/director-gates.md` for the full check pattern.

---

## Phase 1: Read Concept (Required Context)

Read the game concept and any existing design work. This provides the raw material
for systems decomposition.

**Required:**
- Read `design/gdd/game-concept.md` — **fail with a clear message if missing**:
  > "No game concept found at `design/gdd/game-concept.md`. Run `$brainstorm` first
  > to create one, then come back to decompose it into systems."

**Optional (read if they exist):**
- Read `design/gdd/game-pillars.md` — pillars constrain priority and scope
- Read `design/gdd/systems-index.md` — if exists, **resume** from where it left off
  (update, don't recreate from scratch)
- Glob `design/gdd/*.md` — check which system GDDs already exist

**If the systems index already exists:**
- Read it and report current status: "[N] systems ([M] designed, [K] not started)."
- With no argument, update the index (Phases 2–5, resume mode). `next` goes to
  Phase 6. Priorities are revised only where Phase 4 finds a reason; name it.

---

## Phase 2: Systems Enumeration (Collaborative)

Extract and identify all systems the game needs. This is the creative core of the
skill — concept docs rarely enumerate every system explicitly, so the inference
below is the work.

### Step 2a: Extract Explicit Systems

Scan the game concept for directly mentioned systems and mechanics:
- Core Mechanics section (most explicit)
- Core Loop section (implies what systems drive each loop tier)
- Technical Considerations section (networking, procedural generation, etc.)
- MVP Definition section (required features = required systems)

### Step 2b: Identify Implicit Systems

For each explicit system, identify the **hidden systems** it implies. Games always
need more systems than the concept doc mentions. Use this inference pattern:

- "Inventory" implies: item database, equipment slots, weight/capacity rules,
  inventory UI, item serialization for save/load
- "Combat" implies: damage calculation, health system, hit detection, status effects,
  enemy AI, combat UI (health bars, damage numbers), death/respawn
- "Open world" implies: streaming/chunking, LOD system, fast travel, map/minimap,
  point of interest tracking, world state persistence
- "Multiplayer" implies: networking layer, lobby/matchmaking, state synchronization,
  anti-cheat, network UI (ping, player list)
- "Crafting" implies: recipe database, ingredient gathering, crafting UI,
  success/failure mechanics, recipe discovery/learning
- "Dialogue" implies: dialogue tree system, dialogue UI, choice tracking, NPC
  state management, localization hooks
- "Progression" implies: XP system, level-up mechanics, skill tree, unlock
  tracking, progression UI, progression save data

Explain in conversation text why each implicit system is needed (with examples).

### Step 2c: Self-Review

Present the enumeration organized by category. For each system, show:
- Name
- Category
- Brief description (1 sentence)
- Whether it was explicit (from concept) or implicit (inferred)

Then check it against the concept's MVP Definition and anti-pillars: systems the
MVP needs but the list lacks are added; systems an anti-pillar excludes are cut.
Name each change. Continue — the user reviews the whole index once, in Phase 5b.

---

## Phase 3: Dependency Mapping (Collaborative)

For each system, determine what it depends on. A system "depends on" another if
it cannot function without that other system existing first.

### Step 3a: Map Dependencies

For each system, list its dependencies. Use these dependency heuristics:
- **Input/output dependencies**: System A produces data System B needs
- **Structural dependencies**: System A provides the framework System B plugs into
- **UI dependencies**: Every gameplay system has a corresponding UI system that
  depends on it (but UI is designed after the gameplay system)

### Step 3b: Sort by Dependency Order

Arrange systems into layers:
1. **Foundation**: Systems with zero dependencies (designed and built first)
2. **Core**: Systems depending only on Foundation systems
3. **Feature**: Systems depending on Core systems
4. **Presentation**: UI and feedback systems that wrap gameplay systems
5. **Polish**: Meta-systems, tutorials, analytics, accessibility

### Step 3c: Detect Circular Dependencies

Check for cycles in the dependency graph. If found:
- Highlight them to the user
- Propose resolutions (interface abstraction, simultaneous design, breaking the
  cycle by defining a contract between the two systems)

### Step 3d: Present to User

Show the dependency map as a layered list. Highlight:
- Any circular dependencies
- Any "bottleneck" systems (many others depend on them — these are high-risk)
- Any systems with no dependents (leaf nodes — lower risk, can be designed late)

Continue; the ordering is reviewed with the index in Phase 5b.

**Review mode check** — apply before spawning TD-SYSTEM-BOUNDARY:
- `solo` → skip. Note: "TD-SYSTEM-BOUNDARY skipped — Solo mode." Proceed to priority assignment.
- `lean` → skip (not a PHASE-GATE). Note: "TD-SYSTEM-BOUNDARY skipped — Lean mode." Proceed to priority assignment.
- `full` → spawn as normal.

**After dependency mapping is complete, spawn `technical-director` as a Codex subagent using gate TD-SYSTEM-BOUNDARY (`../../docs/director-gates.md`) before proceeding to priority assignment.**

Pass: the dependency map summary, layer assignments, bottleneck systems list, any circular dependency resolutions.

Report the assessment. If REJECT, rework the boundaries via `$self-loop` where a defect ticket exists (`rules/self-loop.md` § 2.1) before priority assignment. If CONCERNS, fix the ticketed items, note the rest inline in the systems index, and continue.

---

## Phase 4: Priority Assignment (Collaborative)

Assign each system to a priority tier based on what milestone it's needed for.

### Step 4a: Auto-Assign Based on Concept

Use these heuristics for initial assignment:
- **MVP**: Systems mentioned in the concept's "Required for MVP" section, plus their
  Foundation-layer dependencies
- **Vertical Slice**: Systems needed for a complete experience in one area
- **Alpha**: All remaining gameplay systems
- **Full Vision**: Polish, meta, and nice-to-have systems

### Step 4b: Explain the Tiers

Present the priority assignments in a table. For each tier, explain why systems
were placed there, e.g. "I placed [system] in MVP because the core loop requires
it — without [system], the 30-second loop can't function." Continue.

**"Why" column guidance**: When explaining why each system was placed in a priority tier, mix technical necessity with player-experience reasoning. Do not use purely technical justifications like "Combat needs damage math" — connect to player experience where relevant. Examples of good "Why" entries:
- "Required for the core loop — without it, placement decisions have no consequence (Pillar 2: Placement is the Puzzle)"
- "Ballista's punch-through identity is established here — this stat definition is what makes it feel different from Archer"
- "Foundation for all economy decisions — players must understand upgrade costs to make meaningful placement choices"

Pure technical necessity ("X depends on Y") is insufficient alone when the system directly shapes player experience.

**Review mode check** — apply before spawning PR-SCOPE:
- `solo` → skip. Note: "PR-SCOPE skipped — Solo mode." Proceed to writing the systems index.
- `lean` → skip (not a PHASE-GATE). Note: "PR-SCOPE skipped — Lean mode." Proceed to writing the systems index.
- `full` → spawn as normal.

**After priorities are assigned, spawn `producer` as a Codex subagent using gate PR-SCOPE (`../../docs/director-gates.md`) before writing the index.**

Pass: total system count per milestone tier, estimated implementation volume per tier (system count × average complexity), team size, stated project timeline.

Report the assessment. If UNREALISTIC, move the lowest-value MVP systems down a tier until the producer's capacity arithmetic holds, and name each move. If CONCERNS, fix the ticketed items, note the rest, and continue.

### Step 4c: Determine Design Order

Combine dependency sort + priority tier to produce the final design order:
1. MVP Foundation systems first
2. MVP Core systems second
3. MVP Feature systems third
4. Vertical Slice Foundation/Core systems
5. ...and so on

This is the order the team should write GDDs in.

---

## Phase 5: Create Systems Index (Write)

### Step 5a: Draft the Document

Using the template at `../../docs/templates/systems-index.md`, populate the
systems index with all data from Phases 2-4:
- Fill the enumeration table
- Fill the dependency map
- Fill the recommended design order
- Fill the high-risk systems
- Fill progress tracker (all systems "Not Started" initially, unless GDDs already exist)

### Step 5b: Write and Report

Write the file to `design/gdd/systems-index.md`; report the path and the revert
command (`git checkout -- design/gdd/systems-index.md`). Then present the summary
— this is the user's single review point for the index:
- Total systems count by category
- MVP system count
- First 3 systems in the design order
- Any high-risk items
- Changes made in Steps 2c and 4b, with reasons

**Review mode check** — apply before spawning CD-SYSTEMS:
- `solo` → skip. Note: "CD-SYSTEMS skipped — Solo mode." Proceed to Phase 7 next steps.
- `lean` → skip (not a PHASE-GATE). Note: "CD-SYSTEMS skipped — Lean mode." Proceed to Phase 7 next steps.
- `full` → spawn as normal.

**After the systems index is written, spawn `creative-director` as a Codex subagent using gate CD-SYSTEMS (`../../docs/director-gates.md`).**

Pass: systems index path, game pillars and core fantasy (from `design/gdd/game-concept.md`), MVP priority tier system list.

Report the assessment. If REJECT, rework the system set via `$self-loop` where a defect ticket exists before GDD authoring begins. If CONCERNS, fix the ticketed items and record the rest in the systems index as a `> **Creative Director Note**` at the top of the relevant tier section.

### Step 5c: Update Session State

After writing, create `production/session-state/active.md` if it does not exist, then update it with:
- Task: Systems decomposition
- Status: Systems index created
- File: design/gdd/systems-index.md
- Next: Design individual system GDDs

**Verdict: COMPLETE** — systems index written to `design/gdd/systems-index.md`.
**Verdict: BLOCKED** only when `design/gdd/game-concept.md` is missing (Phase 1, K2).

---

## Phase 6: Design Individual Systems (Handoff to $design-system)

This phase is entered only when:
- The user invokes `$map-systems [system-name]`
- The user invokes `$map-systems next`

A run that just created the index does not enter it; it ends with Phase 7.

### Step 6a: Select the System

- If a system name was provided, find it in the systems index
- If `next` was used, pick the highest-priority undesigned system (by design order)

### Step 6b: Hand Off to $design-system

Once a system is selected, invoke the `$design-system [system-name]` skill.

The `$design-system` skill handles the full GDD authoring process:
- Gathers context from game concept, systems index, and dependency GDDs
- Creates a file skeleton immediately
- Walks through all 8 required sections one at a time (collaborative, incremental)
- Cross-references existing docs to prevent contradictions
- Routes to specialist agents for domain expertise
- Writes each section to file as soon as it's drafted
- Runs `$design-review` when complete
- Updates the systems index

**Do not duplicate the $design-system workflow here.** This skill owns the systems
*index*; `$design-system` owns individual system *GDDs*.

### Step 6c: Stop

After `$design-system` completes, stop and name `$map-systems next` ([next system
name]) as the next step. Do not loop automatically — each GDD is a session-sized
unit and the user chooses when to spend the next one.

---

## Phase 7: Suggest Next Steps

After the systems index is created (or after designing a system), recommend — do not ask:

- `$map-systems next` (or `$design-system [first-system-in-order]`) to start GDD authoring
- In `lean` mode, `$map-systems --review full` re-runs the index with the director gates spawned — worth it on a new project before committing to 10+ GDD sessions, since scope issues, missing systems and boundary problems are cheapest to fix here

After any individual GDD is completed:
- "Run `$design-review design/gdd/[system].md` in a fresh session to validate quality"
- "Run `$gate-check systems-design` when all MVP GDDs are complete"

---

## Collaborative Protocol

This skill follows the collaborative design principle at every phase:

1. **Explain -> Decide -> Draft -> Write -> Report** at every phase; each decision names its reason
2. **One review point**: the Phase 5b summary, after the index is written — enumeration, dependencies and priorities are all visible there with the changes made
3. **Write and report**: `design/gdd/systems-index.md` and `production/session-state/active.md` are R-grade writes; report the path and the revert command
4. **Incremental writing**: Update the systems index after each system is designed
5. **Handoff**: Individual GDD authoring is owned by `$design-system`, which handles
   incremental section writing, cross-referencing, design review, and index updates
6. **Never start designing a system from this skill** unless invoked with `next` or a system name

**Always** show the enumeration, dependencies, and priorities with the reasons behind them.

## Context Window Awareness

If context reaches or exceeds 70% at any point, append this notice:

> **Context is approaching the limit (≥70%).** The systems index is saved to
> `design/gdd/systems-index.md`. Open a fresh Codex session to continue
> designing individual GDDs — run `$map-systems next` to pick up where you left off.

---

## Recommended Next Steps

- Run `$design-system [first-system-in-order]` to author the first GDD (use design order from the index)
- Run `$map-systems next` to always pick the highest-priority undesigned system automatically
- Run `$design-review design/gdd/[system].md` in a fresh session after each GDD is authored
- Run `$gate-check pre-production` when all MVP GDDs are authored and reviewed
